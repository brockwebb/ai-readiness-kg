# RESULT — control fixture: a robots.txt that forbids an in-product probe. **THE GATE FIRED.**

**Task:** `cc_tasks/2026-09-11_control_fixture_robots_forbids_product.md`. No addenda exist;
globbed before starting and again before §3, both times empty.
**Date:** 2026-09-11 UTC
**Spend:** zero model calls. **Network: loopback only** — every observation's host is
`127.0.0.1`, asserted by a test; the one non-loopback hostname on the log is an `off_host` link
recorded with its URL and never requested.

---

## 1. STOP — the fixture caught two rules on its first run

**Decision 4's stop condition fired.** Two rules other than `RULE-A3-v4` returned a verdict
about the product from a probe they were forbidden to make. **No Results were registered. The
fixture is NOT wired into `make guards` or the agreement gate as a passing control.** Decisions
1, 2 and 3 are complete and are what produced the finding; decision 5's wiring is withheld.

```
RULE-A3-v5  fail  "the largest linked download is below the 51200-byte whole-product floor
                   (3 of 8 link(s) were unobserved and are excluded)"
                  — the excluded link is /bulk/estimates-2026.zip, anchor text
                    "whole-product archive". The verdict is "no whole-product download".

RULE-B3-v2  fail  "no structured-text methodology document reachable from the product surface"
                  — 2 observations cited, 1 of them /methodology.html, robots_disallowed.
```

**Each asserts the absence of exactly the object it was forbidden to fetch.** A3 excluded the
one link that would have settled its question and then answered it; B3's only substantive
evidence was the forbidden document.

**Harness-v5 does not catch this, and the reason is precise.** The invariant
(`test_no_verdict_rests_on_unobserved_evidence`) fires when EVERY cited Observation is blind.
Both of these also cite the product page, which was served. Under both harness versions this
fixture reports **0** verdicts on wholly-blind evidence. The class survived the fix in a form
the fix cannot see.

### The asymmetry, which is the finding worth keeping

`RULE-A1-v4`'s docstring chose: *all links blind → `error`; some blind → judge over the rest,
with the blind count on the Finding.* On this fixture A1 returns **`pass`** with three links
forbidden, and that is **sound**: it found `text/csv` on a link it actually fetched, and three
unfetched links cannot unfind it.

The same policy applied to an **absence** claim is not sound. "No whole-product download" and
"no methodology document" are precisely the propositions the forbidden probes would have
settled. A verdict from partial evidence is safe when positive and unsafe when negative, and
generation 6 drew the line at how MUCH was blind rather than at what the verdict CLAIMS.

**This is the eighth instance of the family** (a verdict from a probe the collector never made)
and the first found by a control rather than by reading a payload — which is what the fixture
was built for.

### What the gate says

Six tests fail with one message, and a seventh on the same cause:

```
2 control verdict(s) were not as expected:
  robots_forbids_product:A3=fail (expected error)
  robots_forbids_product:B3=fail (expected error)
```

**The expectation was derived, not transcribed.** `params.e5_control.expected_verdicts` was
written from decision 2's rule — a leg whose decisive probe the partition forbids expects
`error` — before the fixture was run, and it is not being edited to match what came out. The
params file says why in its own comment, and a test asserts the mismatch stands.

## 2. §1 — the fixture and its partition

`assessment/harness/scan/fixtures/robots_forbids_product/`, an overlay on `passes_all`: one
file differs, its `robots.txt`. The partition is declared in `MANIFEST.json` beside it and
checked against the robots rules by a test.

| forbidden path | probed by | legs it blinds |
|---|---|---|
| `/bulk/` | `links.probe` | A1, A3 — the "whole-product archive" link |
| `/estimates-latest.csv` | `links.probe`, `v2clauses.follow_latest_pointer` | A1, A3, A8 |
| `/methodology.html` | `links.probe`, `http.fetch` | A1, A3, B3 |
| `/index.html/__ai-readiness-kg-probe-404__` | `lighthouse.fetch` | A10 — the invalid route |

Allowed: the product page, `/estimates.csv`, `/estimates.json`, `/openapi.json`,
`/changelog.json`, `/llms.txt`, `/sitemap.xml`, `/data.json`.

**5 `robots_disallowed` observations**, from two collectors. §1's stop condition — zero
forbidden-probe rows — did not fire.

**The robots.txt fetch itself is observed** (200, parseable), so A4, A11-declared and A12 read a
real declared layer rather than an absence. A12 returns a verdict, as decision 2 says it must:
the refusal is its subject.

## 3. §2 decision 3 — the replay, RED under v4 and GREEN under v5

```
A10   harness-v4: pass    "deep link HTTP 200; invalid route correctly HTTP None"
      harness-v5: error   "the invalid-route probe … was not observed (robots_disallowed)"
```

The same observations, judged twice. **No rule module differs between the two runs — one entry
in `errors.CLASSES` does.** This is cycle 4's incident reproduced at the control layer, where
it was missing: `invalid_route_unobserved` makes the same shape with a TCP reset, and no fixture
made it with a robots rule until now.

**Exactly one leg moves between the harness versions** on this fixture, and a test asserts it,
so a second leg starting to move is a new finding rather than a quiet improvement.

## 4. Every premise this task got wrong

1. **"At least one leg from each of A-series product legs, B3 and G1-D forbidden, and at least
   one of each allowed" is not satisfiable, and the reason is structural.** B3 and G1-D are
   single legs, so "one of each forbidden and one of each allowed" is a contradiction at leg
   granularity — and more importantly **G1-D, A2, A6, A9, D1 and F4 read only the surface page**
   (`http.fetch`/`structured_data.fetch` on the surface URL). Forbidding the page blinds every
   one of them at once, which is `resets_connection`, not a partition. A robots partition can
   separate legs only where a leg dereferences something. The manifest records this.
