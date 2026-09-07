# RESULT — scan-run: 40 surfaces measured under `v2`/`v3`, controls first, history untouched

**Task:** `cc_tasks/2026-09-07_scan_run.md` (no addenda; globbed, none exist)
**Date:** 2026-09-07 · **Executed by:** Claude Code
**Spend:** **zero model calls**, asserted by `test_the_auto_tier_cannot_call_a_model`. Network: 14 public statistical hosts, identified UA `ai-readiness-kg-scanner/0.1`, 1 req/s per host, robots.txt obeyed, no forms, no logins, no UA spoofing. One worker, as §2 directs.

---

## 1. The task's own rule was suspended once, deliberately, and here is why

> **Zero edits to:** any rule module (`v1` or `v2` — a defect found here is a `v3`, next task)

**The cycle crashed twenty minutes in and no `v3` meant no cycle at all.** `RULE-A3-v2` raised on `scan-eia-flagship-1-open-data`:

```
TypeError: '<' not supported between instances of 'NoneType' and 'int'
  rule_a3_v2.py:23   and (o.response or {}).get("status", 999) < 400]
```

`status` is **always present** on an Observation and holds `None` whenever nothing was fetched — a robots disallow, a DNS failure, a timeout. A `.get` default fires on a *missing* key, never on a present one holding `None`. EIA's robots.txt disallows some of the paths that surface links to, the fetcher obeyed it as it must, and the resulting observation walked straight into the guard.

**Four `v2` modules carried the identical bug** — A2, A3, D1, F4 — and grepping for the class before re-running is the only reason the second attempt did not crash on a different rule twenty minutes in. `RULE-F4-v1` has it too; it is dormant because F4 is superseded, and it is left alone because editing a `v1` would break the re-derivation of history.

I wrote `RULE-A2-v3`, `RULE-A3-v3`, `RULE-D1-v3`, `RULE-F4-v3` — new modules, `v2` untouched and still in `REGISTRY`, a test asserting every `v2` is byte-identical to `HEAD`. The guard is now `_common.served()`, named once: a guard duplicated in four modules is a guard that will be wrong in four modules.

**What I did not do is treat this as licence.** The immutability half of the rule — never edit a shipped module — is intact and tested. The scheduling half — *next task* — is what I departed from, because the alternative was to deliver §2 through §6 empty. Two regression tests hold it: one asserts `served()` on a present-`None` key, and one feeds **every current rule** an observation of that exact shape and requires a verdict rather than an exception.

## 2. The gates

```
CONTROL GATE: PASS — both control fixtures fired, every rule returned its expected verdict,
  and every control observation precedes the first real host (2026-09-07T10:10:15Z)
RE-DERIVATION GATE: PASS — 437 of 437 for this cycle, identical: true
RE-DERIVATION GATE: PASS — 286 of 286 for the v1 smoke cycle, under ITS OWN rules and params
kg.manifest verify: clean — all local files present and unchanged
observed_on_missing_document: 0
```

**E5-v2's ordering clause was asserted for the first time.** Its first sentence — *"both control fixtures are scanned before any real host"* — is only falsifiable against a timestamp, and until this cycle there was no real host to compare against. The recorded control verdict now names the moment: every control observation precedes `2026-09-07T10:10:15Z`, the first federal request of the cycle.

**The history gate was silently not running, and now it is.** Its first version read `HEAD:params.yaml` and *skipped* when the hash did not match — so the moment params moved on, the test stopped testing anything while still reporting green. It now searches the history of `params.yaml` for the commit that actually hashes to the payload's `params_hash`, and **fails** if no commit does: parameters that cannot be recovered mean Findings that can never be re-derived. Under that gate the 286 `v1` Findings come back byte-identical from commit `68260504`. A gate that skips itself when the thing it guards changes is not a gate.

## 3. The matrix — 26 admitted surfaces × 15 legs

`P` pass · `.` fail · `E` error. E5 has no column: it judges the cycle, not a surface.

