# Acrobat Review Ingestion

This optional workflow converts Adobe Acrobat comments and highlights from
review PDFs into a consolidated Markdown register. It is intentionally separate
from the thesis analytics pipeline and is never invoked by `latexmkrc`.

Install the optional dependency set into the active Python environment:

```bash
pip install -r python/requirements-review.txt
```

Generate the review register from the PDFs stored in `review/`:

```bash
python python/tools/pdf_review_to_register.py review/*.pdf --out review/review_register.md
```

The script writes raw extraction data to `review/.cache/annotations.json` and a
single triage file to `review/review_register.md`. Because the review PDFs may
come from dirty builds, source links are ranked candidates and must be verified
before applying fixes. Durable grouped-resolution decisions belong in
`review/review_resolution_notes.md`; do not rely on manual edits inside the
generated register surviving regeneration.

Recommended fix workflow after the register is reviewed:

1. Keep `review/review_register.md` as the working queue. Source links are
	ranked candidates, so verify the candidate context before editing.
2. Record grouped user decisions in `review/review_resolution_notes.md`, then
	use those decisions to resolve batches rather than asking per annotation.
3. Mark entries that were already fixed after the reviewed dirty builds as
	`resolved_current_source_verified` only after checking the current source and
	rebuilding the PDF.
4. Resolve repeated terminology items in batches. Current triage policy prefers
	`odborová organizovanost` in prose and keeps `hustota` only for the explicit
	statistical density indicator/source concept.
5. Treat P KOV / ZO / OS / §24 ZP notes as one conceptual rewrite cluster around
	the definitions section and the multi-union employer rule.
6. Edit source `.tex` files for prose, citation, and terminology fixes. For
	generated figures or tables, edit the Python analysis script or the tracked
	PGF wrapper as appropriate, not regenerated `texparts/python/*.tex` files.
7. Rebuild the thesis PDF, then update each affected register entry status and
	add a short resolution note.

After a rebuild, generate a PDF-based verification report without rewriting the
generated register:

```bash
python python/tools/verify_review_register_pdf.py \
	--register review/review_register.md \
	--pdf latex/build/main.pdf \
	--out review/review_verification.md
```
