# RESULT — scan-harness-v4: an unobserved probe is never a pass

**Task:** `cc_tasks/2026-09-08_scan_harness_v4.md` (no addenda exist; globbed and confirmed)
**Date:** 2026-09-08 UTC
**Spend:** zero model calls.
**Network: none.** Every request this task issued went to `127.0.0.1`, asserted at the socket
(`manners.Fetcher.requests`) over the whole control cycle. No federal host was contacted. The
corrected cycle numbers come from re-judging stored Observations, not from re-fetching.

---

## 1. The gate — written first

**PASS on all four clauses.**

### 1.1 Control gate — five fixtures, every rule its pre-registered verdict

`RULE-E5-v2` verdict `pass`. `tests/test_scan_harness_v4.py::test_the_control_gate_passes_on_all_five_fixtures`, 405 s.

| fixture | unexpected verdicts | error classes produced |
|---|---|---|
| `passes_all` | none | `http_4xx`, `off_host` |
| `fails_all` | none | — |
| `refuses_identified_client` | none | `refused` |
| `resets_connection` | none | `connection_reset` |
| **`invalid_route_unobserved`** | none | `connection_reset`, `http_4xx`, `off_host` |

`unknown` = **0**. **The fixture that isolates the defect fired**: `invalid_route_unobserved`
returns `A10 = error` against a pre-registered table written from the rule source before the
fixture was first run, while every other leg returns exactly what it returns on `passes_all`.
`off_host` is demonstrably reachable, so a cycle reporting zero off-host exclusions proves
something.

### 1.2 Re-derivation — byte-identical, seven payloads

```
scan_smoke_2026-09-06        recorded 286  rederived 286  identical
scan_controls_2026-09-06              33            33   identical
scan_2026-09-07                      437           437   identical
scan_2026-09-07_controls              33            33   identical
scan_2026-09-07b                     469           469   identical
scan_2026-09-07_rj1                  352           352   identical   (new)
scan_2026-09-07b_rj1                 404           404   identical   (new)
```

The five prior payloads re-derive under **their own** rules and **their own** params, recovered
from git by hash. The two `_rj1` payloads carry no Observations of their own — that is what
makes them re-judgements — so the gate recovers the evidence from the cycle each names in
`derived_from`, through the same `rejudgeable()` filter the re-judgement itself used. They join
the standing set from here.

### 1.3 Off-host — zero requests to any non-fixture host

`test_no_request_in_the_control_cycle_leaves_the_loopback` runs all five fixtures through every
leg and asserts `manners.Fetcher.requests` holds no host outside `127.0.0.1`. It does not. The
`passes_all` fixture links out to `creativecommons.org`; that link is now **recorded** as an
Observation with `parsed.off_host: true` and `error_class: off_host`, and never fetched —
asserted both from the fetcher's per-host counter and from the fixture request log.

### 1.4 Hygiene green; `corpus/evidence/` unchanged

`tests/test_scan_hygiene.py` — 13 passed; `tests/test_scan_figures.py` — 17 passed.
No evidence body entered or left `corpus/evidence/scan/`: a re-judgement promotes nothing,
because it captures nothing.

**`git status --porcelain corpus/` is not empty, and the one entry is a defect of mine.** It
holds `corpus/quarantine/evidence_scan_fixture/reason.txt` — the append-only record of 54
fixture blobs that `rederive.control_gate_record` wrote into the committed store before
`tests/test_scan_hygiene.py` caught them. Root cause, fix and correction in §5.5. After the
sweep, `corpus/evidence/scan/` is exactly what it was and the hygiene suite is green.

**Nothing was registered before this section was written.**

---

## 2. The A10 delta, per cycle, by surface

`RULE-A10-v2` returned `pass` whenever the invalid-route probe was **anything but HTTP 200** —
including when it was nothing at all. `RULE-A10-v3` calls `_common.unobserved_error` on that
probe first and returns `error` naming the class.

| cycle | A10 as measured | A10 re-judged | pass rate, Wilson 95 % |
|---|---|---|---|
| `scan_2026-09-07` | 16 pass / 7 fail / 3 error | **13 pass / 7 fail / 6 error** | 16/23 = 0.696 [0.491, 0.844] → 13/20 = 0.650 [0.433, 0.819] |
| `scan_2026-09-07b` | 17 pass / 6 fail / 3 error | **13 pass / 6 fail / 7 error** | 17/23 = 0.739 [0.535, 0.875] → 13/19 = 0.684 [0.460, 0.846] |

