# RESULT — the self row: six verdicts, 1 pass and 5 fail, and four of them are not about this publication

**Task:** `cc_tasks/2026-09-13_self_row.md`. **No addendum exists** —
`cc_tasks/2026-09-13_self_row_ADDENDUM*.md` globbed before starting and again before §3, both
times `No such file or directory` (`logs/self_row_addendum_glob_start.log`,
`logs/self_row_addendum_glob_pre_s3.log`).
**Date:** 2026-09-13. **Spend:** zero model calls.
**Network: the published authority only.** Every request in this task went to
`brockwebb.github.io` — 20 from the live-host gate and 15 from the scan, counted at the socket —
plus the loopback control fixtures, which are us, and the `git push` §4 orders. **No federal host
and no reference host was contacted**, and the payload's own socket counter is the proof:
`requests_per_host` is `{"brockwebb.github.io": 15}` and nothing else. `corpus/` is byte-identical
to HEAD (`logs/self_row_protected.log`).

## THE GATE: PASS. The row is measured and published.

**Live URL of the row: <https://brockwebb.github.io/ai-readiness-kg/>**, in the section headed
*“This site’s own row”*. The index carries no fragment id on that heading, so the URL is the page's;
naming an anchor that does not exist would be the kind of claim this row is about.

## 1. §1 — decision 4: the host serves the tree

The clause the publish task could only record as **NOT REACHABLE** now runs, and passes.

| | |
|---|---|
| URLs asked of the live host | **20** — every relative `href` on the index, every `<loc>` in the sitemap, plus `robots.txt` and `sitemap.xml`, which neither source can name |
| HTTP 200 | **20 of 20** |
| byte-identical to the tree | **19 of 20** |
| not byte-compared | `progress/` alone, and the reason is on the face of the code: it is a generated page carrying its own build timestamp, so equality of bytes is not the property that holds for it. Its 200 is |
| netlocs contacted | `brockwebb.github.io` only |
| client | `ai-readiness-kg-scanner/0.2 (+https://github.com/brockwebb/ai-readiness-kg)`, at the declared 1 req/s — both **read from `params.manners`**, never typed |

`scripts/check_live_host.py` refuses a computed URL on any other host rather than requesting it,
and it byte-compares rather than merely counting 200s: a 200 serving *different bytes* than the
repository holds is worse than a 404, because the 404 is visible. All seven `data/` files, both
citation files, the index, `llms.txt`, `robots.txt` and `sitemap.xml` are byte-for-byte what the
tree holds. `state/live_host_2026-09-13.json` is the per-URL record.

**I added the two published faces the task's wording would have missed.** A gate built only from
"hrefs on the index" and "`<loc>`s in the sitemap" never asks for `robots.txt` (deliberately not
in the sitemap) or `sitemap.xml` (cannot be in its own urlset) — and those are the two files a
machine reads first.

## 2. The six verdicts, with the URL each one read

**1 pass, 5 fail.** Registered, payload on disk at `state/self_l0_self_2026-09-13.json`, cycle
`self_2026-09-13`, `RULE-*` versions as the instrument currently stands.

| leg | verdict | Result | what answered | URL(s) read |
|---|---|---|---|---|
| **A4** | **fail** | `self_l0_a4_self_2026-09-13` | the authority root — **not** this publication | `https://brockwebb.github.io/robots.txt` → 404 |
| **A5** | **fail** | `self_l0_a5_self_2026-09-13` | the authority root — **not** this publication | `/sitemap_index.xml`, `/sitemap.xml`, `/llms.txt`, `/.well-known/ai-plugin.json`, `/.well-known/mcp.json` — all at `https://brockwebb.github.io/`, all 404 |
| **A10** | **pass** | `self_l0_a10_self_2026-09-13` | **this publication** | `https://brockwebb.github.io/ai-readiness-kg/` → 200, and `…/__ai-readiness-kg-probe-404__` → 404 |
| **A11-declared** | **fail** | `self_l0_a11_declared_self_2026-09-13` | the authority root — **not** this publication | `https://brockwebb.github.io/robots.txt` → 404, `https://brockwebb.github.io/ai-readiness-kg/` → 200 |
| **A12** | **fail** | `self_l0_a12_self_2026-09-13` | the authority root — **not** this publication | `https://brockwebb.github.io/ai-readiness-kg/` → 200, `https://brockwebb.github.io/robots.txt` → 404 |
| **G1-D** | **fail** | `self_l0_g1_d_self_2026-09-13` | **this publication** | `https://brockwebb.github.io/ai-readiness-kg/` → 200 |

