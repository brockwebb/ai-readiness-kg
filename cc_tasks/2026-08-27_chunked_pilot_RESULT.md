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


---

# ADDENDUM-02 RESULT — orphaned-reservation release path

**Date:** 2026-08-29 (UTC). Zero model spend: code, tests, and one ledger write.
**Exit criteria:** suite green (233 passed) · 22 releases on the ledger · `outstanding` zeroed
for all four runs · dry-run table below · committed and pushed.

## Prior art (methodology §7.1 / DD-025)

Named, not invented here. This is **lease expiry**: Gray & Cheriton 1989, *Leases: An Efficient
Fault-Tolerant Mechanism for Distributed File Cache Consistency* — the canonical answer to "the
holder died, reclaim the resource" — and the in-doubt-transaction resolution of presumed-abort
two-phase commit (Mohan, Lindsay & Obermarck 1986). The liveness probe itself is the Unix
stale-pidfile idiom (`kill(pid, 0)`). **Internal precedent search** across this repo and the
Wintermute/Seldon decision logs (grep `orphan|stale lock|lease|os.kill|liveness|reap`, 2026-08-29):
no prior reaper — every existing `orphan` in this repo is the graph-structural `orphan_rate` gate,
an unrelated sense of the word.

**Where the literature disagrees with the spec, recorded:** the field prefers a *renewable lease*
to a *post-hoc liveness probe*, because a probe races with PID recycling. The probe was implemented
anyway, for two reasons on the face of it: the reservations already on disk carry no lease field
(a lease cannot reap holds written before it existed), and the race is safe in one direction only —
PID recycling can make a dead owner look *alive*, which under-releases, but cannot make a live owner
look dead on the host that owns the PID. A renewable lease is the right shape if this ever needs to
reap while a run is live; it is not needed to reap holds whose owners are already gone.

## What was built

`python -m kg.spend release-orphans [--run-id R] [--commit]` (`kg/spend.py`).

- **Orphan requires all three** (§1): outstanding (no settle, no release), age > threshold, owner
  PID provably not alive **on this host**. Any one alone spares the hold.
- **The host guard is an addition to the spec, and it is load-bearing.** A PID absent *here* says
  nothing about a process on another machine; without it, a multi-host ledger would release live
  calls. Reservations from another host report `liveness: unknown_other_host` and are never reaped.
  Mutation-proven (M3 below). The live ledger is single-host (1,991/1,991 records `HexagonMBP.local`),
  so this bought nothing today and costs nothing tomorrow.
- **Threshold in config, not code** (standard §2): `controls.yaml` → `spend.orphan_reservation_age_seconds: 600`.
  600 s is 1.8× the chunked pilot's *measured* 334 s median call duration, so a live call is never in
  reap range on age. A missing key is a **loud refusal**, not a default — `release_orphans` raises
  `SpendConfigError` rather than reap against an implicit threshold (M6).
- **Dry run is the default**; `--commit` is the only thing that writes.
- **Ledger stays append-only.** No prior record is touched; releases are new lines carrying the
  reservation id, run, amount returned, `reason: orphan_pid_dead`, and the full liveness evidence
  (owner pid/host, probe host, age, threshold, and the literal probe result).

### Deviation from §2, with reason

The spec names the event `reservation_released`. It is written as **`record: "release"` with
`reason: "orphan_pid_dead"`** — the record kind the ledger already has and that `_tally` already
honours. A second record kind meaning the same thing to the capacity math is a latent trap: any
future code path that checks `kind == "release"` would silently miss it, which is precisely the
two-mechanisms failure that produced the 22M incident (DD-022). The audit distinction the spec asked
for lives in `reason` + `released_by` + `orphan_evidence`, which is strictly more evidence than the
name would have carried.

### Deviation from §4, with reason

§4 states `committed − settled − released = outstanding`. The implemented invariant is
**`committed = settled + outstanding`**, unchanged from DD-022: a released reservation leaves the
tally entirely rather than becoming a negative term. `released` is reported by `status` as an audit
column — how much capacity a reap handed back — not as a term in the capacity arithmetic. The
invariant is asserted per run in the test suite.

## Tests (8 new, `tests/test_spend_guard.py` #10–#17)

Positive-control discipline (methodology §7.5): no monitor is trusted until a seeded known-bad fires
it. **#13 is that control and it runs in-suite**, so it cannot rot — with `_pid_alive` stubbed dead,
the aged live-owner hold that #12 spares is reaped.

**Mutation matrix — every condition killed at least one test:**