The denominator moves with the numerator: a blind surface leaves the denominator entirely
rather than counting as a failure, which is DD-052 §6 applied in the direction it was written
for. Both intervals widen, and that is the honest consequence of measuring fewer surfaces —
the instrument now says it knows less, because it does.

The task premised "at least that one". It was **four** in cycle 2 and **three** in cycle 1:

| surface | cycle 1 | cycle 2 |
|---|---|---|
| `scan-census-flagship-2-american-community-survey-acs` | pass → error | pass → error |
| `scan-nass-flagship-1-data-statistics` | pass → error | pass → error |
| `scan-nass-flagship-2-livestock-county-estimates` | pass → error | pass → error |
| `scan-eia-flagship-1-open-data` | — (already `fail`) | pass → error |

Three of the four are blind in **both** cycles, which means the defect was never an EIA
transient: three surfaces have been killing the invalid-route probe since the first cycle and
scoring `pass` for it. The one the RESULT happened to catch was the one that *changed*.

**No leg whose rule did not move moved a single verdict**, in either cycle — asserted, not
observed in passing (`test_the_rejudgement_names_the_rules_that_differ_from_the_source`). A
correction that also moved an unrelated leg would be a re-scoring.

## 3. The A8 delta: zero, and why that is the finding

`RULE-A8-v3` moved **no verdict in either cycle**. A8 was 23 fail / 3 error with zero passes in
both, and every one of those 23 fails on the FIRST clause — the surface declares no
`dateModified`/`datePublished`/`temporalCoverage` at all — so the pointer clause is never
reached on any real surface.

That is exactly why the govdelivery pointer "manufactured no verdict": **luck, not design.** The
test that pins the fix therefore does not replay the record (a replay would certify the luck).
It takes the stored pointer entry verbatim — `resolved: true`, HTTP 200,
`public.govdelivery.com`, no `off_host` field, no `anchor_text` field, because neither existed
when it was written — puts it on a surface that *does* declare a date, and asserts that `v2`
returns **pass** on it and `v3` returns **fail**. The one surface property standing between
that record and a published `pass` was a `dateModified` tag.

A second test pins that the real ACS record still fails on the clause it always failed on,
under both versions, so the correction moved nothing it was not about.

**Which token matched is not recoverable from the stored record.** `how` is truncated at
`reporting.anchor_text_retained_chars` = 40 while the matcher scanned the whole anchor. The
collector now records `matched_token` and `matched_on` beside the text. A matcher that cannot
say why it matched leaves a Finding nobody can check.

## 4. What re-judging changed, and what it could not judge

Findings only. **756 Finding events written, 0 Observation events** (`events/batch-040.jsonl`,
`events/batch-041.jsonl` — a shard each, because a re-judged cycle's Findings cite `obs_id`s
that live on another shard, so "the events of the re-judgement" is only a file if the
judgements are alone in it).

| | `scan_2026-09-07_rj1` | `scan_2026-09-07b_rj1` |
|---|---|---|
| derived from | `scan_2026-09-07` | `scan_2026-09-07b` |
| observations reused | 2,018 | 1,428 |
| findings | 352 | 404 |
| verdicts | 68 pass / 240 fail / 1 n/a / 43 error | 81 pass / 263 fail / 1 n/a / 59 error |
| legs judged | 14 | 16 |
| verdicts moved | 3 | 4 |
| requests issued | 0 | 0 |

**Legs not judged, with the reason on the payload:**

* **`A1`, `A3` in cycle 1 only.** `RULE-A1-v3` and `RULE-A3-v4` consume the `link_probe` leg,
  which harness-v3 introduced and cycle 1 never collected. They register nothing. Judging them
  from whatever else sits under `A1` would produce a number that looks like a re-judgement and
  is not one (DD-055: not measured is a reason, not a zero).
* **`E5`, both cycles.** The control SET changed — `invalid_route_unobserved` is a fifth
  fixture — so judging a four-fixture record against a five-fixture expectation would report a
  change in the *instrument* as a failure of the *cycle*. The gate that licenses each
  re-judgement is the five-fixture run recorded on the payload as `control_gate`, and it is
  recorded rather than published because publishing those Findings would require publishing
  the fixture Observations behind them — and a re-judgement creates no Observation.

## 5. Defects found by this task's own gate

### 5.1 `resets_connection` was a non-deterministic control

