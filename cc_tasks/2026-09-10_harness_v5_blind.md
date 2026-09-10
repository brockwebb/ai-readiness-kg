# CC Task — harness-v5: forbidden to look is blind; scope is not

**Date:** 2026-09-10
**Project:** ai-readiness-kg
**Authored by:** Desktop session, OODA on `2026-09-10_scan_run_4_RESULT.md` (gate STOP at the decision-4 invariant; 14 verdicts on unobserved probes; root cause `errors.CLASSES["robots_disallowed"].blind = False`).
**Fulfils:** its own ResearchTask (`seldon cc register`). Precedes `2026-09-10_rejudge_2_3_4.md`, then `2026-09-10_corpus_noaa_esip.md`.
**Spend:** zero model calls. **Network: none.** Loopback fixtures only. No federal host.

**Decisions taken here (operator overrides later):**
1. **Three classes, named in `errors.py` and nowhere else.** `OBSERVED`: a response was received. `BLIND`: a request was made and no usable answer came back (dns, timeout, reset, refused, 5xx, parse_error, collector_unavailable, unknown) **or** a request to a URL inside the product was forbidden by policy and not made (`robots_disallowed`). `SCOPE`: the URL is outside the product and was not requested by design (`off_host`, `sitemap_off_site`). `NOT_FETCHED` is retired as a class name; "was a request made" becomes a boolean attribute on every class, kept because collectors report it. `rules/_common.unobserved()` means BLIND. No rule reads `errors.CLASSES` directly.
2. **This is `harness-v5`.** `CURRENT` binds it; every prior payload stays bound to its recorded harness version, and re-derivation replays each payload under its own. If re-derivation does not currently bind the harness version per payload, that is the first thing this task fixes, and the RESULT says whether it had to.
3. **A12 reads the refusal on purpose.** `RULE-A12-v2`: its evidence is the response status to `/robots.txt`; a 403 is an observation of enforcement and yields a verdict; a BLIND class (no response at all) yields `error`. A12-v1 stays bound to prior payloads. The generalized invariant check (decision 5) then has no exemption list.
4. **`A10` gets its incident replayed.** In the guards suite: cycle 4's EIA A10 Finding (`pass` from two robots-disallowed probes) is the RED case under harness-v4, GREEN (`error`) under harness-v5. `errors.BY_EXCEPTION_TYPE` learns `httpx.TooManyRedirects` (class: `redirect_loop`, BLIND).
5. **The decision-4 invariant becomes a gate clause with a name.** `tests/test_invariants.py::test_no_verdict_rests_on_unobserved_evidence`, parametrised over every payload under its own harness version: a `pass`/`fail` Finding whose cited Observations are all BLIND is a failure. Under harness-v4 payloads it is expected to report the historical counts (9, 9, 14) as `xfail(strict=True)` with the count asserted, so the history is pinned, not hidden; under any harness-v5 payload it must be 0. The failing test CC left in `test_scan_run_4.py` is folded into this and removed from there.
6. **The figure gate skips**, with a stated reason, when `params.cycle.name` has no matrix, so a task that stops before reporting can be green on everything unrelated.

**Zero edits to:** prior payloads, registered Results, prior RESULTs, cycle evidence, report prose and PDF, targets, `params.yaml` beyond binding harness-v5 and A12-v2 into `CURRENT`.

**Immutable once written. Glob `2026-09-10_harness_v5_blind_ADDENDUM*.md` before starting and again before §3.**

---

## 1. Decisions 1 to 4. `fixture_expectations.py` re-derives the control tables; any row that changes under harness-v5 is listed with the class that moved it (expected: rows where a fixture's robots forbids an in-product probe move from `pass`/`fail` to `error`; nothing else).
## 2. Decisions 5 and 6.
## 3. Gate (the one gate of this task)
Seven-fixture control gate under `CURRENT` (harness-v5, A12-v2) against re-derived tables, `unknown` = 0; both-clocks agreement 0 differences; byte-identical re-derivation of all nine stored payloads **under their own harness versions**; the invariant test: historical counts pinned under v4, and a re-judgement of the seven fixtures under v5 reports 0; A10 replay RED under v4 / GREEN under v5; fast tier and full suite green; `seldon verify`; protected paths.
**Failure: report and stop, RESULT with the block on top, commit, push.**
## 4. Report
RESULT `cc_tasks/2026-09-10_harness_v5_blind_RESULT.md`: whether re-derivation already bound the harness version per payload; the control-table rows that moved and why; every premise wrong. DD-064: the three classes and their meanings; harness versioning is how a judgement-layer fix coexists with a bind-once record. `seldon cc complete`, commit, push.

**SEQUENCING:** §1 → §2 → glob addenda → §3 (detached, logged, polled) → §4 → push.
