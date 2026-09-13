# RESULT — publish L0: the data published, the Result states real, the self row STOPPED

**Task:** `cc_tasks/2026-09-12_publish_l0.md`. **No addendum exists**; globbed before starting
and again before §3, both times empty (`no matches found`).
**Date:** 2026-09-13 UTC (the work began 2026-09-12 local). **Spend:** zero model calls.
**Network: the published host only, plus the git remote.** Six requests to
`brockwebb.github.io` with the identified client, all 404; one read-only `gh api` call to
`api.github.com` to read the Pages setting the task requires this file to NAME (§2), and the
`git push` the task orders. **No federal host and no reference host was contacted** — nothing
in this session ran a scan, and `corpus/` is byte-identical to HEAD, which is how that is
checkable (`scripts/check_protected_publish_l0.sh`).

## THE BLOCK, ON TOP: decision 2's self-scan did not run

**Decision 5 fired.** The tree is not served, so the six tier-0 legs were not run against the
published host and **there are no self-row verdicts to report.** Decisions 1, 3 and 4 completed
in full, and so did the *tree* half of decision 2 (`robots.txt`, `llms.txt`, sitemap, generated
and committed) — see §2 for why that half was not held back with the scan.

**The setting the operator must change**, measured rather than assumed:

| what | measured |
|---|---|
| every path under `https://brockwebb.github.io/ai-readiness-kg/` | HTTP **404** |
| `https://brockwebb.github.io/` itself | HTTP **404** — no user site exists either |
| `GET /repos/brockwebb/ai-readiness-kg` | `"has_pages": false`, `"visibility": "public"` |
| `GET /repos/brockwebb/ai-readiness-kg/pages` | **404 Not Found** — no Pages site is configured |

> **Settings → Pages → Build and deployment → Source: "Deploy from a branch" → Branch: `main`,
> folder: `/docs`.** The repository is public, so no plan upgrade is involved. That single
> setting serves the tree this task built at `https://brockwebb.github.io/ai-readiness-kg/`.

**No Pages or account setting was touched**, and this session could not have touched one: it
holds no credential for that API surface and issued only the read above.

## 1. Decision 3 — Result states, and they are real

**All 59 Results the report tags re-derived and reproduced. All 59 are now `published`.**

| | |
|---|---|
| tagged Results (READ from `{{result:...}}` in `docs/reports/sections/*.md`, never typed) | **59** |
| re-derived and reproducing their registered value | **59 of 59** |
| not re-derivable | **0** |
| disagreeing with the registry | **0** |
| `proposed → verified`, each with an `artifact_state_changed` event | **59** |
| `verified → published`, each with a state event **and** an `artifact_updated` event carrying the commit | **59** |
| the publish commit stamped on every one | `9a336eca0912abc5cac6bfcd4704bf982a3f5fe4` |

Verified in the graph after the fact: `MATCH (r:Result {state:"published"}) RETURN count(r),
collect(DISTINCT r.published_commit)` → `59, ['9a336eca0912abc5cac6bfcd4704bf982a3f5fe4']`.

**The generator was re-run; the arithmetic was never re-implemented.**
`scripts/rederive_tagged_results.py` drives, for each Result, the module the registry names in
`GENERATED_BY` over the artifact it names in `COMPUTED_FROM`, with `cycle_results.register`
**intercepted** — the single choke point every registrar in this repo passes through. What is
compared is exactly the `(name, value)` pairs that module would register today. Re-deriving a
number by writing fresh code that computes the same thing would have tested the fresh code.

Three generators are driven differently, each for a reason on its face:

* **`build_roster`** fetches `statspolicy.gov`. It retained both source bodies
  content-addressed when it ran, so the adapter rebuilds its `caps` from
  `corpus/evidence/frame/…` and calls `build_roster.build()` — the same parse over the same
  bytes, off the network.
* **`preflight`** probes nineteen federal hosts. Its generating artifact is
  `state/fss_preflight_2026-09.json`, and the refusal count is recounted from the rows it
  recorded (the adapter also checks the file against itself: summary list vs. row flags agree).
