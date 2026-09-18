# RESULT: nine read-only MCP tools over the graph, every answer carrying the address a stranger would open

**Task:** `cc_tasks/2026-09-17_mcp_over_the_graph.md` (ResearchTask `0f15557e`). I globbed `2026-09-17_mcp_over_the_graph_ADDENDUM*.md` before starting and again before §3. Neither glob found an addendum.
**Session:** launched headless by the standing dispatcher (claimed `2026-09-17T23:09:42Z`, `dispatcher:HexagonMBP.local:24863`) from HEAD `b76f8cb`. The SEQUENCING line held: `2026-09-17_unassigned_indicators.md` has its RESULT on disk and its tier counts are what `get_overview` reports.
**Framework layer served:** DN-005 §2.4 (exposure) and §4 item 4.
**Spend:** zero model calls. **Network:** none beyond `git push`. The server runs on stdio against the local Neo4j; nothing is deployed.
**Gate:** green, with every command run to its `EXIT=` line before this file was written.
- `make gate-full` equivalent — **the full tier**, `/opt/anaconda3/bin/python3 -m pytest tests/ assessment/ -q -rs`: **2425 passed, 3 skipped, 12 xfailed, 0 deselected, 0 failed**, `EXIT=0`, wall-clock 1419.56 s (0:23:39). Expected skips: 3, and the three are the expected three (§5).
- `seldon verify`: **All checks passed**, `EXIT=0`.
- `scripts/check_protected_mcp.sh`: **PROTECTED PATHS OK**, `EXIT=0`.
- `tests/test_framework_projection_roundtrip.py` + `tests/test_mcp_server.py`: **80 passed, 0 skipped**, `EXIT=0` — the DD-057 gate ran and did not skip, which is what makes every Cypher claim below valid.
The log paths are in §6.

**In one paragraph.** `mcp/` holds a read-only MCP server over `seldon-ai-readiness-kg`: **nine tools, 72 new tests, and a locator on every fact**. The architecture is `icsp_notebook/kg/mcp_server.py`'s — a thin FastMCP shell over a verb layer that tests without a transport — and the orientation-tool-plus-pragmatics shape is the Census server's. What could not be copied is named in §0. The rule that makes the server usable as evidence rather than as a summary is decision 2's: every answer carries `locators`, and `resolve_locator` **opens what one names**, so a locator that is present and wrong fails a test rather than passing one — `tests/test_mcp_server.py::test_every_locator_in_every_tool_answer_resolves` walks every locator of every tool and resolves it, with a negative control beside it. `get_overview` recomputes the DD-057 projection gate live against the database, cell for cell over 171 nodes, and `run_cypher` returns that status beside its rows. **One defect was found by driving the registered server over stdio rather than by reading it** (§4 premise 9): `seldon.config.get_neo4j_driver` reads environment variables only and silently falls back to the literal `neo4j`/`password`, so the server as registered answered `AuthError` to every graph question while identical code answered `green` in a shell. Fixed, with the test that would have caught it.

---

## 0. Prior art: the two servers, what was copied, what had to differ

Both were read in full before a line was written here.

| | fss-policy-kg | Census |
|---|---|---|
| **on disk at** | `/Users/brock/Documents/GitHub/icsp_notebook/kg/mcp_server.py` (274 lines) + `kg/verbs.py` (the eight verb bodies) + `tests/test_mcp_server.py` (its rails) | `/Users/brock/Documents/GitHub/census-mcp-server/src/census_mcp/server.py` (451 lines) |
| **not at** | `/Users/brock/GitHub/fss-policy-kg`, which the task file names and which does not exist (§4 premise 2) | — |
| **found via** | `~/Library/Logs/Claude/mcp-server-fss-policy-kg.log` and the Desktop config | the Desktop config's `census-mcp` entry |

**Copied from fss-policy-kg, deliberately and by name:**

