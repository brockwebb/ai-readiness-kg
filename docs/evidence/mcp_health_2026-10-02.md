# MCP health test, 2026-10-02: the `ai-readiness-kg` server, verb by verb

`cc_tasks/2026-10-02_kg_research_questions_ADDENDUM-01.md` decision 6. Each verb called once,
in order, from a **headless** Claude Code session (`claude -p`, PID 79723, dispatched by the
standing dispatcher). Its MCP server was PID 79740, started 13:09:27 local (17:09:27Z) by that
session from `.mcp.json`. Calls ran 17:09:51Z to 17:10:38Z.

**Verdict: every verb answered in ≤ 3.1 s with `projection_gate` green, so this run found no
hang. The Desktop session's four-minute wait on `get_cycle_of_record` never reached the server:
Claude Desktop logs every MCP `tools/call` it sends, it has logged thousands for its other local
servers, and it has logged none to this one in 13 launches since 2026-09-18.**

## Table

The wall time brackets each call between two timestamps written by shell calls placed just
before and just after it (`logs/mcp_health_2026-10-02.log`). It therefore includes the client's
own turn latency and is an upper bound on the server's time. The 60-second ceiling could not be
set as a client-side timeout on a Claude Code MCP call. It held anyway, because no call came near
it.

| verb | argument | wall time (s) | outcome | projection_gate |
|---|---|---|---|---|
| `get_overview` | — | 0.73 | ok | green (228 nodes compared, 0 mismatches) |
| `get_cycle_of_record` | — | 1.03 | ok | not carried by this verb |
| `get_indicator` | `A1` | 1.00 | ok | not carried |
| `get_requirements` | `indicator=A11` | 1.10 | ok | not carried |
| `get_prescriptions` | `leg=A1` | 1.14 | ok | not carried |
| `get_body` | `BTS` | 1.08 | ok (50,978 characters, over the client's inline cap and saved to a file by the client; that is the client's display limit, not a server error) | not carried |
| `get_evidence` | `fnd_2708c4b648297fc3ae5690f3` (from `get_body`) | 3.09 | ok (sha256 verified on disk) | not carried |
| `get_document` | `w3c-dwbp-2017` | 1.18 | ok | not carried |
| `search_text` | `AI-ready`, limit 5 | 1.22 | ok | not carried |
| `run_cypher` | `MATCH (n) RETURN count(n)` | 1.20 | ok (65,142 nodes) | green |

`get_evidence`'s 3.09 s includes a `jq` step in the same bracket, which pulled the Finding id
out of `get_body`'s saved output. The other nine are 0.7 to 1.2 s.

## Cause of the Desktop hang, as far as it can be found without editing anything

1. **The server never received the call.** `~/Library/Logs/Claude/mcp-server-ai-readiness-kg.log`
   records every client message the Desktop sends to this server (`initialize`, `tools/list`,
   `prompts/list`, `resources/list`). It holds **0** `method="tools/call"` lines across its whole
   history: 13 `initialize` messages since its first line on 2026-09-18T10:08:38Z, the latest at
   2026-10-02T10:51:37Z. The same Desktop logs `tools/call` for its other local servers:
   `mcp-server-Filesystem.log` 2,871, `mcp-server-seldon-mcp.log` 1,050,
   `mcp-server-fss-policy-kg.log` 40. A call that reached this server and hung inside it would
   have left a `tools/call` line with no `Message from server` reply. None exists.
2. **The Desktop's server processes never opened the database.** The Desktop is running two
   copies, PID 2128 (parent 2114) and PID 2240 (parent 2239), both started 06:51:37–40 local.
   `~/Library/Logs/Claude/main.log` shows a launch followed by an immediate shutdown at
   06:51:34 and then a relaunch, so one of the two is probably left over from that shutdown.
   Neither holds a TCP connection to Neo4j (`lsof`, port 7687). The server builds its driver
   lazily on the first graph read (`mcp/airkg_tools.py::Graph.driver`) and keeps it, and this
   session's server held one as soon as it had answered. Each Desktop copy has used 1.66 s of CPU
   in six hours, against 1.40 s for a copy that has only started up (PID 34336, an interactive
   session's). That fits item 1: neither copy has served a call.
3. **Neo4j was healthy.** The DBMS (PID 1854) answered every call above. Its own query log was
   not read, because Desktop-managed DBMS logs are outside this task's scope and item 1 already
   puts the fault in front of the server.
4. **The projection was not stale.** `projection_gate` was green, 228 of 228 framework nodes
   equal to the record.

What is left is client-side and cannot be seen from here. Desktop's `main.log` logs no
individual tool call for any server, so it cannot say where the call stopped. One candidate,
**not verified**, is a tool-permission prompt waiting for approval: this connector has never had
a call go through, so no per-tool approval would have been stored yet (Desktop advertises
`mcpPersistentAlwaysAllow`). The duplicate server launch at 06:51:34 is a second candidate. If
the call went to the copy that was being shut down, it would have no reader.

## Desktop and headless differ

This run was headless. The verbs answered here and the Desktop call never reached the server,
so the two kinds of session **do not** behave the same. The server code is the same file
(`mcp/airkg_server.py`), so the difference lies between the Desktop client and the server's
stdin. Re-running the call in a Desktop session with a fresh conversation would test it: after
approving the tool if prompted, check whether
`grep -c 'method="tools/call"' ~/Library/Logs/Claude/mcp-server-ai-readiness-kg.log` goes above
0.
