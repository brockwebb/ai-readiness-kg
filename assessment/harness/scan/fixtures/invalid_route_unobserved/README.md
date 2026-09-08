# Fixture: `invalid_route_unobserved`

**This directory holds no served files on purpose.** The fixture serves `../passes_all`'s tree
(`MODES["invalid_route_unobserved"]["serves_as"]`), and differs from it in exactly one way:
the connection is **reset** — RST, `SO_LINGER` zero, as in `resets_connection` — for the one
path A10 invents to test the error shell, and only for that path. The suffix comes from
`params.a10_soft404.invalid_path_suffix`, never from a literal here.

## Why it exists

`cc_tasks/2026-09-07_scan_run_2_RESULT.md` §6.2. On `scan-eia-flagship-1-open-data` the A10
invalid-route probe raised `RemoteProtocolError: Server disconnected without sending a
response` — `error_class: connection_reset`, which `errors.CLASSES` marks **blind** — while the
valid-route probe was served HTTP 200. `RULE-A10-v2` tests only that the invalid route is not
200, so a killed connection read as a correct rejection and the surface scored **pass**, with
the reason printing `invalid route correctly HTTP None`.

`resets_connection` cannot catch that. It resets *every* path, so every leg is `error` and the
surface is uniformly unobservable; the state that produced the false positive is *partial*
blindness, and only a fixture that serves everything else can reproduce it.

## Pre-registered expectations

In `params.e5_control.expected_verdicts.invalid_route_unobserved`, derived from the rule source
BEFORE the fixture was first run: **A10 → `error`**, every other leg exactly as `passes_all`.
A mismatch is a finding to report, never a line to edit.
