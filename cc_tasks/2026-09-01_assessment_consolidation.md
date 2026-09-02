# CC Task: Consolidate the June ai-readiness-fss assessment work into ai-readiness-kg

**Date:** 2026-09-01
**Authored by:** Desktop session
**Immutable once written. Before starting: glob and read all sibling `2026-09-01_assessment_consolidation_ADDENDUM*.md` files.**
**SEQUENCING: run only AFTER `cc_tasks/2026-09-01_machine_diagnostic_stub.md` has completed (step 5 edits the skeleton the stub also edits). Supersedes the intent of `2026-09-01_harness_reconciliation.md` (already marked SUPERSEDED by its ADDENDUM-01).**

## Decision (operator, 2026-09-01)

The June 2026 project at `/Users/brock/GitHub/brock_projects/ai-readiness-fss` (probe harness, benchmark rubric, three-stream assessment spec, survey draft, covariate schema) is not a separate project. It is the assessment-instrument layer of this framework and is moved INTO this repo, history intact. No divergent copies remain. The design survives in full except where the Desktop comparison (this session) found it superseded: probe depth on the discovery/web surface (superseded by the SEO Machine Diagnostic, empirically shown shallow by census-web-concept-inventory D0-r2) and the MCP-named framing of the access axis (superseded by the orientation-first construct below).

## Steps

### 1. History-preserving import (git subtree, not copy)

In `/Users/brock/GitHub/brock_projects` (it is the monorepo containing the June work):
```
git subtree split --prefix=ai-readiness-fss -b airfss-split
```
In `/Users/brock/GitHub/ai-readiness-kg`:
```
git subtree add --prefix=assessment /Users/brock/GitHub/brock_projects airfss-split
```
Result: `assessment/` in this repo holds the June tree with its internal structure intact (`harness/`, `tests/`, `config/`, `cc_tasks/`, `notes/`, the five design docs, `pyproject.toml`, `README.md`). Do not flatten or rename internals in this task; imports (`harness.*`) keep working. `results/` and `evidence/` are gitignored in the source and must remain so — check the imported `.gitignore` and merge its rules into the repo-root `.gitignore` if the subtree's own is not honored.

Verify: `cd assessment && python -m pytest tests/ -v` passes on the imported tree; `git log --oneline -- assessment | tail` shows June 2026 commits.

If `git subtree` is unavailable or the split fails, STOP and write the RESULT; do not fall back to a plain copy.

### 2. Tombstone the old location

In `brock_projects/ai-readiness-fss/`: remove the tree contents and leave a single `MOVED.md`: "Moved 2026-09-01 to `ai-readiness-kg/assessment/` via git subtree (history preserved). Do not edit here." Commit in brock_projects with that message. Delete the `airfss-split` branch after the kg commit is pushed.

### 3. Downstream consumer

`/Users/brock/GitHub/census-web-concept-inventory/config/rubric_source.yaml` points at the old harness path with sha256 pins. Update the path to the new location. The pins must remain valid (content unchanged); verify by recomputing and comparing, and record both in the RESULT. Do not change anything else in that repo.

### 4. Write the merged live design: `docs/crosswalk/assessment_protocol.md`

This is the one new document. The imported June docs stay verbatim in `assessment/` as record; this file is the live, merged assessment protocol of the framework. Content, in this order, each section short:

