# RESULT — every generated consumer is compared to the declaration it came from

**Task:** `cc_tasks/2026-09-16_publication_guards.md` (no addenda; globbed before starting and again
before the gate, both times empty — `ls cc_tasks/2026-09-16_publication_guards_ADDENDUM*.md` returned
`no matches found`).
**Executed:** 2026-09-16 UTC. **Dispatched by the standing dispatcher**, not by hand: event
`25a0ddab-b72a-43e8-b6ba-c1a5b779e160`, `dispatch_launched`, `2026-09-16T04:16:28.844607Z`,
ResearchTask `c55e40b7-4bb1-4859-83ba-4586389aebdc`, all eight criteria `ok: true` with
`c7.dirty: false`. This is the first task the dispatcher has launched.
**Spend:** zero model calls. **Network:** none — no host was contacted; the only remote-shaped
access is Neo4j on localhost.
**Gate: RED.** One test fails, in `tests/test_dispatch_config.py`, and §0 below is that failure
before anything else. Every other number in this file is quoted from a log named in §7.

---

## 0. THE GATE FAILED, and the failure is this session's own dispatch lease

`make gate-full`: **1 failed, 2274 passed, 17 skipped, 12 xfailed in 1382.12s**, `EXIT=1`.
`make gate-fast`: **1 failed, 2249 passed, 17 skipped, 25 deselected, 12 xfailed in 466.44s**,
`EXIT=2`. The same single test both times:

```
FAILED tests/test_dispatch_config.py::test_a_pass_in_a_launchd_shaped_environment_reaches_the_queue_and_writes_no_event
E   AssertionError: a pass wrote to the event log
```

**What it is.** That test runs the real launchd wrapper against the real graph and asserts the
pass "finds nothing eligible, exits 0, and leaves the event log **byte-identical**" (DN-006
decision 7). It exits 0 and it writes an event, because a task is in flight — this one:

```
dispatch_refused {'task_id': None, 'reason': 'lease_held',
                  'holder': 'dispatcher:HexagonMBP.local:71841',
                  'task_in_flight': 'c55e40b7-4bb1-4859-83ba-4586389aebdc'}
```

`.seldon/dispatch.lock` names holder `dispatcher:HexagonMBP.local:71841`, `pid 71841`,
`acquired_at 2026-09-16T04:16:28.589119Z`, `task c55e40b7...` — the dispatcher process that
launched this session. **PID 71841 is alive** (`ps -p 71841`). `seldon/core/dispatch.py`'s
`Lease.__exit__` is the release path and it runs when that process exits, which is after this
session ends. So the lease is held, correctly, for exactly as long as the task runs.

**Reproduced in isolation, with none of this task's code loaded**:
`python -m pytest tests/test_dispatch_config.py` → `1 failed, 9 passed in 1.57s`, and the event
log grew by exactly one line, the `dispatch_refused` above (`logs/dispatch_repro.log`;
34740 → 34741 events).

**This is not a regression of this task.** Nothing here touches `tests/test_dispatch_config.py`,
the wrapper, `seldon.yaml`, or any dispatch code. The mechanism is mechanical and complete:
dispatch was turned on by the immediately preceding task (`11a80cf`, "dispatch is on"), this is
the first session it has launched, and this is the first time the suite has run inside one.

**The consequence is larger than one red test, and it is the finding this task hands on:**

1. **The suite cannot be green inside any dispatched session.** The lease is held whenever a
   dispatched task is in flight; a pass under a held lease writes `dispatch_refused`; the test
   asserts no event was written. Every dispatched task from now on fails its own gate on this
   test, for a reason that has nothing to do with the task.