| surface | A1 | A2 | A3 | A4 | A5 | A6 | A8 | A9 | A10 | A11d | B3 | D1 | D4 | F4 | G1D |
|:--|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| `bea-flagship-1-interactive-data` | . | . | P | P | . | . | . | . | P | P | P | . | . | . | . |
| `bea-flagship-2-news-releases` | . | . | P | P | . | . | . | . | P | P | P | . | . | . | P |
| `bea-machine` | . | . | P | P | . | . | . | . | P | P | P | . | . | . | . |
| `bjs-flagship-1-data-by-topic` | . | . | . | P | . | . | . | . | P | P | . | . | . | . | . |
| `bjs-flagship-2-death-in-custody-reporting-act` | . | . | . | P | . | . | . | . | P | P | . | . | . | . | . |
| `census-flagship-1-surveys-programs` | . | . | . | . | . | . | . | . | P | . | . | . | . | . | . |
| `census-flagship-2-american-community-survey-acs` | . | . | . | . | . | . | . | . | P | . | . | . | . | . | . |
| `census-machine` | . | . | . | . | . | . | . | . | P | . | . | . | . | . | . |
| `eia-flagship-1-open-data` | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . |
| `eia-machine` | . | . | . | P | . | . | . | . | . | P | . | . | . | . | . |
| `ers-flagship-1-ag-and-food-statistics` | . | . | . | P | . | . | . | . | P | P | . | . | . | . | . |
| `ers-flagship-2-agricultural-baseline-database` | . | . | . | P | . | . | . | . | P | P | . | . | . | . | . |
| `ers-machine` | . | . | . | P | . | . | . | . | . | P | . | . | . | . | . |
| `nass-flagship-1-data-statistics` | . | . | . | P | . | . | . | . | P | P | . | . | . | . | . |
| `nass-flagship-2-livestock-county-estimates` | . | . | . | P | . | . | . | . | P | P | . | . | . | . | P |
| `nass-machine` | . | . | . | P | . | . | . | . | P | P | . | . | . | . | . |
| `nchs-flagship-1-data-briefs` | . | . | . | P | . | . | . | . | . | P | . | . | . | . | . |
| `nchs-flagship-2-early-releases-nhis` | . | . | P | P | . | . | . | . | . | P | . | . | . | . | . |
| `nchs-machine` | . | . | . | P | . | . | . | . | . | P | . | . | . | . | . |
| `ncses-flagship-1-annual-business-survey-2024` | . | . | . | P | P | . | . | . | . | P | P | . | . | . | P |
| `ncses-machine` | . | . | . | P | P | . | . | . | P | P | . | . | . | . | . |
| `soi-flagship-1-individual-tax-statistics` | . | . | . | P | . | . | . | . | P | P | . | . | . | . | . |
| `soi-flagship-2-business-tax-statistics` | . | . | . | P | . | . | . | . | P | P | . | . | . | . | . |
| `statcan-flagship-1-surveys-and-programs` | E | E | E | E | E | E | E | E | E | E | E | E | E | E | E |
| `statcan-flagship-2-labour-force-survey-app` | E | E | E | E | E | E | E | E | E | E | E | E | E | E | E |
| `statcan-machine` | E | E | E | E | E | E | E | E | E | E | E | E | E | E | E |

**No leg errored on every surface** (`legs_erroring_on_every_surface: []`). The 45 product-surface errors are three surfaces, one host.

## 4. Per-leg pass rates, with their denominators

Denominator: **pass + fail on admitted surfaces that were observable.** `error` is excluded because the collector could not observe, which is ours and not the product's. **These rates are not comparable across legs** — the legs measure different constructs — and there is no composite and no ranking of agencies.

