# RESULT — the self cycle joins the record: 25 bodies promoted, 486 events, and the licence on five faces

**Task:** `cc_tasks/2026-09-13_self_cycle_promote.md`. **No addendum exists** —
`cc_tasks/2026-09-13_self_cycle_promote_ADDENDUM*.md` globbed before starting and again before
§3, both times `no matches found` (`logs/promote_addendum_glob_start.log`,
`logs/promote_addendum_glob_pre_s3.log`).
**Date:** 2026-09-13 local. The work crossed UTC midnight into 2026-09-14, which is not
bookkeeping: it moved every generated artifact that carries a build date, and it is why decision
4 could not be honoured on its face (§5).
**Spend:** zero model calls. **Network: none.** Nothing in this task contacted a host — the
promotion, the event writes, the projection, the row, the site and the report are all reads of
what was already on disk and in the graph. The only remote operation is the `git push` §4 orders.

## THE GATE: PASS

Every clause of §3 is green and every one of them has a log (§7). The self cycle is on the
append-only log, its bodies are in the committed store, the row says so on every read, and
nothing it measures moved.

## 1. §1 — neither stop condition was met

Checked **before** a byte was written (`logs/promote_s1_stop_checks.log`):

| §1's condition | measured |
|---|---|
| "promotion would write a body whose digest already exists under a different path" | **No.** 34 cited digests; every body already in the store sits at its own content address and nothing in `corpus/evidence/scan/` sits off one. The store is content-addressed on both sides, so "a different path" is not reachable by construction — checked anyway, because a stop condition nobody evaluates is a sentence, not a gate. |
| "`write_events` would emit an event for a Finding not in the payload" | **No.** 135 Findings in the payload, 0 citing evidence the payload does not carry. |

**25 bodies were written, not 34, and that is the first premise correction.** Nine of the 34
cited digests were **already** in the committed store: they are loopback control-fixture bodies
byte-identical to ones earlier cycles promoted, and content addressing means an identical body is
stored once. `promote_evidence` reports the split rather than the total, which is the honest
number — `evidence_promoted: 25`, `evidence_already_committed: 9`, `evidence_cited_digests: 34`.

## 2. Decision 1 — promote, write, project, in the only order `publish.py` permits

`publish.py --from state/self_2026-09-13.json --project`, one invocation, detached and polled
(`logs/promote_publish.log`, `EXIT=0`).

| | |
|---|---|
| bodies promoted into `corpus/evidence/scan/` | **25** (9 already there, 34 cited) |
| staging root | `state/evidence_staging/self_2026-09-13` **removed**, and every `body_path` on the payload rewritten to `corpus/evidence/scan/…` before a line reached the log |
| Observation events | **351** |
| Finding events | **135** |
| shard | `events/batch-029.jsonl` |
| scan layer re-projected | 11,332 Observations, 4,296 Findings, 40 Rules, 17,276 `SUPPORTS`, 7,751 `OBSERVED_ON`, 40 `MEASURES`, **0 rules without an indicator** |
| `observed_on_missing_document` | **0** |

**The event counts are the second premise correction. The task says "6 Findings and 13
Observations"; the shard took 135 and 351.** `write_events` writes the payload, and the payload
is 6 cycle Findings **plus 129 control Findings**, 13 cycle Observations **plus 338 control
Observations**. 6 and 13 are what the *row* prints. Publishing the controls with the cycle is
what every prior cycle did and it is the thing that makes the control gate re-derivable from the
log rather than only from `state/`: DD-019 says a cycle with zero fired controls is invalid, and
a control Finding whose Observations were never published is an orphan by construction — which is
exactly the 120 the 2026-09-06 scaffold had to annotate instead of publish.

**The events landed on the shared shard, not one of their own.** `publish.CYCLE_BATCH` names a
shard per cycle for the cycles that have one and falls back to `SCAN_BATCH` (29) for the rest;
adding an entry is an edit to `publish.py`, which is harness runtime and on this task's zero-edits
list. Batch 029 already holds four cycles' events under four `params_hash`es, so this is the
default behaviour and not a collision — the refusal in `batch_for` fires only for a cycle that
DOES name a shard. Recorded rather than worked around.

**One number in that output is not this cycle's, and it would be misread.**
`findings_evidence_unretained: 120` is the graph's total, not the self cycle's: `main()` merges
three dicts and `project()`'s keys overwrite `write_events()`'s where they share a name
(`observations`, `findings`, `findings_evidence_unretained`). **This cycle's own unretained count
is 0** — measured directly: of 135 self Findings, 0 are in the annotated set and 0 are orphans
(§3). `state/promote_self_cycle_2026-09-13.json` carries that caveat on its face.

