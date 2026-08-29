# RESULT — 2026-08-29_biblio_cron

**Date:** 2026-08-29. **Zero `model_stub` spend**, and for the first time that claim is
*enforced* rather than asserted: the scheduled entrypoint fails nonzero if the shared spend
ledger changes under it, and the legs' import closure is pinned by test. Both verified on
two live runs.

**Status: unit installed, loaded, and verified by two manual triggers with log evidence.**
No addenda existed for this task (globbed; only the task file).

---

## What was scheduled

| | |
|---|---|
| Label | `com.brock.aikg.biblio-resume` |
| Schedule | 02:30 local (`StartCalendarInterval`), `RunAtLoad` false |
| Entrypoint | `scripts/jobs/biblio_resume_job.py` |
| Leg 1 | `python -m kg.biblio resume` |
| Leg 2 | `t1_build_index.py --phase project` (manifest table + operator pickup) |
| Log | `state/logs/biblio_resume/<date>.log` (gitignored via `logs/`) |
| Mechanism | launchd LaunchAgent from a committed template |

**Mechanism choice (§2): launchd, not cron.** No friction — the repo already had a working
LaunchAgent (`com.wintermute.airkg-extraction-burn`) and a `StartCalendarInterval` exemplar
(`com.arnold.sync-daily`) to copy from, so cron's fallback was never needed.

**Deviation from the repo's other scheduled job, recorded.** `airkg_extraction_burn.sh` is a
bash wrapper; this one has no shell layer — the plist calls Python directly. The reason is
§5: the guardrail has to be *testable*, and a guard living in an untested shell script is an
assertion, not a control. A side benefit is that the DD-007 credential drop
(`ANTHROPIC_API_KEY`/`ANTHROPIC_AUTH_TOKEN`) now protects **every** invocation rather than
only the launchd one, since it moved into the entrypoint.

### Install / uninstall (§2 requirement)

```bash
python3 scripts/launchd/install.py --print --python /opt/anaconda3/bin/python3   # render only
python3 scripts/launchd/install.py --install --python /opt/anaconda3/bin/python3
python3 scripts/launchd/install.py --status
launchctl kickstart -k gui/$(id -u)/com.brock.aikg.biblio-resume                 # fire now
python3 scripts/launchd/install.py --uninstall
```

The plist is **generated**, never hand-authored: schedule from `controls.yaml`, paths from the
checkout, interpreter from `--python`. `--install` is idempotent (boots out an existing copy
first). `--uninstall` removes the unit and leaves `state/logs/` alone — the run record
outlives the unit that wrote it.

**Why the template is committed.** Prior art on this machine, cited in the template itself:
`com.arnold.sync-daily` ran 190 consecutive days and died at a reboot because its plist
existed *only* as an untracked file in `~/Library/LaunchAgents`. Ten days of data were lost
silently with no on-disk copy to restore from. This unit starts in the repo.

---

## §5 guardrail — three checks, and what each is actually worth

The task allows "assert no `model_stub` import **or** a runtime check". Both are present,
because they fail differently and neither subsumes the other. Stated honestly, weakest last:

| check | kind | covers | verified by |
|---|---|---|---|
| leg import closure | **preventive** — spend is *unreachable* | both legs | `test_real_scheduled_legs_import_no_spend_path` imports `kg.biblio` + `t1_build_index` in a clean subprocess and asserts an empty closure |
| spend-ledger fingerprint (sha256 before/after) | **detective** | both legs, by any route | fired on a seeded ledger-appending leg (rc=3); held on two live runs |
| `spend_modules_loaded` delta | detective, **this process only** | the entrypoint's own imports | delta tests below |

**The preventive check is the real one.** It was verified empirically before anything was
written: neither `kg.biblio` nor `t1_build_index` pulls in `kg.extraction.model_stub` or
`kg.spend`, so no reservation is reachable at all. The task's premise held; the test pins it
so a future model call on the harvest path fails the suite.