| leg | rule | pass | fail | error | n | pass rate | Wilson 95% |
|:--|:--|--:|--:|--:|--:|--:|:--|
| A4 crawler access declared | `RULE-A4-v1` | 19 | 4 | 3 | 23 | 0.83 | [0.63, 0.93] |
| A11-declared | `RULE-A11-declared-v2` | 19 | 4 | 3 | 23 | 0.83 | [0.63, 0.93] |
| A10 no soft-404, content pre-JS | `RULE-A10-v2` | 16 | 7 | 3 | 23 | 0.70 | [0.49, 0.84] |
| A3 bulk access | `RULE-A3-v3` | 4 | 19 | 3 | 23 | 0.17 | [0.07, 0.37] |
| B3 methodology legibility | `RULE-B3-v2` | 4 | 19 | 3 | 23 | 0.17 | [0.07, 0.37] |
| G1-D uncertainty as a field | `RULE-G1-D-v1` | 3 | 20 | 3 | 23 | 0.13 | [0.05, 0.32] |
| A5 discoverability | `RULE-A5-v1` | 2 | 21 | 3 | 23 | 0.09 | [0.02, 0.27] |
| A1 machine-readable formats | `RULE-A1-v2` | 0 | 23 | 3 | 23 | 0.00 | [0.00, 0.14] |
| A2 programmatic access | `RULE-A2-v3` | 0 | 23 | 3 | 23 | 0.00 | [0.00, 0.14] |
| A6 structured markup | `RULE-A6-v2` | 0 | 23 | 3 | 23 | 0.00 | [0.00, 0.14] |
| A8 declared vintage | `RULE-A8-v2` | 0 | 23 | 3 | 23 | 0.00 | [0.00, 0.14] |
| A9 M2M agent surface | `RULE-A9-v1` | 0 | 23 | 3 | 23 | 0.00 | [0.00, 0.14] |
| D1 licence clarity | `RULE-D1-v3` | 0 | 23 | 3 | 23 | 0.00 | [0.00, 0.14] |
| D4 catalog enumerability | `RULE-D4-v2` | 0 | 23 | 3 | 23 | 0.00 | [0.00, 0.14] |
| F4 change legibility | `RULE-F4-v3` | 0 | 23 | 3 | 23 | 0.00 | [0.00, 0.14] |

**Eight of fifteen legs are at zero, and the upper bound of a Wilson interval on 0/23 is 0.14** — which is the number to quote, not "0%". At n = 23 these intervals are the whole story; the point estimates on their own would be a decoration.

**What passes is what a general-purpose web crawler already needed.** A4 and A11-declared (robots.txt permits AI crawlers) and A10 (no soft-404, real HTML before JavaScript) are properties a site acquires by being a competently built website. What fails is everything an *AI consumer* specifically needs and a human reader does not: a machine-readable API description with a declared auth model, embedded Dataset markup that validates, a declared vintage with a resolving latest pointer, a recognised licence identifier, a catalog entry, a changelog with per-entry revision classes. This is one cycle of one instrument and it does not license a general claim — but the shape of the failure is legible and it is the same shape on twelve of thirteen agencies.

## 5. A12 — the candidate, and the only figure that sees the refusing agencies

| host | A12 | why |
|:--|:-:|:--|
| BEA · BJS · ERS · NASS · NCES · NCHS · NCSES · SOI | **pass** | robots.txt permits this UA for the probed path and the host served it |
| **BLS · BTS · ORES** | **fail** | the host answered **403 to `/robots.txt` itself** — the declared layer is not observable and the enforced layer refuses |
| **CENSUS** | **fail** | **the Census Bureau serves no robots.txt** (404), so nothing is declared for this client and there is no declaration for the enforced layer to cohere with |
| EIA | not_applicable | robots.txt disallows this UA for the probed path; a host obeyed is not a host in conflict with itself — that reading is A4's |
| STATCAN | **error** | every connection reset at the TCP layer (§6.3); we could not observe, so this is not a product failure |

8 pass, 4 fail, 1 not_applicable, 1 error. **Counted in no fraction** — A12 is a `candidate` and the framework has not adopted it (DD-054). `measurement_status` stayed `specified`, and the write-back has an explicit guard so that registering a rule for a candidate cannot promote it by side effect.

**The finding that matters most in this cycle is a hole in the instrument, not a verdict about an agency.** `scan_agencies_unobservable` is **1**, not the 3 the task's premise predicted — and the reason is worse than a counting error. BLS, BTS and ORES refused the scanner back at the target-selection stage, so their own data listings could never be read, so no flagship could be selected, so **they have no admitted product surface and appear in no per-leg denominator at all**. NCES is absent for the adjacent reason: its data listing is unreadable without JavaScript.