* **The architecture.** Verb bodies in their own module (`mcp/airkg_tools.py`, its `kg/verbs.py`), server a thin shell that registers wrappers (`mcp/airkg_server.py`). This is the reason `tests/test_mcp_server.py` can drive every tool without a transport, and the reason the doc generator can run the tools directly.
* **`run_cypher` as the one escape hatch beside a set of named verbs**, with `MAX_ROWS = 200` as the flood cap — the same constant and the same number.
* **The keyword rail, with string literals stripped first**, so a query searching for the literal text `create` is not read as a `CREATE` clause. Its exact verb list including `DROP` and `FOREACH`, which decision 1 does not list: a rail that drops a verb on the way across is not a copy.
* **Two belts, not one**: the keyword rail before dispatch, and the driver's explicit read transaction at dispatch. Its parity note carried across too — `default_access_mode="r"` is rejected by driver 6.0.3, so `Graph.read` uses `session.execute_read`.
* **Rails as pure functions in their own module**, unit-tested offline with no driver and no graph (`mcp/airkg_guard.py`, 27 of the 72 tests).

**Copied from Census:**

* **The orientation tool a client is told to call first.** `get_overview` here, `get_methodology_guidance` there; its docstring opens "CALL THIS FIRST" for the same reason.
* **The shape that matters most: pragmatics travel with the data, so a client cannot get a number without the caveat.** Its `pragmatics` field bundled with every response is, here: `projection_gate` on `get_overview` and on every `run_cypher` result; `(notional)` and `band_note` on every prescription answer; `hash_meaning` on the cycle; "this is lexical, absence of a hit is absence of a STRING" in `search_text`'s own docstring.

**What had to differ, each with the reason:**

1. **The database rail is inverted, and it is the whole rail.** fss-policy-kg refuses a database named `wintermute-intake` or `seldon-*`. **This project's database IS `seldon-ai-readiness-kg`** — copying that rail verbatim would have refused the only graph this server may touch. `airkg_guard.assert_allowed_db` is therefore an allow-list of exactly one name, read from `seldon.yaml:neo4j.database` and never from a caller. Six databases are driven through it in the tests, including `seldon-fss-policy-kg`.
2. **A refusal is a returned message, not an exception** (decision 1). fss-policy-kg raises `ValueError`. `guard.refusal()` returns the sentence or `None`, and `run_cypher` returns `{"refused": ...}`. The database rail still raises `SystemExit`, because at startup there is no client to hand a message to.
3. **`CALL` is closed, not filtered.** Decision 1 says "`CALL … write procedures`". A blocklist of write procedures is defeated by the next procedure, so the rail allows only the read procedures it names and refuses every other `CALL` **by name** — `apoc.create.node` is refused because it is not on the list, not because someone enumerated it. The CALL rail runs *before* the keyword rail so a procedure is refused as a procedure (`apoc.create.node` trips `\bCREATE\b` too, and "`create` is a write clause" is a true sentence about the wrong thing).
4. **Comments are stripped as well as string literals.** `MATCH (n) // harmless` on one line and `DELETE n` on the next is a write the literal-only strip does not see. Driven in the refusal table (§2).
5. **Locator discipline, which neither server has.** fss-policy-kg returns node ids and verbatim text, which is a locator for a corpus of documents. This graph's facts come from four sources — the framework record, the published matrices, the retained response bodies, the projection — so a node id locates one quarter of the answers. Nine locator kinds, and a resolver that opens each.
6. **Census is not built on FastMCP** (§4 premise 3). Its ADR-005 rejected it: FastMCP's handshake succeeded but its tools did not surface in Claude Desktop on `mcp` 1.9.4. That was a 2025 defect against an old library; fastmcp 3.2.3 is what fss-policy-kg runs under today and what this uses. The pointer to ADR-005 is in `mcp/airkg_server.py`'s docstring so the first place to look, if tools ever fail to surface in Desktop, is named.
7. **`mcp/` is not a Python package** (§4 premise 8). A top-level `mcp/__init__.py` in this repository shadows the installed `mcp` distribution that fastmcp imports; `import fastmcp` then dies with `ImportError: cannot import name 'McpError' from 'mcp'` for the whole suite. Verified both ways before choosing: with an `__init__.py`, `import fastmcp` fails; as a namespace directory it resolves to `/opt/anaconda3/lib/python3.12/site-packages/mcp/__init__.py` with the repo root first on `sys.path`. `scripts/check_protected_mcp.sh` §4 is the standing guard, and modules take the `airkg_` prefix this repo already uses (`scripts/jobs/airkg_extraction_burn.sh`) so a bare `import server` can never be one of ours.