* **`scan_report` over `scan_2026-09-10`** — see §5, the one thing this task got wrong and
  caught.

**The transition verb existed, and `seldon result verify` was not the right one.** The registry
does have the state machine (`research.yaml`: `proposed: [verified]`, `verified: [published]`)
and the validated path (`seldon.core.artifacts.transition_state`), so §1's "if the registry has
no state-transition verb, stop" condition was **not** met. What the CLI lacks is a
`verified → published` verb, and its `verify` verb records `actor="human"` — an event log
saying a person verified fifty-nine Results nobody looked at is worse than no actor field.
`scripts/publish_result_states.py` therefore goes through `transition_state` with `actor="cc"`,
and it **refuses to move anything** unless the re-derivation report on disk records `PASS` with
every tagged name reproducing. A state that can be set without the evidence is a label.

`tests/test_publication.py` asserts both halves: that the script's two moves are edges the
domain state machine actually allows, and that a `BLOCKED` report, a short report and a missing
report are each refused.

**The causal order, stated because it cannot be otherwise.** No document can name the commit
that contains it. The tree was committed (`9a336ec`) and pushed, the transitions were then
stamped with that sha, and the published `results_tagged.json` was rebuilt to show
`"state": "published"` — which is why there are two commits and why the report's title page
says *built from* commit `0d3e0d8e6602`, the commit the build READ, and adds that the commit
publishing it is that one's child.

## 2. Decisions 1, 4 and the tree half of 2 — what publishes

`docs/` is the tree (the framework progress page already lives at `docs/progress/`); **no second
site was created.** `docs/index.html` links, in DN-002 decision 1's order:

1. the three matrices, **JSON and CSV** (`reports/scan_matrix_{tierA,tierC,product}_2026-09-10_rj2.*`);
2. `data/sources_per_check.json` — the per-check source appendix, 73 rows;
3. `data/results_tagged.json` — the 59 Results with value, state, description and provenance;
4. `data/ai_readiness_framework.json` — the framework record;
5. `data/corpus_manifest.json` — the corpus manifest;

then, last and labelled as views, the built markdown and the PDF, under the sentence decision 1
asks for: *the PDF is a projection of the data above it*. Everything linked is generated by an
existing builder; the only hand-written text on the page is that fixed prose.

**Copies are hashed, not trusted.** The framework record and the corpus manifest are canonical
outside the served tree, so `data/index.json` records each copy's source path, byte count and
the sha256 **of the source** — a copy that has drifted is a test failure, not a silent stale
file. The citation files are not copied at all: one string is written to the repository root
(where GitHub and Zenodo read it) and into `data/`, and a test asserts the two are byte-equal.

**Every published citation carries the pair a stranger needs.** All 73 appendix rows carry a
`source_url`, a `content_hash` and an `acquired_at`, with zero exceptions — DN-001's floor, now
machine-readable rather than only rendered. `legs_without_source` is empty.

**Decision 4.** `docs/reports/publication.yaml` is the single declaration of title, authors,
version and snapshot cycle, read by three consumers so they cannot drift. The report's title
page now carries `**Version.** Snapshot cycle `scan_2026-09-10_rj2` · version `2026-09-10_rj2`
· built from commit `0d3e0d8e6602` on `2026-09-13` (UTC)`, generated on every build — it is not
in section prose, which this task may not edit, and a commit hash typed into prose is stale the
moment it is typed. `CITATION.cff` and `.zenodo.json` are generated from the same declaration.
**No DOI is minted and no Zenodo call was made.**

**"CITATION.cff validates" — what was actually done.** No CFF schema validator is installed
(`cffconvert` is absent), and fetching the published schema would have spent the network budget
on a host that is not the published one. Validation is therefore: it parses as YAML, it carries
every CFF 1.2.0 **required** key (`cff-version`, `message`, `title`, `authors`) with the right
types and author shape, and it agrees field-for-field with the declaration it was generated
from. That is asserted in `tests/test_publication.py`, not claimed here.

