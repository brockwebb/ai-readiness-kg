# Fixture: `resets_links_only`

**No served files here on purpose.** It serves `../passes_all`'s tree over GET
(`MODES["resets_links_only"]["serves_as"]`) and **resets the connection on every HEAD**.

## Why

`cc_tasks/2026-09-08_scan_harness_v4_RESULT.md` §7.1 named this and could not fix it then, a
shipped rule module being immutable. `RULE-A1-v3` and `RULE-A3-v4` filter link probes through
`_common.served()` — correct — and then return **`fail`** when nothing survives: *"no probed
link serves a structured content type"*, *"no whole-product download linked from the product
page (0 link(s) probed)"*. A page that was SERVED while every one of its links was reset is
scored as offering nothing.

`_common.only_errors` cannot catch it, because the page observation is real. It is harness-v4's
own defect — a verdict from a probe nobody observed — pointed the other way.

## Why HEAD is the discriminator

The shared link probe is a HEAD (`params.link_probe.method`); the page fetch is a GET. Resetting
HEAD alone blinds exactly the links and leaves every other leg seeing what it sees on
`passes_all`. `resets_connection` blinds everything and `invalid_route_unobserved` blinds one
path, so neither can reach this state.

## Pre-registered expectations

`params.e5_control.expected_verdicts.resets_links_only`: **A1 → `error`, A3 → `error`**, every
other leg exactly as `passes_all`. Derived from the rule source before the fixture was first
run. A mismatch is a finding to report, never a line to edit.