The gate's `unknown = 0` clause fired on the *first* five-fixture run. Root-caused rather than
retuned: `ConnectError: [Errno 22] Invalid argument` — EINVAL, a **local socket-state** failure
on `connect()`, not a statement by the peer — which `errors.classify_exception` correctly
declines to name and files as `unknown`. Reproduced at roughly 1 observation in 100 across four
trials of the fixture (2 of 4 trials produced at least one); **never** on
`invalid_route_unobserved`.

The classifier was not touched: naming EINVAL `connection_reset` on four samples would be
precisely the guess `errors.py` exists to forbid. The fixture was. `resets_connection` reset the
socket *before reading the request*, so the client sometimes failed at connect time;
`invalid_route_unobserved` resets *after* reading it, which is why it was deterministic from its
first run. `resets_connection` now reads the request line first and resets without a byte of
response — its declared behaviour unchanged (RFC 9293, *reset before a byte of response*) and
now actually delivered. Four consecutive trials clean afterwards, `connection_reset` 35/35.

**A control that produces its declared failure only most of the time is not a control.**

### 5.2 The framework's `collector_pin` for E5 named two of five fixtures

`framework_writeback_rules.py` wrote E5's collector block only when the collector NAME
differed, so the pin — the framework of record's statement of *which fixtures E5 judges* — was
frozen at `(passes_all, fails_all)` through two fixture additions. It is now derived from
`fixtures.server.MODES` and written whenever any field differs.

### 5.3 Two standing readers assumed `params.yaml` and `cycle.name` move together

Both broke the moment a task corrected a rule's parameters **without re-measuring anything** —
which is what a rule-correction task is:

* `tests/test_scan_run_2.py::test_this_cycle_re_derives_byte_identically` passed
  `load_params()`, so it reported `params_changed`: the guard working, reading as the gate
  failing. It now recovers the payload's own params from git by hash, like every other
  re-derivation reader.
* `register_evidence_retention_result.py` computed the cycle to hold out of the census as
  `params_hash(load_params())`. That does not error when it is wrong — it silently holds
  nothing out and reports a decomposition that does not close. It now reads the hash off the
  cycle's own payload (`cycle_params_hash`).

### 5.4 `A1-v3`/`A3-v4`'s judgeability could not be decided from their own leg

The first re-judgement of cycle 2 reported *"scan_2026-09-07b recorded no observation on leg
A1"* — while the cycle held 1,118 of them under `link_probe`. Those two rules collect nothing
under their own leg by design (`link_probe.legs_served`), so requiring the own leg skipped
exactly the two rules the shared leg was built for. A rule is judgeable when **some** leg it
reads is present. Caught before publication by reading the payload, not by a test; a test now
pins it.

### 5.5 The re-judgement's control gate wrote fixture bodies into the committed store

**Mine, and the worst thing in this task.** `run.py::main` redirects `model.EVIDENCE_ROOT` to a
per-cycle staging root before collecting anything — that is `cc_tasks/2026-09-07_scan_run_2.md`
§1.1, and DD-058 is the record of what it cost to learn. `control_gate_record` reached
`run_controls` **directly** and so inherited the DEFAULT root, which is `corpus/evidence/scan/`
itself. Three command-line runs put **54 fixture blobs** into the committed evidence store,
which is precisely the class of defect staging exists to make impossible.

Caught by `tests/test_scan_hygiene.py::test_the_committed_evidence_store_holds_no_uncited_fixture_output`
in the full-suite run — not by the hygiene suite run alone, which had passed before the
re-judgements ran. **The standing reader worked**, and it is worth saying that plainly: this is
the hygiene gate of the previous task catching the current one.

Three things follow, all in this commit:

1. `control_gate_record` now collects into a `tempfile.TemporaryDirectory` and restores the
   root in a `finally`. Nothing the gate captures is worth keeping — its Findings are recorded
   on the payload and never published, so no Observation will ever cite those bytes, which is
   the definition of litter.
2. The 54 blobs were swept by `scripts/quarantine_fixture_evidence.py`, the sanctioned tool.
   All 54 were **untracked**, so they were removed rather than moved — invariant 2's own
   distinction: it protects bad *acquisitions*, and an uncommitted test output was never one.
   `cited_fixture_blobs_left_in_place: 13`, `non_fixture_blobs: 1322` — nothing else moved.
