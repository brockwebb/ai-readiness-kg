# RESULT — harness small: the clock through `merge_controls`, a cheap agreement check, `xmlns` at source

**Task:** `cc_tasks/2026-09-10_harness_small.md`. No addenda exist; globbed at dispatch and
again before §3, both times empty.
**Date:** 2026-09-10 UTC
**Spend:** zero model calls. **Network: none.** Loopback fixtures only. No federal host.

---

## 1. The gate — §3

**PASS on every clause.** All long-running commands detached, logged, polled to `EXIT`; §6
cites the paths.

| clause | result |
|---|---|
| Both-clocks agreement, 7 fixtures, 0 differences, wall-clock reported | **0 differences**, **25.7 s** (was 302 s) |
| Fast tier green, wall-clock | **EXIT=0**, 1652 passed, **298 s** (was 1145 s) |
| Full suite green, wall-clock, `--durations=10` | **EXIT=0**, 1663 passed, 2 skipped, **980 s** (was 1815 s) |
| 8 payloads byte-identical | **8 of 8** |
| Hygiene, `seldon verify`, protected paths | all **EXIT=0** |
| `test_merging_controls...` out of the top ten | **out** — §4 |
| §2: `make report-pdf` passes its numeral gate without the namespacing step | **EXIT=0**, 2 passed |

**The headline: the fast tier went 1145 s → 298 s while covering eight MORE tests, and the
full suite went 1815 s → 980 s.** Against where this started two tasks ago, the pre-push suite
is 3354 s → 980 s, a 71 % cut, with no test removed, deselected or weakened.

## 2. Decision 1 — the clock reaches `merge_controls`

`run.py::merge_controls(payload_path, params, clock=None)`; it threads the clock to the
`run_controls` call it makes and defaults to the real one. **`main` was not touched**: it takes
no clock, and `test_production_cannot_be_handed_the_virtual_clock` still asserts that by
signature, so a cycle against real federal hosts remains structurally incapable of running
unthrottled. That is the whole point of clocking one call site rather than the module.

`test_merging_controls_replaces_them_rather_than_accumulating` passes one `VirtualClock` to
both calls — one clock, because the test's subject is that the SECOND merge replaces the first,
and two clocks would have made the two cycles incomparable in a way the test does not intend.

**594 s → 10.4 s.** That single test was a third of the fast tier: it ran two complete
seven-fixture control cycles at the standing 1 req/s to assert a property of a dict merge.

## 3. Decision 2 — the agreement check pays for itself

The both-clocks check stays in the per-task gate. It is what makes every other virtual-clock
test meaningful: if the virtual clock ever returned a different verdict than the real one, all
the speed would be bought with a lie.

Its real-clock side now runs at a test interval instead of the standing rate. **302 s → 25.7 s.**

**Expressed as `TEST_INTERVAL_RPS = 20`, not as an interval of 0.05 s.** Same number — the task
file wrote it as the interval, `params.yaml` holds the rate, and a test that names the rate
reads as a deliberate override of the configured knob rather than a magic float. The real
standing rate is still asserted, unchanged, by the one-fixture `slow` test.

**Verdict agreement is a property of the rules, not of the rate**, which is what licenses this
at all. The check compares leg by leg across all seven fixtures and reports 0 differences.

## 4. Decision 3 — `xmlns` at source, and what it broke

`figures.py` emits `xmlns="http://www.w3.org/2000/svg"` on the root element. All six figures
re-rendered; `docs/progress/index.html` carries six `<svg xmlns`; the namespaced-copy step is
gone from `scripts/build_report_pdf.py`, replaced by a hard stop if a figure ever arrives
without the declaration. `make report-pdf` rebuilds and its numeral-multiset gate passes.

**It broke a lint, and the lint was right to fire.** `test_no_figure_reaches_the_network` bans
`http://` in any figure, and a namespace name is a URI. The fix is not to relax the ban: the
SVG namespace name is an **identifier, not a location** — *Namespaces in XML 1.0* §2.1 is
explicit that it is not a goal for it to be usable for retrieval, and no conforming processor
dereferences it. So the test now asserts the declaration appears **exactly once, on the root**,
strips that one occurrence, and applies the unchanged ban to everything else. The figure still
cannot reach the network; the one URI that is not a fetch is named and accounted for.

Top ten durations of the full suite, with the three that used to lead it gone:

```
264.60s tests/test_scan_run_2.py::test_the_uncited_set_only_shrinks_and_only_by_citation
236.82s tests/test_scan_run_2.py::test_the_overlay_is_idempotent
176.52s tests/test_scan_run_2.py::test_every_recorded_403_now_reads_as_refused_on_the_log
 41.26s tests/test_bulk_v038.py::test_batch_membership_matches_what_provenance_already_records
 25.54s tests/test_virtual_time.py::test_the_control_gate_returns_the_same_verdicts_on_both_clocks
 17.06s tests/test_t0_t1_substrate.py::test_project_refreshes_t0_before_publishing_it
 13.67s tests/test_manners_robots_first.py::test_no_netloc_is_ever_fetched_before_its_robots_txt
 13.12s tests/test_guards_replay_their_incidents.py::test_the_fetcher_gate_catches_the_apex_sitemap_fetch
 10.55s tests/test_bulk_v038.py::test_finishing_a_batch_does_not_renumber_the_batches_after_it
 10.03s tests/test_bulk_v038.py::test_batch_identity_does_not_move_as_chunks_get_extracted
```

