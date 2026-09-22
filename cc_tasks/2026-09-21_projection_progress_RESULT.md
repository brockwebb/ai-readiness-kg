# RESULT: the projection says where it is while it runs (`cc_tasks/2026-09-21_projection_progress.md`)

Done: every step ran and the gate is green. `scripts/build_projection.py` now has a `Progress` class. It writes a line at every phase boundary and, inside each per-item loop, every `projection.progress_every` items (5000, a new key in `controls.yaml`) or every 60 s (`PROGRESS_INTERVAL_SECONDS`, §15.3), whichever comes first. Lines go to stdout and to `logs/projection_<UTC>.log`, flushed and fsynced, and the run closes with a per-phase timing table. `--dry-run` prints the phase plan and opens no driver. The docstring says why §15 points 1, 2 and 6 do not apply. `tests/test_build_projection_progress.py` has 7 tests: item interval, 60 s interval, every phase boundary, log ends with the table, silent by default, dry run opens no driver, config key required.

**Timing, from the measured run** (`logs/projection_20260922T023442Z.log`; stdout `logs/projection_progress_run.log`, `EXIT=0`), in seconds: prepass 2.2 · reset 2.4 · document_skeletons 3.3 · vocabulary 29.5 · **kg_replay 1540.9 (45.0%)** · overlays 389.6 (11.4%) · restorations 134.0 · resolutions 154.4 · thin_spans 10.5 · fingerprint 0.3 · **scan_layer 1149.5 (33.6%)** · framework_layer 7.8 · **TOTAL 3424.4 (57.1 min)**. Two phases take most of the time. kg_replay makes one `session.run` per event, about 50 writes/s over 140,688 events. scan_layer is `publish.py::project`. Both are the obvious case for `UNWIND` batching; that work is filed as ResearchTask `fd753c30` (proposed) and is not done here.

**Graph before and after the run, per label and per rel type** (`logs/projection_progress_fp_{before,after}.json`): the script's own fingerprint matches (32 keys). So do the counts over *all* labels (68,973 label memberships) and *all* rel types (137,196 relationships). Run-internal totals: nodes=30147, edges=37799.

| gate | result | log |
|---|---|---|
| `make gate-fast` (fast tier, not the full suite) | 2748 passed, 3 skipped, 27 deselected, 12 xfailed; 653.18 s; EXIT=0 | `logs/projection_progress_gate_fast.log` |
| `seldon verify` | All checks passed; EXIT=0 | `logs/projection_progress_verify.log` |
| protected paths (`scripts/check_protected_projection_progress.sh`, BASE 06393d7) | PROTECTED PATHS OK; EXIT=0 | `logs/projection_progress_protected.log` |

`make gate-full` was not run. The task says it is not required.

**Premises the task got wrong**
1. "Fingerprint at line 671": the function `fingerprint` starts at line 667, and 671 is its per-label count. It counts only KG labels and relationships that carry provenance, so it cannot show drift in the scan or framework layers. That is why the all-labels and all-rels counts above were added.
2. "~65 min": this run measured 57.1 min.
3. Decision 1 asks for in-loop progress in the scan and framework layers. That code is `assessment/harness/scan/publish.py` and `scripts/load_framework_graph.py`, and neither is in the write set. Those phases get only their boundary lines, so scan_layer runs 1149.5 s with no line. Closing that gap belongs to `fd753c30` or a task that owns `publish.py`.

**Session tokens:** a session-wide total cannot be read from inside this session. About 110k tokens of context were used, far under the 1.5M estimate. Billed tokens including cache reads are higher and are not measured here.
