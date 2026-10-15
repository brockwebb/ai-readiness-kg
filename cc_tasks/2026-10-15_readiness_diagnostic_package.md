# CC Task: the readiness diagnostic package: the instrument entries move into the graph, and the preface, dictionary, rung-two listing and deck are rendered from it for the 2026-10-16 working group

**Date:** 2026-10-15
**Project:** ai-readiness-kg
**Authored by:** Desktop session.
**Implements:** `docs/design/2026-10-15_DN-015_instrument_specification.md` (DN-015: the checks, the four states), DN-005 §2.1.
**Amended by:** `docs/design/2026-10-15_DN-016_readiness_diagnostic_package_and_client_ladder.md` (DN-016), the governing note for this task: the vocabulary, the client ladder, the entries into the graph, the formats, the review. It is untracked and unverified at registration because the Desktop MCP's `seldon_prior_art_search` and `seldon_prior_art_verify` both fail at import (`module 'seldon.core.prior_art' has no attribute 'calling_project'`, 2026-10-15, a seldon defect); Step 0 verifies it from the CLI before anything else, and the task stops if that fails. Where DN-016 and DN-015 differ on rendered vocabulary, DN-016 governs; on measurement, DN-015 governs and DN-016 changes nothing.
**Builds on:** task db464d5f (the audit) and its RESULT: the sixteen `assessment/instrument/RULE-*.yaml` entries, `scripts/instrument.py`, `scripts/apply_instrument_state.py`, `reports/instrument/INSTRUMENT.md`. Task 8f8861ce: the Tool and Precondition nodes. Task c53d0ee6: the scan frame, sixteen bodies plus three flagships. `scripts/dcat_brief_build.py` as the build pattern (`render_report`, hash recorded in the build report).
**Framework layer served (DN-005 §5 rule 1):** the validity layer: the instrument's own content becomes graph state; the package is a view of it (§2.1).
**Fulfils:** its own ResearchTask. Launched by the dispatcher.
**After:** none
**Sequencing note:** this task runs before `2026-10-15_executive_summary_v4_instrument_page_two.md` (98ed1dd1); both write the framework record and the vocabulary file. The edge is recorded on the graph by the Desktop session with `seldon_task_precede`; it is stated here for the reader only.
**Model:** author
**Spend:** est. 3M tokens. The session writes (role `author`, Opus 4.8); the hostile reader is Opus 5.5 (Step 0 says how the role is chosen), at most two rounds per entry; the checker (role `critic`) runs the planted and unsupported checks on the preface.
**Parts:** A 0.25, B 0.10, C 0.35, D 0.20, E 0.10.
**Part map:** A is the entries into the graph; B is the vocabulary and the roster and rung-two queries; C is the plain-language fields and the hostile reading; D is the two renders; E is the gate.
**Network:** none.

**HEADLESS NOTICE.** No next turn. Poll every detached command to its EXIT line.

**Deadline:** the operator presents on 2026-10-16 (morning, America/New_York). If the task cannot finish, Parts A and B finish first, the RESULT says where it stopped, and the operator renders by hand from the graph. A partial RESULT with no placeholder beats a finished one tomorrow afternoon.

## Step 0