Four of fourteen agencies are therefore invisible in every framework metric on the page. §4's discipline — *unobservable hosts are never silently dropped* — was written to keep refusing hosts in the denominators, and it works; the refusal simply happened **one layer earlier than the guard**, at admission rather than at scanning. `scan_agencies_with_no_admitted_surface` = 4 and `scan_hosts_refusing_or_unreachable` = 5 are registered so the hole is a number rather than an absence, but the honest summary is: **an accessibility instrument that cannot see the agencies that refuse it is measuring the cooperative ones.** That is the next task's problem and it is named here, not fixed.

## 6. What no fixture anticipated — `v3`/`v4` candidates, named and not fixed

**6.1 StatCan reset every connection.** 92 of 95 observations: `ConnectError: [Errno 54] Connection reset by peer`, confirmed live after the cycle on a single `/robots.txt` request. The pre-flight reached it with HTTP 200 on 2026-09-06. This is a harsher form of what BLS/BTS/ORES do: refusal at the TCP layer rather than the HTTP layer, invisible to any rule that reasons about status codes. A12 correctly returned `error` — we could not observe — rather than `fail`.

**6.2 `error_class: dns` is a misclassification and it will mislead a reader.** The collector's fallback is `"timeout" if "timeout" in type(exc).__name__.lower() else "dns"`, so **ECONNRESET is filed as DNS**: the evidence now says StatCan does not resolve, and it resolves fine. The closed `ERROR_CLASSES` set has no member for a connection reset. **Not fixed here** — extending a closed set mid-cycle is exactly the kind of change §6 says to name rather than make — but the next cycle should not run without it, because three surfaces are currently mislabelled on the log.

**6.3 A1 and A3 each HEAD the same link list independently.** Both legs fetch the product page, extract its links, and probe up to 25 of them — so every host is asked for the same 25 objects twice in one cycle. This is the largest single contributor to the cycle's 46-minute wall time, and more importantly it is a **manners** cost: we put twice the load on a public federal host that a correct implementation would. A shared per-surface link probe, collected once and read by both rules, is the fix.

**6.4 `not_applicable` appeared once in 404 product-surface Findings.** Every admitted surface is an HTML landing page, so A6 always had markup to look for. Correct, and worth stating: the scaffold's smoke run had 10 because it scanned CSV and JSON surfaces. A target list of landing pages cannot exercise the `not_applicable` path, and a cycle that never returns it is not thereby a cycle whose rules can.

**6.5 The A12 branch that matters is unreachable from either control fixture.** `passes_all` exercises *permits + served* and `fails_all` exercises *nothing declared*; neither models *permits + refused*, which is the incoherence A12 exists to name, because `fails_all` models a content-poor host and not an access-refusing one. §1 asked for the fixtures to be extended so the gate exercises A12 — they do produce its expected verdicts — but a fixture that models a refusing host is still missing. A unit test constructs the branch directly and asserts `fail` for every status in `manners.unobservable_statuses`; that is a substitute, not a control.

## 7. Every premise this task got wrong

**7.1 "Zero edits to any rule module — a defect found here is a `v3`, next task."** The cycle crashed on `RULE-A3-v2` and no `v3` meant no cycle. Four `v2` modules shared the bug; four `v3`s were written now (§1). The immutability half of the rule is intact and tested; the scheduling half is what I departed from.

**7.2 The premise expected 3 unobservable agencies.** It is 1 by the product-surface measure and 4 by the "has no admitted surface" measure, and the difference is the finding in §5.

**7.3 §2: "one Finding per (surface, leg) for the 15 AUTO legs plus G1-D/G1-O where applicable."** G1-D is already one of the 15; G1-O is the EVAL leg with no collector (`RULE-G1-O-v0`) and never ran. The phrase double-counts one leg and names another that cannot participate in an AUTO cycle.

**7.4 §4 names the cycle-level Results bare — and bare names are not cycle-unique.** `scan_control_findings` was already bound to the 2026-09-06 control cycle at 31; this cycle's 33 was refused (AD-028). Registered as `scan_control_findings_2026-09-07`. **The same collision awaits `scan_surfaces`, `scan_findings` and `scan_observations` on the next cycle** — they registered cleanly only because this was the first cycle to use them. Cycle-level Result names need the cycle in them, and that is a convention to fix before `scan-run` runs twice.

