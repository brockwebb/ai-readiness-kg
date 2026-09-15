# RESULT — two standing guards: nothing judged stays off the log, and the report says its snapshot is superseded

**Task:** `cc_tasks/2026-09-14_standing_guards.md`, implementing
`docs/design/2026-09-14_DN-004_report_snapshot_policy.md` decisions 2 and 3 and DN-003
decision 6, under DD-001 and DD-065.
**No addendum exists** — `cc_tasks/2026-09-14_standing_guards_ADDENDUM*.md` globbed before
starting and again before §3, both times `no matches found`
(`logs/sg_addendum_glob_pre_s3.log`).
**Date:** 2026-09-14. **Spend: zero model calls. Network: none** — no host was contacted, no
evidence was promoted, **not one event was written to the log** and no Result moved. The only
remote operation is the `git push` §4 orders.

## THE GATE: PASS

| clause (§3) | result | log |
|---|---|---|
| §1 stop — decision 3's comparison finds no published number moved under rj3 | **PASS — 0 moved**, 41 of 41 tagged Results recomputed and compared, 42 matrix rows, 3 fragments byte-identical | `logs/sg_s1_successor.log` |
| decision 1's guard green across `state/` | **PASS — 14 of 14 re-judged, 6 of 6 measured**; the task says 8 measured and there are 6 plus 3 controls-only (§3a) | `logs/sg_newtests.log`, `logs/sg_guards.log` |
| the supersession line present in the markdown | **PASS** — one line, quoted below | `logs/sg_pdf.log` |
| the supersession line present in the PDF | **PASS** — whole sentence, numerals unbroken | `logs/sg_newtests.log` |
| the line equals the query's answer at build time | **PASS** — asserted character for character against `successor_info` run live | `logs/sg_newtests.log` |
| PDF numeral-multiset gate | **PASS** | `logs/sg_newtests.log` |
| bare-numeral lint over the built body | **PASS — 0**, and no `numerals-exempt` region was opened for the new line (§2) | `logs/sg_report_check3.log` |
| `--project-once` fixture test | **PASS** — two cycles, identical statement sequence, 1 projection against 2 | `logs/sg_newtests.log` |
| page counts unmoved or re-registered | **PASS — unmoved**, total 14 / prose 6, which is what `l0_report_pages_{total,prose}_2026-09-11` are bound at; nothing re-registered | `logs/sg_pdf.log`, `logs/sg_protected.log` |
| `make guards` | **PASS — 50 passed, 21.55 s** (was 25; the two new files are the other 25) | `logs/sg_guards.log` |
| `make gate-task` | **PASS — 2,180 passed, 17 skipped, 25 deselected, 12 xfailed, 398.81 s**, then 22 of 22 re-derive in 7.20 s | `logs/sg_gate_task.log` |
| `make gate-full` (detached, logged, polled to EXIT) | **PASS — 2,205 passed, 17 skipped, 12 xfailed, 1,294.04 s (21:34)** | `logs/suite.log` |
| `seldon verify` | **PASS — all checks passed** | `logs/sg_verify.log` |
| protected paths | **PASS** | `logs/sg_protected.log` |

Every log carries its own `EXIT=0` and all of them were written before this file was.

## 1. The supersession line, as it renders

In `docs/reports/2026-09_fss_ai_readiness_L0.md`, appended to the generated version block:

> **Standing.** This snapshot has been superseded on the event log by `scan_2026-09-10_rj3`,
> generation 3 of this cycle, which re-judged the same evidence: 739 of this snapshot's 739
> findings have a successor, 0 of them move a verdict and 3 change only the sentence that
> explains one. No number this report publishes differs under that successor, which is why the
> report is not re-snapshotted on it (`DN-004 decision 1`); the build refuses if that ever
> stops being true.

and in the PDF, identically, with pandoc's smart apostrophe and the backticks rendered away.
Every numeral in it is an answer `snapshot_successor.successor_info` gave on this build: 739,
739, 0, 3 and the generation. Nothing is typed, and
`test_the_lines_numerals_all_came_from_the_graph` asserts exactly that — strip the backticked
identifiers and what remains must be a subset of the query's own answers.

