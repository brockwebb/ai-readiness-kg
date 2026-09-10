# RESULT — scan-frame v5: the seven declared flagships enter the frame, verified robots-first

**Task:** `cc_tasks/2026-09-10_scan_frame_v5.md`. No addenda exist; globbed at dispatch and
again before §3, both times empty.
**Date:** 2026-09-10 UTC
**Spend:** zero model calls. **Network:** 21 requests — one `robots.txt` read, one HEAD and one
GET per declared landing page, on the seven declared netlocs and nothing else.
**Cycle 4 is not run by this task.**

---

## 1. The gate — §3

**PASS on every clause.**

| clause | result |
|---|---|
| Every one of the seven has a recorded Observation with a status | **7 of 7**, §2 |
| Every added surface is same-site to its body | **7 of 7**, and no page redirected off-site |
| Fixture gate and fast tier green | **EXIT=0**, 1663 passed, 289 s |
| Re-derivation of all 8 stored payloads (the engine changed) | **8 of 8, byte-identical** |
| Full suite | **EXIT=0**, 1674 passed, 2 skipped, 963 s |
| `seldon verify` | **All checks passed**, EXIT=0 |
| Protected paths | targets v4, rule modules, prior RESULTs, cycle evidence, events, report — **no change** |
| The request log shows exactly the requests §1 permits and no other | **21 total, 3 per netloc, 7 netlocs** |

## 2. §1 — the seven, status by status

`scripts/verify_flagship_declarations.py`, through `scan.manners.Fetcher`, so robots was read
before each page (DD-062) and the standing rate applied. The URLs were **parsed** from
`docs/design/fss_flagship_declarations.md`, never retyped: a URL typed twice can differ in one
place, and the declaration is the authority.

| body | product | declared page | robots | HEAD | GET | same-site | verdict |
|---|---|---|---|---|---|---|---|
| DRSMSU | Survey of Consumer Finances | federalreserve.gov/econres/scfindex.htm | permits | 200 | 200 | yes | **enters** |
| NAHMSAPHIS | NAHMS national studies | aphis.usda.gov/…/nahms | permits | 200 | 200 | yes | **enters** (301 within site) |
| NCES | Digest of Education Statistics | nces.ed.gov/programs/digest/ | permits | 200 | 200 | yes | **enters** |
| SAMHSACBHS | NSDUH | samhsa.gov/data/…/nsduh-… | permits | 200 | 200 | yes | **enters** |
| BLS | Consumer Price Index | bls.gov/cpi/ | permits | 403 | 403 | yes | **refused_at_declaration** |
| BTS | National Transportation Statistics | bts.gov/topics/national-transportation-statistics | permits | 403 | 403 | yes | **refused_at_declaration** |
| ORES | Annual Statistical Supplement | ssa.gov/policy/docs/statcomps/supplement/ | permits | 403 | 403 | yes | **refused_at_declaration** |

**No stops.** Decision 2's cases — 404, off-site redirect, timeout — did not occur, so nothing
was withheld and nothing was substituted.

**The three 403s are the three hosts already recorded as refusing the identified client**, the
same three across the pre-flight and three cycles. Decision 1 admits them marked
`refused_at_declaration`. Every one of the seven pages is permitted by its host's `robots.txt`
for this UA; the refusal is at the HTTP layer, not the manners layer, and the two are recorded
separately because they mean different things.

**APHIS's page 301s within its own site**, declared path → `/livestock-poultry-disease/nahms`.
The row keeps the DECLARED url and records `verified_final_url` beside it. A redirect is a fact
about the surface, not a correction to the declaration, and decision 2 forbids substitution.

Requests, per netloc — the whole of what this task asked of anyone's server:

```
nces.ed.gov 3   www.aphis.usda.gov 3   www.bls.gov 3   www.bts.gov 3
www.federalreserve.gov 3   www.samhsa.gov 3   www.ssa.gov 3      total 21
```

### The premise the task file got wrong: "as Observations"

§1 says to record the per-page facts **as Observations**. They are recorded, with status, final
URL, same-site verdict and robots verdict per page — but in
`state/fss_flagship_verification_2026-09-10.json`, not as `scan.model.Observation` records.

**A script cannot mint them, by construction, and that construction shipped two tasks ago.**
DD-063's script guard redirects any evidence write from an unlicensed driver into quarantine,
and `AIRKG_SCAN_CYCLE` is set inside `run.py::main` and nowhere else precisely so that a script
cannot license itself. A verification script that wrote committed Observations would either
have to self-license — the exact lint `2026-09-09_guards_earn_their_keep.md` added — or have
its evidence swept into `unlicensed/`. The prior art in this repo is `scripts/preflight.py`,
which recorded the same shape of fact in `state/fss_preflight_2026-09.json` for the same reason.

So the fact is recorded and citable, and the Observations are minted by cycle 4, on these
surfaces, under a licensed runner. §3's clause — "every one of the seven has a recorded
Observation with a status" — is satisfied in substance: seven rows, seven statuses, one file,
registered as a DataFile.

