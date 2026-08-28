# RESULT — 2026-08-27_chunked_pilot

**Task:** `cc_tasks/2026-08-27_chunked_pilot.md` (Seldon: see §Exit). **Addenda:** none exist —
`cc_tasks/2026-08-27_chunked_pilot_ADDENDUM*.md` matched nothing at dispatch and at close.
**Session:** 2026-08-27 evening ET / 2026-08-28 UTC.

---

## §0 — Band protection: what the STOP file could and could not do

**Premise vs live state (reported, not reconciled).**

| § | premise | true? | live state |
|---|---|---|---|
| §0 | Lane 4 driver pid `70576`/`70596` | **partly** | `70576` is the driver and was alive throughout. `70596` was killed by the driver's own 3898 s subprocess timeout at 2026-08-27T18:52:59Z (recorded in the previous task's RESULT); at dispatch Lane 4's stage-2 child was pid `5123`. |
| §0 | "sleeping to 00:05Z … write the STOP file **now, before 00:05Z**" | **false at dispatch** | The task file was written at 00:36Z and dispatched at ~00:40Z. Lane 4 had already woken at 00:05Z and stage 2 was running when the first action of this task executed. The STOP file was written at **00:45Z**, 40 minutes after the deadline the task assumed. |
| §0 | stage 2 would need most of the band | **false** | Stage 2 was 92 % complete: 5,130 of 5,554 proposals judged, **424 remaining**. It finished on its own at 01:14Z. |

**What was done.** `state/overnight_burn_STOP` was written at 00:45Z with a reason block naming
this task. That is the file `scripts/overnight_burn.py` honors (`STOP_FILE`, line 43;
`halted()`, line 67). **No process was killed.** The task instructed writing the STOP file, not
killing anything, and on the live numbers killing was the worse option: stage 2 had 424
proposals left, and a kill would have bought ~2M tokens at the price of a resume task for 8 %
of the work.

**Stage-2 judgment count at stop (§0 requirement).**

| moment | judged | accepted | rejected |
|---|---|---|---|
| STOP file written, 00:45Z | 5,110 | — | — |
| stage 2 complete, 01:14Z | 5,554 | 4,021 | 1,533 |

670 of those judgments were made after the 00:00Z band roll and before the STOP file existed.

**Defect found in the driver (recorded, not fixed here).** `scripts/overnight_burn.py::lane4`
checks `halted()` at the top of the stage loop (line 703) and before each relocation shard
(line 774) — but **not between the stage loop and step (b), the acceptance sample** (lines
724-726). So the STOP file blocks relocation, which is what §0 names as the band risk, and does
**not** block the 100-item acceptance gate, which the driver entered at 01:14Z on a
now-complete stage-2 class. That gate is bounded and correctly sequenced (it runs on the
complete class), so it was allowed to proceed; the missing guard is the finding.

---

## §1 — The existing chunker: located, assessed, NOT reused as a unit

Searched `/Users/brock/GitHub/wintermute` and `/Users/brock/.wintermute` (`find -iname "*chunk*"`,
`grep -l "def .*chunk|chunk_size|chunk_text"` excluding `.venv`). Three artifacts, none of them a
structure-aware chunker:

| artifact | unit | overlap | tokenizer | headings | verdict |
|---|---|---|---|---|---|
| `neo4j_graphrag…FixedSizeSplitter`, driven by `extraction.chunk_size` / `chunk_overlap` in `~/.wintermute/sources/*.yaml` — the **production** extraction chunker (`p2_spike_extract.py:223`, `p2_g2pp_extract.py:155`) | fixed **characters** (era-2b: 4,000, overlap 0; p2 spike: 4,000) | 0–200 chars | none (characters) | none | **unit not reused** — fixed-character, splits mid-paragraph |
| `~/.wintermute/scripts/stage_book.py` | chapter, with a `chunk_by_tokens` fallback at ~4,000 "tokens" | none | **chars/4**, not a tokenizer | detects chapter/ALLCAPS headings | **pattern reused, code not** — its heading families (numbered, ALLCAPS standalone) are the model for the plain-text detector here; its unit and token proxy are wrong for a 1,500-token cap |
| `~/.wintermute/scripts/p3_chunking_probe.py` + `state/p3_build/chunking_frontier.json` | — | — | — | — | **the internal precedent for this whole pilot** |

**The internal precedent, cited.** Wintermute ran the *same experiment* on 2026-08-13 — chunk
size varied, model/schema/prompt/grounding held constant, 8 chat documents:

- 4,000-char chunks: **65 entities**; whole-doc (60,000): **26**. Era-1 chat entities/doc 27.93
  vs era-2 at 60,000: **3.12**.
- `chunking_frontier.json` records the reading as "the 4,000 arm is the only difference clearly
  outside noise; 30,000 reading ×0.92 is consistent with no effect", and production moved to
  `chunk_size: 4000` (`sources/p3_era2b_config.yaml`).

That is an independent, internal replication of Edge et al. 2024's ~2× entity-reference finding,
on this operator's own stack, eleven days before the whole-document pilot was designed without
citing it. It does not speak to *faithfulness*, which is what this pilot measures.

