# CC Task: hosts are scanned in parallel with politeness kept per host, the suite runs under pytest-xdist, and the full suite runs once a day on main instead of before every push

**Date:** 2026-10-07
**Project:** ai-readiness-kg
**Authored by:** Desktop session, from DN-013 §2 (R2, R4). R3, worktree-per-task dispatch, is a Seldon change and is registered in the seldon repo as `cc_tasks/2026-10-07_SEL-004_worktree_per_task_dispatch.md`.
**Implements:** DN-013-R2, DN-013-R4.
**Framework layer served (DN-005 §5 rule 1):** §2.2, measurement: the instrument's wall-clock. No verdict may change.
**Fulfils:** its own ResearchTask. Launched by the dispatcher.
**After:** 2026-10-07_install_closure_v2
**Spend:** est. 2M tokens (Opus). Concurrency work, the xdist conversion, the suite three times. No harness model call.
**Network:** allowlist: pypi.org, files.pythonhosted.org
**Network, prose:** `pip install pytest-xdist` only; `git push`. No fetch by the harness; every scan in this task runs against the loopback control fixtures.

**HEADLESS NOTICE.** No next turn. Poll every detached command to its EXIT line.

## Measured premises (verify before acting; report any that is wrong)
- `manners.py:111-120`, `Fetcher._wait`: one `self._last[host]` dict and a blocking sleep of `1.0 / requests_per_second_per_host` (`params.yaml:141`), called from GET (:245) and HEAD (:276). One `Fetcher` per run (`run.py:766`, `:933`). No locking.
- `run.py:563`: `for t in tgts:` runs `run_surface` one surface at a time.
- The recollection made 2,074 requests over 42 netlocs, the largest `www.nass.usda.gov` 193 and `www.census.gov` 189 (its RESULT §4). At 1 request per second per host, a serial cycle cannot take less than the sum; a per-host-parallel one is bounded below by the largest host.
- The last full suite took 3,140.64 s single-process (`logs/arc_gate_full_2.log`). pytest-xdist is not installed or declared. The only markers are `slow` and `live_plan`; 21 test files open a Neo4j driver.
- The recollection's first full-suite run died at 35% with no EXIT line at 02:17:51Z, when a Desktop session committed in the same checkout. A gate must not run in a tree another process commits to.

## Decisions

1. **Politeness per host, parallelism across hosts (DN-013-R2).** `Fetcher` becomes thread-safe: a lock per netloc guards that netloc's last-request time and its robots cache, so two threads that reach the same netloc (an off-roster host several bodies declare, such as `www.usda.gov`) wait on one clock. Nothing crosses netlocs. Prior art: Heritrix's per-host frontier queues with politeness delay, Scrapy's `CONCURRENT_REQUESTS_PER_DOMAIN` with `DOWNLOAD_DELAY`. The rate, the UA, robots-first and the refusal rules are unchanged.

2. **The runner.** `run_cycle` groups targets by surface netloc and runs one worker per group (`ThreadPoolExecutor`, `manners.max_parallel_hosts` in `params.yaml`, default the number of groups, ceiling 16); within a group, surfaces keep their order. Results are reassembled in the original target order, so the payload is the serial payload except for timing fields. `max_parallel_hosts: 1` reproduces today's run exactly and is the escape hatch.

3. **Two guards, with a fake clock.**
   - Equivalence: the loopback control fixtures run serial and parallel give payloads equal after removing `fetched_at`, elapsed times and request ids. Every rule's verdict is identical.
   - Politeness under concurrency: from the fetch log of the parallel run, consecutive requests to one netloc are never closer than `1 / requests_per_second_per_host`, including the shared off-roster host case.
   Both are in `make guards`.

4. **Wall-clock, measured and projected.** Report the control cycle serial and parallel, and project a 16-body cycle from the recollection's per-netloc request counts (serial lower bound: the sum; parallel: the largest netloc plus overhead). The projection says it is a projection.

5. **pytest-xdist (DN-013-R4).** Declare it in the dev dependencies and run the suite with `-n auto --dist loadgroup`. A test that shares mutable state (the Neo4j database, `state/`, `logs/`, the event shards, git operations on the working tree, the `.seldon/` files) goes into a named `xdist_group` for that resource; find them by static scan and by a run that fails under `-n` and passes serially. Such a test is grouped, never skipped and never weakened. Gate: on one commit, the xdist run and the serial run report the same outcome for every node id (pass, skip, xfail), not just the same totals. Report both wall-clocks.

6. **Gate policy (DN-013-R4), written into `CLAUDE.md`.** In "Suite tiers": a task's gate is `make gate-fast` when its write set touches nothing under `assessment/harness/scan/rules/`, `collectors/`, `runner.py`, `run.py`, `manners.py`, `rederive.py`, `scripts/score.py` or the framework record, and `make gate-task` otherwise. `make gate-full` runs once a day on `main`, from its own `git worktree` (never the working checkout), by a launchd job written like `scripts/jobs/com.brock.airkg-dispatch.plist` and installed the same way. A red daily run writes `.seldon/DISPATCH_STOP` with the log path and opens an Issue, so nothing is dispatched onto a red main. In "The RESULT waits for the suite", "the full suite" becomes "the task's gate tier", and the rule that a fast tier is never reported as a green suite stays word for word. Do not touch the headless paragraph that `tests/test_dispatch_config.py` asserts is byte-identical to the launch prompt.

**Write set:** `manners.py`, `run.py`, `params.yaml` (`manners.max_parallel_hosts` only), the new guards, `tests/conftest.py` and the xdist groups, `pyproject.toml` (dev dependencies only), `Makefile`, `CLAUDE.md` (the two sections named), `scripts/jobs/` (the daily job and its plist), the RESULT. Byte-identical: `rules/`, `collectors/`, `runner.py`'s collection logic, `scripts/score.py`, every stored payload, every task file.

**Immutable once written.**

## Gate and report
`make gate-task` and `make guards`, then the whole suite under xdist and once serially on the final commit, `seldon verify`, the protected-paths diff. RESULT `cc_tasks/2026-10-07_parallel_hosts_and_fast_gate_RESULT.md`, under 50 lines: the control cycle's wall-clock serial and parallel; the 16-body projection; the suite's wall-clock serial and xdist, with passed, skipped, xfailed and deselected for each; the xdist groups and why each exists; the daily job as installed (or the exact command for the operator if installing it needs his session); premises wrong; tokens and model. `seldon cc complete`, commit, push.

**SEQUENCING:** verify premises → thread-safe Fetcher → runner groups → guards → wall-clock → xdist and groups → node-id comparison → CLAUDE.md and daily job → gate → RESULT → push.