| # | Mutation of the shipped code | Tests that failed |
|---|---|---|
| M1 | liveness probe always reports dead | #11 live-fresh, #12 aged-live |
| M2 | `age >` conjunct dropped | #17 dead-pid-inside-window |
| M3 | host guard removed | #14 other-host |
| M4 | `--commit` gate removed (dry run writes) | #10 seeded-orphan |
| M5 | `release` no longer clears a reservation | #10 (double-reap) |
| M6 | missing-config check replaced by a default | #15 loud-config-error |

**M2 initially killed nothing** — the age condition was mandated by §1 but untested, so it could
have been deleted silently. #17 was written to close that gap and now fails under M2 as shown.

**Method note, recorded because it invalidated a first pass.** The first mutation run was executed
against **stale `.pyc` bytecode**: `cp`-ing the clean file back gave a source whose (mtime, size)
pair matched the cached bytecode of the mutated version, so pytest kept running mutated code after
the restore — which is how a passing test appeared to fail after a clean restore. The matrix above
was re-run under `PYTHONDONTWRITEBYTECODE=1` with `__pycache__` cleared. **Any future mutation
testing in this repo must disable bytecode caching**; a mutation harness that silently tests the
wrong bytes is worse than no harness.

Full suite: **233 passed** (was 225; +8).

## First real run

Dry run, 2026-08-29T02:42Z. **22 reservations across 4 runs, 1,326,274 tokens** — every owner PID
dead, every hold ~1 day old, **0 retained** (nothing was running).

| run_id | reservations | tokens | owner PIDs | oldest |
|---|---:|---:|---|---:|
| `pilot_chunked_v035` | 19 | 1,113,669 | 12567, 13470, 15846 (fleet workers) | 92,291 s |
| `pilot_v035b_opus5` | 1 | 111,000 | 96564 | 105,222 s |
| `restoration_v2_s2` | 1 | 65,605 | 46662 | 151,077 s |
| `restoration_v2_s1` | 1 | 36,000 | 25559 | 172,005 s |
| **total** | **22** | **1,326,274** | all `liveness: dead` | |

**Premise discrepancy, reported not reconciled:** §6 expects "the four known orphans released". The
§0 report named four *runs* holding capacity; the underlying holds are **22 reservations**. The
token total is unchanged and matches §0 exactly (1,326,274). The 19 holds on `pilot_chunked_v035`
across three PIDs are the three fleet workers killed mid-flight by the operator stop — one hold per
worker in flight, plus the per-worker backlog, exactly the shape the reaper is for.

Committed with `--commit`. Verification after the write:

- Ledger grew by exactly 22 lines; `head -1991` is byte-identical to the pre-reap file — **no prior
  record mutated**.
- All 22 appended records are `release` / `orphan_pid_dead`, summing to 1,326,274.
- `outstanding` is **0 for all 11 runs**; `committed == settled + outstanding` asserted and holds
  for every run.
- `reconcile` still `ok: true` for all four reaped runs, settled totals unchanged
  (2,851,499 / 5,517,758 / 21,514,241 / 7,458,511) — reaping returns *reserved* capacity and does
  not touch *settled* spend, which is the point.
- `committed_today` reads 0, but **not because of the reap** — the UTC day rolled to 2026-08-29
  between the §0 report and this run. The reap returned reserved capacity dated 08-27/08-28.

Recovered against ceilings: `pilot_chunked_v035` remaining 9,034,832 → **10,148,501**;
`pilot_v035b_opus5` 3,371,242 → **3,482,242**; `restoration_v2_s1` 33,449,759 → **33,485,759**;
`restoration_v2_s2` 47,475,884 → **47,541,489**.

## Not done

`release-orphans` is **not** wired into any runner as an automatic pre-flight. A reaper that runs
itself is a second mechanism operating on the ledger without an operator in the loop, and the
capacity it returns is exactly the capacity a stuck run would otherwise be refused for — which is
information, not noise. It stays a hand-run verb until there is a reason for it not to be.

---

# ADDENDUM-01 §1 RESULT — the banked 44 chunks, judged

**Date:** 2026-08-29 (UTC). **Both Instrument strata PASS the pre-registered gate.** This
**reverses** the whole-document arm's banked FAIL, and the reversal is an instrument change,
not an extraction change — see "What actually moved" below.

## 1. Pre-judge census (§1: count first, report before judging)

| arm | Instrument | semantic_edge | documents covered |
|---|---:|---:|---|
| chunked (44/128 partial) | **92** | **20** | 2 of 5 |
| wholedoc (banked) | **24** | **21** | 5 of 5 |

