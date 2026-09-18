# RESULT: the cadence is off; a cycle is something a person asks for

**Task:** `cc_tasks/2026-09-18_cadence_off.md`. No addenda existed at either glob, before §1 and before §2.
**Framework layer served:** none (the dispatch path).
**Spend:** zero model calls. **Network:** none beyond `git push`.

**Gate, in one line.** Full suite **2577 passed, 3 skipped, 12 xfailed, 0 deselected**, `EXIT=0`, 24 min 48 s. `seldon verify`: all checks passed, `EXIT=0`. Protected paths: OK, `EXIT=0`. The table and log paths are in §3.

**What changed.**
- **Decision 1.** `dispatch.cadence` is now `[]`. `dispatch.enabled` stays `true`.
- **Decision 2.** The template's "Authored by" sentence is replaced.
- **Decision 3.** The tests assert the new state: an empty cadence list loads, nothing renders at the 2026-10-05 tick, and the template still renders on request into a dispatch candidate with the three headers and `ok c5`.
- **Decision 4.** `docs/design/2026-09-15_DN-006_standing_dispatcher_ADDENDUM_07.md` records the supersession. DD-060 is untouched.
- **Seldon issue filed.** The missing `seldon cadence render` command is filed as `~/GitHub/seldon/issues/2026-09-18_cadence_render_on_request.md`, committed in the Seldon repo.

---

## 0. The config diff

`seldon.yaml`, `@@ -112,63 +112,8 @@`: 60 lines removed, 5 added. Removed:
- the decision-8 comment block;
- the whole `scan_cycle` entry, including `rule: {monthly_first_weekday: monday, at_utc: "00:00"}`, `template`, `instances_dir`, `cycle_name_format: "scan_{date}"`, `start_period: "2026-10"` and `last_instance: ""`, each with its comments.

What stands in their place:

```yaml
  # ------------------------------------------------------------------------------ cadence
  # Schedule turned OFF 2026-09-18 by operator ruling: a scan cycle is requested, not scheduled
  # (`cc_tasks/2026-09-18_cadence_off.md`; DN-006 ADDENDUM_07 supersedes DD-060's monthly cadence).
  # The template `cc_tasks/templates/scan_cycle.md` stays and is rendered on request by the command
  # in `cc_tasks/2026-09-18_cadence_off_RESULT.md` §1 until Seldon ships `seldon cadence render`.
  cadence: []
```

`load_dispatch_config` now returns `cadence == []` and `enabled is True`, checked live and asserted by `tests/test_cadence_template.py::test_the_cadence_list_is_empty_and_loads`.

## 1. How to render a cycle on request

`seldon cadence render` does not exist in the Seldon repo, so here is the equivalent. Run it from the repo root, in a shell where `python` imports `seldon`, which is `/opt/anaconda3/bin/python` here:

```bash
f=$(python -c "from datetime import datetime,timezone;from pathlib import Path;from seldon.core import cadence as C;n=datetime.now(timezone.utc);p=n.strftime('%Y-%m-%d');e={'name':'scan_cycle','cycle_name_format':'scan_{date}','instances_dir':'cc_tasks'};s=C.instance_stem(e,p,n);f=Path('cc_tasks',s+'.md');assert not f.exists(),f;f.write_text(C.render(Path('cc_tasks/templates/scan_cycle.md').read_text(),cycle_name=C.cycle_name_for(e,n),period=p,cadence_name=e['name'],created_at=n.strftime('%Y-%m-%dT%H:%M:%SZ'),instance_stem=s));print(f)") && git add -- "$f" && seldon cc register "$f" && git commit -m "register: $f — scan cycle rendered on request" -- "$f" seldon_events.jsonl && git push
```

What it does:
- **Renders.** It uses the same `seldon.core.cadence` functions (`instance_stem`, `cycle_name_for`, `render`) that `_create_instance` used. For a request on 2026-09-18 it writes `cc_tasks/2026-09-18_scan_cycle_2026-09-18.md`, with cycle name `scan_2026-09-18`.
- **Refuses a second render.** It will not overwrite an instance from the same day.
- **Stages before registering.** `git add` comes first because `seldon cc register` refuses an untracked file (`register_task_file`: `status != GIT_TRACKED`). It then commits the task file and the `artifact_created` line, and the dispatcher's next pass takes it as an ordinary candidate.
- **Uses the date as the period.** A requested cycle's period is its UTC date rather than `YYYY-MM`, so two cycles requested in the same month cannot collide on the instance glob.

**Tested.** The render step was run in a scratch directory against this template. It produced the file above with zero unsubstituted `{field}` placeholders. The registration and commit steps were not run, because doing so would create a real cycle task. `tests/test_cadence_template.py` renders with the same four values and asserts the output is a dispatch candidate: all three headers, `ok c5` via "under cadence scan_cycle", `ok c4` at zero declared tokens, and no superseding addendum.

**The Seldon issue that asks for the command:** `~/GitHub/seldon/issues/2026-09-18_cadence_render_on_request.md`. It asks for `seldon cadence render <name> [--period P]`, with the entry held in config and its rule optional, and `cadence_created` carrying `"trigger": "request"`.