**A design defect the full suite caught.** The runtime module check first read `sys.modules`
absolutely. That fails two ways: any *other* test importing `kg.spend` for its own reasons
failed this job rc=4 (false alarm), and — the substantive half — **the legs are subprocesses,
so their imports never appear in this process at all**, making an absolute reading close to
vacuous for the thing it appeared to cover. Rescoped to a delta against a start-up baseline,
so only what appears *during* the run is attributed to the run, and the module docstring now
says plainly that the ledger fingerprint, not this check, is what covers the legs.

No ceiling is declared in the unit, because none is permitted to be needed. That is the point
of the two guards: the claim is auditable, not merely stated.

---

## Verification — two live runs

Run 1 (`17:17:41Z`) and run 2 (`17:21:34Z`), both via `launchctl kickstart -k`.

| | run 1 | run 2 |
|---|---|---|
| rc | 0 | 0 |
| legs | `[0, 0]` | `[0, 0]` |
| elapsed | 88.0s | **2.6s** |
| harvest requests issued | 149 | **3** |
| coverage after | 29/178, 149 retryable | 29/178, 149 retryable |
| ledger sha256 | `19864ce2ffea` → unchanged | `19864ce2ffea` → unchanged |

Both guardrail lines present on both runs (`spend ledger unchanged`, `this run imported no
spend-path module`). Leg 2 regenerated both projections (178 rows, 5 pickup rows).

**The harvest made no progress, and that is the honest result.** OpenAlex's daily quota was
exhausted at run time: `HTTP 429 … Retry-After 24138s (6.7h) — daily quota exhausted`. This is
exactly §1's "may no-op harmlessly on quota-exhausted nights", so it is a valid demonstration
of the scheduled path — but it does **not** demonstrate the job harvesting successfully. The
harvest path itself is separately proven (the 29 resolved records came from it). What these
runs prove is that the wrapper invokes it correctly, classifies every document, degrades
without hanging on a 6.7-hour `Retry-After`, and leaves coverage and the ledger untouched.

---

## Adjacent defect found and fixed: a doomed sweep, nightly

Run 1 issued **149 requests after the first response had already said "retry in 6.7h."**
Unscheduled, that is one wasted burst. Scheduled nightly — which is what this task does — it
becomes 149 known-doomed requests against a polite-pool API every night. **The scheduling is
what makes it matter**, so it is in scope, and it is fixed rather than filed.

`scripts/t0_biblio_harvest.py` now stops a sweep after `CONSECUTIVE_QUOTA_STOP = 3`
consecutive documents that failed on daily quota *alone*. Three, not one, follows this repo's
existing systemic-failure idiom (`BURN_QUARANTINE_STOP_MODE=systemic` halts on 3 consecutive
over-threshold documents): one failure is an incident, three is a condition. Not one, because
the provider ladder can still resolve a document through Crossref while OpenAlex is
quota-dead, and stopping on the first would forfeit those.

Detection is `all`, not `any`: a document whose Crossref lookup returned a genuine "no
record" has learned something about the world and must not count toward a stop meaning "come
back tomorrow." Documents after the stop are left **untouched** in their existing retryable
state — hence run 2's coverage is byte-identical to run 1's. The stop costs no information.

Measured effect: **88.0s / 149 requests → 2.6s / 3 requests, coverage unchanged.**

---

## Log-bomb guard and retention (§3)

Per line **and** per run, because neither bound implies the other: one pathological line is
the Docling failure already met on this project (~230,000 lines from a single exception), and
a flood of ordinary lines is the other half of the same denial of service.

- `log_max_line_chars: 2000` — the same figure as `MAX_ERR_CHARS` in `t1_build_index.py`.
  Same hazard, same number; a second figure for one hazard is a drift source.
