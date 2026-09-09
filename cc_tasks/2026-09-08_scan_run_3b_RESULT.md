# RESULT — scan-run-3b: the first cycle over the whole frame

**Task:** `cc_tasks/2026-09-08_scan_run_3b.md` (no addenda exist; globbed at dispatch and again
before §2).
**Date:** 2026-09-09 UTC
**Cycle:** `scan_2026-09-09`, `params_hash 7ee55f512e8473e6d74ab8c0d089d694078baa8548b60f2b5f22fed66728d6a6`
**Spend:** zero model calls.
**Network:** 2,341 requests, identified UA `0.2` (DD-060), 1 req/s per host, robots obeyed, one
worker. **24 netlocs were contacted, not 22 — see §2, which is the first thing in this report
that is not a number.**

---

## 1. The gate — §3

**PASS on all four clauses.**

| clause | result |
|---|---|
| Byte-identical re-derivation, this cycle | **731 recorded / 731 rederived**, identical |
| …and all seven prior payloads | identical, each under **its own** rules and params |
| Zero Tier C Findings outside `params.tier0.legs` | **0** |
| Zero duplicate Finding identities across rows of one host | **0** |
| Hygiene suite green | 13 passed |
| `git status --porcelain corpus/` | only this cycle's 443 promoted bodies |

`observed_on_missing_document` is **0**, and getting there was a defect of mine: §2's first
projection returned **957**. Decision 3 added two synthetic id kinds (`home:`, `machine:`) and
`publish.py::project()` still recognised only `control:` and `host:`, so 957 observations of
ordinary host-level surfaces — which have no `:Document` and need none — were counted as
integrity failures. The check was measuring its own staleness. `SYNTHETIC_PREFIXES` is named
once now; `host_observations` went 94 → 1,051 and the missing count to 0.

**Nothing was registered before this section was written.**

## 2. The contact bound was exceeded, by two requests, and the scanner was right

The task and the dispatch both say: contact only the 22 netlocs of `scan_targets_fss_2026-09`
v2. **24 were contacted.** The two extra are `data.gov` and `samhsa.gov` — the apex domains of
`www.data.gov` and `www.samhsa.gov` — at **one request each**, both `robots.txt`, no content.

The cause is on the record and is not a bug:

```
www.samhsa.gov/robots.txt  →  Sitemap: https://samhsa.gov/sitemap.xml
www.data.gov/robots.txt    →  Sitemap: https://data.gov/sitemap.xml
```

A5 measures discovery by following the host's **own** declared sitemap, and RFC 9309 obliges
this scanner to read a host's `robots.txt` before fetching anything from it. Those two sites
declare their sitemap on a sibling netloc, so obeying both rules at once requires one request
to each sibling. Only `robots.txt` was fetched — the count is 1, not 2 — so no sitemap was
retrieved from either.

**The premise that cannot hold is "contact only this list" while the instrument follows
declared sitemaps.** A host may declare one anywhere, and honouring the declaration is what A5
measures. The choice is between a closed contact list and a discovery leg that reads what the
host actually says; this cycle took the second and I am reporting it rather than having chosen
it. Cycle 4 should settle which — `params.frame` could bound sitemap-following to the roster
and record a `sitemap_off_roster` observation instead, which would make the refusal a
measurement in its own right.

## 3. Tier A — 16 agencies, 55 surfaces

| leg | pass | fail | error | n | rate |
|---|---|---|---|---|---|
| A4 robots.txt | 33 | 2 | 4 | 35 | **0.943** |
| A11-declared | 32 | 3 | 4 | 35 | **0.914** |
| A10 deep link / bogus route | 24 | 8 | 7 | 32 | **0.750** |
| A5 discovery | 6 | 29 | 4 | 35 | 0.171 |
| A3 bulk | 6 | 30 | 3 | 36 | 0.167 |
| B3 without JS | 5 | 30 | 4 | 35 | 0.143 |
| G1-D error fields | 5 | 30 | 4 | 35 | 0.143 |
| D4 catalog | 2 | 32 | 5 | 34 | 0.059 |
| **A1, A2, A6, A8, A9, D1, F4** | **0** | 34–36 | 3–5 | 34–36 | **0.000** |

Seven legs at zero, upper bound 0.10. The three tier-0 legs that ask what a HOST declares —
robots.txt served, machine layer declared, deep links behaving — are where the federal
statistical system does well. Every leg that asks what a PRODUCT offers a machine — an API, a
bulk download, structured markup, a licence, a changelog, a declared vintage — is at or near
zero across sixteen agencies.