**Prior art the task did not name and this did not need:** Neo4j Labs' `mcp-neo4j-cypher` was already evaluated and rejected as a base by the fss-policy-kg server, for three reasons that all still hold here (no single-database rail, no read-only default, no reuse of this project's config wiring). Its `text2cypher` pattern is what `run_cypher` is. Re-running that evaluation would have been re-deriving a decision this operator's own repo already recorded.

---

## 1. The nine tools, one real call and its real output each

Decision 2 says "Eight tools" and then lists nine (one bullet carries `get_document` and `search_text`). Nine are built, registered and tested; the count is §4 premise 1.

The **full** outputs, every field, are in `docs/design/mcp_over_the_graph.md` — generated by running the tools, never typed, and `mcp/airkg_doc.py --check` re-renders and compares, so the page is either what the tools answer or the protected-paths check is red. What follows is the same calls, abridged to the fields that show the shape.

### 1. `get_overview()` — the call-first tool

```json
{"indicators_by_measurement_tier": {"M": 34, "unassigned": 8, "O": 2, "D": 5},
 "actions": 45, "edges": 325,
 "cycle": "scan_2026-09-10_rj2", "measured": "2026-09-10", "n_bodies": 16,
 "gate": {"status": "green", "nodes_compared": 171, "mismatches": []}}
```

The tier distribution is the one `2026-09-17_unassigned_indicators_RESULT.md` settled, read off the record rather than restated. `by_tier_and_basis` carries the crosstab, `counts` and `counts_basis` the record's own counters and the sentence saying what each counts.

### 2. `get_indicator(code='A5')`

```json
{"code": "A5", "indicator": "llms.txt (or equivalent) present; sitemap covers data products",
 "construct": "Discoverability surface", "tier": "public",
 "measurement_tier": "M", "measurement_basis": "harness_leg",
 "rule": "RULE-A5-v2", "spec": "spec:A5",
 "actions": ["act:a5-list-the-product-url-in-the-sitemap",
             "act:a5-publish-a-sitemap-and-point-robots-txt-at-it"],
 "cycle_of_record": {"fail": 36, "error": 9, "pass": 7},
 "locators": [{"kind": "record", "path": "framework/ai_readiness_framework.json", "node_id": "ind:A5"},
              {"kind": "record", "path": "framework/ai_readiness_framework.json", "node_id": "con:A:discoverability-surface"}]}
```

`tier_source` is carried in full (for A5: `rules.CURRENT['A5'] = RULE-A5-v2 … measurement spec \`spec:A5\``), and every record property not otherwise surfaced lands in `notes` rather than being dropped.

### 3. `get_body(name='NCHS')`

```json
{"summary": "21 failing of 25 judged on scan_2026-09-10_rj2; 16 bodies are on this cycle",
 "first_cell": {"leg": "A4", "verdict": "pass", "surface": "home:www.cdc.gov",
                "finding_id": "fnd_6bc41a5d60eb49319167f0fb", "rule_id": "RULE-A4-v1",
                "reason": "robots.txt allows the product path for all 8 AI-crawler user agents"},
 "first_cell_evidence_0": {"obs_id": "obs_7d5add4fb04ea068d859b649", "retained": true,
   "path": "corpus/evidence/scan/28/2837016c20845bf0f86ecfad68dbb4d37993338ee4584abd502087da48ea5ca7",
   "sha256_verified": true, "captured_at": "2026-09-10T17:59:54.672232+00:00"},
 "first_cell_locators": [{"kind": "matrix", "path": "docs/reports/scan_matrix_tierA_2026-09-10_rj2.json", "cell": "NCHS/A4"},
                         {"kind": "graph", "label": "Finding", "id_property": "finding_id", "id": "fnd_6bc41a5d60eb49319167f0fb"}]}
```

`sha256_verified` is computed, not copied: the bytes are read and hashed. See §4 finding 11 for the cells whose collector retains no body.

### 4. `get_prescriptions(body='NCHS')`

