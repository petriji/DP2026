#!/usr/bin/env python3
"""Verify an Acrobat review register against a rebuilt thesis PDF.

The register is generated from dirty-build review PDFs, so this checker does
not rewrite register statuses. It extracts text from the rebuilt PDF, applies a
small set of grouped resolution checks, and writes an auditable Markdown report
with one row per register ID.
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

try:
    import fitz  # PyMuPDF
except ImportError as exc:  # pragma: no cover - friendly CLI failure
    raise SystemExit(
        "Missing optional dependency PyMuPDF. Install with:\n"
        "  pip install -r python/requirements-review.txt"
    ) from exc

from pdf_review_to_register import normalize_text, short


@dataclass(frozen=True)
class Issue:
    review_id: str
    category: str
    register_status: str
    pages: str
    reviewer_comment: str
    highlighted_text: str
    nearby_text: str
    source_candidate: str


@dataclass(frozen=True)
class CheckResult:
    name: str
    status: str
    evidence: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--register",
        type=Path,
        default=Path("review/review_register.md"),
        help="Generated review register Markdown file.",
    )
    parser.add_argument(
        "--pdf",
        type=Path,
        default=Path("latex/build/main.pdf"),
        help="Rebuilt thesis PDF to verify against.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("review/review_verification.md"),
        help="Markdown report path.",
    )
    return parser.parse_args()


def block_value(block: str, heading: str) -> str:
    pattern = rf"{re.escape(heading)}:\n\n> (.*?)(?=\n\n[A-Z][^\n]+:\n|\n\nSource candidates:|\Z)"
    match = re.search(pattern, block, flags=re.S)
    if not match:
        return ""
    value = re.sub(r"\s+", " ", match.group(1)).strip()
    if value.startswith("_No "):
        return ""
    return value


def parse_register(path: Path) -> list[Issue]:
    text = path.read_text(encoding="utf-8")
    sections = re.split(r"(?=^### REV-2026-04-\d+ — )", text, flags=re.M)
    issues: list[Issue] = []
    for section in sections:
        heading = re.match(r"^### (REV-2026-04-\d+) — ([^\n]+)", section)
        if not heading:
            continue
        status = re.search(r"^- Status: `([^`]+)`", section, flags=re.M)
        pages = re.search(r"^- Page\(s\): (.+)$", section, flags=re.M)
        candidate = re.search(r"^- \[([^\]]+)\]\(([^)]+)\)", section, flags=re.M)
        source_candidate = "-"
        if candidate:
            source_candidate = candidate.group(2).split("#", 1)[0]
        issues.append(
            Issue(
                review_id=heading.group(1),
                category=heading.group(2),
                register_status=status.group(1) if status else "unknown",
                pages=pages.group(1) if pages else "-",
                reviewer_comment=block_value(section, "Reviewer comment"),
                highlighted_text=block_value(section, "Highlighted text"),
                nearby_text=block_value(section, "Nearby PDF text"),
                source_candidate=source_candidate,
            )
        )
    return issues


def extract_pdf_text(path: Path) -> tuple[str, list[str]]:
    doc = fitz.open(path)
    pages = [page.get_text("text") for page in doc]
    doc.close()
    return "\n".join(pages), pages


def contains_any(normalized_pdf: str, phrases: Iterable[str]) -> list[str]:
    found: list[str] = []
    for phrase in phrases:
        normalized = normalize_text(phrase)
        if normalized and normalized in normalized_pdf:
            found.append(phrase)
    return found


def count_any(normalized_pdf: str, phrases: Iterable[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for phrase in phrases:
        normalized = normalize_text(phrase)
        if normalized:
            counts[phrase] = normalized_pdf.count(normalized)
    return counts


def issue_text(issue: Issue) -> str:
    return normalize_text(" ".join([issue.reviewer_comment, issue.highlighted_text, issue.nearby_text]))


def is_noise(issue: Issue) -> bool:
    text = issue_text(issue).strip(" .,:;()[]{}")
    if not text:
        return True
    if text in {"false", "fals", "fal", "f", "e", "k", "s", "je", "na", "od", "po", "o", "y"}:
        return True
    return len(text) <= 2


def issue_group(issue: Issue) -> str:
    text = issue_text(issue)
    if is_noise(issue):
        return "extraction_noise"
    if re.search(r"hustot|organizovanost|density", text):
        return "hustota_organizovanost"
    if re.search(r"p kov|\bzo\b|\boo\b|\bos\b|§\s*24|par\. 24", text):
        return "p_kov_zo_os_par24"
    if "zdravotní pojištění" in text or "zdravotni pojisteni" in text:
        return "zdravotni_pojisteni_zp"
    if "extenze" in text or "rozšiřování" in text or "rozsirovani" in text:
        return "ksvs_term"
    if re.search(r"\bks\b|\bkv\b|\bksvs\b", text):
        return "ks_kv_semantics"
    if re.search(r"mzda|mzdy|plat|tarif|výdělek|vydělek|sjednan", text):
        return "wages_tariffs"
    if re.search(r"326/2023|365/2025|§\s*79|§\s*22|§\s*25|zákon|zakon", text):
        return "legal_references"
    if re.search(r"pošta|posta|pks|čp|cp", text):
        return "ceska_posta"
    if re.search(r"ústav|ustav|legislativ|zaměstnavatelsk", text):
        return "conclusion_recommendations"
    if "polsko" in text and "slovensko" in text:
        return "model_introduction"
    return "source_specific"


def group_checks(normalized_pdf: str) -> dict[str, CheckResult]:
    checks: dict[str, CheckResult] = {}

    bad_hustota = [
        "hustota odborů",
        "odborová hustota",
        "odborové hustoty",
        "hustota organizovanosti",
    ]
    counts = count_any(normalized_pdf, bad_hustota)
    remaining = {phrase: count for phrase, count in counts.items() if count}
    checks["hustota_organizovanost"] = CheckResult(
        "Hustota / organizovanost",
        "verified" if not remaining else "needs_review",
        "No discouraged prose forms found." if not remaining else f"Remaining forms: {remaining}",
    )

    old_par24 = [
        "v opačném případě se uzavřená KS vztahuje pouze na zaměstnance členů té organizace",
        "Tento princip kolektivní vyjednávání fragmentuje",
        "zde uvádět §24 není na místě",
    ]
    found = contains_any(normalized_pdf, old_par24)
    checks["p_kov_zo_os_par24"] = CheckResult(
        "P KOV / ZO / OS / §24 ZP",
        "verified" if not found else "needs_review",
        "Old simplified §24 wording is absent." if not found else f"Old wording still found: {found}",
    )

    found = contains_any(normalized_pdf, ["zdravotní pojištění (ZP)", "zdravotní pojištění, ZP"])
    checks["zdravotni_pojisteni_zp"] = CheckResult(
        "Zdravotní pojištění / ZP conflict",
        "verified" if not found else "needs_review",
        "Ambiguous health-insurance ZP rendering is absent." if not found else f"Ambiguous rendering still found: {found}",
    )

    legal_bad = contains_any(normalized_pdf, ["nařízení vlády č. 326/2023 Sb.", "326/2023 Sb."])
    checks["legal_references"] = CheckResult(
        "Legal references",
        "verified" if not legal_bad else "needs_review",
        "Obsolete 326/2023 guaranteed-wage reference is absent." if not legal_bad else f"Obsolete reference still found: {legal_bad}",
    )

    model_terms = [
        "postkomunistický model",
        "postkomunistický srovnávací model",
        "postsocialistický model",
        "postsocialistická srovnání",
    ]
    has_model_term = any(normalize_text(term) in normalized_pdf for term in model_terms)
    checks["model_introduction"] = CheckResult(
        "Model introduction",
        "verified" if has_model_term else "needs_review",
        "Post-communist/post-socialist model framing is present." if has_model_term else "Post-communist model framing not found by text extraction.",
    )

    checks["ksvs_term"] = CheckResult(
        "KSVS term",
        "verified" if "rozšiřování závaznosti" in normalized_pdf else "needs_review",
        "Rozšiřování závaznosti wording is present." if "rozšiřování závaznosti" in normalized_pdf else "Rozšiřování závaznosti wording not found by text extraction.",
    )

    checks["conclusion_recommendations"] = CheckResult(
        "Conclusion recommendations",
        "verified" if "legislativního rámce" in normalized_pdf and "zaměstnavatelských svaz" in normalized_pdf else "needs_review",
        "Legislative-frame and employer-association recommendations are present."
        if "legislativního rámce" in normalized_pdf and "zaměstnavatelských svaz" in normalized_pdf
        else "Expected conclusion recommendation wording not fully found by text extraction.",
    )

    checks["ceska_posta"] = CheckResult(
        "Česká pošta / PKS case study",
        "verified" if "sociální fond" in normalized_pdf and "koordinační" in normalized_pdf else "needs_review",
        "Social-fund and coordination wording is present."
        if "sociální fond" in normalized_pdf and "koordinační" in normalized_pdf
        else "Expected Czech Post rewrite evidence not fully found by text extraction.",
    )

    checks["wages_tariffs"] = CheckResult(
        "Wages / tariffs",
        "verified" if "sjednané minimum" in normalized_pdf or "sjednaná minima" in normalized_pdf else "needs_review",
        "Negotiated-minimum wording is present." if "sjednané minimum" in normalized_pdf or "sjednaná minima" in normalized_pdf else "Negotiated-minimum wording not found by text extraction.",
    )

    checks["ks_kv_semantics"] = CheckResult(
        "KS / KV semantics",
        "manual_review",
        "PDF text extraction cannot prove each semantic choice; source acro audit is required for this group.",
    )
    checks["source_specific"] = CheckResult(
        "Residual source-specific items",
        "manual_review",
        "No shared objective PDF pattern; each item needs source/PDF spot-check if not covered by exact-text absence.",
    )
    checks["extraction_noise"] = CheckResult(
        "Extraction noise",
        "not_actionable",
        "Grouped as OCR/highlight extraction fragments in the resolution notes.",
    )
    return checks


def exact_absence_status(issue: Issue, normalized_pdf: str) -> tuple[str | None, str]:
    highlighted = normalize_text(issue.highlighted_text)
    if len(highlighted) >= 28:
        if highlighted in normalized_pdf:
            return "needs_review", "Original highlighted phrase is still present in rebuilt PDF text."
        return "verified", "Original highlighted phrase is absent from rebuilt PDF text."
    nearby = normalize_text(issue.nearby_text)
    if len(nearby) >= 80 and nearby in normalized_pdf:
        return "needs_review", "Original nearby dirty-build context is still present in rebuilt PDF text."
    return None, "No sufficiently specific original phrase for exact PDF-text verification."


def classify_issue(issue: Issue, normalized_pdf: str, checks: dict[str, CheckResult]) -> tuple[str, str, str]:
    group = issue_group(issue)
    exact_status, exact_evidence = exact_absence_status(issue, normalized_pdf)
    if exact_status == "needs_review":
        return group, exact_status, exact_evidence
    if group == "extraction_noise":
        result = checks[group]
        return group, result.status, result.evidence
    result = checks.get(group, checks["source_specific"])
    if result.status == "verified":
        return group, "verified", result.evidence
    if exact_status == "verified":
        return group, "verified", exact_evidence
    return group, result.status, result.evidence


def write_report(register_path: Path, pdf_path: Path, out_path: Path) -> None:
    issues = parse_register(register_path)
    pdf_text, pages = extract_pdf_text(pdf_path)
    normalized_pdf = normalize_text(pdf_text)
    checks = group_checks(normalized_pdf)

    rows: list[tuple[Issue, str, str, str]] = []
    status_counts: dict[str, int] = {}
    group_counts: dict[str, int] = {}
    for issue in issues:
        group, status, evidence = classify_issue(issue, normalized_pdf, checks)
        rows.append((issue, group, status, evidence))
        status_counts[status] = status_counts.get(status, 0) + 1
        group_counts[group] = group_counts.get(group, 0) + 1

    lines = [
        "# Review Register Verification",
        "",
        f"Generated: {dt.datetime.now().isoformat(timespec='seconds')}",
        f"Register: `{register_path.as_posix()}`",
        f"Rebuilt PDF: `{pdf_path.as_posix()}`",
        f"PDF pages extracted: {len(pages)}",
        "",
        "## Summary By Verification Status",
        "",
    ]
    for status, count in sorted(status_counts.items()):
        lines.append(f"- `{status}`: {count}")
    lines.extend(["", "## Summary By Group", ""])
    for group, count in sorted(group_counts.items()):
        lines.append(f"- `{group}`: {count}")

    lines.extend(["", "## Group Evidence", ""])
    for key, result in sorted(checks.items()):
        lines.append(f"- `{key}`: `{result.status}` — {result.evidence}")

    lines.extend(
        [
            "",
            "## Issue Verification Table",
            "",
            "| ID | Register Status | Group | Verification | Pages | Top Candidate | Evidence |",
            "|---|---|---|---|---|---|---|",
        ]
    )
    for issue, group, status, evidence in rows:
        evidence = short(evidence.replace("|", "\\|"), 140)
        lines.append(
            f"| {issue.review_id} | `{issue.register_status}` | `{group}` | `{status}` | "
            f"{issue.pages} | {issue.source_candidate} | {evidence} |"
        )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(f"Issues verified: {len(issues)}")
    print(f"PDF pages extracted: {len(pages)}")
    print(f"Report: {out_path}")


def main() -> None:
    args = parse_args()
    write_report(args.register, args.pdf, args.out)


if __name__ == "__main__":
    main()