# RESULT: node-key fusion audit (`cc_tasks/2026-10-04_node_key_fusion_audit.md`)

**Status:** audit complete; nothing on the log, graph or record changed. **Gate RED on the same five regenerate-and-compare guards that are red at HEAD without this task's files** (§6). The audit's own tests, `--check`, `seldon verify` and the protected-paths diff are green. No addendum exists. Audit: `docs/research/2026-10-04_node_key_fusion_audit.md` (+ `.csv`, 4,661 rows); script `scripts/audit_node_key_fusion.py`.

## 1. Totals (G2), by (label, key): the unit the projection's MERGE fuses on
| label | fused nodes | benign_duplicate | same_term_lost_evidence | collision | distinct spans lost |
|---|---|---|---|---|---|
| Definition | 162 of 2,064 | 16 | 90 | 132 | 222 |
| Claim | 331 of 6,906 | 22 | 5 | 861 | 865 |
| Concept | 1,395 | 77 | 1,373 | 1,283 | 2,655 |
| all 10 labels | 2,396 of 26,035 | 147 | 1,811 | 2,703 | 4,511 on 2,283 nodes |

Origin: 4,182 pairs from another chunk of the survivor's run, 479 from another run, 0 from the same chunk. Every survivor is in `bulk_v038` (62 documents) or v1 `batch-004` (3); 63 documents in all. 3,322 of 38,485 projectable edge events attach to an endpoint a different item took over, and 209 relocation overlays were written against an overwritten assertion. **Controls:** replay counts equal live Neo4j for all ten labels; all 2,312 fused non-Instrument nodes match on span and identity; Q1 19/11, Q2, Q4 29, glossary 48, 2,064 and 1,975 all reproduce.

## 2. Collisions
2,703 in the CSV (`class == collision`, both identity texts in full). The 132 Definition collisions are listed in full in audit G9. The class is an **upper bound** on wrong nodes: 331 are narrower or wider names for one item, and spelling variants such as `Relevance`/`relevant` also land in it (audit §5). 2,180 sit on positional ids (`d1`, `cl4`).

## 3. Impact on cited figures (audit §3, G6): current → (a) chunk-qualified / (b) first-wins
- Definitions: 1,975 → 2,180 / 1,975; the current 2,064 → 2,281 (+10.5%) / 2,064 (which item survives changes on 162 nodes).
- **Q1 19 → 20 / 20**: `data-readiness-for-ai-a-360-degree-survey::d1` is today "data model"; the overwritten "Data readiness for artificial intelligence (AI)" is missing from Q1. Of Q1's 19 rows, 17 are unfused, 1 benign, 1 same-term.
- Q2: all ten tallies unchanged; `naming_none` 13 → 14. Q3 and definition pairs: no judged node is a collision; the new definition's pairs were never judged.
- **Q4 29 → 31 / 31**: AIDRIN's survivor name is the bare acronym, so the readiness regex misses it. Instrument nodes 502 → 669 / 502.
- Commerce 48/49 → 48 / **38**. No `CL-` entry counts KG extraction nodes or edges; CL-085's locator is unfused.

## 4. Recommended fix
(a): standardize apart (`<doc>::<chunk>::<id>`, only for the 2,283 groups with more than one distinct span), resolve edge endpoints within the asserting chunk (edge events already carry `chunk_id`), and leave uniting same-term nodes to an explicit within-document merge. That merge already exists as the chunked pilot's `merge.normalized_key` rule and never reached the projection. (b) only changes which item is lost (glossary 48 → 38), and the fix task must first decide run-scoped supersession for the 31 multi-run documents, because `extraction_superseded` keys on `(doc, sha)`.

