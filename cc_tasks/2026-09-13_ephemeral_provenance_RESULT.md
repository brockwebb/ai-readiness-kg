# RESULT — the ephemeral DataFile: the absence is on the node now, and the derivation with it

**Task:** `cc_tasks/2026-09-13_ephemeral_provenance.md`, together with
`cc_tasks/2026-09-13_ephemeral_provenance_ADDENDUM_1.md` (licences), which **amends** and does
not supersede it. `cc_tasks/2026-09-13_ephemeral_provenance_ADDENDUM*.md` was globbed before
starting and again before §3 — **ADDENDUM_1 both times and no other addendum**
(`logs/ephemeral_addendum_glob_pre_s3.log`).
**Date:** 2026-09-13. **Spend:** zero model calls. **Network: none.** No host was contacted by
anything in this task: the CC BY 4.0 legal code was taken off this machine (§4), and the only
remote operation is the `git push` §4 orders.

## THE GATE: PASS

§1's stop condition was **not met** — the registry has a property-update path that writes an
event and creates no new node (§1). Both halves shipped, the suite is green at every tier, and
**no Result value and no Result state moved**: 7,256 live Results queried before the node was
touched and again after everything, zero differences
(`state/ephemeral_provenance_2026-09-13.json`).

## 1. §1 — the update path exists, so §1 did not stop

The task's condition was *"Stop if the registry has no update path for a DataFile node's
properties without a new node."* Measured, not assumed:

| what was looked for | found |
|---|---|
| a CLI verb | `seldon artifact update ARTIFACT_ID -p KEY=VALUE --actor` |
| the code behind it | `seldon.core.artifacts.update_artifact` — appends an `artifact_updated` event to `seldon_events.jsonl`, **then** updates the node's properties in place |
| a new node, a supersession, a re-bind | **none of the three.** The `artifact_id` is unchanged and the event carries only the changed properties |
| an edge verb | `seldon link create <from> generated_by <to>`, which MERGEs, so re-running is idempotent |
| whether `DataFile -[:generated_by]-> Script` is a legal edge | **yes**, `seldon/domain/research.yaml`: `generated_by.from_types` includes `DataFile` (added by AD-028 for this repo) |

**The CLI was not used for the properties, and the reason is the one thing here worth keeping.**
`-p KEY=VALUE` can only carry strings, and `materialized` has to be a real boolean: a node
property reading `"false"` is **truthy** to every consumer that tests it, which would make the
mark a decoration that reads as its own opposite. `scripts/mark_ephemeral_datafile.py` therefore
calls `update_artifact` directly — the same function the CLI calls — and the boolean is a
boolean. The edge went through the CLI, where there is no such problem.

## 2. Decision 1 — the node, before and after

`scan_matrix_2026-09-10`, `83ae0f2d-739a-4e79-b1e1-e1b94b3d8cbe`. Name, path, description and
state are **untouched**; what it gained is what it owed a reader.

**Before**

```
name         scan_matrix_2026-09-10
path         state/scan_matrix_2026-09-10.json      <- nothing writes it, nothing holds it
state        proposed
description  The Tier A matrix of cycle scan_2026-09-10, whose JUDGEMENTS the cycle's gate
             refused to register and whose COLLECTION is what this registers. …
edges        (none)
```

**After**

```
materialized        false
derivable_from      state/scan_2026-09-10.json      <- the repository DOES hold this
derivation_command  scripts/scan_report.py --cycle scan_2026-09-10
derivation_note     Cycle scan_2026-09-10 was MEASURED and deliberately never reported: its
                    judgements were refused by its own gate and the judgement of record is the
                    re-judgement scan_2026-09-10_rj2. This matrix is the side effect of
                    reporting it, so the repository does not hold it and
                    tests/test_scan_figures.py skips the figure suite on exactly that absence
                    (cc_tasks/2026-09-10_harness_v5_blind.md decision 6). … Decision of
                    record: cc_tasks/2026-09-13_ephemeral_provenance.md decision 1.
edges               GENERATED_BY -> scan_report
```

**Both changes are on the event log**, with `actor: cc` — an `artifact_updated` at
`2026-09-13T16:56:57.038382Z` carrying the four properties, and a `link_created` at
`…:57.912239Z` carrying `DataFile -generated_by-> Script`. No event was edited and none was
deleted (`scripts/check_protected_ephemeral_provenance.sh` checks the log only grew).