`test_merging_controls...` is out, as §3 predicted. The three that now lead are `slow`-marked
event-log replays, not rate-limited sleeping; they are the next target and they are a different
problem.

## 5. Decision 4 — one scanner, and the premise it got wrong

`tests/support/sourcescan.py`. `strip_prose(source)` blanks comments, docstrings and string
literals through the tokeniser, preserving line numbers so a report still points at a line;
`scan(roots, needles, skip=())` returns `[(path, lineno, line)]` of code hits. A file that does
not tokenise comes back **unchanged**, not empty — returning nothing would make every check
pass on a file nobody could parse.

Converted to it: the suffix-list retirement check, the bare-wall-time lint, the self-licensing
lint, the `error_class` guess check, and five single-file source assertions in
`test_scan_figures`, `test_scan_frame`, `test_scan_run_2`, `test_virtual_time` and
`test_manners_robots_first`. Everything else that reads `*.py` in this repo already parses
rather than greps (`ast` in `test_scan_harness.py` and `fixture_expectations.py`) or reads
string literals **on purpose** (the Cypher lint, whose subject is the query inside the string).

### The task file's premise that was wrong

**"Strip comments and string literals" is right for four of the five checks and wrong for the
fifth.** The self-licensing lint looks for `os.environ["AIRKG_SCAN_CYCLE"] = ...`, where the
token is the **subscript key**. Blanking string literals does not sharpen that lint, it blinds
it: the converted lint went green against its own planted driver, which is the exact line it
exists to catch. The RED/GREEN incident replay written for it in the previous task caught this
within one run.

So `strip_prose` takes `literals: bool = True`, and exactly one caller passes `False`. The
distinction it draws is the one that was actually meant: **prose versus code, not quoted versus
unquoted.** For four checks those coincide. For a check whose needle is data — a dict key, an
env var name — they do not, and comments and docstrings still go in that mode. A test pins both
sides of the switch.

The needles are still assembled from parts in every check. That is a separate defence, against
a file matching its own scanner's definition, and stripping prose does not replace it.

This is the **fifth** source-scanning check in this repo to be fixed for reading prose as code,
and the class fix arrived one incident after the class was named.

## 6. Verification

```
logs/gate_agreement.log   both clocks, 7 fixtures, 0 differences        27 s   EXIT=0
logs/gate_report_pdf.log  make report-pdf, numeral gate 2 passed         1 s   EXIT=0
logs/gate_fast.log        1652 passed, 2 skipped, 11 deselected        298 s   EXIT=0
logs/gate_rederive.log    8 passed, 25 deselected — byte-identical       4 s   EXIT=0
logs/gate_full.log        1663 passed, 2 skipped, --durations=10       980 s   EXIT=0
logs/verify.log           seldon verify — All checks passed                    EXIT=0
logs/hygiene.log          manifest verify clean; no redirect log               EXIT=0
logs/protected.log        protected-paths diff                                 EXIT=0
                            shipped rule modules   no change
                            prior RESULTs          no change
                            state/ (targets v4)    no change
                            cycle evidence         no change
                            events/                no change (append-only)
                            report PROSE (.md)     no change
                            report PDF             rebuilt — decision 3, numerals identical
                            run.py::main           interface unchanged

test count   1644 -> 1652 fast, 1655 -> 1663 full: +8, and both tiers moved by
             the same 8 because none of the new tests is slow. Six are
             tests/test_source_scanning.py, from THIS task. The other two are
             tests/test_report_pdf.py, which landed in d721516 between the
             1644 measurement and this one and are not this task's doing.
             No test removed, deselected or weakened.

registered   suite_fast_seconds_2026-09-10b = 298
             suite_full_seconds_2026-09-10b = 980
             2 registered, 0 failed
             `b` because 2026-09-10 is already bound at 1145/1815 and a Result
             name binds once (AD-028, DD-056).
```

## 7. What the next task needs

1. **The three `slow` leaders are event-log replays, not sleeps.** 678 s of the 980 s full suite
   is three tests in `test_scan_run_2.py` that each replay the whole log. A clock cannot help
   them; a fixture that replays once per module can.
2. **`literals=False` has exactly one caller and should keep having one.** If a second check
   ever needs it, the question to ask first is whether its needle is really data or whether it
   should be matching an AST node instead.
3. **`2026-09-10_scan_frame_v5.md` is next**, and it is the first task in this chain that
   contacts a host: the seven declared landing pages, robots-first, through the fetcher.