A12 (candidate, in no fraction): **14 pass / 4 fail / 1 error** across 19 hosts — and that
block **pools the two tiers**, which is a defect of mine and §8 item 5. Decomposed: Tier A is
**11 pass / 4 fail / 1 error** over its 16 hosts, and all three Tier C reference hosts pass.
The registered `scan_a12_*` Results carry the pooled figure and name their hosts individually;
they are bound at that value (AD-028) and are not re-bound here.

## 4. Tier C — reference hosts, tier-0 legs only

| | A4 | A11-declared | A10 | A5 | G1-D |
|---|---|---|---|---|---|
| pass | 6 | 6 | 4 | 0 | 0 |
| fail | 0 | 0 | 2 | 6 | 0→6 |

All six Tier C surfaces serve `robots.txt` and declare a machine layer. **`data.nist.gov` and
`open.gsa.gov` both fail A10** while all three homes and `catalog.data.gov` pass it. All six
fail A5 discovery, and all six fail G1-D — which is the expected and uninteresting answer, a
catalog carries no estimates and so no error measures. Reported in F6, in no Tier A denominator,
on no agencies × legs matrix (DD-059).

The catalog finding compounds the one already on the record: `catalog.data.gov`'s CKAN action
API answered 404 at every documented endpoint on 2026-09-08, and its host now also fails
discovery. That is Tier C doing exactly the job ADDENDUM-01 declared it for.

## 5. What moved against cycle 2, and whether the instrument or the host moved it

**The instrument, overwhelmingly, and the frame moved too.** Four legs changed rule between the
cycles — A1 v3→v4, A3 v4→v5, A8 v3→v4, A10 v2→v3 — and the frame went from 13 agencies plus
StatCan to 16 plus 3 reference hosts, on 22 netlocs. F5 marks the four rule changes and its
note says the frame differs; a reader who compares a rate across those two cycles is comparing
two instruments over two populations.

**The generation-6 rules fired on real hosts, not only on fixtures**: 8 Findings carry a blind
count (4 A1, 4 A3), and A1 returned `error` 3 times and A8 5 times where their predecessors
would have returned `fail`. That is the harness-v4 §7.1 defect, closed and demonstrated on
federal surfaces rather than argued.

## 6. Refusal consistency — a finding about accessibility, not a footnote

`www.bls.gov`, `www.bts.gov` and `www.ssa.gov` refused an identified, robots-compliant client
again. That is now **five consecutive measurements** — the 2026-09-07 pre-flight, cycles 1 and
2, the 2026-09-08 frame pre-flight, and this cycle — under two user-agent strings and across
three days. It is not transient and it is not a sampling accident: three of sixteen recognized
statistical agencies do not serve a client that identifies itself and obeys their own
`robots.txt`. Their surfaces stay in the frame and return `error`, and the instrument has never
retried under another identity (DD-060).

`www.federalreserve.gov` serves no `robots.txt` (404) and `www.eia.gov` answered 503 on its home
in both pre-flights; this cycle observed EIA normally, so the 503 was transient and is recorded
as observed rather than pre-judged.

## 7. Requests per netloc

2,341 requests across 24 netlocs. Heaviest: `www.nass.usda.gov` 247, `www.bea.gov` 247,
`www.census.gov` 246, `www.ers.usda.gov` 243, `www.cdc.gov` 219. The three new Tier C machine
netlocs answered the identified client normally: `catalog.data.gov` 13, `data.nist.gov` 13,
`open.gsa.gov` 13. Refusing hosts still cost requests — `www.bls.gov` 38, `www.bts.gov` 37,
`www.ssa.gov` 37 — because a refusal is measured, not assumed.

`error_class_unknown` = **1** for the cycle. One observation the classifier's map does not name;
it is counted and reported rather than absorbed into a neighbour, which is what `unknown` is
for. Running it down is a cycle-4 item.

## 8. The suite — eight failures, and none of them was a threshold

§6's full run returned **8 failed, 1601 passed**. Every one is triaged below with what it
turned out to be. **No threshold was moved and no expectation was rewritten to match an
output**. Four were real defects — two in the code, two in a test's own population filter or
exemption list — and four were tests pinned to a fact this cycle changed by design, rewritten
to assert the property instead of the fact. Where the stale thing was a list a test kept its
own copy of, it now reads it from the module that owns it.

