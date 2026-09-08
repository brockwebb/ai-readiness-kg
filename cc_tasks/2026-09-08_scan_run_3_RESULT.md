# RESULT — scan-run-3: BLOCKED at §1.4. The six-fixture control gate failed, and it failed for the right reason.

**Task:** `cc_tasks/2026-09-08_scan_run_3.md` (no addenda exist; globbed at dispatch and again
before this was written).
**Date:** 2026-09-08 UTC
**Spend:** zero model calls.
**Network: none.** **Not one of the 19 hosts was contacted.** Every request this task made went
to `127.0.0.1`. The cycle did not run.

---

## 1. THE BLOCK

**§1.4's control gate is a hard stop and it did not pass.** `RULE-E5-v2` returned `fail`:

```
1 control verdict(s) were not as expected: resets_links_only:A8=fail (expected pass)
```

| fixture | unexpected verdicts | error classes |
|---|---|---|
| `passes_all` | none | `http_4xx`, `off_host` |
| `fails_all` | none | — |
| `refuses_identified_client` | none | `refused` |
| `resets_connection` | none | `connection_reset` |
| `invalid_route_unobserved` | none | `connection_reset`, `http_4xx`, `off_host` |
| **`resets_links_only`** | **`A8=fail` (expected `pass`)** | `connection_reset`, `http_4xx`, `off_host` |

`unknown` = 0 across all six. The two rules §1.2 ordered — `RULE-A1-v4` and `RULE-A3-v5` —
return `error` on the new fixture exactly as pre-registered. **The fixture built to catch one
defect caught a second one nobody was looking for.**

Per §3: no Results registered, no page, no cycle. RESULT, commit, push, stop.

### What the failure is

`RULE-A8-v3` reads a **blind** pointer probe as a **failed resolution**. Verbatim from the
control run:

```json
{"how": "href token", "matched_token": "latest.",
 "url": "http://127.0.0.1:58722/estimates-latest.csv",
 "status": null, "resolved": false, "note": "ReadError"}
```
> *"markup declares the vintage via dateModified, but none of the 1 latest-vintage pointer(s)
> resolves (first: … -> HTTP None)"* → **`fail`**

`status: null`, `note: ReadError` — the connection was reset; nobody observed whether that
pointer resolves. A8 scored the product as having a broken latest-vintage pointer.

**This is the third instance of one defect.** DD-052 §6 said `error` must never mean the
product failed. Harness-v4 added the mirror — `error` must never mean the product *passed* —
and fixed A10. This task's §1.2 fixed A1 and A3, which harness-v4 §7.1 had named and could not
touch. A8 is the same shape again, on a probe nobody had thought of as a link probe:
`v2clauses.follow_latest_pointer` dereferences with `raw_head`, so it is blinded by exactly the
condition `resets_links_only` creates.

### Why I did not fix it, and did not adjust the expectation

The task authorises new behaviour in a new module, so `RULE-A8-v4` would be permitted in the
letter. I stopped anyway, for two reasons and the second is the binding one:

1. §1.2 names A1 and A3. A8 is a different leg with its own control expectations across six
   fixtures, and shipping it inside a hard stop it caused is how a gate becomes advisory.
2. **No fix makes the pre-registered table right.** `resets_links_only:A8` was pre-registered
   `pass`; a corrected A8 would return `error` on this fixture, not `pass`. The table is wrong
   either way, and *"a task that fails a pre-registered threshold writes nothing and reports;
   the next task is authored from the failure, never by moving the threshold"* is the rule.
   Editing `pass` → `error` to get a green gate is precisely the move that rule forbids.

**The wrong expectation is mine.** I derived `resets_links_only`'s table from the rule source
believing only A1 and A3 probe with HEAD. `follow_latest_pointer` does too. The fixture is
right; my reading of which legs it would touch was not.

## 2. What §1.1–§1.3 completed and is on disk

**§1.1 — `params.tier0.legs` declared**, before the cycle that uses it, which is the point:

```yaml
tier0:
  legs: ["A4", "A5", "A10", "A11-declared", "A12", "G1-D"]
  candidate_legs_in_set: ["A12"]
```

The criterion is written down beside it: a tier-0 leg asks about a *host that publishes data*
rather than about a statistical product, which is what licenses the Tier C comparison (DD-059)
and what would stop being true above it. A12 is in the set and in no denominator (DD-054).