`docs/data/results_tagged.json` carries the same facts as fields (`snapshot_standing`,
`successor_moves_no_published_number`, `successor_comparison`) from the same query, and
`test_results_tagged_carries_the_same_fields_as_the_line` asserts the file and the graph agree
key by key.

## 2. Decision 3's comparison, and why it is a refusal rather than a check

`scripts/snapshot_successor.py` is the module. Before a line of the report is rendered, and
before the site writes `results_tagged.json`, it compares the snapshot with its successor on
three fronts, because the report publishes its numbers in three shapes:

| what | how many | moved |
|---|---|---|
| tagged Results carrying the snapshot's cycle suffix, recomputed under `scan_2026-09-10_rj3` | **41 of 41** | **0** |
| published matrix cells — three matrices, every verdict and every published non-provenance column | **42 rows** across tierA, tierC and product | **0** |
| the three rendered matrix fragments the report INCLUDES, byte-compared | **3** | **0** |

**`uncovered` refuses as loudly as `moved` does, and that is the load-bearing part.** A tagged
Result of this cycle that the recomputation does not produce is a number the comparison cannot
speak for; reporting "nothing moved" over the subset it happened to understand is the exact
shape of a gate that passes by not looking. Today `uncovered` is empty and
`recomputed_and_compared == tagged_results_on_this_cycle == 41`, asserted three ways in
`test_the_comparison_covers_every_tagged_result_of_the_snapshot_cycle`.

Thirty-eight of the 41 come from `build_l0_matrices.compute`; the other three
(`scan_findings`, `scan_a5_fail_offroster_sitemap`,
`scan_refusal_consecutive_measurements`) are recomputed by the functions that **registered**
them, in `register_l0_report_results.py` and the payload itself, so the comparison cannot
disagree with the registrar about what a metric means.

The refusal names the numbers, names the successor, and names the route out — move
`snapshot_cycle` in `publication.yaml`, rebuild the matrices, register that cycle's Results,
which is a report revision under DN-002. It is not fixed by rebuilding, and the message says
so. `test_a_moved_number_refuses_and_names_it` and `test_an_uncovered_tagged_result_refuses_too`
are the red halves, planted rather than produced: producing a real move means re-judging a
cycle into a different verdict, and a guard testable only by moving a real number is a guard
nobody tests.

### The refactor decision 3 needed, and the defect it exposed

`scripts/build_l0_matrices.py` gained `compute(cycle)` and `write_matrices(c, out_dir, gen_dir)`;
`main` is now those two plus the registrar. The comparison needs a cycle's matrices and Result
values **without writing a file or registering a Result**, and nothing in that script could do
it: `--dry-run` printed its summary *after* `write_pair` had already written all six matrix
files and both fragments into the published tree, and returned before the Result values were
computed at all. A comparison built on it would have overwritten the snapshot's matrices with
the successor's in order to find out whether they differed. `--dry-run` now writes nothing.

The refactor is verified as a byte-for-byte no-op: `compute` + `write_matrices` for
`scan_2026-09-10_rj2` into a temporary tree reproduces all **11** published files — six matrix
files and five fragments — byte-identically, and all **138** Result values it computes match
what the registry holds, 0 moved and 0 absent. `test_computing_a_cycle_writes_nothing` and
`test_writing_into_a_temporary_tree_restores_the_published_one` hold both properties standing,
including that the module globals are restored on the way out of a **failed** write — without
that `finally`, one failed comparison would leave the writer pointed at a deleted temporary
directory and the next build would publish into nowhere.

## 3. Every premise the task or DN-004 got wrong

