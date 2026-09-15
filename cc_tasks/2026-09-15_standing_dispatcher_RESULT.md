# RESULT — the standing dispatcher: a registered task with a clean gate no longer waits for a person

**Task:** `cc_tasks/2026-09-15_standing_dispatcher.md`, implementing
`docs/design/2026-09-15_DN-006_standing_dispatcher.md` decisions 1 to 7, 9 and 10.
**Addendum:** `cc_tasks/2026-09-15_standing_dispatcher_ADDENDUM_01.md` **exists and amends**
decisions 2 and 3 (the third required header, and the CLAUDE.md sentence stating the
three-header rule). Globbed before starting and again before §5
(`logs/sd_addendum_glob_start.log`, `logs/sd_addendum_glob_pre_s5.log`), both times the same
one file. It amends; it does not supersede; the base task was executed.
**Framework layer served (DN-005 §5 rule 1):** §2.2 Tier M.
**Date:** 2026-09-15. **Spend: zero model calls. Network: none** — the stub CC in the tests is a
shell script, `dispatch.enabled` stays `false`, no host was contacted, no `ANTHROPIC_API_KEY`
was set at any point, and **the dispatcher wrote not one event**. The only remote operations are
the two `git push`es §6 orders.

## THE GATE: PASS

| clause (§5) | result | log |
|---|---|---|
| Seldon suite green on the merged commit | **PASS — 1,787 passed, 146.82 s** on `dfae15d` | `logs/sd_seldon_suite2.log` |
| `make gate-fast` here (detached, logged, polled) | **PASS — 2,187 passed, 17 skipped, 25 deselected, 12 xfailed, 422.54 s (7:02)** | `logs/sd_gate_fast.log` |
| no payload touched, so `gate-task` is not owed | **correct** — this task writes no rule, no engine, no payload; `assessment/`, `state/`, `events/`, `kg/` are all untouched, asserted by the protected-paths diff | `logs/sd_protected.log` |
| `seldon verify` | **PASS — all checks passed** | `logs/sd_verify.log` |
| protected paths | **PASS** — `CLAUDE.md +2 −0`, `seldon.yaml` changed only by the new block, `controls.yaml` untouched, no `dispatch_*` event written | `logs/sd_protected.log` |
| §4's byte comparison | **PASS — BYTE-IDENTICAL: YES**, sha256 `f9f3da6e…` before and after the dry pass | `logs/sd_dry_pass.log` |
| the two `CLAUDE.md` sentences present | **PASS**, asserted by the protected-paths check and by `test_claude_md_carries_the_marker_rule_and_the_no_hand_dispatch_rule` | `logs/sd_protected.log` |

Every log carries its own `EXIT=0` and all of them were written before this file was.

## 1. Both commits

| repo | commit | what |
|---|---|---|
| `seldon` | **`b04335b`** | `feat: seldon dispatch — the standing dispatcher` (on `feat/standing-dispatcher`) |
| `seldon` | **`702ac32`** | `Merge feat/standing-dispatcher: seldon dispatch command group` → `main`, pushed |
| `seldon` | **`dfae15d`** | `fix: dispatch tree_state truncated the first dirty path` → `main`, pushed. §3 below |
| `ai-readiness-kg` | see §7 | this repo's configuration, plist, test, addendum and RESULT |

`pip install -e .` re-run here after the merge; `seldon dispatch --help` resolves and
`seldon.commands.dispatch` imports from `/Users/brock/GitHub/seldon/seldon/commands/dispatch.py`.
The task's decision 8 ("a task that ends on an unmerged branch is not complete") is satisfied:
nothing is left on the branch.

## 2. The exact `claude -p` invocation

```
claude -p "Read CLAUDE.md, then execute cc_tasks/<stem>.md. Glob and read all sibling <stem>_ADDENDUM*.md files before starting; an addendum can amend or SUPERSEDE the base task." --permission-mode bypassPermissions
```