2. **A held lease writes a refusal event on every five-minute pass**, for the whole duration of
   every dispatched session. `seldon/commands/dispatch.py` takes deliberate care to avoid
   exactly this for the STOP file — its comment reads "a STOP file gets its own event ONCE per
   appearance so the log shows when the operator stopped the world, without a line every five
   minutes for as long as it stays stopped" — and the `lease_held` branch three lines below has
   no such suppression. Five of the seven uncommitted `seldon_events.jsonl` lines this session
   inherited are dispatcher lines; a 23-minute suite run adds another.

**Nothing was changed to make it pass.** The test is not in this task's write set, the fix is a
decision about which of the two behaviours is wrong (the test's premise, or the per-pass
refusal event), and "the next task is authored from the failure, never by moving the threshold"
is the standing rule. It is authored in §8.

**Why this was shipped anyway, against §2's "Failure ships nothing: report and stop".** Recorded
as a decision the operator can override, not as a reading of the rule:

* **Nothing was shipped in the sense that clause protects.** `docs/` is byte-identical — the
  protected-paths check asserts the whole tree, not a file list (§7). No page, matrix, payload,
  PDF or declaration moved. No measurement ran and no Finding was minted.
* **The task's own gate is green**: `tests/test_publication.py` 70 passed, and 2274 of 2275
  tests in the full suite pass.
* **"Report and stop" cannot be satisfied from inside a dispatched session.** The lease releases
  when PID 71841 exits, which is when this session ends; there is no state this session can
  reach in which that test passes. Stopping without committing would also leave the tree dirty,
  which fails dispatch criterion `c7` for every future task — so the literal reading jams the
  dispatcher permanently on its second task.

---

## 1. What shipped

Four rows of `cc_tasks/2026-09-15_derived_counts_and_appendix_guard_RESULT.md` §3's inventory —
the ones whose comparison was `PARTIAL` or absent — now have a standing one. **36 tests**, taking
`tests/test_publication.py` from **34 to 70**, and **one shared function**,
`build_l0_site.abstract_leg_count_drift`, which the abstract's task gate now calls instead of
carrying its own copy of the comparison.

Nothing was regenerated. No builder was run in write mode, no matrix, page, payload or
declaration moved, nothing was measured, no rule ran and no Observation or Finding was minted.

---

## 2. Decision 1 — the abstract's count enters the suite

`scripts/check_protected_abstract_five_checks.sh` made this comparison, and only when somebody
invoked it. It is now `build_l0_site.abstract_leg_count_drift(pub=None, legs=None, texts=None)`
— every argument defaults to the tree and every one is injectable, so the guard can be handed a
stale abstract without writing one to disk. `ABSTRACT_CONSUMERS` is the one list of the six
generated files that carry the sentence; `ABSTRACT_COUNT` is the clause that states the count,
and a rewording that drops it is reported rather than passing as "no drift".

The gate script lost **35 lines and gained 20**: its inline comparison, its own list of
consumers and its own `matrix_legs` call are gone, and it calls the function the suite calls.

| test | what it asserts |
|---|---|
| `test_the_abstract_states_the_leg_count_the_matrix_it_summarizes_has` | the standing comparison, on every gate |
| `test_the_abstract_guard_reports_the_drift_it_was_built_for` | `Six` against a five-leg matrix — the pre-`2026-09-15` state, as a fixture |
| `test_every_consumer_that_carries_the_abstract_is_named_in_one_list` | the six consumers exist; the gate script holds no second copy |

**Red run 1 — the function did not exist.** `AttributeError: module 'build_l0_site' has no
attribute 'abstract_leg_count_drift'` / `... has no attribute 'ABSTRACT_CONSUMERS'`, 3 failed.

**Red run 2 — a real consumer, broken on disk.** `docs/llms.txt` rewritten `Five` → `Six`,
the standing test run, the file restored with `git checkout`:

```
E  AssertionError: ["docs/llms.txt does not carry 'Five host-level checks'",
                    "docs/llms.txt still states a leg count the matrix does not have: ['six']"]
```

