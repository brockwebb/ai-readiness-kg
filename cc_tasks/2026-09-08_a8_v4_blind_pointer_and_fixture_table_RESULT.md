# RESULT — A8-v4: a blind latest-vintage pointer is `error`, and control tables are derived

**Task:** `cc_tasks/2026-09-08_a8_v4_blind_pointer_and_fixture_table.md` (no addenda exist;
globbed at dispatch and again before §3).
**Date:** 2026-09-08 UTC
**Spend:** zero model calls.
**Network: none.** **No federal host was contacted.** Every request went to `127.0.0.1`.

---

## 1. The gate — §3

**PASS on all four clauses.**

### 1.1 Six-fixture control gate, against the DERIVED tables

`RULE-E5-v2` = `pass`, zero unexpected verdicts, `unknown` = **0**.

| fixture | unexpected | error classes |
|---|---|---|
| `passes_all` | none | `http_4xx`, `off_host` |
| `fails_all` | none | — |
| `refuses_identified_client` | none | `refused` |
| `resets_connection` | none | `connection_reset` |
| `invalid_route_unobserved` | none | `connection_reset`, `http_4xx`, `off_host` |
| `resets_links_only` | none | `connection_reset`, `http_4xx`, `off_host` |

`CURRENT` for the run: `RULE-A1-v4`, `RULE-A3-v5`, `RULE-A8-v4`, `RULE-A10-v3`.

### 1.2 Re-derivation — byte-identical, all **seven** prior payloads

`scan_smoke_2026-09-06` (286), `scan_controls_2026-09-06` (33), `scan_2026-09-07` (437),
`scan_2026-09-07_controls` (33), `scan_2026-09-07b` (469), `scan_2026-09-07_rj1` (352),
`scan_2026-09-07b_rj1` (404). Each under **its own** rules and params, recovered from git by
hash. `RULE-A8-v3` stays bound to cycles 1, 2 and 2-rj1; nothing was re-judged.

**The two `_rj1` payloads were not in the standing set.** The harness-v4 RESULT promised they
would "join the set for the next task" and they never were added, so running them by hand
reported `params_changed` — the guard working, and indistinguishable at a glance from a failed
gate. They are in `PRIOR_CYCLES` now, where `_params_for` recovers what they were judged under.

### 1.3 Hygiene green; `corpus/` clean

Nothing captured, nothing promoted. `git status --porcelain corpus/` empty.

### 1.4 Full suite

**1,607 passed, 0 failed, 2 skipped** (2,745 s).

**Nothing was registered before this section was written.**

## 2. §1 — the derivation, run against the tables *before* any rule changed

`assessment/harness/scan/fixture_expectations.py` reads three facts from source and none from
memory: which collector functions each leg dispatches to, which HTTP method each issues, and
whether a probe is a **dereference** (a function taking `links` or `pointers` is handed URLs it
did not choose).

Run with `CURRENT` as it stood — A8-v3 — it reported **exactly one difference**, which is what
§1 predicted:

```
resets_links_only:A8   table=pass   derived=error
```

It derives **22** rows and defers **74**, and every row says which. It derives blindness and
refuses to guess at content judgements; a script that claimed to derive `A12 = fail` on a
refusing host would be the method being retired, wearing a better costume.

**One defect in the script, found and fixed before the gate.** The first version derived only
18 rows and left A1 and A3 *deferred* — it would have confirmed their rows by not looking at
them. Two causes, both now closed:

* it read only a leg's own dispatch block, and A1/A3 collect nothing of their own; their
  evidence comes through `rules.consumes` from the shared `link_probe` leg;
* the runner selects that leg through a **parameter** — `if leg == lp["shared_leg"]` — so a
  block parser reading literals named the block `lp` and lost the shared link probe entirely.

With both fixed the derivation finds all three legs that dereference with HEAD — A1 and A3 via
`links.probe`, A8 via `follow_latest_pointer` — and derives their rows rather than trusting
them.

## 3. §2 — `RULE-A8-v4`, five branches

`follow_latest_pointer` records `resolved: False` for four different things. A8-v3 read the
flattened boolean. v4 classifies each entry and then decides:

| state | test | verdict contribution |
|---|---|---|
| `off_host` | `off_host` flag or note | **scope, not blindness** — excluded from every count |
| blind | `status is None`, or `note == robots_disallowed` | unobserved |
| resolved | status in `a8_latest.resolves_statuses` | resolves |
| observed non-resolution | any other real status | a measurement |