| test | what it was | fixed where |
|---|---|---|
| `test_framework_projection_roundtrip::…cell_for_cell` | **Real, mine.** §5's framework write-back edited `ai_readiness_framework.json` and no projection followed it, so `ind:E5` still named cycle 2 in the graph. CLAUDE.md: *a write-back is not finished until a projection follows it.* | ran `scripts/load_framework_graph.py` |
| `test_scan_figures::…the_things_the_task_asked_them_to` | **Real, mine.** `scan_report.matrix()` filtered its `rows` by tier and left `agencies`, `agencies_without_surfaces` and `agencies_wholly_unobservable` computed over the whole payload — a Tier A matrix listing 19 agencies over 16 agencies' rows, which is the count DD-059 says the reference hosts are never inside. It read as "F2 omits GSA": the figure drew the 16 it had rows for and was checked against the wrong roster. | `scripts/scan_report.py` |
| `test_scan_figures::…re_derive_from_the_graph` | **Real, in the test.** Its Cypher excluded `control:` and nothing else, and cycle 3 introduced a third population. Six differences, each exactly the Tier C rows (A4 39 vs 33, A11-declared 38 vs 32, A5 fail 35 vs 29, G1-D fail 36 vs 30, A10 28/10 vs 24/8). Excluding them alone would have left `scan_tierc_*` the one family nothing re-derives, so both families are now checked, each against its own population. | `tests/test_scan_figures.py` |
| `test_scan_run_2::…grounded_in_recorded_text_or_a_status` | **Real, in the test, and the same shape as the defect `errors.py` exists to close.** It carried `robots_disallowed` as a literal exemption; `off_host` is the same thing one policy layer up and arrived as the second member of a set nobody had named, so 164 correctly recorded observations read as ungrounded. `errors.CLASSES` now declares `not_fetched` beside `blind`, and the test reads `errors.NOT_FETCHED`. | `scan/errors.py` + the test |
| `test_scan_run_2::…uncited_set_only_shrinks…` | **Stale pin.** `retention.NAME` is deliberately bare: it is the *pre-flight* census, what the store held uncited when `promote_evidence` was installed. Two clauses read it as this cycle's `before` figure, which it was for exactly one cycle. Cycle 2 cited one of those bodies, so cycle 3's `before` is 417 against a registered 418 — **the property working, reported as the property failing.** The arithmetic now closes against `uncited_before_this_cycle`, and `registered` is used only for what it can still say. | `tests/test_scan_run_2.py` |
| `test_scan_harness::…judged_only_by_host_legs` | **Stale pin.** `all(t["admitted"] for t in docs)` was true only while the synthetic `host:` row was the sole documentless surface. Targets v2's `home:`/`machine:` rows are synthetic and documentless *by design*. Replaced by the property that matters and that actually broke this cycle: every target has a `:Document` **or** an id `publish.SYNTHETIC_PREFIXES` places. | `tests/test_scan_harness.py` |
| `test_scan_frame::…outside_the_nineteen_hosts` | **Stale pin.** 19 is the ROSTER's hosts; the target list names 22, because all three declared Tier C machine entry points sit on their own hostname. The row check already carved them out — the pin was measuring the id scheme, not the frame. Now asserts the composition. | `tests/test_scan_frame.py` |
| `test_scan_frame::…preflight_covers_exactly…` | **Stale pin, and the tempting fix was the wrong one.** The pre-flight measured the roster's 19 on 2026-09-08, before targets v2 existed. Back-filling three rows into a registered artifact so an equality holds would be editing the record to fit the test; the test now says the pre-flight covers the roster and not the machine entry points, which cycle 3 contacted for the first time. | `tests/test_scan_frame.py` |

Two things fell out of the triage that no test asked about and that are reported rather than
carried:

* **The progress page claimed the wrong client identity.** `scripts/framework_progress.py`
  printed `ai-readiness-kg-scanner/0.1` as a hardcoded literal and kept printing it after
  DD-060 moved the identity to `0.2` — a published page making a false statement about how the
  measurement beneath it was taken. It now reads `params.manners.user_agent`.
* **`retention.census(cycle)` is exact only for the MOST RECENT cycle.** Asked about cycle 2
  today it answers `promoted_by_this_cycle: 603` where the true figure was 160, because
  `tracked` is read now and `before` at the publishing commit — cycle 3's 443 bodies land in
  the difference. Its one caller always asks about the current cycle, where it is exact, so
  nothing on the record is wrong; the shape is the same two-moments trap that made this
  census red once already. Cycle 4 item.

## 9. The push is blocked, and the block is a real property of this design