The reasons, verbatim from the Findings:

* **A4** — "no robots.txt served; retrieval is permitted by default but nothing is declared for
  AI crawlers"
* **A5** — "no sitemap, llms.txt or well-known discovery file served"
* **A10** — "deep link HTTP 200; invalid route correctly HTTP 404; 4603 visible characters present
  before JS. The pre/post-JS DOM diff the signal also names was NOT run (renderer: none)"
* **A11-declared** — "nothing is DECLARED: no robots.txt is served, so the declared layer of the
  A11 triad is empty"
* **A12** — "robots.txt is served with a content type that cannot be robots.txt, so nothing is
  DECLARED for this client and there is no declaration for the enforced layer to cohere with"
  (see §6 — this reason misdescribes a 404, and the misdescription is not confined to this row)
* **G1-D** — "none of the 11 error-measure field tokens appears as a structured field on the
  surface"

**The four fails against the authority root are the predicted finding, now measured.**
`cc_tasks/2026-09-12_publish_l0_RESULT.md` §3 said that on a project Pages site A4, A5,
A11-declared and A12 "will be measuring `brockwebb.github.io` and not this publication". They did.
RFC 9309 §2.3 scopes a robots.txt to an authority — scheme, host and port — and the authority here
is the whole of `brockwebb.github.io`, whose root belongs to a user-site repository that does not
exist. **The tree's own `robots.txt` and `llms.txt`, which admit all eight AI crawlers by name and
disallow nothing, were never read by any leg**, because no crawler would read them either. That is
the whole point: this instrument, applied to itself, reproduces the exact failure mode it exists to
detect — declarations sitting somewhere a machine will not look.

**Two fails are about this publication and are earned.** A10 passes (the deep link serves, the
invalid route 404s, 4,603 characters render before JavaScript). G1-D fails because the index
declares no error-measure field — which is true: it is a link page over data files, and the
uncertainty declarations live inside the matrices, not on the surface G1-D reads. It is a fair
fail against the rule as written and it stays.

**Decision 3 was honoured literally.** Nothing under `docs/` was changed after measurement except
to render the row. `robots.txt`, `llms.txt` and `sitemap.xml` are byte-identical to HEAD, asserted
by `scripts/check_protected_self_row.sh` — which is how "we did not repair the site after scanning
it" is a check rather than a promise.

## 3. Decision 1 — the normal harness path, and the one premise that forbade the obvious route

`scripts/run_self_scan.py` calls **`scan.run.main()`** — the same entry point every other cycle
ran through: the control gate first (**`pass`**, loopback fixtures, 338 control observations), the
same collectors, the same rules, the same `Fetcher` and manners, the same payload shape, the same
`refuse_clobber`, evidence staged per cycle. 2 surfaces, 6 Findings, 13 cycle Observations, 15
requests.

**What it does NOT do is edit `params.cycle`, and that is a premise correction, not a shortcut.**
The obvious way to run a cycle here is to point `params.cycle.name`/`targets` at the new frame.
That cannot be done for this cycle:
`scripts/register_l0_report_results.py::netlocs_declared` reads **whatever target file
`params.cycle.targets` currently names** and counts its netlocs — and the Result it registers,
`fss_scan_netlocs_2026-09`, is one of the 59 the L0 report tags and is `published` at **22**.
Pointing the declaration at a one-host frame would make it re-derive to **1**, so
`scripts/rederive_tagged_results.py` would BLOCK and the publication's own gate would fail for a
reason with nothing to do with the self-scan. Measured, not assumed:
`netlocs_declared(load_params())` is 22 today.

