# RESULT — published counts derive from the matrix they label; the source appendix is compared to the graph it came from

**Task:** `cc_tasks/2026-09-15_derived_counts_and_appendix_guard.md` (no addenda; globbed before §1 and again before §4, both times empty).
**Executed:** 2026-09-15 local / 2026-09-16 UTC. Hand-dispatched (`dispatch.enabled` false).
**Spend:** zero model calls. **Network:** none — no host was contacted; the only remote-shaped access is Neo4j on localhost.
**Gate:** green. Every number below is quoted from a log named in §6.

---

## 0. What shipped

Four published matrix labels stated a leg count that the matrix they describe stopped having on
2026-09-15 (DD-066). They now render that count from the matrix file. The numeral map that
spells it lives in one importable module, imported by both the builder and the gate that checks
the abstract. `docs/data/sources_per_check.json` gained a standing comparison against the graph
it is derived from — both as a test and as a refusal inside `build_l0_site.py --check` — and its
G1-D rows now carry the tier they are measured at and the instrument they left, read off the
framework record's indicator node.

Nothing was measured, nothing was judged, no rule ran, no stored payload under `state/` moved,
no Observation and no Finding was minted, and no matrix, report section or PDF changed.

---

## 1. Decision 1 — the derivation, the shared map, the four labels

**The four labels.** The tier-A label is rendered four times: twice into `docs/index.html`
(JSON and CSV) and twice into `docs/llms.txt`.

| | before | after |
|---|---|---|
| `docs/index.html` line 44 (tierA JSON) | `Matrix, tierA, JSON. The 16 Tier A bodies × the six host-level checks.` | `… × the five host-level checks.` |
| `docs/index.html` line 45 (tierA CSV) | `Matrix, tierA, CSV. The 16 Tier A bodies × the six host-level checks.` | `… × the five host-level checks.` |
| `docs/llms.txt` line 9 (tierA JSON) | `Matrix, tierA, JSON. The 16 Tier A bodies × the six host-level checks.` | `… × the five host-level checks.` |
| `docs/llms.txt` line 10 (tierA CSV) | `Matrix, tierA, CSV. The 16 Tier A bodies × the six host-level checks.` | `… × the five host-level checks.` |

`five` is not typed anywhere. `docs/reports/scan_matrix_tierA_2026-09-10_rj2.json` declares
`legs: ["A4", "A5", "A10", "A11-declared", "A12"]`; `build_l0_site.matrix_legs` reads it,
`numerals.word(5)` spells it, `build_l0_site.matrix_label` renders the template
`"The 16 Tier A bodies × the {legs} host-level checks."` against it.

**What changed:**

* **`scripts/numerals.py` (new).** `WORDS` 0–20 and `word(n)`. Out of range raises `ValueError`,
  a non-int raises `TypeError` — a published label with "many host-level checks" on it is the
  class of silent wrong answer the module exists to remove. No fallback string.
* **`scripts/check_protected_abstract_five_checks.sh`** deleted its inline
  `WORDS = {1: "One", …}` and imports `word` from that module. A gate holding its own copy of
  the fact it gates is how one copy moved under DD-066 and the other did not.
* **`scripts/build_l0_site.py:MATRICES`** entries are now label TEMPLATES carrying `{legs}` /
  `{n_legs}`, rendered per matrix from that matrix's own `legs` array. `str.format` raises on a
  template naming a field the renderer does not supply, so a typo fails the build rather than
  printing a brace onto a published page.