2. **`always_fetch_paths` makes four paths unblockable in principle.** `/robots.txt`,
   `/sitemap.xml`, `/llms.txt` and `/data.json` short-circuit `allowed()` to `True`, so A4, A5,
   A12 and D4 cannot be blinded by a Disallow even deliberately. That carve-out is right — a
   robots.txt that disallows `/robots.txt` cannot thereby hide it from a measurement OF
   robots.txt — and it bounds what any fixture of this kind can do.
3. **Decision 4 expected `RULE-A3-v4` to be the known failure.** A3-v4 is not `CURRENT`; A3-v5
   is, and **A3-v5 fails this fixture too**, for a different reason than v4 would. v4 never
   consults the blind guard at all; v5 consults it per link, excludes the blind ones, and then
   makes an absence claim over what is left. The pinned-xfail-by-ResearchTask-`969f73c6` shape
   decision 4 describes does not fit: the gap is not "A3 has no guard", it is "the guard does
   not ask what the verdict claims".
4. **Decision 5's wiring could not be done**, and not only because of the stop: adding the
   fixture to `MODES` forces a `params.e5_control.expected_verdicts` entry
   (`set(expected) == set(MODES)`, asserted), so there is no way to make the fixture runnable
   without pre-registering an expectation for it. The expectation registered is the derived one,
   which is why the gate is red rather than the fixture being absent.

## 5. Two things I broke and fixed, neither a finding

1. **My own exploratory runs littered the redirect log with 282 entries.** `run_surface` stores
   bodies through `model.EVIDENCE_ROOT`, which defaults to the committed store, and only
   `run.py::main` may write there (DD-063). The guard redirected every write and `make guards`
   reported it — working exactly as built. Swept with `scripts/quarantine_fixture_evidence.py`,
   and the test now stages evidence into `tmp_path` the way `run.py::main` redirects before
   collecting anything, so it leaves nothing behind on a suite run.
2. **E5's `collector_pin` is derived from the fixture roster**, so growing the set to eight made
   `framework/ai_readiness_framework.json` stale and
   `test_the_rule_write_back_is_idempotent` red. Ran `framework_writeback_rules.py` and
   `load_framework_graph.py`, per CLAUDE.md's standing rule. The pin now names all eight
   fixtures. The write-back's own comment anticipated this: *"the fixture set grew twice, and a
   guard keyed on the collector NAME would have left the framework of record naming two of five
   forever."*

## 6. Verification

```
logs/cf2_fixture.log    8 passed, 2 xfailed (the finding, pinned strict)     2 s   EXIT=0
logs/cf2_rederive.log   12 of 12 payloads byte-identical                     5 s   EXIT=0
logs/cf2_invariant.log  45 passed, 4 xfailed — no stored payload moved      20 s   EXIT=0
logs/cf2_guards.log     12 passed — redirect log clean                      15 s   EXIT=0
logs/cf2_full.log       1755 passed, 7 FAILED, 17 skipped, 6 xfailed      1192 s   EXIT=1
logs/cf2_verify.log     seldon verify — All checks passed                          EXIT=0
logs/cf2_protected.log  protected paths — rule modules, stored payloads,           EXIT=0
                        prior RESULTs, cycle evidence, targets, docs/reports/
                        and the seven existing fixtures all unchanged;
                        params.yaml +27 lines, the derived expectation alone

the 7 failures, all one cause:
  test_scan_harness_v3::test_the_control_gate_passes_on_all_four_fixtures
  test_scan_harness_v4::test_the_control_gate_passes_on_all_five_fixtures
  test_virtual_time::test_the_control_gate_returns_the_same_verdicts_on_both_clocks
  test_scan_harness::test_findings_re_derive_byte_identically_from_stored_observations
  test_scan_harness::test_merging_controls_replaces_them_rather_than_accumulating
  test_scan_harness::test_the_cycles_own_validity_verdict_is_on_the_record
  test_scan_harness::test_the_re_derivation_gate_covers_the_control_findings_too

  Each runs a control cycle; the cycle is INVALID while a control fires. That is what a
  fired positive control does, and the red stays until the rules are fixed.
```

**No cycle may run while this is red** — `run_controls` returns `ok=False`, which is the
designed consequence and the reason this task precedes any cycle 5.

## 7. What the next task needs

1. **The fix is in the rules, not in the fixture or the class table.** A3 and B3 must
   distinguish "I looked and found none" from "I was forbidden to look at the candidate". The
   shape that generalises: a rule making an ABSENCE claim must return `error` when a blind probe
   could have falsified it — which is `unobserved_error` asked about the claim rather than about
   the probe set. `RULE-A3-v6` and `RULE-B3-v3`; A3-v5 and B3-v2 stay in `REGISTRY` re-deriving
   the four cycles that used them.
2. **Then wire decision 5**: the fixture into `make guards` and the agreement gate, and the
   eight-fixture control gate goes green. It is one line in the Makefile and nothing else — the
   fixture, its manifest, its table and its tests are all in place and passing on everything
   except the two rules.
3. **A1-v4's policy should be re-read, not changed.** It is right for an existential-positive
   leg and this fixture shows it holding. The next version of A3 should not copy it.
4. **Check the other absence-claim legs against this fixture once they are fixed**: A2, A6, A9,
   D1, D4, F4 and G1-D all make absence claims and all read only the surface here, so this
   fixture cannot exercise them. A fixture that forbids a SECOND page — one they dereference —
   would, and there is no such page in `passes_all` to forbid.
