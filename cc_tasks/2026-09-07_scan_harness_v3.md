# CC Task — scan-harness-v3: what the first cycle taught, built before the second cycle runs

**Date:** 2026-09-07
**Project:** ai-readiness-kg
**Authored by:** Desktop session (OODA on `2026-09-07_scan_run_RESULT.md` §6, `2026-09-07_framework_projection_repair_RESULT.md` §4 and §7.2, `2026-09-07_eda_and_charts_RESULT.md` §7)
**Fulfils:** its own ResearchTask (registered by `seldon cc register`). Precedes the second scan cycle, which is **not** this task: this task changes the instrument and proves history survives; the next task points it at the hosts.
**Spend:** zero model calls. Network: **none against any federal host.** Every probe in this task hits the local fixture server only. Cycle 2 against real hosts is the next task.

**Premise (verified against the RESULTs and the graph):**
1. `assessment/harness/scan/rules/_common.py:6` holds `RULE_VERSION = "v1"` and every rule's `make` stamps it; all 1,353 Findings carry `rule_version: v1` and the constant is an input to `finding_id` (`model.py:135`). Fixing the constant re-identifies history (repair §7.2). `Rule.version` in the graph is parsed from `rule_id` as a workaround.
2. `error_class` is a closed set with no member for a connection reset; ECONNRESET is filed as `dns` (scan-run §6.2); three StatCan surfaces are mislabelled on the log.
3. A1 and A3 each HEAD the same 25 links per surface independently: double load on public hosts, largest share of the 46-minute wall time (§6.3).
4. Neither control fixture models *permits + refused*, the A12 branch that matters; a unit test substitutes for a control (§6.5).
5. `kg/manifest.py::_convertibility_gate` (`:158`) has no `purpose: scan_surface` escape; cycle 2 would emit 26 more false conversion-gap tasks (repair §4).
6. Bare cycle-level Result names collide on cycle 2 (DD-056 records the rule; nothing enforces it yet).
7. Framework snapshot Results `framework_indicators_{measured,specified,harness_built}` also exist bare (from earlier tasks) beside the suffixed ones; same class, leave them, never reuse them.

**Zero edits to:** any shipped rule module (`v1`, `v2`, `v3`; a new behaviour is a new module), `params.yaml` beyond the keys §1 names, the target list, any event line, the G1 harness, `assessment/cq/*.yaml`, `framework/ai_readiness_framework.json`, any prior cc_task or RESULT.

**Immutable once written. Changes require a new task file or an `_ADDENDUM-NN.md` sibling. Glob and read all siblings `2026-09-07_scan_harness_v3_ADDENDUM*.md` before starting.**

---

## 0. Grounding
- Finding identity is a **parameter, not code**: `params.yaml` gains `finding_identity: 2`, hashed into `params_hash` like every other constant (the harness's existing rule). Under identity 1 (every committed params revision) `make` stamps the constant `v1`; under identity 2 it stamps `parse_rule_id(rule_id).version`. History re-derives under its own params hash, which the history gate already recovers from git (scan-run §2), so no stored Finding changes id. This is the same move the event log makes with `schema_version` on every event (CLAUDE.md invariant 1): the identifier scheme is versioned data, not an edit to the past. Modules stay byte-identical; only `_common.make` learns to read the param.
- A control that fails is the evidence that a zero means something (Cleveland's argument for F1's control marks; scan-run §5): every new verdict branch and every new error class gets a fixture that produces it, or the gate cannot tell a dead rule from a true zero.
- Manners: RFC 9309 (robots exclusion) governs what may be fetched; nothing in it licenses fetching the same object twice in one cycle. One probe per object per cycle.

## 1. Changes (each a new module, new fixture, or new param; nothing shipped is edited)
1. **`finding_identity: 2`** in `params.yaml`; `_common.make` reads it; `parse_rule_id` (rules package, already tested) supplies the version. Test: under identity 1 the id of a known Finding is byte-identical to its stored id; under identity 2 a `v3` rule stamps `v3`.
2. **`ERROR_CLASSES` gains `connection_reset` and `refused`** (TCP-layer reset; HTTP 401/403/429 to the identified client on a robots-permitted path). The collector's fallback classification is replaced by an explicit map from exception type / status to class, with `unknown` as the only remainder, and `unknown` counted and reported per cycle. Do **not** relabel the three StatCan observations on the log: append an `observation_error_reclassified` overlay event for them (append-only correction) and project it.
3. **Shared per-surface link probe.** A `link_probe` observation collected once per surface (up to 25 links, HEAD, 1 req/s, robots-obeyed); `RULE-A1-v3` and `RULE-A3-v4` read it. `A1-v2` and `A3-v3` remain in `REGISTRY`, out of `CURRENT`. Assert by fixture-server request log that a surface's links are HEADed once per cycle.
4. **Three fixtures, not two:** keep `passes_all`, `fails_all`; add `refuses_identified_client` (robots permits, every content path answers 403 to the scanner UA; expected A12 `fail`, A4 `pass`, every content leg `error` class `refused`) and `resets_connection` (accepts then closes the socket; expected error class `connection_reset` on every leg, A12 `error`). Expected verdict tables written before running (pre-registered).
5. **Admission escape:** `_convertibility_gate` returns early when the manifest entry carries `purpose: scan_surface`; the 26 admitted scan Documents get that purpose via a manifest overlay event, not by editing batch lines. Test: admitting a landing page with the purpose emits no `conversion_gap`.
6. **Cycle-suffix enforcement:** the harness's Result registrar refuses any per-cycle name that does not end in `_<cycle>` (DD-056); the bare 2026-09-07 names are allow-listed by exact string as the recorded exception. Test both branches.

## 2. Gate (the one gate of this task)
- Re-derivation, all three prior cycles (2026-09-06 smoke 286, 2026-09-06 control, 2026-09-07 437), each under its own rules and params, **byte-identical**: history untouched under `finding_identity: 2`.
- Control gate over the four fixtures under `CURRENT`: every rule returns its pre-registered verdict, every error class in the table appears at least once, `unknown` = 0.
- `python -m pytest tests/ assessment/` green; `git status --porcelain corpus/` empty after it (scan-hygiene's gate, inherited).
**Failure writes no RESULT numbers as achieved: report and stop.**

## 3. Report
RESULT `cc_tasks/2026-09-07_scan_harness_v3_RESULT.md`: gate output first; the list of `CURRENT` rules with versions; the fixture request log proving one HEAD per link; the reclassification overlay count; every premise this task got wrong. Name (do not build) anything cycle 2 still needs. `seldon verify`, `git diff` empty on protected paths. `seldon cc complete`; commit, push.

**SEQUENCING:** scan-hygiene complete and green → §1.1 → §1.2 → §1.3 → §1.4 → §1.5 → §1.6 → §2 (hard stop) → §3.