## 3. Decision 2 — `PRIOR_CYCLES`, the census, and the number the gate actually counts

`self_2026-09-13` is in the standing re-derivation set (`tests/test_scan_harness_v4.py`), **at
135, not 6** — the third premise correction. That gate's number is `len(findings_detail) +
len(control_findings_detail)` for every entry in the table, which is how `scan_2026-09-09` is 731
rather than 634. Six is the row.

**It is the first entry whose parameters are not a commit of `params.yaml`, and `_params_for` now
says so rather than failing.** The self cycle ran under the committed base with its cycle identity
overlaid in memory, so a lookup by `params_hash` finds nothing in git and the gate would have
failed with "the parameters this cycle was measured under are not recoverable" — true of the
lookup, false of the cycle. `_params_for` recovers the base by `base_params_hash`, re-applies the
recorded `params_overlay`, and **refuses unless the result hashes to what every Observation and
Finding of the cycle carries**. The same discipline, one step longer; nothing is reconstructed by
hand. **17 of 17 payloads re-derive byte-identically** (was 16).

**The retention census, before and after** (`logs/promote_census_{before,after}.log`):

| | before | after |
|---|---|---|
| orphan Findings on the log | 120 | **120** |
| …of them the self cycle's | 0 | **0** |
| self-cycle digests cited on the log | 9 | **34** |
| uncited tracked bodies | 411 | 411 |
| `uncited_now + newly_cited == uncited_before` | holds | **holds** |
| `tracked == before + promoted` | holds | **holds** |

`self_cycle_digests_tracked_in_the_store` reads **9** after, and that is `git ls-files` answering
about a working tree where the 25 promoted bodies are not yet committed — the census counts the
TRACKED set on purpose, because an untracked body is this session's litter and not part of the
retained set. The commit §4 orders is what makes it 34, and the census is recomputed by the
standing test on every later run.

## 4. Decisions 3 and 4 — the licence reaches five faces; the sitemap moved and robots.txt did not

**The licence, deferred by three consecutive RESULTs, is on every published face.** Read from
`publication.yaml` in every case; not one SPDX identifier is typed into a consumer.

| face | how |
|---|---|
| `docs/llms.txt` | a generated `## Licence` section — code `MIT`, data/report/artefacts `CC-BY-4.0`, each linking its text, plus the corpus-exclusion sentence. On the MACHINE-readable face on purpose: it is the file the A5 discovery probe looks for. |
| the report (`.md`) and **the PDF** | one sentence in the generated version block, on the title page: the faces a reader meets first, and the two that stated no licence at all. `load_publication` now REQUIRES the three licence keys, so a build that lost them stops rather than shipping silence. |
| `docs/index.html` | already had it (previous task) |
| `CITATION.cff` / `.zenodo.json` (+ published copies) | already had it |

`tests/test_publication.py::test_both_spdx_identifiers_reach_every_generated_consumer` went from
three consumers to **five**, and the corpus-exclusion test with it;
`tests/test_report_pdf.py::test_the_pdf_states_both_licences` asserts both identifiers survive the
pandoc/typst conversion, which is the one step between the declaration and the artifact that
nothing else watches. Neither test can pass vacuously: the report is a published build product, so
its absence is an assertion failure and not a skip.

**PDF gates green and the page counts did not move:** `{"total": 14, "prose": 6}`, identical to
the registered `l0_report_pages_total_2026-09-11 = 14` and `l0_report_pages_prose_2026-09-11 = 6`,
so **nothing was re-registered** — the task's "unmoved or re-registered" resolved to unmoved.
`bare_numerals_in_prose: []`, `unresolved_tokens: []`, numeral-multiset gate PASS, 3 PDF tests
green (`logs/promote_report_pdf.log`).

**Decision 4 could not be honoured on its face, and this is the fourth premise correction.**
`docs/robots.txt` **is** byte-identical. `docs/sitemap.xml` is **not**: every one of its 18
`<lastmod>` values is the build date, the build ran at 00:38 UTC on 2026-09-14, and the files it
dates — `llms.txt`, `index.html`, the report — really did change then. Restoring yesterday's
sitemap would have published a document that dates today's files to yesterday, which is the class
of false statement this instrument exists to detect. So it moved, and it moved in its `lastmod`
dates **and nothing else**, asserted by
`scripts/check_protected_self_cycle_promote.sh` rather than asserted in prose.

