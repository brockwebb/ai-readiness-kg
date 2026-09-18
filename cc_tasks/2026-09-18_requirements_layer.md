# CC Task: what you would need: Tool and Precondition nodes for every indicator the harness cannot measure alone, and `get_requirements` on the MCP

**Date:** 2026-09-18
**Project:** ai-readiness-kg
**Authored by:** Desktop session, from the operator's ruling of 2026-09-18: the framework is operationalized when a body can ask, through an LLM over the graph, where it stands and what it would need to measure or improve the rest; tests this project cannot run are limits recorded in the graph as the tools, accounts, scripts or agency data they require, with cost and access as data.
**Implements:** DN-005 §2.2 (three ways to measure) extended with the object each way needs; DD-001 (every assertion citable). The tool map (`docs/design/scan_tool_map.md`) §3 gap table is the prose this graph write replaces.
**Framework layer served (DN-005 §5 rule 1):** §2.2 and §2.4: the expert-system edge, indicator → test → requirement.
**Fulfils:** its own ResearchTask (`seldon cc register`). Launched by the dispatcher.
**Spend:** zero model calls. **Network:** none beyond `git push`. Every tool named is documented on disk or named by the tool map; nothing is fetched.

---

## 0. The shape, and its prior art

An expert system's rule base pairs a question with what answering it requires; the graph already has the question (the indicator), the test (the rule or the named open tool) and the fix (the action). It lacks the requirement: the thing a body must have or buy or grant before the test can run. CIS Benchmarks record it as *audit prerequisites*; Lighthouse marks audits that need a Chrome extension or an authenticated origin; Google Search Console data is the canonical example of a measurement that needs the site owner's account. The shape is one node type with an access class and a cost, linked from every test that needs it.

**Decisions taken here (operator overrides later):**

1. **Two node types in the framework record, through the one writer.**
   - `Tool`: `id` (`tool:<slug>`), `name`, `kind` ∈ {open_source, hosted_free, hosted_paid, platform_account, agency_internal}, `doc_source` (a corpus locator; `oasdiff-readme`, `wayback-cdx-server-api-readme`, `extruct-readme`, `slsa-specification-v1-0`, and whatever the tool map names that is on disk), `cost_band` ∈ {none, tooling, staff_time, procurement} with `cost_source` (`notional:` per `2026-09-17_notional_bands` decision 3; `tooling` finally has a use).
   - `Precondition`: `id` (`pre:<slug>`), `kind` ∈ {site_owner_account (a search-console or analytics property), page_script (a tag or beacon the publisher must add), agency_records (data only the agency holds), benchmark_set (an evaluation corpus this project would have to build), second_cycle (a comparison needs two measurements)}, `description`, `who_provides` ∈ {publisher, this_project, third_party}.
2. **`REQUIRES` edges** from every non-`harness_leg` indicator, and from every `harness_leg` whose `tier_note` records an unmeasured half, to the Tool or Precondition that would close it, with `for_clause` quoting the indicator's definition clause it serves. Tier O rows require their tool. `evaluation` rows require a `benchmark_set` precondition and, where the definition names a generative engine, a `hosted_paid` or `platform_account` tool. `judged_reading` rows require an `agency_records` or `page_script` precondition as the definition says. `declaration` rows require `agency_records` with `who_provides: publisher`. The three unassigned rows get whatever their reason names, or nothing with the reason unchanged.
3. **Every edge cites.** `source` on each `REQUIRES` edge is a tool-map row, a corpus locator, or the definition sentence; an edge with no citation is a gate failure. The count of `notional:` costs is a number in the RESULT.
4. **`get_requirements(indicator=None, body=None)` on the MCP.** For an indicator: the tests that measure it, and for each what it requires, with kind, cost and who provides. For a body on the cycle of record: everything the harness could not observe for it (errors, refusals, unmeasured halves), and what would be needed to observe it, grouped by requirement so a body sees "a search-console grant would unlock these four" as one line. Locators on every fact; a test opens each.
5. **The tool map §3 regenerates from the graph** and stops being hand-held prose.
6. **Nothing is measured.** The site's framework copy and manifest move as before; the MCP page regenerates.

**Write set:** `framework/ai_readiness_framework.json` through the writer; the schema file; `scripts/tag_requirements.py` (new); the projection for the two node types and the edge; `mcp/` (the tool and its tests); `scripts/scan_tool_map.py` (§3 from the graph); `tests/test_requirements.py` (new); the regenerated views; `scripts/check_protected_requirements.sh` (new); `seldon_events.jsonl`; the RESULT. `state/`, `corpus/`, `docs/reports/` byte-identical.

**Immutable once written. Glob `2026-09-18_requirements_layer_ADDENDUM*.md` before starting and again before §3.**

---

## 1. Read the tool map §2 and §3, the five O rows' `tier_source`, the eight evaluation rows' definitions, and the `tier_note`s carrying "unmeasured".
## 2. Decisions 1 to 5. Tests first.
## 3. Gate
`make gate-full` (`-rs`), `seldon verify`, protected paths, projection round-trip. Detached and polled inside this turn per `CLAUDE.md`. Expected skips: 3. Failure ships nothing.
## 4. Report
RESULT `cc_tasks/2026-09-18_requirements_layer_RESULT.md`: §0 the node and edge counts by kind, the `notional:` count, and the indicators with no requirement and why; §1 the full requirement table (indicator, clause, requirement, kind, cost, who provides, source); §2 one `get_requirements` output for an indicator and one for a body; §3 every premise this task file got wrong; §4 the gate table, tier named. `seldon cc complete`, commit, push.

**SEQUENCING:** §1 → §2 → glob addenda → §3 → §4 → push. Runs after `2026-09-18_rejudge_seven_legs.md`.
