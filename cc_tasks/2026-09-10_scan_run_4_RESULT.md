# RESULT — scan-run-4: the cycle ran, the gate STOPPED it before registration

**Task:** `cc_tasks/2026-09-10_scan_run_4.md`. No addenda exist; globbed at dispatch and again
before §2, both times empty.
**Date:** 2026-09-10 UTC
**Spend:** zero model calls. **Network:** 2,684 requests over 35 netlocs, all on the 19 declared
site keys, robots-first through the fetcher.

---

## 1. THE GATE FAILED. No Results are registered, no page or figures were rebuilt.

**What failed:** fourteen Findings in this cycle carry a `pass` or `fail` verdict about a
product while **every observation they rest on is one the collector never made.** Task decision
4 pre-registers the invariant they break — *"`error` never means the product failed (DD-052
§6)"* — and its mirror, that `error` must never mean the product passed either.

The two that state the problem in one line each:

```
fail  RULE-A1-v4   flagship:www.bls.gov/cpi/
      "no probed link serves a structured content type (1 link(s) observed)"
      The page answered 403. The links it "observed" were parsed out of the REFUSAL page,
      and the one that was probed was itself refused. The Consumer Price Index is scored
      `fail` on a measurement of an access-denied page.

pass  RULE-A10-v3  scan-eia-flagship-1-open-data
      "deep link HTTP None; invalid route correctly HTTP None"
      Both probes were disallowed by robots.txt and never issued. HTTP None is not a
      correct rejection; it is no rejection at all.
```

**§3's own enumerated clauses all pass** (table in §2). This is not one of them; it is the
invariant the task file states in decision 4, checked because decision 4 said to check it, and
it is why §3's failure clause applies: *"Failure writes no Results and no page: report and stop,
RESULT with the block on top, commit, push."*

**What was done anyway, and why.** The payload, the promoted evidence and the events are
committed (`c388b5c`). The Observations are sound — they record exactly what happened, including
the refusals — and the measurement cannot be taken again. Only the *judgement* over them is
wrong, and this repo corrects a judgement by re-judging into a new payload
(`scan_2026-09-07_rj1`, `scan_2026-09-07b_rj1`), never by editing an event. The next task can
fix the rules and re-judge cycle 4 without contacting a single host.

**Why registration is the line.** A Seldon Result name binds once (AD-028). Registering the A1
and A3 leg rates today would put a number I already know to be wrong into a name that cannot be
corrected — only superseded. The rates are contaminated by three false `fail`s each out of 62
tier-A product surfaces; small, and permanent.

### Root cause, one line of `errors.py`

`robots_disallowed` is declared `blind: False`. `rules/_common.unobserved()` reads
`errors.BLIND`, so **a URL that was never fetched reports as observed**, and every rule
downstream treats "we were forbidden to look" as "we looked and found nothing".

```python
"robots_disallowed": {"blind": False, "not_fetched": True, ...}
BLIND       = ('dns','timeout','connection_reset','refused','http_5xx','parse_error',
               'collector_unavailable','unknown')
NOT_FETCHED = ('robots_disallowed','sitemap_off_site','off_host')   # read by nothing in rules/
```

`blind: False` is **right for `off_host`** and the comment beside it says why: an off-host link
is a scope boundary, and marking it blind would let a page whose links all point elsewhere
return `error` instead of the `fail` it has earned. `robots_disallowed` was given the same flag
and is not the same thing. An off-host URL is outside the product; a robots-disallowed URL is
*inside* the product and we were refused permission to look at it. That is blindness by any
reading, and `NOT_FETCHED` — added later, naming the truth that no request was made — is not
consulted by a single rule.

**This is the seventh instance of one defect family** (a verdict from an unobserved probe) and
the first where the fix is one flag rather than one rule.

### It is not new, and cycle 4 did not create it

