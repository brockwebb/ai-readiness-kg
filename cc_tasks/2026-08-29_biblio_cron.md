# Micro-task: schedule quota-constrained harvests (biblio resume nightly)

**Date:** 2026-08-29. Zero `model_stub` spend, ever, by construction — this task schedules only metadata/projection work.

## Scope

1. **One scheduled job:** nightly run (suggest 02:30 local; pick and record) of `python -m kg.biblio resume` followed by `--phase project` (manifest table + operator pickup regeneration). Idempotent and quota-safe is already proven; the job may no-op harmlessly on quota-exhausted nights.
2. **Mechanism:** launchd LaunchAgent (macOS-native; label `com.brock.aikg.biblio-resume`), plist under `~/Library/LaunchAgents/`, generated from a template committed to the repo (`scripts/launchd/`) so the unit is reproducible; install/uninstall documented in the RESULT. Do not stand up any server or web surface (webdesktop rule untouched — this is a timer, not a service). If launchd friction is disproportionate, plain cron is acceptable; record the choice and why.
3. **Logging:** stdout/err to `state/logs/biblio_resume/<date>.log`, log-bomb guard applies (2K truncation), 30-day retention cleanup in the same job.
4. **Completion behavior:** when T0 reaches full coverage, the job keeps running harmlessly (resume no-ops); add a line to the log noting coverage complete. Removal is an operator choice later, not automated.
5. **Guardrail, explicit and tested:** the scheduled entrypoint refuses to invoke anything that reserves against the spend guard — assert no `model_stub` import on the resume path, or a runtime check that exits nonzero if a reservation is attempted. **No model-spending job is ever scheduled without an operator-declared ceiling in the unit itself; this task schedules none.**

## Exit
Unit installed and verified by one manual trigger (`launchctl kickstart` or equivalent) with log evidence; template + docs committed; `seldon cc complete`; RESULT; push.
