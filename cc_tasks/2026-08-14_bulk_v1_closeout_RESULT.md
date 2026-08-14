# RESULT — AIRKG bulk-v1 closeout

**Task:** `cc_tasks/2026-08-14_bulk_v1_closeout.md`
**Executed:** 2026-08-14, cockpit session. Max OAuth only; `ANTHROPIC_API_KEY` unset throughout.
**Registry:** `task-1a34ae89`
**Gate report:** `docs/research/2026-08-14_bulk_v1_closeout_gate_report.md`
**Left uncommitted** per burn convention — operator commits.

---

## Headline

| gate | value | verdict |
|---|---|---|
| min_verified_included | 71 | PASS |
| **grounding_zero_ungrounded** | **0** | **PASS** |
| quarantine_rate | 0.0343 | FAIL (finding) |
| edge_endpoint_validation | 747 | FAIL (finding) |
| orphan_rate | 0.098 | FAIL (finding) |
| projection_drift | 0 | PASS |
| empty_extraction_rate | 0.0141 | PASS |

The STOP condition **did** trigger on the first gate run (`grounding = 96`). Work
halted, cause found, fixed, re-run. Details below — it is the most useful thing
this task produced.

## Discrepancies vs the figures quoted in the task

Reported live, never silently reconciled.

| task said | live | note |
|---|---|---|
| Item 1: manifest-add + extract `fcsm-19-01` | **already complete** | Manifested 2026-07-17 superseding the corrupt copy; already in `OVERSIZE_ALLOW` under the 2026-07-16 standing clearance; already extracted. Clearance 1 re-authorizes work already done. |
| §515 out of scope, "corpus stays 70/71" | **71/71 extracted** | §515 is manifested AND extracted at *corrected extent* — the 1,675-char standalone excerpt (sha `6d69b226`), not the 2.1M megastatute. The dixie ledger's newest events are that re-acquisition. |
| 683 `edge_endpoint_validation` failures | **750** at baseline | 683 came from the 69-doc report quoted in the 07-16 RESULT. The 07-17 report already read 750. |
| fcsm-19-01 staged at `corpus/staging/inbox/` | **not there** | Already consumed into `corpus/bulk/` on 07-17. Inbox holds only OECD + the two FCSM provenance backups (left untouched, per scope). |
| `OVERSIZE_ALLOW` comment: 361,161 chars | **361,303** | 142-char drift in a code comment; behaviourally irrelevant (the allowlist keys on doc_id). Not edited — no config change. |

Net: **item 1 required no work**, item 2 was real, item 3 was real and needed no spend.

## Item 2 — OECD supersession + re-extract

The premise resolved a contradiction worth recording: the "truncated 287,110-char
partial" is *larger* than the "full" 142,364-char report because it was a crawl4ai
capture of `component-5.html` — one component plus site boilerplate. Bigger file,
less report.

Superseded through the repo's **existing designed path**, not a new one. Dixie's
`_on_file_observed` only moves `canonical_path` when the path is unchanged (that is
why §515 worked — bytes replaced in place). A PDF cannot take the `.md` path, since
the runner dispatches text extraction on suffix. The correct sequence is the one
`_on_quarantined` implements: observe the new file (it lands as an *alternate*),
integrity-check it (alternate now verified), then quarantine the old canonical —
which **promotes the verified alternate**. Result: `canonical_path` =
`corpus/bulk/introducing-the-oecd-ai-capability-indicators.pdf`, sha `798d84db…`,
integrity verified, stage verified. The partial is preserved at
`corpus/quarantine/bulk_md/…partial-component-5-web-capture.md`, never deleted.
The staged inbox copy was **copied, not moved**.

Re-extraction, standard runner, same config:

| | partial (superseded) | full report (new) |
|---|---|---|
| chars | 287,110 | 142,364 |
| nodes / edges / quarantined | 99 / 137 / 7 | **83 / 139 / 7** |
| quarantine_rate | 0.0288 | 0.0306 |
| tokens | 338,165 | **185,398** |

Slightly more edges for 45% fewer tokens — what you expect when 145K chars of site
furniture stop being fed to the model.

**Cost: UNKNOWN, not zero.** The runner emitted
`circuit 'extraction' has 1 unpriced call(s) today; day_cost_usd=0.0 is a LOWER BOUND`.
`model_stub` books tokens but no price. Recorded as unknown rather than letting a
0.0 stand as a spend claim.

