# CC Task: executive summary v4: page two is the instrument with the grid beneath it, page one carries FAIR lineage, and A6 gets its second hearing

**Date:** 2026-10-15
**Project:** ai-readiness-kg
**Authored by:** Desktop session.
**Implements:** `docs/design/2026-10-12_DN-014_executive_summary_brief.md` (DN-014), its ADDENDUM 01, `docs/design/2026-10-15_DN-015_instrument_specification.md` (DN-015), DN-010, DN-001.
**Amended by:** DN-014 ADDENDUM 02 (dated 2026-10-15, beside DN-014); where it and ADDENDUM 01 differ on page two, ADDENDUM 02 governs. It is untracked and unverified at registration; Step 0 verifies it before anything else, and the task stops if that fails.
**Resolves:** Issue bcd28ee0 (page one: FAIR lineage, the three added criteria named, the definition set apart, the ruled-out line removed).
**Builds on:** task ba40cb29 (v3) and its RESULT: the vocabulary, the plain names in the record, `scripts/summary_grid.py`, the build script and the checks all stand. Task db464d5f (the audit) and its RESULT: the sixteen instrument entries, `scripts/instrument.py`, `scripts/apply_instrument_state.py`, `reports/instrument/PAGE_TWO_VERDICT.md` as the worked example of the four-state rule.
**Framework layer served (DN-005 §5 rule 1):** §2.1, the summary as a view of the framework; the instrument states shown on page two are the validity layer's own.
**Fulfils:** its own ResearchTask. Launched by the dispatcher.
**After:** none
**Model:** author
**Spend:** est. 2.5M tokens. The session writes (role `author`); Fable reads (role `judge`): the A6 entry under DN-015 §7 at most two rounds, the prose at most three rounds; the checker (role `critic`) runs the planted and unsupported checks.
**Parts:** A 0.15, B 0.15, C 0.30, D 0.25, E 0.15.
**Part map:** A is A6's re-specification; B is the Results; C is page two; D is page one and the USAFacts note; E is the build and the gate.
**Network:** none. A6's passages are quoted from the receipted source text already on disk (`assessment/instrument/standards_receipts.yaml` and the fetched bodies the audit verified quotes against). If a passage A6 needs is not in that text, A6 stays `invalid` and the RESULT says which passage was missing; nothing is fetched.

**HEADLESS NOTICE.** No next turn. Poll every detached command to its EXIT line.

## Step 0