## 2. Premises the task file got wrong

1. **`tests/test_cadence_pass.py` does not exist.** The cadence tests that read this project's entry are in `tests/test_cadence_template.py`. That file indexed `DISPATCH["cadence"][0]` at import, so it would have failed collection outright once the list was empty. It was edited instead, within decision 3's intent. `tests/test_dispatch_config.py` was correctly named.
2. **"The template still renders on request" had no mechanism in this project to point at.** With the entry gone, the render parameters (`name`, `template`, `instances_dir`, `cycle_name_format`) are in no config. They now appear twice as literals:
   - in the §1 command;
   - in `ON_REQUEST` in `tests/test_cadence_template.py`.

   That duplication is what the Seldon issue removes. Until then, the test holds the constants and the command must match them.
3. **Decision 1's four-line comment cannot also name the Seldon issue.** The comment points to this RESULT's §1, and this RESULT names the issue. The four-line limit was kept.
4. **The one-sentence template change leaves other stale prose in the template.** The write set allowed one sentence, so the rest was left and is listed here for a follow-up task:
   - "**Authored by:** the standing dispatcher, rendering …". A requested render is authored by whoever runs §1.
   - "**Implements:** DD-060 (monthly, first Monday UTC)". The cadence clause is replaced by ADDENDUM_07.
   - "the standing measured cycle for {period}" in the title.
   - "**Fulfils:** … registered by the dispatcher when this file was rendered".
   - "The measured tier's cadence is the thing this advances: January's numbers are January's only if the January cycle ran in January."

   `test_the_template_cites_the_decisions_it_implements` requires "DD-060" in the text. The identity and refusal parts of DD-060 still apply, so that citation stays even after the cadence prose is fixed.
5. **c5 was not re-examined by the task, and it matters.**
   - DN-006 decision 2 defines c5's second limb as "the task was created by the cadence rule". A requested instance is not.
   - It is still eligible, because c5 as implemented matches the header grammar `under cadence <name>` by regex (`seldon/core/dispatch.py` `_NETWORK_CADENCE_RE`) and does not check that the cadence is configured.
   - ADDENDUM_07 §2 rules this intended. The Seldon issue records the dependency, so that a future tightening of c5 does not silently make every requested cycle ineligible.
6. **Cycle 5 was scheduled for 2026-10-05T00:00Z. It is now cancelled, not moved.** The task file did not say so outright. ADDENDUM_07 §1 does.

## 3. Gate

**Tier:** the full suite (`make gate-full`'s command, `pytest tests/ assessment/ -q -rs`, run detached to its own log). It includes every test in `make gate-fast` plus the slow tier, and was run because CLAUDE.md requires `gate-full` before every push. No separate `gate-fast` wall-clock was taken. `gate-task` was not required, because no rule module, registry or re-derivation engine changed.

| check | result | log |
|---|---|---|
| full suite | **2577 passed, 3 skipped, 12 xfailed, 0 deselected**, 443 warnings, 1488.25 s, `EXIT=0` (12:38:21Z → 13:03:12Z) | `logs/cadence_off_full.log` |
| skips (3) | `tests/test_dispatch_config.py:333` (interactive_only; this is a dispatched session); `tests/test_scan_harness.py:283` (E5 judges the cycle's controls, not a surface); `assessment/tests/test_g1_preservation.py:337` (no dev proposition publishes SE and CI together). These are the same three as the prior RESULT (`2026-09-18_manners_status_and_b5_control_RESULT.md`). | `logs/cadence_off_full.log` |
| count vs prior full run (2581 passed) | −4, accounted for (breakdown below) | — |
| `seldon verify` | all checks passed (event log 34955 events readable; replay skipped as expensive, its default), `EXIT=0` | `logs/cadence_off_seldon_verify.log` |
| protected paths | the changed set vs `ec35af1` is exactly the write set; nothing under `docs/` changed except ADDENDUM_07; `seldon_events.jsonl` lost no line; template `+2 −4`; `PROTECTED PATHS OK`, `EXIT=0` | `logs/cadence_off_protected.log` |

**The −4 in the passed count.** Eight tests were removed and four added:
- **Removed from `test_dispatch_config.py` (4):** the cycle-5 due test, and the three parametrized blocked-reason cases.
- **Removed from `test_cadence_template.py` (4):** the tests for the configured entry, the rule, "nothing due at ship because of `start_period`", and "no instance exists".
- **Added (4):** `test_nothing_renders_on_the_first_monday`, `test_the_template_exists_under_cc_tasks_templates`, `test_the_cadence_list_is_empty_and_loads` and `test_the_template_says_a_cycle_runs_on_request`.

The protected-paths check was an inline bash script against the task's declared write set, because this task has no `check_protected_*.sh` of its own. The log carries the script's output, not the script. It made three checks:
- every path in `git diff --name-only HEAD` plus the untracked files is in the write set;
- no path under `docs/` other than ADDENDUM_07 changed;
- `git diff HEAD -- seldon_events.jsonl` shows no removed line.
