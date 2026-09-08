# RESULT — scan-frame-fss: the frame is 16 + 3, and every surface in it is declared

**Task:** `cc_tasks/2026-09-08_scan_frame_fss.md` with `ADDENDUM-01` (Tier C, stands) and
`ADDENDUM-05` (governing; withdraws `-02`, `-03`, `-04` and Tier B).
**Date:** 2026-09-08 UTC
**Spend:** zero model calls.
**Network:** the 19 hosts of the frame, two probes each in pre-flight, plus one home fetch for
the single unadmitted surface. Identified UA, 1 req/s per host, robots obeyed. **No scan cycle
was run.** Earlier turns of this task contacted `statspolicy.gov`, `raw.githubusercontent.com`
and `catalog.data.gov` under the addenda then in force; those fetches are on the record in §6.

---

## 1. The gate — §6 as amended by ADDENDUM-05 step 5

**PASS on all six clauses.** `tests/test_scan_frame.py`, 12 tests.

| clause | result |
|---|---|
| Roster Tier A = 16 | **16**, by parse from the ICSP charter's `^` flag, from a retained body |
| Every row's `selection_source` is `operator declaration` or `roster host` | **65 of 65** |
| Zero rows outside the 19 hosts | **0** (Tier C machine entry points are inside the frame and named by ADDENDUM-01) |
| Zero conversion-gap tasks from this admission | **0** |
| Pre-flight Results for exactly 19 hosts | **41 Results**: 2 per host + 3 summaries |
| Tool map regenerates byte-identically | **yes** |
| Full suite green | **1,592 passed, 0 failed, 2 skipped** |

**Nothing was registered before this section was written.**

## 2. The frame

**16 Tier A + 3 Tier C = 19 hosts. No Tier B. 65 surfaces, none derived.**

| | |
|---|---|
| Tier A | 16 OMB-recognized statistical agencies and units (CIPSEA 2018, 44 U.S.C. 3561(11), 3562) |
| Tier C | `data.gov`/`catalog.data.gov`, `nist.gov`/`data.nist.gov`, `gsa.gov`/`open.gsa.gov` — tier-0 legs only |
| Surfaces | 19 home, 19 well-known, 17 flagship, 10 machine |
| Carried from cycle 1 | **24** doc_ids, so two cycles of Findings stay attached to the surface they were measured on |
| Pending operator declaration | **7** agencies: BLS, BTS, DRSMSU, NAHMSAPHIS, NCES, ORES, SAMHSACBHS |
| Not admitted | **1**: `scan-eia-flagship-2-eia-survey-forms` — `eia.gov/robots.txt` disallows it for this UA |

The 7 pending agencies carry their home and their tier-0 probes and nothing else.
`docs/design/fss_flagship_shortlist.md` is where the operator declares; no rule fills the gap
and none should.

## 3. The roster, and the disagreement in its sources

Tier A parses to **16** from the ICSP charter. The live statspolicy.gov About page flags
**15** and links **15**, while that same page's prose says **16** — it contradicts itself. The
one entry that differs is `Social Security Administration, Office of Research, Evaluation, and
Statistics`, which the charter flags `^` (Recognized Statistical Agency or Unit) and the About
page carries as `*` (Statistical Official) only, absent from its own recognized-agency list.

`params.frame.roster_authority` settles it and **was declared before either body was parsed**:
membership from the charter, because it is the Council's constitutive document and enumerates
under an explicit legend; URLs from the About page, because it is the only source carrying one
per agency. The disagreement is on the roster's face as `tier_a_disagreements`, not resolved
silently. Both bodies are retained content-addressed under `corpus/evidence/frame/` — a lane of
its own, because a roster body in `corpus/evidence/scan/` would grow the set DD-058 says can
only shrink.

An independent third federal source agreed: CISA's `.gov` registry, consulted under the
now-withdrawn ADDENDUM-03, placed **16 of 16** Tier A domains and confirmed **15 of 16** parent
departments. The sixteenth is a Federal Reserve name-string difference ("…Federal Reserve"
against "…Federal Reserve System"), not a disagreement about ownership.

## 4. Pre-flight — 19 hosts, two probes each