**Nothing any leg reads changed in substance.** A4, A5, A11-declared and A12 read the AUTHORITY
root (`https://brockwebb.github.io/…`), all 404, and never read the tree's files at all — that is
the finding the row exists to report. A10 and G1-D read the index, whose only change is its build
stamp; the row's own HTML is byte-identical, because the index does not print
`body_in_committed_store` (that lives on `state/self_l0_self_2026-09-13.json`). The verdicts were
measured before any of this and none of them moved.

## 5. Decision 1's diff — the row, before and after

`logs/promote_row_diff.log`. The row carries **13 reads**, not 34 — the 34 are the cycle's bodies
*and the control fixtures'*; the row cites only the six legs' own Observations.

| | |
|---|---|
| `body_in_committed_store: false` before | **13 of 13** |
| after | **0 of 13** — all flipped to `true` |
| every other difference | **`generated_at` alone**, `2026-09-13T17:49:21Z → 2026-09-14T00:37:58Z` |
| verdicts / reasons / URLs / statuses / `finding_id`s | **identical, all six legs** |

1 pass, 5 fail, unchanged: A10 `pass`, A4 / A5 / A11-declared / A12 / G1-D `fail`. The six
`self_l0_*` Results were re-registered idempotently — **0 registered, 6 already at this value, 0
failed** — so `seldon_events.jsonl` gained nothing from this step.

**Provenance resolves into `corpus/`, through the chain and not on the Result node** — the fifth
premise correction, and it matters for what a reader should check. Each Result is
`COMPUTED_FROM` the row's DataFile (`state/self_l0_self_2026-09-13.json`); the row names each
leg's `finding_id` and every `obs_id` under it; those Observations are on the log and **259 of
259 bodied Observations of this cycle carry a `raw_ref` under `corpus/evidence/scan/`** in the
graph, with 0 Findings unsupported (`logs/promote_verify.log`).

## 6. What publishing the self cycle changed that nothing predicted

**`docs/data/sources_per_check.json` moved in exactly three numbers** — the per-check `rules`
count for *Access policy coherence* 1→2, *Bulk access* 4→5, *Methodology legibility* 2→3 — and the
cause is worth recording rather than filing as noise:

**`RULE-A12-v2`, `RULE-A3-v6` and `RULE-B3-v3` reached the event log for the first time with this
cycle.** Measured: of every `finding_derived` event on the log, 9, 8 and 8 respectively carry those
rule ids, and **all of them are this cycle's**. Every earlier payload judged under generation 8 and
9 is a **re-judgement**, and no re-judged payload has ever been published to the event log. So the
projection minted three more `Rule` nodes with their `MEASURES` edges, and the appendix counts
rules per check.

That is a true consequence of a correct publication, and it is also a question: **the graph's
Findings are the measured cycles plus, now, one self cycle — the twelve re-judged payloads are on
disk and in `state/`, not on the log.** Whether that is the intended boundary or an omission is not
this task's to decide, and it is §9 item 1.

No row, no source, no locator and no `doc_id` in the appendix moved; the report's own text moved
only in its generated version block. Both are asserted by the protected-paths script, not by
reading the diff once.

## 7. The gate (§3), clause by clause, with the log that carries each