- `log_max_run_bytes: 2097152` (2 MiB, ~40× a normal run's ~50 KB).
- `log_retention_days: 30`, swept by the job itself.

All three live in `controls.yaml` under a new append-only `jobs:` block (`schema_version`
0.2 → 0.3, following the `spend:` block's precedent). A missing block or key is a hard
`SystemExit`, never a silent default — a defaulted retention window is a deletion policy the
operator never chose.

**Retention deletes only files it owns** (`^\d{4}-\d{2}-\d{2}\.log$`), so `launchd.log` and
any operator-saved file survive.

**Schedule rationale is measured, not assumed.** 02:30 EDT = 06:30 UTC. The observed
`Retry-After 24138s` at 17:20 UTC puts the quota reset at ~00:02 UTC — a UTC midnight
boundary — so the window sits ~6.5h clear of it. Recorded in `controls.yaml` because the
plist's numeric fields cannot carry a reason.

**One more fix while verifying:** legs run with `PYTHONUNBUFFERED=1`. A child writing to a
pipe is block-buffered, and the parent's `bufsize=1` governs only its own side — so before
this, a long leg showed nothing until exit (a hang and progress look identical) and a leg
killed mid-run lost its buffered output entirely. For a scheduled job whose only artifact is
its log, that is the whole record.

---

## Completion behaviour (§4)

At full coverage the job keeps running and logs `coverage: COMPLETE — no retryable documents
remain…`, stating that unloading is an operator decision. **Nothing self-disables**: a job
that deletes itself on a threshold takes its own evidence with it. Both branches are tested.

---

## Tests: 259 → **287 passed**

28 new (22 in `tests/test_biblio_resume_job.py`, 6 in `tests/test_t0_t1_substrate.py`).

**Mutation matrix, 11/11 killed** (`PYTHONDONTWRITEBYTECODE=1` with `__pycache__` cleared
between runs — stale bytecode invalidated a matrix on this project on 2026-08-28, where a
restored file matched the cached `.pyc`'s mtime and size and pytest ran the mutant anyway):

| mutation | result |
|---|---|
| M1 ledger-change breach removed | KILLED |
| M2 retention ownership filter removed | KILLED *(after amendment — see below)* |
| M3 per-line truncation removed | KILLED |
| M4 per-run cap removed | KILLED |
| M5 module check reverted to absolute reading | KILLED |
| M6 credential drop removed | KILLED |
| M7 placeholder scan removed | KILLED |
| M8 coverage-complete note removed | KILLED |
| M9 quota stop removed | KILLED |
| M10 `all`→`any` in quota detector | KILLED |
| M11 quota streak never resets | KILLED |

**M2 initially SURVIVED**, and the reason is worth recording: the ownership test listed only
filenames (`launchd.log`, `notes.log`) that `date.fromisoformat` rejects anyway, so deleting
the ownership filter outright left the test green. It was measuring the **date parse, not the
guard** — the same class as the wrapper-guard defect in methodology §7.9. Amended with names
that separate the two: `20200101.log` and `2020-W01-1.log` are accepted by `fromisoformat` on
Python 3.11+ (basic and week ISO forms) but are not this job's `YYYY-MM-DD.log` naming. M2
then killed.

**A guard test that fires on the second-strongest filter is not a test of the guard.** Two
tasks running, this is now the failure mode that has cost the most rework here.

Two other seeded-defect checks that found real bugs during authoring, not after:
`test_render_fails_loud_on_an_unsubstituted_placeholder` showed the installer's placeholder
check only looked for keys it already knew, so a *renamed* placeholder — the actual hazard —
passed straight through into a loaded unit; it now scans for any surviving `@MARKER@`.

---

## Files

**New:** `scripts/jobs/biblio_resume_job.py`, `scripts/launchd/install.py`,
`scripts/launchd/com.brock.aikg.biblio-resume.plist.template`,
`tests/test_biblio_resume_job.py`, this RESULT.
**Modified:** `controls.yaml` (`jobs:` block, schema 0.3), `scripts/t0_biblio_harvest.py`
(quota stop), `tests/test_t0_t1_substrate.py` (6 tests).
**Installed (outside the repo, by design):**
`~/Library/LaunchAgents/com.brock.aikg.biblio-resume.plist`, rendered from the template.

## Not done, deliberately

- **T0 is still 29/178.** The quota was out on both runs. The job now finishes it
  unattended; nothing further is owed by this task.
- **No server, no web surface** — the webdesktop rule is untouched. This is a timer.
- **The Commerce PDF and 4 degraded PDFs** remain on the operator pickup list; leg 2
  regenerates it nightly but cannot acquire anything.