If this task is `in_progress` from an earlier dispatch (a `dispatch_launched` stamp older than this session's), stop. Confirm the served model equals `seldon models resolve author`; a mismatch stops the task as `model_substituted`.

Then ADDENDUM 02, before any other step: its `## Prior art` section is prose. Run `seldon prior-art search` for each entry (library and internal), replace the prose entries with the receipts or a recorded failed search, run `seldon prior-art verify` on the file, and commit it path-scoped through the hooks. If the verdict is not PASS, stop and report the verdict; nothing below runs on an unverified note (AD-036-R4). Record the verdict and the commit in the RESULT.

Then verify this task's premises against the graph and quote the queries: db464d5f and ba40cb29 `completed`; Issue bcd28ee0 `open`; `get_overview` reports `projection_gate.status: green` before any write-back. Any premise found wrong is reported in the RESULT, never reconciled silently.

## Part A: A6 re-specified (audit RESULT premise 7)

Rewrite `assessment/instrument/RULE-A6*.yaml` so every attributed requirement carries a verbatim passage from the receipted source text, including the two the reader faulted: the "JSON-LD preferred" attribution and `name` as a required property. A requirement with no passage behind it in the source on disk is dropped from the entry, not kept unquoted. `scripts/instrument.py check` must report 0 problems. Then Fable reads the entry under DN-015 §7 (q1 source, q2 misreading, q3 undefined terms), round 2 only after a q1 no. The outcome sets A6's state: a q1 yes in its last round is `specified`; a second no keeps `invalid`.

Write the state to the record through `scripts/apply_instrument_state.py` and `framework_writeback.save` (never a hand edit), then rebuild the projection and run `tests/test_framework_projection_roundtrip.py`. The grid's column count follows from this: five if A6 is `specified`, four if not.

- check: `scripts/instrument.py check` quotes 0 problems; quote it.
- check: the planted false quote still fails the check; quote the run.
- judgment: Fable's rounds on A6, one line each, reasons verbatim into `reports/instrument/run/verify.json`.
- check: `get_overview` reports `projection_gate.status: green` after the write-back; quote it.

## Part B: the numbers become Results

Before any prose cites them, register through `seldon result register`, each linked to its generating script and the cycle of record: the count of grid checks (thirteen); the count `specified`, `invalid` and `project_defined` after Part A; the count of cells whose state changed under the four-state rule, and the cells by state in the reduced grid (could not measure, fail, pass, partial); the not-measured cells by reason class (access denied, absence unconfirmed, scanner held by robots); the bodies with every cell unmeasured. `scripts/summary_grid.py` writes these from `reports/summary/grid.json` in the same run that writes the grid, so the Result and the grid come from one computation.

- check: every Result above exists in the graph with a `generated_by` edge to the script and a `computed_from` edge to the cycle of record; a labelled Cypher query lists them; quote it.
- check: the audit RESULT's Part D numbers (4 of 13; 86 of 208; 64 cells 41/15/8) are reproduced by the script when A6 is held `invalid`, as a regression test; quote it. If Part A set A6 `specified`, the test also runs the five-column case and both are quoted.

## Part C: page two (ADDENDUM 02 §3)

1. Header line: the anonymous, keyless client, the same for every body.
2. The instrument table, compressed to the thirteen grid checks plus A4 and A11-declared marked excluded as declarations: plain name, state, source in one phrase or "the project's", with a one-line pointer to `reports/instrument/INSTRUMENT.pdf`. The table is generated from the `RULE-*.yaml` entries by the build, never typed.
3. The grid over the `specified` checks only, under ADDENDUM 01's pass/fail/partial rules and DN-015's fourth state. A grey cell carries its reason class as a glyph. Legend names the three reason classes with their counts as result tokens. Fix lines under the columns as in v3.
4. Row labels: "N data products", never "N pages". Sixteen rows, alphabetical.
5. Landscape page if it needs one. Still one body page.

- check: a round-trip test recomputes ten random cells from the matrices by hand and matches `grid.json`, including at least three grey cells and their reason class.
- check: every grid cell carries at least one locator; `seldon verify` accepts them.
- check: the table's states equal `instrument_state` on the MeasurementSpecs in the record; a script compares and exits non-zero on a mismatch; quote it.
- check: no digit appears on page two outside row labels' product counts, result tokens and the footnote's date.

## Part D: page one (Issue bcd28ee0) and the USAFacts note

Rewrite page one in `reports/summary/summary_source.yaml`, every item of the Issue:

1. A set-apart SI readiness definition at the top of page one, anchored to FAIR's stated purpose (machines find, access, interoperate and reuse with minimal human intervention), which is also the operator's "machine as first-class user".
2. Lineage stated as the record states it: FAIR is the base; USAFacts' standards apply it to published statistics for a public audience and add accuracy and understandability; this work keeps that structure and adds three criteria. The sentence that named USAFacts' four qualities as the base is gone.
3. The three added criteria named in plain words: whether the publisher checks and corrects what machines actually get (crit:E); how releases are versioned and announced (crit:F); what is particular to federal statistical products (crit:G).
4. "we meet an SI problem with SI" removed, and nothing of its kind written in its place.
5. The "what we found" paragraph is written from Part B's Results as tokens: the finding is what can be measured and what the measured cells show, in that order.

The USAFacts note (`reports/summary/usafacts_note.md` or wherever e2c4e125 wrote it; find it through the graph) is re-read against the plain names now in the record and states, from the document, whether USAFacts defines levels of progression. Edit through `seldon paper fix` or a tracked rebuild, never a hand edit of a tracked file.

Fable reads page one as in v3 with the fifth question: name every term a CIO new to SI would not know; a term named in two rounds is replaced. The planted-sentence and unsupported-sentence checks run as before, with the lineage sentences in the unsupported check's scope: each must resolve to a corpus document id (wilkinson-2016-fair-guiding-principles, usafacts-ai-ready-data-guide) or a record node.

- check: the text check word list (tier letters, rule and indicator codes) returns zero findings on both pages; quote its output.
- check: every lineage sentence resolves; quote the resolver's output.
- judgment: Fable's last round says the 30-second bullets can be said from page one alone and names no unknown term. Quote it.
- check: the USAFacts note's answer on levels of progression quotes the passage it rests on, or says the document is silent.

## Part E: build and gate

`reports/summary/SUMMARY.md` and `SUMMARY.pdf` rebuilt by the writing script, the PDF by the same script (CLAUDE.md, reports rule). Body: page one prose, page two instrument and grid, exactly two pages; sources after. Keep the v3 output as `reports/summary/v3/` for the record.

- check: pypdf body page count is 2; quote.
- check: `make gate-task` (passed, skipped, xfailed, deselected, wall clock), `seldon verify`, protected-paths diff showing only the authorized write-back if Part A changed the record.
- check: Issue bcd28ee0 closed with a note naming this task, only after Part D's checks pass.

## RESULT

Under 45 lines: served model; Step 0 verdict and commit; A6's rounds and its final state; the column count; the Results registered (ids and values); the grid's state counts and reason-class counts; the bodies fully unmeasured; Fable's prose rounds one line each; page count; text check; gates with log paths; premises found wrong. Then `seldon cc complete`, commit, push. The operator reads `reports/summary/SUMMARY.pdf`, with `reports/instrument/INSTRUMENT.pdf` and `PAGE_TWO_VERDICT.pdf` beside it.