```json
{"failing_legs": ["A1","A10","A11-declared","A2","A5","A6","A8","A9","B3","D1","D4","F4"],
 "n_actions": 33,
 "top": {"id": "act:a2-expose-an-api-and-publish-its-description", "leg": "A2",
         "outcome": "no_api_description", "effort": "quarter", "cost": "procurement",
         "verifies_by": "RULE-A2-v3",
         "failing_on": ["scan-nchs-flagship-1-data-briefs",
                        "scan-nchs-flagship-2-early-releases-of-selected-estimates-from-the-nhis"]},
 "band_note": "Notional relative estimate for a typical federal statistical publisher. Adjust for your pl…"}
```

`scripts/prescriptions.py` **is** this tool: `actions`, `failing`, `bodies`, `matrices` and `band_note` are imported from it rather than reimplemented, because a second `failing()` is a second answer to "which legs does this body fail" and the two would drift. A test asserts the tool's legs equal that script's, leg for leg.

### 5. `get_evidence(finding_id='fnd_6bc41a5d60eb49319167f0fb')`

```json
{"finding_id": "fnd_6bc41a5d60eb49319167f0fb", "verdict": "pass", "rule_id": "RULE-A4-v1",
 "rule_version": "v1", "indicator_code": "A4", "target_doc_id": "home:www.cdc.gov",
 "evidence_unretained": false,
 "observations": [{"obs_id": "obs_7d5add4fb04ea068d859b649", "retained": true,
   "path": "corpus/evidence/scan/28/2837016c…", "sha256_verified": true, "bytes": 1699}]}
```

`rule_version` is derived from the rule id through `scan.rules.parse_rule_id`, never read off the Finding — every stored Finding carries the literal `v1` (`rules/_common.py`), and that field is an input to the derived `finding_id`, so it cannot be corrected in the events.

### 6. `get_document(doc_id='rfc-9309-robots-exclusion-protocol')`

```json
{"doc_id": "rfc-9309-robots-exclusion-protocol", "title": "RFC 9309: Robots Exclusion Protocol",
 "source_type": "standard", "primary_url": "https://www.rfc-editor.org/rfc/rfc9309",
 "content_hash": "aea78e3b6eeca189a9ec60458e4fa83277ec0e4ef42613923b5e21933bd62e76",
 "counts": {"definitions": 11, "concepts": 63, "claims": 59, "standards": 20, "practices": 15, "platforms": 2},
 "evidences_indicators": ["A11", "A12", "A4"]}
```

An unknown doc_id returns the nearest ids from the graph, never a guess.

### 7. `search_text(q='sitemap', limit=3)`

```json
{"n_hits": 10, "truncated": true, "hits": [
 {"kind": "indicator", "code": "A5", "doc_id": null, "section": "Discoverability surface",
  "locator": {"kind": "record", "node_id": "ind:A5", "path": "framework/ai_readiness_framework.json"}},
 {"kind": "action", "code": "A5", "doc_id": null, "section": "discovery_file_omits_product",
  "locator": {"kind": "record", "node_id": "act:a5-list-the-product-url-in-the-sitemap", "path": "framework/ai_readiness_framework.json"}},
 {"kind": "technique", "code": "A5", "doc_id": "sitemaps-protocol", "section": "Sitemaps XML format",
  "locator": {"kind": "document", "doc_id": "sitemaps-protocol", "section": "Sitemaps XML format", "path": "corpus/kernel/sitemaps-protocol.md"}}]}
```

All **110** technique quotes on the record parse to a doc_id and a section — asserted outright, because a parser that matched a few and returned `None` for the rest would leave most hits unlocated while every other test still passed. See §4 finding 12 on `doc_id` for record-sourced hits.

### 8. `get_cycle_of_record()`

