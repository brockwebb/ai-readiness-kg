# DN-007 — Operator rulings of 2026-09-16 to 2026-09-19, and the state they leave the project in

**Date:** 2026-09-19
**Status:** Active. Records rulings made in the Desktop thread that ran the standing dispatcher through its first four days. Each ruling is already enacted by a completed task; this note is where a stranger finds them in one place.
**Supersedes:** DD-060's monthly cadence for this project (ruling 3); DN-006 c5's binary `Network: none` (ruling 4); the pending-band table in `2026-09-17_prescription_layer_RESULT.md` §2 as an ask (ruling 2).

## 1. Rulings

1. **The dispatcher is the workflow.** A registered task with the three headers and a clean gate is launched, gated and reported without a person pasting anything. Sixteen tasks ran that way between 09-16 and 09-19. The operator is brought in for credentials the machine lacks, blocks it cannot route around, and public releases; nothing else. A step the Desktop can execute with the tools it holds (a config file, a fetch under the project's manners) is never listed as the operator's.
2. **Effort and cost are notional, relative, and never an ask.** Bands are assigned by technique class or tool kind, carry a `notional:` source, and print with one adjust-for-your-shop sentence. The planning fallacy (Kahneman and Tversky 1979) and reference-class forecasting (Flyvbjerg 2006) are the reason absolute figures are not sought; agencies that act on a prescription refine the bands by evidence. `ADDENDUM_02` to DN-005 holds the classes.
3. **No standing rescan on this machine.** `dispatch.cadence` is empty; the dispatcher stays on for tasks. A cycle is rendered on request (`scripts/render_spot_scan.py --target <body> --write`, or the full template). A spot cycle measures one body, publishes beside the cycle of record, never becomes the snapshot and never supersedes the frame's findings. Adopters set their own `schedule:` in `params.yaml` (`on_demand` or cron), outside `params_hash`, with no Seldon involved.
4. **Network is a declared budget, like spend.** `**Network:** allowlist: host1, host2` is a legal header; the dispatcher passes it, records it, and the session fetches only through `scripts/fetch_allowlisted.py` (robots-first, identified UA, every request logged). Enforcement is the fetch log, not a sandbox.
5. **The framework is the goal and the harness is its instrument.** The initial set on the 16 bodies is the deliverable; the graph answers where a body stands (`get_body`, the two scores, the readiness ladder, the concentration sentence), what to do (63 actions bound to verifying rules), and what it would need (13 tools, 19 preconditions, 37 `REQUIRES` edges, `get_requirements`). Tests this project cannot run are recorded as the requirement that would unlock them, with cost and who provides.

## 2. State on 2026-09-19

- Cycle of record: `scan_2026-09-10_rj4`, 23 legs judged, 1,009 findings, report and site re-snapshotted on it. Every rank rests on a one-leg criterion (F4 for nine bodies; a single pass on G4 or A10 for four); both equal-weight views are shown and no weighting is asserted.
- 24 harness legs; 36 M / 5 O / 5 D / 3 unassigned indicators.
- MCP: ten read-only tools, in Claude Desktop, local stdio; a hosted endpoint is a release decision.
- Adopter path: `make scan-now FRAME=<file>` under the adopter's own UA, results as files with or without Neo4j, runbook at `docs/adopt/run_on_your_site.md` whose commands the gate runs.

## 3. Open, none blocking

- Seldon: `check_stale_artifacts` should treat `superseded_by` as a recorded decision (`seldon verify` warns at `EXIT=1` since the re-snapshot); `seldon cadence render` does not exist; SEQUENCING lines are read into `precedes` edges inconsistently; a mid-run Desktop registration is now committed path-scoped, so that window is closed.
- G4's two appendix sources have no locator; cycle 3's generation-10 judgement registered no Results; `docs/progress/` can drift from the record unnoticed; a Tier C spot has no view; `make project` on an adopter run was not exercised on this machine.
- Weighting: the evidence that every rank turns on one leg is on the record; a stated priority from the working group or an empirical relation between a leg and use is what would justify departing from equal weights.