with `cwd` = the project root, `stdout`+`stderr` to `logs/dispatch/<stem>.log`, `EXIT=<code>`
appended, and `ANTHROPIC_API_KEY`/`ANTHROPIC_AUTH_TOKEN` stripped from the child environment as
well as refused in the parent's.

Three things about it are decisions, not defaults:

* **The prompt is `CLAUDE.md`'s own dispatch line, verbatim**, formatted from the task's path.
  A dispatcher that reworded it would be sending a session a different instruction from the one
  an operator sends, and the difference would show up only in what the session did.
  `test_the_launch_command_is_the_protocol_sentence_with_the_permission_mode` asserts the string.
* **The working directory is the project root, so `CLAUDE.md` loads** — the exact inverse of
  `kg/extraction/model_stub.py`'s hermetic empty cwd, which exists so a JSON-only call cannot
  narrate. Here the narration is the point.
  `test_the_launch_runs_from_the_project_root_so_claude_md_loads` asserts it by having the stub
  print `pwd`.
* **`--permission-mode bypassPermissions` could not be derived from this repository**, which is
  §3 item (b) and DN-006 ADDENDUM_01 §3.

## 3. Step 0: the marker survey (decision 3)

34 `cc_tasks/*_ADDENDUM*.md` files surveyed (`logs/sd_marker_survey.log`). A bolded `Status`
field in the first ten lines is an established habit; base-task supersession has been expressed
**once**.

| addendum | the line that expressed supersession, if any | what it supersedes |
|---|---|---|
| `2026-09-01_harness_reconciliation_ADDENDUM-01.md` | `**Date:** 2026-09-01. **Status of base task: SUPERSEDED — DO NOT EXECUTE.**` | **the base task** — the only one |
| `2026-09-03_hygiene_sweep_post_g1_freeze_ADDENDUM-01.md` | `**Status:** AMENDS the base task. Does not supersede it. Base task + this addendum = the spec.` | nothing |
| `2026-09-04_extract_g1eval_17_and_rerun_ADDENDUM-01.md` | `**Status:** AMENDS. Resume, do not restart.` | nothing |
| `2026-09-04_extract_g1eval_17_and_rerun_ADDENDUM-02.md` | `**Status:** AMENDS ADDENDUM-01. Adds one zero-spend step after §3 (CQ rerun), before §4.` | a prior addendum |
| `2026-09-04_result_migration_completion_ADDENDUM-01.md` | `**Status:** AMENDS the base task.` | nothing |
| `2026-08-24_source_triage_ADDENDUM-02.md` | `**Supersedes the "operator drops the file" clause of ADDENDUM-01.**` | a clause of a prior addendum |
| `2026-08-26_overnight_burn_ADDENDUM-01.md` | `**Supersedes:** the clause "A FAIL is a finding for the morning…"` | a clause |
| `2026-08-26_overnight_burn_ADDENDUM-02.md` | `**Supersedes:** ADDENDUM-01's pilot precondition and every wall-clock stop…` | a prior addendum |
| `2026-08-26_overnight_burn_ADDENDUM-04.md` | `**Supersedes ADDENDUM-03 in full.**` | a prior addendum |
| `2026-08-27_chunked_pilot_ADDENDUM-03.md` | `**(b) ADDENDUM-01 §2.5 is superseded by DD-023 ERRATUM 2.**` (line 15) | a prior addendum's section |
| `2026-08-27_chunked_pilot_ADDENDUM-06.md` | `…supersedes ADDENDUM-05 §1.1 … and §1.3 …` | a prior addendum's sections |
| `2026-09-07_scan_run_2_ADDENDUM-01.md` | `…this addendum supersedes the base task's SEQUENCING from §3 onward…` (line 18) | a clause of the base task |
| `2026-09-08_scan_frame_fss_ADDENDUM-05.md` | `Supersedes ADDENDUM-02, -03, -04 and every Tier B clause.` (line 1) | prior addenda |
| `2026-09-10_corpus_noaa_esip_ADDENDUM_01.md` | `**Date:** 2026-09-10. Amends, does not supersede.` | nothing |
| `2026-09-13_ephemeral_provenance_ADDENDUM_1.md` | `**Date:** 2026-09-13. **Amends** the base task; does not supersede it.` | nothing |
| `2026-09-15_standing_dispatcher_ADDENDUM_01.md` | `**Date:** 2026-09-15. **Amends, does not supersede.**` | nothing |
| the other 18 | — | nothing |