If this task is `in_progress` from an earlier dispatch (a `dispatch_launched` stamp older than this session's), stop. Confirm the served model equals `seldon models resolve author`; a mismatch stops the task as `model_substituted`.

DN-016 before any other step: its `## Prior art` is prose. Run `seldon prior-art search` for each entry (library and internal), replace the prose with receipts or a recorded failed search, run `seldon prior-art verify` on the note, commit path-scoped through the hooks. A verdict other than PASS stops the task (AD-036-R4). If the CLI fails the same way the MCP did, stop, quote the traceback, and report: the defect is then confirmed in the CLI and belongs in the seldon repo. Record verdict and commit in the RESULT.

The hostile reader: run `seldon models resolve judge` and `seldon models resolve critic` and quote both. Use whichever resolves to Opus 5.5 for the hostile reading. If neither does, use `judge`, and record the pin in the RESULT as a premise found wrong; do not substitute by hand.

Verify premises against the graph and quote the queries: db464d5f, 8f8861ce, c53d0ee6 `completed`; 16 MeasurementSpecs carry `instrument_state`; `get_overview` reports `projection_gate.status: green`. A wrong premise is reported, never reconciled silently.

## Part A: the entries into the graph (DN-016 ruling 4)

Extend `scripts/apply_instrument_state.py` (or a sibling that reuses its loader) so every reader-facing field of each `RULE-*.yaml` entry is written to its MeasurementSpec through `scripts/framework_writeback.py::save`: the hypothesis, where we look (seeded location and product page, as the roster names them), what the client does, the pass, partial, fail and not-measured definitions, the quoted requirements with their source ids, the state, and the plain name and fix line already there. For every source that is a corpus id, write an `evidenced_by` edge from the MeasurementSpec to that Document; a receipted URL that is not a corpus id is recorded as a property, not an edge, and listed in the RESULT. Projection follows the write-back, then `tests/test_framework_projection_roundtrip.py`.

- check: `framework_writeback.save` reports nodes changed and nothing dropped; the `framework_writeback` event carries the delta; quote both.
- check: a labelled Cypher query returns 16 MeasurementSpecs with every field above non-empty, and the count of `evidenced_by` edges to Documents; quote it.
- check: `scripts/instrument.py check` still reports 0 problems, and the planted false quote still fails.
- check: `get_overview` reports `projection_gate.status: green` after projection; quote it.
- check: `reports/instrument/INSTRUMENT.md` regenerated from the graph is identical in content to the one generated from YAML, or the RESULT lists every difference. This is the proof the YAML and the graph say the same thing.

## Part B: vocabulary, roster, rung two

1. Vocabulary (ruling 1): add the rendered terms to the vocabulary file (`summary_grid_vocab.yaml` or the file the build reads; find it through the graph, not by guess): the run is a *readiness diagnostic*, the unit a *check*, the actor the *public client*, the states as DN-015 names them with *not measured* and its three reasons in plain words. A test asserts that no rendered product contains "scan", "probe", "crawl" or "audit" as a word; code paths are exempt.
2. Roster: a query over the scan frame returning body, surface, seeded locations, in the order the frame holds them. Three flagships marked as such.
3. Rung-two listing (ruling 3): a query over Tool and Precondition nodes returning, per surface, whether a key is required and whether registration is open to the public, with the node that says so. Where the record is silent the cell says "to be confirmed"; nothing is inferred from the agency's reputation or from a page not in the record.

- check: the vocabulary test passes on every rendered product; quote it.
- check: the roster query's row count equals the frame's body count plus flagships; quote it.
- check: every rung-two row cites a node id or says "to be confirmed"; a script exits non-zero otherwise.

## Part C: the plain-language fields and the hostile reading (ruling 6)

For each of the sixteen entries, the author writes the fields DN-016 §3 lists that the YAML does not yet carry in plain language: the question in one sentence; what the client does, as a person would describe one request; why it matters, naming the source in plain words or stating "this is the project's rule"; who else runs this check, where the audit found one; what rung two changes. Written back through Part A's path, never into the render.

The preface (DN-016 §3, page one) is written to `reports/diagnostic/preface_source.yaml`: the exact user-agent string read from the harness configuration (quote the file and line); one request per check per surface; the standing rate limit as the harness enforces it; robots honored, with the count of surfaces not fetched on the cycle of record as a result token; what the client never does; the four states; the two rungs; the one sentence on what the diagnostic is not. Every number is a `{{result:...}}` token.

The hostile reader reads every entry and the preface as the most hostile agency representative in the room, with three questions: what would I object to; what word would I not understand; what would I say we were secretly doing. Round two only after round one raised an objection. An entry whose round-two objection matches round one is rewritten by the author and read a third time; a third match is recorded, not rewritten again. Every objection and every rewrite goes in the RESULT, verbatim, so the operator walks in having heard the room.

The planted-sentence and unsupported-sentence checks (role `critic`) run on the preface as they ran on the summary.

- check: every entry's new fields are non-empty in the graph after write-back; quote the query.
- check: the text check word list (tier letters, rule and indicator codes) returns zero findings on the preface and the dictionary; quote it.
- judgment: the hostile reader's last round on each entry, one line each.
- check: the preface's user-agent string equals the one the harness sends; a test compares the rendered string to the configuration value.

## Part D: the renders (ruling 5)

One build script, `scripts/diagnostic_package_build.py`, patterned on `scripts/dcat_brief_build.py`, writes from the graph (never from YAML, never from a prior render) a Markdown source and from it both `reports/diagnostic/READINESS_DIAGNOSTIC.docx` and `reports/diagnostic/READINESS_DIAGNOSTIC.pptx`. No PDF. The Markdown's sha256 is recorded in the build report beside each product.

Word: preface; dictionary, one entry per page or half page, the nine fields in DN-016's order as labelled lines, A4 and A11 marked as declarations read but not scored, A12 as under review; roster; rung-two listing; what comes next (the access check and the rung-two cycle, named as specified and not yet run). Calibri.

PowerPoint: the preface as two slides; the roster as one; the ladder as one; the sixteen checks as one slide per criterion group, each check as plain name, the one-sentence question, and why it matters; the rung-two listing as one; what comes next as one. Calibri, white background, black or grey text, orange accent only, no other colour. Speaker notes on each check slide carry the where-we-look and pass definition so the operator does not read them off the slide.

- check: both files open (python-docx and python-pptx round-trip load); slide count and page count quoted.
- check: a font and colour test over the .pptx finds Calibri only and no colour outside black, greys and the one orange; quote it.
- check: the vocabulary test from Part B passes on the Markdown source, the .docx text and the .pptx text.
- check: no digit in either product outside result tokens, roster counts and dates.

## Part E: gate

`make gate-task` (the write set touches the framework record), `seldon verify`, protected-paths diff showing only the authorized write-back and its event. Register the build script, the preface source and both products as artifacts.

- check: gate line with passed, skipped, xfailed, deselected and wall clock; `seldon verify` EXIT=0; log paths.

## RESULT

Under 50 lines: served model and the hostile reader's resolved role; Step 0 verdict and commit; Part A's write-back delta, edge count and the INSTRUMENT.md diff verdict; vocabulary test; roster and rung-two row counts and how many "to be confirmed"; the hostile reader's objections and rewrites, verbatim, grouped by entry; page and slide counts; font test; gates with log paths; premises found wrong; where it stopped, if it stopped. Then `seldon cc complete`, commit, push. The operator opens `reports/diagnostic/READINESS_DIAGNOSTIC.pptx` first.