```json
{"cycle": "scan_2026-09-10_rj2", "kind": "rejudged", "derived_from": "scan_2026-09-10",
 "derived_from_params_hash": "4e0a92ba19ab769bb98b3a4a0c68640fbe465a04eaaec4aa6f2f0f41dc75c0df",
 "judgement_params_hash": "d3499218ef48273597ec67a6a81ae9c966e5801cf66915fbc106403c6da94624",
 "verdict_counts": {"pass": 161, "fail": 459, "not_applicable": 0, "error": 119},
 "matrices": [{"kind": "tierA", "path": "docs/reports/scan_matrix_tierA_2026-09-10_rj2.json", "rows": 16},
              {"kind": "product", "path": "docs/reports/scan_matrix_product_2026-09-10_rj2.json", "rows": 23}],
 "supersession": {"successor": "scan_2026-09-10_rj3", "superseded_findings": 739,
                  "verdict_moves": 0, "reason_only_changes": 3}}
```

The supersession is `scripts/snapshot_successor.py::successor_info` and `supersession_line`, called rather than re-queried, so the server and the published report answer DN-004 from one query. **`_rj3` moved no verdict**, as the task file said.

### 9. `run_cypher('MATCH (r:Rule {current: true}) RETURN count(r) AS current_rules')`

```json
{"rows": [{"current_rules": 17}], "row_count": 1, "truncated": false, "max_rows": 200,
 "database": "seldon-ai-readiness-kg", "projection_gate": "green",
 "locator": {"kind": "graph", "label": "*", "id_property": "database", "id": "seldon-ai-readiness-kg"}}
```

### The locator kinds, and the test that makes them mean something

Nine kinds — `record`, `record_key`, `config`, `matrix`, `payload`, `evidence`, `graph`, `document`, `source` — and `Tools.resolve_locator` opens each: the record node must exist in the record, the matrix cell must exist in that matrix, the evidence file must be on disk **and hash to the name it is filed under**, the graph node must exist, the internal document must be a file containing the section it names. `test_every_locator_in_every_tool_answer_resolves` walks every locator of all nine tools' answers and resolves it; `test_the_resolver_refuses_a_locator_that_points_at_nothing` is the negative control that stops the first test being vacuous.

A `graph` locator's label is checked against a literal whitelist before any query is built — invariant 4, because Cypher has no parameter form for a label and a locator is a dict a caller can hand back. `test_a_locator_label_is_never_interpolated_into_cypher_unchecked` drives an injected label through it.

---

## 2. The guard's refusal table

Every row below was produced by calling `airkg_guard.refusal()`; the messages are truncated here for width and are complete in the code.

| query | outcome |
|---|---|
| `CREATE (n:Hack) RETURN n` | refused: `` `CREATE` is a write clause `` |
| `MERGE (n:AssessmentIndicator {code:'A1'})` | refused: `` `MERGE` is a write clause `` |
| `MATCH (i:AssessmentIndicator) SET i.tier='public'` | refused: `` `SET` is a write clause `` |
| `MATCH (n) DETACH DELETE n` | refused: `` `DELETE` is a write clause `` |
| `MATCH (i) REMOVE i.tier` | refused: `` `REMOVE` is a write clause `` |
| `DROP CONSTRAINT indicator_id` | refused: `` `DROP` is a write clause `` |
| `MATCH (n) FOREACH (x IN [1] \| SET n.k = x)` | refused: `` `FOREACH` is a write clause `` |
| `LOAD CSV FROM 'file:///x.csv' AS row CREATE (:N)` | refused: `` `LOAD CSV` is a write clause `` |
| `MATCH (n) CALL { CREATE (:Y) } RETURN n` | refused: `` `CREATE` is a write clause `` — a write in an anonymous subquery |
| `CALL apoc.create.node(['X'], {}) YIELD node RETURN node` | refused: `` `CALL apoc.create.node` is not one of the read procedures this read-only server allows `` |
| `MATCH (n) // harmless` ⏎ `DELETE n` | refused: `` `DELETE` is a write clause `` — the comment does not hide it |
| `` (empty) `` | refused: empty query |
| `MATCH (a:Action) WHERE a.description CONTAINS 'create' RETURN a.id` | **passed** — a write word inside a string literal is not a write |
| `CALL db.labels() YIELD label RETURN label` | **passed** — on the read-procedure allow-list |

Belt two is independent of all of it: `Graph.read` runs every statement in `session.execute_read`, so a statement that somehow got past the rail would still be refused by the database. `scripts/check_protected_mcp.sh` §6 greps `mcp/` for `execute_write` and `begin_transaction` and asserts `execute_read` is still there.