3. **The sweep's own record was wrong, and is corrected on its face.** The reason line named
   `tests/test_scan_harness.py` as the writer, because that attribution was a CONSTANT in the
   sweep script rather than an argument. A quarantine record that names the wrong writer sends
   the next reader to the wrong file. The script now takes `--wrote-by` (defaulting to the old
   text, which was true of every sweep before this one), and a correction naming the real
   writer is **appended** to `reason.txt` rather than editing the line — the same append-only
   discipline the event log uses.

## 6. Premises this task file got wrong — including my own

1. **"`scan_a10_pass_2026-09-07b` = 17 contains at least that one."** It contains **four**, and
   cycle 1's 16 contains **three**. The task said cycle 1's count was "unknown until
   re-judged"; that was right, and the answer is not zero.
2. **"add a lint over `rules/` that any module with generation ≥ 4 uses it"** — the two rules
   this task ships are `RULE-A10-v3` and `RULE-A8-v3`, whose *version numbers* are 3. The lint
   is over the GENERATION (index in `rules.GENERATIONS`), which is where the new wave `V5`
   sits, and it does cover them. It also covers `rule_a3_v4`, which shipped in generation 4
   before the helper existed and **may not be edited**. That module is exempt by **content
   hash**, with the reason on the exemption; the moment its bytes change the exemption stops
   applying. See §7.1 for what it costs.
3. **"Zero edits to … framework content beyond the `measured` write-back fields."** Moving
   `CURRENT` for two legs makes
   `tests/test_scan_harness.py::test_the_framework_records_the_rule_each_leg_is_judged_by` red
   until the framework's `MeasurementSpec.rule_id` follows. That is not a hand edit and was not
   made as one: `scripts/framework_writeback_rules.py --task cc_tasks/2026-09-08_scan_harness_v4.md`
   is the sanctioned writer, it touched 2 spec `rule_id`s and E5's collector block, and the
   projection followed it (CLAUDE.md: a write-back is not finished until a projection follows).
4. **"`link_probe.same_host_only` … enforced in `collectors/links.probe`"** — true, and the
   enforcement was a bare `continue`, so an off-host link left **no record at all**. Nothing on
   the log could show whether the policy had been applied or to what. The policy is now one
   function and the exclusion is an Observation.
5. **"A8 dereferenced `public.govdelivery.com`… The anchor matcher matched 'subscribe to
   govdelivery email updates' as a latest-vintage pointer."** The stored `how` reads
   `anchor text 'subscribe subscribe to govdelivery email'` and stops there — the token that
   actually matched is beyond the 40-character retention and is **not recoverable**. §3.
6. **"`rederive.py` already re-judges stored observations … Re-judging under a different
   CURRENT is the same machinery pointed at a new params hash."** Nearly. The machinery also
   had to learn (a) that a Findings-only payload's evidence lives in the cycle it names, and
   (b) that a re-judgement judges surfaces and not controls — one rule, `rejudgeable()`, called
   by both the run and the gate, or the gate re-judges 64 fixture Findings the run never
   recorded and calls the difference non-determinism.
7. **My own, in the first pass:** I regenerated both `_rj1` payloads after fixing §5.4 and
   again after `rejudgeable()` moved the observation count, rather than getting the filter
   right once. Three control-gate runs, ~21 minutes of loopback, no consequence beyond time.

## 7. A pre-existing red test, and one gap this task could not close

### 7.1 `RULE-A3-v4` can still fail a surface whose links were all blind

The lint's one exemption is not a clean bill. `RULE-A3-v4` filters link observations through
`_common.served()`, which excludes blind ones — correctly — and then, if none survives, returns
**`fail`**: *"no whole-product download linked from the product page (0 link(s) probed)"*. A
product page that WAS served while every one of its 25 link HEADs was reset is scored as
offering no bulk download. It is the same defect class this task exists to close, pointed the
other way, and `_common.only_errors` does not catch it because the page observation is real.

Not fixed here: a shipped rule module may not be edited, and a new one is a new measurement
with its own control fixture and its own task. `RULE-A1-v3` has the same shape in its final
`fail` branch, and additionally now miscounts — its message says "N links HEADed" and N counts
the off-host records that were never HEADed. Cosmetic, in a `fail` reason only.

### 7.2 `test_the_uncited_set_only_shrinks_and_only_by_citation` is red, and was red at HEAD

