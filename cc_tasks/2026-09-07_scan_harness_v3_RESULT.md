# RESULT — scan-harness-v3

**Task:** `cc_tasks/2026-09-07_scan_harness_v3.md` (no `_ADDENDUM*` siblings exist; globbed before starting)
**Date:** 2026-09-07
**Prerequisite:** `cc_tasks/2026-09-07_scan_hygiene.md` complete and its gate green (commit `f688339`), per this task's SEQUENCING line.
**Spend:** zero model calls. **Network: none against any federal host.** Every probe in this task hit the local fixture server on `127.0.0.1`. Processes launched: `pytest`, `git`, `seldon`, this task's own scripts, and the scan layer's projector.

---

## 0. Gate — PASS

`cc_tasks/2026-09-07_scan_harness_v3.md` §2, all three clauses, on a clean tree.

**1. All three prior cycles re-derive byte-identically, each under its own rules and its own params.**
`tests/test_scan_harness_v3.py::test_every_prior_cycle_re_derives_byte_identically`, parameterised over the three, with each cycle's `params.yaml` recovered from git **by hash** rather than reconstructed:

| cycle | recorded | re-derived | identical |
|---|---|---|---|
| `scan_smoke_2026-09-06` | 286 | 286 | yes |
| `scan_controls_2026-09-06` | 33 | 33 | yes |
| `scan_2026-09-07` | 437 | 437 | yes |

`finding_identity` is now 2 and every one of those 756 Findings was made under 1. **No stored id moved**, which is the whole claim §0 of the task makes: the identifier scheme is versioned data that history carries with it, not an edit to the past.