| clause | result | log |
|---|---|---|
| addendum glob, before starting and before §3 | **none exists**, both times | `logs/promote_addendum_glob_start.log`, `logs/promote_addendum_glob_pre_s3.log` |
| §1's two stop conditions | **neither met** | `logs/promote_s1_stop_checks.log` |
| bodies promoted, content-addressed, digests matching the payload | **PASS** — 25 written, 9 already held, 34 cited, 0 missing anywhere | `logs/promote_publish.log`, `logs/promote_verify.log` |
| events written for the payload's Findings and Observations | **PASS** — 135 Findings, 351 Observations, `events/batch-029.jsonl` | `logs/promote_publish.log` |
| scan layer re-projected; the six Results' provenance resolves into `corpus/` | **PASS** — 351/135 of this cycle in the graph; 259 of 259 bodied Observations `raw_ref` under `corpus/evidence/scan/`; 0 unsupported Findings | `logs/promote_verify.log` |
| `PRIOR_CYCLES` carries the self cycle | **PASS** — at 135; **17 of 17 payloads re-derive byte-identically**, 6.81 s | `logs/promote_gate_task.log` |
| retention census shows 0 unretained on it | **PASS** — orphans 120 → 120, 0 of them the self cycle's; both decomposition identities hold | `logs/promote_census_before.log`, `logs/promote_census_after.log` |
| both invariant readings 0 | **PASS** — `observed_on_missing_document` 0 on the row AND 0 across the whole projection; `findings_evidence_unretained` 0 on this cycle | `logs/promote_row_regen.log`, `logs/promote_publish.log` |
| the self payload re-derives byte-identically | **PASS** — under base-from-git + recorded overlay | `logs/promote_gate_task.log` |
| the row regenerated with `body_in_committed_store: true` and no other field changed | **PASS** — 13 of 13 flipped; only `generated_at` besides | `logs/promote_row_diff.log` |
| licence test green on all five faces | **PASS** — `llms.txt`, the report, `index.html`, `CITATION.cff`, `.zenodo.json`; plus the PDF's text layer | `logs/promote_gate_task.log`, `logs/promote_report_pdf.log` |
| PDF gates green; page counts unmoved | **PASS** — 14 total / 6 prose, unmoved, nothing re-registered; numeral multiset, bare-numeral lint and reference resolution all clean | `logs/promote_report_pdf.log` |
| `make gate-task` | **PASS** — **2,032 passed, 17 skipped, 20 deselected, 12 xfailed, 384.40 s**; then 17 of 17 payloads re-derive, 6.81 s | `logs/promote_gate_task.log` |
| `make guards` | **PASS** — 25 passed, 16.21 s | `logs/promote_guards.log` |
| `make gate-full` (detached, logged, polled to EXIT) | **PASS** — **2,052 passed, 17 skipped, 12 xfailed, 1,353.97 s (22:33)** | `logs/suite.log` |
| `seldon verify` | **PASS** — all checks passed, 34,636 events readable | `logs/promote_verify_seldon.log` |
| protected paths | **PASS** | `logs/promote_protected.log` |

Every log carries its own `EXIT=0` and all of them were written before this file was. The two
tiers differ by 20 tests: the slow-marked control fixtures and the re-derivations outside the
two-most-recent window, which now include this cycle's.

## 8. What changed

**New:** `scripts/check_protected_self_cycle_promote.sh`,
`state/promote_self_cycle_2026-09-13.json`, 25 bodies under `corpus/evidence/scan/`.
**Modified:** `scripts/build_l0_site.py` (the `llms.txt` licence section),
`scripts/build_l0_report.py` (the version block's licence sentence; the licence keys are
required), `tests/test_publication.py` (three → five consumers, both licence tests),
`tests/test_report_pdf.py` (+1: the PDF states both licences),
`tests/test_scan_harness_v4.py` (`PRIOR_CYCLES` + the overlay in `_params_for`),
`events/batch-029.jsonl` (+486 lines), `state/self_2026-09-13.json` (body paths rewritten into
`corpus/`), `state/self_l0_self_2026-09-13.json` (regenerated), `docs/llms.txt`,
`docs/index.html`, `docs/sitemap.xml` (lastmod only), `docs/data/{index,sources_per_check}.json`,
`docs/data/{CITATION.cff,zenodo.json}` + the root copies (release date only),
`docs/reports/2026-09_fss_ai_readiness_L0.{md,pdf}`.
**Zero edits** to rule modules, harness runtime (`publish.py` included), manners, prior payloads,
prior Results' values and states, prior RESULTs, figures, section prose, the skeleton, the
framework record, `kg/`, `corpus/manifest.json`, `docs/robots.txt`, every published matrix, and
both licence texts. `corpus/` was only ADDED to; `events/` only grew; `seldon_events.jsonl` gained
nothing from this task.

## 9. What the next task should pick up

1. **The twelve re-judged payloads are not on the event log** (§6). The self cycle is the first
   payload published under generations 8 and 9, which means the graph's Findings are the measured
   cycles and this one — the judgements the published report is a view of (`scan_2026-09-10_rj2`)
   are in `state/` and nowhere on the append-only log. Whether that is the intended boundary
   (a re-judgement creates no evidence, so publishing it publishes judgements citing another
   cycle's `obs_id`s — which `publish.write_events` explicitly permits) or an omission is a real
   question about what the log is for, and it is the first thing to settle.
2. **`RULE-A12-v2`'s reason string**, still open and now the next task in the chain
   (`cc_tasks/2026-09-13_rule_a12_v3.md`).
3. **The host** (`2026-09-13_self_row_RESULT.md` §10 item 3). Four of the six fails are about an
   authority this publication does not own. A custom domain or the user-site repository is the
   only thing that changes them, it is a value input, and the row is honest until then.
4. **The sitemap's `lastmod` is the build date, not the file's** (§4). Every URL in it re-dates on
   every build whether or not that file changed, which makes it a build stamp wearing a
   content-modification field. Per-file `lastmod` from the tree would be truer and would stop this
   file moving on every rebuild.
