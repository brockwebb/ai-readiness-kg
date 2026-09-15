# RESULT — the abstract says five host-level checks, because the matrix has five columns

**Task:** `cc_tasks/2026-09-15_abstract_five_checks.md`, implementing DD-066, under DN-002
decision 5 and DN-005 §5 rule 1.
**Addendum:** **none exists.** Globbed at the start of the session and again before §2
(`logs/abstract_addendum_glob_pre_s2.log`); both times zero files. The base task was executed
as written.
**Framework layer served (DN-005 §5 rule 1):** none. Hygiene, as the task says: a published
summary must not disagree with the report it summarizes.
**Date:** 2026-09-15. **Spend: zero model calls. Network: none** — no host was contacted, no
`ANTHROPIC_API_KEY` was set, nothing was judged, nothing was measured, and **not one byte under
`state/` or `events/` changed**. The only remote operation is the `git push` §3 orders.

## THE GATE: PASS

| clause (§2) | result | log |
|---|---|---|
| `tests/test_publication.py` | **PASS — 28 passed, 1.20 s** | `logs/abstract_test_publication.log` |
| site `--check` **before** the write | **PASS — EXIT=0**, 10 data links, 56 tagged Results, self row `measured` | `logs/abstract_site_check1.log` |
| the regeneration itself | **PASS — EXIT=0**, 14 files written by the builder | `logs/abstract_site_build.log` |
| site `--check` **after** the write (idempotence) | **PASS — `wrote: []`**, nothing left to change | `logs/abstract_site_check2.log` |
| `make gate-fast`, detached and polled | **PASS — 2,188 passed, 17 skipped, 25 deselected, 12 xfailed, 435.45 s (7:15)** | `logs/abstract_gate_fast.log` |
| `seldon verify` | **PASS — all checks passed**; the five G1-D withdrawals still report as *withdrawn by decision*, not stale | `logs/abstract_verify.log` |
| protected paths | **PASS** | `logs/abstract_protected.log` |
| `make gate-full`, detached and polled (pre-push, CLAUDE.md) | **PASS — 2,213 passed, 17 skipped, 12 xfailed, 1,405.00 s (23:24)** | `logs/suite.log` |

Every log carries its own `EXIT=0` and all of them were written before this file was. The tier
run was **`gate-fast`, not `gate-task`** — correctly, and stated rather than glossed: no rule
module, no rule registry and no re-derivation engine moved, and nothing under `state/` was
touched, so the re-derivation tier had nothing new to re-derive. `gate-full` ran anyway, before
the push, and it contains the re-derivation tests.

## 1. The abstract sentence, before and after

The change is **one word**, on one line, in one file.

**Before** (`logs/abstract_before.log`, whitespace-normalised as every consumer reads it):

> Host-level AI-readiness findings for the sixteen recognized agencies and units of the US
> federal statistical system, plus three federal reference hosts shown separately. **Six**
> host-level checks over one measurement cycle with one declared client identity, every verdict
> traceable to the Finding, the rule version and the retained response body that produced it.
> The matrices, the per-check source appendix and every registered Result the report quotes are
> published as data beside it; the PDF is a view of them.

**After:**

> Host-level AI-readiness findings for the sixteen recognized agencies and units of the US
> federal statistical system, plus three federal reference hosts shown separately. **Five**
> host-level checks over one measurement cycle with one declared client identity, every verdict
> traceable to the Finding, the rule version and the retained response body that produced it.
> The matrices, the per-check source appendix and every registered Result the report quotes are
> published as data beside it; the PDF is a view of them.

The diff on `docs/reports/publication.yaml` is `+1 / −1`, asserted by the protected-paths check
rather than described here.

**Decision 1's conditional did not fire, and that is why this is one word.** The task provided
for two cases: the abstract enumerating the checks by name, or the abstract stating a rate that
included G1-D. It does **neither**. It states a bare count, so no name left a list and no
sentence had to be re-sourced from the registered Results. **Five** is the right count on the
report's own arithmetic — `## The five checks`, of which A4, A5, A10 and A11-declared are rated
and A12 "is a candidate check, adopted by nobody, and it enters no fraction here"
(`docs/reports/2026-09_fss_ai_readiness_L0.md` lines 54 and 76) — and on the published matrix's,
whose `legs` array is exactly `['A4', 'A5', 'A10', 'A11-declared', 'A12']`.