`git push` was refused by **GitHub push protection**, which found what it calls a *Mapbox
Secret Access Token* in **eight evidence bodies**, all committed at `7a3bdc4`, all captured
from `www.nist.gov` — the Tier C reference host this cycle added. The commit is made and
verified; it is local and unpushed.

**What the string actually is.** One token, identical in all eight bodies:

```
"nist_map":{"mapbox_access_token":"pk.eyJ1IjoidGltd29vZCIsImEiOiJjbXIw…"}
```

A Mapbox **`pk.`** token — a *public* token, designed to ship in client-side JavaScript and
downloaded by every visitor to NIST's homepage. Mapbox's secret tokens carry the `sk.` prefix;
`grep` over the whole evidence store finds **zero** `sk.` tokens and exactly **one distinct**
`pk.` token. The detection is a prefix false positive on somebody else's already-public value.
No credential of this project is involved, and none has ever been committed.

**Why this is structural rather than an accident.** Invariant 3 and DD-058 require the repo to
hold the whole body a Finding cites, `corpus/evidence/scan/` is the one `corpus/` lane that is
tracked for exactly that reason, and the digest of those bytes IS the identifier every
Observation cites. Redacting the token changes the bytes, changes the sha256, and severs eight
Observations from their evidence; dropping the bodies leaves eight verdicts uncitable. Both
"fixes" trade a false positive for a broken audit trail. **Federal home pages embed third-party
public API tokens, and a scanner that retains whole bodies will keep capturing them** — cycle 3
is the first cycle whose frame included a host that does it, not the last.

**What was not done.** No byte was redacted, no body dropped, and no commit that had already
been pushed was rewritten.

**How it was resolved — operator's decision, 2026-09-09.** A repo-level
`.github/secret_scanning.yml` carrying `paths-ignore: corpus/evidence/scan/**`, rather than the
per-detection unblock GitHub offered: the block is structural and will recur every time the
frame gains a host that ships a public token, so the decision belongs on the record once
instead of as a click per cycle.

I had flagged that I could not confirm push protection honours `paths-ignore` — only that
secret-scanning *alerts* do. **It does, and both halves of that are now checked rather than
assumed.** GitHub's own exclusion doc says a `secret_scanning.yml` closes alerts in the named
directories "and exclude these directories included in push protection", and the push itself
then confirmed it. The doc does **not** say which branch the file is read from, so the
exclusion was landed on `main` on its own commit (`9f8ebc0`) *before* the cycle commits were
offered, and the two cycle commits were rebased onto it — which removes the question rather
than betting on an answer, and is why their hashes are `7a3bdc4` and `0c24004` and not the
ones the first push attempt carried. Nothing already published was rewritten.

`corpus/evidence/frame/` and `corpus/quarantine/evidence_scan_fixture/` hold third-party
captures for the same reason and are deliberately NOT on the list: neither has blocked a push,
and widening an exclusion past the thing that actually failed is how an exclusion stops meaning
anything. The file says so on its face.

§6 is complete: suite green, `seldon verify` green, protected paths empty, `seldon cc complete`
recorded, committed and **pushed**.

## 10. Premises this task got wrong

1. **"Contact only the 22 netlocs."** Cannot hold while A5 follows declared sitemaps. §2.
2. **Decision 3's id scheme was right and its consequences were not carried through.** Adding
   `home:` and `machine:` needed `publish.py`'s synthetic-prefix list to move with it. Mine. §1.
3. **§2's "the 65 surfaces".** 64 were scanned: the unadmitted EIA flagship has no `:Document`
   and was skipped with its reason, as decision 2 provides. Decision 2 also says its
   `robots_disallowed` reason is "on the Observation" — no Observation exists, because creating
   one would have put an un-documented target on the log and made
   `observed_on_missing_document` non-zero by construction. The reason is on the target row
   instead.
4. **§4's `blind_links` per leg** assumed every leg could report one. Only A1 and A3 do
   (`blind_pointers` for A8), so the Results exist for those legs and not as a uniform family.

### Mine

5. **The tier split was applied to the rows and not to everything computed beside them.**
   `matrix()` filtered `rows` and left three agency fields over the whole payload, and `a12()`
   was never made tier-aware at all — so the Tier A matrix listed 19 agencies and the A12
   block pools 16 Tier A hosts with 3 Tier C reference hosts. The matrix fields are corrected
   (§8) and no registered value moved: the reporter re-ran at **181 of 181 already at this
   value, 0 failed**. **The A12 pooling is NOT corrected**, and that is a decision worth
   stating rather than a thing left undone: `scan_a12_pass_2026-09-09` is bound at 14 and a
   Seldon Result name is bound once (AD-028), so re-registering it at 11 is refused by design
   and would be number mutation if it were not. The decomposition is on the face of §3
   instead, and cycle 4 registers the tiers separately from the start.