The figure assertion and the Tier C rendering block (§1.1's other half) are **not built** — they
were sequenced after a gate that stopped.

**§1.2 — two new rule modules and a sixth fixture, all working.**

* `RULE-A1-v4`, `RULE-A3-v5` (generation 6). A link probe whose class is blind is unobserved
  *for that link*; all blind → `error`; some blind → judged over the observed links with the
  blind count on the Finding; none blind → byte-identical to `v3`/`v4`. `off_host` is excluded
  as a scope boundary, not counted as blind. Predecessors untouched, in `REGISTRY`.
* Fixture `resets_links_only`: serves everything `passes_all` serves over GET and **resets
  every HEAD**. HEAD is the discriminator because the link probe is a HEAD and the page fetch
  is a GET, so it blinds exactly the links. Pre-registered A1 `error`, A3 `error`, rest as
  `passes_all` — and A1/A3 returned exactly that.

**§1.3 — not reached.** `cycle.name` and `cycle.targets` are untouched; no `params_hash` was
registered; `refuse_clobber` was not exercised. `params.cycle.name` still reads
`scan_2026-09-07b`, which is correct for a cycle that did not run.

## 3. Verification

```
six-fixture control gate            FAIL — resets_links_only:A8, above
tests/test_scan_harness_v4.py       green after the two consequential updates below
tests/test_scan_frame.py            green (12)
tests/test_scan_hygiene.py          green (13)
tests/test_scan_figures.py          green
full suite                          NOT RUN — the gate stopped before §2
seldon verify                       not run at this stage
git status --porcelain corpus/      clean; nothing promoted, nothing captured
```

Three tests moved as consequences of §1.1–§1.2, none of them the gate:

1. **The generation-4 lint** now accepts either blind guard — `unobserved_error` (one probe,
   returns the Finding) or `unobserved` (the predicate underneath). A rule judging a *set* of
   probes needs the predicate per link, not a Finding per link; requiring the wrapper alone
   would push A1-v4 and A3-v5 toward the coarser check, which is backwards.
2. **The fixture-roster test** is re-pinned at six and rewritten as a superset assertion, so the
   next fixture is one line rather than a failure that reads as a regression. It already had to
   be widened once when the fifth was added.
3. **The tool map** regenerated: `rules.CURRENT` moved for A1 and A3, and the map reads
   `CURRENT`. Byte-identical on re-check.

## 4. Premises this task got wrong

1. **§1.2's pre-registered table for `resets_links_only`.** Mine. `A8: pass` assumed only A1
   and A3 probe with HEAD; `follow_latest_pointer` does too. §1.
2. **§2's "the 65 surfaces".** Not reached, but the mapping would not have been 65 scanned
   surfaces, and the next task should settle it rather than discover it mid-run:
   * 3 Tier C **machine** rows point at `catalog.data.gov`, `data.nist.gov` and `open.gsa.gov`
     — hosts that are **not among the 19** in `scan_targets_fss_2026-09.hosts`. The dispatch
     constraint is "contact only the 19 hosts", so those three rows cannot be scanned as
     written. Either the 19 becomes 22 or the rows become unscannable; both are decisions.
   * 1 flagship row (`scan-eia-flagship-2-eia-survey-forms`) is unadmitted — `robots.txt`
     disallows it — so it has no `:Document` and can produce no Finding.
   * 19 `home` rows and 19 `well_known` rows both describe the same host. Cycle 1 and 2 gave the
     well-known row `doc_id: host:<netloc>`; if the home row takes the same id the two collide
     on any shared leg, and Tier C's tier-0 set includes A12, which the well-known row already
     carries. That needs an id scheme, not an improvisation.
3. **§4's `blind_links` per-leg Result.** Registrable now that A1-v4/A3-v5 carry the count, but
   the count lives in the Finding's reason text rather than a field, so registering it means
   parsing prose. A field on the Finding would be a schema change; naming it here.

## 5. What cycle 3 needs, on the next attempt

1. **`RULE-A8-v4`: a blind pointer probe is `error`, not a failed resolution.** With its own
   pre-registered row for all six fixtures — `resets_links_only:A8` becomes `error`, and the
   other five are unchanged from A8-v3's current behaviour, which the gate confirms.
2. **Re-derive the pre-registered table from the collectors, not from the rules.** The question
   "which legs does this fixture touch" is answered by which collectors issue which *methods*,
   and I answered it from the rule source. A table derived from `runner.collect_leg`'s dispatch
   would have caught A8 before the fixture ran.
3. **The three surface-mapping decisions in §4.2**, settled in the task file rather than in the
   runner.
4. **Then §1.3 onward as written.** Nothing else in the task is invalidated: the tier-0 set,
   the two new rules, and the sixth fixture all stand and are on disk.

## 6. One-line summary

The fixture built to prove that a blind link is not a missing download proved it — A1 and A3
returned `error` exactly as pre-registered — and then caught a third instance of the same
defect in A8, which reads an unobserved latest-vintage pointer as a broken one. The gate is a
hard stop, the pre-registered expectation was wrong in a way no fix would make right, and the
cycle did not run.
