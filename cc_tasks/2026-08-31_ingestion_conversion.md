# CC Task — T1 ingestion: any-format→markdown conversion, admission convertibility gate, shared skill

**Date:** 2026-08-31. **Repo:** /Users/brock/GitHub/ai-readiness-kg. **Immutable once written.**
**Before starting:** glob and read every `cc_tasks/2026-08-31_ingestion_conversion_ADDENDUM*.md`.
**Result:** `cc_tasks/2026-08-31_ingestion_conversion_RESULT.md`; `seldon cc complete` this file AND task `6c39a235` (this task subsumes it); commit, push.
**Spend:** zero model tokens. Conversion is deterministic tooling. Declare `--ceiling-tokens 0`; any model call is a defect. Extraction of converted docs is NOT this task — it rides the bulk task's standing rules (ADDENDUM-02 §2.3).

## Prior art (DD-025 block)

**External.** Docling (IBM Research, MIT, layout-aware, best table fidelity); MarkItDown (Microsoft, MIT, fast path for clean digital formats, built for LLM ingestion); Pandoc (universal converter, strongest for structured markup: HTML/LaTeX/RST/DOCX); trafilatura (HTML main-content extraction, boilerplate/nav removal); Marker/MinerU (GPU, academic PDF — noted, not adopted now). The 2026 production consensus is a **tiered pipeline**: cheap converter first, escalate on structural failure signals, heavy tools only where earned. Adopt this pattern; build no converter.
**Internal.** Wintermute staging format (markdown + YAML frontmatter, sha-stamped) is the canonical target shape; `ingest-youtube` skill is the packaging precedent; the schema-org navigation-table edge (bulk RESULT §5.1) is corpus evidence that unstripped web boilerplate pollutes extraction; symlink-not-copy rule governs skill sharing (drift proven at 363B in <24h).

## The rule this task installs (register as the next free DD)

**Canonical substrate format is markdown with YAML frontmatter. Admission requires convertibility.** A document is admitted only when (a) it is already markdown, or (b) the converter registry declares its format and conversion succeeds, or (c) conversion fails/format unknown → admission still records the document but emits `conversion_gap` (doc, format, tool attempted, failure class) AND auto-registers a ResearchTask naming the gap. Detection at admission, improvement launched by the system, per-item operator review nowhere. The bulk RESULT's `unconvertible_source` discovered at burn time is the counterexample this rule exists to prevent.

## Deliverables

1. **Converter dispatch in T0/T1** (`kg/ingest/convert.py` or the existing substrate module — read the code first, extend don't duplicate): format registry mapping extension/MIME → tool chain. Now: HTML → pandoc with trafilatura pre-extraction for boilerplate removal (compare both on one W3C doc; pick per output inspection, record the choice and reason in RESULT). PDF → existing path unchanged. Everything else → `conversion_gap` per the rule. Frontmatter carries: source URL if known, version, access/acquisition date, source sha256, converter + version, conversion date. Citability survives conversion.
2. **Admission gate** wired per the rule above, with the auto-task mechanism (Seldon task creation from the gap event — the registration is the improvement launch).
3. **Convert the 5 crosswalk HTML docs** (odcs, slsa, ddi, w3c-prov-dm, w3c-prov-o). All five convert (conversion is free); only odcs + slsa get `extraction_request` under the pinned bulk profile (4 demand; ADDENDUM-02 §2.3 governs their burn). The three deferred docs stay deferred — converted substrate, no extraction.
4. **Shared skill** `document-ingest`: SKILL.md wrapping the tiered pipeline for any agent (Molly/Wintermute intake included), placed in the shared skills location and symlinked, never copied. Content: format registry, tool invocations, frontmatter contract, gap protocol.
5. **Mutations:** (a) seeded unsupported format (e.g. `.epub` stub) at admission emits `conversion_gap` and the auto-task appears; (b) seeded broken HTML that fails conversion takes the gap path, not silent admission; (c) frontmatter sha mismatch is detected; (d) drive admission entry points, not fixtures that cannot fail (ninth instance not wanted — the eighth arrived through a fixture with a docstring that named the right principle).
6. Tests green, suite count; RESULT records per-doc conversion output stats (chars in/out, tables preserved for w3c docs) and the queue surface after the two extraction requests.

## Out of scope

Extraction spend; Docling/Marker adoption (add via `conversion_gap` when a format earns it); re-conversion of the existing PDF corpus (working substrate is not a defect); OCR.
