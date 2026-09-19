# CC Task: the adopter's path: run the harness on your own site, on demand or on a schedule, and load the result

**Date:** 2026-09-19
**Project:** ai-readiness-kg
**Authored by:** Desktop session, from the operator's ruling of 2026-09-19: anyone can download the suite and scan their own site(s); on-demand or cadenced is their configuration; the last scan and its results are artifacts; this project keeps its own auto-rescan off.
**Implements:** DN-005 §2.4 (the framework is useful when a body can develop its readiness from it) and DD-060 (manners hold for every scan, whoever runs it).
**Framework layer served (DN-005 §5 rule 1):** §2.4, exposure.
**Fulfils:** its own ResearchTask (`seldon cc register`). Launched by the dispatcher.
**Spend:** zero model calls. **Network:** allowlist: 127.0.0.1
The walkthrough is exercised against a loopback fixture as "your site". No external host is contacted.

---

## 0. What an adopter has and lacks today

They have the repo, the harness, the rules, the fixtures, the record and the MCP. They lack: a way to name their own site as the frame without editing this project's target list; a schedule knob that is theirs and not `seldon.yaml`'s; a written path from "clone" to "ask the MCP where I stand"; and a statement of what the harness needs on their machine (Python, Neo4j or not, the identified UA they must set to their own contact).

**Decisions taken here (operator overrides later):**

1. **A frame file is the unit of adoption.** `assessment/harness/scan/frames/fss16.yaml` holds this project's 16 bodies (moved out of `params.yaml` or wherever `run.targets` reads them; behaviour byte-identical, the re-derivation gate proves it). `run.py --frame my_site.yaml` takes a file of the same shape: body name, home, flagships, and nothing else required. A one-body frame is the adopter's normal case; `--target` from `2026-09-19_spot_scan.md` still works within any frame.
2. **Schedule is theirs, in `params.yaml` under `schedule:`**: `on_demand` (default) or a cron expression, with a documented `make scan-now` and a `make install-schedule` that writes a cron or launchd entry for the adopter's own machine, printing what it wrote. This project's `params.yaml` says `on_demand`. Nothing in Seldon is involved; the adopter does not need Seldon at all.
3. **Manners are non-negotiable and the UA is theirs.** `params.yaml:manners.user_agent` must be set to the adopter's own identity and contact before a scan runs against anything but loopback; `run.py` refuses the project's default UA against a non-loopback host in a foreign frame. Rate limits and robots-first stay as they are.
4. **Results are artifacts.** A run writes its payload, matrices and a rendered `report/<cycle>.md` (the body's verdicts, the prescriptions ranked for it, what it would need, the concentration sentence) into `out/<cycle>/`. Without Neo4j the adopter gets those files; with Neo4j, `make project` loads the framework and the run and the MCP answers over it. The MCP and `score.py` gain `--no-neo4j` where they can read the record and the payload directly (the record is JSON), and say plainly which tools need the graph.
5. **One runbook, `docs/adopt/run_on_your_site.md`, exercised end to end in the gate** against a loopback fixture named as a one-body frame: clone, set UA, write the frame, `make scan-now`, read `out/<cycle>/report.md`, optionally `make project` and `get_body`. Every command in the runbook is the command the gate ran, copied from its log, not typed.
6. **This project's own settings are unchanged**: `fss16.yaml`, `on_demand`, the project UA, cadence off.

**Write set:** `assessment/harness/scan/frames/fss16.yaml` (new; the target list moves), `run.py`, `params.yaml` (`schedule`, `manners.user_agent` unchanged in value), `Makefile` (`scan-now`, `install-schedule`, `project`), `scripts/render_run_report.py` (new), `scripts/score.py` and `mcp/` (`--no-neo4j`), `docs/adopt/run_on_your_site.md` (new), tests, `scripts/check_protected_adopt.sh` (new), `seldon_events.jsonl`, the RESULT. `state/`, `corpus/`, `docs/reports/` byte-identical.

**Immutable once written. Glob `2026-09-19_adopter_path_ADDENDUM*.md` before starting and again before §3.**

---

## 1. Decisions 1 to 4, tests first (the moved frame re-derives every stored payload byte-identically; the default UA is refused against a foreign non-loopback host; `on_demand` installs nothing).
## 2. Decision 5, the runbook run as written.
## 3. Gate
`make gate-task` (re-derivation, non-optional after moving the frame) and `make gate-full` (`-rs`), `seldon verify`, protected paths. Detached and polled inside this turn per `CLAUDE.md`. Expected skips: 3. Failure ships nothing.
## 4. Report
RESULT `cc_tasks/2026-09-19_adopter_path_RESULT.md`: §0 the runbook's commands and their logged output; §1 the rendered `report.md` for the fixture body; §2 what needs Neo4j and what does not; §3 every premise this task file got wrong; §4 the gate table, tier named. `seldon cc complete`, commit, push.

**SEQUENCING:** §1 → §2 → glob addenda → §3 → §4 → push. Runs after `2026-09-19_spot_scan.md`.