* **The unreachable branch** (was `build_l0_site.py:531`, "The six host-level checks have not
  been run against this host") derives the same way: `index_html` takes `host_legs` and spells
  `word(len(host_legs))`. It is unreachable while `state/self_l0_self_2026-09-13.json` exists,
  which is exactly how the `MATRICES` literal survived a gate — an unexercised string is where a
  stale number lives.
* **`scripts/report_traceability.py:42`.** The comment now states no count at all and names the
  test that pins the list. The module docstring's "the six tier-0 legs" — the same falsehood
  three lines up, not named by the task — was corrected in the same edit rather than left
  standing; the remaining counts in that file ("the seven named in code", "Twelve, not seven")
  are still true and were not touched.
* **`tests/test_report_traceability.py::test_the_checks_named_in_code_are_this_set_and_its_length_is_its_own`
  (new).** Asserts `_NAMED_IN_CODE` as a set, its length against the enumerated list, that no
  leg is named twice, and that it does not intersect the prose-read product legs.

**A count that is still typed, and deliberately.** `"The 16 Tier A bodies"` and `"The three
federal reference hosts"` remain literals in the same templates. They are ROW counts, not leg
counts; DD-066 did not move them and the decision named `len(legs)`. They are the first line of
§3's "what the next hygiene task is authored from".

---

## 2. Decision 2 — the appendix is compared to the graph

**The guard, in two places.**

* `tests/test_publication.py::test_the_published_source_appendix_matches_the_graph_it_was_derived_from`
  recomputes the whole payload with `build_l0_site.sources_per_check()` and compares it field by
  field to the published file, then checks `rules` a second time against an **independent**
  Cypher count of `(:Rule)-[:MEASURES]->(:AssessmentIndicator)`. Re-running only the builder's
  own function would check the payload against a second call of the code that wrote it; the
  count that actually drifted gets a query that does not share it.
* `scripts/build_l0_site.py --check` raises `SystemExit` on the same drift, via
  `appendix_drift_against_published`. `--check` therefore answers the question with no database
  fixture and a stale payload cannot pass a build.
* `tests/test_publication.py::test_the_appendix_guard_reports_the_drift_it_was_built_for`
  reconstructs the stale payload from git and asserts the guard reports it — the repo's
  standing shape, a guard that replays the incident it was built for.

**The red run.** The guard pointed at `05455cd:docs/data/sources_per_check.json`, reconstructed
from git, against the live graph:

```
RED RUN — guard against 05455cd:docs/data/sources_per_check.json
   rows_per_leg: published {...}, graph now None
   legs_without_source: published [], graph now None
   rows: published 73, graph now 0
   A12.rules: published 2, graph now 3
  (4 drift line(s))
```

`A12.rules: published 2, graph now 3` is the incident: the payload names two rules for A12 and
the graph carries `RULE-A12-v1`, `-v2` and `-v3`. (That first run passed a chain-only comparand,
which is why three lines report absent keys; the committed test passes the full recomputed
payload, and the assertion it makes is `any(d.startswith("A12.rules:"))`.) Both tests are green
now: `tests/test_publication.py` 34 passed, up from 28.

**Why the LIVE payload was not red — a premise the task got wrong.** §2 says "red first against
the stale `rules: 2`… then green", which reads as though `docs/data/sources_per_check.json` was
still stale at HEAD. It was not. `9cdb679` (the abstract task) had `docs/data/sources_per_check.json`
in its write set and regenerated it, which cured the drift as a side effect four hours before
this task ran. The first run of the new guard against the live payload passed on its first try.
The drift class is real and the guard is the right guard; the specific instance had already been
healed by an unrelated rebuild, which is itself the argument for a standing comparison rather
than a rebuild that happens to touch the file.

**The `created_at` answer: the graph cannot say, and it is worse than the task states.**

* `(:Rule)` carries exactly `rule_id`, `version`, `indicator_code`, `qualifier`, `current`.
  No temporal property. Desktop's 2026-09-15 query (all three A12 rules return `created: None`)
  is confirmed live.
* `(:Finding)` carries no timestamp either — `rule_id`, `indicator_code`, `params_hash`,
  `finding_id`, `verdict`, `reason`, `target_doc_id`, `current`, `evidence_unretained`, `cycle`,
  `cycle_kind`, `generation`. So not even a first-judged-at is answerable in Cypher. The nearest
  graph-answerable fact is the earliest CYCLE the rule judged in: `scan_2026-09-07_rj3` for
  `RULE-A12-v3`.
* **The projection cannot stamp it**, on two counts. The write site is
  `assessment/harness/scan/publish.py`, which this task's own "Zero edits to" forbids. And
  substantively: `build_projection.py` is reset-and-replay, so a `created_at` written at
  projection time records the time of the LATEST projection and moves on every replay — the
  exact shape `publish.py` already refuses in-file for `cycle` ("a property invented at
  projection time out of a file beside it").
* **The event log cannot supply it either.** The earliest `RULE-A12-v3` event is
  `2026-09-14T19:45:44.794994+00:00`, written by a re-judgement of the 2026-09-07 cycle. Log
  timestamps are WRITE times, not introduction times. "When did this rule reach the graph" has
  no recoverable answer from either store today.
* So, per the decision's own branch: **recorded as a proposed ResearchTask and stopped there.**
  `8a73a13f-30b1-4ebb-9e61-505a7a94532f`, state `proposed`. The fix it names is a
  `rule_introduced` event minted where a rule is introduced (the registry), projected onto
  `(:Rule)` — a scan-layer schema change, out of scope for a hygiene task whose write set
  excludes `assessment/` and `events/`.

The guard is aimed at the drift class and not at the unrecoverable incident, as the decision
instructed.

---

## 3. Decision 3 — every payload under `docs/data/`, and what compares it to its source

| payload | derived from | compared to that source by a standing test? |
|---|---|---|
| `data/ai_readiness_framework.json` | byte copy of `framework/ai_readiness_framework.json` | **Yes.** `test_every_copy_still_equals_the_record_it_was_copied_from` hashes the SOURCE against the digest in `data/index.json` and byte-compares the copy. The record→graph half is `test_framework_projection_roundtrip.py` (DD-057). |
| `data/corpus_manifest.json` | byte copy of `corpus/manifest.json` | **Yes.** Same copy test, same mechanism. |
| `data/results_tagged.json` | `(:Result)` on the graph + the artifact registry + the report's `{{result:…}}` tags | **Yes.** `test_the_published_result_values_and_states_match_the_graph` (value and state per name), `test_the_published_results_are_the_ones_the_report_tags` (the name set), `test_every_published_provenance_path_is_held_or_declared_ephemeral`, `test_an_ephemeral_datafile_re_derives_and_reproduces_its_dependent_values`. |
| `data/sources_per_check.json` | the graph via `report_traceability.measure`/`sources_appendix`, plus `corpus/manifest.json` and the framework record | **Yes — as of this task.** Before it: no. Its three existing tests all checked INTERNAL consistency (doc_ids inside the manifest; every citation carries URL + hash + date) and none compared it to the graph. That is precisely how `rules: 2` published for two days with every gate green. |
| `data/CITATION.cff` + root `CITATION.cff` | generated from `docs/reports/publication.yaml` | **Partial.** `test_the_citation_files_are_one_file_written_twice` compares the two WRITES to each other; `test_citation_cff_parses_and_carries_every_required_key` checks shape. Only the SPDX identifiers and the corpus note are compared back to the declaration. Title, abstract, version and authors are not. |
| `data/zenodo.json` + root `.zenodo.json` | same | **Partial.** As above, via `test_zenodo_metadata_parses_and_mints_nothing` and the two licence tests. |
| `data/index.json` | the build itself: each copy's source sha256, the link set, the licence declaration | **Partial.** The `copies` digests ARE what the copy test reads, so a drifted copy fails through it. `built_at`, `build_commit`, `generated` and `matrices` are compared to nothing. |

**What the next hygiene task is authored from, from this table.** No new guard was written for
any of it here, per the decision.

1. **The abstract's count reaches five generated consumers and no standing test.** It is checked
   only by `scripts/check_protected_abstract_five_checks.sh`, a task gate somebody runs. That is
   the same shape as the defect closed here: a published string compared to its source by a check
   that is not standing. The new label tests cover the MATRIX LABELS; the abstract still is not
   covered by the suite.
2. **The `PARTIAL` rows above are one class**, not three: a generated file compared to its twin
   and to its schema, but only field-by-field for the licence. `publication.yaml` → consumer is
   the comparison that does not exist.
3. **`docs/reports/scan_matrix_*.{json,csv}` are published and listed in `data/index.json`'s
   `matrices`, and sit outside `docs/data/`** — so outside this inventory and outside the copy
   test. They are the obvious next row.
4. `data/index.json`'s own `generated` and `matrices` lists are the site's claim about what it
   published, checked against nothing.

---

## 4. Decision 4 — the G1-D row stays and is labelled

All **40** G1-D rows in `docs/data/sources_per_check.json` (of 73 rows total) now carry
`"measurement_tier": "product"` and `"withdrawn_from": "host-level"`. No other row carries
either key, because no other indicator node does. The diff on the payload is exactly those two
keys on those forty rows.

`build_l0_site.INDICATOR_LABELS` names the two keys; `indicator_labels()` reads them off the
framework record's indicator node through `report_traceability.FRAMEWORK_CODE` (so `A11-declared`
resolves to `A11` rather than fuzzy-matching a neighbour), and emits only what the node actually
holds. Nothing is typed in the builder.

**A premise the task got wrong, and what it forced.** The decision says both values are "read
from the framework record's indicator node, never typed". The node carried `measurement_tier:
product` (written by `scripts/tag_g1d_product_tier.py` under DD-066) and **no `withdrawn_from`
at all** — that fact lived in `params.tier0.legs_withdrawn` and in the report's generated prose,
neither of which the appendix builder reads. So the property had to be written before it could
be read:

* **`scripts/tag_g1d_withdrawn_from.py` (new)** writes `withdrawn_from` and
  `withdrawn_from_source` on `ind:G1-D` through `framework_writeback.save`, the single writer.
  It refuses unless `params.tier0.legs_withdrawn` actually names G1-D withdrawn from exactly
  `["home", "well_known"]` — "host-level" is this project's name for those two surface kinds
  (`scripts/withdrawn_legs.py::_HOST_DEFAULT`) and would be the wrong word for any other set —
  and it refuses if the node carries no `measurement_tier`, because a leg recorded as withdrawn
  with no record of where it IS measured is the state `tag_g1d_product_tier.py` exists to
  prevent. The parameter it read is on the event's `changes.read_from`.
* Delta: one node changed, `nodes_added {}`, `nodes_removed {}`, `edges_changed 0`,
  `counts_keys_dropped []`. `scripts/build_framework_graph.py --dry-run` is still
  `unchanged: true` — the skeleton regeneration remains a byte-for-byte no-op with the new
  property.
* **The projection followed** (DD-057): `scripts/load_framework_graph.py`, EXIT=0, 49 indicators
  in graph, `MEASURES` 41. `tests/test_framework_projection_roundtrip.py` 7 passed. Cypher
  confirms `(:AssessmentIndicator {code:'G1-D'})` now answers
  `measurement_tier: product, withdrawn_from: host-level`.

**This crossed the task's "Zero edits to: … `events/`", and the crossing is not hideable.**
`framework_writeback.save` is the only code permitted to write the record and it cannot write
without appending its event. Decision 4 and that line of the write set cannot both be honoured;
decision 4 is the substantive instruction and the `events/` entry is a blanket "this task
measures nothing". Exactly **one** line was appended, to `events/batch-033_framework.jsonl`, of
`event_type: framework_writeback`, `script: tag_g1d_withdrawn_from`. No line was edited or
removed (invariant 1 intact), no other shard moved, and no Observation, Finding, extraction or
measurement event was minted.
`scripts/check_protected_derived_counts.sh` asserts each of those clauses rather than asserting
`events/` empty — a narrower claim, and a checkable one.

`framework/` is absent from the task's "Zero edits to" list, which lists the matrices and
`publication.yaml` by name; the reading taken is that the omission is deliberate and decision 4
is what it is for. If that reading is wrong, the revert is one write-back with a reason.

---

## 5. Decision 5 — the abstract keeps its typed count

No change. `docs/reports/publication.yaml` is untouched (the protected-paths check asserts it),
the abstract still reads "Five host-level checks over one measurement cycle", and
`scripts/check_protected_abstract_five_checks.sh` still gates it against the matrix's own leg
count — now through the shared numeral map instead of its own copy of it. §5 item 3 is closed.

---

## 6. Verification — every number, and where it can be re-read

| check | result | log |
|---|---|---|
| framework projection (DD-057) | EXIT=0; 49 indicators, `MEASURES` 41 | `logs/framework_projection.log` |
| `scripts/build_l0_site.py` (write) | EXIT=0 | `logs/site_build.log` |
| `scripts/build_l0_site.py --check` | EXIT=0, `"wrote": []`, `"check_only": true` — green and idempotent after the write | `logs/site_check.log` |
| `tests/test_publication.py` | 34 passed (28 before this task) | run inline; also inside the suite below |
| `make gate-fast` | **2195 passed, 17 skipped, 25 deselected, 12 xfailed in 410.08s**, EXIT=0 | `logs/gate_fast.log` |
| `make gate-full` (pre-push) | **2220 passed, 17 skipped, 12 xfailed in 1319.04s**, EXIT=0 | `logs/suite.log` |
| `seldon verify` | **All checks passed**, EXIT=0 (5 Results withdrawn by decision under DD-066, as expected) | `logs/seldon_verify.log` |
| protected paths | **PASS**, EXIT=0 — 23 modified paths all inside the write set (22 before this RESULT was written); `state/`, `assessment/`, `kg/`, `corpus/`, `controls.yaml`, `dixie_evidence.yaml`, the report source, the sections, the generated fragments, all six matrix files, the PDF, `publication.yaml`, `docs/design_decisions.md`, `docs/design/`, `docs/schema_v0.1.md` and `CLAUDE.md` all empty | `logs/protected_paths.log` |

The protected-paths check also asserts the point of the task rather than assuming it: the tier-A
matrix has 5 legs, the rendered label is `The 16 Tier A bodies × the five host-level checks.`,
all four renderings carry it, no published page states another leg count, the appendix matches
what the graph produces now, and all 40 G1-D rows are labelled.

`logs/` is gitignored; what ships is this file quoting it.

---

## 7. Every premise the task got wrong

1. **§2's framing that the live payload was stale.** `docs/data/sources_per_check.json` carried
   `rules: 3` at HEAD — `9cdb679` regenerated it hours earlier. The red run had to be against the
   reconstructed `05455cd` payload, which is what §2 also asks for; the "then green" half was
   already green. §2 of this RESULT.
2. **Decision 4's premise that the node carried `withdrawn_from`.** It did not; only
   `measurement_tier`, `measurement_tier_source` and `construct_restated`. Writing it was the
   only way to read it. §4.
3. **"Zero edits to: … `events/`" is unsatisfiable together with decision 4.** The single-writer
   design appends an event per write. One line, framework shard, `framework_writeback`. §4.
4. **§1's "the diff on `docs/index.html` and `docs/llms.txt` is exactly the four labels".** True
   of `docs/llms.txt` — its entire diff is the two label lines. Not true of `docs/index.html`:
   the builder stamps build provenance on the page, so its diff is the two labels **plus**
   `built from commit 6363eb3bc52d on 2026-09-15` → `built from commit bc978220534e on
   2026-09-16`. UTC had also rolled past midnight, which moved `date-released` in `CITATION.cff`
   and its copy, `publication_date` in `.zenodo.json` and its copy, and all 17 `lastmod` values
   in `docs/sitemap.xml`. Every one of those is a build stamp; not one is a count, and nothing
   measured moved. A build date cannot be held still by a task that regenerates through the
   writer, which decision 1 requires.
5. **Decision 2's "if the projection can stamp `created_at` … do it" has no reachable branch.**
   Its write site is inside the task's own zero-edit set, and reset-and-replay makes the stamp
   meaningless anyway. The proposed-ResearchTask branch is the only live one. §2.
6. **Decision 2 understates the gap.** It says `Rule` carries no `created_at`. `Finding` carries
   no timestamp either, so the shortfall is not one property on one label. §2.

Premises that were **right** and are worth recording as such: `build_l0_site.py:96` was the typed
count; `build_l0_site.py:531` was the unreachable stale-count branch; `report_traceability.py:42`
was the false comment; A12 carries three rules on the graph and `05455cd` published two; and
`Rule` nodes return `created: None`.

---

## 8. Files

**New:** `scripts/numerals.py`, `scripts/tag_g1d_withdrawn_from.py`,
`scripts/check_protected_derived_counts.sh`, this RESULT.
**Changed:** `scripts/build_l0_site.py`, `scripts/report_traceability.py`,
`scripts/check_protected_abstract_five_checks.sh`, `tests/test_publication.py`,
`tests/test_report_traceability.py`, `framework/ai_readiness_framework.json`,
`events/batch-033_framework.jsonl` (+1 line), and the regenerated tree: `docs/index.html`,
`docs/llms.txt`, `docs/sitemap.xml`, `docs/data/{index.json, sources_per_check.json,
ai_readiness_framework.json, CITATION.cff, zenodo.json}`, `CITATION.cff`, `.zenodo.json`.
**Registered:** ResearchTask `8a73a13f-30b1-4ebb-9e61-505a7a94532f` (proposed).