## Item 3 — id-mismatch fix + refetch surface

**All 750 baseline violations are `cites`.** The (a)/(b) split is not near-even:
(a) is small, and the obvious way to find it is dangerous.

Similarity matching — the natural reading of "doc-id mismatches" — produces
false positives that would inject wrong citations into the graph:
`executive-order-14110` → `13960`, `executive-order-14091` → `13960`,
`nist-cybersecurity-framework` → `nist-ai-rmf`, `nist-privacy-framework` →
`nist-ai-rmf`, `cisco-ai-readiness-index-2024` → `…-2025`,
`informatica-data-quality` → `fcsm-23-02`, `pub-l-113-101-data-act` →
`information-quality-act`. The trap is dropping digits during normalization: for
EOs, public laws and FCSM numbers, **the number is the identity**.

Rule actually applied: the alias must be a token-**prefix** of the canonical id (or
identical once stopwords drop) **AND** every numeric identifier must agree.
That yields **8 aliases / 14 refs**, every one provably the same document.

> The task's own example, `doc-fcsm-framework-for-data-quality`, did not survive that
> rule — genuinely ambiguous between `fcsm-20-04-a-framework-for-data-quality` and
> `fcsm-23-02-a-framework-for-data-quality-case-studies`. **Resolved 2026-08-14 by
> operator adjudication rule** (resolve by grounding span; numeric/year match wins;
> bare title maps to 20-04; else defer). See "FCSM adjudication" below. Final: **9
> aliases / 15 refs.**

### FCSM adjudication — branch fired: `bare_title -> fcsm-20-04`

Evidence, from `edge_asserted acac0af1…` (batch-002, citing doc `fcsm-25-03`,
location "Challenge & Opportunity (p.3)"):

> "The Federal Committee on Statistical Methodology (FCSM) developed the Framework
> for Data Quality to help analysts and the public assess fitness for use of data sets."

| branch | fired | why |
|---|---|---|
| numeric / year match | **no** | No numeric or year identifier for the *cited* work. The only numbers in the citing document are `25-03` (×2) and `2025` — those identify `fcsm-25-03` itself, not the framework it cites. |
| bare title → `fcsm-20-04` | **YES** | Bare title, no number, no year, no qualifier — and the span states the framework's *purpose* ("to help analysts and the public assess fitness for use of data sets"), which is the framework document. Corroborating negative evidence: the string `case stud` occurs **nowhere** in the citing document, excluding `fcsm-23-02` on its own distinguishing feature. |
| defer | no | not reached |

Span confirmed grounded against the current source (`is_grounded` = True). Recorded
as `edge_endpoint_alias aa435c02…` in `batch-005` with the full branch trace, so the
adjudication is auditable rather than asserted. Mutation-checked: removing this one
alias moves `edge_endpoint_validation` 747 → 748, delta exactly 1.

**Mechanism chosen: projection-time canonical-id mapping via append-only events.**
Neither an amendment facility nor an alias table existed, so both are new event
types resolved at read time by `build_projection.py` *and* `run_baseline_gates.py`:

- `edge_endpoint_alias {alias_id, canonical_id, refs, rule, authorization}`
- `extraction_superseded {doc_id, superseded_source_sha256, superseded_by_source_sha256, reason, authorization}`

Keyed on **(doc_id, source_sha)**, not doc_id alone — a doc_id-only rule would drop
the replacement too, since both extractions share the doc_id. No raw event mutated;
no threshold touched. Written to a new shard `events/batch-005.jsonl` for a clean
audit boundary.

**(b) register:** `corpus/staging/refetch_candidates.jsonl` — **721 candidates,
747 refs**, sorted by citation count, each with citing-doc provenance, distinct-citer
count, and example grounding spans. Top: `omb-circular-a-130` (5 citations across 5
docs), then `eo-13642`, `executive-order-14091`, `gao-21-519sp`,
`national-ai-initiative-act-2020`, `nist-ai-600-1`, `omb-circular-a-119`. **Nothing
manifest-added** — corpus expansion is Desktop triage.

## The STOP, and what caused it

First gate run: **`grounding_zero_ungrounded = 96`**, threshold 0. Halted per task
instruction.

