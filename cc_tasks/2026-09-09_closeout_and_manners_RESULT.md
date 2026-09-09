# RESULT — closeout, then manners: robots-first, and the contact bound is the site

**Task:** `cc_tasks/2026-09-09_closeout_and_manners.md` (no addenda exist; globbed at dispatch
and again before §3).
**Date:** 2026-09-09 UTC
**Spend:** zero model calls. **Network: none.** Loopback fixtures only. No federal host was
contacted.

---

## 0. §0 was already done, and not by this task

**The dispatch said "resume from §1; §0 is already complete on the record" and asked, if I had
stopped after §0 last time, at which line and why. I did not stop after §0. I never started
this task.** When it was registered I was finishing `report-draft`, and I said at the time that
its file was untracked and not mine to touch.

§0's substance was done as the closing steps of `report-draft` itself, before this task file
existed. Verified on the machine rather than taken from the dispatch:

| §0 clause | state | where |
|---|---|---|
| full suite | 1614 passed, 0 failed, 2 skipped | report-draft RESULT §6 |
| protected-paths diff | recorded, clean | report-draft RESULT §6 |
| both `<SUITE>` / `<PROTECTED>` placeholders replaced | no placeholder remains | grep |
| `seldon cc complete e1b7cd4b` | task state `completed` | Cypher |
| commit, push | `eaa0f7e`, pushed | `git log origin/main..HEAD` empty |

**The task file's own authoring premise is therefore stale, and it says so on its face:**
"Verified on the graph: `e1b7cd4b` still `proposed`; RESULT §6 carries `<SUITE>` and
`<PROTECTED>` unfilled; no `cc complete` recorded." Every clause of that was true when Desktop
wrote it and false by the time it was dispatched. Nothing was reconciled silently; §0 was
re-verified, not re-run, and no file it names was touched again.

## 1. The gate — §3

**PASS on all five clauses.**

| clause | result |
|---|---|
| Seven-fixture control gate against derived tables | **PASS**, zero unexpected verdicts on all seven, 112 control Findings |
| `unknown` = 0 | **0** — the class appears in no fixture's `error_classes` |
| Byte-identical re-derivation, all **eight** prior payloads | 8 passed, each under its own rules and params |
| Replay of cycle 3's request log through the new policy | exactly **2** requests named, by URL; see §4 |
| Hygiene green | 13 passed |
| Full suite | **1624 passed, 0 failed, 2 skipped** (3338 s), 2026-09-09 |
| `seldon verify` | All checks passed, 2026-09-09 |

The eighth payload was not in the standing set. `scan_2026-09-09` was measured, committed and
cited in a RESULT, and nothing would have noticed a rule change that stopped it re-deriving —
the same position the two re-judged payloads were in one task ago. It is in `PRIOR_CYCLES` now
at 731 Findings.

## 2. The fixture, and the mechanism chosen

`sitemap_on_sibling`: a host whose `robots.txt` declares its sitemap on a **second netloc of the
same site**. It serves everything `passes_all` serves through a one-file overlay, because it
differs from a well-formed surface in exactly one line and copying eleven files would make two
definitions of "well formed".

**Two ports on `127.0.0.1`, and the task asked which mechanism and why.** The defect needs two
properties at once and this is the only mechanism that gives both using nothing but loopback:

* **Different netloc**, so the sibling has its own `robots.txt` that a compliant client must
  read before touching it. One server cannot express "the declared URL is somewhere this cycle
  has not read robots for".
* **Same site**, because the WHATWG URL and Fetch standards define a site as scheme plus
  registrable domain with the **port excluded**, and an IP-literal host has no registrable
  domain, so the host itself is the site key. That is the same relation `www.samhsa.gov` has to
  `samhsa.gov`, so the fixture reproduces the real shape rather than a neighbouring one.

Two hostnames would have needed `/etc/hosts`, which is machine state a test may not depend on.
Two schemes would have changed the site.