| | |
|---|---|
| Reachable | **19 of 19** |
| Serving `robots.txt` | **15 of 19** — `www.federalreserve.gov` 404s it; the three refusing hosts 403 it |
| Refusing an identified client | **3**: `www.bls.gov`, `www.bts.gov`, `www.ssa.gov` |
| Unreachable | **0** |

Measured first under UA `0.1`, then again under `0.2` after DD-060 bumped the identity. **Every
host answered identically both times** — which is the point of DD-060: the instrument does not
vary its identity to get a better answer, and here there was nothing to gain by it.

`ua_permitted_on_root` reads 19 of 19, and that number needs its caveat. It reads the DECLARED
layer: where `robots.txt` is not served there is nothing to forbid us, which is not the same as
being served. The gap between those two is exactly what A12 measures, and three hosts sit in
it. `www.eia.gov` answered 503 on its home in both runs — reachable, and its own kind of
finding for cycle 3.

## 5. Two design decisions

**DD-059** — the frame: 16 + 3, no Tier B, StatCan out, unit of analysis the surface, and the
sampling statement is that **every surface is declared rather than derived**, with the three
failed derivations recorded as the reason.

**DD-060** — one client identity, `ai-readiness-kg-scanner/0.2 (+…)`, contact URL on its face
per RFC 9309 practice; refusals are findings and are never retried under another identity;
monthly cadence from cycle 3, first Monday UTC, **after** cycle 3 validates the frame. No
scheduler installed.

## 6. Three selection rules, all built, all failed — and why the frame is declared

This is the substance of the task and it is worth stating plainly, because two of the three
failures were mine and the third is a fact about the federal data estate.

**1. Anchor-substring scraping of agency home pages** (base task §2). Written before any page
was fetched, which was right. Its own output falsified it: **12 flagships across 16 agencies**
where cycle 1's hand list had 26 for 13, **12 of 16 agencies with none at all**, and matches by
accident — `api` inside *"Capital Markets"* on the Federal Reserve's staff page, `products`
inside *"traveling-with-ag-products"* at APHIS, whose selected "flagship products" were travel
advisories. A rule that finds fewer real surfaces than the list it replaces, and finds some by
accident, is not a sampling statement.

**2. The Enterprise Data Inventory at `/data.json`** (ADDENDUM-02). Sound prior art — the OPEN
Government Data Act requires every CFO Act department to publish one — and blocked on a fact
nobody publishes: the department → domain mapping. Probing the hosts that ARE derivable found
an inventory for **5 of 16** agencies and an API distribution for **1**. `cdc.gov` is not
`hhs.gov`, `bls.gov` is not `dol.gov`, `irs.gov` is not `treasury.gov`.

**3. CISA's `.gov` registry plus data.gov's harvest API** (ADDENDUM-03). The registry has no
primary-domain field — one row per domain, 28 for Labor, 124 for HHS, and neither `hhs.gov` nor
`ed.gov` nor `treasury.gov` is in its department's suborganization-empty set; forward-resolvable
for **3 of 26** departments. And data.gov's CKAN action API is **gone**: `organization_list`,
`harvest_source_list` and `package_search` all answer **HTTP 404**.

**The government publishes no machine-readable department → inventory map, and its own catalog's
machine interface is down.** That is a recorded observation about the federal data estate, not a
defect in this harness, and it belongs in the report rather than in a workaround. ADDENDUM-01
declared Tier C on the reasoning that *"if the government's own catalog is not machine-legible
at tier 0, that is a finding in its own right"* — this is that finding one layer above tier 0.

Tier 0 needs none of it. What a tier-0 leg asks — is `robots.txt` served, are the discovery
files there, does a deep link behave, is the machine layer declared, do the declared and
enforced layers agree — is answered against a **host**, and the host is on the roster. That is
what ADDENDUM-05 saw and the three drafts did not.

## 7. Premises this task and its addenda got wrong

1. **Base task §1: "Tier A count must be 16 by parse."** True of the charter and false of the
   About page, which the frame decision named as the primary source. The page's own prose and
   its own list disagree. §3.
2. **Base task §2: the selection rule.** Falsified by its own output. §6.1.
3. **Base task §3 and the frame decision: Tier B hosts.** Neither named source carries a URL
   for a department without a recognized unit; the ICSP member detail pages are empty (1 byte).
   Tier B could never have been pre-flighted from the sources the task named. ADDENDUM-05
   removed Tier B for a different reason and the block disappeared with it.