Verified by `git stash`: it fails identically before any change in this task, 578 against a
registered 418. Root cause: the assertion compares a `tracked` set measured **now** against a
census taken **before cycle 2 promoted 160 bodies**. Those 160 are tracked today and were cited
by no pre-cycle-2 observation, so they land in `uncited_before_this_cycle`: 418 + 160 = 578,
exactly. The invariant is right; the reader needs the pre-cycle tracked set, which is only
recoverable from git.

Not fixed here — one gate per task, and this is the run-2 gate's, not this one's. Named for
cycle 3 in §9.

## 8. Verification

```
python -m pytest tests/ assessment/
    1579 passed, 1 failed, 2 skipped, 2262 s
    the one failure is tests/test_scan_run_2.py::test_the_uncited_set_only_shrinks_and_
    only_by_citation — PRE-EXISTING, verified red at HEAD by `git stash` with the same
    numbers (578 against 418). Root cause and its owner in §7.2.

seldon verify
    All checks passed. 27805 events readable; 78 task source files resolve; precedence
    acyclic; no stale artifacts; no blocking tasks.

git diff HEAD -- <protected paths>
    assessment/harness/scan/rules/rule_a{1,2,3,8,10}.py       untouched
    assessment/harness/scan/rules/rule_a{8,10}_v2.py          untouched
    every other v1/v2/v3/v4 rule module                       untouched
    assessment/harness/scan/targets.yaml, assessment/cq/      untouched
    cc_tasks/2026-09-07_scan_run_2{,_RESULT}.md               untouched
    events/                                                  APPEND ONLY:
        batch-033_framework.jsonl  +1 line, 0 deleted (the framework_writeback event)
        batch-040.jsonl            new, 352 finding_derived
        batch-041.jsonl            new, 404 finding_derived
    Only rules/__init__.py (+15/-1, the V5 generation) and rules/_common.py (+54/-0,
    two new helpers) changed in rules/, and both are additive.
```

**Graph state after publication and projection** (`scripts/build_projection.py`, all three
layers): 5,297 Observations, 2,578 Findings (1,822 + 756 re-judged), 33 Rules,
`observed_on_missing_document: 0`, `rules_unparseable: []`, `rules_without_indicator: []`.
The framework layer projects 33 `MEASURES` edges, so the two new rules resolve to their
indicators.

**Registered:** 113 Results for `scan_2026-09-07b_rj1` + 101 for `scan_2026-09-07_rj1`
(0 failed), 76 figure-input Results for the re-judged cycle (67 new, 9 already at value),
2 Figures with 242 `CONTAINS`/`GENERATED_BY` edges. The page footer names the re-judgement,
which rules differ, and how many verdicts moved — derived from the `_rj1` payload, not typed.

## 9. What cycle 3 needs — named, not built

1. **`RULE-A3-v5` / `RULE-A1-v4`: a `fail` from zero surviving link probes is an `error`**
   (§7.1). Needs its own fixture — a surface served whole whose LINKS alone are reset — because
   `invalid_route_unobserved` blinds one path and `resets_connection` blinds all of them.
2. **The uncited-body census needs its pre-cycle tracked set from git** (§7.2), or the
   invariant needs restating over a set that is recoverable from disk.
3. **A8's first clause is what A8 actually measures right now.** 23 of 23 surfaces fail on
   "no declared vintage" and the pointer clause has never been reached on a real surface. The
   pointer half of the rule is, so far, tested only by fixtures and by one reconstructed record.
4. **Three surfaces have been killing the A10 invalid-route probe since cycle 1** (§2). Whether
   that is a WAF rule, a path-length limit or a genuine reset is unmeasured, and it is the
   difference between `error` forever and a measurable property.
5. **`cycle.name` and `params_hash` came apart** and two readers broke (§5.3). A task that
   changes params without measuring has no cycle name to move to; whether `cycle.name` should
   name a *parameter set* rather than a *cycle* is the question that would settle it.
6. **The re-judged rates are not on the page's figures**, only in its footer and in the `_rj1`
   cycle's own F1 and F5. Whether the page should lead with the corrected rate is a reporting
   decision, not a harness one.

## 10. One-line summary

An unobserved probe is no longer a pass: `RULE-A10-v3` and `RULE-A8-v3` consult a blind-probe
guard on every probe they score, a fifth control fixture reproduces the exact partial blindness
that produced the false positive, one same-host policy now governs both collectors that
dereference discovered URLs, and re-judging both cycles from stored Observations — zero
requests, zero new Observations — found that **seven** A10 passes across the two cycles rested
on connections nobody ever observed.