---

## 3. Registering it

**Claude Code** reads `.mcp.json` at the repository root and needs nothing else. It is committed:

```json
{ "mcpServers": { "ai-readiness-kg": {
    "command": "/opt/anaconda3/bin/python3",
    "args": ["/Users/brock/GitHub/ai-readiness-kg/mcp/airkg_server.py"] } } }
```

**Claude Desktop** — the one-line addition, to the `mcpServers` object of `~/Library/Application Support/Claude/claude_desktop_config.json`, beside the `fss-policy-kg` and `census-mcp` entries already there. This task did not edit that file; it is outside the repository and it is the operator's:

```json
    "ai-readiness-kg": {
      "command": "/opt/anaconda3/bin/python3",
      "args": ["/Users/brock/GitHub/ai-readiness-kg/mcp/airkg_server.py"]
    }
```

No `env` block, deliberately: the credentials would be a password in a file, and the server resolves them from `~/.wintermute/.env` instead (§4 premise 9). The interpreter is named explicitly for the reason `CLAUDE.md` names it for extraction and projection — it is the one that has `fastmcp`, the Neo4j driver and `pyyaml`. A bare `python3` would surface as a connector that failed to connect with nothing saying why.

**Driven over stdio as a subprocess, after the fix**, which is how a client will actually start it:

```
tools: 9 ['get_overview','get_indicator','get_body','get_prescriptions','get_evidence',
          'get_document','search_text','get_cycle_of_record','run_cypher']
gate: green | nodes: 171
BLS: 1 failing of 15 judged on scan_2026-09-10_rj2; 16 bodies are on this cycle
evidence obs: 1 | first retained: True
refusal: refused: `SET` is a write clause and this server is read-onl…
```

---

## 4. Every premise this task file got wrong, and what the build found