---

## §2/§3 — What was built

- `kg/extraction/chunker.py` + `kg/extraction/chunker_config.yaml` (all tunables are data),
  15 tests in `tests/test_chunker.py`.
- `kg/extraction/chunked_template.md` — `prompt_template.md` v0.3.5 with the framing swapped and
  **nothing else**; sha-pinned in the new `chunked_v035` profile (`scripts/run_profiles.yaml`),
  which `apply_profile` refuses to run under a drifted prompt.
- `scripts/chunked_pilot.py` — phases `dry_run | extract | ingest | resolve | judge | register`.
- Events to the **tagged** shard `events/batch-016_chunked_v035.jsonl` (tagged shards are never
  replayed into the graph — an experiment arm must not become graph state).

### Discrepancy: the input the task names does not exist

§2 names `corpus/bulk_md/<doc_id>.md` as the chunker's input. **None of the five pilot documents
has a file there** (that directory holds 17 unrelated documents). All five are PDFs read through
`run_bulk_extraction.doc_text` → pypdf, which is also the exact text the whole-document arm was
given. Measured on that text:

| doc | chars | ATX headings | blank-line paragraphs |
|---|---|---|---|
| data-readiness-for-ai-a-360-degree-survey | 162,981 | 0 | 1 |
| aidrin-hiniduma-2024 | 67,587 | 0 | 1 |
| fcsm-23-02-a-framework-for-data-quality-case-studies | 136,370 | 0 | 4 |
| from-accuracy-to-readiness-metrics-and-benchmarks-for-human | 49,728 | 0 | 1 |
| mitre-ai-maturity-model | 102,257 | 0 | 1 |

So §2 rules 1 and 2 as literally written have nothing to bind to. Both were implemented as
written **and** a plain-text family was added for this input: headings by the numbered
(`2 RELATED WORK`, `3.1 …`) and ALLCAPS-standalone patterns from `stage_book.py`, paragraphs by
the short-line reflow rule (a line below 0.85 × the document's 95th-percentile line width closes
a paragraph). Which family fired is recorded on every chunk set (`structure_source`); for all
five documents it was `plain_text`, heading level 1. Chunking the pypdf text rather than
re-deriving markdown with docling was deliberate: a different text extractor would have been a
**second** variable and the task's whole claim is that there is only one.

**Tokenizer (§2.3).** `model_stub` exposes no tokenizer — it reads usage off the `claude -p`
envelope after the call. §2.3's stated fallback therefore applies: **tiktoken `cl100k_base`**,
recorded on every chunk set and in `chunker_config.yaml`.

**Two chunker findings, both config-recorded:**
1. Running page headers/footers were being detected as headings — `"AUGUST  2022"` appears 41
   times in `mitre-ai-maturity-model` and forced 41 spurious section boundaries (91 chunks,
   median 201 tokens). A line repeating more than `max_heading_repeats` (2) times is a running
   header, not a heading: mitre 91 → 52 chunks.
2. A chunk holding only heading lines has no document body to extract from. 23 of 151 chunks
   were of that shape (17 in mitre). They now ride forward into the next chunk (`emit(force=…)`),
   and the end-of-document flush keeps the trailing heading text: 151 → **128 chunks**.

---

## §5 — Probe-protocol changes, applied to BOTH arms

§5 requires the two defects diagnosed in `2026-08-27_pilot_instrument_verdict.md` to be fixed in
both arms' facts before judging. A third was found while implementing them. All three are
versioned; the whole-document arm was **re-judged from scratch** under the new versions, so the
comparison is like-for-like and the banked 08-27 Instrument numbers are not comparable to the
rows below (superseded for comparison, not retracted).

| # | change | version | what it fixes |
|---|---|---|---|
| 1 | coordination is not redistributed | `decompose_version` 1.0.0 → **1.1.0** | 14 of 27 `span_truncated` facts had every content word inside the span; they failed only because the decomposer rewrote `"designed for data profiling, cleansing, and monitoring capabilities"` into `"is designed for data monitoring capabilities"` — a sentence the source never wrote, which no quote from the source can entail. |
| 2 | mid-noun-phrase truncation check | `kg/extraction/span_checks.py` **1.0.0** (7 tests) | The other 13: a span cut before its head noun (`"…consistency of the state-reported commercial"`). POS-based (nltk perceptron tagger): the span's last token is a noun-modifier and the document's next token is its head noun. **Records only** — it never removes a fact from a denominator, because excluding a class from a pre-registered metric is moving the threshold by other means. |
| 3 | a fact about an attribute is judged against *that attribute's* span | `probe_judge_version` 1.0.0 → **1.1.0** (5 tests) | Found here, not in the task. `scripts/probe_judge.py::load_facts` presented `item["grounding_span"]` — the node's own, name-bearing span — for **every** fact, including `method` facts, even though prompt v0.3.4+ requires Instruments to carry per-attribute `grounding_spans`. So the protocol was asking whether the *name* span entailed the *method* content; 26 of the 27 `span_truncated` labels were `method` facts judged that way. `span_for()` now presents the attribute's own span when one exists and falls back to the node span otherwise (and for every edge). This is a defect in the measuring instrument, not a threshold: no threshold moved. |