4. **ADDENDUM-02 §2.a: "fetch the parent department's `/data.json` … 13 hosts at most."**
   Presumes the mapping above. §6.2.
5. **ADDENDUM-03 §2.a.1: the registry's columns.** Expected `Domain name, Agency,
   Organization`; the file served is `Domain name, Domain type, Organization name,
   Suborganization name, City, State, Security contact email`, one row per domain. §6.3.
6. **ADDENDUM-03 §2.a.2: the harvest source registry.** Not available. §6.3.
7. **ADDENDUM-05 step 1: "26 carried flagship rows."** The cycle-1 list holds 27 doc_id-bearing
   rows, 3 of them StatCan, leaving **24** in frame — 17 flagship and 7 machine. Carried: 24.

### Mine, separately

8. **Agency codes derived from unit names.** `NAHMAPHIS`, `SAMHSACBHSQ`, `RES` match no cycle-1
   code, so only 4 of 26 cycle-1 surfaces carried forward and the rest looked dropped. Matching
   on **host** instead restored all 24. The defect was mine, not the rule's, and I reported the
   carry-forward number before finding it.
9. **The word-boundary matcher fixes less than it looks like.** It stops `api` matching inside
   "Capital Markets" — but `traveling-with-ag-products` genuinely contains the word "products",
   so it would not have saved APHIS. What fixes APHIS is not scraping at all.
10. **I stopped three times.** Each stop produced a measured finding rather than a shrug, and
    each was the right call under "a task that fails a pre-registered premise writes nothing and
    reports". But the first stop would have been unnecessary had I read the addenda that
    appeared mid-run; I globbed once at dispatch and not again.

## 8. Verification

```
python -m pytest tests/ assessment/     1592 passed, 2 skipped, 0 failed (2377 s)
tests/test_scan_frame.py                12 passed
seldon verify                           All checks passed. 27,981 events readable;
                                        79 task source files resolve; precedence acyclic;
                                        no stale artifacts; no blocking tasks.
git diff HEAD -- <protected>            EMPTY on assessment/harness/scan/rules/,
                                        assessment/cq/, events/, framework/.
                                        git status --porcelain corpus/ — clean.
```

**Registered this task:** `fss_agencies_tier_a`=16, `fss_departments_tier_b`=14,
`fss_tier_a_source_disagreements`=1, `fss_scan_hosts_2026-09`=19,
`fss_scan_surfaces_2026-09`=65, `fss_surfaces_carried_from_cycle_1_2026-09`=24,
`fss_agencies_pending_operator_declaration_2026-09`=7, 38 per-host pre-flight Results and 3
pre-flight summaries. DataFiles `fss_roster_2026-09`, `scan_targets_fss_2026-09`,
`fss_preflight_2026-09`.

**Superseded:** `fss_department_domains_2026-09`, with the reason on its face — outside the
frame per ADDENDUM-05. The five measurements computed from it stand as facts on the log and are
used by nothing.

## 9. What cycle 3 needs

1. **The 7 pending declarations.** `docs/design/fss_flagship_shortlist.md` is written and
   waiting. Until then those agencies contribute tier-0 legs only, which is a real measurement
   and a thin one.
2. **`params.tier0.legs` does not exist yet.** The base task's Tier 0 headline names A4, A5,
   A10, A11-declared, A12 and G1-D, and DD-059 and the figure tests refer to
   `params.tier0.legs`. Cycle 3 must declare it before it can enforce the Tier C restriction
   mechanically; today that restriction is carried on the row and honoured by convention.
3. **The Tier C figure assertion** (ADDENDUM-01 item 5): no Tier C row in F2, no Tier C point
   in F1 outside the tier-0 legs. Named, not built — it needs item 2 first.
4. **`www.eia.gov` answered 503 on its home** in both pre-flight runs. Transient or not is
   unmeasured, and it is the difference between a cycle-3 `error` and a finding.
5. **Three hosts have refused an identified client across four measurements** now
   (2026-09-07 pre-flight, both cycles, this pre-flight). That consistency is itself worth
   reporting as a finding about federal accessibility rather than as a footnote about coverage.
6. **The 22 cycle-1 conversion gaps** remain on the log, withdrawn. They are accounted for and
   they still make "zero conversion gaps" an awkward thing to assert; the gate now checks the
   delta instead.