**(a) "8 of 8 measured" — there are six measured payloads, three controls-only, and they are
not one question.** `state/` holds 23 payloads carrying `findings_detail`: 14 re-judged, 6
measured (`scan_smoke_2026-09-06`, `scan_2026-09-07`, `scan_2026-09-07b`, `scan_2026-09-09`,
`scan_2026-09-10`, `self_2026-09-13`) and 3 **controls-only**
(`scan_controls_2026-09-06`, `scan_2026-09-07_controls`, `scan_2026-09-07b_controls`). The
eight is `PRIOR_CYCLES`'s count of non-re-judged entries, and `PRIOR_CYCLES` is a re-derivation
set, not a publication set: it holds 22 of the 23 and counts the controls among its eight.

The controls-only payloads' Observations are **deliberately** not on the log — 2 of 91, 4 of
152 and 2 of 91 — because they are loopback fixtures measuring the harness, not evidence about
a federal surface, which is the same reason `publish.project` counts control observations
apart. Asserting them the way decision 1 asserts a measured cycle would have made the guard red
on day one and invited exactly the retune a failed gate must never get. So the guard says three
kinds and the controls-only exemption is a **closed, named set, asserted to be exactly those
three and asserted to carry no Finding at all** — otherwise "controls-only" becomes the label
under which a real judgement goes unpublished.

**(b) "attributed to it by `Finding.cycle` ... passes today at 14 of 14" — it passes at 12 of
14.** `scan_2026-09-07_rj1` and `scan_2026-09-07b_rj1` were published on 2026-09-08, before
DN-003 put `cycle` on the event; the graph carries **0** attributed Findings for either, and
the previous RESULT's §6 says why it must stay that way — `Finding.cycle` is null for every
pre-DN-003 event and is deliberately not backfilled from `state/`, because a property invented
at projection time out of a file beside the log is the convention DN-003 decision 3 replaced
with an edge. The guard therefore asserts the attribution over the twelve and exempts the two
as a **closed, named set that may only shrink**, and it exempts them from `Finding.cycle` and
from **nothing else**: both are on the log in full and all 756 of their Findings carry a
`SUPERSEDES` edge, which `test_the_two_pre_dn003_cycles_are_linked_even_though_they_are_not_attributed`
asserts, along with the condition that would eject them from the exemption.

**(c) "generation 10" — the graph holds 3, and cannot hold 10.** Decision 2 asks the line to
carry "generation 10". That is the project-wide count of re-judgement *runs*, a RESULT-title
convention (`2026-09-13_rule_a12_v3_RESULT.md` is titled "generation 10"), and nothing in the
graph records it: generation 10 produced cycle-generations 3, 4, 3 and 3 across four cycles, so
it is not recoverable from any Finding. `Finding.generation` is the cycle's OWN generation —
how many times *this* cycle has been judged — and for `scan_2026-09-10_rj3` it is **3**. DN-004
decision 2 requires the line to be generated from a query with nothing typed; inventing a
project-wide generation to satisfy the number in the task would have been the typed value that
requirement exists to forbid. The line says 3 and names what 3 counts.

**(d) "scoped out of the bare-numeral lint like the matrices" — they needed no scoping.** The
matrices are exempt because they are table rows. The generated counts are wrapped in
`build_l0_report`'s own value markers — the ones every resolved `{{result:...}}` already gets,
stripped before the file is written — so `_mask` blanks them and the lint sees no numeral. That
is strictly narrower than a `numerals-exempt` region, which would have exempted the whole
paragraph including anything a later edit put in it;
`test_the_bare_numeral_lint_passes_over_the_version_block_carrying_the_line` asserts both the
clean lint and the absence of such a region.

Two things in the line genuinely were not numbers from the graph and were dealt with as what
they are, not swallowed:

* **`DN` joined the exemption class that already reads "a numbered decision."** The entry
  covered `DD|AD|PL|RFC`; design notes are numbered decisions and simply did not exist when the
  list was written — the first is 2026-09-12, the list is 2026-09-09. Widening a class the
  entry already names is not the move the docstring forbids, which is adding a pattern to
  swallow a measurement.
* **"decision 1" is inside the backticks with `DN-004`.** `DN-004` alone left the lint staring
  at a bare `1`. The version block's own stated rule is that every identifier in it is
  backticked because the numbers in that paragraph are addresses, not findings; the whole
  address goes in the ticks.