**Why the tree half of decision 2 shipped and the scan did not.** Decision 5 stops the task
"before decision 2 (**the self-scan** needs a live host)", and it names the reason. `robots.txt`,
`llms.txt` and the sitemap need no live host, are additive and reversible, and are precisely
what the operator's one setting would serve; holding them back would have forced a follow-up
task to write them before the scan could ever run. They are generated and committed; the scan
is not run. `robots.txt` admits, **by name**, every crawler in `params.a4_crawlers.user_agents`
— read from params, so adding a crawler to the instrument and forgetting to admit it here is a
test failure rather than an asymmetry nobody notices — and disallows nothing.

## 3. A structural finding the self row will have to carry: RFC 9309 binds robots.txt to an AUTHORITY

**A project Pages site cannot serve an effective `robots.txt`, `llms.txt` or
`/.well-known/` probe, and this is not an omission — it is what the standard says.** RFC 9309
§2.3 scopes a robots.txt to the authority (scheme, host, port), not to a path prefix. On
`https://brockwebb.github.io/ai-readiness-kg/`, the authority is the whole of
`brockwebb.github.io`, whose `/robots.txt` belongs to a user-site repository that does not
exist. The same holds for A5's discovery probes, which are host-root paths
(`/llms.txt`, `/.well-known/ai-plugin.json`, `/.well-known/mcp.json`), and for A12, which
compares a declared layer read from the host root against enforced behaviour.

So when the self-scan does run against a project Pages site, **A4, A5, A11-declared and A12
will be measuring `brockwebb.github.io` and not this publication.** That is a measurement of
the wrong object, and it is worth more than a caveat: it means this instrument, applied to
itself, reproduces the exact failure mode it exists to detect — a publisher whose declarations
sit somewhere a machine will not read them.

The files say so on their own faces rather than implying compliance they cannot have
(`tests/test_publication.py::test_robots_states_the_authority_limit_rather_than_implying_compliance`),
and the index says it too. **The fix is a host, not a file:** a custom domain on this repository,
or the user-site repository `brockwebb.github.io`. That is the operator's decision and is not
taken here.

## 4. Premises the task file got wrong, and one it got right

| premise | measured |
|---|---|
| "The tree Pages **already serves** (the graph page lives there; find it…)" | **Wrong.** Pages has never been enabled: `has_pages: false`, `/pages` 404, and `brockwebb.github.io` itself 404s. The graph page lives in `docs/progress/` and has never been served. The tree was found and prepared; nothing has ever been published from it. |
| §1's condition "if the registry has no state-transition verb, §1 stops and publication waits" | **Not met, and correctly so.** The state machine and `transition_state` both exist. Only a `verified → published` CLI wrapper is missing, which is not the same claim. §1 did not stop. |
| Decision 3's "`verified → published` **in the publish commit** with an event carrying the commit hash" | **Unachievable as literally worded**, and the task's own decision 4 shows why: nothing can name the commit that contains it. Done as: commit, then stamp the transitions with that sha (§1). |
| Decision 4's "Title page carries … the git commit" | **Done as the commit the build READ**, labelled `built from`, with the relation to the publishing commit stated in the same sentence. |
| Decision 2's "the index prints the six verdicts **outside the agency matrix** with the reference-host caveat" | **Not reachable**; the index prints, in its place, that the row is not measured and why. It prints no verdict — see §7. |
| the ordered list of what publishes (decision 1) | **Right, and shipped verbatim in that order.** |

## 5. The one thing this task got wrong, and the gate that caught it

The four Results computed from `scan_matrix_2026-09-10` are `COMPUTED_FROM` a DataFile whose
registered path — `state/scan_matrix_2026-09-10.json` — **the repository does not hold.** The
first re-derivation pass "restored" it by re-running `scan_report` for real.