Neither the pre-registered thresholds (F_upper < 0.10, item-faithful ≥ 0.70, pooled ≥ 20 per
stratum) nor the class definitions were touched.


---

# ⏸ PAUSED — operator stop, 2026-08-28T01:37Z

**Operator instruction (verbatim intent):** "full pause until I say go again. We will run out of
limit before this job finishes."

Nothing is running. Extraction was stopped mid-pass, everything already paid for was ingested at
zero further spend, and the run is resume-safe: `--phase extract` skips any chunk with a
persisted raw, `--phase ingest` skips any chunk already on the shard.

## State at pause

| doc | chunks | extracted | remaining |
|---|---|---|---|
| data-readiness-for-ai-a-360-degree-survey | 30 | **30** | 0 |
| aidrin-hiniduma-2024 | 18 | 14 | 4 |
| fcsm-23-02-a-framework-for-data-quality-case-studies | 27 | 0 | 27 |
| from-accuracy-to-readiness-metrics-and-benchmarks-for-human | 18 | 0 | 18 |
| mitre-ai-maturity-model | 35 | 0 | 35 |
| **total** | **128** | **44** | **84** |

- Spend: run `pilot_chunked_v035` **settled 2,851,499** of a declared 13,000,000 ceiling;
  `committed_today` 11.4M of the 55M band. Reconcile `ok: true`.
- 44 chunk raws persisted under `events/raw/chunked_v035/`; all 44 ingested to the tagged shard
  `events/batch-016_chunked_v035.jsonl` — 746 node events, 1,244 edge events, 379 mention stubs,
  281 diverted relations.
- Judging (`--phase judge`) has **not** run. No judge tokens spent. The whole-document arm has
  not been re-judged under the new protocol versions either.

## What the 44 chunks already show (partial, 2 of 5 docs)

These are observations on an incomplete arm and are **not** a verdict; the pre-registered gate is
not evaluated until both arms are judged.

1. **Chunking costs more here, not less.** 44 calls settled 2,851,499 → **64,807 tokens/chunk** →
   ~8.3M projected for the five documents, against the whole-document arm's measured **3,925,860**
   — about **2.1× more expensive**. The driver is visible in the raws: the prompt asks for an
   exhaustive concept inventory and the model produces one *per chunk* (33–46K output tokens for
   a 1,500-token chunk; median call duration 334 s). This answers the lab note's first open
   question ("does per-doc cost land at or below the single-pass figure?") in the negative,
   independent of what the faithfulness judge later says.
2. **Node yield is much higher.** 746 admitted nodes over 2 documents (432 Concept, **101
   Instrument**, 96 Claim, 65 Definition, 33 Measure) against the whole-document arm's 24
   Instruments over all five. Consistent in direction with Edge et al. 2024 and with Wintermute's
   own 2026-08-13 measurement (§1).
3. **The quarantine rate is high and must be reported with the yield.** 75.5 % of items
   (666 of 882 over the first 10 chunks) were quarantined, nearly all `span_partial` — the
   model's quote does not contain the node's own name verbatim. Some of this is pypdf damage:
   the model quoted `Heterogeneous Euclidean-Overlap Metri (HEOM)` because the extracted text
   is missing the "c". The same gate ran on both arms, so the comparison stays like-for-like.
4. **The semantic stratum is nearly empty at chunk scope.** 20 semantic edges of 1,244
   (19 `subtype_of`, **1 `has_component`**). Relations keep failing endpoint typing because the
   same metric is a Concept in one chunk and an Instrument in another. On this trajectory the
   chunked arm may not reach §5's pooled ≥ 20 precondition for `semantic_edge` across all five
   documents — which would itself be the finding.
5. **ADDENDUM-06's closed `diversion_reason` list is not honored by the model.** It emitted 34
   distinct values over the first 10 chunks, most of them whole sentences. Report-side
   normalization was added (`normalize_reason`, raw string untouched on the shard):
   281 diversions → `other 108, unstated 94, cross_chunk 47, structural_inference 20,
   other:schema_cannot_express 12`. **cross_chunk is 47/281 = 16.7 %** so far.

## To resume (no decisions pending, no state to reconstruct)

```bash
python scripts/chunked_pilot.py --phase extract --ceiling-tokens 13000000 --workers 8
python scripts/chunked_pilot.py --phase resolve
python scripts/chunked_pilot.py --phase judge --fact-cap 120 --judge-ceiling 6000000
python scripts/chunked_pilot.py --phase register
```
`extract` runs `ingest` itself on completion. Remaining estimated spend: ~5.4M extraction
(84 chunks × 64,807) + ~4M judging.

## Ledger note

Three kill/relaunch cycles (a chunk-boundary fix, a truncation-detector fix, and this pause) left
reservations outstanding for in-flight calls. Those calls **had dispatched**, so their tokens were
probably consumed server-side; the reservations are deliberately left committed rather than
released, because releasing them would under-count real spend. `reconcile` reports `ok: true`.