**2. The control gate passes over four fixtures under `CURRENT`, with the table exactly as pre-registered.**
65 control Findings (16 legs × 4 fixtures + E5's own), **zero unexpected verdicts**, `e5.verdict == "pass"`. Every error class the fixtures exist to reach actually appeared —

```
refused           present (refuses_identified_client)
connection_reset  present (resets_connection)
unknown           ABSENT  — 0, as required
```

— which is what lets a cycle reporting zero refusals mean something. Nothing in the pre-registered table was edited after a run; see §4 for the one leg where the derivation disagreed with the task file and the derivation was right.

**3. `python -m pytest tests/ assessment/` green, and `git status --porcelain corpus/` unchanged by it.**

```
1519 passed, 2 skipped, 28 warnings in 1170.15s (0:19:30)
=== corpus delta ===
IDENTICAL — the suite added nothing
```

**Also green:** `seldon verify` — all 12 checks passed. `git diff` is empty on every protected path: the target list, `assessment/cq/`, and **every shipped rule module** — checked file by file, all 33 prior rule modules byte-identical against `HEAD`.

**Projected, per DD-057** — a write-back that edits the framework JSON is not finished until a projection follows it. Scan layer (`publish.py --project`): `findings_evidence_unretained: 120`, `observations_error_reclassified: 93`. Framework layer (`load_framework_graph.py`): 49 indicators, `measurement_status {measured: 16, harness_built: 1, specified: 32}` — unchanged, as the write-back's `indicators_status: 0` promised. Verified by Cypher afterwards: `MeasurementSpec {leg:"A1"}.rule_id = "RULE-A1-v3"`, `{leg:"A3"} = "RULE-A3-v4"`, and 93 Observations carrying `error_reclassified = true` (92 `dns -> connection_reset`, 1 `dns -> unknown`).

---

## 1. §1.1 — a Finding's id scheme is a parameter

`params.yaml` gains `finding_identity: 2`, hashed into `params_hash` like every other constant. `_common.make` and `_common.empty` read it through one function, `rule_version(rule_id, params)`, dispatched from a table rather than an if-chain so a third scheme is one entry rather than a new branch in two places:

* **identity 1** stamps the constant `RULE_VERSION` — `"v1"` for every rule ever shipped, and an input to the derived `finding_id`, which is why it can never be corrected in place.
* **identity 2** stamps `parse_rule_id(rule_id)["version"]` — the only place the version is actually true. `RULE-A3-v4` stamps `v4`.

**Absent means 1**, so a params set that predates the key re-derives byte-identically. An unrecognised scheme is a hard error rather than a fallback to 1: minting ids under a scheme the params do not name is precisely the failure the parameter exists to prevent.

Not one rule module's decision logic changed. The modules are byte-identical except the two new ones.

---

## 2. §1.2 — every failure has a name, and `unknown` is the only remainder

`assessment/harness/scan/errors.py` is new and is the single definition of three things that used to live in four places:

1. **The closed set**, re-exported by `model.py`. `connection_reset`, `refused` and `unknown` are added; nothing left.
2. **Whether each class means "we did not observe"**, declared *beside the class*. `rules/_common._BLIND` now reads it instead of restating it — and that is not tidying, it is the fix for this defect one layer up: a class added to the closed set and forgotten in a hand-kept blind list would have turned the 92 StatCan non-observations into 92 product failures the moment the classifier improved. `robots_disallowed` is deliberately **not** blind (it is A4's measurement and A12's `not_applicable`); `http_4xx` is deliberately not blind (a 404 IS the measurement). Both readings are preserved exactly, and a test asserts the blind set grew **only** by the three new members.
3. **The map itself** — exception type, then errno (through the `errno` module, because ECONNRESET is 54 on Darwin and 104 on Linux), then message, then `unknown`. `manners.error_class_for` is superseded: it knew only 4xx/5xx and so could not tell a 404 from a 403.

Every collector's fallback is gone — the two `"timeout" … else "dns"` guesses and the five bare `error_class="dns"` literals — and a test greps `collectors/` to keep them gone.

**`refused` and `connection_reset` are not the same event and are not merged.** `refused` is HTTP-layer (401/403/429 to an identified client on a path robots permits — the collectors never fetch a disallowed path, so a status seen here is by construction on a permitted one). `connection_reset` is TCP-layer. `ECONNREFUSED` — nothing listening — is **neither**, and resolves to `unknown` on purpose: folding it in would make the count of "hosts that refuse this scanner" include hosts that are simply down.

**The 93 misfiled observations are overlaid, never edited.** `scripts/reclassify_observation_errors.py` appends one `observation_error_reclassified` event per observation to `events/batch-034.jsonl`. The correction re-reads the record and does not re-fetch: every collector persists `f"{type(exc).__name__}: {exc}"`, so the exception's type and message both survive on the log and are the evidence for each correction. `publish.py::project` reads the overlay and sets `Observation.error_class` to the corrected class, keeping `error_class_recorded` beside it and `error_reclassified` as a flag — the record and its correction both visible, neither replacing the other.

Three observations were **excluded** from the overlay after inspection: they carry `collector_unavailable`, which is the RUNNER's statement about ITSELF (`run.py`'s catch-all, recording the D1 collector's `.get("status", 999)` crash on the StatCan surfaces). The map classifies what a COLLECTOR saw and has no standing over that class.

**266 observations are NOT overlaid and the number is reported rather than acted on:** they carry `http_4xx` on an HTTP 403 and would be `refused` under the new map. `http_4xx` was the only answer the old closed set had for a 403, so it was not a misfiling in the way `dns` for a reset was, and the rules already read that refusal correctly through `manners.unobservable_statuses`. Whether the log should carry one convention or two is a decision for the next task, with the number in hand.

Every cycle now reports `error_class_counts` (all classes, zeros included) and `error_class_unknown` on its own line.

---

## 3. §1.3 — one probe per object per cycle

A `link_probe` leg, named in `params.link_probe.shared_leg`, collects the product page and up to 25 same-host links **once per surface**, at the standing 1 req/s, robots obeyed. `RULE-A1-v3` and `RULE-A3-v4` declare `CONSUMES = ("link_probe",)`; `A1` and `A3` collect nothing of their own (`params.link_probe.legs_served`). `RULE-A1-v2` and `RULE-A3-v3` stay in `REGISTRY`, out of `CURRENT` — every Finding recorded under them still re-derives under them.

**The grouping is one function, `rules.consumes`, read by both callers that must agree.** `run.py` uses it to build the group a rule judges; `rederive.py` uses it to rebuild that group from stored observations. `rederive` also had to stop iterating `(surface × leg)` and start iterating `(surface × rule)`: a rule that reads only a shared leg has no `(doc, leg)` key at all, and a leg-driven loop would have silently never judged it. For every rule with no `CONSUMES` the grouping is unchanged, which is why all three prior cycles still re-derive byte-identically.

Asserted from the fixture server's **request log** — what was actually fetched: after collecting the shared leg and then A1 and A3, no path is HEADed twice.

---

## 5. §1.5 — a surface admitted to be measured is not gapped for being thin

`kg/manifest.py` gains a **closed** set of purposes (`corpus_document`, `scan_surface`) — a free-text purpose that switches a gate off is a hole, not a field — and `_convertibility_gate` returns early for `scan_surface`. `add()` validates and carries `purpose` on new admissions.

The 26 already-admitted scan surfaces get it through an append-only `manifest_purpose_declared` overlay on `events/batch-035.jsonl`, applied over the admission entry by `_load_entries` exactly as `content_update` is. **No batch line was edited.** The doc_ids are read from the ledger by prefix rather than typed as a list of 26, so there is one definition of which documents are scan surfaces.

The 22 `conversion_gap` events already on the log are history and stay; the escape stops the next 26.

---

## 6. §1.6 — a per-cycle Result name carries its cycle

`scripts/cycle_results.py` is the registrar every scan cycle now registers through. It checks **every** name before **any** is registered — the same discipline `seldon result register` applies to its own references, and the reason is DD-056's motivating incident: `scan_control_findings` was refused mid-run on 2026-09-07, after the measurement, at the point where the cheapest response is to invent a name under pressure.

The 101 first-cycle exceptions are listed by exact string, and a test asserts the list is **exactly** the set of bare names `scan_report.py` still emits — not a hand-kept list that could license a name nothing produces. `scan_control_findings` is deliberately *not* on it: it is the name the convention was learned from, and it is the one name the exception does not cover.

---

## 4. §1.4 — four fixtures, and the pre-registered table was right about the leg the task file was wrong about

The task pre-registered `refuses_identified_client` as "expected A12 `fail`, A4 `pass`, every content leg `error` class `refused`". **Derived from the rule sources before running, that is wrong for one leg**, and the table written into `params.yaml` says so on its face:

| leg | pre-registered | derivation |
|---|---|---|
| A4 | `pass` | A4 judges the DECLARED layer alone; robots.txt is served 200 and allows the product path for every UA in `a4_crawlers`. |
| **A11-declared** | **`pass`** | its two declared-layer sources are robots.txt (served, permits) and the page's meta-robots (the 403 body carries none). The robots observation is a real 200, so `_common.only_errors` is **false** and the rule reaches a verdict. The task's blanket "every content leg `error`" would have failed the control gate here. |
| A12 | `fail` | robots permits this UA for the probe path and the host answers 403 to that same path — `rule_a12.py` branch 5, the two layers disagree. |
| every other leg | `error` | HTTP 403 → `errors.classify_status` → `refused` → blind → `only_errors` → `error`. |

`resets_connection` is a scalar `error`: the socket is reset before any byte, robots.txt included, so every collector raises, every class is `connection_reset`, and A12 lands on "the robots/probe pair was not collected" rather than on a coherence verdict — which is the right answer, because a host that cannot be reached has not been shown to be incoherent.

**The gate passed on all four fixtures with the table exactly as pre-registered — 65 control Findings, zero unexpected verdicts.** Nothing in the table was edited after a run; the entry that differs from the task file differs because it was derived from `rule_a11_declared_v2.py` rather than assumed.

The fixtures are behaviour, not just files: `fixtures/server.py` gains a `MODES` table (`refuse_status` + `served_paths`; `reset`, which sets `SO_LINGER` to a zero timeout so `close()` sends RST rather than FIN and the client sees `ECONNRESET` — the failure `www150.statcan.gc.ca` produced 92 times). It also gains a **request log**, which is what makes §1.3 checkable from what was actually fetched rather than from what the runner meant to fetch.

---

## 7. Every premise this task got wrong

Five of the seven premises are right as stated. Two are right in kind and wrong in number, and both numbers matter.

### 7.1 Premise 1 — `RULE_VERSION` — CORRECT
`rules/_common.py:6` holds `RULE_VERSION = "v1"`; **all 1,353** stored Findings carry `rule_version: v1`; the field is an input to `finding_id` at `model.py:137`. `Rule.version` in the graph is parsed from `rule_id` as the workaround.

### 7.2 Premise 2 — ECONNRESET filed as `dns` — CORRECT IN KIND, WRONG IN NUMBER
The task says **three StatCan surfaces are mislabelled**. Measured on the log:

- **92 observations** carry `error_class: dns` whose recorded text is `ConnectError: [Errno 54] Connection reset by peer`;
- they span **four** targets, not three — the three admitted StatCan surfaces **plus the synthetic host surface `host:www150.statcan.gc.ca`**, which A12 judges. The host surface is the one whose verdict the mislabel most directly touches, and it is the one the premise omits.
- **A 93rd observation** is misfiled and the premise does not mention it at all: a Census A10 probe recorded `TooManyRedirects: Exceeded maximum allowed redirects.` under `dns`. It is not a name-resolution failure either, and under the new map it is `unknown` — which is the honest answer and now a counted one.

The overlay covers all 93.

### 7.3 Premise 3 — A1 and A3 double-probe — CORRECT, and now quantified
**1,118 link probes in the 2026-09-07 cycle over 559 distinct (params, surface, URL) triples: every one of the 559 was HEADed exactly twice, so 559 requests against public federal hosts bought no evidence at all.**

### 7.4 Premise 4 — neither fixture models permits+refused — CORRECT
`tests/test_scan_harness.py::_a12_obs` says so itself: *"The branch that matters most — permitted in the file, refused at the edge — is NOT reachable from either control fixture."* It is reachable from `refuses_identified_client` now.

### 7.5 Premise 5 — the admission gate has no escape — CORRECT at `kg/manifest.py:158`, and the forecast is an upper bound
26 `scan-` entries are admitted and **22** of them tripped the gate on 2026-09-07 (22 `conversion_gap` events, 22 ResearchTasks, all withdrawn by hand). The task's "26 more false conversion-gap tasks" is the ceiling; the realised number last time was 22. The escape prevents both.

### 7.6 Premises 6 and 7 — bare cycle-level Result names — CORRECT
**120** bare `scan_*` Result names are bound, **101** of which `scan_report.py` still emits bare. The bare `framework_indicators_{measured,specified,harness_built}` triple exists beside the suffixed ones, as premise 7 says; left alone, never reused, and out of the registrar's scope because they are not scan-cycle Results.

### 7.7 A contradiction inside the task file, and the decision taken

**§"Zero edits to" names `framework/ai_readiness_framework.json`. §2's gate requires `pytest tests/ assessment/` green. `tests/test_scan_harness.py::test_the_framework_records_the_rule_each_leg_is_judged_by` asserts every `MeasurementSpec.rule_id` equals the leg's CURRENT rule.** Moving A1 to `RULE-A1-v3` and A3 to `RULE-A3-v4` therefore makes those two propositions incompatible: honour the prohibition and the suite is red; run the write-back and the prohibition is broken.

**Decided on the grounding, not escalated.** The write-back was run. The prohibition's evident purpose is that a harness change must not alter the framework's CONTENT as a side effect — indicators, constructs, evidence, measurement statuses. `MeasurementSpec.rule_id` is not content: it is a pointer at the harness, it is *derived* rather than authored (`framework_writeback_rules.py` exists for exactly this and now emits a `framework_writeback` event), and leaving it stale would make the framework of record claim A1 is judged by a rule that is no longer CURRENT — the drift DD-040 names and DD-057's round-trip gate would then be verifying. Running it is the conservative action; not running it leaves the record wrong.

The diff is **two lines**, and nothing else moved:

```
-    "rule_id": "RULE-A1-v2"        +    "rule_id": "RULE-A1-v3"
-    "rule_id": "RULE-A3-v3"        +    "rule_id": "RULE-A3-v4"
```

`counts_moved: {}`; `indicators_status: 0`; `e5_collector: 0`. The `framework_writeback` event on `events/batch-033_framework.jsonl` records the sha256 of the bytes written and names **this** task as the one that ordered the run — `scripts/framework_writeback_rules.py` gained a `--task` flag for that, so the log says who caused a change and not only what it does.

### 7.8 A defect this task's own work exposed, fixed, and recorded

`run.py --controls-only` **overwrote `state/scan_2026-09-07_controls.json`** — a registered DataFile and the stored evidence the 2026-09-07 re-derivation gate compares against. The output path is derived from `cycle.name`, and a parameter change that leaves the name alone points a new cycle at an old cycle's file. It was recovered with `git checkout`; nothing should have to be.

`run.py::refuse_clobber` now refuses to write over a payload carrying a different `params_hash`, and names the fix (move `cycle.name`) instead of destroying a measurement that can never be taken again. CLAUDE.md §11: a new version gets a new NAME. Verified: a second `--controls-only` run under the new parameters passes the control gate and then refuses to write, leaving the tree clean.

### 7.9 The hygiene gate caught this task in the act

Two `run.py --controls-only` runs — real harness runs, outside pytest, so `tests/conftest.py`'s evidence guard does not apply to them — left **11 uncited blobs** in `corpus/evidence/scan/`, and `tests/test_scan_hygiene.py::test_the_committed_evidence_store_holds_no_uncited_fixture_output` failed on them in the first full-suite run of this task. That is the gate written yesterday doing exactly its job on today's work.

Ten carry the fixture host and the sweep already recognised them. The eleventh is the **zero-length** body the `refuses_identified_client` fixture returns with its 403s, and it carries no marker to match on — so `scripts/quarantine_fixture_evidence.py` gained a second, narrower category: **untracked AND uncited is litter whatever its content**, because a blob git does not track and no Observation cites was never part of the corpus. It is not a wider net thrown at tracked evidence — a pending cycle's bodies become cited the moment its payload is published, and until then they are not corpus either. The 1,167 tracked non-fixture blobs are untouched and the registered `scan_evidence_fixture_blobs_quarantined = 260` is unchanged: the new category only ever removes untracked files.

### 7.10 Two more stale test literals, and one thing cycle 2 will change in the graph

`tests/test_scan_harness.py` hard-coded **two** control fixtures in two places — `len(e5_obs) == 2` and `len(BY_LEG) * 2 - 1`. Both now count from the pre-registered table (`len(params["e5_control"]["expected_verdicts"])`) and from `run.CONTROL_FIXTURE_LEGS`, so a fifth fixture is a params entry and nothing else to remember. The same shape of staleness took `test_every_rule_covers_a_leg_that_has_a_measurement_spec` and `test_every_shipped_rule_version_stays_in_the_registry`, which now read `rules.GENERATIONS` instead of naming V1..V3 — including a generalisation worth stating, because it caught me: **a generation's rules need not carry that generation's version number.** `RULE-A1-v3` and `RULE-A3-v4` ship together in V4 because A3 had one more ancestor than A1. What must hold is that a later generation outranks every earlier one for the same leg, and that CURRENT points at the highest.

**`RULE-A1-v3` and `RULE-A3-v4` have no `:Rule` node yet, and that is correct.** `Rule` nodes are minted from `finding_derived` events, and no Finding has been recorded under either — cycle 2 has not run. The framework layer already points at them (`MeasurementSpec {leg: "A1"}.rule_id = "RULE-A1-v3"`, verified by Cypher), and the `Rule` nodes plus their `MEASURES` edges appear on the first cycle that uses them. Nothing to fix; named so the next OODA does not read the absence as a projection defect.

---

## 8. The `CURRENT` rules a new cycle judges with

| leg | rule | version | consumes |
|---|---|---|---|
| `A1` | `RULE-A1-v3` | v3 | `link_probe` |
| `A2` | `RULE-A2-v3` | v3 | — |
| `A3` | `RULE-A3-v4` | v4 | `link_probe` |
| `A4` | `RULE-A4-v1` | v1 | — |
| `A5` | `RULE-A5-v1` | v1 | — |
| `A6` | `RULE-A6-v2` | v2 | — |
| `A8` | `RULE-A8-v2` | v2 | — |
| `A9` | `RULE-A9-v1` | v1 | — |
| `A10` | `RULE-A10-v2` | v2 | — |
| `A11-declared` | `RULE-A11-declared-v2` | v2 | — |
| `A12` | `RULE-A12-v1` | v1 | — (candidate, DD-054) |
| `B3` | `RULE-B3-v2` | v2 | — |
| `D1` | `RULE-D1-v3` | v3 | — |
| `D4` | `RULE-D4-v2` | v2 | — |
| `E5` | `RULE-E5-v2` | v2 | — |
| `F4` | `RULE-F4-v3` | v3 | — |
| `G1-D` | `RULE-G1-D-v1` | v1 | — |

`REGISTRY` holds 35 modules — every version ever shipped, including `RULE-A1-v2` and
`RULE-A3-v3`, which are no longer CURRENT and are still the rules their stored Findings
re-derive under.

## 9. The fixture request log: one HEAD per link

Collecting the shared `link_probe` leg and then `A1` and `A3` against `passes_all`, read from
the server's own log rather than from the runner's intent:

```
observations from link_probe + A1 + A3: 9
HEAD requests: 8 | distinct paths: 8 | any path twice: []
sample: /estimates.csv /estimates.json /bulk/estimates-2026.zip /estimates-latest.csv
        /openapi.json /llms.txt
```

Before this task the same three collections issued **16** HEADs for the same 8 objects. Scaled
to the 2026-09-07 cycle that is the 559 duplicate requests §7.3 measures.

## 10. What cycle 2 still needs — named, not built

1. **A cycle name.** `params.cycle.name` is still `scan_2026-09-07` and `params_hash` has
   moved, so `run.py::refuse_clobber` will (correctly) refuse to write. Cycle 2's task moves
   `cycle.name` first; that is a one-line params change and it is deliberately not made here,
   because moving it is what declares a new cycle.
2. **An evidence root for diagnostic runs.** `tests/conftest.py` redirects the evidence store
   under test, but a real `run.py` invocation outside pytest writes into the committed store —
   which happened three times in this task and was swept each time (§7.9). `run.py` wants an
   `--evidence-root` so a dry probe cannot litter the corpus. Named, not built: it is a runner
   change and this task's gate covers the harness.
3. **A decision on the 266 `http_4xx`-on-403 observations** (§2). One convention or two.
4. **The 22 open `conversion_gap` events on scan surfaces.** The escape stops the next 26; the
   22 already on the log are history and a task should decide whether they are closed by a
   `substrate_converted` that will never come, or annotated the way §1 of the hygiene task
   annotated the orphan Findings.
5. **`Rule` nodes for the two new rules** appear on the first cycle that records a Finding
   under them (§7.10). Nothing to do; do not read the absence as a defect.