1. **Purpose and unit of analysis.** Two-level design: the data product is the measurement unit (scored profile = dimension vector + evidence + gap list); products aggregate to agency-level dimension vectors; agency vectors are read within peer cohorts (never as a naked cross-agency ranking). State this as the reconciliation of the June agency-level design and the September product-level pilot.
2. **Orientation first (replaces June Part B's mechanism naming).** Discoverability/retrievability is the first-order construct: an agent arriving cold must be able to find what exists, what it means, how to get it, and what it can do. The established discovery stack (robots exclusion RFC 9309, sitemaps protocol, well-known URIs RFC 8615, schema.org Dataset/DataCatalog, DCAT/data.json, content negotiation, persistent identifiers) is the core-scored mechanism set. Every mechanism, old or new, is a hypothesis about how machines actually orient; the evidence that admits or retires a mechanism is observed machine behavior (crawler/edge logs, D0-class probes, citation telemetry), never vintage or fashion. llms.txt and MCP/WebMCP-class endpoints are dated frontier candidates under this rule.
3. **Scoring model (from June, unchanged).** Pass/partial/fail (2/1/0) per probe; per-dimension vectors; no composite until intended use is decided; evidence emitted for every score; no self-attested input is ever a scored input.
4. **Core/frontier firewall with as_of dating (from June, unchanged).** Applied to this framework's A-group indicators: any indicator testing a post-corpus mechanism carries an as_of date and reports on the frontier track, structurally partitioned before any aggregate.
5. **Enumeration and scope (from June, unchanged).** Two measurement universes per agency (catalog vs web surface), separate vectors never summed; public and public-mandated assets only; restriction-discoverability as the sole surviving restriction concern.
6. **Three evidence streams and cross-checks (from June, unchanged).** Machine diagnostic + agency roll-up + practitioner survey; every response carries the agency (and data-area) join key; designed contradictions are the payload (phantom-policy R3↔P6, lived-vs-measured P8↔probe). Point to `assessment/internal_survey_draft.md` and `assessment/fss_ai_readiness_assessment.md` for the instruments. Note that the survey streams assess organizational readiness, a separable module beyond the product-centric indicator groups.
7. **Dimension naming.** June's D1–D4 are referred to here as Discovery, Retrieval, Interpretability, Trust (spelled out), never "D1–D4", because "D" already means group D (Open) in the skeleton and the D block in census-web-concept-inventory. Map: Discovery+Retrieval ↔ group A; Interpretability ↔ groups B/G; Trust ↔ groups D/F. Groups C, E, G1 have no June counterpart: they are the EVAL-tier measurement of June's own Part A definition ("without loss of statistical integrity"), which June states but does not probe.
8. **Peer-cohort layer.** Dormant pointer to `assessment/covariate_clustering_schema.md`; activates when scores aggregate across agencies.
9. **Reference implementation.** `assessment/harness/` is the public/AUTO-tier reference implementation; new AUTO indicators are specified as probes against its conventions. Known probe-depth gaps (from D0-r2) are listed as open items: meta-robots not read; sitemap read from fixed path not robots-declared; catalog presence scored, not coverage; no declared/enforced/observed triad. The SEO Machine Diagnostic (stub task, A10/A11) is the specification those probes grow toward.

No bold in prose, no em-dashes, no one-sentence paragraphs.

### 5. Skeleton pointer

In `docs/crosswalk/usafacts_operationalization_skeleton.md`, add one paragraph at the top of §6 (or wherever instrument design lives) pointing to `assessment_protocol.md` as the assessment protocol, and append to the Status line: `; v0.2.2 2026-09-01: assessment layer consolidated from ai-readiness-fss (assessment/, docs/crosswalk/assessment_protocol.md) — task cc_tasks/2026-09-01_assessment_consolidation.md`. Nothing else in the skeleton changes.

### 6. Deck content edits (`docs/crosswalk/deck_content_2026-09-01.md`)

- Slide 5: reframe the design stance from "machine surface first (APIs, MCP/A2A-class agent endpoints...)" to orientation-first: the established discovery stack, working and measured, is the machine surface; the human surface derives from it. Remove MCP/A2A from this slide.
- Slide 8: "agent endpoints" → "discovery surfaces".
- Slide 9: add a line: a working in-house reference implementation exists (evidence-emitting probe harness, now `assessment/harness/`), already run against a live Census product.
- Slide 16: add the harness/June work as prior art absorbed, one line.
- Slide 17 item 3 or a new closing line on slide 13: MCP/WebMCP-class endpoints named as dated frontier candidates, admitted on evidence of agent use, not on vintage.
- Bump the file header to v3. If `docs/crosswalk/framework_deck_2026-09-01.pptx` already exists (deck build task ran), rebuild it with the same procedure as `2026-09-01_framework_deck_build.md`; if not, leave the build to that task.

### 7. Seldon

Register `docs/crosswalk/assessment_protocol.md` and `assessment/` as artifacts (type per project conventions). Record a design decision entry in `docs/design_decisions.md` (next DD number): consolidation of the June assessment layer, the two-level unit design, and the orientation-first rule with its evidence criterion.

## Constraints

- Zero model calls, zero spend. Do not touch the running burn, ledger, or corpus manifest.
- Do not edit the imported June documents in `assessment/`; they are record. The live design is `assessment_protocol.md`.
- Every discrepancy between this task's premises and live state goes in the RESULT, never silently reconciled.

## Completion

- `seldon verify`; `cd assessment && python -m pytest tests/ -v`; `python -m pytest tests/ -v` at repo root still passes.
- Write `cc_tasks/2026-09-01_assessment_consolidation_RESULT.md` (subtree commit hashes, test results, pin verification, deck rebuild status).
- `seldon cc complete cc_tasks/2026-09-01_assessment_consolidation.md`.
- Commit and push all three repos touched (ai-readiness-kg, brock_projects, census-web-concept-inventory).