| cycle | verdicts resting on no observed evidence |
|---|---|
| `scan_2026-09-07b` (cycle 2) | 9 |
| `scan_2026-09-09` (cycle 3) | 9 |
| `scan_2026-09-10` (cycle 4) | **14** |

Cycles 2 and 3 carry it too, and **their Results are registered and cited in the L0 report.**
Six of the nine in each are EIA's robots-disallowed flagship; three are A12 (examined below and
sound). Cycle 4 adds five: BLS's home and flagship gained A1/A3 verdicts once the flagship
surface existed, and EIA's A10 flipped to a `pass` from two unissued probes.

**What the next task must decide is not whether to fix the rules — it is what to do about two
registered cycles that contain the same defect.** That is a question about the record, not about
the code, and re-judgement payloads are the mechanism this repo already has for it.

### The three A12 verdicts are examined and SOUND

`RULE-A12-v1` returns `fail` on `host:www.bls.gov`, `host:www.bts.gov` and `host:www.ssa.gov`,
reason *"the host answered HTTP 403 to /robots.txt itself"*. My filter counts these as
"resting on no observed evidence" because a 403 is in `manners.unobservable_statuses` — but
A12's subject **is** the refusal. Declare-vs-enforce asks what the host enforces, and a 403 on
`/robots.txt` to a compliant identified client is the enforcement, observed. A12 is also a
candidate indicator (DD-054), in no denominator. These three are correct and unchanged since
cycle 1; they are listed here so the count of fourteen is not read as fourteen defects.

## 2. §3, clause by clause

| clause | result |
|---|---|
| Byte-identical re-derivation, this cycle and all prior (9 of 9) | **PASS** — 852 recorded, 852 re-derived, identical |
| Zero Tier C Findings outside `tier0.legs` | **PASS** — 9 Tier C rows, 6 legs, all in the set |
| Zero duplicate Finding identities across rows of one host | **PASS** — 739 of 739 cycle Findings distinct (852 with the 113 control Findings) |
| Every request same-site to a roster site key | **PASS** — **0 off-site** over 35 netlocs |
| Every netloc's `robots.txt` read before its first fetch | **PASS** — 0 robots-late (§3 explains how this is checked) |
| Requests refused by the site bound | **0** |
| Hygiene: `corpus/` shows only this cycle's promoted bodies | **PASS** — 555 new files, **0 modified, 0 deleted** |
| Events append-only | **PASS** — `batch-029.jsonl` +3,862 / **-0** |
| `seldon verify` | **PASS** — All checks passed |
| Protected paths | **PASS** — rule modules, targets v5, prior RESULTs, report, graph page, G1, `assessment/cq` all unchanged; `params.yaml` touched only in `cycle.*` |
| Control gate | **PASS** — both fixtures fired, every rule returned its expected verdict, 113 control Findings |
| **The invariant of decision 4** | **FAIL — §1** |
| Fast tier / full suite | **RED, and deliberately** — §5 |

## 3. §1 and §2 — what ran

**§1.1.** `params.cycle.targets` → `scan_targets_fss_2026-09_v5`, `cycle.name` →
`scan_2026-09-10`, `params_hash` `4e0a92ba19ab…`. `refuse_clobber` was then driven against
**every** existing `state/scan_*.json`: it refuses all 15 that carry a `params_hash` and passes
the 4 that are target and pre-flight files rather than cycle payloads. Neither cycle-4 output
path existed.

**§1.2.** Control gate: 18 checks, EXIT=0 in 32 s — the fixtures under `CURRENT`, `unknown` = 0
on the fixtures, derived tables agree, both-clocks agreement 0 differences.

**§2.** One pass over targets v5, 55 minutes:

| | cycle 3 | cycle 4 |
|---|---|---|
| surfaces measured | 64 | **71** |
| Observations | 2,429 | **2,718** |
| Findings | 634 | **739** (+113 control) |
| requests | 2,341 | **2,684** |
| verdicts | 143 pass / 426 fail / 65 error | **162 pass / 481 fail / 96 error** |

