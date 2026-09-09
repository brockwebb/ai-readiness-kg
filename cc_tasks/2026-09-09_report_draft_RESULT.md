# RESULT — report-draft: the L0 product, first draft

**Task:** `cc_tasks/2026-09-09_report_draft.md` (no addenda exist; globbed at dispatch and again
before §3).
**Governing design:** `docs/design/2026-09-08_l0_product_shape.md`, read before §1.
**Date:** 2026-09-09 UTC
**Spend:** zero model calls. **Network: none.** No host was contacted; every number comes from
the graph and from artifacts already on disk.

---

## 1. The gate — §3

**PASS on all five clauses.**

| clause | result |
|---|---|
| The build resolves every `{{result:...}}` tag | **0 unresolved**, 0 fatal reference errors |
| Zero bare numerals in prose outside tags, tables and the appendix | **0** |
| Every matrix CSV row re-derives from the graph by Cypher | **274 cells** checked against the Finding each names; 70 carry no Finding by design |
| Hygiene suite green | 13 passed |
| `seldon verify` green | All checks passed |

`docs/reports/2026-09_fss_ai_readiness_L0.md` is written. **Nothing was registered after this
section was written; §0 and §1 registered first, and the gate then ran against what they
produced.**

**The lint was negative-tested rather than trusted.** A gate that passes because it stopped
looking is worse than no gate, so a typed numeral was injected into a section (`Exactly 7 legs
sit at zero`) and the build was re-run: it blocked, named the line, and wrote no report file.
The injection was then reverted and the gate re-run green. Two defects in the lint were found
that way and are in §5.

## 2. What was registered

**140 Results** across the families below, plus one DataFile and two Script artifacts. Every
value is recounted in the registrar from the artifact it describes; none is read out of a
RESULT, a task file or a prior report.

| family | n | source |
|---|---|---|
| `scan_l0_<check>_{pass,fail,error,not_applicable,applicable_n}` | 30 | the 16 bodies' host-level surfaces |
| `scan_l0_product_<check>_{...}` | 50 | the 16 declared flagship surfaces |
| `scan_l0_tierc_<check>_{...}` | 30 | the 3 reference hosts |
| `scan_leg_rate_<check>_upper95` | 16 | Wilson upper bounds, from `harness/rollup.py` |
| `scan_a12_tier{A,C}_<verdict>` | 4 | A12 split by tier |
| `scan_l0_declared_flagship_{agencies,surfaces}` | 2 | 9 agencies, 16 surfaces |
| `scan_l0_product_legs{,_at_zero}` | 2 | 10 checks, 8 of them at zero |
| `scan_l0_home_flagship_disagreement_{cells,bodies}` | 2 | 15 cells, 6 bodies |
| `fss_scan_netlocs`, `fss_scan_netlocs_contacted` | 2 | 22 declared, 24 contacted |
| `scan_a5_fail_offroster_sitemap` | 1 | §3 below |
| `scan_refusal_consecutive_measurements` | 1 | §4 below |

**`scan_targets_fss_2026-09_v2` was never registered and is now** (§0.2). The v1 DataFile was
bound on 2026-09-08 and still describes v1: "19 hosts, 65 surfaces". The file on that path has
carried `targets_version: 2` since scan-run-3b rewrote the id scheme, and nothing recorded it.
v1 stays LIVE and is not superseded: four Results are `COMPUTED_FROM` it, and its description
is a true statement about the bytes it was registered against.

**Two tasks superseded** (§0.1): `d261be8b` (scan-run-3, blocked at its own control gate) by
`3b47290e`, and `2517cda8` (the report-draft placeholder) by this task, `e1b7cd4b`.

## 3. The off-frame sitemap caveat is **zero**, and finding that out corrected the record

§0.4 asked how many A5 failures belong to a host whose `robots.txt` declares a sitemap outside
the frame that the scanner then did not follow. **Measured: 0**, and the task says that if it
is zero the report says zero, which it does.

Getting there re-read every `robots.txt` body the cycle retained: 12 distinct sitemap
declarations from 12 of the frame's hosts, 2 of them naming an off-frame netloc. **Both were
fetched.** So no failure is attributable to a declaration the scanner declined to follow.