**No Result was touched.** The four that are `COMPUTED_FROM` it keep their values, their states
and their edges:
`fss_scan_netlocs_contacted_2026-09-10` 35, `scan_error_class_unknown_2026-09-10` 1,
`scan_observations_2026-09-10` 2718, `scan_requests_total_2026-09-10` 2684 — all `published`,
all unchanged. Re-pointing them at a file the repository happens to hold would have rewritten
what happened; the matrix WAS computed and they WERE computed from it.

**The script refuses three ways before it writes anything**, which is what makes the mark a
measurement rather than a label: a DataFile whose path the repository **does** hold (a file that
exists is materialized, and saying otherwise is a false statement about the tree); a
`derivable_from` the repository does **not** hold (the whole claim is that the value is still
reachable, and an unreachable source is a dead end with extra words); and a derivation command
whose script is not the one the `GENERATED_BY` edge names (one node, two derivations).

## 3. Decision 4 — the temporary-tree rule is read from the graph, and the special case is gone

**Deleted:** `rederive_tagged_results.rederive_base_cycle_counts`, which named `scan_report`,
monkeypatched `matrix_path`, and then **deleted the Tier C sibling by hand** if the run had
created it.

**In its place**, three general pieces, none of which names a generator:

* `ephemeral_data_files()` — `MATCH (d:DataFile) WHERE d.materialized = false`, returning each
  node's `path`, `derivable_from`, `derivation_command` and its `GENERATED_BY` Script.
* `temporary_output_root(module)` — points the module's output root at a temp tree under
  `REPO/tmp` (gitignored) for the duration of one run. The seam is the module-path output
  global this repo's convention already requires, and which `build_l0_matrices` already had:
  `OUT_DIR`, plus `GEN_DIR` when present. A generator that exposes **neither is a refusal with
  a message**, not a silent fall-through into the tree — the fall-through is how the matrix got
  materialised the first time.
* `rederive_ephemeral(captured)` — drives each node's own `derivation_command`, then asserts
  three things, because a redirect that quietly failed looks exactly like a success: the
  repository still does not hold the path; the **temporary tree does**, so the derivation
  really ran and really wrote it; and `derivable_from` exists.

**`scripts/scan_report.py` gained the seam it lacked**: `OUT_DIR = REPO / "state"`, used by
`matrix_path()` and by the Tier C write, with the *read* side deliberately left on
`REPO / "state"` (a re-derivation needs the real payload and a temporary output). Default
behaviour is byte-identical — the published matrices are protected in §6 and did not move — and
`main` now refuses an `OUT_DIR` outside the repository, because this module reports its outputs
with `Path.relative_to(REPO)`.

**What the general path produced**, from `state/rederive_tagged_2026-09-13.json`:

```json
"ephemeral_data_files": [{
  "data_file": "scan_matrix_2026-09-10",
  "path": "state/scan_matrix_2026-09-10.json",
  "derivable_from": "state/scan_2026-09-10.json",
  "command": "scripts/scan_report.py --cycle scan_2026-09-10",
  "generator": "scan_report",
  "wrote_into_temporary_tree": ["scan_matrix_2026-09-10.json",
                               "scan_matrix_tierc_2026-09-10.json"]
}]
```

**Both files landed in the temporary tree**, which is the point: the sibling that used to need a
hand-written deletion is now covered by the same one-line rule, and neither path exists under
`state/` afterwards (asserted by the engine, by the new test, and by the protected-paths check
independently).

**The whole tagged gate still passes through it:** 59 tagged Results, **59 reproduce**, 0 not
re-derived, 0 disagreements, `"gate": "PASS"`. The four that depend on the ephemeral DataFile
re-derive to exactly their registered values (35, 1, 2718, 2684).

## 4. ADDENDUM_1 — the licences, and where the text came from

`LICENSE` (MIT, © 2026 Brock Webb) and `LICENSE-DATA` (CC BY 4.0 International) are at the
repository root. `docs/reports/publication.yaml` declares `license_code: MIT`,
`license_data: CC-BY-4.0` and `license_corpus_note`, and `scripts/build_l0_site.py` now
**refuses to build** if any of the three is missing or if either text file is absent: a declared
licence with no text is the claim without the grant, and the previous build shipped with no
licence at all.

