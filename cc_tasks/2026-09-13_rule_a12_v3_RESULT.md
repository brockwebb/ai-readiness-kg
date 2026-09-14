# RESULT — generation 10: fifteen sentences corrected, not one verdict moved

**Task:** `cc_tasks/2026-09-13_rule_a12_v3.md`. **No addendum exists** —
`cc_tasks/2026-09-13_rule_a12_v3_ADDENDUM*.md` globbed before starting and again before §3, both
times `no matches found` (`logs/a12v3_addendum_glob_start.log`,
`logs/a12v3_addendum_glob_pre_s3.log`).
**Date:** 2026-09-13 local / 2026-09-14 UTC. **Spend:** zero model calls.
**Network: none.** The re-judgement reads stored Observations and the control gate binds nine
loopback sockets; no host was contacted, and every payload this task wrote records
`requests_total: 0` and `requests_per_host: {}`. The only remote operation is the `git push` §4
orders.

## THE GATE: PASS — zero verdict moves across five payloads, 15 reason-only changes

| payload | supersedes | findings | verdict moves | reason-only changes, by leg |
|---|---|---|---|---|
| `scan_2026-09-07_rj3` | `scan_2026-09-07_rj2` | 352 | **0** | **6** — A5 ×3, A10 ×2, A12 ×1 |
| `scan_2026-09-07b_rj4` | `scan_2026-09-07b_rj3` | 404 | **0** | **2** — A10 ×2 |
| `scan_2026-09-09_rj3` | `scan_2026-09-09_rj2` | 634 | **0** | **3** — A10 ×2, A12 ×1 |
| `scan_2026-09-10_rj3` | `scan_2026-09-10_rj2` | 739 | **0** | **3** — A10 ×2, A12 ×1 |
| `self_2026-09-13_rj1` | `self_2026-09-13` | 6 | **0** | **1** — A12 ×1 |
| **total** | | **2,135** | **0** | **15** |

**4 of the 15 are the A12 branch order; 11 are the `unobserved_error` note.** Every one is
checked against the two corrections by its own text rather than by its leg
(`test_the_reasons_that_changed_are_the_two_this_generation_corrects`), because "A12 changed" is
not evidence that A12 changed for the right reason: a rule that had also reworded an unrelated
branch would show up on the same leg. Full before/after for all fifteen:
`logs/a12v3_reason_changes.log` and `state/rejudgement_diff_2026-09-13.json`.

## 1. Decision 5 — the federalreserve sentence, on the stored evidence

`host:www.federalreserve.gov`, A12, cycle 4. The evidence, from `scan_2026-09-10`'s own
Observations: `robots_status: 404`, `served_content_type: "text/html"`,
`wrong_content_type: true`, `present: false`.

| | |
|---|---|
| **`RULE-A12-v2`** | `fail` — *"**robots.txt is served with a content type that cannot be robots.txt**, so nothing is DECLARED for this client and there is no declaration for the enforced layer to cohere with"* |
| **`RULE-A12-v3`** | `fail` — *"**no robots.txt served (HTTP 404)**, so nothing is DECLARED for this client and there is no declaration for the enforced layer to cohere with"* |

Same verdict, true sentence. The published Finding in `scan_2026-09-10_rj2` is superseded by the
one in **`scan_2026-09-10_rj3`**.