So the cycle identity is overlaid **in memory**, at the one seam that decides which cycle is
running (`run.load_params`, replaced for the duration — the repo's own call-time-indirection
convention), and `overlaid()` **asserts that nothing but `cycle` differs**: the self row is
measured by the same instrument as the report, not by a copy of it.

**And the overlay records itself, because otherwise it would have created the defect this repo has
fought twice.** A payload whose parameters exist only in a dead process is a payload nothing can
ever re-judge — the position the two `_rj1` payloads sat in for a task. The payload therefore
carries `base_params_hash` (the committed `params.yaml`), `params_overlay` (the exact two-key
change) and a note saying why. `tests/test_self_row.py` recovers the base from git **by hash**,
applies the overlay, checks the result hashes to the cycle's own `params_hash`, and then
**re-derives every Finding byte-identically**. The self cycle is re-derivable on the same terms as
every other cycle.

## 4. Decisions 2 and 5 — the row states which authority answered, per leg

`state/self_l0_self_2026-09-13.json` carries, per leg: the verdict, the reason, the rule and its
version, the Finding id, **every URL read with its status, collector, error class and body
digest**, the authorities that answered, and `authority_is_this_publication` — a **derived** fact
(every URL under `site_url` and none outside it), re-derived from the URLs by
`test_the_authority_claim_on_each_leg_is_derived_from_the_urls` rather than trusted as a label.
`legs_measuring_this_publication` is `[A10, G1-D]`; `legs_measuring_the_authority` is
`[A4, A5, A11-declared, A12]`.

**The index prints it** (decision 5) with a four-column table — Check, Verdict, **What answered**,
Reason — every URL visible on the row, and the reader told in bold to *read the third column
before the second*. `tests/test_publication.py::test_the_self_row_is_measured_or_says_it_is_not`
**flipped to its measured branch with no edit to the test**, exactly as decision 5 asked.

**A Result holds a number and a verdict is categorical**, so the value is `1.0` for `pass` and
`0.0` for `fail` — and a leg whose verdict is *neither* (`error`, `not_applicable`) is **refused**
rather than filed as a 0 that would read as a fail. All six verdicts here are pass or fail, so
nothing is conflated; the refusal exists so a future self-scan cannot quietly file an `error` as a
failure. The verdict word is authoritative and is on every Result's description and in the payload.

## 5. Premises the task file got wrong

| premise | measured |
|---|---|
| decision 1's "payload dropped at `state/self_l0_self_2026-09-13.json`, **which the site builder already reads**" | **Wrong.** The builder read `state/self_l0_{cycle_suffix(snapshot_cycle)}.json` = `state/self_l0_2026-09-10_rj2.json`. The path in the task is the one it would read only if the snapshot cycle *were* the self cycle. **Fixed at the cause:** the self cycle is now DECLARED (`publication.yaml: self_scan_cycle`) and the builder reads `state/self_l0_<that>.json`, which is the task's path. Deriving the self row's path from the snapshot cycle was wrong on its own terms — the snapshot is a nineteen-host measurement from three days earlier and the row is a measurement of this host now. |
| decision 1's "`run.py` as any cycle runs" | **Its substance, not its letter** (§3). `run.main()` runs unchanged; what it may not do is edit `params.cycle`, because that breaks the re-derivation of a published Result. The task could not have known this without tracing `netlocs_declared`. |
| §3's "**socket counter** shows the published authority only" | **Right and satisfied**, and it is the payload's own `requests_per_host`, not an inference from Observations. |
| §3's "both invariant readings 0 **on the self payload**" | **Taken literally, and it is the reading that works.** Both are computed on the payload with `scan.publish`'s own predicates (imported, not restated): `observed_on_missing_document` **0**, `findings_evidence_unretained` **0**, with 13 synthetic host observations and 338 control observations counted apart — the same carve-outs the projection makes, without which a zero would mean nothing. See §7 for what this does NOT do. |
| decision 2's "If the operator has since created the user-site repository and its root serves `robots.txt` and `llms.txt`, that is what the legs read … if the root still answers 404, the legs return what they return" | **The second case.** `https://brockwebb.github.io/robots.txt` is 404; no user site exists. Nothing was inferred from which case it is — the payload is the record. |