**That measurement falsifies `cc_tasks/2026-09-08_scan_run_3b_RESULT.md` §2 on two points of
fact.** It said of `data.gov` and `samhsa.gov`: *"Only `robots.txt` was fetched — the count is
1, not 2 — so no sitemap was retrieved from either."* The log says otherwise. Each apex netloc
received exactly one request and it was the **sitemap**, not `robots.txt`:

```
GET https://samhsa.gov/sitemap.xml  -> 200, 537,750 bytes, body retained
GET https://data.gov/sitemap.xml    -> 200,  34,962 bytes, body retained
```

The consequence is worse than the contact-bound overrun that RESULT reported. It argued the
extra contacts were required because *"RFC 9309 requires reading the sibling's robots.txt
first"*. The scanner did not read either sibling's `robots.txt`; it fetched the sitemap
directly. **Two GETs went to hosts whose `robots.txt` this scanner had not read**, which its
own manners forbid. This task collects nothing and re-runs nothing, so the defect is recorded
and not fixed: it is on the face of the report under what the matrix cannot see, and it is a
cycle-4 item.

## 4. The report

`docs/reports/2026-09_fss_ai_readiness_L0.md`, built from eight section files.

**Length: 4,718 words** — about **6.6 pages of prose**, plus roughly 2.4 pages of matrix and
1.5 of appendix, so **about nine pages against the design note's seven**. Trimmed twice and
stopped there. Cutting the remaining two pages would have meant removing the per-check
paragraphs or the limits section, and a shorter report that a reader cannot check is not the
product the design asks for. Reported rather than hidden, and the measurement is above.

**What it says.** The matrix is the report: 16 bodies against six host-level checks. Serving
`robots.txt` and answering deep links honestly are near-universal among observable bodies
(11 of 12 each); declaring a machine layer nearly so (10 of 12); discovery is weak (3 of 12);
uncertainty fields at the host level are absent everywhere (0 of 12, upper bound 0.24). The
product-level matrix is explicitly PARTIAL: it covers 9 of 16 bodies, and 8 of its 10 checks
return not a single pass across the 16 declared surfaces.

**The self-assessment row is absent and says why.** The report has no host, serves no
`robots.txt` and answers no deep links, because nothing is serving it. Scoring it would mean
inventing answers for a site that does not exist. What publication would have to provide is
stated instead.

**Nothing was published.** The report, its matrices and its fragments are files in the repo.

## 5. Premises this task got wrong

1. **§2's "Seven legs at zero across the declared surfaces". It is eight.** D4 (catalogue
   entry) has 2 passes over the whole Tier A product population and **0** over the declared
   flagship surfaces, so it joins A1, A2, A6, A8, A9, D1 and F4. The earlier figure came from a
   different denominator. The report quotes the registered count and not the task's number.
2. **§0.2's `derived_from`.** The schema refuses it: `derived_from` may originate only from a
   Result, `supersedes` only from an ArchitecturalDecision. `computed_from` is the one edge a
   DataFile may originate and its meaning fits, so v2 `COMPUTED_FROM` v1, and the phrase
   "derived_from version 1" is carried verbatim in v2's description where the schema cannot
   object. Recorded because the next reader will reach for `derived_from` too.
3. **§1.1's "16 agencies × the six legs" assumes a host-level cell is well defined.** It is
   not. Five of the six checks are judged per SURFACE, and this cycle's home and flagship
   surfaces disagree on 15 cells across 6 bodies: a `robots.txt` permitting the front door can
   disallow a particular product. The matrix therefore names the surface every cell was
   measured on, and the disagreement count is registered rather than described.
4. **"Through the build pipeline" is not quite available.** `seldon paper build` hardcodes
   `paper_dir = project_dir / "paper"`, and this report is not a paper. It also fails outright
   on a `proposed` Result, and every one of this project's 6,300 Results is proposed. The
   library's own resolver, SI checks and Tier 2/3 QC are used as they stand, through a thin
   runner that passes the two knobs `resolve_references` documents for exactly this case and
   `build_paper` does not forward: `mark_proposed=False` and a `value_formatter` (the graph
   stores every value as a float, and "16.0 agencies" is not what the measurement says).