1. **"Eight tools"** — decision 2's own enumeration is nine: `get_document` and `search_text` share a bullet. Nine are built, registered and listed by the client. No tool was dropped to make the count true.
2. **`/Users/brock/GitHub/fss-policy-kg` does not exist.** The fss-policy-kg MCP server is `/Users/brock/Documents/GitHub/icsp_notebook/kg/mcp_server.py` with its verbs in `kg/verbs.py`; found through `~/Library/Logs/Claude/mcp-server-fss-policy-kg.log` and the Desktop config, not by guessing. (`~/GitHub/icsp_notebook` reaches the same inode.)
3. **"FastMCP in Python, as those use"** — only one of the two uses FastMCP. The Census server is built on the low-level `mcp.server.Server` **deliberately**, under its own ADR-005: "FastMCP (mcp 1.9.4) handshake succeeds but tools fail to surface in Claude Desktop. The low-level pattern is proven to work (used by all Arnold MCPs)." FastMCP was still the right choice here (fastmcp 3.2.3, and fss-policy-kg runs on it today), but the reason is "one of the two, on a current library", not "as those use", and ADR-005 is now cited in the server's docstring as the first place to look if Desktop ever shows zero tools.
4. **"the same server shape … its read-only Cypher guard" could not be copied whole.** The database rail is a pattern that refuses `seldon-*`, and this project's database IS `seldon-ai-readiness-kg`. Copied verbatim it would refuse the only graph the server may touch. §0 item 1.
5. **"The pending bands print as `pending`, never as a number."** No band is pending: `cc_tasks/2026-09-17_notional_bands.md` filled all 90 with notional values by technique class, and the prescription RESULT the task cites (§3, "0 sourced bands, 90 pending") was superseded the same day. The rule is implemented and tested against a cleared band, because a band the operator clears is a band with no estimate again — but today it fires on nothing, and `band_source` is carried verbatim so a reader can see which kind of band they have.
6. **The label list in §0 is not the record's.** The task names `AssessmentIndicator, Construct, Definition, MeasurementSpec, Rule, Document, Action`. `framework/ai_readiness_framework.json` holds `AssessmentCriterion` (7), `AssessmentConstruct` (48), `AssessmentIndicator` (49), `MeasurementSpec` (22) and `Action` (45) — there is no `Construct`. `Definition` (1,975), `Document` (262) and `Rule` (41) are in the graph and are real, but they belong to the extraction KG and the scan projection, not to the framework record; `AssessmentInternalRef` (20) is minted by the loader and is in neither list. Decision 3's split is what makes the distinction matter, and the tools follow the actual ownership.
7. **"171 nodes and 325 edges after the prescription layer"** — correct, confirmed against the record and against the graph by the round-trip comparison (171 nodes compared, 0 mismatches).
8. **The write set names `mcp/`, and `mcp/` as a Python package breaks the suite.** `fastmcp` imports the installed `mcp` distribution; a repo-root `mcp/__init__.py` shadows it with pytest's own `sys.path` insertion, and `import fastmcp` fails with `ImportError: cannot import name 'McpError' from 'mcp'`. The directory name is kept — it is what the task asked for and what a reader looks for — and it is a namespace directory, which does not shadow a regular package. Guarded in `scripts/check_protected_mcp.sh` §4, both by the absence of `__init__.py` and by importing fastmcp with the repo root first on `sys.path`.
9. **The premise nobody stated: that a server registered in `.mcp.json` would reach Neo4j.** It would not have. `seldon.config.get_neo4j_driver` reads `NEO4J_USERNAME`/`NEO4J_PASSWORD` then `NEO4J_USER`/`NEO4J_PASS` from the environment **and nothing else**, falling back to the literal `neo4j`/`password` when neither is set (`seldon/config.py:91-92`). An MCP client starts the server with an environment of its own, so "unset" is the normal case there. Driven over stdio the server returned `AuthError` and `projection_gate: unverified` for every graph question, while the identical code in this shell returned `green`. **This was found by running the registered server, not by reading it** — every in-process test passed throughout. Fixed by resolving credentials through this repository's own resolver, `scripts/build_projection.py::_neo4j_creds` (both spellings, then `~/.wintermute/.env`, which is the fallback `CLAUDE.md` documents), with the missing-credential case re-raised naming both variable pairs and the file, and no guessed password anywhere. Two tests: one connects with every `NEO4J_*` variable deleted and **fails rather than skips** (the module fixture has already proved the database is up in the same process); one sets `HOME` to an empty directory and asserts `SystemExit` naming the variables.
10. **`scan_2026-09-10_rj2`'s two hashes are both real and both needed.** `derived_from_params_hash` (`4e0a92ba…`) identifies the collection; `params_hash` (`d3499218…`) identifies this judgement of it. The task called the second "judgement hash"; the payload's field name is `params_hash`, and the tool returns it as `judgement_params_hash` with a `hash_meaning` sentence, because two 64-character hashes side by side with no sentence is how a report comes to publish the wrong one.
11. **"evidence locator per cell" cannot always be an evidence file, and that is by design.** 4,301 of the graph's 11,332 Observations retain no response body; for NCHS's 25 judged cells, 100 of 160 supporting Observations are `links` HEAD probes, and `assessment/harness/scan/collectors/links.py` writes `body_sha256: None, body_path: None` deliberately — there is no body to keep, and the evidence is the status and content type recorded on the Observation. Those cells carry a `graph` locator on the Observation and say so in `retention`, rather than an `evidence` locator naming a file that was never written. This is a different fact from `Finding.evidence_unretained` (the append-only admission that cited evidence is *gone*), and both are reported under their own names.
12. **"doc_id and section on every hit" cannot hold for record-sourced hits.** An indicator's text and an action's description have no corpus document — they are the record's own prose. Those hits carry `doc_id: null`, `section` set to the construct or the outcome, and a `record` locator that resolves; definition and technique hits carry the real corpus address. Honouring the sentence literally would have meant inventing a doc_id, which is the one thing a locator may not be.
13. **"the round-trip gate's last status" is not stored anywhere**, so there was nothing to read. `get_overview` **recomputes** it against the database, cell for cell over all 171 nodes, using `scripts/load_framework_graph.py::flatten` — the same comparison `tests/test_framework_projection_roundtrip.py` makes. A cached status is exactly the thing DD-057 exists to distrust: a stale projection does not look stale, it answers.
14. **Decision 4 asks for a generated page but the write set has no generator.** `mcp/airkg_doc.py` is inside `mcp/`, which the write set covers. It has a `--check` mode that re-renders into memory and diffs, so "generated, not typed" is a thing the protected-paths check asserts rather than a thing the RESULT claims.