**That was wrong, and `make gate-task` said so: 3 failed, 8 errors.** The absence is a
*decision*, not an omission. `scan_2026-09-10` was measured and deliberately never reported —
the judgement of record is the re-judgement `_rj2` — and `tests/test_scan_figures.py::matrix`
**skips the whole figure suite on exactly that absence**, with a docstring saying so
(`cc_tasks/2026-09-10_harness_v5_blind.md` decision 6: *"a gate that cannot distinguish 'the
figures are wrong' from 'there are no figures yet' is a gate that trains its reader to ignore
it"*). Materialising the file turned eight documented skips into eight errors, because the base
cycle never registered the pooled per-leg rates a figure resolves, and it broke
`test_the_denominator_is_per_leg_and_the_page_says_so`, which asserts the progress page states
the live cycle's denominator range.

**Fixed at the cause, not at the symptom.** The re-derivation now points `scan_report`'s matrix
write at a temporary tree (and removes the Tier C sibling only if the run created it), so the
arithmetic is still the generator's and the side effect whose absence is a recorded decision is
no longer produced. The two files were deleted, `scripts/check_protected_publish_l0.sh` now
carries a comment saying why `state/scan_matrix_2026-09-10.json` must never appear in its
allow-list, and the suite returned to 7 passed / 15 skipped on the targeted rerun.

**The underlying registry defect is NOT patched here, it is recorded.** Four published Results
name a provenance path nothing writes and nothing holds. Rather than leave a stranger to
discover a dead link, `data/results_tagged.json` now carries `present_in_repository` on every
provenance reference and a top-level `provenance_paths_absent`, which currently reads
`["state/scan_matrix_2026-09-10.json"]`. **That is a finding for the next task** — either those
four Results should be `COMPUTED_FROM` the cycle payload the repo does hold, or the DataFile
should name it — and it is one gate per task, so it is not fixed inside a publication task.

## 6. The gate (§3), clause by clause, with the log that carries each

| clause | result | log |
|---|---|---|
| Every tagged Result `verified` then `published`, each with events | **PASS** — 59 and 59; graph re-queried after the fact (§1) | `logs/publish_l0_rederive.log` |
| Re-derivation reproduces every tagged value | **PASS** — 59 of 59, `"gate": "PASS"` | `logs/publish_l0_rederive.log`, `state/rederive_tagged_2026-09-12.json` |
| Every index link resolves **on the live host** | **NOT REACHABLE** — the host serves nothing (block, on top). Asserted instead against the tree: every relative `href` on the index, and every `<loc>` in the sitemap, resolves to a file the tree holds | `tests/test_publication.py` |
| The self row registered and printed | **STOPPED** under decision 5. The index prints the absence and its reason; **no verdict is printed** | §7 |
| `robots.txt`, `llms.txt`, sitemap present and parseable | **PASS** — robots names all 8 crawlers and disallows nothing; `llms.txt` is in the llmstxt.org shape (H1 + blockquote + linked lists); the sitemap parses as XML and its 18 `<loc>`s all exist | `tests/test_publication.py` |
| `CITATION.cff` validates | **PASS**, as defined in §2 (required-key + type + agreement; no validator installed, none fetched) | `tests/test_publication.py` |
| PDF numeral-multiset gate, tag-coverage lint, versioned title page | **PASS** — `gate: PASS`, `bare_numerals_in_prose: []`, `unresolved_tokens: []`, `missing_fragments: []`, `fatal_reference_errors: []`; `test_report_pdf` 2 passed; 14 pages total / 6 prose, unmoved by the version block | `logs/report_pdf.log` |
| Socket counter shows the published host only | **PASS, and stronger** — no scan ran, so there is no socket counter to read; the only hosts contacted at all were `brockwebb.github.io` (6 requests, all 404) and the git remote. `corpus/` byte-identical | `logs/publish_l0_protected.log` |
| `make gate-task` | **PASS** — 2,016 passed, 17 skipped, 19 deselected, 12 xfailed, **376.96 s**; then 16 of 16 payloads re-derive, 6.55 s | `logs/publish_l0_gate_task.log` |
| `make guards` | **PASS** — 25 passed, 15.84 s | `logs/publish_l0_guards.log` |
| `make gate-full` (detached, logged, polled to EXIT) | **PASS** — 2,035 passed, 17 skipped, 12 xfailed, **1,316.96 s (21:56)** | `logs/publish_l0_suite_full.log` |
| `seldon verify` | **PASS** — all checks passed, 34,473 events readable | `logs/publish_l0_verify.log` |
| Protected paths | **PASS** — harness, `corpus/`, `events/`, the record, the skeleton, section prose, the report fragments and every published matrix byte-identical to HEAD | `logs/publish_l0_protected.log` |

Every log above carries its own `EXIT=0` line and was written before this file was.
`logs/` is gitignored; what ships is this file quoting it.

**The published matrices being byte-identical is not housekeeping — it is the re-derivation
claim.** The gate re-ran `build_l0_matrices` for the snapshot cycle into the *shipped* paths on
purpose, so a generator that did not reproduce its own output would have failed the protected
check rather than passed quietly.

## 7. What the index says where the self row goes

Verbatim, because a reader of this file should not have to fetch the page to know what was
published in the place a verdict was supposed to be:

> **Not measured.** The six host-level checks have not been run against this host, because at
> the time of this build the host was not serving this tree: GitHub Pages is not enabled for the
> repository (`has_pages: false`), and every path under
> `https://brockwebb.github.io/ai-readiness-kg/` answered HTTP 404. A verdict cannot be invented
> for a host that does not answer, and a placeholder row on a page whose whole subject is
> publishers who claim more than they serve would be the worst possible entry. The row appears
> here as soon as the scan has been run.

`tests/test_publication.py::test_the_self_row_is_measured_or_says_it_is_not` enforces the
either/or: when `state/self_l0_<cycle>.json` is absent the page must carry that block and must
contain **no** verdict cell; when it is present the verdicts must render. The builder reads
that file and never invents one.

## 8. What changed

**New:** `scripts/rederive_tagged_results.py` (the §1 gate), `scripts/publish_result_states.py`
(the two state moves), `scripts/build_l0_site.py` (the tree), `scripts/check_protected_publish_l0.sh`,
`tests/test_publication.py` (22 tests), `docs/reports/publication.yaml`, `CITATION.cff`,
`.zenodo.json`, and under `docs/`: `index.html`, `robots.txt`, `llms.txt`, `sitemap.xml`,
`.nojekyll`, `data/` (6 files).
**Modified:** `scripts/build_l0_report.py` (the generated version block and its two helpers),
the built report markdown and PDF, `seldon_events.jsonl` (118 transition events + 2 idempotent
`link_created` re-assertions from driving `register_l0_report_results`, whose
`_link_derived_from` MERGEs).
**Zero edits** to rule modules, harness runtime, stored payloads, cycle evidence, targets,
figures, section prose, the skeleton, the record, `corpus/`.

## 9. What the next task should pick up

1. **The operator enables Pages** (the one setting, §"THE BLOCK"). Then the self-scan runs:
   a one-host frame, `run.py` through its normal path, verdicts registered
   `self_l0_<leg>_<cycle>` and dropped at `state/self_l0_<cycle>.json`, which the site builder
   already reads. **Author it knowing §3:** on a project Pages site four of the six legs will
   measure `brockwebb.github.io` rather than this publication, so the task either takes a host
   of its own first, or it registers the row with that limitation on its face.
2. **The dangling provenance path** (§5): four Results `COMPUTED_FROM` a DataFile naming
   `state/scan_matrix_2026-09-10.json`, which the repository deliberately does not hold.
   Re-point them at the payload, or re-point the DataFile. `provenance_paths_absent` in the
   published data is the standing measurement of it.
3. **A licence.** The repository carries no `LICENSE`, so `CITATION.cff` and `.zenodo.json`
   declare none — and a declared licence is one of the things this instrument measures other
   publishers for. That is a value input and the operator's to set; nothing here guessed one.
4. **The DOI**, when he wants it: `.zenodo.json` is prepared and no deposit was made.