6. **A published page carried a hardcoded client identity** and went stale against DD-060.
   §8.
7. **Five of the eight suite failures were tests I wrote or edited in the previous three
   tasks, pinned to facts those same tasks were about to change.** That is a pattern, not five
   incidents: a test written the day a fact is established tends to record the fact rather
   than the property. Each rewrite above says which property it now asserts.

## 11. Verification

```
six-fixture control gate       PASS, ordering asserted against the first real host
re-derivation                  731/731 this cycle; 7 prior payloads identical
Tier C outside tier0.legs      0
duplicate Finding identities   0
observed_on_missing_document   0   (957 before the fix in §1)
projection                     7,971 observations, 3,309 findings, 36 rules, 12,709 supports,
                               rules_without_indicator []
registered                     181 cycle Results + 76 figure-input Results, 0 failed
figures                        6 created, 276 CONTAINS/GENERATED_BY links, 0 failed
full suite                     1610 passed, 0 failed, 2 skipped (2924 s), after the eight
                               triaged in §8. The count is 1610 and not 1609 because one
                               clause became its own test: §8's `admitted` pin was replaced by
                               a check that every target has a :Document or an id the
                               projection places.
seldon verify                  All checks passed. 29,026 events readable; 82 task source files
                               resolve; precedence 12 edges, acyclic.
push                           refused once by GitHub push protection on eight cycle-3 evidence
                               bodies from www.nist.gov, all carrying one Mapbox PUBLIC (`pk.`)
                               token that NIST ships to every visitor. Zero `sk.` tokens in the
                               store; no credential of this project is involved. Resolved by
                               `.github/secret_scanning.yml` landed on main first (9f8ebc0);
                               pushed at 7a3bdc4 + 0c24004. §9.
git diff on protected paths    EMPTY on assessment/harness/scan/rules/ (every shipped module,
                               v1 through v6), assessment/cq/, and the targets DataFile.
                               events/ APPEND ONLY: batch-033_framework.jsonl +1/-0, the
                               `framework_writeback_measured` event for this task.
                               corpus/ clean — 0 paths, this cycle's 443 promoted bodies
                               already committed at 7a3bdc4.
framework projection           re-run after §5's write-back; the roundtrip gate that makes
                               Cypher verification of framework state valid is green
                               (7 passed). §8, first row.
```

## 12. What cycle 4 needs

1. **Settle the sitemap-following bound** (§2): either sitemap-following is roster-bounded and
   an off-roster declaration becomes a recorded observation, or the contact bound is stated as
   "the roster plus whatever the roster's own robots.txt declares".
2. **The one `unknown` error class.** §7.
3. **The 7 agencies still pending an operator flagship declaration.** Their thin rows are
   measurements and they are also 7 of 16 agencies contributing host-level evidence only.
   `docs/design/fss_flagship_shortlist.md` is written and waiting.
4. **Seven legs at zero across sixteen agencies** is the finding the report draft is for, and
   it wants the Hanley–Lippman-Hand rule-of-three caveat stated at n ≈ 35 rather than n ≈ 23.
5. **A10's 7 errors** are the blind-probe guard doing its job on real hosts; whether those
   seven surfaces are permanently unobservable or transiently so is unmeasured.
6. **A12 registered per tier from the start** (§9 item 5), so the candidate leg's block stops
   pooling the reference hosts with the agencies. Cycle 3's names are bound; cycle 4's are not
   yet.
7. **`retention.census(cycle)` answers correctly only about the most recent cycle** (§8). Its
   `before` is read at a commit and its `tracked` is read now, and the mismatch is invisible
   until someone asks it about an older cycle — which the standing test never does and a
   future reader eventually will.
8. **Nothing on push protection — it is settled** (§9). `.github/secret_scanning.yml` excludes
   `corpus/evidence/scan/**` and the exclusion is verified to hold at push time. What cycle 4
   should watch is the *other* two tracked capture lanes: `corpus/evidence/frame/` and
   `corpus/quarantine/evidence_scan_fixture/` are the same class and are deliberately not on
   the list, so the first push either of them blocks is a decision already made, not a new one.
