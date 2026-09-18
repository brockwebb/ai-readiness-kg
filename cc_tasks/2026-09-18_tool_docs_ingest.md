# CC Task: the two tool documents the corpus lacks are fetched, admitted, and three indicators take tier O

**Date:** 2026-09-18
**Project:** ai-readiness-kg
**Authored by:** Desktop session, from `cc_tasks/2026-09-17_unassigned_indicators_RESULT.md` §2 (the `open_tool_candidate` list) and `2026-09-18_network_allowlist.md` (the fetch path this task is the first to use).
**Implements:** DN-005 §2.2 (tier O requires the tool's documentation on disk) and the corpus admission path (`scripts/admit_esip_checklist.py`'s, which is `manifest_triage.py`'s).
**Framework layer served (DN-005 §5 rule 1):** §2.2; A7, F2, F3 move from unassigned to O.
**Fulfils:** its own ResearchTask (`seldon cc register`). Launched by the dispatcher.
**Spend:** zero model calls. **Network:** allowlist: raw.githubusercontent.com, github.com, archive.org

---

## 0. What is fetched and why these

Two documents, named by the tier RESULT's `open_tool_candidate` field on the nodes:

- **`oasdiff`** (F2, API description diffing): the project README at `github.com/oasdiff/oasdiff`, via the raw URL for its default branch. Record the URL as resolved and the commit or tag the raw fetch served, if the response carries one.
- **Wayback CDX Server API** (A7 and F3, archived-surface comparison): the CDX server README in `github.com/internetarchive/wayback` under `wayback-cdx-server/`, and the Internet Archive's own API page if one is served on `archive.org`. Two documents if both resolve; one with the failure logged if not.

The fetch is `scripts/fetch_allowlisted.py`: robots-first, identified UA, every request logged. A refused or failed fetch is a logged fact and the indicator stays unassigned; nothing is retried by hand.

**Decisions taken here (operator overrides later):**

1. **Admission through the designed path, one script per epoch** (`scripts/admit_tool_docs.py`, from `admit_esip_checklist.py`): document dir `corpus/tools/` added to `dixie_evidence.yaml` with this task's citation; `screening_imported` with `acquisition_method: scripted_fetch`, `acquired_by: scripts/fetch_allowlisted.py`, `expected_sha256` from the bytes; sweep; `corpus_epoch_declared` naming this task; `manifest.rebuild()`. `doc_type: reference`. Dry-run first, then live, both logged.
2. **Tier O on the strength of the document, not the candidate field.** For each of A7, F2, F3: cite the section of the admitted document that reaches the indicator's spec (the CDX API's `url`, `from`/`to`, `filter` parameters for archived-surface retrieval; `oasdiff`'s breaking-change diff for API description change). If the section exists, `measurement_tier: O`, basis `open_tool`, `tier_source` the locator, and `open_tool_candidate` removed. If it does not, the row stays unassigned with the reason updated to say the document is on disk and what it lacks.
3. **Nothing is measured.** No archived fetch, no diff run. The tool map regenerates; the site's framework copy and manifest move.

**Write set:** `corpus/tools/*` (the fetched documents), `dixie_evidence.yaml`, `corpus/evidence/decisions.jsonl` (append), `corpus/manifest.json` (rebuilt), `scripts/admit_tool_docs.py` (new), `framework/ai_readiness_framework.json` through the writer, `scripts/tag_measurement_tiers.py`, `tests/test_measurement_tiers.py` (distribution literal), the regenerated tool map and site payloads, `scripts/check_protected_tool_docs.sh` (new), `seldon_events.jsonl`, the RESULT. `state/`, `docs/reports/` byte-identical.

**Immutable once written. Glob `2026-09-18_tool_docs_ingest_ADDENDUM*.md` before starting and again before §3.**

---

## 1. Fetch, with the log; admit, dry-run then live.
## 2. Decision 2, row by row; decision 3.
## 3. Gate
`make gate-full` (`-rs`), `seldon verify`, protected paths, projection round-trip. Detached and polled inside this turn per `CLAUDE.md`. Expected skips: 3. Failure ships nothing.
## 4. Report
RESULT `cc_tasks/2026-09-18_tool_docs_ingest_RESULT.md`: §0 the fetch log whole (URL, status, bytes, sha256, robots verdict per request); §1 the ledger entries and epoch; §2 the three rows with locators or updated reasons; §3 new tier counts; §4 every premise this task file got wrong; §5 the gate table, tier named. `seldon cc complete`, commit, push.

**SEQUENCING:** §1 → §2 → glob addenda → §3 → §4 → push. Runs after `2026-09-18_network_allowlist.md`, whose helper and header grammar this task is the first to use.