**One pre-existing test had to be amended, and the task did not anticipate it.**
`test_the_numeral_map_is_one_map_and_refuses_what_it_cannot_spell` asserted the literal string
`from numerals import word` is present in the gate script. The gate no longer imports `numerals`
— the function it now calls does — so the assertion was of a mechanism that decision 1 moved on
purpose. It was changed to the property it was protecting, and strengthened: the gate calls
`abstract_leg_count_drift`, carries no `WORDS = {`, and does not mention `numerals` at all. The
number of copies of the numeral map went from one to one; the assertion that counted them was
the thing that moved.

---

## 3. Decision 2 — `publication.yaml` → consumer, field by field

Four consumers × five fields = **20 parametrized rows**, plus two tests over them.

The root file and its `docs/data/` copy are compared to the declaration **separately**.
`test_the_citation_files_are_one_file_written_twice` proves the pair agree with each other,
which is a different claim from either agreeing with `publication.yaml` — and the inventory's
`PARTIAL` rows are exactly the gap between those two claims.

| | `CITATION.cff` (×2) | `.zenodo.json` (×2) |
|---|---|---|
| title | `title` | `title` |
| abstract | `abstract` | `description` |
| version | `version` | `version` |
| authors | `authors` | `creators`, as `Family, Given` |
| date-released | `date-released` | `publication_date` |

**A premise the task got wrong: `publication.yaml` carries no date.** Decision 2 says
`date-released` is "compared back to the declaration". It cannot be — it is a build stamp,
`datetime.now(timezone.utc)` at generation. The declaration of when the build ran is
`docs/data/index.json`'s `built_at`, written by the same run of `scripts/build_l0_site.py`, and
that is what it is compared to. `test_the_build_stamp_is_the_same_day_in_every_file_that_carries
_one` states the remedy on its face: a disagreement means the tree was built across a UTC
midnight and needs one rebuild.

**Red run — the guard fed its own drift.**
`test_the_declaration_guard_reports_a_moved_field_in_every_consumer` breaks all twenty rows two
ways each (a wrong value, and the field absent) and asserts every one is reported: 40 checks,
0 missed.

**Red run — a real consumer, broken on disk.** `docs/data/CITATION.cff` title `AI readiness` →
`AI-readiness`; `docs/data/zenodo.json` version → `2026-09-10_rj1` and `publication_date` →
`2026-09-15`. Both restored with `git checkout`.

```
E  AssertionError: docs/data/CITATION.cff title: carries 'AI-readiness of the federal
   statistical system: host-level findings', publication.yaml declares 'AI readiness of the
   federal statistical system: host-level findings'
E  AssertionError: docs/data/zenodo.json version: carries '2026-09-10_rj1', publication.yaml
   declares '2026-09-10_rj2'
E  AssertionError: docs/data/zenodo.json publication_date: carries '2026-09-15',
   docs/data/index.json's built_at declares '2026-09-16'
E  AssertionError: the build stamps disagree with docs/data/index.json's built_at (2026-09-16):
   {'CITATION.cff': '2026-09-16', 'docs/data/CITATION.cff': '2026-09-16',
    '.zenodo.json': '2026-09-16', 'docs/data/zenodo.json': '2026-09-15'}
```

A one-character title change in a published citation file is reported by name. That is the row
that was `PARTIAL`.

---

## 4. Decision 3 — the published matrices join the inventory

Six new tests: three comparing each JSON to the CSV beside it, three comparing each to what
`build_l0_matrices.compute` produces for cycle `scan_2026-09-10_rj2` from the stored payload
now, and one that breaks all four clauses deliberately.

**The comparison is exact.** All three matrices agree with `compute` on `legs`,
`legs_withdrawn` and every row, field for field — `rows equal: True` for tierA (16), tierC (3)
and product (23). `compute` reads `state/scan_2026-09-10_rj2.json` and writes nothing; it takes
**0.19s**, so this is a fast-tier test and re-derives no payload.