**The CC BY 4.0 legal code is verbatim, and no host was contacted for it.** A2 asks for the
verbatim creativecommons.org text "held in the corpus if admitted, otherwise the canonical text
with its URL". **No admitted corpus document is the legal code** — the manifest's 377 entries
contain zero Creative Commons licence documents; the greps that found `creativecommons.org` in
`corpus/` found page footers. So the text came from this machine and was **cross-checked
word-for-word against an independent copy** before being used:

| copy | what it is | agreement |
|---|---|---|
| `/Users/brock/GitHub/book_responsible_ai/LICENSE` | the complete official document — the "not a law firm" front matter, the Public License, the closing trademark note | the source used |
| `…/site-packages/pypdfium2-5.4.0.dist-info/licenses/LICENSES/CC-BY-4.0.txt` | the SPDX/REUSE-format copy | its whole text appears **verbatim inside** the above, whitespace-normalised |
| `…/site-packages/colorcet-3.1.0.dist-info/LICENSE.txt` | a third, independent copy | agrees word-for-word with the SPDX copy but for a title suffix and footnote markers |

Only the part of the source file from its first `=======` rule onward was taken, and it was
checked to contain no project-specific text before use. `LICENSE-DATA` is therefore the project's
own header (the grant, what it covers, the corpus exclusion, the SPDX id, the canonical deed and
legalcode URLs) followed by 398 lines of unmodified licence. A test asserts the legal code is
present rather than merely referenced.

**Both identifiers reach all three generated consumers**, and each carries the licence of the
thing it describes rather than conflating the two:

* `CITATION.cff` — `license: CC-BY-4.0`, because CFF's `license` is the licence of the **cited
  artefact**, which here is the report; MIT is named in `notes`.
* `.zenodo.json` — `"license": "CC-BY-4.0"` for the same reason; MIT in `notes`. **No DOI**, and
  the asymmetry is deliberate: the licence is the operator's declaration, the mint is an action
  under his own name that no build step may take.
* `docs/index.html` — a `Licence` section in the fixed prose, generated from the declaration,
  naming both with links to both texts.

**A3, the corpus exclusion, has one source and five destinations.** The sentence lives once in
`publication.yaml` and is asserted present — whitespace-normalised, so line-wrapping cannot
break it — in `LICENSE`, `LICENSE-DATA`, `CITATION.cff`, `.zenodo.json` and `docs/index.html`,
and on the **corpus manifest's own published copy entry** in `docs/data/index.json`
(`copies[].license_note`), which is the one file on the site a reader could mistake for a grant
over third-party works. `docs/data/index.json` also gained a top-level `license` block, so a
machine reading only the manifest can tell what it may do with the files it lists.

### One thing ADDENDUM_1 does not cover, left undone on purpose

**`docs/llms.txt` carries no licence.** It is the machine-readable face of this site and the
licence belongs on it — but the addendum's widening names `docs/index.html`,
`docs/data/index.json` and the two citation copies, and nothing else. The section was written,
then **withdrawn and the file restored byte-identical to HEAD**, with the reason left in
`build_l0_site.llms_txt` where the next author will meet it. A boundary widened whenever the
next edit looks additive is not a boundary. One line of work for a task that may touch that file.

## 5. Decisions 2 and 3 — the stranger test is a test, and the published record says which kind of absence

**Decision 3.** `results_tagged.json` publishes two buckets where it published one:

```json
"provenance_paths_absent": [],
"provenance_paths_ephemeral": [{
  "path": "state/scan_matrix_2026-09-10.json",
  "artifact": "scan_matrix_2026-09-10",
  "derivable_from": "state/scan_2026-09-10.json",
  "derivation_command": "scripts/scan_report.py --cycle scan_2026-09-10",
  "generated_by": ["scan_report"],
  "depended_on_by": ["fss_scan_netlocs_contacted_2026-09-10",
                     "scan_error_class_unknown_2026-09-10",
                     "scan_observations_2026-09-10", "scan_requests_total_2026-09-10"]
}]
```

