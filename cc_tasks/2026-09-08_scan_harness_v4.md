# CC Task — scan-harness-v4: an unobserved probe is never a pass; one same-host policy; re-judge cycle 2 from its stored observations

**Date:** 2026-09-08
**Project:** ai-readiness-kg
**Authored by:** Desktop session (OODA on `2026-09-07_scan_run_2_RESULT.md` §6, §7, §13; premises checked against the graph 2026-09-08)
**Fulfils:** its own ResearchTask (registered by `seldon cc register`). Precedes `report-draft` (`2517cda8`): the report must not quote an A10 rate that contains a pass the collector never observed.
**Spend:** zero model calls. **Network: none against any federal host.** Fixtures on `127.0.0.1` only. The corrected cycle-2 numbers come from re-judging the stored observations, not from re-fetching.

**Premise (verified):**
1. `RULE-A10-v2` returns `pass` when the invalid-route probe is anything but HTTP 200. On `scan-eia-flagship-1-open-data` the probe got `RemoteProtocolError` (class `connection_reset`, blind) and the rule scored `pass` with reason "invalid route correctly HTTP None" (run-2 RESULT §6.2). DD-052 §6 says `error` never means the product failed; the mirror rule, that a blind observation never means it passed, is not enforced anywhere. `scan_a10_pass_2026-09-07b` = 17 contains at least that one. Whether cycle 1's 16 contains one is unknown until re-judged.
2. `link_probe.same_host_only` is enforced in `collectors/links.probe` and not in `collectors/v2clauses.follow_latest_pointer`; A8 dereferenced `public.govdelivery.com` (2 requests, robots obeyed, no verdict rested on it). The anchor matcher matched "subscribe to govdelivery email updates" as a latest-vintage pointer (§6.1).
3. The observations of both real cycles are on the log with their bodies promoted; `rederive.py` already re-judges stored observations under a named rule set and params (the byte-identical gate is exactly that). Re-judging under a **different** CURRENT is the same machinery pointed at a new params hash and a new cycle name.
4. `resets_connection` resets every path; it cannot isolate "invalid route unobserved, everything else served".
5. Prior art: re-analysis of retained raw data under a corrected scoring rule is ordinary practice; the raw data here are the Observations, Findings are derived. The harness's own doctrine says so (observations are evidence, findings are judgments, DD-052).

**Zero edits to:** any shipped rule module (v4 is new modules), `params.yaml` beyond `cycle.*` and the additions §1 names, the target list, any event line, the G1 harness, `assessment/cq/*.yaml`, framework content beyond the `measured` write-back fields, any prior cc_task or RESULT.

**Immutable once written. Changes require a new task file or an `_ADDENDUM-NN.md` sibling. Glob and read all siblings `2026-09-08_scan_harness_v4_ADDENDUM*.md` before starting.**

---

## 1. Changes
1. **`_common.unobserved(obs)` is consulted for every probe a rule scores on**, not only for the whole-surface `only_errors` check: a rule that reaches a verdict from a probe whose class is blind is a defect by construction. Implement as a helper every v4+ rule calls on each probe it reads; add a lint over `rules/` that any module with generation ≥ 4 uses it. **`RULE-A10-v3`**: invalid-route probe blind → `error` with reason naming the class; deep-link blind → `error`; otherwise as v2. CURRENT moves to A10-v3; A10-v2 stays in REGISTRY.
2. **Fixture `invalid_route_unobserved`**: serves everything `passes_all` serves, but resets the connection (SO_LINGER zero, as `resets_connection`) on the invalid-route path only. Pre-registered table before running: A10 → `error`; every other leg as `passes_all`. Add it to the control set (five fixtures).
3. **One same-host policy.** `link_probe.same_host_only` (rename to `probes.same_host_only` if the key's scope widened; keep the old key readable) governs every collector that dereferences a discovered URL, in one function (`manners.on_roster_host(url, surface)` or equivalent) that both `links.probe` and `follow_latest_pointer` call. An off-host pointer is recorded as an observation with `parsed.off_host: true` and **not fetched**. Test from the fixture request log: an off-host anchor in a fixture page produces zero requests to that host.
4. **`RULE-A8-v3`**: pointer must be same-host (via 3) and the anchor-token set drops any token that matches subscription/notification language; write the exclusion as a list in `params.yaml` with the govdelivery anchor as the test case. A8-v2 stays in REGISTRY.
5. **Re-judge, no network.** A `run.py --rejudge <cycle>` mode (or `rederive.py --under-current`) that judges the stored observations of a named cycle under CURRENT and the current params, writing a new payload `scan_<cycle>_rj1` with `derived_from: <cycle>` and the source `params_hash`, publishing Findings only (no new observations; Findings cite the original `obs_id`s), and registering cycle-suffixed Results `_2026-09-07b_rj1` (and `_2026-09-07_rj1`). Legs whose CURRENT rule consumes an observation the source cycle did not collect (cycle 1 has no `link_probe`) are **not judged** and register nothing, with a reason. State in the payload which rules differ from the source cycle's (A10, A8; plus A1/A3 for cycle 1).

## 2. Gate (the one gate of this task)
- Control gate over **five** fixtures, every rule its pre-registered verdict, `unknown` = 0, and `invalid_route_unobserved` produces A10 `error` (the fixture that isolates the defect must fire).
- Byte-identical re-derivation of all five prior payloads under their own rules and params (the two `_rj1` payloads then join the set for the next task).
- Off-host: zero requests to any non-fixture host across the whole test suite, asserted from the fixture request log and from `manners.Fetcher.requests` keyed by host.
- Hygiene suite green; `git status --porcelain corpus/` empty after the suite (re-judging promotes nothing).
**Failure writes no Results and no page: report and stop.**

## 3. Figures and page
Regenerate F1 and F5 for `_2026-09-07b_rj1` beside the originals (do not overwrite cycle-2 figures; a re-judged cycle is its own cycle). F5 gains the re-judged points marked "re-judged under v4 from stored observations, no re-fetch". Register figures with `CONTAINS` edges as before. Page footer states which rates are re-judged and which rule versions differ.

## 4. Report
RESULT `cc_tasks/2026-09-08_scan_harness_v4_RESULT.md`: gate first; the A10 delta per cycle (how many cycle-1 and cycle-2 A10 passes were blind, by surface); A8 delta; what re-judging changed and what it could not judge; every premise this task got wrong; cycle-3 needs named not built. `python -m pytest tests/ assessment/`, `seldon verify`, `git diff` empty on protected paths. `seldon cc complete`; commit, push.

**SEQUENCING:** §1.1 → §1.2 → §1.3 → §1.4 → §2 controls (hard stop) → §1.5 → §2 remainder (hard stop) → §3 → §4.