**The count is now asserted against the matrix, not against this RESULT.** The protected-paths
check reads `legs` off `docs/reports/scan_matrix_tierA_2026-09-10_rj2.json`, maps its length to
an English numeral, and fails if the abstract or any generated consumer disagrees. The next
withdrawal moves the matrix and the check fails until the abstract follows; that is the whole
defect this task exists for, and it is now a gate rather than a habit.

## 2. The regenerated files, by path

Decision 2 was honoured literally: **not one consumer was edited by hand.** Every file below was
written by `scripts/build_l0_site.py`, the existing writer.

**Carry the abstract — six files, seven occurrences:**

| path | occurrences |
|---|---|
| `CITATION.cff` | 1 (`abstract:`) |
| `.zenodo.json` | 1 (`description`) |
| `docs/data/CITATION.cff` | 1 (the served copy of the same string) |
| `docs/data/zenodo.json` | 1 (the served copy) |
| `docs/index.html` | 2 — the `<meta name="description">`, truncated at 300 chars, and the body `<p>` |
| `docs/llms.txt` | 1 (the blockquote) |

**Regenerated and changed for a reason other than the abstract — two files:**

| path | what moved | why |
|---|---|---|
| `docs/data/index.json` | `built_at`, `build_commit` (`6932a9ee5daa` → `6363eb3bc52d`), and the sha256 + byte count of both citation copies (1794 → 1795 bytes, 1497 → 1498) | the record of what was published; `Six` → `Five` is one byte longer, and the record says so |
| `docs/sitemap.xml` | every `lastmod` 2026-09-14 → 2026-09-15 | ordinary build-date stamp, 18 entries |

**Regenerated byte-identical — five files:** `docs/.nojekyll`, `docs/robots.txt`,
`docs/data/ai_readiness_framework.json`, `docs/data/corpus_manifest.json`,
`docs/data/results_tagged.json`. The builder rewrote them; git reports no change.

**One more file changed, and it is not this task's:** see §3 item 4.

**Nothing else moved.** Two files outside the generated set are this task's own record —
`cc_tasks/2026-09-15_abstract_five_checks_RESULT.md` (this file) and
`scripts/check_protected_abstract_five_checks.sh` (the gate §2 requires; every prior task has
its own). The protected-paths check enumerates the permitted set and fails on anything else, so
"nothing else moved" is a check, not a claim.

## 3. Every premise the task got wrong

**1. `publication.yaml` is not at the repository root.** It is
`docs/reports/publication.yaml`. Cosmetic — the "Implements" line names it unqualified, and the
first `cat` failed. No consequence; recorded because a path in a task file is a path somebody
will paste.

**2. "the abstract feeds `CITATION.cff`, `zenodo.json` and the site index" undercounts by
half.** It feeds **six generated files in seven places**, per the table in §2: the two citation
records exist twice each, once at the root where GitHub and Zenodo read them and once under
`docs/data/` where the index links them, and `docs/index.html` carries the sentence twice
because the `<meta>` description is a 300-character truncation of the same string. Every one of
them was regenerated, so the undercount cost nothing — but a task that had edited "the three
consumers" by hand would have left three copies saying `Six`.

**3. The abstract was NOT the last "six" on a published face. Four more remain, and they are
outside this task's write set.** `docs/index.html` (lines 44–45) and `docs/llms.txt` (lines
9–10) each say, twice:

> Matrix, tierA, JSON. The 16 Tier A bodies × **the six host-level checks**.

This is wrong about a file it is the label for: that matrix's `legs` array has five entries. It
does not come from `publication.yaml` — it is a **hardcoded literal** in
`scripts/build_l0_site.py:96` (`MATRICES`), so regenerating re-emitted it verbatim, and the two
published pages now say `Five` in the abstract and `six` four lines down.