## 6. What the self-scan found in the instrument itself

**`RULE-A12-v2` describes a 404 as a file that was served, and the published report's evidence
carries one instance of it.** A12's reason on this row reads *"robots.txt is served with a content
type that cannot be robots.txt"* — but the host answered **HTTP 404**, and what carries the HTML
content type is GitHub's 404 page. The rule checks `wrong_content_type` **before** `robots_status`
(`rule_a12_v2.py` lines 79-82), so on any host whose `/robots.txt` 404s with an HTML error page the
reason asserts "is served" about a file that was not. A4-v1, on identical evidence, says the true
thing: *"no robots.txt served"*.

**The verdict is not affected** — nothing is declared either way, so `fail` stands — but the reason
string misdescribes the evidence, and it is not confined to this row: **one published Tier A
Finding has it**, `host:www.federalreserve.gov` (verdict `fail`, robots.txt 404). Measured, not
guessed: that is the only one of cycle 4's re-judged A12 Findings carrying the phrase.

**Not fixed here.** Rule modules are on this task's zero-edits list, a rule change is a new rule
version and a re-judgement rather than an edit, and it is one gate per task. Recorded for the next
one (§8).

## 7. What this task deliberately did NOT do, and why

**The self cycle's Observations and Findings are not on the KG event log, and its captured bodies
are not in `corpus/evidence/scan/`.** The two are one decision, because `publish.py` permits only
one order: it promotes staged bodies **before** writing events, since the alternative "would put a
staging path — a directory this run then deletes — on a line that can never be edited". Promoting
writes into `corpus/`, which this task's zero-edits list forbids. So neither was done: no
`write_events`, no `promote_evidence`, no re-projection of the scan layer.

What that costs, stated rather than left for a reader to discover: the self payload's
`body_path` values point into `state/evidence_staging/self_2026-09-13/` (gitignored, 156 KB, 34
bodies), so **the row's bodies are not retained in the repository**. The row says so itself —
every read in `state/self_l0_self_2026-09-13.json` carries `body_in_committed_store: false` — and
the loss is smaller than it looks: every body except the authority root's 404 pages is a file this
repository holds under `docs/` at the commit the payload names, and the live-host gate byte-compared
19 of them the same day. The six verdicts, their rules, their versions, their URLs and their status
codes are all on the committed payload.

**What the follow-up needs to do** is both halves in one task: `publish.py --from
state/self_2026-09-13.json` (promote, then `write_events`) `--project`, add `self_2026-09-13` to
`PRIOR_CYCLES` with its Finding count, and let the retention census see it. That task edits
`corpus/` and re-projects the scan layer, which is why it is a task and not a paragraph here.

**`docs/llms.txt` still carries no licence**, carried forward from
`cc_tasks/2026-09-13_ephemeral_provenance_RESULT.md` §4 — and it is now *also* a row on this
table, because A5 read the authority root's `/llms.txt` and never saw the tree's.

## 8. The gate (§3), clause by clause, with the log that carries each

