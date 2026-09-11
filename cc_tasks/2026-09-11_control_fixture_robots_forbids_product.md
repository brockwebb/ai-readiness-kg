# CC Task — control fixture: a robots.txt that forbids an in-product probe

**Date:** 2026-09-11
**Project:** ai-readiness-kg
**Authored by:** Desktop session, OODA on `2026-09-10_harness_v5_blind_RESULT.md` §7 item 2 / §9 item 1 and `2026-09-10_l0_figures_and_leg_rate_names_RESULT.md` §8 item 3. Fulfils ResearchTask `a2981a12`.
**Fulfils:** ResearchTask `a2981a12` (`seldon cc register` links it). Runs while the operator reads the L0 PDF. Touches nothing under `docs/reports/`. Precedes any cycle 5.
**Spend:** zero model calls. **Network: loopback only.** No federal host, no reference host. A test asserts the socket counter records no non-loopback address.

**Why this task exists.** The seven-fixture control set has no mode in which a product's own robots.txt forbids the probe a rule needs. That is why harness-v5's class change moved 0 derived control rows, and why the same defect reached a federal host in cycle 4 and was found four times by reading payloads and zero times by the gate. A control set that cannot exercise the class it was built to catch is a positive control that never fires.

**Decisions taken here (operator overrides later):**
1. **One new loopback fixture, partially forbidden.** Its robots.txt is present, parseable, and disallows the paths that a known subset of product legs probe, while allowing the rest. The robots.txt fetch itself is OBSERVED. Which legs land under the Disallow is chosen so that at least one leg from each of A-series product legs, B3 and G1-D is forbidden and at least one of each is allowed; the exact partition is written in the fixture's own manifest, not inferred from rule source (DD-061).
2. **Pre-registered expectation is derived from collector dispatch**, as the seven are: the derived control table gains one row per (leg, class) from what the collectors actually issued against the fixture, never from reading a rule module. Expected verdict for every forbidden-probe leg under harness-v5 is `error` (BLIND); for every allowed leg, whatever the derivation says; A12-v2 yields a verdict, because the refusal is its subject.
3. **Replay red/green.** The fixture's payload re-judged under harness-v4 (`is_blind(…, 4)`) must yield at least one `pass`/`fail` on a forbidden probe (RED); under v5, zero (GREEN). This is the incident replay for the A10 class at the control layer, where it was missing.
4. **A3-v4 is expected to fail this fixture and that is not a stop.** `rule_a3_v4` never consults the blind guard (harness-v5 RESULT §9 item 3; exemption pinned by content hash in the lint). Its row in the new fixture's invariant reading is a strict `xfail` pinned to ResearchTask `969f73c6` (RULE-A3-v5) by id, so the gate is green on the one known gap and red on anything else. The RESULT reports A3's actual verdict on the forbidden probe. Any other rule returning a verdict on a forbidden probe is a stop: it is a new instance of the class, and this task writes nothing.
5. **The fixture joins `make guards` and the agreement gate.** Both-clocks agreement runs over eight fixtures. The virtual-clock path covers it; one real-rate run stays in `slow` as today.

**Zero edits to:** rule modules, stored payloads, prior Results, prior RESULTs, cycle evidence, targets, `docs/reports/`, the seven existing fixtures.

**Immutable once written. Glob `2026-09-11_control_fixture_robots_forbids_product_ADDENDUM*.md` before starting and again before §3.**

---

## 1. Decision 1, 2. Build the fixture and its manifest. Run the collectors against it on loopback; derive its control rows. Stop if the derivation shows zero forbidden-probe rows: then the partition did not land on a probe path and the fixture is not exercising the class.
## 2. Decision 3, 4, 5. Write the replay, the pinned A3 xfail, the guards and agreement wiring.
## 3. Gate (the one gate of this task)
Eight-fixture control gate under `CURRENT`, `unknown` = 0; both-clocks agreement, 0 differences; the new fixture's derived table has ≥ 1 forbidden-probe row per leg the partition forbids; replay RED under v4 / GREEN under v5; invariant test over the new fixture payload: 0 verdicts on unobserved evidence excluding the pinned A3 xfail; byte-identical re-derivation of all stored payloads under their own harness versions (this task must not move any of them); socket counter shows loopback only; `make guards`; `make gate-task`; `make gate-full` detached, logged, polled; `seldon verify`; protected paths.
**Failure writes nothing: report and stop, RESULT with the block on top, commit, push.**
## 4. Report
RESULT `cc_tasks/2026-09-11_control_fixture_robots_forbids_product_RESULT.md`: the partition (which legs forbidden, which allowed, by path); the derived rows; the replay counts under v4 and v5; A3-v4's actual verdict on the forbidden probe; any rule other than A3-v4 that returned a verdict (should be none); every premise wrong. `seldon cc complete`, commit, push. Final message states whether the push succeeded.

**SEQUENCING:** §1 (stop on zero forbidden-probe rows) → §2 → glob addenda → §3 (detached, logged, polled) → §4 → push.