**The finding: a partial convention, which is neither branch of decision 3.** The `**Status:**`
field exists and its verbs are upper case; base-task supersession has one instance and spells it
`**Status of base task:`. Eleven files carry `Supersedes…`, and **every one supersedes a prior
addendum or a clause, never the base task** — a matcher that read those as base-task
supersession would make eleven executable tasks undispatchable.

So: **`**Status:** SUPERSEDED` within the first ten lines is the marker from here on**, written
into `CLAUDE.md`; the matcher also accepts the one historical spelling, because the alternative
is a dispatcher that reads `2026-09-01_harness_reconciliation.md` — genuinely `superseded` on
the graph as `481b6994` — as executable, which is the one outcome c3 exists to prevent. The
regex is case-sensitive on `SUPERSEDED` (four of five Status lines say "Does not supersede it")
and **searches within** the line rather than anchoring to its start (every real Status line sits
after a `**Date:** …` on the same line, so an anchored pattern reads none of them — the first
version of the regex did exactly that and two tests caught it).

DN-006 ADDENDUM_01 §1 records the correction, as decision 3 requires.

## 4. §4's dry pass, quoted

```
seldon_events.jsonl sha256 BEFORE: f9f3da6efad20d487bd1c728bdd170e68e4d6561ed29cdc406ee197b5579b306

=== seldon dispatch once  (dispatch.enabled: false) ===
dispatch is disabled; nothing evaluated
ONCE_EXIT=0

=== seldon dispatch status ===
dispatch: enabled=False  branch=main (configured main)  dirty=True (7 path(s))
  stop file   : .seldon/DISPATCH_STOP absent
  standing band: 55,000,000 tokens  <- controls.yaml#spend.daily_tokens
  lease        : free
  claim        : none
  open tasks   : 23  candidates: 1  eligible: 0

  0128144c  proposed   NOT A CANDIDATE (no_source_file)
  … 21 more, all NOT A CANDIDATE (no_source_file) …
  e2885e86  proposed   ineligible on c7,c8  cc_tasks/2026-09-15_standing_dispatcher.md
      ok c1: {"state": "proposed", "source_file": "cc_tasks/2026-09-15_standing_dispatcher.md", "file_exists": true, "git_tracked": true}
      ok c2: {"predecessors": 1, "unsatisfied": []}
      ok c3: {"addenda": ["2026-09-15_standing_dispatcher_ADDENDUM_01.md"], "superseding": null}
      ok c4: {"spend_header": "zero model calls. The stub CC used by the tests is a shell script, not the CLI. **Network:** none.", "declared_tokens": 0, "standing_band": 55000000, "band_ref": "controls.yaml#spend.daily_tokens"}
      ok c5: {"network_header": "none."}
      ok c6: {"in_progress_claim": null, "lease_task": null, "lease_holder": null}
      NO c7: {"branch": "main", "configured_branch": "main", "dirty": true, "dirty_count": 7, "dirty_paths": ["CLAUDE.md", "seldon.yaml", "seldon_events.jsonl", "cc_tasks/2026-09-15_standing_dispatcher_ADDENDUM_01.md", "scripts/jobs/airkg_dispatch.sh", "scripts/jobs/com.brock.airkg-dispatch.plist", "tests/test_dispatch_config.py"]}
      NO c8: {"enabled": false, "stop_file": ".seldon/DISPATCH_STOP", "stop_file_present": false}
      ok c9: {"framework_layer": "§2.2 Tier M. The measured tier's cadence cannot be standing while its cycles wait on a pasted line."}
  f1da94c6  proposed   NOT A CANDIDATE (no_source_file)
  f6b24c9d  proposed   NOT A CANDIDATE (no_source_file)
  f9c5d054  proposed   NOT A CANDIDATE (no_source_file)
STATUS_EXIT=0

seldon_events.jsonl sha256 AFTER : f9f3da6efad20d487bd1c728bdd170e68e4d6561ed29cdc406ee197b5579b306
BYTE-IDENTICAL: YES
```