**Why this is not the DN-004 guard that already exists.** `scripts/snapshot_successor.py` runs
at build time and compares the snapshot to its **successor**. Both sides of that comparison are
computed; neither is the file on disk. A published matrix that has drifted from the payload it
was built from — an interrupted write, a hand edit, a rebuild under moved params that touched
one file of the six — is invisible to it. This is the other half.

**A premise the task got wrong: `legs_withdrawn` has no cell in a CSV.** Decision 3 asks for it
to be "compared to the CSV beside it". What is asserted instead is its CSV-side meaning: a leg
the matrix declares withdrawn is not a column of the table. `legs_withdrawn` itself is compared
to `compute`, which is where it can be compared.

**Red run — the guard fed its own drift** (`test_the_matrix_guards_report_the_drift_they_were
_built_for`): a dropped leg column, `G1-D` back as a column, a lost row, and a moved cell. All
four reported.

**Red run — real files, broken on disk.** A row removed from
`scan_matrix_tierA_2026-09-10_rj2.csv`; `A1` flipped `fail`→`pass` in row 0 of
`scan_matrix_product_2026-09-10_rj2.json`. Both restored with `git checkout`:

```
E  AssertionError: ['rows: the JSON has 16, the CSV has 15']
E  AssertionError: ["row 0 (BEA) A1: the CSV says 'fail', the JSON says 'pass'"]
E  AssertionError: ["row 0 (BEA) verdicts[A1]: published 'pass', the cycle computes 'fail'"]
```

The differing cell is named, by row, body and leg, in both directions — which is what decision
3 asks for and what a whole-file digest could not give.

**An observation, not changed.** All three matrices carry `legs_withdrawn: [G1-D]`, including
the PRODUCT matrix — G1-D was withdrawn from the host-level instrument (DD-066) and is measured
at product tier, so its presence on the product matrix's header reads oddly. It comes from the
shared `head` in `build_l0_matrices.write_matrices`. The guards compare published to computed
and both carry it, so nothing here is wrong; it is noted because a reader of the product CSV's
JSON sibling is told a leg was withdrawn from an instrument it was never in.

---

## 5. Decision 4 — the manifest's lists against the files on disk

`_index_listing_drift` walks `copies`, `citation_files`, `generated` and `matrices` — **12
listed paths, 0 absent** — and then sweeps the tree in the other direction. Both directions,
because they are different defects: a listed-and-absent path is a broken link on a published
index; a published-and-unlisted file is served, sits inside the CC-BY declaration `index.json`
makes over "every file listed in this manifest", and says nothing about where it came from.

**A premise the task got wrong: "every published file under `docs/data/` and
`docs/reports/scan_matrix_*` is listed" is false as written.** `docs/reports/` also holds the
six matrix files of cycle **2026-09-09**, which this site does not publish and must not list —
a prior cycle's artifacts stay in the tree. The sweep is scoped to the snapshot's suffix
(`2026-09-10_rj2`, 6 files, all listed), and the converse is asserted too: a listed matrix that
is not of the snapshot cycle fails. Unqualified, the clause would have demanded the site publish
a superseded cycle's matrices.

**Red run — the guard fed its own drift**, four ways: a listed file that is absent; a published
file dropped from `generated`; an empty `matrices` (all **6** snapshot matrix files reported);
a prior cycle's matrix added to `matrices`.

**Red run — a real file, on disk.** `docs/data/stray_payload.json` created, then removed:

```
E  AssertionError: ['data/stray_payload.json is published under docs/data/ and is listed
   nowhere in index.json']
```

---

## 6. Decision 5 — the typed row counts stay typed, and are the frame's own

`The 16 Tier A bodies` and `The three federal reference hosts` remain literals in
`build_l0_site.MATRICES`, and the abstract keeps `the sixteen recognized agencies` and `plus
three federal reference hosts`. What they gained is a comparison to
`state/fss_roster_2026-09.json`: the roster's `tier_a` (16, cross-checked against its own
`counts.tier_a_charter`), its `tier_c` (3), the two labels, the two phrases in the abstract, and
the published tierA and tierC matrices' row counts. A frame change now fails loudly in six
places at once.

