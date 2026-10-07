# DN-013 — Design note: three defects the operator named on 2026-10-06 evening, and the rulings that fix them

**Date:** 2026-10-06, 22:20. Desktop session, from the operator's objections at thread close. These are design defects, not task defects; each ruling names the task that implements it. Under DN-005 §1, DN-009 d1 and d2, DN-012.

## 1. Existence is not discoverability (the known-endpoints defect)

**Defect.** The harness tests whether a stranger can find an agency's API, inventory, terms or changelog from the product page, and reported the failure of that search as the absence of the thing. api.census.gov, api.bls.gov, api.eia.gov, the BEA API, NASS Quick Stats and the data.gov API catalog are public knowledge, in training data and in the project's own files, and the harness guessed URLs instead. DN-012 d3 kept the stranger rule for the declared layer ("read from the agency's own developer page") and so repeated the defect one level up.

**DN-013-R1.** Two legs, two questions. **Existence:** does the body publish an API, an inventory on data.gov, API terms, a changelog? The declared layer is seeded from what is already known (model knowledge, api.data.gov, catalog.data.gov, each agency's developer page, this repository's own citations), every entry verified by one live fetch and recorded with its provenance (`seeded_from`, `verified_at`, status). **Discoverability:** can a machine reach it from the product page unaided? That is what the link probe, the guessed paths and the cap measure, and it is scored as its own indicator, never as existence. An existence `error` is reached only when a seeded location cannot be verified; a discoverability `fail` is a finding about the page.

**Implements:** `2026-10-07_seed_known_locations_and_split_discoverability.md`. It supersedes the link-cap question: the cap stays a politeness bound on the discoverability probe and decides nothing about existence.

## 2. Serial where nothing depends on anything (the wall-clock defect)

**Defect.** The scanner walks 16 hosts one after another at one request per second per host, so a cycle takes 16 times longer than its slowest host. The dispatcher runs one task at a time because every session shares one working tree. The test suite runs single-process, 42 minutes, usually twice per task. None of these is a model call; all of it is mechanical.

**DN-013-R2.** Hosts run in parallel, one worker per host, each worker holding its own per-host rate; the manners layer is per host and nothing crosses hosts. Prior art: every polite crawler since Heritrix keeps politeness per host and parallelism across hosts.

**DN-013-R3.** Tasks run in parallel when independent: the dispatcher launches each task in its own `git worktree` on a task branch, merges on green, and the lease becomes per worktree. The precedes graph already says which tasks are independent. This is a Seldon change and is registered there.

**DN-013-R4.** The suite runs under `pytest-xdist` by default, and the gate on a task whose write set touches no rule, collector or scoring code is `gate-fast`, with `gate-full` once per day on main. Prior art: CI test tiering, the same direction DN-043 takes for Squiddy.

**Implements:** R2 and R4 in `2026-10-07_parallel_hosts_and_fast_gate.md` (this repository); R3 as a Seldon task, written by the next Seldon session.

## 3. Assembled text is not prose (the writing defect)

**Defect.** The deck and the brief pack were built under the rule that no sentence may appear that is not in a record file. The output reads as assertion, qualifier, assertion, qualifier, with nothing carrying one thought into the next. The operator rejected the long-report-as-slides on 2026-10-02 and the same mechanism would produce the same text again.

**DN-013-R5.** The concise report (three to five pages, or what the argument needs; no page cap) is written as prose, by a model, from the evidence map and the record, in a technical register that stays readable. Then every claim in it is checked against the map, and a claim the map does not support is cut or marked. Checked, not assembled. The operator writes the summary himself from the report; nothing is dictated and Desktop drafts no summary. This amends DN-009 d1 (the destination keeps the evidence map and the report, drops the one-page summary and the four-to-six page brief as Desktop deliverables).

**DN-013-R6.** A prose gate for the report, run before the fresh-reader gate: no em dashes; no sentence pattern "statement, short clarification" repeated more than twice in a section (measured by sentence length alternation and clause count, with the measure named in the task); no word of the operator's banned list; repeated-word warnings reported, not silenced.

**Implements:** `2026-10-07_concise_report_prose.md`, after R1's task has landed and the numbers are frozen.

## 4. Order of work

1. Seed known locations and split discoverability (R1). Freezes the numbers.
2. Parallel hosts and the fast gate (R2, R4), alongside 1; independent.
3. The concise report as prose (R5, R6), after 1.
4. DCAT-004, independent, runs when the STOP file is removed.
5. Seldon: worktree-per-task dispatch (R3), next Seldon session.

## Prior art

- **External.** Heritrix and Nutch politeness-per-host with cross-host parallelism; pytest-xdist; git worktrees as the standard for parallel agent sessions on one repository; CI test tiering (fast on every change, full on a schedule).
- **Internal precedent.** DN-012 d1 to d3 (the absence rules, which this note corrects at the declared layer); DN-009 d1 and d2 (destination and evidence map, amended here); the audit's C-14 (the Census API case); DN-006 (the dispatcher's one-lease design, whose reason, one working tree, R3 removes); Squiddy DN-043's direction on test tiering, not yet written.