* no pointers at all → `fail`, **v3's wording unchanged**
* any resolved → `pass`
* none resolved, some observed, **zero blind** → `fail`
* every non-excluded pointer blind → **`error`**
* **mixed observed and blind → `error`** — a pointer that might have resolved was never looked
  at, so "none resolves" is not established

Thirteen unit tests, including the pair that pins the defect: on the exact record from the
block, `RULE-A8-v3` still returns `fail` and `RULE-A8-v4` returns `error`. Asserting only the
second would let a rule that returned `error` for everything pass.

**Blind counts are fields now** (decision 3, closing scan-run-3 RESULT §4.3): `blind_links` on
A1-v4/A3-v5, `blind_pointers` on A8-v4. Both are **omitted from the record when unset**, which
is what keeps history re-derivable — a Finding made before the fields existed produces exactly
the dict it produced then. They are **not inputs to `finding_id`**, so no stored Finding is
re-identified; `finding_identity` is unchanged and stays at 2.

## 4. Premises this task got wrong

1. **Decision 3's parenthesis — "`finding_identity` unchanged unless the identity function
   reads them, in which case say so and stop."** It does not read them, so no stop. But the
   danger was not in the id: it was in `to_dict`, which the re-derivation gate compares
   byte-for-byte. Two new dataclass fields would have added two keys to every re-derived
   Finding and failed all seven prior payloads on keys nobody wrote. Omitting them when unset
   is what makes the change safe, and the task file did not anticipate that path.
2. **§1's "if it reports anything else … name which, and stop."** It reported nothing else —
   but it under-derived, which no clause covered. A derivation that defers a row is not a
   difference and not a pass; it is a row nobody checked. §2 above.
3. **The two `_rj1` payloads were assumed to be in the standing gate.** They were not. §1.2.

### Mine

4. Six standing tests pinned facts that move by design — `CURRENT["A1"] == "RULE-A1-v3"`,
   `GENERATIONS[-1]` versions in `("v3", "v4")`, and a re-judgement test that re-ran `rejudge`
   under today's `CURRENT` instead of reading the payload it was about. Each reported a rule
   advance as a regression. They now assert the property (does the current rule read the shared
   leg; is the predecessor still in `REGISTRY`; what did the payload record) rather than the
   moving fact.
5. I edited `rule_a1_v4.py` and `rule_a3_v5.py` — modules committed by scan-run-3 — to add the
   blind counts. Defensible and worth stating plainly: **no Finding has ever been recorded
   under either**, because that cycle never ran, so nothing is re-identified and no history is
   re-scored. The immutability rule protects modules with Findings on the log; these have none.

## 5. Verification

```
six-fixture control gate       PASS, unknown = 0
re-derivation, 7 payloads      byte-identical, each under its own rules and params
tests/test_a8_v4_and_fixture_tables.py   13 passed
full suite                     1607 passed, 0 failed, 2 skipped (2745 s)
seldon verify                  All checks passed. 27,993 events readable; 82 task
                               source files resolve; precedence acyclic.
framework write-back           3 spec rule_ids (A1, A3, A8) + E5 collector block,
                               via scripts/framework_writeback_rules.py --task <this file>,
                               projection followed (CLAUDE.md: a write-back is not finished
                               until a projection follows it)
git diff on protected paths    EMPTY on rule_a8_v3 / rule_a1_v3 / rule_a3_v4 /
                               rule_a10_v3, the targets DataFile, assessment/cq/.
                               events/ APPEND ONLY: batch-033_framework.jsonl +1/-0
                               (the framework_writeback event). corpus/ clean.
projection                     33 rules, measures 33, rules_unparseable [],
                               rules_without_indicator [],
                               observed_on_missing_document 0
```

**DD-061 appended**: control tables are derived from collector dispatch, never written from
rule source; blind is `status is None` or not-fetched-by-policy; `off_host` is scope, not
blindness; neither the table nor the script is edited to match the other.

## 6. What scan-run-3b needs

1. **The three surface-mapping decisions** scan-run-3 RESULT §4.2 named are still open and are
   the next thing to hit: Tier C machine rows on hosts outside the frame, the unadmitted EIA
   flagship, and the `home`/`well_known` doc_id collision.
2. **`blind_links` and `blind_pointers` are registrable now** — fields, not prose — so §4's
   per-leg `blind_links` Result no longer needs a parser.
3. **The derivation covers six fixtures and 22 rows.** Every leg it *defers* is a row still
   pre-registered by hand. That is not a defect, but it is the honest size of what is checked.
