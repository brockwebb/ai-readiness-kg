# CC Task — A8-v4: a blind latest-vintage pointer is `error`; fixture tables derived from collectors, not rules

**Date:** 2026-09-08
**Project:** ai-readiness-kg
**Authored by:** Desktop session, OODA on `2026-09-08_scan_run_3_RESULT.md` (BLOCKED at §1.4; `d261be8b` still `proposed`; no `state/scan_2026-09-08*.json`; no cycle-3 Results on the graph; `RULE-A8-v3` on the graph, `RULE-A1-v4`/`RULE-A3-v5` on disk only, as expected for a cycle that did not run).
**Fulfils:** its own ResearchTask (`seldon cc register`). Precedes `2026-09-08_scan_run_3b.md`.
**Spend:** zero model calls. **Network: none.** Fixtures on `127.0.0.1` only. No federal host.

**Premise (verified by Desktop against `collectors/v2clauses.py`):** `follow_latest_pointer` dereferences with `fetcher.raw_head`; an exception yields `{status: None, resolved: False, note: <ExceptionName>}`; `robots_disallowed` and `off_host` yield the same `resolved: False`. `latest_pointer_resolves = any(resolved)` therefore conflates four states: resolved, observed non-resolution, blind (exception), and not-fetched-by-policy. `RULE-A8-v3` reads the boolean and returns `fail` on a blind probe. This is DD-052 §6 (`error` never means the product failed), fourth instance after A10, A1, A3.

**Premise (from the RESULT, accepted):** the pre-registered row `resets_links_only:A8 = pass` was derived from reading rule source, not from which collectors issue which HTTP methods. That derivation method produced a wrong expectation once; it is retired here.

**Decisions taken here (operator overrides later):**
1. `RULE-A8-v4` (new module; A8-v3 untouched, stays in `REGISTRY`). Classify each `pointers_tried` entry: `off_host: True` is a scope boundary and is excluded from every count; `note == "robots_disallowed"` or `status is None` is **blind** (unobserved); `status in resolves_statuses` is resolved; any other status is an observed non-resolution. Verdict: no pointers found → as A8-v3 (unchanged); at least one resolved → `pass`; none resolved and at least one observed non-resolution and zero blind → `fail`; none resolved and every non-excluded pointer blind → `error`; mixed observed-non-resolution and blind → `error` with the counts on the Finding (a pointer that might have resolved was not observed, so "none resolves" is not established). Blind and off-host counts on the Finding as fields, not only in reason text.
2. The pre-registered control table for every fixture is **derived, not written**: a script `assessment/harness/scan/fixture_expectations.py` reads `runner.collect_leg` dispatch (which collectors run for which leg, which HTTP methods each issues) and each fixture's declared behaviour (which methods it blinds, resets, refuses, or 4xx's) and emits the expected verdict per leg per fixture. Its output is diffed against the six checked-in tables. **Any difference is a stop**, reported line by line; the table is not edited to match the script and the script is not edited to match the table. Existing tables that the script confirms stay as they are.
3. `blind_links` and `blind_pointers` become fields on the Finding record (schema minor bump, `finding_identity` unchanged unless the identity function reads them, in which case say so and stop). The RESULT's §4.3 concern (count lives in prose) is closed by this.

**Zero edits to:** A8-v3 or any shipped rule module, the targets DataFile, events, `params.yaml` beyond adding `RULE-A8-v4` to `CURRENT` and the fixture-expectation path, any prior cc_task or RESULT.

**Immutable once written. Glob `2026-09-08_a8_v4_blind_pointer_and_fixture_table_ADDENDUM*.md` before starting and again before §3.**

---

## 1. Derive the tables (no rule change yet)
Write `fixture_expectations.py`. Run it against the six existing tables **with `CURRENT` as it stands (A8-v3)**. Expected outcome: it reports `resets_links_only:A8` as `error` where the table says `pass`, and nothing else. If it reports anything else, that is either a fifth blind-probe instance or a defect in the script; name which, and stop if it is the former (it belongs to its own task).

## 2. RULE-A8-v4
Implement per decision 1. Unit tests for all five verdict branches with synthetic `pointers_tried` lists. Update `CURRENT`, regenerate the tool map, re-run the lint (both blind guards accepted, per the RESULT's §3.1).

## 3. Gate (the one gate of this task)
Six-fixture control gate under `CURRENT` = harness-v4 + A1-v4 + A3-v5 + A8-v4, against tables **as emitted by `fixture_expectations.py`** (which now includes `resets_links_only:A8 = error`), every rule its expected verdict, `unknown` = 0. Byte-identical re-derivation for all prior payloads under their own rules and params (A8-v3 stays bound to cycles 1, 2, 2-rj1; nothing re-judged). Hygiene suite green; full `pytest tests/ assessment/`.
**Failure writes no params change and no tool map: report and stop, RESULT with the block on top, commit, push.**

## 4. Report
RESULT `cc_tasks/2026-09-08_a8_v4_blind_pointer_and_fixture_table_RESULT.md`: gate first; the derived tables versus the checked-in ones (diff, expected to be the one A8 row); the five A8-v4 branches with fixture evidence; every premise this task got wrong; whether `finding_identity` changed. Append **DD-061** to `docs/design_decisions.md`: control tables are derived from collector dispatch, never from rule source; blind is `status is None` or policy-not-fetched; `off_host` is scope, not blind. `seldon verify`, `seldon cc complete`, commit, push.

**SEQUENCING:** §1 → §2 → glob addenda → §3 (hard stop) → §4 → push. Then `2026-09-08_scan_run_3b.md`, not before.