Full output in `logs/sd_dry_pass.log`. **Zero events written**, by sha256 identity and again by
the protected-paths check, which reads the log's new lines and asserts none is a `dispatch_*`
type.

## 5. Every premise wrong

**(a) §4's expected output is wrong in three ways, and all three are measurements the task
could not have had.**

1. **"every open task … not a candidate (no headers)".** 22 of the 23 are not candidates
   because they carry **no `source_file` at all** — they were created with `seldon task create`
   from a Desktop thread, never registered from a task file — so there is no file to read
   headers from. `status` says `no_source_file`, not `no_header:…`, so a reader is not sent
   looking for headers in a file that does not exist. DN-006 decision 2's closing paragraph
   pictures the 24 as files without headers; the opt-in works exactly as designed, the
   diagnostic differs. Recorded in DN-006 ADDENDUM_01 §4.
2. **"and `2026-09-15_claude_md_cites_dn005.md`".** That task is `completed` (`a5a046cf`,
   closed by the preceding CC session), so it is not open and does not appear at all.
3. **"both shown ineligible on c8".** This task's own file is ineligible on **c7 and c8** — the
   working tree is dirty with this task's own edits, which is the ordinary state of a checkout
   mid-task and exactly what c7 is for. A dispatcher that ran while a session was editing the
   tree is the condition decision 10 forbids by rule and c7 catches by measurement.

Also: **23 open tasks, not 24.** `6ee71737` became the 24th→23rd when §3 superseded it earlier
in this same run.

**(b) Decision 5's permission mode cannot be derived from this repository, and the reason is the
finding.** The task says to derive the non-interactive mode "from how this repo already runs
`claude -p` unattended". The one unattended invocation here is
`kg/extraction/model_stub.py`, and it runs `--allowed-tools ""` — an empty allowlist, **no tools
at all** — from a hermetic empty cwd. That is the deliberate opposite of a dispatched session's
needs and is evidence this repository has **never** run a tool-executing headless session. There
was nothing to derive. The value comes from the CLI's own interface instead
(`claude --permission-mode acceptEdits|auto|bypassPermissions|manual|dontAsk|plan`, claude
2.1.272): `bypassPermissions` is the one that does not prompt, and a headless session in a
prompting mode blocks forever on its first tool call having consumed a claim and produced
nothing. In `seldon.yaml` with that reasoning beside it, per decision 5, and in DN-006
ADDENDUM_01 §3.

**(c) `proposed -> in_progress` is not an edge on the ResearchTask state machine.** Decision 4
calls the claim "the `in_progress` transition" and decision 2's c1 admits `proposed` or
`accepted`. `seldon/domain/research.yaml` has `proposed: [accepted, rejected, superseded,
withdrawn]`. From `proposed` the claim is two transitions with the marker on the second, which
is the shape `walk_to_completed` already uses. The compare-and-set property is unchanged: a
failed first hop leaves the graph untouched, a failed second leaves the task `accepted` — an
open state the next pass re-evaluates — and **a failed transition launches nothing** either way.
DN-006 ADDENDUM_01 §2, and `test_the_claim_path_walks_proposed_through_accepted` asserts the
walk against the shipped state machine rather than against a copy of it.