**Under the code as it stood, the sibling's first and only request was `GET /sitemap.xml`.**
After the fix it receives `GET /robots.txt` and then `GET /sitemap.xml`. Both were driven
through real HTTP, not asserted over source.

## 3. §1's other half: the derivation could not see it, and now can

`fixture_expectations.py` derived **blindness and nothing else**, which is correct and
insufficient: a fixture makes a leg blind, and no fact about blindness says whether a request
was polite. §1 anticipated this and asked for the derivation to be extended, which it was, in
two ways:

* `declared_sitemaps` joined `links` and `pointers` as a **dereference parameter**. That is the
  signature of "URLs this function did not choose", `sitemap.fetch` has it, and while the
  cycle-3 defect ran along that probe the derivation could not see the probe at all.
* A new derivation of **who gates on robots**, read from source: whether the fetcher gates every
  request, and which collectors issue one without a gate. The invariant needs no pre-registered
  table and has no threshold — the set is empty — because a request no collector gates is a
  request the fetcher must.

Run before any code change, it reported the defect as a difference and reported it **wider than
the task's premise**:

```
fetcher gates every request : False   (raw_get False, raw_head False)
A5   sitemap.fetch          ungated, dereference=True    <- the cycle-3 defect
A10  lighthouse.fetch       ungated, dereference=False
D4   dcat.fetch_catalog     ungated, dereference=False
A4/A5/A11-declared/A12  robots.fetch  ungated, and correctly so (the carve-out)
```

**Three collectors, not one.** Only four of the eight request-issuing collectors ever called
the gate. After the fix: `fetcher gates every request: True`, ungated set empty.

## 4. The replay

Cycle 3's request log, replayed through the new policy:

```
requests issued                        2256
netlocs actually contacted               24   (agrees with the per-host counter)
netlocs whose robots.txt was fetched     22
contacted with NO robots read             2   https://data.gov/sitemap.xml
                                              https://samhsa.gov/sitemap.xml
requests the new policy would REFUSE      0
```

**§3 expected "exactly the two apex sitemap GETs" and named the right two requests with the
wrong verb.** The new policy refuses neither. Both apex netlocs are the **same site** as the
host that declared them, so decision 3 permits the fetch; decision 1 is what applies, and it
precedes each with a `robots.txt` read. The policy refuses nothing on this log and adds two
reads. Both numbers are registered, because "refused none" and "added two" are different claims
and only one of them was predicted.

## 5. Premises this task got wrong

1. **The dispatch's premise about §0.** §0 was complete, but not because I stopped after it.
   §0 above.
2. **The task file's own header premise** was true at authoring and stale at dispatch. §0.
3. **"the sitemap follower dereferences a declared URL ... `manners` gates on-roster hosts."**
   `manners.on_roster_host` was never wired into the fetcher at all, and the sitemap follower
   was one of **three** collectors issuing requests with no robots gate. §3.
4. **§3's "which requests it would have refused: expected exactly the two apex sitemap GETs."**
   Right requests, wrong verb: the new policy refuses none of them. §4.
5. **Decision 2's "the list snapshot's date is a registered param."** The bundled Public Suffix
   List carries **no date**: it is the raw list with an MPL header, and its file mtime is the
   install time. The resolver, its version and the snapshot's digest are registered instead,
   with a note saying why there is no date. A date recovered from an mtime would be a number
   that looks like provenance and is not.
6. **Decision 2's consequence was not anticipated, and it is large.** The frame's 22 netlocs
   collapse to **17 sites**. `www.ers.usda.gov`, `www.nass.usda.gov` and `www.aphis.usda.gov`
   are one site, `usda.gov`; BJS's site is `ojp.gov`; NCES's is `ed.gov`. "Every netloc under a
   roster site is in scope" therefore admits entire department domains, not the agency
   subdomains the roster was drawn around. Decision 4 protects the denominator and does its job:
   the frame's unit stays the body, and targets v3 publishes site, netloc and body counts
   separately so none can stand in for another. **The contact bound genuinely widened, and that
   is an operator decision this records rather than one it takes.**

