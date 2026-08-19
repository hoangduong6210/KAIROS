---
title: Contributing to the Wiki
status: canonical
last_updated: 2026-08-19
paper_source: false
---

# Contributing to the Wiki

Every page requires YAML front matter with `title`, `status`, one ISO date, and
`paper_source`. A page marked `paper_source: true` additionally requires
`prose_reviewed: true` and admitted `claim_ids`.

Update the semantic owner instead of copying mutable values. Add every page and
identifier to [INDEX](INDEX.md). Preserve rejected, failed, quarantined, and
superseded records. Run `python -m pytest` before handoff; passing contract tests
does not replace scientific or prose review.

Any section containing a scientific quantity must declare both a claim ID and
an evidence ID using the convention in the [traceability policy](evidence/Traceability-Policy.md).
Blocked and historical wording still requires a direct evidence record showing
where the wording or value came from.

Run the repository checks after wiki changes:

```bash
python -m pytest
```