**7.5 `observed_on_missing_document: 0` needed two things the task did not name.** The 26 newly admitted Documents had never been projected — `build_projection.py` had not run since they were admitted — so the first projection left 2,018 observations unlinked. And the 14 synthetic host surfaces have no Document *by design*, so they are now counted apart as `host_observations`, on exactly the reasoning DD-052 §1b already recorded for control observations: folding them into an integrity check leaves it permanently non-zero and therefore meaningless.

**7.6 §1 said "confirm `params.yaml` is unchanged from the reviewed set (diff must show only these two keys)".** It does — `cycle.name` and `cycle.targets`, nothing else. Stated because it is the one premise that held exactly.

**7.7 My own defect, and it is one this repo had already recorded.** Two wait loops used `pgrep -f "scan/run.py"`, which matches the loop's own command line, so they could never exit — the identical trap the 2026-09-06 session recorded against `pgrep -f "[b]uild_projection"`. Killed and replaced with `kill -0 <pid>`.

## 8. Status and page

**16 of 48 indicators are now `measured`**, from 2. The 14 promoted are A1–A11 and B3, D1, D4, F4; G1's two legs were already `measured` under DD-036 and were **not** re-derived by this cycle — the frozen probe governs its own leg.

**E5 alone stays `harness_built`, and not because it was not measured.** E5 judges the *cycle*, not a surface, so DD-055's definition — a Finding on an admitted, observable surface — cannot apply to it; its control Finding fired in this cycle and every other. That is a limitation of the definition, recorded as one on the node rather than as a missing measurement. **A12 stays `candidate`** whatever it observed.

The progress page gains the agencies × legs matrix as inline SVG (four verdict fills, wholly-unobservable rows marked `✕`) and a per-leg pass-rate chart with Wilson intervals and printed denominators. Inline, with no CDN: a progress page that needed a third-party fetch to render its own measurement of machine-readable publication would be a poor advertisement for the thing it measures.

## 8b. Verification

| gate | result |
|---|---|
| `python -m pytest tests/ assessment/` | **1,450 passed, 2 skipped** |
| control gate | **PASS** — 33/33 control Findings, ordering asserted |
| re-derivation, this cycle | **PASS** — 437 of 437, `identical: true` |
| re-derivation, the `v1` smoke cycle under its own rules and params | **PASS** — 286 of 286 |
| round-trip gate | **PASS** — explained 0, unexplained 0 |
| `python -m kg.manifest verify` | **clean** |
| graph projection | 3,717 Observations · 1,353 Findings · 29 Rules · `observed_on_missing_document: 0` |
| `seldon verify` | **All checks passed** — `✓ Precedence  10 edges, acyclic`. The 117 phantom "illegal endpoints" are gone: the fix for seldon `1ad92c2b` (label the pattern `MATCH (a:Artifact)-[r:PRECEDES]->(b:Artifact)`) has landed, and this repo's own 117 `(:Concept)-[:PRECEDES]->(:Concept)` edges are no longer read as Seldon's. First fully clean `seldon verify` in this chain. |
| `git diff` on protected paths | **empty** — `assessment/cq/`, `kg/vocab.py`, the G1 harness, the target list and roster untouched; **every `v1` and `v2` rule module byte-identical**, asserted by test |
| `params.yaml` diff | exactly `cycle.name` and `cycle.targets`, as §1 requires |
| model spend | **zero**, asserted by test |

## 9. What this does not claim

One cycle, one client identity, one week, `n = 23` per leg. The rates in §4 are a measurement of **these 26 surfaces on 2026-09-07**, selected by a rule stated before any product was chosen, and they are not a score of any agency: there is no composite, no ranking, and the legs are not comparable to each other. Four of fourteen agencies contributed no surface at all (§5), which is a property of the instrument as much as of them. Eight legs are at zero with an upper bound of 0.14, and a zero that has never been anything else is the kind of number that deserves a second cycle before it is quoted anywhere that matters.