Cause was this closeout's own change. `check_edges` was taught the supersession
overlay; `check_grounding` was not. That check re-verifies every span against the
document's *current* canonical source, so the superseded extraction's spans were
checked against the PDF that replaced them. All 96 were the OECD doc.

Not a real grounding breach — no ungrounded item was ever admitted — but the gate
was right to fire: the log genuinely held assertions that do not ground against the
corpus as it now stands.

Fixed by hoisting the overlay into a shared `live_events()` used by grounding,
edges, quarantine and empty, rather than patching the one check that failed.
`check_quarantine` had the same exposure by another route — it sums `build_metrics`,
and a superseded doc now has two, so OECD was double-counted. `build_metrics` carries
no sha, only `extraction_event_id`, so that id is mapped to a sha through the
assertions it produced rather than by newest-timestamp guesswork.

## Verification discipline

Both overlays mutation-tested, not read:

| overlay | neutered | with | delta | matches |
|---|---|---|---|---|
| `edge_endpoint_alias` | 738 | 724 | 14 | the 14 aliased refs exactly |
| `extraction_superseded` | 736 | 724 | 12 | the superseded extraction's cites |

Projection end-state queried directly: **0** nodes carry the superseded sha,
**83** carry the new one, Document `content_hash` reads the PDF, **71** distinct
Document nodes.

## edge_endpoint_validation: −3 net, large components

| step | value | Δ |
|---|---|---|
| baseline | 750 | — |
| + alias overlay | 736 | **−14** |
| + supersession overlay | 724 | −12 |
| + new OECD extraction's own citations | 748 | +24 |
| + FCSM adjudication (9th alias) | **747** | **−1** |

The (a) fix removed exactly what it aliased. The +24 is the full report citing more
external works than the partial did — the (b) surface grew for a legitimate reason.

## Files touched

**New:** `events/batch-005.jsonl` · `corpus/bulk/introducing-the-oecd-ai-capability-indicators.pdf` ·
`corpus/quarantine/bulk_md/…partial-component-5-web-capture.md` ·
`corpus/staging/refetch_candidates.jsonl` ·
`docs/research/2026-08-14_bulk_v1_closeout_gate_report.md` · this RESULT ·
`events/raw/bulk_v1/introducing-the-oecd-ai-capability-indicators.798d84dbc8ab.*.json`

**Modified:** `scripts/build_projection.py` (overlay reader + supersession skip + alias
rewrite) · `scripts/run_baseline_gates.py` (shared `live_events`/`read_overlays`;
applied to 4 checks) · `scripts/run_bulk_extraction.py` (`--only DOC_ID`, selection
only — needed because resume is keyed on doc_id, so a superseded doc is otherwise
"done" forever) · `corpus/evidence/decisions.jsonl` (4 dixie events) ·
`events/batch-004.jsonl` (re-extraction) · `docs/research/bulk_v1_gate_report.md`
(fixed-path artifact, overwritten by the runner; prior values transcribed into the
dated report, old version in git)

**Deleted:** `corpus/bulk_md/introducing-the-oecd-ai-capability-indicators.md` —
copied to quarantine first; removed only from the live corpus path so dixie's
promote-verified-alternate path could fire. Content preserved.

## Out of scope, untouched

§515 (verified already done, reported above) · FCSM 20.04 / 23.02 inbox backups ·
no corpus expansion · no threshold change · no extraction-config change · no commits.

## Open items for the operator

1. ~~`doc-fcsm-framework-for-data-quality` → 20-04 or 23-02?~~ **RESOLVED 2026-08-14**
   by operator adjudication rule → `fcsm-20-04`, branch `bare_title`. See above.
2. `OVERSIZE_ALLOW` still lists `introducing-the-oecd-ai-capability-indicators`
   (287,110 chars). Now moot — the PDF is 142,364, under the 250K limit. Left in
   place; removing it is a config edit this task did not authorize.
3. `build_projection.py` reports `documents: 72` (counts `manifest_add` events, not
   distinct docs). Graph is correct at 71. Cosmetic counter defect, unfixed.
4. Control-plane note, Wintermute side: `wm_power.py on` re-enabled **all** circuits,
   including `extraction`, which had been OFF by operator act since 2026-08-05. That
   was the state requested for this task, but the command is broader than "master on".
