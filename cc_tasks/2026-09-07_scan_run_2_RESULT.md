# RESULT — scan-run-2: the second cycle, under the instrument the first one taught

**Task:** `cc_tasks/2026-09-07_scan_run_2.md` + `_ADDENDUM-01.md`
**Date:** 2026-09-07 / 2026-09-08 UTC
**Cycle:** `scan_2026-09-07b`, `params_hash 8762d72c0073c8d3332fa5d2454e09dd7c0e6e88edeee051ca066a7cf65b0b45`
**Spend:** zero model calls. Network: 1,469 HTTP requests across 15 hosts, identified UA, 1 req/s per host, robots obeyed.

---

## 1. The gate — written first, per ADDENDUM-01

**PASS on all three clauses.**

### 1.1 Control gate — four fixtures, every rule its pre-registered verdict

Run before any real host was touched. `RULE-E5-v2` verdict `pass`; 65 control Findings (4 fixtures × 16 legs + E5's own).

| fixture | unexpected verdicts | error classes produced |
|---|---|---|
| `passes_all` | none | `http_4xx` |
| `fails_all` | none | — |
| `refuses_identified_client` | none | `refused` |
| `resets_connection` | none | `connection_reset` |

`unknown` = **0** on the controls. All three classes added by harness-v3 (`refused`, `connection_reset`, `unknown`) are demonstrably *reachable*: a class nothing can produce is a class nobody can trust a zero from, and two of the three fired on the fixtures built for them.

**No control observation referenced any off-fixture URL.** Checked directly (0 of 152 control observations carry a non-loopback URL anywhere in `parsed`), because `params.link_probe.same_host_only` exists partly to stop the control cycle reaching the real internet before the gate that runs before any real host. It did not.

### 1.2 Re-derivation — byte-identical, this cycle and all four prior payloads

```
scan_2026-09-07b     recorded 469  rederived 469  missing 0  unexpected 0  mismatches 0  identical
scan_smoke_2026-09-06        286                                                         identical
scan_controls_2026-09-06      33                                                         identical
scan_2026-09-07              437                                                         identical
scan_2026-09-07_controls      33                                                         identical
```

Each prior cycle re-derives under **its own** rules and **its own** params, recovered from git *by hash* — `finding_identity` is 2 and every stored Finding of the four was made under 1, so re-judging history under today's parameters would fail for the one reason that does not matter.

`scan_2026-09-07_controls` is new to this gate. The harness-v3 gate covered three payloads and not this one — which is precisely the payload a `--controls-only` run overwrote on 2026-09-07 and that had to be recovered from git. The payload most likely to be lost was the one nothing checked.

### 1.3 Hygiene suite green after the run

`tests/test_scan_hygiene.py` — 13 passed. No uncited fixture output in the committed store; `git status --porcelain corpus/` shows **exactly the 160 promoted bodies of this cycle and nothing else**.

**Nothing was registered before this section was written.**

---

## 2. Why this run stopped the first time — what the disk shows, not a reconstruction

ADDENDUM-01 asked for this section and asked that it state only what disk and log show.

The disk showed §1 and §2 complete and §3 onward absent: the cycle payload and its controls
payload written, the events published to `events/batch-038.jsonl`, the graph projected, the
staging root emptied — and no matrix DataFile, no `figures/scan_2026-09-07b/`, no RESULT, the
ResearchTask still `proposed`. That is a run that measured and did not report.

**What the disk does not show is why**, and this section does not guess. The measurement is a
measurement that was taken; the addendum's instruction — *"it is not retaken because the
paperwork stopped"* — is what was followed. No host was contacted again.

Two of the addendum's "unknown" items resolved from disk, both **already done**:
`events/batch-037.jsonl` holds **22** `conversion_gap_withdrawn` events (§1.3), and
`docs/design_decisions.md` holds **DD-058** (§1.4).

## 3. The cycle

| | cycle 1 `scan_2026-09-07` | cycle 2 `scan_2026-09-07b` |
|---|---|---|
| surfaces | 40 | 40 |
| Findings | 404 | 404 |
| control Findings | 33 (2 fixtures) | **65** (4 fixtures) |
| Observations | 2,018 | **1,428** |
| HTTP requests | not counted | **1,469** across 15 hosts |
| verdicts | — | pass 85 / fail 263 / n\_a 1 / error 55 |
| `error_class_unknown` | — | **1** |

**The shared link probe did what harness-v3 §1.3 predicted.** 590 fewer Observations, because
A1 and A3 no longer each probe the same objects. And — the point of the exercise — **the rule
change is measurement-neutral**: A1 moved on no surface (0/23 → 0/22) and A3 moved on no
surface (4/23 → 4/22); the only difference on either leg is the ERS denominator below. `v2→v3`
and `v3→v4` changed what the instrument *asks of a host*, not what it *concludes*.

### Requests per host, and the manners claim

1,469 requests, rate-limited to 1/s per host under `ai-readiness-kg-scanner/0.1`, robots
obeyed. Counted at the socket (`manners.Fetcher.requests`), including `robots.txt` fetches,
429/503 retries and HEAD-refused GET fallbacks — **not** the Observation count, because a link
probe issues one HEAD per link inside one Observation. The table is on the progress page,
where a reader who is being scored can see the load we placed on them.

| host | requests | | host | requests |
|---|---|---|---|---|
| `www.bea.gov` | 186 | | `www.irs.gov` | 121 |
| `www.nass.usda.gov` | 186 | | `www150.statcan.gc.ca` | 105 |
| `www.cdc.gov` | 184 | | `www.eia.gov` | 85 |
| `www.census.gov` | 184 | | `nces.ed.gov` | 3 |
| `www.ers.usda.gov` | 157 | | `www.bls.gov` | 3 |
| `ncses.nsf.gov` | 124 | | `www.bts.gov` | 3 |
| `bjs.ojp.gov` | 123 | | `www.ssa.gov` | 3 |
| | | | `public.govdelivery.com` | **2** |

**`public.govdelivery.com` is not on the roster.** See §6.1 — it is a real finding, and RFC
9309 was obeyed for it.

## 4. What moved between the cycles, and why

ADDENDUM-01 required each movement attributed to **host change**, **instrument change**, or
**denominator change**, and required saying which cannot be told apart.

| leg | cycle 1 | cycle 2 | attribution |
|---|---|---|---|
| A4 | 19/23 | **21/22** | host (Census ×3), denominator (ERS) |
| A11-declared | 19/23 | **22/23** | host (Census ×3) |
| A10 | 16/23 | **17/23** | host (EIA) — **and one false pass, §6.2** |
| G1-D | 3/23 | **5/22** | host/content (Census ×2), denominator (ERS) |
| A5 | 2/23 | **3/22** | host (Census ×1), denominator (ERS) |
| A12 (candidate) | 8 pass | **9 pass** | host (Census) |
| A1, A3, A2, A6, A8, A9, B3, D1, D4, F4 | — | — | **no surface moved**; only the ERS denominator |

**ADDENDUM-01's A10 figure is wrong.** It says "A10 19→17". Cycle 1's registered
`scan_a10_pass` is **16**, and cycle 2's is **17** — the leg went *up* by one, not down by two.

### 4.1 One host-side change explains almost all of it: Census's robots.txt came back

Every Census movement traces to a single measured fact, and the evidence is two stored bodies:

```
cycle 1   https://www.census.gov/robots.txt   HTTP 404   25,773 bytes  (a soft-404 error page)
cycle 2   https://www.census.gov/robots.txt   HTTP 200    1,162 bytes  (the file)
```

A4's `MeasurementSpec` says *"a host that has declared nothing has not declared permission"*,
so a 404 on robots.txt is `fail` by design; a served file is `pass`. That one change moves A4
on three Census surfaces, A11-declared on the same three, and A12 on `host:www.census.gov`
(absence of a declaration was `fail`; a served, coherent one is `pass`). A5 on
`scan-census-flagship-1` moves for the same family reason — cycle 1: *"no sitemap, llms.txt or
well-known discovery file served"*; cycle 2: *"sitemap at census.gov/sitemap.xml lists the
product URL (5,408 URLs)"*.

**This is a host change and not an instrument change.** None of A4, A11-declared, A12 or A5
changed rule between the cycles, and the bytes differ.

G1-D on two Census surfaces moves on page content, not on robots: cycle 1 *"none of the 11
error-measure field tokens appears as a structured field"*, cycle 2 *"error-measure field(s)
present: `se`"*. `scan-census-machine` is among them — the machine entry point the eda RESULT
§5.5 recorded as never having passed. **What cannot be told apart:** whether the `se` field was
added to the surface between cycles or was present and unretrieved in cycle 1. One cycle
either way is not enough to say, and this RESULT does not.

### 4.2 The ERS denominator: a host-side DNS transient

`www.ers.usda.gov` failed name resolution partway through the cycle — **21 observations**
across `scan-ers-machine` and `scan-ers-flagship-2`, every one carrying
`ConnectError: [Errno 8] nodename nor servname provided, or not known`. ERS was fully
observable in cycle 1, so this is transient and host-side.

Consequence: **`applicable_n` is 22 on nine legs and 23 on six**, where cycle 1 had a constant
23. Every rate and interval already used its own leg's denominator; what was stale was the
progress page, which stated "n = 23 per leg" as a non-claim. Now derived (§6.4).

A leg that lost a surface to `error` did **not** lose a passing one: the ERS surfaces were
`fail` on those legs in cycle 1, so the numerators are unchanged and only the denominators
moved. That is why A1 and A3 read `0/23 → 0/22` and `4/23 → 4/22` rather than moving at all.

## 5. Every premise this task got wrong

### 5.1 Base task

1. **§1.5: "`cycle.name: scan_<UTC date at this step>`" was unusable.** The UTC date at that
   step *is* `2026-09-07` — cycle 1's name. Following it literally would have pointed cycle 2
   at cycle 1's payload; `refuse_clobber` would have refused, which is the guard working. Named
   **`scan_2026-09-07b`**, which is DD-041's own rerun convention
   (`kg_diag_<metric>_2026-09-04b` against the unsuffixed first run). Result suffix
   `_2026-09-07b`.

2. **§1.2: "the 266" is a floor, not the set.** The status classifier finds **313** divergent
   observations. 47 of them are `lighthouse`'s `invalid_route` probe, which records
   `error_class=None` on a 4xx **deliberately** — that 404 *is* A10's measurement. Overlaying
   them would have relabelled passing measurements as refusals. The pass is scoped to records
   that carry a class to correct: exactly **266**, `http_4xx → refused`. Effective `http_4xx`
   on a refusal status across the whole log is now **0**; `refused` = 317 (266 overlaid + 51
   recorded directly by cycle 2's collectors).

3. **§2: "the 41 surfaces from the target DataFile".** The DataFile holds **41 rows**, of which
   one (`scan-eia-flagship-2-eia-survey-forms`) was never admitted. **40** surfaces, as cycle 1.

4. **§1.3's second clause could not be executed as written.** "Project as a flag on whatever
   the gap event projects to" — `conversion_gap` projects to **nothing** in the KG. No
   projector reads the event type (verified against `build_projection.py`,
   `load_framework_graph.py`, `publish.py`, and now gated by a test). Its only projection is
   the Seldon ResearchTask minted at admission, and all 22 already read `withdrawn`. Per the
   clause's own instruction — *"if it projects to nothing, say so and stop that step"* — the 22
   overlay events were written and no projector was invented.

5. **§5: "expect no status change".** Correct. `promoted: []`, `indicators_measured` stays 16,
   `counts_moved: {}`. F4 therefore gains **no** fourth snapshot, per §5's condition.

### 5.2 ADDENDUM-01

6. **Defect 2's premise is false.** The addendum reports that the 20 ERS `dns` observations and
   the one `unknown` "carry **no error text** (the `response`/`parsed` fields are empty where
   cycle 1 persisted `f"{type(exc).__name__}: {exc}"`)", and asks whether `errors.py` dropped
   it. **Measured: all 21 carry their text.** The 20 ERS records carry
   `ConnectError: [Errno 8] nodename nor servname provided, or not known` — a genuine
   name-resolution failure, correctly `dns` via `errors.BY_MESSAGE`. The `unknown` carries
   `TooManyRedirects: Exceeded maximum allowed redirects.` — `unknown` **by design**, because
   the map refuses to fold a redirect loop into a neighbouring class. **No regression, nothing
   to fix.** A test now asserts the property so the question is answered mechanically next time.

7. **Defect 3 is a fact about the data, not a defect in the arithmetic.** `applicable_n` was
   already per leg (`per_leg` computes `pass + fail` per leg; the Wilson bounds are computed
   from each leg's own `n` and cross-checked against the matrix by
   `register_figure_results.py`). What *was* wrong is the **page**, which carried cycle 1's
   constant "n = 23 per leg" and "upper bound of 0.14". Now derived: "n = 22–23 depending on
   the leg", 8 legs at zero, upper bound 0.15.

8. **Defect 1 is real and is fixed.** `state/scan_2026-09-07b.json` carried
   `"task": "cc_tasks/2026-09-07_scan_run.md"` because `run.py` stamped a module constant.
   `run.py --task` is the source fix; `events/batch-039.jsonl` carries one
   `cycle_task_corrected` event as the append-only correction for the cycle already published.
   Neither the payload nor any event was edited. `task` is not an input to any derived id, so
   nothing was re-identified — which is exactly why it could be wrong for a whole cycle
   without anything noticing.

9. **The addendum's status report was a stale snapshot.** It records §3, §4, §5 as "not done";
   they were done before it was read (it was authored at 21:55 local from a disk state that
   predates them). Its A10 figure is also wrong (§4). Recorded here rather than silently
   reconciled, per CLAUDE.md. Its *instructions* were followed in full: gate first, gate output
   to the RESULT before anything else, §1.3/§1.4 confirmed from disk, defects 1–3 addressed
   with tests, and no host re-contacted.

## 6. What a surface did that no fixture anticipated — named, not fixed

These are v4 candidates. None is fixed in this task; each has evidence on the log.

### 6.1 A8 dereferenced a link on a host that is not on the roster

`RULE-A8`'s pointer probe (`collectors/v2clauses.follow_latest_pointer`) matched the anchor
text *"subscribe subscribe to govdelivery email updates…"* on
`scan-census-flagship-2-american-community-survey-acs` against `a8_latest.anchor_tokens`, and
dereferenced `https://public.govdelivery.com/accounts/USCENSUS/signup/12426` → **HTTP 200,
`resolved: True`**. That is the two requests to `public.govdelivery.com` in §3's table.

Two distinct problems, one policy:

- **`link_probe.same_host_only: true` is enforced in one collector and not the other.**
  `links.probe` filters off-host links before probing; `follow_latest_pointer` has no host
  filter at all. The `params.yaml` comment on that switch names the risk exactly — *"the
  control fixture links out to a licence URL, so probing off-host would make the control cycle
  reach the real internet before the gate"*. **It did not**: 0 of 152 control observations
  reference a non-loopback URL (§1.1). The exposure is real and did not fire.
- **The anchor matcher is too loose for what A8 claims.** An email-signup page is not a
  latest-vintage pointer, and it resolved 200. It did not manufacture a verdict this cycle —
  A8 is **23 fail / 3 error, zero pass** — so no Finding rests on it. 12 pointers were
  dereferenced in total; 1 went off-roster.

**RFC 9309 was obeyed for the third-party host**: `follow_latest_pointer` calls
`fetcher.allowed()`, which fetches and consults that host's `robots.txt` first. That is the
second of the two requests.

### 6.2 A10 turned a blind observation into a `pass` — a false positive

`scan-eia-flagship-1-open-data`, A10, `fail → pass`. The reason string says it:

> *"deep link HTTP 200; invalid route correctly HTTP **None**"*

The invalid-route probe did not receive a 404. It received
`RemoteProtocolError: Server disconnected without sending a response.` — `error_class:
connection_reset`, which `errors.CLASSES` marks **blind**: *the collector could not observe*.
`RULE-A10-v2` tests only that the invalid route is not 200, so a killed connection reads as a
correct rejection.

This is the mirror image of the defect DD-052 §6 exists to prevent. That rule says `error`
must never mean the product **failed**; this shows `error` must never mean the product
**passed** either. **A10's 17/23 in cycle 2 contains at least one pass that is not evidence.**
The fix is a v4 rule that calls `_common.unobserved` on the invalid-route probe and returns
`error`; it is named here and not built, because a shipped rule module may not be edited and a
new one is a new measurement that belongs to its own task with its own control fixture.

### 6.3 Cycle 2 cited a body that cycle 1 had left uncited

`corpus/evidence/scan/06/06264024…` (61,379 bytes, `bjs.ojp.gov/data/topic`) was one of the 418
tracked-but-uncited bodies. Cycle 2 re-fetched it byte-identically for A12, so it is now cited
and the census reads **417**. This falsified a sentence in DD-058; see §7.2.

### 6.4 The progress page carried cycle 1's numbers as non-claims

Fixed here rather than named: `NON_CLAIMS` is now `non_claims()`, derived from the cycle's own
matrix, and the "Zero counts" citation no longer hard-codes `n = 23`. A paragraph headed *"What
this does not claim"* that quotes a stale denominator is making a claim.

## 7. Defects in the harness found by this task's own gate

Six, all in code this task touched, all fixed. Five were found by a test failing.

### 7.1 DD-056's allow-list was a loophole, and a test asserted the loophole

`cycle_results.check_name` returned early for any name in `FIRST_CYCLE_EXCEPTIONS`
**regardless of cycle**. So cycle 2 would have passed the pre-flight with a bare
`scan_surfaces` and then been refused by `seldon result register` mid-run, after the
measurement — *the exact incident DD-056 was written about*. The module's own docstring already
promised these names "are never reused by a later cycle"; nothing enforced it.

Worse, `test_a_cycle_suffixed_name_and_a_recorded_exception_are_allowed` **asserted** that
`check_name("scan_surfaces", "scan_2026-09-08")` passes. The test and the implementation were
wrong in the same direction, which is why the hole survived the harness-v3 gate. The check is
now scoped to `FIRST_CYCLE` and refuses with the suffixed name to use; the test is rewritten as
`test_the_first_cycles_exceptions_belong_to_the_first_cycle_and_to_no_other`.

### 7.2 DD-058 over-claimed, and is amended

I wrote that the uncited-body set is "not re-measurable by a later cycle". Wrong in one
direction: staging forbids it **growing**, but content addressing lets it **shrink** (§6.3).
The corrected property is stronger and is now gated —
`uncited_now + newly_cited_by_this_cycle == uncited_before`, **417 + 1 = 418** — and the
amendment is on the face of `docs/design_decisions.md`.

### 7.3 `refuse_clobber`'s failure path itself failed

It formatted its refusal with `path.relative_to(REPO)` unconditionally, so a path outside the
repo raised `ValueError` instead of `SystemExit`. A guard that raises the wrong thing at the
one moment it fires is worse than no guard.

### 7.4 `seldon artifact list` does not print names, so two registrars' guards could never see

`register_hygiene_results.py` and `register_evidence_retention_result.py` both tested
`name in $(seldon artifact list --type <kind>)`. That command prints type, state and UUID —
**never the name**. The test was permanently `False`, so every run minted a twin;
`seldon artifact create` enforces name uniqueness only on Results (AD-028), so nothing refused
it. The twins surface much later as `ValueError: Multiple Script artifacts with name=…`.
Duplicates superseded; the resolver now lives once in `scripts/seldon_artifacts.py` and asks
the graph. `register_scan_figures.existing()`, which had already learned this for Figures, now
calls the same function.

### 7.5 `--script-name` resolves over superseded artifacts too

So a name that was ever duplicated stays unresolvable even after the twin is superseded. Every
registrar now passes `--script-id` / `--data-ids` with the UUID.

### 7.6 A shadowed loop variable bound a Result under the wrong name

`for kind, name, path, d in ARTIFACTS` rebound `name`, which was already the Result name, to
the last artifact's name — so the cycle-2 census registered as `scan_evidence_store` = 417.
A Result name is bound once (AD-028) and cannot be edited away; it is **superseded with the
reason on its face**, and `scan_evidence_uncited_real_host_bodies_2026-09-07b` = 417 is the
correct record. Mine, and the cheapest possible mistake to make.

### 7.7 A stale-cycle comparison in the figure gate

`test_each_legs_registered_counts_re_derive_from_the_graph` selected Findings by cycle 2's
`params_hash` and compared them to **bare** Result names — which are cycle 1's. It reported the
difference as drift. Now resolved through `figures.rname`, the same single point the figures
use.

## 8. Boundary calls, stated rather than assumed

**The `measured` write-back edits one field the task's "Zero edits" line does not enumerate.**
That line permits `measurement_status` and `measured_by`; the run also rewrote E5's
`not_measured_reason.cycle` (`scan_2026-09-07` → `scan_2026-09-07b`) and its `recorded_by`. Two
lines, one indicator, `counts` unmoved, no status moved.

Decided rather than escalated. §5 explicitly orders `framework_writeback_measured.py --task
<this file>`, and `not_measured_reason` is the third field that one script owns — DD-055 §5's
companion to `measurement_status` ("not measured is a reason, not a silence"). Leaving it would
make the record say cycle 1 is the evidence for E5's status when cycle 2 re-checked it, which
is DD-057's stale-projection defect in a different file: *a stale record does not look stale,
it answers*. When a task's specific instruction and its general scope line disagree, the
specific one governs and the disagreement is reported. Same shape as harness-v3 §7.7. Override
if you disagree; the diff is two lines.

## 9. The matrix, per leg

Denominator: `pass + fail` on **admitted, observable** surfaces. `error` is excluded — the
collector could not observe, which is ours and not the product's. Wilson 95 % score intervals
(Wilson 1927; Brown, Cai & DasGupta 2001 and Newcombe 1998 recommend it over Wald at these n
and at 0 or n successes). **No composite, no ranking, and the legs are not comparable to each
other — they measure different constructs.**

| leg | rule | pass | fail | error | n | rate | Wilson 95 % |
|---|---|---|---|---|---|---|---|
| A1 | `RULE-A1-v3` | 0 | 22 | 4 | 22 | 0.000 | [0.00, 0.149] |
| A2 | `RULE-A2-v3` | 0 | 22 | 4 | 22 | 0.000 | [0.00, 0.149] |
| A3 | `RULE-A3-v4` | 4 | 18 | 4 | 22 | 0.182 | [0.073, 0.385] |
| A4 | `RULE-A4-v1` | 21 | 1 | 4 | 22 | 0.955 | [0.782, 0.992] |
| A5 | `RULE-A5-v1` | 3 | 19 | 4 | 22 | 0.136 | [0.047, 0.333] |
| A6 | `RULE-A6-v2` | 0 | 23 | 3 | 23 | 0.000 | [0.00, 0.143] |
| A8 | `RULE-A8-v2` | 0 | 23 | 3 | 23 | 0.000 | [0.00, 0.143] |
| A9 | `RULE-A9-v1` | 0 | 23 | 3 | 23 | 0.000 | [0.00, 0.143] |
| A10 | `RULE-A10-v2` | 17 | 6 | 3 | 23 | 0.739 | [0.535, 0.875] |
| A11-declared | `RULE-A11-declared-v2` | 22 | 1 | 3 | 23 | 0.957 | [0.790, 0.992] |
| B3 | `RULE-B3-v2` | 4 | 19 | 3 | 23 | 0.174 | [0.070, 0.371] |
| D1 | `RULE-D1-v3` | 0 | 22 | 4 | 22 | 0.000 | [0.00, 0.149] |
| D4 | `RULE-D4-v2` | 0 | 22 | 4 | 22 | 0.000 | [0.00, 0.149] |
| F4 | `RULE-F4-v3` | 0 | 22 | 4 | 22 | 0.000 | [0.00, 0.149] |
| G1-D | `RULE-G1-D-v1` | 5 | 17 | 4 | 22 | 0.227 | [0.101, 0.434] |

**Eight legs remain at zero across both cycles** — A1, A2, A6, A8, A9, D1, D4, F4 — with
upper bounds around 0.15. Their controls fired in both cycles, so these are not dead rules;
they are products that do not have the property. A10's 17 includes the false pass of §6.2.

**A12 (candidate, DD-054 — in no numerator and no denominator).** 9 pass / 3 fail / 1
`not_applicable` / 1 `error` of 14 hosts. `fail`: BLS, BTS, ORES. `not_applicable`: EIA (robots
disallows this client — a host obeyed is not a host in conflict with itself). `error`: StatCan.
Registered per host as `scan_a12_declared_enforced_cohere_<agency>_2026-09-07b` = 1/0 against a
named proposition; the two hosts A12 could not measure register **nothing**, because under
DD-055 not-measured is a reason and not a zero.

**Four of fourteen agencies contributed no admitted surface** — BLS, BTS, NCES, ORES. Three
refuse an identified robots-compliant client outright. A refusal upstream removes an agency
from every denominator on the page, one layer earlier than the guard that keeps unobservable
surfaces in them, and it is the more consequential of the two for an accessibility assessment.
**StatCan** was wholly unobservable again (TCP reset), as in cycle 1.

## 10. Registered

- **143** cycle Results through `scripts/cycle_results.py`, every one cycle-suffixed
  `_2026-09-07b`: per-leg pass/fail/error/not_applicable/applicable_n/pass_rate; A12 per host
  plus `scan_a12_hosts_not_measured`; surfaces, findings, observations, control_findings,
  **`scan_rederived_findings` = 469**; agencies unobservable / with no admitted surface; hosts
  refusing or unreachable; **one Result per host** for requests plus `scan_requests_total`;
  **every error class, zeros included**, plus `scan_error_class_observed`.
- **76** figure inputs (`scripts/register_figure_results.py`): Wilson bounds per leg,
  `control_fired` per leg, framework snapshots, per-criterion counts.
- **`scan_evidence_uncited_real_host_bodies_2026-09-07b` = 417** beside the pre-flight
  **418**.
- **5 Figure artifacts** with **275** `CONTAINS`/`GENERATED_BY` edges, read back out of each
  SVG's own `data-src` attributes so the dependency list cannot go stale.
- DataFiles `scan_matrix_2026-09-07b` and `scan_2026-09-07b`, created by the registrars that
  need them.

**F5 `cycle_over_cycle` is new.** Both cycles' rate per leg with `k/n` and interval on each,
and **A1 and A3 marked "rule changed (v2→v3, v3→v4): not comparable"** so a reader cannot read
a difference there as a change in the host. No line, no delta, no arrow between the two dots: a
difference between two points is not a direction of travel, and two cycles on one day are not a
rate of change. F4 gained **no** fourth snapshot, because no status moved (§5.5).

## 11. What §1 installed

**§1.1 — evidence enters the committed store on citation, and only then.** `run.py
--evidence-root` stages into `state/evidence_staging/<cycle>/` (gitignored);
`publish.promote_evidence` copies exactly the digests the published payload's Observations
cite, rewrites each `body_path` to the promoted location *before* any event is written, and
deletes the staging root. A cited digest present in neither place is a hard failure —
invariant 3 one layer down. Measured on this cycle: **247 cited digests, 160 promoted, 87
already present** (content-addressed dedup against cycle 1), staging root removed,
`git status corpus/` showing exactly those 160.

Rewriting `body_path` is safe and is the point: it is not an input to the derived `obs_id`, so
the record keeps its identity, and a staging path on an append-only line would be a dangling
reference to a directory the same run deletes.

**§1.2 — one error convention.** 266 overlays on `events/batch-036.jsonl`, its own shard, its
own pass (`--pass status`), idempotent. `error_class_recorded` retained on every line. **No
Finding moved**: rules read `manners.unobservable_statuses`, never the class, and the
re-derivation gate proves it — 469/469 byte-identical.

**§1.3 — 22 `conversion_gap_withdrawn` overlays** on `events/batch-037.jsonl`, each naming its
withdrawn ResearchTask id and `cc_tasks/2026-09-07_framework_projection_repair.md`. Verified in
the graph: all 22 ResearchTasks read `withdrawn`.

**§1.4 — DD-058** (plus its amendment, §7.2) and the two censuses.

**§1.5 — `cycle.name` moved**, `refuse_clobber` no longer refuses, `params_hash`
`8762d72c0073…`.

## 12. Verification

- `python -m pytest tests/ assessment/` — **1,546 passed, 2 skipped** in 26 min. One failure
  on the first pass and it was a stale literal, not a regression:
  `test_the_misfiled_observations_are_overlaid_and_never_edited` asserted
  `len(rc.overlaid()) == 93`, but `overlaid()` is deliberately **pass-agnostic** — it is the
  idempotence guard that stops a second pass re-correcting a record a first pass fixed — so it
  became 359 when §1.2 added its 266. Asserting against the total made it a test of *how many
  passes have ever run*. Now counted per pass (`classified_from`), and the 93 stands.
- `seldon verify` — **all 12 checks passed**, 26,709 events readable.
- **Zero shipped rule modules changed**: all 37 in `rules/` byte-identical against `HEAD`,
  checked file by file. `state/scan_targets_2026-09.json`, `assessment/cq/`,
  `docs/schema_v0.1.md` and `kg/schema.yaml` clean.
- **No event line edited.** `events/batch-033_framework.jsonl` is the only prior shard touched
  and the diff is `1 insertion, 0 deletions` — the write-back's own append. Shards 036–039 are
  new.
- Re-derivation: **five** payloads byte-identical (§1.2).
- `observed_on_missing_document`: **0**.
- Projection: 5,297 Observations, 1,822 Findings, 31 Rules, all 31 with a `MEASURES` edge, 0
  unparseable, 0 without an indicator. `findings_evidence_unretained` 120,
  `observations_error_reclassified` **359** (93 + 266).
- Framework layer re-projected after the write-back (DD-057): 49 indicators,
  `measurement_status {measured: 16, harness_built: 1, specified: 32}` — unchanged.
- Figure gate `tests/test_scan_figures.py`: 17 passed, every numeral in all five figures
  resolving to a registered Result, a matrix count, or a declared axis tick.

## 13. What cycle 3 needs — named, not built

1. **A10-v3: an unobserved invalid-route probe is `error`, not `pass`** (§6.2). The one
   substantive measurement defect this cycle found. Needs its own control fixture — a host that
   resets the connection on the invalid route specifically — because `resets_connection` resets
   *everything* and would not isolate it.
2. **One same-host policy, enforced in one place** (§6.1). `link_probe.same_host_only` should
   govern `follow_latest_pointer` too, or A8 should declare its own and say why it differs.
3. **A8's anchor matcher** (§6.1): "subscribe … email updates" matched a *latest-vintage*
   pointer token. Tighten the tokens, or require the pointer to be on the product's host, or
   both.
4. **The 417 retained uncited bodies** still have no retention policy — DD-058 says they stay
   and why, and says a policy for contact records is a different question.
5. **Whether Census's `se` field is new or was unretrieved in cycle 1** (§4.1) — the one
   movement this RESULT explicitly declines to attribute.
6. `run.py --task` exists now; every future cycle should pass it.

7. **The `overlaid()` / per-pass distinction should be a helper, not a convention.** §12's one
   test failure was a reasonable literal that a second pass invalidated. `overlaid()` is
   pass-agnostic on purpose and `rows(pass)` is pass-scoped; a `overlaid(pass)` would have made
   the right thing the easy thing.

---

## 14. One-line summary

Cycle 2 measured the same 40 surfaces with **590 fewer observations** and **1,469 requests**,
re-derived byte-identically along with all four prior cycles, and found that almost everything
that moved moved because **`www.census.gov` started serving its `robots.txt` again** — while
the two legs whose rules changed moved on no surface at all. The instrument also caught itself
scoring a `pass` on a connection it never observed (§6.2), which is the finding worth acting on.