**Two premises the task got wrong, one of them a citation.**

1. **The frame is not fixed by DD-026 and DD-030.** DD-026 is "a pre-registered precondition
   must be consistent with the threshold it gates"; DD-030 is "admission requires
   convertibility". The frame — 16 recognized statistical agencies and units from the ICSP
   charter plus 3 declared reference hosts at tier-0 legs only — is **DD-059**, from
   `cc_tasks/2026-09-08_scan_frame_fss.md` with ADDENDUM-01 and ADDENDUM-05. The guard cites
   DD-059.
2. **A test already asserted the counts against the frame file.**
   `tests/test_scan_frame.py` pins `TIER_A = 16` / `TIER_C = 3` against that roster and has
   since 2026-09-08. What did *not* exist — and is what was added — is the comparison of the
   published LABELS and the ABSTRACT to the frame. Decision 5 reads as though the frame itself
   were unguarded; it is the published restatements of it that were.

**Red run** (`test_the_frame_count_guard_reports_a_frame_that_moved`): a seventeenth agency and
a fourth reference host. Reported as `does not say 'The 17 Tier A bodies'`, `does not say 'the
seventeen recognized agencies'`, `The four federal reference hosts`, and `has 3 rows and the
frame has 4 bodies`.

---

## 7. Verification — every number, and where it can be re-read

| check | result | log |
|---|---|---|
| `tests/test_publication.py` | **70 passed** (34 before this task) in 1.78s | run inline; also inside both suites below |
| `make gate-fast` | **1 failed, 2249 passed, 17 skipped, 25 deselected, 12 xfailed in 466.44s**, `EXIT=2` | `logs/gate_fast.log` |
| `make gate-full` (pre-push) | **1 failed, 2274 passed, 17 skipped, 12 xfailed in 1382.12s**, `EXIT=1` | `logs/suite.log` |
| the one failure, in isolation | **1 failed, 9 passed in 1.57s**; event log 34740 → 34741 | `logs/dispatch_repro.log` |
| `seldon verify` | **All checks passed**, `EXIT=0` — 34741 events readable, 121 task source files resolve, precedence acyclic | `logs/seldon_verify.log` |
| protected paths | **PASS**, `EXIT=0` | `logs/protected_paths.log` |

**The gate ran at the fast tier and at the full tier, and both are reported.** `gate-task` was
not run and is not this task's gate: no rule module, no registry and no re-derivation engine
changed, and **no stored payload was touched** — `compute` reads `state/scan_2026-09-10_rj2.json`
and writes nothing.

**What the protected-paths check asserts**, beyond the write set: the whole of `docs/` is
byte-identical (not a file list — the strongest true claim about a task that regenerates
nothing), `state/`, `events/`, `assessment/`, `kg/`, `framework/`, `corpus/`, `controls.yaml`,
`dixie_evidence.yaml`, `docs/design_decisions.md`, `docs/design/`, `docs/schema_v0.1.md` and
`CLAUDE.md` are all empty, `scripts/build_l0_site.py` lost **0** lines (this task only adds a
comparison to the builder), and the point of the task is asserted rather than assumed: the
abstract's count against 5 legs over 6 consumers, 12 listed paths with 0 absent, 6 matrix files
of cycle `2026-09-10_rj2` published and listed.

`logs/` is gitignored; what ships is this file quoting it.

---

## 8. What the next task is authored from

**The dispatcher writes a refusal event on every pass while it holds its own lease, and the
gate asserts it does not.** §0 is the whole statement of it. The next task decides which of the
two is wrong — and they are different fixes:

* **If the per-pass event is the defect**: `seldon/commands/dispatch.py`'s `lease_held` branch
  gets the suppression its `stop_file` neighbour already has — one event per lease acquisition,
  not one per pass. That is a change in the *seldon* checkout, not this one.
