#!/usr/bin/env python3
"""Convert Acrobat PDF annotations into a Markdown review register.

The reviewed PDFs can come from dirty builds, so this tool treats source mapping
as best-effort evidence. It extracts Acrobat annotations, deduplicates repeated
comments across PDFs, fuzzy-matches text against current TeX sources, and writes
a single register for human triage.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import textwrap
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Iterable

try:
    import fitz  # PyMuPDF
except ImportError as exc:  # pragma: no cover - friendly CLI failure
    raise SystemExit(
        "Missing optional dependency PyMuPDF. Install with:\n"
        "  pip install -r python/requirements-review.txt"
    ) from exc


SOURCE_ROOTS = [
    Path("latex/texparts/commentary"),
    Path("latex/texparts/figures"),
    Path("latex/texparts"),
    Path("latex/main.tex"),
    Path("latex/texparts/python"),
    Path("python/analyses"),
    Path("python/stattool"),
]

ROOT_PRIORITY = {
    "latex/texparts/commentary": 0.07,
    "latex/texparts/figures": 0.06,
    "latex/texparts": 0.04,
    "latex/main.tex": 0.03,
    "python/analyses": 0.02,
    "python/stattool": 0.01,
    "latex/texparts/python": -0.03,
}

STATUS_NEEDS_CLARIFICATION = "needs_user_clarification"
STATUS_MAPPED = "mapped_candidate"
STATUS_UNMAPPED = "unmapped"
STATUS_LIKELY_RESOLVED = "likely_resolved_current_source"


@dataclass(frozen=True)
class SourceCandidate:
    path: str
    line: int
    score: float
    confidence: str
    reason: str
    snippet: str


@dataclass
class SourceDoc:
    path: Path
    rel_path: str
    lines: list[str]
    normalized_lines: list[str]
    normalized_text: str
    line_offsets: list[int]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdfs", nargs="+", type=Path, help="Reviewed PDF files")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path.cwd(),
        help="Repository root (default: current working directory)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("review/review_register.md"),
        help="Markdown register path, relative to repo root unless absolute",
    )
    parser.add_argument(
        "--cache",
        type=Path,
        default=Path("review/.cache/annotations.json"),
        help="Raw normalized annotation cache path",
    )
    parser.add_argument(
        "--top-candidates",
        type=int,
        default=3,
        help="Number of source candidates to keep per issue",
    )
    return parser.parse_args()


def clean_pdf_date(value: str | None) -> str:
    if not value:
        return ""
    match = re.match(r"D:(\d{4})(\d{2})(\d{2})(\d{2})?(\d{2})?(\d{2})?", value)
    if not match:
        return value
    year, month, day, hour, minute, second = match.groups()
    if hour is None:
        return f"{year}-{month}-{day}"
    return f"{year}-{month}-{day} {hour or '00'}:{minute or '00'}:{second or '00'}"


def normalize_text(text: str) -> str:
    replacements = {
        "\u00a0": " ",
        "\u00ad": "",
        "\ufb01": "fi",
        "\ufb02": "fl",
        "„": '"',
        "“": '"',
        "”": '"',
        "’": "'",
        "–": "-",
        "—": "-",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = re.sub(r"(\w)-\s+([a-zá-ž])", r"\1\2", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text)
    return text.strip().casefold()


def latex_to_search_text(text: str) -> str:
    text = text.replace("~", " ")
    text = text.replace(r"\,", " ")
    text = text.replace(r"\%", "%")
    text = text.replace(r"\&", "&")
    text = re.sub(r"%.*", "", text)
    # Keep the payload of common one-argument macros where it is useful.
    for _ in range(3):
        text = re.sub(
            r"\\(?:emph|textit|textbf|acl|acs|ac|acp|SI|num|enquote)\{([^{}]*)\}",
            r" \1 ",
            text,
        )
    text = re.sub(r"\\[a-zA-Z@]+\*?(?:\[[^\]]*\])?", " ", text)
    text = text.replace("{", " ").replace("}", " ")
    return normalize_text(text)


def short(text: str, limit: int = 180) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "..."


def markdown_escape(text: str) -> str:
    return (text or "").replace("|", "\\|").replace("\n", " ")


def build_review_id(index: int) -> str:
    return f"REV-2026-04-{index:04d}"


def annotation_text_from_quads(page: fitz.Page, annot: fitz.Annot) -> tuple[str, str]:
    vertices = getattr(annot, "vertices", None)
    if not vertices:
        rect = annot.rect
        expanded = fitz.Rect(rect.x0 - 12, rect.y0 - 12, rect.x1 + 12, rect.y1 + 12)
        return page.get_textbox(rect).strip(), page.get_textbox(expanded).strip()

    chunks: list[str] = []
    context_rect: fitz.Rect | None = None
    for start in range(0, len(vertices), 4):
        quad_points = vertices[start : start + 4]
        if len(quad_points) < 4:
            continue
        quad = fitz.Quad(quad_points)
        rect = quad.rect
        text = page.get_textbox(rect).strip()
        if text:
            chunks.append(text)
        context_rect = rect if context_rect is None else context_rect | rect

    if context_rect is None:
        return "", ""
    expanded = fitz.Rect(
        context_rect.x0 - 40,
        context_rect.y0 - 26,
        context_rect.x1 + 40,
        context_rect.y1 + 26,
    )
    return " ".join(chunks).strip(), page.get_textbox(expanded).strip()


def extract_annotations(pdf_path: Path, repo_root: Path) -> list[dict[str, Any]]:
    abs_pdf = pdf_path if pdf_path.is_absolute() else repo_root / pdf_path
    doc = fitz.open(abs_pdf)
    items: list[dict[str, Any]] = []
    build_id = abs_pdf.stem
    rel_pdf = abs_pdf.relative_to(repo_root).as_posix() if abs_pdf.is_relative_to(repo_root) else str(abs_pdf)

    for page_index, page in enumerate(doc, start=1):
        annots = list(page.annots() or [])
        for annot_index, annot in enumerate(annots, start=1):
            info = annot.info or {}
            highlighted_text, nearby_text = annotation_text_from_quads(page, annot)
            rect = annot.rect
            comment = (info.get("content") or "").strip()
            annotation_type = annot.type[1] if annot.type else "unknown"
            items.append(
                {
                    "source_pdf": rel_pdf,
                    "build_id": build_id,
                    "page": page_index,
                    "annotation_index": annot_index,
                    "annotation_type": annotation_type,
                    "author": info.get("title") or "",
                    "subject": info.get("subject") or "",
                    "created_at": clean_pdf_date(info.get("creationDate")),
                    "modified_at": clean_pdf_date(info.get("modDate")),
                    "comment_text": comment,
                    "highlighted_text": highlighted_text,
                    "nearby_text": nearby_text,
                    "rect": [round(rect.x0, 2), round(rect.y0, 2), round(rect.x1, 2), round(rect.y1, 2)],
                }
            )
    doc.close()
    return items


def fingerprint(item: dict[str, Any]) -> str:
    highlighted = normalize_text(item.get("highlighted_text", ""))
    comment = normalize_text(item.get("comment_text", ""))
    nearby = normalize_text(item.get("nearby_text", ""))

    if len(comment) >= 18:
        core = "\n".join([highlighted, comment]).strip()
    elif highlighted:
        # Highlight-only reviews often mark the same term in many places.
        # Keep nearby context so separate source locations do not collapse into
        # one vague issue just because the highlighted word is identical.
        core = "\n".join([highlighted, nearby[:240]]).strip()
    else:
        core = "\n".join(
            [
                nearby[:240],
                str(item.get("page", "")),
                str(item.get("annotation_type", "")),
            ]
        )
    return hashlib.sha1(core.encode("utf-8")).hexdigest()[:12]


def dedupe_annotations(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for item in items:
        fp = fingerprint(item)
        if fp not in grouped:
            grouped[fp] = {
                "fingerprint": fp,
                "highlighted_text": item.get("highlighted_text", ""),
                "comment_text": item.get("comment_text", ""),
                "nearby_text": item.get("nearby_text", ""),
                "annotation_type": item.get("annotation_type", ""),
                "occurrences": [],
            }
        grouped[fp]["occurrences"].append(item)

        # Prefer the richest text payload for canonical display.
        for key in ["highlighted_text", "comment_text", "nearby_text"]:
            if len(item.get(key, "")) > len(grouped[fp].get(key, "")):
                grouped[fp][key] = item.get(key, "")

    issues = list(grouped.values())
    issues.sort(key=lambda issue: (issue["occurrences"][0]["source_pdf"], issue["occurrences"][0]["page"]))
    for index, issue in enumerate(issues, start=1):
        issue["id"] = build_review_id(index)
        builds = [occ["build_id"] for occ in issue["occurrences"]]
        issue["seen_in"] = sorted(set(builds))
        issue["first_seen"] = builds[0]
        issue["last_seen"] = builds[-1]
        issue["occurrence_count"] = len(issue["occurrences"])
    return issues


def iter_source_files(repo_root: Path) -> Iterable[Path]:
    seen: set[Path] = set()
    for root in SOURCE_ROOTS:
        abs_root = repo_root / root
        if abs_root.is_file() and abs_root.suffix == ".tex":
            if abs_root not in seen:
                seen.add(abs_root)
                yield abs_root
            continue
        if abs_root.is_dir():
            suffixes = (".tex", ".py") if str(root).startswith("python/") else (".tex",)
            for path in sorted(abs_root.rglob("*")):
                if path.is_file() and path.suffix in suffixes and path not in seen:
                    seen.add(path)
                    yield path


def build_source_index(repo_root: Path) -> list[SourceDoc]:
    docs: list[SourceDoc] = []
    for path in iter_source_files(repo_root):
        try:
            raw = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            raw = path.read_text(encoding="utf-8", errors="replace")
        lines = raw.splitlines()
        normalized_lines = [latex_to_search_text(line) for line in lines]
        normalized_text_parts: list[str] = []
        offsets: list[int] = []
        cursor = 0
        for line in normalized_lines:
            offsets.append(cursor)
            normalized_text_parts.append(line)
            cursor += len(line) + 1
        docs.append(
            SourceDoc(
                path=path,
                rel_path=path.relative_to(repo_root).as_posix(),
                lines=lines,
                normalized_lines=normalized_lines,
                normalized_text="\n".join(normalized_text_parts),
                line_offsets=offsets,
            )
        )
    return docs


def line_for_offset(doc: SourceDoc, offset: int) -> int:
    line_no = 1
    for idx, start in enumerate(doc.line_offsets, start=1):
        if start > offset:
            break
        line_no = idx
    return line_no


def priority_for_path(rel_path: str) -> float:
    best = 0.0
    for prefix, value in ROOT_PRIORITY.items():
        if rel_path == prefix or rel_path.startswith(prefix + "/"):
            best = max(best, value)
    return best


def query_texts(issue: dict[str, Any]) -> list[tuple[str, str]]:
    raw_queries = [
        ("highlighted text", issue.get("highlighted_text", "")),
        ("reviewer comment", issue.get("comment_text", "")),
        ("nearby PDF text", issue.get("nearby_text", "")),
    ]
    queries: list[tuple[str, str]] = []
    seen: set[str] = set()
    for label, text in raw_queries:
        norm = normalize_text(text)
        if len(norm) < 18 or norm in seen:
            continue
        if len(norm) > 700:
            norm = norm[:700]
        queries.append((label, norm))
        seen.add(norm)
    return queries


def snippet_for_line(doc: SourceDoc, line: int, radius: int = 1) -> str:
    start = max(1, line - radius)
    end = min(len(doc.lines), line + radius)
    parts = []
    for line_no in range(start, end + 1):
        parts.append(f"{line_no}: {doc.lines[line_no - 1].strip()}")
    return "\n".join(parts)


def confidence(score: float) -> str:
    if score >= 0.88:
        return "high"
    if score >= 0.68:
        return "medium"
    if score >= 0.48:
        return "low"
    return "very low"


def best_window_match(query: str, doc: SourceDoc) -> tuple[float, int, str]:
    best_score = 0.0
    best_line = 1
    best_reason = "fuzzy line-window match"
    query_words = set(query.split())
    if not query_words:
        return best_score, best_line, best_reason

    for idx in range(len(doc.normalized_lines)):
        for span in (1, 2, 3):
            window = " ".join(doc.normalized_lines[idx : idx + span]).strip()
            if len(window) < 15:
                continue
            overlap = len(query_words & set(window.split())) / max(len(query_words), 1)
            if overlap < 0.18:
                continue
            ratio = SequenceMatcher(None, query, window).ratio()
            partial = SequenceMatcher(None, query[: min(len(query), 240)], window).ratio()
            score = max(ratio, partial * 0.92) + min(overlap, 0.45) * 0.18
            if score > best_score:
                best_score = score
                best_line = idx + 1
    return min(best_score, 0.89), best_line, best_reason


def map_issue(issue: dict[str, Any], docs: list[SourceDoc], top_n: int) -> list[SourceCandidate]:
    candidates: list[SourceCandidate] = []
    for label, query in query_texts(issue):
        for doc in docs:
            offset = doc.normalized_text.find(query)
            if offset >= 0:
                line = line_for_offset(doc, offset)
                score = min(0.98, 0.91 + priority_for_path(doc.rel_path))
                candidates.append(
                    SourceCandidate(
                        path=doc.rel_path,
                        line=line,
                        score=score,
                        confidence=confidence(score),
                        reason=f"exact normalized match on {label}",
                        snippet=snippet_for_line(doc, line),
                    )
                )
                continue

            score, line, reason = best_window_match(query, doc)
            score += priority_for_path(doc.rel_path)
            if score >= 0.43:
                candidates.append(
                    SourceCandidate(
                        path=doc.rel_path,
                        line=line,
                        score=min(score, 0.89),
                        confidence=confidence(score),
                        reason=f"{reason} on {label}",
                        snippet=snippet_for_line(doc, line),
                    )
                )

    deduped: dict[tuple[str, int], SourceCandidate] = {}
    for candidate in candidates:
        key = (candidate.path, candidate.line)
        if key not in deduped or candidate.score > deduped[key].score:
            deduped[key] = candidate
    ranked = sorted(deduped.values(), key=lambda item: item.score, reverse=True)
    return ranked[:top_n]


def classify_status(issue: dict[str, Any], candidates: list[SourceCandidate]) -> tuple[str, str]:
    has_comment = bool(normalize_text(issue.get("comment_text", "")))
    has_highlight = bool(normalize_text(issue.get("highlighted_text", "")))
    if not has_comment:
        if candidates:
            return STATUS_NEEDS_CLARIFICATION, "Highlight or markup has no reviewer comment."
        return STATUS_UNMAPPED, "No reviewer comment and no source candidate found."
    if not candidates:
        return STATUS_UNMAPPED, "No plausible source candidate found."
    top = candidates[0]
    if top.score < 0.55:
        return STATUS_NEEDS_CLARIFICATION, "Only low-confidence source candidates were found."

    highlighted_norm = normalize_text(issue.get("highlighted_text", ""))
    if highlighted_norm and top.score < 0.68:
        return STATUS_LIKELY_RESOLVED, "Problematic highlighted text was not found exactly in current source."
    return STATUS_MAPPED, "Review item has a source candidate that should be verified."


def issue_category(issue: dict[str, Any]) -> str:
    text = normalize_text(" ".join([issue.get("comment_text", ""), issue.get("highlighted_text", "")]))
    if any(word in text for word in ["hustot", "organizovanost", "density", "false", "pokrytí", "pokryti"]):
        return "terminology"
    if re.search(r"\b(?:ks|kv|kov|ksvs|zo|oo|os|zp)\b", text):
        return "terminology"
    if any(word in text for word in ["cit", "zdroj", "bibli", "literatur"]):
        return "citation/source"
    if any(word in text for word in ["obraz", "graf", "tabulk", "caption", "popisek"]):
        return "figure/table"
    if any(word in text for word in ["acro", "zkrat", "siunit", "procent", "latex"]):
        return "latex/macro"
    if any(word in text for word in ["data", "metod", "srovnat", "definic"]):
        return "data/method"
    if text:
        return "language/content"
    return "unclear"


def format_candidate(candidate: SourceCandidate) -> str:
    link = f"[{candidate.path}]({candidate.path}#L{candidate.line})"
    snippet = textwrap.indent(candidate.snippet, "    ")
    return (
        f"- {link} — {candidate.confidence} ({candidate.score:.2f}); "
        f"{candidate.reason}\n\n```text\n{snippet}\n```"
    )


def write_register(
    issues: list[dict[str, Any]],
    out_path: Path,
    repo_root: Path,
    pdfs: list[Path],
) -> None:
    today = dt.date.today().isoformat()
    status_counts: dict[str, int] = {}
    category_counts: dict[str, int] = {}
    for issue in issues:
        status_counts[issue["status"]] = status_counts.get(issue["status"], 0) + 1
        category_counts[issue["category"]] = category_counts.get(issue["category"], 0) + 1

    lines: list[str] = [
        "# Acrobat Review Register",
        "",
        f"Generated: {today}",
        "",
        "Scope: Adobe Acrobat comments and highlights extracted from dirty-build PDFs. ",
        "Source links are ranked candidates against the current workspace, not proof that the reviewed PDF was built from the current source.",
        "",
        "## Source PDFs",
        "",
    ]
    for pdf in pdfs:
        rel = (pdf if pdf.is_absolute() else repo_root / pdf).relative_to(repo_root).as_posix()
        lines.append(f"- {rel}")

    lines.extend(
        [
            "",
            "## Triage Decisions",
            "",
            "- Prose should prefer `odborová organizovanost`; `hustota` is retained only where the statistical density indicator/source concept is being named explicitly.",
            "- P KOV / ZO / OS / §24 ZP comments are treated as one conceptual rewrite cluster around definitions and the multi-union employer rule.",
            "- Highlight-only annotations are batched by repeated theme rather than handled one by one.",
            "- `likely_resolved_current_source` entries stay in the register and must be verified after a rebuild.",
        ]
    )

    lines.extend(["", "## Summary", "", "### By Status", ""])
    for status, count in sorted(status_counts.items()):
        lines.append(f"- `{status}`: {count}")
    lines.extend(["", "### By Category", ""])
    for category, count in sorted(category_counts.items()):
        lines.append(f"- `{category}`: {count}")

    lines.extend(
        [
            "",
            "## Triage Table",
            "",
            "| ID | Status | Category | Seen In | Page(s) | Top Source Candidate | Reviewer Note |",
            "|---|---|---|---|---|---|---|",
        ]
    )
    for issue in issues:
        pages = sorted({str(occ["page"]) for occ in issue["occurrences"]})
        top = issue["source_candidates"][0] if issue["source_candidates"] else None
        top_link = f"[{top.path}]({top.path}#L{top.line})" if top else "-"
        lines.append(
            "| {id} | `{status}` | `{category}` | {seen} | {pages} | {top} | {note} |".format(
                id=issue["id"],
                status=issue["status"],
                category=issue["category"],
                seen=", ".join(issue["seen_in"]),
                pages=", ".join(pages),
                top=top_link,
                note=markdown_escape(short(issue.get("comment_text") or issue.get("highlighted_text") or "", 90)),
            )
        )

    lines.extend(["", "## Issues", ""])
    for issue in issues:
        pages = sorted({str(occ["page"]) for occ in issue["occurrences"]})
        lines.extend(
            [
                f"### {issue['id']} — {issue['category']}",
                "",
                f"- Status: `{issue['status']}`",
                f"- Mapping note: {issue['mapping_note']}",
                f"- Seen in: {', '.join(issue['seen_in'])}",
                f"- Page(s): {', '.join(pages)}",
                f"- Occurrences: {issue['occurrence_count']}",
                "",
                "Reviewer comment:",
                "",
                f"> {short(issue.get('comment_text', ''), 900) or '_No comment text extracted._'}",
                "",
                "Highlighted text:",
                "",
                f"> {short(issue.get('highlighted_text', ''), 1200) or '_No highlighted text extracted._'}",
                "",
                "Nearby PDF text:",
                "",
                f"> {short(issue.get('nearby_text', ''), 1200) or '_No nearby text extracted._'}",
                "",
                "Source candidates:",
                "",
            ]
        )
        if issue["source_candidates"]:
            for candidate in issue["source_candidates"]:
                lines.append(format_candidate(candidate))
                lines.append("")
        else:
            lines.append("- No plausible current-source candidate found.")
            lines.append("")

        lines.extend(
            [
                "Occurrences:",
                "",
            ]
        )
        for occ in issue["occurrences"]:
            lines.append(
                f"- {occ['source_pdf']}, page {occ['page']}, `{occ['annotation_type']}`, "
                f"author: {occ.get('author') or '-'}, modified: {occ.get('modified_at') or '-'}"
            )
        lines.extend(["", "Clarification:", "", "- TODO", ""])

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    out_path = args.out if args.out.is_absolute() else repo_root / args.out
    cache_path = args.cache if args.cache.is_absolute() else repo_root / args.cache

    all_annotations: list[dict[str, Any]] = []
    for pdf in args.pdfs:
        all_annotations.extend(extract_annotations(pdf, repo_root))

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_payload = {
        "generated_at": dt.datetime.now().isoformat(timespec="seconds"),
        "annotations": all_annotations,
    }
    cache_path.write_text(json.dumps(cache_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    issues = dedupe_annotations(all_annotations)
    docs = build_source_index(repo_root)
    for issue in issues:
        candidates = map_issue(issue, docs, args.top_candidates)
        status, note = classify_status(issue, candidates)
        issue["source_candidates"] = candidates
        issue["status"] = status
        issue["mapping_note"] = note
        issue["category"] = issue_category(issue)

    write_register(issues, out_path, repo_root, args.pdfs)

    print(f"Extracted annotations: {len(all_annotations)}")
    print(f"Canonical issues: {len(issues)}")
    print(f"Cache: {cache_path.relative_to(repo_root)}")
    print(f"Register: {out_path.relative_to(repo_root)}")


if __name__ == "__main__":
    main()