### Mine

5. **The first matrix CSV put the refusal counts in the leg columns.** The writer collected all
   non-leg fields into one list and concatenated, and `refused_identified_client` sits after
   the legs in the header. The file parsed, every row had the right number of fields, and every
   verdict was one column adrift. A header and a row that agree only in length agree about
   nothing.
6. **The bare-numeral lint had two defects, and both would have made it pass by not looking.**
   It ran after reference resolution, where `{{result:...}}` has already become `19`, so it
   flagged every number in the report including every correct one; substitutions are now marked
   during resolution and the markers stripped before the file is written, which keeps the lint
   on the built body while letting it tell a resolved value from a typed one. It was also
   line-scoped, so a statute citation rewrapped across two lines read as a bare numeral; it now
   judges a paragraph, which is the unit its patterns were written against.
7. **I typed "thirteen cells across nine bodies" into the report and both numbers were wrong.**
   The true figures are 15 and 6; my ad-hoc count compared one flagship per agency and counted
   the agencies that *had* both surfaces rather than those that disagreed. It was caught only
   because I went to register it. That is the design note's "no prose number" rule earning its
   place, and it is the reason the lint exists.

### Not defects, but worth stating

8. **Tier 2 and Tier 3 prose QC report 93 and 57 findings, and none is part of the gate.**
   They run against Seldon's paper templates: sentences capped at 30 words, no inline bold, at
   least one citation token per section, paragraphs of at least two sentences. This report uses
   bold labels for the per-check paragraphs because the design note's shape calls for them, and
   most of its sections cite no literature because they report a measurement. The genuinely
   long sentences were shortened; the remaining findings are a genre mismatch. **No QC config
   was written for this report**, deliberately: authoring a config that zeroes a checker's
   output is the same move as moving a threshold, and the honest record is the count and the
   reason.
9. **Every rendered value is a `proposed` Result** (42 distinct ones in the built text). That
   is this project's normal state, not a defect; the marker is suppressed in the prose and the
   count is reported here instead.

## 6. Verification

```
build                          0 unresolved tags, 0 fatal reference errors, 0 missing fragments
bare-numeral lint              0, and negative-tested: an injected numeral blocks the gate
matrix re-derivation           274 cells checked by Cypher against the Finding each names
                               (tierA 96, tierC 18, product 160), 70 undeclared by design
hygiene suite                  13 passed
seldon verify                  All checks passed. 29,454 events readable; 83 task source files
                               resolve; precedence 12 edges, acyclic.
full suite                     1614 passed, 0 failed, 2 skipped (2941 s)
registered                     140 Results, 0 failed; 1 DataFile (targets v2), 2 Scripts
protected paths                EMPTY on assessment/harness/scan/rules/ (every shipped module),
                               assessment/cq/, the targets DataFile, params.yaml, and every
                               prior cc_task and RESULT. events/ UNTOUCHED: this task wrote no
                               kg event, only Seldon registrations. corpus/ clean.
```

## 7. What the next task needs

1. **The manners defect in §3.** The scanner fetched two sitemaps without first reading those
   hosts' `robots.txt`. That is a collector fix and a control fixture, not a report edit.
2. **Settle the contact bound.** Either sitemap-following is frame-bounded and an off-frame
   declaration becomes a recorded observation, or the bound is stated as the frame plus what
   the frame's own hosts declare. The report names the choice as open because it is.
3. **Declared flagships for the remaining 7 bodies.** It is a list, not a cycle, and it is the
   cheapest available improvement to the product-level measurement: the intervals are wide
   because the population is 16 surfaces from 9 bodies.
4. **A publication host for the report**, so its own last row can be measured rather than
   explained. Everything the design asks for is already emitted except the serving.
5. **The report's sections are not registered as PaperSection artifacts**, so `seldon verify`
   still reports "No PaperSection files to check". Registering them would make
   `seldon paper sync` meaningful for this document; it was not asked for here.