**Three hosts carried it, not one — the first premise correction.** The task names
`host:www.federalreserve.gov` and that is right about the PUBLISHED report, whose snapshot is
`scan_2026-09-10_rj2`. Across the stored payloads the same false sentence also sits on
`host:www.census.gov` (cycle 1's re-judgement, `scan_2026-09-07_rj2`) and on
`host:brockwebb.github.io` — this publication's own authority, the row that found the defect.
All three are corrected.

## 2. Decision 1 — `RULE-A12-v3`, and what it deliberately does not change

Status before content type. A response that is not a 2xx did not serve a robots.txt whatever its
content type, and the sentence for that is `_common.NO_ROBOTS_SERVED` — the phrase `RULE-A4-v1`
has said since the first generation. The wrong-content-type branch now fires **only on a 2xx**,
which is the case it was written for: the soft-404 host that answers HTTP 200 with an HTML shell.

**Both 2xx sentences are v2's, verbatim, and that is a decision.** The first draft also named the
content type on the 2xx branch (`…cannot be robots.txt (text/html)`), which is an improvement and
is not what this task was sent to do — a rule version that also tidies a branch it was not sent to
touch makes its own re-judgement unreadable, because every changed reason then has to be sorted
into "the correction" and "while I was here". **My own test caught it**
(`test_v3_changes_the_sentence_for_an_unserved_file_and_nothing_else`, which walks six branches
and demands byte-equality on the five v3 must not move), and the wording was reverted.

**The shared sentence is enforced against A4-v1's shipped bytes, not by editing them** — the
second premise correction. Decision 1 says the sentence is "read from a shared constant so the two
rules cannot drift", and A4-v1 cannot read it: it is a shipped module, every Finding recorded
under it must keep re-deriving from its own source, and the same task forbids editing it. So the
constant lives in `_common`, `RULE-A12-v3` reads it, and a test asserts the string is still inside
`rule_a4.py`'s source. Same shape as the content-hash pin the generation-4 lint uses for
`rule_a3_v4`: the constraint binds the shipped bytes rather than rewriting them.

## 3. Decision 2 — the note names the branch that fired, and it is versioned in PARAMS, not in a rule

`_common.unobserved` returns True for two different reasons — a BLIND error class, or a response
carrying a status in `manners.unobservable_statuses` — and `unobserved_error` printed the error
CLASS's note either way. On a probe whose class is `None` and whose status is 403, that note reads
***"the collector observed the surface"*** about a probe the same sentence has just called
unobserved. Three stored Findings carry that exact contradiction; three more named `http_4xx` when
a 403 was what fired.

**Decision 2 says "every rule that calls it turns over to a new version only if its reason text is
inside the re-derivation comparison for that rule". It is — for all four callers — and turning
them over would not have helped. That is the third and most important premise correction.**
`rederive` re-judges each stored Finding under **its own** `rule_id`, so a `RULE-A10-v3` Finding is
re-judged by `rule_a10_v3.py`, which calls the shared helper: a `v4` of it would never be reached.
Shipping four new rule modules would have changed nothing about the payloads that carry the
defective text, and they would simply have stopped re-deriving.

The lever that does work is the one this repo already established for exactly this class of
problem: **`params.finding_identity` versions the id scheme, and `params.reason_text` now versions
the reason text.** Scheme 1 is what every stored Finding was made under and is kept forever;
scheme 2 prints the note for the branch that fired. History re-derives under its own params — the
gate recovers them from git by hash — so raising it moves no stored reason. `_REASON_TEXT` is a
dispatch table beside `_IDENTITY`, defaults to 1 when the key is absent, and raises on an unknown
scheme rather than falling back.

**So the answer to "which rules turned over" is: none, and none needed to.** `RULE-A12-v3` is this
generation's only new module, and it is new for decision 1's reason, not decision 2's. The four
callers — `rule_a5_v2`, `rule_a8_v3`, `rule_a8_v4`, `rule_a10_v3` — are byte-identical.

**The absorbed ResearchTask predicted the wrong lever, and that is worth recording.** `c5c0d15d`
says *"reason is inside the re-derivation comparison, so the fix needs a rule version"*. The first
half is exactly right and is why this was not a two-line edit; the second half is one level off,
for the reason above. Closed with a pointer here.

Both branches are asserted, and so is the contradiction itself
(`test_the_contradiction_scheme_1_produces_is_real_and_is_preserved`): scheme 1 must keep saying
"the collector observed the surface" or the payloads that recorded it stop re-deriving, and scheme
2 must not.

## 4. Decision 1's second clause — the ninth fixture

**None of the eight produced the 404-with-HTML case.** Surveyed, not assumed
(`logs/a12v3_fixture_survey.log`): seven serve a `robots.txt` at 200 `text/plain` or reset before
any response, and `fails_all` answers **200** with the soft-404 shell — a 200 with the wrong
content type, which is the case `RULE-A12-v2` gets RIGHT. The case it gets wrong had no control at
all, which is why a live federal host was the first thing to find it.

`robots_404_html` serves everything `passes_all` serves and answers `/robots.txt` with **404 and
an HTML body** — what a static host or CDN does with any unknown path, and what both
`www.federalreserve.gov` and `brockwebb.github.io` do. Its expected verdicts were **derived from
the rule source and written into `params.yaml` before the fixture was ever run**, as every row in
that table was: `{default: pass, A4: fail, A11-declared: fail, A12: fail}`. The gate returned
exactly that — **E5 `pass`, `unexpected: []`, `unknown` = 0** across all nine.

`fixture_expectations` derives no row from dispatch here, and says so: the fixture blinds nothing
(a 404 is an observation, `http_4xx` is OBSERVED, and the fetcher reads an unparseable robots body
as permitting everything), so every entry is a rule's judgement over served content and is
`deferred` to the pre-registered table.

## 5. Decision 4 — nothing registered, nothing republished as a measurement

**No Result was registered**, asserted by count before and after: **7,261 live / 7,262 total**,
both times (`logs/a12v3_results_{before,after}.log`). The report is not rebuilt, its snapshot
stays `scan_2026-09-10_rj2`, and its tagged Results stay `published` at their values.

## 6. The two things the zero-edits list could not have got right

Both are reported rather than quietly widened, and both are consequences of decision 1 rather than
choices made here.

**(a) "Zero edits to … the record" cannot hold when a new `CURRENT` rule ships.**
`framework/ai_readiness_framework.json` records the rule each leg is judged by, so shipping
`RULE-A12-v3` and not writing it back leaves the record and the instrument disagreeing — and three
standing tests say so (`test_framework_graph.py` ×2, `test_scan_harness.py` ×1). Running
`framework_writeback_rules.py` and then `load_framework_graph.py` after shipping a rule is this
repo's standing procedure, recorded in four prior RESULTs. Run through the single writer: **exactly
two derived fields moved** — `spec:A12.rule_id` → `RULE-A12-v3`, and `spec:E5.collector_pin` → the
nine fixtures — with **no node or edge added or removed and no `counts` key moved**, and one
append-only `framework_writeback` event. Neither field is authored; both are read from
`assessment/harness/scan/rules` and `fixtures.server.MODES`.

**(b) Shipping a rule now makes the PUBLISHED tree stale, which was not true the last time a rule
generation shipped.** The site publishes a COPY of the framework record and hashes the SOURCE in
its manifest — `cc_tasks/2026-09-12_publish_l0.md`, **one day after generation 9** — and
`docs/design/scan_tool_map.md` is a generated table naming the rule each collector feeds. So two
more standing tests went red, and both were repaired by their own generators, never by hand.
`docs/` moved on four files and nothing else: the framework copy (the same two fields), its digest
and size in `docs/data/index.json`, the tool map's two A12 cells, and `docs/index.html`'s build
stamp. **No matrix, no report, no PDF, no `llms.txt`, no `robots.txt`, no sitemap and no citation
file changed.** Each is asserted field by field in
`scripts/check_protected_rule_a12_v3.sh` rather than in prose.

A third, smaller one: `tests/test_invariants.py`'s `MEASURES` audit is a literal list of the rules
declaring a non-product subject. `RULE-A12-v3` joins it for the reason v1 and v2 are in it — A12's
subject IS the host's refusal — and the test now also asserts every entry is an A12 version, so a
rule on a DIFFERENT leg still trips it.

## 7. A defect found in passing, recorded and not fixed

`_common.rule_version` catches `(KeyError, ValueError, TypeError)` around
`_IDENTITY[int(scheme)](rule_id)`, and under `finding_identity: 2` that call is
`parse_rule_id(rule_id)`, which raises `ValueError` on an unparseable id. So an unparseable rule id
is reported as **`finding_identity 2 is not a known Finding-id scheme [1, 2]`** — a message that
names the wrong thing and lists the value it says is unknown. Found while writing these tests (a
synthetic `RULE-X-v1`); it costs a reader real time and it is one gate per task. §9 item 2.

## 8. The gate (§3), clause by clause, with the log that carries each

| clause | result | log |
|---|---|---|
| addendum glob, before starting and before §3 | **none exists**, both times | `logs/a12v3_addendum_glob_start.log`, `logs/a12v3_addendum_glob_pre_s3.log` |
| zero verdict moves across every re-judged payload | **PASS — 0**, five payloads, 2,135 Findings | `logs/a12v3_rejudge.log`, `state/rejudgement_diff_2026-09-13.json` |
| per-payload counts of reason-only changes | **PASS** — 6 / 2 / 3 / 3 / 1 = **15**, every one traced to one of the two corrections | `logs/a12v3_reason_changes.log` |
| A12-v3 and A4-v1 share the 404 sentence by construction | **PASS** — the constant, plus a test over A4-v1's shipped source | `logs/a12v3_gate_task.log` |
| `unobserved_error` branch test green | **PASS** — status branch names the status, class branch names the class, and scheme 1 still reproduces the contradiction | `logs/a12v3_gate_task.log` |
| control gate green over all fixtures with `unknown` = 0 | **PASS** — nine fixtures, E5 `pass`, `unexpected: []`, `unknown` 0 | `logs/a12v3_rejudge.log` |
| byte-identical re-derivation of every stored payload under its own versions | **PASS — 22 of 22**, 9.22 s | `logs/a12v3_gate_task.log` |
| both invariant readings 0 on every new payload | **PASS** — every re-judged payload cites only `obs_id`s its source cycle recorded; none is an orphan | `logs/a12v3_gate_task.log` |
| no Result registered, asserted by count before and after | **PASS** — 7,261 live / 7,262 total, both times | `logs/a12v3_results_before.log`, `logs/a12v3_results_after.log` |
| `make gate-task` | **PASS** — **2,046 passed, 17 skipped, 25 deselected, 12 xfailed, 365.78 s**; then 22 of 22 payloads re-derive, 9.22 s | `logs/a12v3_gate_task.log` |
| `make guards` | **PASS** — 25 passed, 15.59 s | `logs/a12v3_guards.log` |
| `make gate-full` (detached, logged, polled to EXIT) | **PASS** — **2,071 passed, 17 skipped, 12 xfailed, 1,269.02 s (21:09)** | `logs/suite.log` |
| `seldon verify` | **PASS** — all checks passed, 34,641 events readable | `logs/a12v3_verify_seldon.log` |
| protected paths | **PASS** | `logs/a12v3_protected.log` |

Every log carries its own `EXIT=0` and all of them were written before this file was. **Three
gate-task runs were discarded before the green one** and their logs are kept beside it
(`logs/a12v3_gate_task_stale_pre_writeback.log`, `_stale2`, `_stale3`): the first found the three
framework tests, the second the `MEASURES` audit, the third the two publication tests. Each red run
is a premise in §6, not a flake, and none of them was re-run without a change in between.

## 9. What the next task should pick up

1. **The twelve — now seventeen — re-judged payloads are not on the event log.** Carried forward
   from `cc_tasks/2026-09-13_self_cycle_promote_RESULT.md` §9 item 1 and made larger by this task:
   generation 10 wrote five more payloads that live only in `state/`. The graph's Findings are the
   measured cycles plus one self cycle; the judgements the published report is a view of are not
   among them. Settling what the log is for is the first thing.
2. **`_common.rule_version` misreports an unparseable rule id** as an unknown `finding_identity`
   scheme (§7). Two lines and a test.
3. **A5's blind-candidate message says "N of M discovery probe(s) … was not observed"** — singular
   verb on a plural count, visible in every one of the three A5 sentences this task corrected. A
   reason string is published prose; it is worth one pass.
4. **`RULE-A12-v3` is still a CANDIDATE rule** (DD-054), so none of this enters a numerator. That is
   unchanged and deliberate, and the question of whether A12 should graduate is a framework
   decision rather than a rule one.