### Mine

7. **My first replay reported 68 contacted netlocs against a true 24.** It counted every URL an
   Observation carries, and an `off_host` or `robots_disallowed` record carries a URL precisely
   because no request was made. 161 recorded exclusions became 44 imaginary hosts, including
   `facebook.com` and `youtube.com`. The filter is `errors.NOT_FETCHED`, read from the module
   that owns it. The number the task predicted was recoverable only after the filter was right.
8. **My fixture drivers wrote 29 fixture bodies into the committed evidence store**, because I
   ran collectors directly without `--evidence-root`. The standing guard is
   `tests/conftest.py`, which redirects the store under pytest and does not cover a script.
   Swept with `scripts/quarantine_fixture_evidence.py`, which recorded who wrote them; the
   store is clean and no cited body was touched. Same defect as harness-v4 §7.2, from the same
   cause, in a path the fix did not cover.
9. **The gate detector was wrong twice, in opposite directions.** A text search for `.allowed(`
   matched the phrase inside `robots.py`'s own comment explaining why a rule does not use it,
   and reported that collector as gated when it never calls it. Replacing it with an AST parse
   of the joined reachable source returned False for every collector, because concatenating two
   `def` blocks produces text that does not parse. Each source is parsed separately now. Both
   mistakes gave an answer with no relation to the code, and the second would have made the
   fixed fetcher read as ungated.

## 6. Verification

```
seven-fixture control gate     PASS, 0 unexpected verdicts, unknown = 0, 112 control Findings
re-derivation                  8 of 8 prior payloads byte-identical, each under its own rules
replay                         2 netlocs contacted without a robots read, named by URL;
                               0 requests the new policy would refuse
manners unit tests             9 passed (same-site sibling, off-site declaration, robots-first
                               over every netloc, RULE-A5-v2 against v1, the replay)
derived tables                 7 fixtures, 0 differences, fetcher gates every request
hygiene                        13 passed; corpus/ clean after the sweep
tool map                       regenerated, then regenerates byte-identically
full suite                     1624 passed, 0 failed, 2 skipped (3338 s), 2026-09-09.
                               The first run of this suite was RED: 6 failed / 1618 passed,
                               six failures with four causes, every one of them unfinished or
                               wrong work in THIS task rather than a falsified threshold. They
                               were triaged and closed under
                               cc_tasks/2026-09-09_manners_closeout.md §0, whose RESULT carries
                               the triage. The one that matters: RULE-A5-v2 shipped without
                               consulting the blind guard, which the standing lint over rules/
                               caught.
seldon verify                  All checks passed, 2026-09-09. 29,473 events readable; 85 task
                               source files resolve; precedence 12 edges, acyclic.
protected paths                EMPTY on every shipped rule module: `rules/__init__.py` is
                               modified only to register V7 and `rule_a5_v2.py` is new, which
                               is the one way a rule may ship. No prior RESULT was touched.
                               events/ APPEND ONLY: batch-033_framework.jsonl +1/-0, the
                               framework write-back for RULE-A5-v2. corpus/ clean apart from
                               the quarantine reason.txt this task appended to.
```

## 7. What the next task needs

1. **The site bound is wider than anyone has looked at.** §5 item 6. Cycle 4 will treat every
   netloc under `usda.gov`, `ed.gov`, `ojp.gov`, `cdc.gov` and `nsf.gov` as in scope. That is
   the decision as written and it deserves a deliberate look before a cycle runs under it.
2. **`params.manners.same_host_only` and the site bound now say different things.** The netloc
   policy is still what `on_roster_host` applies to links; the site bound governs declarations.
   One of them should absorb the other, and this task did not do it because decisions 1 to 3
   did not ask.
3. **A guard that stops a SCRIPT writing into the evidence store**, not only a test. §5 item 8
   is the second occurrence from the same gap.
4. **Cycle 4 itself**, which this task deliberately does not run.