---

## 5. The gate

| check | command | result | tier |
|---|---|---|---|
| full suite | `/opt/anaconda3/bin/python3 -m pytest tests/ assessment/ -q -rs` | **2425 passed, 3 skipped, 12 xfailed, 0 deselected, 0 failed**, `EXIT=0`, 1419.56 s (0:23:39) | **full** (`make gate-full` equivalent) |
| Seldon | `seldon verify` | **All checks passed**, `EXIT=0` | — |
| protected paths | `bash scripts/check_protected_mcp.sh` | **PROTECTED PATHS OK**, `EXIT=0` | — |
| projection round-trip + this task's tests | `pytest tests/test_framework_projection_roundtrip.py tests/test_mcp_server.py -q -rs` | **80 passed, 0 skipped, 0 xfailed, 0 deselected**, `EXIT=0`, 4.24 s | — |

**The three skips are the expected three**, quoted from the run:

* `tests/test_dispatch_config.py:333` — `interactive_only: SELDON_SESSION_ID is set, so this is a dispatched session, which holds its own task's claim and dirties the tree for its whole life`
* `tests/test_scan_harness.py:281` — `E5 judges the cycle's controls, not a surface`
* `assessment/tests/test_g1_preservation.py:337` — `no dev proposition publishes SE and CI together`

**No Neo4j test skipped.** The round-trip gate ran, which is what makes every Cypher-derived number in this RESULT valid under DD-057, and the 30 graph-backed tests of `tests/test_mcp_server.py` ran rather than skipping.

`tests/test_mcp_server.py` contributes **72 of the 2,425** (45 test functions, 72 after parametrisation): **27** rails, **25** tools-and-locators, **20** through the in-process client, the registration and the credential resolver. The delta against the previous full run is not quoted, because the previous full-tier count on record is `2026-09-17_unassigned_indicators_RESULT.md`'s and two tasks landed between it and this one; what is checkable is the file's own contribution, and `pytest tests/test_mcp_server.py --collect-only -q` prints it.

---

## 6. Logs, and where to re-read every number above

| number | log |
|---|---|
| suite counts and wall clock | `logs/mcp_gate_full.log` |
| `seldon verify` | `logs/mcp_verify.log` |
| protected paths | `logs/mcp_protected.log` |
| round-trip gate + this task's tests | `logs/mcp_roundtrip.log` |

`logs/` is gitignored; what ships is this file and the generated page.

**Re-derive any tool output above** with `/opt/anaconda3/bin/python3 mcp/airkg_doc.py --check`, which fails if the page and the tools have drifted, or by calling the tool: `/opt/anaconda3/bin/python3 -c "import sys; sys.path.insert(0,'mcp'); import airkg_tools as T; print(T.Tools(graph=T.Graph()).get_overview())"`.

---

## 7. What is now possible that was not, and what the next task should verify

A client can ask one question and get the framework, the instrument, the verdict, the bytes and the prescription with the addresses of all five. That is DN-005 §2.4's "one interface", and it is the layer, not the goal: the framework is the goal, and this is the way to reach it without opening five files.

What a following OODA should check against the live graph before trusting anything here:

* **`get_overview().projection_gate.status` is `green`.** Every Cypher-derived answer in this RESULT stands on it, and it is recomputed on every call precisely so it can be checked rather than remembered.
* **The tier counts are still 34 M / 2 O / 5 D / 8 unassigned.** They are asserted as literals in `tests/test_mcp_server.py` on purpose: a write-back that moves an indicator without a task saying so fails the test rather than silently changing what the server reports.
* **No band has been cleared.** `get_prescriptions()` prints `pending` for a band with no estimate; if any appears, the operator cleared one and the prescription layer's §2 table is live again.
* **DN-005 §2.4 also names "a natural-language front", and decision 5 declined to build one**: the MCP client is the front. If a following task wants a web front, that is a *publication* under DN-005 §5 rule 3 and the operator's, not a next step here.
