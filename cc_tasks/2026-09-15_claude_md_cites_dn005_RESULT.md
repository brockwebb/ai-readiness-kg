# RESULT — the bootloader states the goal, and one stale task is closed on the graph

**Task:** `cc_tasks/2026-09-15_claude_md_cites_dn005.md`, implementing DN-005 §6
(`docs/design/2026-09-15_DN-005_reorientation_the_framework_is_the_goal.md`).
**Framework layer served (DN-005 §5 rule 1):** none. A hygiene task, and it says so.
**No addendum exists** — `cc_tasks/2026-09-15_claude_md_cites_dn005_ADDENDUM*.md` globbed
before starting and again before §3, both times `no matches found`
(`logs/cmd_addendum_glob_start.log`, `logs/cmd_addendum_glob_pre_s3.log`).
**Date:** 2026-09-15. **Spend: zero model calls. Network: none** — no host was contacted, no
event was written to the append-only log, no Result moved, and no payload was read. The only
remote operation is the `git push` §4 orders.

**Ran after `cc_tasks/2026-09-14_standing_guards.md` pushed** (`2431510`), as its SEQUENCING
line requires. That task turned out not to touch `CLAUDE.md` at all, so the stated collision
never materialised; the ordering was still the right call, since it could not be known in
advance.

## THE GATE: PASS

| clause (§3) | result | log |
|---|---|---|
| decision 3 — the after-Cypher shows `superseded` with the edge | **PASS** — `proposed` → `superseded`, `SUPERSEDED_BY` → `95911824`, quoted in §1 | `logs/cmd_after_cypher.log` |
| `make gate-fast` (detached, logged, polled to EXIT) | **PASS — 2,180 passed, 17 skipped, 25 deselected, 12 xfailed, 417.19 s (6:57)** | `logs/cmd_gate_fast.log` |
| `gate-task` not owed | **correct, and checked rather than assumed** — see §3 | — |
| `seldon verify` | **PASS — all checks passed** | `logs/cmd_verify.log` |
| protected paths | **PASS** — `CLAUDE.md +3 −0`, nothing else in the tree, both insertions carry what decisions 1 and 2 require | `logs/cmd_protected.log` |

Every log carries its own `EXIT=0` and all of them were written before this file was.

## 1. Decision 3: `eaa47eb3`, before and after

**Before** (`logs/cmd_before_cypher.log`), taken before the CLI was invoked:

```json
{
 "id": "eaa47eb3-63d6-4fca-94db-230c218d18bd",
 "name": "cited documents metadata",
 "state": "proposed",
 "source_file": "cc_tasks/2026-09-12_cited_documents_metadata.md",
 "created_by": "desktop",
 "edges": []
}
```

and a second query for every outgoing relationship of that node returned **nothing at all**.

**The command** (`logs/cmd_supersede.log`), the Seldon CLI's own, not the MCP:

```
seldon task supersede eaa47eb3-63d6-4fca-94db-230c218d18bd \
  --reason "stopped at §1; work completed by 2026-09-12_cited_documents_metadata_2.md (95911824)" \
  --superseded-by 95911824-dc0d-4c0c-ad9c-e49f39806575

Updated Task: eaa47eb3...
  state: proposed → superseded
  reason: stopped at §1; work completed by 2026-09-12_cited_documents_metadata_2.md (95911824)
  superseded_by: 95911824-dc0d-4c0c-ad9c-e49f39806575
EXIT=0
```

**After** (`logs/cmd_after_cypher.log`), the same query:

```json
{
 "id": "eaa47eb3-63d6-4fca-94db-230c218d18bd",
 "name": "cited documents metadata",
 "state": "superseded",
 "source_file": "cc_tasks/2026-09-12_cited_documents_metadata.md",
 "created_by": "desktop",
 "edges": [
  {
   "type": "SUPERSEDED_BY",
   "target": "95911824-dc0d-4c0c-ad9c-e49f39806575",
   "target_name": "cited documents metadata 2"
  }
 ]
}
```

and the relationship query, which returned nothing before:

```
{'t': 'SUPERSEDED_BY', 'l': ['Artifact', 'ResearchTask'],
 'id': '95911824-dc0d-4c0c-ad9c-e49f39806575', 'n': 'cited documents metadata 2'}
```

Every property on the node afterwards, so the reason is visible where it actually landed:

```json
{
 "state": "superseded",
 "terminal_reason": "stopped at §1; work completed by 2026-09-12_cited_documents_metadata_2.md (95911824)",
 "updated_at": "2026-09-15T11:41:06.428739+00:00",
 "authority": "accepted",
 "created_at": "2026-09-12T20:00:33.258567+00:00"
}
```

The `SUPERSEDED_BY` edge carries `created_at: 2026-09-15T11:41:06.444774Z` and nothing else.
`95911824` is untouched: still `completed`, `updated_at 2026-09-13T02:30:24.808642+00:00`,
which is the completion timestamp the task file cites. It is now one of **40** superseded
ResearchTasks in the graph.

## 2. Decisions 1 and 2: what went into `CLAUDE.md`

Three lines added, none removed, nothing else in the file moved — asserted by the
protected-paths check as an exact `+3 −0`, because a diff that only counts insertions would not
notice a paragraph being rewritten in place.

**Decision 1**, inserted as the first paragraph of "What this is", with the paragraph that used
to open the section left verbatim below it:

> **The goal is the framework.** An AI-readiness framework for federal statistical publishers:
> a way to rate and score, quantitatively and qualitatively, whether the public and the tools
> the public now uses can reach, understand and use the data they paid for
> (`docs/design/2026-09-15_DN-005_reorientation_the_framework_is_the_goal.md` §1). Everything
> in this repository is a level of that framework, a measurement of it, a view of it, or a
> demonstration of it. The knowledge graph described in the next paragraph is the framework's
> **validity layer**; **L0** is its most basic level — the host-level checks, and the one step
> with cold, re-derivable data behind it today. The L0 report, the site and the January ICSP
> briefing are views of the framework and evidence under it, never the product. DN-005 is the
> standing map: read it before authoring or executing anything, because naming the most recent
> artifact as the goal is the error it exists to stop.

The sentence of purpose is DN-005 §1's own, quoted rather than paraphrased. The last sentence
is DN-005 §5 rule 4 turned outward at the reader: the note exists because two direction errors
were made in one session and both were the same error, and a bootloader that cited the map
without saying what it is for would be read as a reference and not as an instruction.

**Decision 2**, the new first bullet of "Where to read first", above `docs/design_decisions.md`:

> - `docs/design/2026-09-15_DN-005_reorientation_the_framework_is_the_goal.md` — the standing
>   map every task cites.

The protected-paths check asserts both insertions by content, not only by line count: that the
first paragraph of "What this is" cites DN-005 by path and names the framework, the validity
layer and L0; that the original opening paragraph survives verbatim after it; and that the
first bullet of "Where to read first" is the DN-005 line carrying the required phrase.

## 3. Why `gate-task` is not owed, checked rather than asserted

`gate-task` is `gate-fast` plus the re-derivation of every stored payload, and CLAUDE.md §"Suite
tiers" owes it "whenever the task could have touched a stored payload". This task edits one
markdown file that no payload, rule, params file or engine reads. Two things make that a fact
rather than a plausible reading:

* **Nothing in the code reads `CLAUDE.md`'s bytes.** Every reference to it under `tests/` and
  `assessment/` is prose — a docstring in `consumers.py`, two error messages in
  `scan/run.py` citing §11, one assertion message in `test_scan_run_2.py`. No file is opened.