| clause | result | log |
|---|---|---|
| addendum glob, before starting and before §3 | **none exists**, both times | `logs/self_row_addendum_glob_start.log`, `logs/self_row_addendum_glob_pre_s3.log` |
| §1: index and sitemap resolve **on the live host**; `data/` byte-matches | **PASS** — 20 of 20 HTTP 200, 19 byte-identical (all `data/`, both citation files, index, robots, llms, sitemap) | `logs/self_row_live_host.log`, `state/live_host_2026-09-13.json` |
| six verdicts registered under `self_l0_*` with the payload on disk | **PASS** — 6 registered, 0 failed; `state/self_l0_self_2026-09-13.json` | `logs/self_row_register.log` |
| every Finding carries the URL read | **PASS** — asserted on the payload and on the row | `logs/self_row_gate_task.log` |
| the row renders with per-leg authority stated | **PASS** — four columns, every URL on the row, the RFC 9309 limit in prose | `logs/self_row_gate_task.log` |
| socket counter shows the published authority only | **PASS** — `{"brockwebb.github.io": 15}`; no federal host, no reference host; `corpus/` byte-identical | `logs/self_row_scan.log`, `logs/self_row_protected.log` |
| both invariant readings 0 on the self payload | **PASS** — `observed_on_missing_document` 0, `findings_evidence_unretained` 0 | `logs/self_row_register.log` |
| the self payload re-derives byte-identically | **PASS** — under base-from-git + recorded overlay (not in §3's list; added because the overlay would otherwise have made this the one payload nothing can re-judge) | `logs/self_row_gate_task.log` |
| `make gate-task` | **PASS** — **2,031 passed, 17 skipped, 19 deselected, 12 xfailed, 375.82 s**; then 16 of 16 payloads re-derive, 5.86 s | `logs/self_row_gate_task.log` |
| `make guards` | **PASS** — 25 passed, 15.70 s | `logs/self_row_guards.log` |
| `make gate-full` (detached, logged, polled to EXIT) | **PASS** — **2,050 passed, 17 skipped, 12 xfailed, 1,239.15 s (20:39)** | `logs/self_row_suite_full.log` |
| `seldon verify` | **PASS** — all checks passed | `logs/self_row_verify.log` |
| protected paths | **PASS** — the harness, the manners, every rule module, `corpus/`, `events/`, the record, the skeleton, section prose, the report and its PDF, every published matrix, `robots.txt`, `llms.txt`, the sitemap and both licences byte-identical | `logs/self_row_protected.log` |

Every log carries its own `EXIT=0` and all eight were written before this file was. The nine tests
the two tiers differ by are `tests/test_self_row.py`.

## 9. What changed

**New:** `scripts/check_live_host.py`, `scripts/build_self_frame.py`, `scripts/run_self_scan.py`,
`scripts/self_row_report.py`, `scripts/check_protected_self_row.sh`, `tests/test_self_row.py`,
`state/scan_targets_self_2026-09-13.json`, `state/self_2026-09-13.json`,
`state/self_l0_self_2026-09-13.json`, `state/live_host_2026-09-13.json`.
**Modified:** `scripts/build_l0_site.py` (the self cycle is declared, not derived; the row renders
with per-leg authority), `docs/reports/publication.yaml` (`self_scan_cycle`), `docs/index.html`
(the row), `docs/data/index.json` (rebuild), `seldon_events.jsonl` (6 Results, 1 Script, 1
DataFile).
**Zero edits** to rule modules, harness runtime, manners, stored payloads, prior Results, prior
RESULTs, figures, section prose, the skeleton, the record, `corpus/`, `events/`,
`docs/robots.txt`, `docs/llms.txt`, `docs/sitemap.xml`, the report and its PDF, both licences.

## 10. What the next task should pick up

1. **Publish and promote the self cycle** (§7): `publish.py --from state/self_2026-09-13.json
   --project`, add `self_2026-09-13` to `PRIOR_CYCLES`. It touches `corpus/` and re-projects the
   scan layer, so it is its own gate.
2. **`RULE-A12-v2`'s reason string** (§6): reorder the `wrong_content_type` / `robots_status`
   branches, as `RULE-A12-v3`, and re-judge. One published Tier A Finding
   (`host:www.federalreserve.gov`) carries the misdescription.
3. **The host, which is the only thing that fixes four of the six fails** (§2). A custom domain on
   this repository, or the user-site repository `brockwebb.github.io`, moves this publication's
   `robots.txt` and `llms.txt` to the authority a crawler actually reads. That is a value input and
   the operator's to decide; nothing here assumed one. **Until then the row is honest and should
   stay exactly as it is.**
4. **`docs/llms.txt` should state the licence** — now a row on this table as well as a line in the
   previous RESULT.
5. **G1-D on the index** is a fair fail against a link page. Whether the *publication* should
   declare its error measures on the surface a machine reads first, rather than only inside the
   matrices, is a design question about the publication and not a scanner defect.