**(d) Decision 2's cross-repo test had to be split.** "a test asserts the resolved value equals
what `kg/spend.py` reads" — `kg/spend.py` is this project's module and the Seldon suite has no
business importing it. The reference-resolution *mechanism* is tested in Seldon against a
fixture `controls.yaml`; the *equality* is tested here, in `tests/test_dispatch_config.py`,
against both real readers. Between them the claim is whole. The task's "Zero edits to" list does
not cover `tests/`, so adding a test file here is within scope.

**(e) The `Spend:` header of this very task parses to a value that spans two headers, and it is
right anyway.** `c4` reports `spend_header` as `"zero model calls. The stub CC used by the tests
is a shell script, not the CLI. **Network:** none."` — the two headers share a line, so the
first header's value runs to the end of it. `spend_tokens` finds `zero` and returns 0;
`network_declared_none` reads the `**Network:**` header separately and finds `none.`. Both
answers are correct and the raw value is ugly. Left as is: trimming a header value at the next
`**` would be a parser guessing at markdown structure, and the criteria vector's job is to show
what was read.

**(f) The one premise that held exactly.** Decision 7's log caps: `controls.yaml
jobs.biblio_resume` does declare `log_max_line_chars`, `log_max_run_bytes` and
`log_retention_days`, and the wrapper reads all three by reference.

## 6. The defect the dry pass found, which no amount of reading would have

**`tree_state` truncated the first dirty path.** `git status --porcelain` writes `XY PATH`, and
an unstaged modification is `" M path"`. The first version called `.strip()` on the whole blob,
which removes the leading space of the **first line only**; `ln[3:]` then ate one character of
exactly that one path and of no other. The live criteria vector reported `"LAUDE.md"`.

It was found by running §4's dry pass and reading the output — not by review, and not by the 71
tests then passing, because every fixture that made the tree dirty made it dirty with one file
and one file cannot tell a truncation of the first entry from a truncation of every entry. Fixed
in `dfae15d` with two regression tests that each dirty **two** files, one covering the staged
spelling (`M  path`) and one the unstaged (` M path`). This is the whole argument for §4
existing: the dry pass is not a formality, it is the first time the code meets real data.

## 7. What was built

**Seldon repo** (`702ac32`, `dfae15d`):

* `seldon/core/dispatch.py` — candidacy (three headers), the nine criteria each recorded as a
  **value**, the standing-band reference resolver, the `flock` lease with an identified holder,
  PID-liveness reap, the supersession matcher, FIFO, the DD-007 key check.
* `seldon/commands/dispatch.py` — `once`, `status`, `lease show|reap`; the graph reads, the
  compare-and-set claim, the detached logged launch, the finish check, the four event types.
* `seldon/cli.py` — one import, one `add_command`.
* `docs/design/2026-09-15_standing_dispatcher.md` — the Seldon-side record: shape, the config
  block, the criteria, the events, the lease, the two note corrections, how a second project
  adopts it.
* `tests/test_dispatch.py` (**59**) and `tests/test_dispatch_launch.py` (**14**, Neo4j).

**This repo:**

* `seldon.yaml` — the `dispatch:` block, `enabled: false`, every key commented with its basis;
  `poll_interval_s: 300` carries DN-006 §5's "no measured basis" sentence in the file an
  operator changes it in.
* `scripts/jobs/com.brock.airkg-dispatch.plist` and `scripts/jobs/airkg_dispatch.sh` — the
  launchd job. **Not installed and not loaded by this task.** The wrapper reads the log caps
  from `controls.yaml jobs.biblio_resume` by reference and **refuses a pass (exit 2) when the
  plist's `StartInterval` and `seldon.yaml`'s `poll_interval_s` disagree**, because one
  parameter written in two files drifts; `test_the_wrapper_refuses_when_the_two_intervals_disagree`
  runs the wrapper against a deliberately mismatched copy and sees the refusal.
* `tests/test_dispatch_config.py` (**7**) — the band equality against `kg/spend.py`, that no
  copied token number sits in the block, that it ships disabled, the plist/YAML interval
  agreement and the wrapper's refusal, the two gitignores, and the two `CLAUDE.md` sentences.
* `CLAUDE.md` — two sentences in "CC dispatch protocol", `+2 −0`: the supersession marker with
  the three-header candidacy rule in one clause (ADDENDUM_01's amendment to decision 3), and
  decision 10's no-hand-dispatch rule.
* `docs/design/2026-09-15_DN-006_standing_dispatcher_ADDENDUM_01.md` — the three corrections
  above, written rather than deviated from.
* `scripts/check_protected_standing_dispatcher.sh`.

**`logs/dispatch/` and `.seldon/dispatch.lock` are already gitignored** by the existing
`logs/` and `.seldon/` entries — verified with `git check-ignore -v`, and asserted standing by
`test_the_lease_and_the_dispatch_logs_are_gitignored`. No `.gitignore` line was added, because a
redundant entry is a second place to maintain the same rule.

**`dispatch.enabled` is `false` and this task did not enable it.** Enabling is the first line of
the cadence task, after the operator-dispatched queue has drained under decision 10.

## 8. Logs

```
logs/sd_addendum_glob_start.log   addendum glob, before starting      ADDENDUM_01 found
logs/sd_addendum_glob_pre_s5.log  addendum glob, before §5            the same one file
logs/sd_marker_survey.log         §0, all 34 addenda                  the table in §3
logs/sd_open_tasks_before.log     the graph's open tasks, before      24 open, 1 with a source_file
logs/sd_before_cypher.log         §3 BEFORE: 6ee71737 proposed, 0 edges
logs/sd_supersede.log             seldon task supersede               EXIT=0
logs/sd_after_cypher.log          §3 AFTER: superseded + SUPERSEDED_BY -> e2885e86
logs/sd_launch_tests.log          the Neo4j launch tests              EXIT=0  14 passed
logs/sd_seldon_suite.log          Seldon suite, before the fix        EXIT=0  1,785 passed
logs/sd_seldon_suite2.log         Seldon suite, on the merged commit  EXIT=0  1,787 passed / 146.82 s
logs/sd_dry_pass.log              §4 once + status + byte comparison  EXIT=0  BYTE-IDENTICAL: YES
logs/sd_gate_fast.log             make gate-fast, detached, polled    EXIT=0  2,187 passed / 422.54 s
logs/sd_verify.log                seldon verify                       EXIT=0  all checks passed
logs/sd_protected.log             protected paths                     EXIT=0  PASS
```

## 9. Open, for the next OODA

1. **Nothing is enabled and nothing is installed.** The plist is in `scripts/jobs/` and not in
   `~/Library/LaunchAgents/`; `dispatch.enabled` is `false`. The cadence task (DN-006 decision
   8) owns both, and decision 10 says the operator-dispatched queue drains first.
2. **The dispatcher has launched nothing, so `poll_interval_s: 300` still has no measured
   basis.** DN-006 §5 says one week of `dispatch_launched` events makes dispatch latency
   measurable. Zero such events exist; the value stays declared until they do.
3. **Twenty-two open tasks carry no `source_file` and can never be dispatched.** Not a defect —
   it is the opt-in — but "re-authored" in DN-006 decision 2 means authoring a task FILE for
   each, not adding a header to one that does not exist. Whether all twenty-two deserve that is
   a question nobody has asked; several are from the DN-005 §4 continuing list and several are
   hygiene.
4. **The three-header rule now binds only what the dispatcher reads.** A task file missing
   `**Framework layer served` is undispatchable, which is a real consequence, but a task that
   never becomes dispatchable is unaffected — so DN-005 §5 rule 1 is enforced for the
   automated path and still only a reader's check for the hand-dispatched one.
5. **`seldon dispatch` has no cross-project test.** It is written to be adopted by any project
   with a `dispatch:` block, and the only block that exists is this repository's. The Seldon
   suite tests it against synthetic fixture projects; the first real second project will be the
   first test of whether "adopting it in another project" is as short as that doc claims.