* **The extraction path is hermetic by construction.** `model_stub.py` runs `claude -p` from an
  empty temporary cwd precisely so the model does not load the project `CLAUDE.md`
  (root-caused 2026-07-09, recorded in CLAUDE.md's own "Extraction runtime quirk"). A change to
  this file cannot reach a model call, let alone a stored payload.

`gate-fast` ran anyway and passed at 2,180 — the same count the previous task's `gate-task`
reported for its fast tier, which is the other half of the claim: the edit moved nothing.

## 4. Every premise wrong

**(a) The task's premises all held.** Unusually, and it is worth saying rather than leaving as
an absence. `eaa47eb3` really was `proposed` with no outgoing edge of any kind, so the Desktop's
two `seldon_task_supersede` MCP attempts on 2026-09-15 really did time out **without writing** —
a partial write would have left a state change without an edge, or an edge without a state
change, and there was neither. `95911824` really is `completed` at the cited timestamp. The
`CLAUDE.md` anchors were where the task said. The standing_guards task really had pushed.

**(b) The edge is `SUPERSEDED_BY`, not `superseded_by`.** The task file and the CLI's own
`--superseded-by` flag and success line all spell it lower case; the relationship type written
into Neo4j is upper case, as every relationship type in this graph is. A verification query
written from the task file's spelling alone returns nothing and reads exactly like a failed
write. The before/after queries here match either spelling for that reason.

**(c) The reason is on `terminal_reason`, and this session's first query looked for
`superseded_reason`.** The before-query asked for a property of that name, got `null`, and would
have gone on reporting `null` after the write too — it did, in the first after-query, which is
why a second query printing **every** property on the node is in §1 and in the log. Guessing a
property name from the CLI's output line is the same defect as guessing a relationship type from
it. The protected-paths check reads `terminal_reason`.

**(d) The "zero edits" clause and this task's own gate instrument.** "Zero edits to: anything
other than `CLAUDE.md` and the graph event for decision 3. No code, no tests, no docs" — and §3
orders a protected-paths diff, which in this repository is a committed
`scripts/check_protected_*.sh` (thirteen of them precede this one). Taking "no code" to forbid
it would forbid the gate the same task orders. Read as it must be — the clause governs the
PROJECT's substance, the way it does not forbid the RESULT file §4 orders — the task's own
execution artifacts sit outside it. `scripts/check_protected_claude_md_dn005.sh` is that
artifact and is named in the check's own declared-changes list, so the reading is on the face of
the diff rather than only here.

**(e) This check is a whitelist, and that is a departure worth naming.** The other twelve list
what may not move. With an allowed set of four paths, a blacklist of everything else would be a
list nobody could read and would miss whatever it forgot; this one refuses every path in
`git status` that is not one of the four. It also strips the two-character status prefix before
matching, which is the defect found in `check_protected_standing_guards.sh` yesterday — that
clause answered differently before and after `git add`.

## 5. Logs

```
logs/cmd_addendum_glob_start.log   addendum glob, before starting     no matches
logs/cmd_addendum_glob_pre_s3.log  addendum glob, before §3           no matches
logs/cmd_before_cypher.log         eaa47eb3 BEFORE: proposed, 0 edges
logs/cmd_supersede.log             seldon task supersede              EXIT=0
logs/cmd_after_cypher.log          eaa47eb3 AFTER: superseded + edge, and every property
logs/cmd_gate_fast.log             make gate-fast, detached, polled   EXIT=0  2,180 passed / 417.19 s
logs/cmd_verify.log                seldon verify                      EXIT=0  all checks passed
logs/cmd_protected.log             protected paths                    EXIT=0  PASS, CLAUDE.md +3 −0
```

## 6. Open, for the next OODA

1. **DN-005 is now cited from the bootloader and is binding on task authorship** (§5 rule 1:
   every task file names the framework layer it advances, or says it is hygiene). This task is
   the first to carry that header. Nothing enforces it — a task file that names no layer is
   caught by a reader, not by a gate. Whether that should become a check is a question for the
   dispatcher task (`6ee71737`), not for this one.
2. **Thirty-nine other superseded ResearchTasks, and no audit of the open ones.** `eaa47eb3` was
   found by hand. DN-005 §4's list of continuing threads names roughly twenty open task ids; how
   many of them are, like this one, already fulfilled by a completed successor is not known and
   was not asked here.
3. **The MCP `seldon_task_supersede` path timed out twice and the CLI succeeded immediately.**
   The CLI is the route that works today; whether the MCP tool has a real defect or the two
   timeouts were transient is untested, and nothing here tested it.