**(e) Not a premise of the task's — a premise of this session's, and it was wrong.** Mid-run
this session queried the graph for the task's ResearchTask, matched on `t.name CONTAINS
"standing_guards"`, got nothing, and concluded the Desktop session had never registered it. It
had: the node is named **`standing guards`**, with a space, and its `source_file` is the path.
The node existed as `proposed`, created by `desktop`, throughout; `seldon cc register` refused
to duplicate it and `seldon cc complete` walked that same node to `completed`. The lesson is
this repo's own (CLAUDE.md §"verify state-words against the machine", inverted): an absence read
off one field of one query is not an absence, and "no prior art found" is a claim that has to
show the search — which this one, shown, fails.

**(f) `state/scan_2026-09-07b_rj2.json` is untouched**, per decision 5. The guard keys every
payload by its **file stem** for exactly that reason: keying on the `cycle` field would collapse
two judgements of cycle 2 into one entry and hide whichever of them was missing.

## 4. Decision 4: `--project-once`, and how "the same graph" is actually asserted

`scripts/publish_rejudgements.py --project-once` projects once after the last cycle instead of
after each. The per-cycle default stands: for a live cadence the graph should never be a
generation behind the log even for the length of a run, and `--project-once` is for a
**backlog**, where the intermediate states are ones nobody reads and every one of them is
discarded by the next reset. `--no-project` and `--project-once` together are refused, and the
record carries `projection_mode` and `projections_run`.

**The two-cycle fixture compares the graph, not the runner.** A real comparison of two live
projections would mean two full replays at about sixteen minutes each and would reset the live
graph twice inside a test. Instead the fixture — a measured cycle and two generations of
re-judgement over it, in a throwaway `state/` and a throwaway log — is published both ways with
a **recording Neo4j session**, and what is compared is the full ordered sequence of statements
`project()` issues, parameters included. That sequence *is* the end-state graph, because
`project()` opens by deleting every scan-schema label and rebuilds from the whole log. The
per-cycle run issues the once-run's sequence as its tail (`calls[-n:] == once_calls`), the logs
are equal, and the projection counts are 2 against 1. Two supporting assertions keep the
comparison honest rather than convenient: `project()` really is reset-and-replay (its first
statement is the `DETACH DELETE` over the labels), and it reads neither `event_id` nor
`timestamp` — the two fields the log comparison drops because a uuid4 and a wall clock differ
between runs by construction — asserted from the source by AST.

## 5. What changed

**Code.** `scripts/snapshot_successor.py` (new, the DN-004 query, comparison and refusal),
`scripts/build_l0_matrices.py` (`compute`, `write_matrices`, a `--dry-run` that writes
nothing), `scripts/build_l0_report.py` (the refusal before rendering, the generated standing
line, `DN` in the exemption class), `scripts/build_l0_site.py` (the standing fields in
`results_tagged.json`, the same refusal, `--only results_tagged`, and a `wrote` key beside
`written` so the summary stops claiming writes it did not make), `scripts/publish_rejudgements.py`
(`--project-once`), `Makefile` (`make guards` gains both new files),
`scripts/check_protected_standing_guards.sh` (new),
`tests/test_standing_guards.py` (new, 11 tests), `tests/test_snapshot_successor.py` (new, 14
tests).

**`--only` exists because the site carries a build date.** A full site rebuild moves
`index.html`, `sitemap.xml` and `data/index.json` on their timestamps, and this task's declared
blast radius under `docs/` is three files. The flag's write set is a declared table, not a
prefix match, and its correctness is not asserted by a unit test but by the protected-paths
diff that runs every task: `docs/` moved on exactly `2026-09_fss_ai_readiness_L0.md`, its PDF
and `data/results_tagged.json`, and on nothing else. That is the check that would catch it.

**A defect in this task's own protected-paths check, found by running it twice.** The `docs/`
clause matched whole `git status --porcelain` lines, including the two-character status prefix,
and it was written against the UNSTAGED spellings (`?? `, ` M `). It passed before `git add` and
failed immediately after, when the same three files came back as `A  ` and `M  `. A check that
answers differently depending on whether the commit has been prepared yet is a check nobody can
run twice; the prefix is stripped before matching now and the PATH is the subject, which is what
it was always meant to be. Both runs are in `logs/sg_protected.log`'s history — the failing one
is quoted here rather than tidied away, because it is the only reason anyone would know the
clause had ever been conditional on staging.

**No DD was added.** DN-003 owed DD-065 because it changed DD-008's sharding unit. DN-004
supersedes no design decision — it is new publication policy over a question DD-001 raises and
does not answer — so the design note is the record and a DD would be a number for its own sake.

**What did NOT change.** Not one event. Not a rule module, manners, `params.yaml`, `rederive`,
a figure, a stored payload, the framework record, the skeleton, section prose,
`publication.yaml`, a published matrix or fragment, `corpus/`, or a prior RESULT. All **60**
committed shards are byte-identical to `HEAD`. The Result registry is where it was: 7,262
total, 59 published, 1 superseded, page counts 14 and 6.

## 6. Logs, so no number here has to be trusted from the summary

```
logs/sg_addendum_glob_pre_s3.log  addendum glob, before §3                no matches
logs/sg_s1_successor.log          §1 STOP CHECK — 0 moved, 41/41 covered  EXIT=0
logs/sg_report_check.log          the markdown gate, first pass           EXIT=1  (bare numeral: DN-004)
logs/sg_report_check2.log         after DN joined the class               EXIT=1  (bare numeral: "decision 1")
logs/sg_report_check3.log         the markdown gate, green                EXIT=0  gate PASS, 0 bare numerals
logs/sg_pdf.log                   report + PDF rebuild                    EXIT=0  597,840 bytes, pages 14 / 6
logs/sg_site.log                  results_tagged.json, --only             EXIT=0
logs/sg_site2.log                 --check then --only, after the `wrote` fix  EXIT=0  wrote: [data/results_tagged.json]
logs/sg_newtests.log              the two new files + PDF + publication   EXIT=0  56 passed
logs/sg_guards.log                make guards                             EXIT=0  50 passed / 21.55 s
logs/sg_gate_task.log             make gate-task + 22 of 22 re-derive     EXIT=0  2,180 passed / 398.81 s, then 7.20 s
logs/suite.log                    make gate-full, detached and polled     EXIT=0  2,205 passed / 1,294.04 s (21:34)
logs/sg_verify.log                seldon verify                           EXIT=0  all checks passed
logs/sg_protected.log             protected paths                         EXIT=0  PASS
```

The three markdown-gate logs are kept rather than tidied: they are the record of the two
numerals the new line contributed and of how each was resolved, which is the part of §3d a
reader would otherwise have to take on trust.

## 7. Open, for the next OODA

1. **The report now says it is one generation behind, and the build will refuse when that
   stops being harmless.** The re-snapshot decision DN-004 defers is still deferred, and it is
   now deferred with a guard behind it rather than with a sentence in a RESULT. The next
   re-judgement of cycle 4 that moves a verdict turns the build red and the answer is a report
   revision under DN-002.
2. **`--project-once` has never been run over a real backlog.** It is asserted on a two-cycle
   fixture and on the reset-and-replay property; the fourteen-cycle publication that motivated
   it is already done and will not recur. The first real use is a backlog nobody has yet.
3. **The 41 tagged Results are covered by three recomputation sources, and the closure check is
   what keeps that true.** A new tagged Result of the snapshot cycle whose base
   `build_l0_matrices.compute` does not emit will refuse the build as `uncovered`. That is the
   designed behaviour and it will read, the first time it happens, like a broken builder. It is
   not: it is the comparison saying it cannot speak for a number the report publishes.
4. **`PRIOR_CYCLES` holds 22 of the 23 payloads in `state/`** and counts controls among its
   "eight measured" (§3a). `scan_2026-09-07b_controls` is the one not in it. Nothing depends on
   it today; it is the next thing a reader of that dict will trip over.
