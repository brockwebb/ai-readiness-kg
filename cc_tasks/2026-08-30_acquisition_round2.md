# CC Task — Acquisition round 2: SEO/AI-O cluster, reference-driven expansion, evaluated cuts

**Date:** 2026-08-30. **Repo:** /Users/brock/GitHub/ai-readiness-kg
**Mode:** Zero `model_stub` spend. Metadata APIs, web retrieval, deterministic parsing, code. Any step needing a model call is out of scope and stops. Independent of the chunked pilot — runs in parallel.
**Before starting:** glob and read any `cc_tasks/2026-08-30_acquisition_round2_ADDENDUM*.md`. Read `docs/corpus/acquisition_candidates.md`, the manifest, and the T0/T1 substrate RESULT for current state.
**Result:** `cc_tasks/2026-08-30_acquisition_round2_RESULT.md`. `seldon cc complete` this file at the end. Commit, push.

## 0. Standing

Round-2 machinery exists but is starved: reference lists cover 2 of 178 docs, so coupling-based candidate expansion has almost nothing to chew on. The AIO/GEO cluster was queued but only partially followed. The operator's observed gap: SEO/AI-O/GEO and adjacent recent literature is under-represented.

Manifest discipline (established practice, FSS pattern): every evaluated candidate gets a record — admitted with reason, or **cut with reason**. Cuts are decided evidence, not deletions; they close the question unless new evidence reopens it. No candidate is silently dropped.

## 1. Feed the coupling engine — reference parsing from Docling output

The 176 docs without reference lists are mostly gov/gray PDFs no index covers. Parse their reference sections from the existing Docling output (T1 store) — deterministic: locate reference/bibliography sections by heading, split entries, extract DOIs/arXiv ids/titles/years by pattern. No model calls.

- Evidence class: `bibliographic_derived` — new class, derived from the document's own text. NEVER pooled with `bibliographic` (third-party asserted). Records carry `derivation: docling_refparse` and the section offset.
- Report per-doc: references found / DOIs resolved / unparseable. An imperfect parse is fine; this feeds ranking, not claims.
- Re-run the ≥3-citer coupling expansion over the enlarged reference set. Regenerate `docs/corpus/acquisition_candidates.md` with the same columns (candidate, score, citing docs, OA status, fetchable vs manual).

## 2. SEO / AI-O / GEO cluster search

Targeted retrieval for the under-represented cluster: generative engine optimization, answer-engine optimization, AI-readable content/data surfaces, llms.txt, machine-first metadata for AI consumption, agent-consumable knowledge formats (OKF belongs here). Sources: OpenAlex (keyed), Crossref, Semantic Scholar, arXiv, plus direct web for the gray literature this cluster lives in (spec repos, standards posts, measured-practice writeups).

- Emit candidates into the same candidates file, source recorded, cluster-tagged.
- Quality bar for gray-lit candidates: primary sources (specs, original announcements, measured results) over commentary. A Medium explainer of a spec is not a candidate; the spec is.

## 3. Evaluate — admit or cut, nothing pending

For every candidate (rounds 1 leftovers + new): apply the standing admission rules (AUTH-2 class).

- **Admit:** fetch OA items, manifest entry with reason and cluster tag. Paywalled/unfetchable → `manual_download_needed` list for the operator.
- **Cut:** manifest record `evaluated_not_admitted` with the specific reason (no marginal contribution over doc X; commentary not primary; out of scope; superseded by Y). Cuts are terminal absent new evidence.
- Nothing remains in candidate limbo at close. The candidates file empties into decisions.
- Do not invent a contribution rubric beyond the standing rules; where a call is genuinely ambiguous, admit conservatively is wrong — cut with reason `ambiguous_contribution` and list it in a short operator-review section of the RESULT rather than admitting noise. Ever-expanding graphs are trash; the default is cut.

## 4. Downstream hooks (no extraction)

- Admitted docs enter T0 (keyed harvest, eligibility gate applies) and T1 (Docling + chunking + index) via the existing pipelines. Run both for new admits.
- `t2_priority` regenerated. New admits get priority scores; none of this dispatches extraction — the bulk decision waits on §3 of the pilot, per ADDENDUM-04.

## 5. Report

Counts: references parsed, candidates generated (by source), admitted / cut / manual, T0+T1 coverage after. The cut list with reasons, verbatim, in the RESULT. Register the regenerated candidates and manifest artifacts in Seldon.

## 6. Out of scope

Any model call; any extraction; relevance summaries written by a model; changes to admission rules; touching the pilot's shards, profiles, or templates.