## 5. Reader gate (fresh subagent, audit markdown only; final run, verbatim)
> The defect fuses 2,396 of 26,035 knowledge-graph nodes (9.2%), and 2,283 of those (8.8%) lost at least one grounding span, so 4,511 distinct spans are no longer on the graph; of the 4,661 overwritten pairs, 2,703 are classed as collisions (one id carrying two different items), and 3,322 of 38,485 projectable edges (including 130 `defines` and 853 `asserts`) were asserted in a chunk whose endpoint was overwritten by a different item, while 209 `grounding_relocated` overlays put an earlier item's span onto the survivor. It touches these cited figures: the Definition count (1,975 becomes 2,180 and 2,064 becomes 2,281 under chunk-qualified keys), the Instrument count of 502 (becomes 669), Q1's "19 definitions from 11 documents" (becomes 20 under either fix), Q4's 29 readiness-named Instruments (becomes 31), and the Commerce two-pipelines 48/49 (unchanged under fix (a) but 38 under fix (b)). Per the file, it leaves these alone: the ten Q2 construct tallies (only `naming_none` goes from 13 to 14), the Q3 conflict edges (12, 5 cross-document) and the 151-of-158 `definition_pairs` judgments, the quoted spans of Q1's 19 rows (17 are unfused, one has a benign duplicate, one lost a second span of the same term), and every `CL-` entry in `claims.yaml`, since none counts KG extraction nodes and CL-085's locator is not fused. I would not trust 2,064 as a count of the definitions in the corpus: it is a count of surviving `(label, key)` nodes under last-wins, it hides up to 222 lost Definition items (and up to 132 Definition nodes may show one item's term after another item's evidence was overwritten), and the file itself says 31 documents carry nodes from two or three extraction runs, so neither 2,064 nor the fix-(a) figure of 2,281 is free of cross-run duplicates and run-scoped supersession is still unresolved. What I found unclear or internally inconsistent is this: §5 calls 2,703 an upper bound on wrong nodes, yet §2 heads with "collisions are the majority" (2,703 minus the 331 containment cases is 2,372, barely above half of 4,661, and paraphrases or spelling variants could push it under) and says the 3,322 edges "each" attach to the wrong node, a count built on that same upper bound; "every KG node count" is said not to move under (b) while Q1, Q4 and Commerce derived figures do move under (b), and "the 222 lost definitions stay lost" under (b) is inexact because first-wins changes which items are lost; the survivor runs are given as 62 + 3 documents but G8 lists 63 documents, with no statement of the two-document overlap; and the RDF section citations and the GraphRAG paper are cited from memory, not retrieved, so the prior-art grounding for the recommended fix is unchecked.

Every point in the fifth sentence was then fixed in the audit's prose, which is outside the generated block (`--check` still no drift). The first reader-gate run found a real script defect: whole-document runs share an empty chunk id, so cross-run overwrites read as `same_chunk`. That run also flagged the unrecomputed 1,975. Both were fixed before this run.

## 6. Gate (logs in `logs/`)
- `make gate-fast`: **5 failed, 2903 passed, 3 skipped, 27 deselected, 12 xfailed**, 703.12 s, EXIT=2 (`node_key_fusion_gate_fast.log`). `make gate-full`: **5 failed, 2930 passed, 3 skipped, 0 deselected, 12 xfailed**, 2388.30 s, EXIT=1 (`node_key_fusion_gate_full.log`).
- The five: `test_brief_deck:63`, `test_brief_pack:63,74`, `test_g4_resourcing_reissue:234`, `test_publication:106`. These are views embedding the corpus manifest, which the Commerce admission left stale and declared byte-identical; its RESULT §6 named their follow-on. The same five fail in a clean HEAD worktree without this task's files (`node_key_fusion_head_red_guards.log`; its extra failures there come from gitignored PDFs missing in a worktree). Not regenerated: they are outside this write set.
- Audit tests: **4 passed, 0 skipped, 0 deselected, 0 xfailed**, EXIT=0 (`node_key_fusion_audit_tests.log`). `--check`: no drift, EXIT=0 (`node_key_fusion_check.log`). `seldon verify`: all checks passed, EXIT=0 (`node_key_fusion_seldon_verify.log`). Protected paths: only the five write-set files moved; `events/`, `kg/`, `docs/evidence/`, `docs/brief/` and `framework/` are untouched; PASS, EXIT=0 (`node_key_fusion_protected.log`, run inline rather than as a new script, to stay inside the write set).

## 7. Premises wrong
1. "Framework layer §2.3, extraction integrity": DN-005 §2.3 is *Prescription*. Extraction integrity belongs to the validity layer (DN-005 §1), which feeds §2.1.
2. "the 1,975 Definitions": that is the pre-Commerce epoch (`kg_research_questions_RESULT` §1). The record reads 2,064; both are bounded.
3. The source RESULT's 4,070 / 1,966 / 64 / 815 / 184 came from an uncommitted query and does not reproduce. For `bulk_v038` survivors this audit finds 4,469 pairs / 2,238 nodes / 62 documents / 863 Claim / 218 Definition.
4. "Group by key": the projection fuses on (label, key). 83 keys carry two labels and are two nodes, not fusion.
5. "Any `CL-` entry that counts nodes or edges": none counts KG extraction nodes.
6. Unanticipated by the task: the fusion is also cross-run (31 documents), and the chunked pilot's surface-form merge rule (2026-08-27 §4) never reached the projection.
7. "List those in full": 2,703 collisions are too many for the markdown (550 KB), so the full list is in the CSV and the markdown lists the 132 Definitions. `--check` covers the CSV and the generated block; the prose around the block is hand-written.

## 8. Tokens and model
Session model `claude-opus-5-5`. Harness counter: about 216K tokens of this session's context consumed. Two reader-gate subagents: 69,170 and 70,420 tokens. No `claude -p` call and no spend-ledger reservation. The declared estimate was 3M.