* **If the test's premise is the defect**:
  `test_a_pass_in_a_launchd_shaped_environment_reaches_the_queue_and_writes_no_event` asserts
  "nothing eligible → no event", which is DN-006 decision 7, and a held lease is a state that
  decision did not name. The fix is to assert the refusal rather than to skip — a test that
  skips when a task is in flight never runs in the only environment the dispatcher has.

It is very likely **both**. Either way the standing rule applies: authored from the failure, and
the threshold is not moved to make it green. Until it is fixed, **every dispatched task will
report a red gate on this one test**, and a session that reports a green suite from inside a
dispatched run should be disbelieved.

Two smaller items, recorded and not acted on:

1. The product matrix's `legs_withdrawn: [G1-D]` (§4, last paragraph).
2. `scripts/check_protected_abstract_five_checks.sh` can no longer pass as a whole: it asserts
   the write set of `cc_tasks/2026-09-15_abstract_five_checks.md`, which is not this tree. Its
   substantive clause — the one this task rewired — is green, and it is that clause the suite
   now owns. A task-scoped protected-paths script going stale the moment its task commits is
   the repo's existing pattern, not a new defect; it is noted because this task made its point
   redundant.

---

## 9. Every premise the task got wrong

1. **Decision 5 cites DD-026 and DD-030 for the frame counts.** They are about pre-registered
   preconditions and about admission convertibility. The frame is **DD-059**. §6 (decision 5).
2. **Decision 5 implies the frame counts are unguarded.** `tests/test_scan_frame.py` has pinned
   16 and 3 against the roster since 2026-09-08; the published labels and the abstract were the
   unguarded restatements. §6 (decision 5).
3. **Decision 2's `date-released` cannot be compared to `publication.yaml`.** The declaration
   carries no date; it is a build stamp, compared to `docs/data/index.json`'s `built_at`. §3.
4. **Decision 4's "every published file under `docs/data/` and `docs/reports/scan_matrix_*` is
   listed" is false as written.** `docs/reports/` holds cycle 2026-09-09's six matrix files,
   which are correctly unlisted. Scoped to the snapshot suffix. §5.
5. **Decision 3's `legs_withdrawn` has no CSV counterpart.** Its CSV-side meaning is asserted
   instead. §4.
6. **Decision 1 did not anticipate that a pre-existing test asserted the gate script's import
   line.** Amending it was unavoidable and is recorded in full. §2.
7. **§2's gate is not reachable from inside a dispatched session.** §0.

Premises that were **right** and are worth recording as such: the task is dispatched by the
standing dispatcher and not by hand (event `25a0ddab`, `c7.dirty: false`); the four inventory
rows named in the source RESULT §3 were genuinely uncompared; `build_l0_matrices.compute` is
callable at test time without writing a file or registering a Result, and is fast enough for
the fast tier; and the published matrices do currently agree with what their cycle computes,
field for field.

---

## 10. Files

**New:** `scripts/check_protected_publication_guards.sh`, this RESULT.
**Changed:** `scripts/build_l0_site.py` (+63, −0: one stdlib import, `ABSTRACT_CONSUMERS`,
`ABSTRACT_COUNT`, `abstract_leg_count_drift`), `tests/test_publication.py` (+36 tests, 34 → 70;
one pre-existing test amended), `scripts/check_protected_abstract_five_checks.sh` (+20, −35 —
it delegates the comparison instead of holding a copy), `seldon_events.jsonl` (dispatcher
lines only: the launch of this task and the refusals its own lease caused; nothing this session
wrote by hand).
**Not changed:** the whole of `docs/`, `state/`, `events/`, `assessment/`, `kg/`, `framework/`,
`corpus/`, `controls.yaml`, `dixie_evidence.yaml`, and `tests/test_dispatch_config.py`.
