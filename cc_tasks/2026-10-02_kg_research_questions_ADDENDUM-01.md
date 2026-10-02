# ADDENDUM-01 to `2026-10-02_kg_research_questions.md`: test the MCP, verb by verb

**Date:** 2026-10-02 **Status:** AMENDS the base task. Does not supersede it. Read before any step.

## Added decision

6. **MCP health test, before the five questions.** On 2026-10-02 a Desktop session's call to `get_cycle_of_record` returned nothing for four minutes. Call each of the nine verbs of the `ai-readiness-kg` MCP once, with a 60 second ceiling per call and the wall time recorded: `get_overview`, `get_cycle_of_record`, `get_indicator`, `get_requirements`, `get_prescriptions`, `get_evidence`, `get_document`, `get_body`, `search_text`, plus `run_cypher` with `MATCH (n) RETURN count(n)`. Report a table of verb, wall time, outcome (`ok`, `timeout`, `error`, `projection_gate` value). For every `timeout`, find the cause if it can be found without editing anything: the MCP server process and its log, Neo4j's state, a long-running query, or a stale projection. Put the table and the cause in `docs/evidence/mcp_health_2026-10-02.md` and a one-line verdict in the RESULT. If a verb hangs, do not retry in a loop; the bounded call is the test. Whether a Desktop session and a headless session see the same behaviour is itself a finding: say which kind this run was.

**Write set addition:** `docs/evidence/mcp_health_2026-10-02.md`.