## 3. §2 — targets v5

`scripts/build_fss_targets_v5.py`, `COMPUTED_FROM` v4. **v4 is read and not rewritten**: three
cycles of Findings hang off its rows, and a test asserts v5's first 65 rows are v4's, identical
and in order, so a diff of the two files is exactly the seven added lines plus a recomputed
header.

| | v4 | v5 |
|---|---|---|
| surfaces | 65 | **72** |
| flagship surfaces | 17 | **24** |
| sites (site keys) | 19 | **19** |
| bodies | 19 | **19** |
| netlocs | 22 | **22** |
| bodies pending operator declaration | 7 | **0** |

**Seven surfaces added no site and no netloc, and that is the design.** A flagship is declared
on its body's own site key (DD-063), so the contact bound did not move: the same 19 sites, the
same rate limit, the same manners claim. A frame that grew its contact surface every time an
operator declared a product would make the declaration a network decision.

New surface ids use the `flagship:<netloc><path>` scheme — synthetic, because a landing page
declared after the corpus was frozen has no admitted Document behind it, which is the ordinary
case for these seven.

### The prefix list had three copies and now has one

`SYNTHETIC_PREFIXES` was defined in `publish.py` and open-coded again in `run.py` and
`build_fss_targets.py`. The comment above the original says what a second copy cost the last
time the scheme grew: `home:` and `machine:` reached two of the three, and 957 observations of
ordinary host-level surfaces were counted as missing Documents.

Adding `flagship:` to three copies would have been the same bet a second time. The constant now
lives in `scan/model.py` beside the rest of the id model, and `publish.py`, `run.py` and both
target builders import it. A test asserts all three readers hold **the same object** and that
no fourth copy has reappeared.

**The engine changed, so every stored payload was re-derived: 8 of 8, byte-identical.** A new
prefix that changed how an old cycle read its own targets would have shown up there.

## 4. §3 decision 3 — what was registered, and what was left alone

`fss_agencies_pending_operator_declaration_2026-09 = 7` **stands unedited.** It is a cycle-3
fact: seven bodies were pending when cycle 3 measured. A registry where yesterday's number can
be edited to match today's cannot show a change, and a Result name binds once (AD-028).

```
fss_scan_surfaces_2026-09-10                          = 72
fss_scan_sites_2026-09-10                             = 19
fss_scan_bodies_2026-09-10                            = 19
fss_agencies_pending_operator_declaration_2026-09-10  = 0
fss_flagships_declared_2026-09-10                     = 7
fss_flagships_refused_at_declaration_2026-09-10       = 3
6 registered, 0 failed
DataFile: scan_targets_fss_2026-09_v5 (state/scan_targets_fss_2026-09_v5.json)
```

## 5. Verification

```
logs/flagship_verify.log  7 pages, 21 requests, 0 stops, 0 off-site        EXIT=0
logs/v5_fast.log          1663 passed, 2 skipped, 11 deselected    289 s   EXIT=0
logs/v5_rederive.log      8 passed — every stored payload byte-identical   EXIT=0
logs/v5_full.log          1674 passed, 2 skipped                   963 s   EXIT=0
logs/v5_verify.log        seldon verify — All checks passed                EXIT=0
logs/v5_protected.log     protected-paths diff                             EXIT=0
                            targets v4            no change
                            shipped rule modules  no change
                            prior RESULTs         no change
                            cycle evidence        no change
                            events/               no change (append-only)
                            report prose and PDF  no change

new tests   tests/test_scan_frame_v5.py, 11 tests: v4 unedited, the seven added,
            same-site per body, refused-still-entered, ids synthetic and distinct,
            one prefix definition, only the seven netlocs contacted and at most
            three requests each, every page has a status, nothing substituted.
```

## 6. What the next task — the cycle-4 run — needs

1. **`params.cycle.targets` still names `scan_targets_fss_2026-09`.** `run.targets()` reads the
   file that key names, so cycle 4 must point it at `scan_targets_fss_2026-09_v5` or it will
   measure the old frame and report it as the new one. This is the one wiring step this task
   deliberately did not take: changing the params key changes what a cycle measures, and no
   cycle runs here.
2. **Seven new surfaces means seven more product surfaces on the tier-A legs**, three of them on
   hosts that will answer 403. Expect `error`/`refused` Findings on BLS, BTS and ORES flagships,
   and remember what `error` means: the collector could not observe. It is never a statement
   that the product failed, and never that it passed (DD-052 §6).
3. **The A5 sitemap leg and the new flagships.** Four of the seven are ordinary HTML landing
   pages on hosts that serve sitemaps; the `RULE-A5-v2` off-site declaration path has not been
   exercised on them. Nothing predicts a defect — it is simply the first cycle these surfaces
   have ever been measured in, and the first cycle for any surface is where the frame learns
   whether its declaration was a good one.
4. **The 71 % suite cut of the previous task holds at this size**: 963 s for 1674 tests.