**Left standing deliberately, and not because of the write set alone.** The task's `Zero edits
to` clause excludes `scripts/`, and `cc_tasks` are immutable — but the stronger reason is that
**typing `five` there would be the same defect this task was authored to clean up.** A count of
derived columns typed into prose is exactly what went stale when G1-D was withdrawn; retyping it
one lower buys one cycle and re-arms the trap. The fix is to read `len(legs)` off the matrix the
description labels, which is what the new protected-paths check does for the abstract and what
the builder should do for the matrix labels. That is a code change with a testable surface, and
it is the next task, not a word swap smuggled in under "regeneration".

**Two further "six"s are not published today and should go with it:**

* `scripts/build_l0_site.py:531` — "The six host-level checks have not been run against this
  host", in the branch that runs when `state/self_l0_<self_scan_cycle>.json` is absent.
  Unreachable right now (`self_row: measured`), so it ships nothing, but it is a latent wrong
  number waiting for the next self-scan gap.
* `scripts/report_traceability.py:42` — the comment "The report's six host-level checks" sits
  above a **seven**-entry `_NAMED_IN_CODE` list (`A4, A5, A10, A11-declared, A12, G1-D, A3`).
  A stale comment, and it was stale before G1-D was withdrawn.

`docs/design/2026-09-08_l0_product_shape.md:6` also says six. That one is **correct as
history** — it records what L0 was on 2026-09-08, when it was six legs — and a design note is
not a published summary. Left alone on purpose.

**4. The regeneration corrected a stale published payload that nobody had noticed, and it has
nothing to do with the abstract.** `docs/data/sources_per_check.json`, A12's chain row:

```
-   "rules": 2,
+   "rules": 3,
```

Checked against the live graph rather than inferred (`logs/abstract_a12_rules.log`):

```cypher
MATCH (r:Rule)-[:MEASURES]->(i:AssessmentIndicator {code: 'A12'}) RETURN r.rule_id
```

**Three: `RULE-A12-v1`, `RULE-A12-v2`, `RULE-A12-v3`.** The payload said two. It was last
written at `05455cd` on 2026-09-13; `RULE-A12-v3`'s module landed at `52ec048` on 2026-09-07,
six days earlier, which means the *graph* did not yet carry the third `Rule` node when that
build ran and has carried it ever since. **I did not root-cause when it was projected, and I am
not guessing** — the verifiable facts are that the published number disagreed with the graph,
that the disagreement survived two days and every green gate, and that it was corrected here
only because this task happened to re-run the builder.

**That is the DN-004 family again** — a published artifact one generation behind the graph, with
nothing comparing the two. `tests/test_publication.py` asserts published *Result* values and
states against the graph (`test_the_published_result_values_and_states_match_the_graph`) and
asserts each copy equals the record it was copied from, but **nothing asserts the source-appendix
chain counts against the graph they were derived from.** DN-004 built exactly that guard for the
report's snapshot and its successor; the same guard does not exist for this payload. Flagged for
the next OODA in §5, with the honest caveat that this is the gap, not yet the incident's cause.

**5. The SEQUENCING line's ordering was already unsatisfiable when it was written.** "Runs now,
before `cc_tasks/2026-09-15_standing_dispatcher.md`" — but that task had already executed and
pushed (`cc_tasks/2026-09-15_standing_dispatcher_RESULT.md`, commit `6932a9e`), which
`cc_tasks/2026-09-15_g1d_leaves_l0_ADDENDUM_01.md` had **already recorded** ("this task runs
before the dispatcher (which had already pushed)"). The premise was wrong twice in one day, from
the same author, about the same task. **No operational consequence:** `seldon.yaml` has
`dispatch.enabled: false`, so the standing dispatcher is not running, hand-dispatch is the
correct mode under DN-006 decision 10, and this session's hand dispatch created no
batch-identity exposure. Recorded because a sequencing constraint that cannot be satisfied is a
sequencing constraint nobody can check.

**What the task got right:** decisions 2 and 3 were exactly the right instructions. Regenerating
through the writer caught the stale A12 count as a side effect; hand-editing "the three
consumers" would have hidden it and left three copies wrong. Holding `publication.yaml` to one
moved line is what let the gate assert `+1 / −1` instead of reading a diff.

## 4. What this task did not do

* **Did not touch the report, the PDF, the matrices, the sections or the fragments.** The
  abstract summarizes the report; it is not an input to it. Asserted, not asserted-by-intent:
  the protected-paths check names all six matrix files, the report source, the PDF,
  `docs/reports/sections/` and `docs/reports/generated/` and fails if any moves.
* **Did not touch `state/`, `events/`, `corpus/`, `framework/`, `assessment/`, `kg/`,
  `controls.yaml` or `dixie_evidence.yaml`.** No measurement, no judgement, no re-judgement, no
  event. This task changed a sentence.
* **Did not run a projection**, because nothing edited
  `framework/ai_readiness_framework.json`. DD-057's "a write-back is not finished until a
  projection follows it" does not apply: there was no write-back. `seldon verify` and the
  framework roundtrip test ran inside `gate-full` regardless.
* **Did not fix the four published "six host-level checks" matrix labels**, for the reason
  in §3 item 3.
* **Registered no new Result.** Nothing here is a measurement.

## 5. Open, for the next OODA

1. **The matrix labels, and the class they belong to.** Four published strings say "the six
   host-level checks" about a five-column matrix, from a hardcoded literal at
   `scripts/build_l0_site.py:96`; two more unpublished ones sit at `build_l0_site.py:531` and
   `report_traceability.py:42`. The fix is **derivation, not retyping**: read `len(legs)` off
   the matrix each label describes, the way
   `scripts/check_protected_abstract_five_checks.sh` now does for the abstract. Doing it that
   way also closes the next withdrawal, not just this one.
2. **No guard compares the published source-appendix to the graph.** §3 item 4 is a published
   payload that sat one rule-version behind the graph for two days with every gate green — the
   DN-004 shape, in a payload DN-004's guard does not cover. Two questions for the author, in
   order: *when* did `RULE-A12-v3` reach the graph (not established here), and *what else* in
   `docs/data/` has no graph comparison. A guard authored before the first question is answered
   is a guard aimed at a guess.
3. **The abstract still states a count in prose.** It is now gated against the matrix, so it
   cannot drift silently — but it is still a typed English numeral in a declaration file whose
   header says "Nothing here is a measurement." Worth asking whether the sentence should carry
   the count at all, or whether the count belongs to the report and the abstract should point at
   it. Not urgent; the gate holds either way.
4. **`docs/data/sources_per_check.json` still carries a full G1-D row** — 40 sources, 364
   definitions, one rule — for a leg withdrawn from L0 by DD-066. That is arguably correct (the
   sources exist; the construct stands; only the host-level *level* was wrong) and arguably a
   published appendix advertising a check the report withdrew. It is a DD-066 scope question,
   not a defect, and it was outside this task either way.

## 6. Logs

Every number above is re-readable at these paths. `logs/` is gitignored; what ships is this
file that quotes it.

```
logs/abstract_before.log                    the abstract as it stood, whitespace-normalised
logs/abstract_addendum_glob_pre_s2.log      the pre-§2 addendum glob          EXIT=0  zero files
logs/abstract_site_check1.log               site --check before the write     EXIT=0
logs/abstract_site_build.log                the regeneration                  EXIT=0  14 written
logs/abstract_site_check2.log               site --check after the write      EXIT=0  wrote: []
logs/abstract_consumers.log                 the abstract in all six consumers, and what still says six
logs/abstract_a12_rules.log                 RULE-A12-v1/v2/v3 on the graph    EXIT=0
logs/abstract_test_publication.log          tests/test_publication.py         EXIT=0  28 passed / 1.20 s
logs/abstract_gate_fast.log                 make gate-fast + check + verify   EXIT=0  2,188 passed / 435.45 s
logs/abstract_verify.log                    seldon verify                     EXIT=0  all checks passed
logs/abstract_protected.log                 protected paths                   EXIT=0  PASS
logs/suite.log                              make gate-full, detached, polled  EXIT=0  2,213 passed / 1,405.00 s
```