The task says `provenance_paths_absent` *becomes* `provenance_paths_ephemeral` and its gate says
`provenance_paths_absent` must be **empty**. Both are satisfied by keeping both keys with
different meanings: `ephemeral` is an absence that is a **decision**, carrying its derivation;
`absent` is an absence that is a **defect**, and its being non-empty is a finding on the face of
the published data. One list could not tell those apart, which is what made the previous
publication's `provenance_paths_absent: ["state/scan_matrix_2026-09-10.json"]` read as a broken
link. The derivation also rides on **each reference row**, beside the Result that needs it, so a
reader who never scrolls to the top-level buckets still finds it.

**Nothing is hardcoded in the builder** — no path, no cycle, no generator. `_with_presence`
reads `materialized`, `derivable_from` and `derivation_command` off the node and reports
`ephemeral: true` only on an explicit `materialized is False`; the day a second artifact becomes
ephemeral, neither the builder nor the engine needs an edit.

**Decision 2 — four tests, in `tests/test_publication.py`:**

1. `test_every_published_provenance_path_is_held_or_declared_ephemeral` — for every DataFile any
   `published` Result is `COMPUTED_FROM`: held, or `materialized: false` **with a
   `derivable_from` the repository holds**. A DataFile in neither is red, and the failure names
   the Results that depend on it. **Both branches are asserted, not just whichever exists
   today**: 9 held, 1 ephemeral, 0 dead — and if the last ephemeral one is ever materialised,
   the assertion that fails says so and says to delete it deliberately rather than let the test
   pass vacuously.
2. `test_an_ephemeral_datafile_re_derives_and_reproduces_its_dependent_values` — drives the
   **general path** and compares against the registry. See §6 for the one thing this found.
3. `test_the_published_record_separates_a_decided_absence_from_a_defect` — the two buckets, and
   every unheld reference row carrying its derivation.
4. A5's three: both texts exist and carry their SPDX id; both ids reach all three consumers;
   the corpus sentence is in all five places and on the corpus copy's manifest entry.

## 6. The premise this task got wrong, and one the registry has

| premise | measured |
|---|---|
| §1's "stop if the registry has no update path for a DataFile node's properties without a new node" | **Not met.** `seldon artifact update` / `update_artifact` is exactly that path and writes an `artifact_updated` event. §1 did not stop. The one real constraint is that the CLI cannot carry a boolean (§1). |
| decision 3's "`provenance_paths_absent` **becomes** `provenance_paths_ephemeral`" vs its gate's "`provenance_paths_absent` empty **and** `provenance_paths_ephemeral` carries one entry" | **Both, read as two keys with different meanings** (§5). A rename alone would have deleted the place a genuine dead path gets reported. |
| decision 2's "…and reproduce the **dependent values**" | **True for three of the four dependents, and the fourth is a registry imprecision, not a hole.** `fss_scan_netlocs_contacted_2026-09-10` is `COMPUTED_FROM` this DataFile and its `GENERATED_BY` names `scan_report` — but the function that computes it is `register_l0_report_results.netlocs_contacted`. `cycle_results.register` takes **one** script per batch, and `scripts/register_measured_collection_facts.py` registered it inside the `scan_report` batch, so the edge names the batch's script rather than the computation's. The test does not wave it through: a dependent the derivation does not yield must be one the standing tagged gate covers, or it is red. It is (it re-derives there, at 35). **Recorded, not patched** — a `GENERATED_BY` edge is not corrected by editing a node this task was not sent to change, and it is one gate per task. |
| ADDENDUM_1 A2's "verbatim text … otherwise the canonical text with its URL" | **The first branch, from this machine rather than from the corpus** (§4). No admitted corpus document is the legal code; two independent on-disk copies agree word-for-word, so the verbatim text was available without contacting a host. |
| ADDENDUM_1 A4's "`docs/index.html` states both licences" | **Done**, and it is the only `docs/` face that does — `llms.txt` is outside the widening (§4). |

## 7. The gate (§3), clause by clause, with the log that carries each