**Premise discrepancy, reported not reconciled.** §1 states "530 admitted nodes / 841 edges
across 34 ingested chunks". Live state is **746 nodes / 1,244 edges across 44 chunks** — the
addendum was drafted while ingest was still catching up. Nothing was reconciled; the larger
figure is what the shard holds and what was judged from.

## 2. The semantic stratum: not judged, on stronger grounds than §1 anticipated

§1 predicted the semantic stratum would land under 20 and fail the precondition. It landed at
**20 (chunked) and 21 (wholedoc)** — the precondition *passes*. It is still not judgeable, for
a reason §1 did not have in view:

`probe_decompose.deterministic_facts` emits **exactly one fact per edge**, so for this stratum
n_facts = n_items. Under the aggregator's own Wilson 95% interval, `F_upper < 0.10` is
attainable only at **n >= 35**. At n = 20 a **perfect result — zero fabrications — still returns
F_upper = 0.1611**; at n = 21, 0.1546. The gate cannot be cleared at that sample size however
good the extraction is.

**This is a defect in the pre-registration itself, recorded and not repaired here.** The
precondition (pooled >= 20) and the threshold (F_upper < 0.10) are mutually inconsistent at the
boundary: a stratum sampled at exactly the pre-registered minimum can only ever FAIL. The
minimum count consistent with the threshold is 35, not 20. This is arithmetic from the task's
own F_STOP and the aggregator's own interval method — no threshold was moved, and the finding
applies identically to both arms. Prior art for the calculation, named not invented: the
one-sided binomial bound with zero events (Louis 1981; Hanley & Lippman-Hand 1983, "If nothing
goes wrong, is everything all right?" — the rule of three, of which Wilson is the exact form).

Judging it anyway would have bought a foregone FAIL at roughly 470K tokens. ADDENDUM-01 §1
forbids judging a sub-minimum sample; this is that case, reached by the stronger route. Both
rows are recorded **GATE UNREACHABLE** with the counts, per §1's instruction to record rather
than judge.

## 3. Verdict

| arm | stratum | admitted | judged items | facts | F [Wilson 95%] | item-faithful | gate |
|---|---|---:|---:|---:|---|---|---|
| chunked | Instrument | 92 | 30 | 80 | **0.0000 [0.0000, 0.0458]** | **30/30 = 1.000** | **PASS** |
| chunked | semantic_edge | 20 | 0 | — | — | — | GATE UNREACHABLE |
| wholedoc | Instrument | 24 | 24 | 75 | **0.0000 [0.0000, 0.0487]** | **22/24 = 0.917** | **PASS** |
| wholedoc | semantic_edge | 21 | 0 | — | — | — | GATE UNREACHABLE |

Zero fabrications in either arm. Non-entailments: chunked none; wholedoc 2 of 75
(1 `span_truncated`, 1 `subject_dropped`) — neither is a fabrication class.

Rater agreement with the aggregated label: chunked `claude-opus-4-8` 1.000 / `claude-sonnet-5`
1.000; wholedoc 1.000 / 0.947. Same two raters as every prior probe run, unchanged.

Mid-noun-phrase span sidecar (recorded, never subtracted from a denominator): chunked 9/80,
wholedoc 12/75.

## 4. What actually moved — the prior FAIL was an instrument artifact

The whole-document arm's banked verdict was **F_upper 0.158 / item-faithful 0.292 (FAIL)**. The
same arm, same banked extraction, same raters, same thresholds now measures **F_upper 0.0487 /
item-faithful 0.917 (PASS)**. **No extraction was re-run.** The only change is the probe:
decompose 1.0.0 -> 1.1.0 and probe_judge 1.0.0 -> 1.1.0, i.e. the two attribute-quoting fixes
diagnosed in methodology §6.3 (26/34 non-entailments were truncated `method` spans; 14 a
probe-protocol artifact, 13 a mid-noun-phrase quote).

So methodology §6.3's diagnosis is confirmed at the strongest available level: **the Instrument
stratum was never failing on extraction faithfulness. It was failing on how the probe cut the
spans it judged.** A validity instrument that mis-measures its own subject produced a FAIL
verdict that stood for two days and is now withdrawn.

**Consequence for DD-023, recorded as an erratum on that decision, not a reversal of it:**
DD-023 retired whole-document extraction on four measurements. Measurement (3) — "Pilot gate
FAIL both strata under the whole-doc arm (Instrument F_upper 0.158 / faithful 0.292)" — is
**superseded**: that arm now PASSES. Measurements (1) and (2), the cost pathology, are
untouched and are measurements of a different thing. **DD-023's decision therefore stands on
cost, and no longer on faithfulness.** The erratum is filed in `docs/design_decisions.md`; the
decision is not re-opened here, because nothing in §1 bears on the cost argument that carries it.

## 5. Cost — like-for-like, on the documents the chunked arm actually covers

The headline "2.1x" in the pause record projected all five documents from a partial. On the two
documents with any chunked extraction:

| doc | chunked settled | whole-doc settled | ratio | chunked completeness |
|---|---:|---:|---:|---|
| data-readiness-for-ai-a-360-degree-survey | 2,021,101 | 1,330,683 | **1.52x** | 30/30 complete |
| aidrin-hiniduma-2024 | 795,582 | 903,365 | 0.88x | 14/18 partial (~78%) |
| both | 2,816,683 | 2,234,048 | 1.26x | mixed |

**The only honest single-document number is 1.52x** — the one complete chunked pass. The 0.88x
on `aidrin` is an artifact of its arm being 4 chunks short and must not be quoted as a chunking
saving. Direction is unchanged from DD-023 (chunking under the exhaustive-verbatim contract
costs more, not less); the magnitude is **1.52x on complete evidence, not 2.1x**.

## 6. Spend against the §1 ceiling

Declared 2,000,000 (the top of §1's stated ~1-2M). **Settled 2,023,212 — 23,212 over.** This is
the guard's designed at-most-one-in-flight overshoot, not a breach: a reservation is taken at an
estimate and settled at the measured cost, so the final call can land above the estimate that
admitted it; the door then closes (`tests/test_spend_guard.py` #3). Refusals: 0. The run
completed; nothing was truncated by the guard.

**§1's ceiling estimate was low, and why.** §1 sized ~1-2M "from per-class mean". The realized
judge-class mean here is **52,230/call over 16 settles** (median ~40K, one 207,591 outlier)
against the ~40K the estimate implied. Two arms x two raters x 155 facts at batch 10, plus
decompose, is 39 calls. Sized on the realized mean the section was always a ~2.0M job.

Spend was held down by two decisions taken before any label was bought, both reported here
because they bound what the numbers can support:
- **Instrument item cap 30/arm**, seeded (`arm_<arm>:30`) and reproducible. The chunked arm
  judged 30 of its 92 admitted Instruments; the whole-doc arm's 24 were all judged. A smaller
  sample widens the Wilson interval and so makes PASS *harder*, never easier — it is a spend
  bound, not a threshold move.
- **Semantic stratum not judged** (§2 above), saving roughly 470K.

## 7. Two defects found and fixed mid-run (`scripts/probe_decompose.py`)

Both were found live while sizing this section; the first cost one judge call (78,898 tokens)
on a fact set that was missing every free-text proposition.

1. **Resume marked an item done on the presence of ANY fact.** An item whose deterministic
   facts were written but whose free-text fields never reached a model batch was skipped
   forever. The lost fields are `method`/`description` — precisely where this stratum's
   non-entailments live (§6.3) — so the silent loss landed exactly on the measurement. Fixed by
   tracking `have_model` separately from `done`: the model half is owed whenever an item has
   free-text fields and no model-sourced fact yet, independently of its deterministic half.
   Effect on this run: arm_chunked went from **47 facts to 80** after the fix.
2. **`--dry-run` wrote the deterministic facts.** A dry run mutated the resume state of the run
   it was estimating for, which is how (1) was triggered: my own sizing dry-run poisoned it.
   Fixed — a dry run is now a read.

Tests written **before** the fixes, both failing first, both mutation-verified after
(`tests/test_probe_resume.py`, +2). Suite **233 -> 235 passed**.

An existing test (`test_decompose_still_decomposes_an_item_whose_sample_was_rebuilt`) had used
`--dry-run` as a shortcut to avoid a model call and therefore **asserted the write-on-dry-run
behaviour that is now a proven defect**. It is amended, with the reason recorded in its
docstring — a test that pins buggy behaviour is not evidence, and was silently protecting this
defect.

**Method note.** A `{min_facts}` placeholder in `write_verdict` shipped uninterpolated into the
first written verdict (a `str.replace` whose anchor did not match, applied without an assert).
Corrected in source and in the artifact. Every other patch in this task asserts its anchor
before replacing; that one did not, and that is the whole reason it failed silently.

## 8. What §1 does and does not establish

**Establishes:** the Instrument stratum is faithful under BOTH extraction units — zero
fabrications, F_upper 0.046 (chunked) and 0.049 (wholedoc), item-faithful 1.000 and 0.917. The
pre-registered question "does chunk-local extraction move faithfulness?" answers: **on this
evidence it does not move it, because there was nothing to move — both units already pass.**
The instrument, not the unit, was the problem.

**Does not establish**, and must not be read as establishing:
- Anything about the semantic stratum in either arm (gate unreachable at the available n).
- A like-for-like document comparison. The chunked arm covers 2 of 5 documents, and 27 of its
  30 judged Instruments come from a single document (`data-readiness-for-ai-a-360-degree-survey`).
  The whole-doc arm spans all five. **The arms do not run on the same document mix.**
- Any ranking of the two arms on faithfulness. Both pass; the intervals overlap almost
  completely; the item-faithful difference (1.000 vs 0.917) is 2 non-entailed items out of 24
  and is not a detectable difference at these sample sizes.
- Recall. Nothing in this protocol measures it, in either arm.

Per §4 of the addendum, §2 and §3 do not start on this result; this section is a hard stop.

---

# ADDENDUM-03 §1 — v0.3.7 emission contract built (2026-08-29)

**Zero model spend, verified**, not merely intended: the spend ledger's last entries belong to
the overnight `chunked_pilot_judge` run and nothing in §1 dispatched a call. `committed_today`
2,023,212 is entirely that prior judge. Nothing here imports `model_stub`.

**Suite 303 → 337 passed. Mutation matrix 13/13 killed.** Committed and pushed.
**STOPPING HERE per §1's exit and the user's instruction — §2 (dry run and ceilings) and §3
(the two extractor arms) are not started.**

## §0 corrections acknowledged as pre-registered

Both of the addendum's corrections are recorded as binding before any §3 data exists:
**(a)** §3 gates the Instrument stratum only; the semantic count is reported, not judged.
**(b)** ADDENDUM-01 §2.5 is superseded by DD-023 ERRATUM 2 — no re-conversion was performed,
the existing Docling output is used, and no quarantine improvement is attributed to the
converter. Any §3 improvement credits the anchor contract, as pre-registered.

## 1. Anchor contract — `kg/extraction/anchors.py` (new)

Model emits `name`, `type`, `anchor` (≤ 10 tokens, shortest *unique* substring). The harness
locates it and **cuts the grounding span from the source text** as the containing sentence.

**The locate-at-birth guarantee is not merely preserved, it is strengthened**: the span in the
graph is document-derived, so it cannot drift from the source by construction. A model-supplied
`grounding_span` is deliberately **discarded** — honouring one would reopen the `span_partial`
drift the contract exists to close, and there is a test asserting exactly that.

`grounding.py`'s normalization is **reused, not forked**, as §1.1 requires. But locating needs
*offsets* and `normalize()` returns a string, so the module rebuilds the same transformation
while tracking each output character to its source index — and then **verifies the rebuild
against `grounding.normalize` itself**. On mismatch it reports `anchor_not_located` rather than
cut a span from coordinates it cannot vouch for. **Failing closed is the design point: a wrong
span is worse than a missing one, because a wrong one still looks grounded.**

Quarantine reason is `anchor_not_located` for every failure (missing / not found / ambiguous /
over-length / unverifiable offsets), with the detail after the colon as diagnosis — the
addendum names one reason and this keeps it one class.

**A real defect the module's own smoke test caught before it shipped:** the newline inside a
hyphenated line break (`read-\nability`) was being read as a sentence boundary, so the derived
span was cut mid-word — `"ability of the file is high."`, a string that genuinely occurs in the
source and is still wrong. De-hyphenation joins that word, so that newline is not a boundary.
Fixed, and pinned by M26.

## 2. Salience — `kg/extraction/prompt_template_v0_3_7.md` (new)

Derived from `chunked_template.md` **by substitution**, the same discipline that file used on
v0.3.5: the schema, the Instrument positive criterion, the semantic-edge relation rule,
`evidence_grade`, `Measure.tier` and the edge whitelist are carried over unchanged. Only the
emission contract moved. Dropped: `concept_inventory`, "the exhaustive Concept layer", "Be
thorough". Added: the anchor contract up front, one `gleaned` pass (names only), and the closed
`diversion_reason` list restated so the prompt and the parser name one vocabulary.

Instrument attributes use the same mechanism per attribute (`attribute_anchors`), so no anchor
⇒ that attribute is null — the v0.3.4 no-background-knowledge rule survives intact.

## 3. Closed list enforced at parse — `kg/extraction/parser.py`

`normalize_diversion_reason` promoted out of `scripts/chunked_pilot.py` into the parser.
Behaviour is unchanged; the enforcement point is not. **A model cannot be bound by an
instruction; it can be bound by a parser** — measured basis: over the first 10 chunks the model
emitted 34 distinct values for this field, mostly whole sentences.

The **raw value is preserved** on the shard as `diversion_reason_raw`: normalization governs
the vocabulary, not a licence to discard what the model said. `chunked_pilot.py` now
re-exports the parser's function rather than keeping a second copy — two copies of a
vocabulary is precisely how the "resolved" definition drifted across three call sites in
today's T0 work, and one test asserts the identity.

## 4. Type reconciliation at merge — `kg/extraction/merge.py` (new)

Rule, mechanical and logged per entity: **instrument evidence wins → majority → `type_conflict`**.

The first rule is asymmetric on purpose, and the reason is worth stating because it is not
symmetric voting: typing something an Instrument *with grounded evidence* is a **positive
observation**, while `Concept` is the default a chunk falls back to when it says nothing more.
Presence of evidence outranks absence of it, so a majority of uninformative views must not
outvote one informative view. An Instrument claim **without** evidence gets no privilege and
falls through to the count (M28).

A tie is **flagged, never broken by ordering** — a coin flip would put an arbitrary type into
the graph and leave no trace it was arbitrary. Conflicted entities are excluded from strata
pooling (`poolable`), because pooling an entity whose type is unresolved puts the conflict into
a gate's denominator. Tested with the observation order reversed, so the outcome cannot depend
on it.

## 5. Profile `v0_3_7` — registered and sha-pinned

`scripts/run_profiles.yaml`. Pins **both** the prompt template and the chunker config: a
chunk-local contract read against a differently-cut chunk is a different experiment, and the
prompt pin alone cannot see that. The extractor model is deliberately **not** pinned — §3 runs
two arms and DD-023 makes the gate indifferent to which model produced the candidates.

**The comparison profiles are retained** (`v1`, `reextract_v035`, `chunked_v035`), per §1.5,
with a test asserting they are still there: deleting the arm you measured against destroys the
measurement.

**A gap found while wiring this:** `apply_profile` enforced the *prompt* pin but would have
accepted `chunker_config_sha256` as decoration. A pin that is declared and never checked reads
like a guarantee and is not one. Generalized into `_verify_pin` and applied to both.

## 6. Mutation matrix — 13/13 killed

| mutation | result |
|---|---|
| M22 model-typed span honoured instead of derived | KILLED |
| M23 ambiguity check removed (first hit wins) | KILLED |
| M24 anchor length bound removed | KILLED |
| M25 fail-closed on unverified offsets removed | KILLED |
| M26 hyphen-linebreak boundary exemption removed | KILLED |
| M27 instrument evidence no longer privileged | KILLED |
| M28 evidence flag ignored (any Instrument claim wins) | KILLED |
| M29 tie broken by ordering instead of flagged | KILLED |
| M30 conflicted entity allowed into pooling | KILLED |
| M31 diversion normalization removed at parse | KILLED |
| M32 raw diversion value discarded | KILLED |
| M33 pin check made permissive | KILLED |
| M34 exhaustive-inventory instruction restored | KILLED |

§1.6 names the M2 failure mode as the specific thing to avoid, so five of these target the
*test* rather than the code: M28 and M29 exist because "instrument evidence wins" and "a tie is
flagged" are each two claims that a single happy-path test would conflate, and M34 rewrites the
banned instruction back into the prompt to prove the salience test reads the rule and not a
word. Three tests were themselves corrected during authoring after they failed for the wrong
reason: one asserted an anchor was ambiguous when the fixture made it unique, one broke on
where the prompt happened to hard-wrap, and one banned the bare phrase "exhaustive list" —
which the new template's own sentence saying an exhaustive list is *not* wanted would have
tripped. That third one is the M2 pattern in miniature: a word, not a rule.

## Discrepancies

**None between the addendum and live state.** `run_profiles.yaml`, `parser.py`,
`grounding.py`, `chunked_template.md` and `chunker_config.yaml` were all as described.

## Not done (the hard stop)

§2 dry run and ceiling declaration; §3 Arm A / Arm B. No `--ceiling-tokens` declared, no
`release-orphans` run — those belong to §2, which begins only on the next instruction.
