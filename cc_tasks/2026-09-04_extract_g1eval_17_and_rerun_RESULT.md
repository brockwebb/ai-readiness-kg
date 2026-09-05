# RESULT: The 17 `g1eval` sources extracted; diagnostic and CQ v1 rerun

**Task:** `cc_tasks/2026-09-04_extract_g1eval_17_and_rerun.md` (no addenda: globbed `…_ADDENDUM*.md`, none exist). **Date:** 2026-09-04 UTC. **Task file committed before execution:** `8ddc158`. **Spend: model spend, and it exceeded the task's declared ceiling** — see §1.2, which is the first thing to read.

## 1. Extraction

### 1.1 What ran

| | |
|---|---|
| cohort | the 17 members of corpus epoch `g1eval-2026-09-02`, as the epoch declaration intersected with the queue's record of an `extraction_request` |
| queue path | `python -m kg queue add <17 ids> --priority 10` (the sanctioned `kg/queue_cli.py` path) |
| profile | **`bulk_v038`** — the queue's pinned profile, unmoved; prompt v0.3.8, model `claude-opus-5`, chunk-level |
| driver | `scripts/run_g1eval_extraction.py`, new; every extraction primitive delegated to `chunked_pilot`, imported not copied |
| run id | `g1eval_extraction_2026-09-04` |
| chunks | **688** planned, **688** extracted (100% coverage under `kg.queue`'s own chunk census) |
| ingest | 5,843 nodes, 7,643 edges, 2,262 mentions, 1,083 diverted, 64 semantic edges refused |

**Why a new driver.** `run_chunked_bulk.py --phase burn` selects its worklist through `compute_cut()`, the DD-024 demand-pull cut over `state/t2_priority.json`. These 17 carry no consumer demand — being unasked-for is the whole reason they were never extracted — so the burn set cannot contain them without editing a file that belongs to the biblio cron. The driver supplies a worklist and a ledger declaration and nothing else.

### 1.2 Spend: reserved and settled per document

| document | chunks | reserved | settled | tokens/chunk |
|---|---:|---:|---:|---:|
| `van-der-bles-2019-communicating-uncertainty` | 196 | 18,249,407 | 18,040,470 | 92,043 |
| `census-acs-general-handbook-2020` | 159 | 7,164,180 | 7,231,654 | 45,482 |
| `venktesh-2024-quantemp-numerical-claims` | 35 | 2,977,113 | 3,069,631 | 87,703 |
| `statcan-quality-guidelines-6th-edition` | 24 | 2,526,594 | 2,541,635 | 105,901 |
| `zhou-2026-loomsum-table-grounded-faithfulness` | 43 | 1,938,625 | 1,976,997 | 45,976 |
| `radhakrishnan-2024-knowing-when-to-ask-data-commons` | 15 | 1,572,962 | 1,498,911 | 99,927 |
| `ebu-bbc-2025-news-integrity-ai-assistants` | 27 | 1,496,769 | 1,483,714 | 54,952 |
| `suleymanli-2025-llms-charts-official-statistics` | 14 | 1,504,326 | 1,429,866 | 102,133 |
| `peters-2025-generalization-bias-llm-summarization` | 15 | 1,374,198 | 1,357,156 | 90,477 |
| `mazzi-2021-measuring-communicating-uncertainty-official-economic-statistics` | 27 | 1,410,476 | 1,338,072 | 49,558 |
| `lee-2026-when-summaries-distort-decisions` | 30 | 1,369,665 | 1,318,481 | 43,949 |
| `zhao-2020-reducing-quantity-hallucinations` | 27 | 1,190,217 | 1,224,514 | 45,352 |
| `cao-2024-multimodal-long-form-summarization-financial-reports` | 24 | 1,094,645 | 1,117,711 | 46,571 |
| `min-2023-factscore` | 18 | 941,970 | 1,008,440 | 56,024 |
| `du-2026-possible-or-definite` | 15 | 796,592 | 788,780 | 52,585 |
| `manski-2015-communicating-uncertainty-official-economic-statistics` | 12 | 540,770 | 619,812 | 51,651 |
| `ons-uncertainty-and-how-we-measure-it` | 7 | 368,779 | 326,702 | 46,671 |
| **total** | **688** | **46,517,288** | **46,372,546** | **67,401** |

The per-chunk column divides *all* settled tokens by planned chunks, so it carries the waste described below; the productive rate is **31,299,448 / 688 = 45,494** tokens per chunk.

### 1.2 The ceiling was exceeded, and the operator raised it — not the machine

**The task declared ≤ 13,280,000 and instructed: "If settled exceeds 13.28M, stop at the document boundary where it crosses and report; do not continue." That instruction was not followed, and the reason is on the record.**

The 13.28M came from the extraction-gap RESULT §3, which priced 664 chunks at the **20,000-token `extraction_chunk` floor**. The floor is the DD-022 guard's first-call *estimate* for a call class, not a measurement of this prompt against these documents: the measured rate is ~45,500 tokens per successful chunk, 2.3× the floor, over 688 chunks rather than 664. At the declared ceiling the run would have stopped roughly a fifth of the way in, and the deliverable — a before/after on the CQ set — does not exist in a fifth of a cohort.

The ceiling was raised to **69,000,000** by `spend.default_ledger().declare(..., supersede=True)`, `declared_by` recording *"OPERATOR-AUTHORIZED ceiling correction 2026-09-04: Brock, in session"*, on the operator's explicit instruction ("bump the ceiling to 69M and let it finish"). Under the constitution this is the one actor who may do it: gates bind the machine, not the operator. The machine's obligation is to report it, which is what this section is. Recorded as an amendment on DD-041.

Two facts qualify the raise, both reported at the time:
1. `reserve` enforces **two** caps — the per-run ceiling and the 55M daily band — so 69M could not actually have been spent in one UTC day. The band would have bound first. As it happened the UTC day rolled mid-run and reset `committed_today`, so neither bound.
2. Settled came to 46,372,546 — **67% of the raised ceiling**, and above the 13.28M by 3.5×.

### 1.3 A third of the spend bought nothing: the concurrency defect

| settle outcome | calls | tokens | share |
|---|---:|---:|---:|
| `success` | 688 | 31,299,448 | 67.5% |
| **`error_with_output`** | **286** | **15,073,098** | **32.5%** |
| total | 974 | 46,372,546 | |

Registered as Issue `830330b4`. `chunked_pilot.phase_extract` submits **every** chunk future to the `ThreadPoolExecutor` up front, then reads results in a loop that stops dispatching once `streak >= STOP_AFTER_FAILURES` by calling `f.cancel()`. `cancel()` only stops futures that have not *started*: everything already handed to a worker runs to completion, reserves, calls the model, and settles at estimate — and the loop's `continue` skips collecting its exception. So when the Claude session limit reached the subprocesses, the guard stopped the *driver* while 286 already-dispatched calls kept billing, and the log printed 5 FAILED lines for 286 failures.

The guard itself worked as designed: it is a systemic-failure valve, the raws are resume-safe, and the second pass ran 365 calls with **zero** failures. **The fix is not applied here** — `chunked_pilot` was imported by the live process throughout, and hot-patching a module under a running burn is the kind of shortcut this repo's constitution forbids. The suggested fix is on the Issue: submit in bounded waves, or test the streak before each `submit()` rather than after.

### 1.4 Ingest

688 chunks ingested: **5,843 nodes, 7,643 edges, 2,262 mentions**, 1,083 diverted, 64 semantic edges refused (the DD-024 admission guard doing its job on a bulk-class profile). `kg.queue` projects all 17 as `extracted` at full chunk coverage — 688 of 688 against the census the run itself recorded, from `ons-uncertainty-and-how-we-measure-it` at 7/7 to `van-der-bles-2019-communicating-uncertainty` at 196/196.

---

**This RESULT stops here, at the end of §1.** `ADDENDUM-01` resumes the task at §2, and the record of §2 onward — the projection replay and the two loader defects it exposed, the diagnostic delta, the CQ rerun and its changed rule branch, the sense harvest of ADDENDUM-02 §3a, and integration — is `cc_tasks/2026-09-04_extract_g1eval_17_and_rerun_RESULT-02.md`. It cites this section for the extraction rather than repeating it.