| clause | result | log |
|---|---|---|
| addendum glob, before starting and before §3 | **ADDENDUM_1 only**, both times | `logs/ephemeral_addendum_glob_pre_s3.log` |
| decision 2's test green over **every** DataFile a published Result depends on | **PASS** — 9 held, 1 ephemeral, 0 dead | `logs/ephemeral_gate_task.log` |
| the four Results re-derive and reproduce **through the general path** | **PASS** — 35, 1, 2718, 2684, all `reproduces`; whole gate 59/59, `"gate": "PASS"` | `logs/ephemeral_rederive.log`, `state/rederive_tagged_2026-09-13.json` |
| `provenance_paths_absent` empty; `provenance_paths_ephemeral` one entry with its derivation | **PASS** — `[]` and one entry carrying `derivable_from`, the command, the generator and its four dependents | `docs/data/results_tagged.json` |
| every change to the DataFile on an event | **PASS** — one `artifact_updated` + one `link_created`, both `actor: cc`; the log only grew | `logs/ephemeral_mark.log`, `logs/ephemeral_protected.log` |
| no Result value or state changed, **asserted by query before and after** | **PASS** — 7,256 Results both times, **0 differences** | `state/ephemeral_provenance_2026-09-13.json` |
| A5 green (ADDENDUM_1's gate) | **PASS** — 3 licence tests | `logs/ephemeral_gate_task.log` |
| `docs/index.html` and `data/` regenerated by the site builder, no other `docs/` change | **PASS** — exactly the six allowed paths changed; `robots.txt`, `llms.txt`, `sitemap.xml`, the report, the fragments and every published matrix byte-identical | `logs/ephemeral_protected.log` |
| `make gate-task` | **PASS** — **2,022 passed, 17 skipped, 19 deselected, 12 xfailed, 369.09 s**; then 16 of 16 payloads re-derive, 6.05 s | `logs/ephemeral_gate_task.log` |
| `make guards` | **PASS** — 25 passed, 15.63 s | `logs/ephemeral_guards.log` |
| `make gate-full` (detached, logged, polled to EXIT) | **PASS** — **2,041 passed, 17 skipped, 12 xfailed, 1,215.93 s (20:15)** | `logs/ephemeral_suite_full.log` |
| `seldon verify` | **PASS** — all checks passed, 34,603 events readable | `logs/ephemeral_verify.log` |
| protected paths | **PASS** | `logs/ephemeral_protected.log` |

Every log carries its own `EXIT=0` line and all five were written before this file was. `logs/`
is gitignored; what ships is this file quoting it. The six tests the two tiers differ by are the
six added here (2,022 + 19 deselected = the fast tier; 2,041 is the whole suite).

## 8. What changed

**New:** `scripts/mark_ephemeral_datafile.py`, `scripts/check_protected_ephemeral_provenance.sh`,
`LICENSE`, `LICENSE-DATA`, `state/rederive_tagged_2026-09-13.json`,
`state/ephemeral_provenance_2026-09-13.json`.
**Modified:** `scripts/rederive_tagged_results.py` (the general ephemeral path; the special case
deleted), `scripts/scan_report.py` (the `OUT_DIR` seam, default behaviour unchanged),
`scripts/build_l0_site.py` (the two buckets, the licence consumers, the required declaration
keys), `docs/reports/publication.yaml` (the licences), `tests/test_publication.py` (+6 tests),
`CITATION.cff`, `.zenodo.json`, `docs/index.html`, `docs/data/{results_tagged,index,CITATION.cff,zenodo}.json`,
`seldon_events.jsonl` (+2 events).
**Zero edits** to rule modules, harness runtime, stored payloads, prior Results' values and
states, prior RESULTs, figures, section prose, the skeleton, the record, `corpus/`, `events/`,
`docs/robots.txt`, `docs/llms.txt`, `docs/sitemap.xml`, the built report and its PDF.

## 9. What the next task should pick up

1. **`docs/llms.txt` should state the licence** (§4). Two lines and a test; it is outside this
   addendum's widening and nothing else blocks it.
2. **The `GENERATED_BY` edge of `fss_scan_netlocs_contacted_2026-09-10` names the batch's script
   rather than the function that computes it** (§6). The general fix is in
   `cycle_results.register`, which takes one script per batch of rows that may have more than
   one author. Worth a task of its own, because it is a provenance edge on a published Result.
3. **The report and its PDF state no licence.** The addendum's four consumers do not include
   the document itself, and a reader who meets the PDF first meets no licence at all.
4. **The DOI**, when the operator wants it: `.zenodo.json` is prepared, now with a licence, and
   no deposit was made.