The 71 is 72 target rows less `scan-eia-flagship-2-eia-survey-forms`, which the frame already
records as `not_admitted: robots_disallowed` — no Document, so no Finding, and the frame says
so on the row rather than letting a reader assume every declared surface is measurable.

### Requests per site — the manners claim

```
aphis.usda.gov     121   bea.gov            233   bjs.ojp.gov        183
bls.gov             74   bts.gov             71   cdc.gov            223
census.gov         246   data.gov            30   eia.gov            142
ers.usda.gov       243   federalreserve.gov 123   gsa.gov             28
irs.gov            185   nass.usda.gov      244   nces.ed.gov        128
ncses.nsf.gov      184   nist.gov            28   samhsa.gov         127
ssa.gov             71
                                    TOTAL  2,684 over 35 netlocs on 19 sites
```

### A premise the task file got wrong: "the 22 netlocs of targets v5 and no other"

The frame is 22 netlocs. **The contact set is not, and never was** — cycle 3 reached 24, this
cycle 35. A statistical agency serves its products from siblings of its own host:
`apps.bea.gov`, `data.census.gov`, `wonder.cdc.gov`, `sa.www4.irs.gov`. DD-063 binds the scanner
to the **site**, by RFC 6265 §5.1.3 domain matching, precisely so a deep link into a body's own
tooling is followable and a hop to another body's host is not. A bound of "the roster netlocs
and no other" would score every agency that uses a subdomain as unreachable — a measurement of
our frame, not of their publishing.

The number that holds is the **site** count, and it is 19 in both cycles. Zero requests left the
site bound. The same wording reached the dispatch line, so it is named here rather than left to
be noticed later.

### How "0 robots-late" is checked, since the Observations cannot answer it

An Observation records a request, but the fetcher issues requests no Observation carries:
`/robots.txt` is read inside `_robots_for`, and a link probe issues one HEAD per link inside a
single Observation's `parsed`. Eleven of the 33 netlocs carrying Observations have no
`/robots.txt` Observation, and every one of them was read. Two further netlocs
(`data.bls.gov`, `quickstats.nass.usda.gov`) appear in the socket log with **one** request each
and no Observation at all: robots was read, the path was disallowed, nothing else was asked.

So the check is the socket counter against the Observations: for **all 33**, the socket count
leaves room for the robots read. Structurally, `raw_get` and `raw_head` both enter through
`_gate`, which is what DD-062 moved into the fetcher so no collector could forget it, and
`test_manners_robots_first.py` drives that against a live fixture.

## 4. The seven flagships, first cycle

**The four reachable ones produced real verdicts.** None errored on every leg, so no declaration
names a page the scanner cannot read at all (frame-v5 RESULT §6 item 3).

| body | pass | fail | error | legs passed |
|---|---|---|---|---|
| DRSMSU (Survey of Consumer Finances) | 5 | 10 | 0 | A6, A8, A10, D4, G1-D |
| NAHMSAPHIS (NAHMS studies) | 3 | 12 | 0 | A4, A10, A11-declared |
| NCES (Digest of Education Statistics) | 4 | 11 | 0 | A3, A4, A10, A11-declared |
| SAMHSACBHS (NSDUH) | 4 | 10 | 1 | A4, A5, A10, A11-declared |

DRSMSU is the interesting row: it is the only one of the four that passes A6 (structured markup)
and G1-D (error measures as structured fields), and the only one that fails A4 and
A11-declared. It is a different publishing posture from the other three, not a better or worse
one, and one cycle is not enough to say more.

**The three refused ones.** BTS and ORES are `error` on all fifteen legs, which is correct and
is what decision 4 expects: a host that refused us told us nothing about its product. **BLS is
not** — A1 and A3 read `fail` — and that is §1.

## 5. Verification

```
logs/c4_preflight_gate.log  control gate, derived tables, both clocks   32 s   EXIT=0
logs/cycle4.log             the cycle, 71 surfaces                    3278 s   EXIT=0
logs/c4_publish.log         3,010 obs + 852 finding events, projected  422 s   EXIT=0
                              observed_on_missing_document = 0
logs/c4_fast.log            1,659 passed, 3 failed, 8 errors           296 s   EXIT=1
logs/c4_full.log            1,670 passed, 4 failed, 8 errors           733 s   EXIT=1
logs/c4_verify.log          seldon verify — All checks passed                  EXIT=0
logs/c4_protected.log       protected-paths diff                               EXIT=0
```

**The suite is red, and every red line is accounted for:**

1. `test_scan_run_4.py::test_the_refusing_three_are_error_and_never_a_verdict_about_the_product`
   — **the gate finding itself.** It is left failing on purpose. A test that reports the defect
   and then gets deleted or relaxed is how a defect becomes a convention.
2. `test_scan_figures.py`, 2 failures and 8 errors, all
   `FileNotFoundError: state/scan_matrix_2026-09-10.json`. The figure gate is written around
   `params.cycle.name` and this cycle was deliberately not reported (§5 of the task not run).
   Downstream of the stop, not an independent defect. It also means **a task that stops before
   §5 cannot have a green suite** while the figure gate reads the current cycle unconditionally —
   worth fixing with a skip, in a task that is not itself reporting a gate failure.
3. `test_scan_run_2.py::test_the_uncited_set_only_shrinks_and_only_by_citation` — failed on the
   run above with *"no commit adds state/scan_2026-09-10.json"*, because the suite ran before the
   payload was committed. Re-run after `c388b5c`: **1 passed**. Not a defect.

New: `tests/test_scan_run_4.py`, 11 tests, the §3 clauses as code.

## 6. Two more findings, smaller

**An unnamed error class, once.** `httpx.TooManyRedirects` on Census's A10 invalid-route probe
resolves to `unknown` — the classifier's only remainder, and a cycle that produces any is a
cycle whose map is missing a rule. The instrument handled it exactly as designed: `RULE-A10-v3`
refused to reach a verdict and said *"the map does not name this failure; counted and reported
per cycle, never absorbed into a neighbour."* It is one observation and it did not become a
verdict. `errors.BY_EXCEPTION_TYPE` should learn the name; not in this task, which is not
touching the classifier while reporting a defect in it.

**`publish.py` had one entry point tested and two entry points.** The `flagship:` change gave it
`from .model import SYNTHETIC_PREFIXES`. Every test imports it as `scan.publish`, where that is
fine; the cycle runs it as `python assessment/harness/scan/publish.py`, where it raises
`ImportError: attempted relative import with no known parent package`. The fast tier was green
and the publish step was not — discovered after the run, with 2,718 Observations waiting to
reach the log. Fixed to the absolute form, with a test that runs the script's own entry point.

## 7. What the next task needs

1. **`robots_disallowed` should be blind.** One flag in `errors.CLASSES`, and then the question
   `NOT_FETCHED` exists to answer — was a request made at all — should be the one `_common`
   asks, rather than `BLIND`, which is a list of ways a request that WAS made can fail. Check
   `sitemap_off_site` at the same time: like `off_host`, it is scope, so it likely stays.
2. **Re-judge cycle 4 into `scan_2026-09-10_rj1`** under the fixed rules, from stored
   Observations, contacting nothing. Then register — from the re-judged payload, not this one.
3. **Decide what to do about cycles 2 and 3**, which carry 9 each of the same defect under
   registered names that bind once. This is the only part that needs a decision rather than a
   fix, and the L0 report quotes those numbers.
4. **`RULE-A10-v3` returned `pass` from two unissued probes.** Item 1 fixes the cause, but A10 is
   the leg where the mirror defect was first named, and it should get its own red/green replay
   in the guards suite rather than being assumed fixed by the flag.
5. **The figure gate should skip when the current cycle has no matrix**, so a task that stops
   before reporting can still show a green suite for everything unrelated.
