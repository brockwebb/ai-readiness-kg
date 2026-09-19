# Run the harness on your own site

The same instrument this project runs over the federal statistical system can scan your site: the same control fixtures first, the same legs and rules, the same manners. It writes a verdict for every leg with the reason behind it, the fixes ranked for you, and what it could not see and what would let it. Run it by hand or on a schedule you set. Neo4j is optional, and Seldon is not used.

`cc_tasks/2026-09-19_adopter_path.md`. **Every `bash` block on this page is run by the gate, word for word and in order** (`tests/test_adopter_path.py::test_the_runbook_runs_as_written`, log in `logs/adopt_runbook.log`). The gate uses a loopback fixture as "your site", so its frame names `127.0.0.1:${SITE_PORT}`. Replace that with your own URLs. Blocks marked `not run by the gate` need the network or a database, and each says why.

## What you need

* **Python 3.12** (the gate ran 3.12.4) with nine packages. These are the third-party modules the scan and the report import, and the gate checks the list against the imports the run actually loaded. Versions are the ones the gate ran under:
  `beautifulsoup4` 4.12.3, `extruct` 0.18.0, `httpx` 0.28.1, `jsonschema` 4.26.0, `Protego` 0.1.16, `pyshacl` 0.40.1, `rdflib` 7.6.0, `ultimate-sitemap-parser` 1.8.1, `PyYAML` 6.0.1.
* **`make`**.
* **Optional:** `neo4j` (6.0.3) and a Neo4j server, if you want graph answers; `fastmcp` (3.2.3), if you want to connect the MCP server to a client.
* **Your own identity for the scanner** (step 2). A scan that reaches any host other than your own machine will not run without one.

## 1. Get the code (not run by the gate: needs the network)

```bash not-run-by-gate
git clone https://github.com/brockwebb/ai-readiness-kg.git
cd ai-readiness-kg
python3 -m pip install beautifulsoup4 extruct httpx jsonschema Protego pyshacl rdflib ultimate-sitemap-parser PyYAML
```

The gate copies the working tree to a scratch directory instead: every tracked file and none of the ignored ones. That is what a clone of the pushed commit holds.

Tell `make` which Python to use, and check that it has the packages:

```bash
export PY="$(command -v python3)"
"$PY" -c 'import bs4, extruct, httpx, jsonschema, protego, pyshacl, rdflib, usp, yaml; print("requirements OK")'
```

## 2. Set your User-Agent

The scanner sends one identity on every request, with a contact a host operator can reach (DD-060, following RFC 9309 practice). Out of the box that identity is this project's. A scan of your site has to go out under yours, so `run.py` refuses to reach any non-loopback host under this project's identity, or under one with no contact. The refusal happens before anything is fetched:

```bash
mkdir -p frames
cat > frames/example.yaml <<'EOF'
frame: example
bodies:
  - name: EXAMPLE
    home: https://www.example.org/
EOF
"$PY" assessment/harness/scan/run.py --frame frames/example.yaml || echo "refused, as it should be"
```

Set it in `assessment/harness/scan/params.yaml`, under `manners:`. Use your own product name and contact, not the ones below:

```bash
sed -i.orig 's|^  user_agent: .*|  user_agent: "example-readiness-scan/1.0 (+mailto:webmaster@example.org)"|' assessment/harness/scan/params.yaml
grep -n '^  user_agent:' assessment/harness/scan/params.yaml
```

The rate limit (1 request per second per host), robots.txt first, and the rest of `manners:` stay as they are. Changing the identity changes `params_hash`, which every Observation carries: the run records that it went out under your name.

## 3. Write your frame

A frame names each body you want measured: a name, its home page, and the flagship pages that are its products. One body is the normal case. For your site it looks like this:

```yaml
frame: my-site
bodies:
  - name: MYSITE
    home: https://www.example.gov/
    flagships:
      - https://www.example.gov/data/product-one
      - https://www.example.gov/data/product-two
```

Each body gets three kinds of surface. The home page gets the host-level legs. The host's well-known set (`robots.txt`, the sitemap, `/.well-known/`) gets A12. Each flagship gets the product legs. `tier: C` on a body limits it to the tier-0 legs, as this project does for its reference hosts. A frame holds one body per host.

The gate's frame is the same shape, pointed at the loopback fixture:

```bash
cat > frames/my_site.yaml <<EOF
frame: my-site
bodies:
  - name: MYSITE
    home: http://127.0.0.1:${SITE_PORT}/index.html
    flagships:
      - http://127.0.0.1:${SITE_PORT}/index.html
      - http://127.0.0.1:${SITE_PORT}/second.html
EOF
```

## 4. Scan

```bash
make scan-now FRAME=frames/my_site.yaml
```

First the control fixtures run on your own machine. If any rule misfires on them, the scan stops before your site is touched. Then every surface of the frame is scanned, robots.txt first, at 1 request per second. Then the matrices and the report are rendered. Everything is written under `out/my-site/`:

| path | what it is |
|---|---|
| `out/my-site/LATEST` | the name of the last run |
| `out/my-site/state/<cycle>.json` | the payload: every Observation and every Finding |
| `out/my-site/evidence/<cycle>/` | every response body the run kept, filed by sha256 |
| `out/my-site/reports/scan_matrix_*` | the host-level and product matrices, JSON and CSV |
| `out/my-site/reports/publication.yaml` | the frame's cycle of record (its newest run) |
| `out/my-site/report/<cycle>.md` | the report |

A second scan of the same frame on the same day is refused unless it takes a rerun letter: `"$PY" assessment/harness/scan/run.py --frame frames/my_site.yaml --rerun b`, then `"$PY" scripts/render_run_report.py --frame frames/my_site.yaml`. `--target <body>` scans one body of a multi-body frame as a spot run, and its report shows it beside the frame's last run.

## 5. Read where you stand

```bash
cat out/my-site/LATEST
cat "out/my-site/report/$(cat out/my-site/LATEST).md"
ls out/my-site/reports
```

The same answers, one at a time. The score and the sentence your rank rests on:

```bash
"$PY" scripts/score.py --run out/my-site --body MYSITE
```

Ask the MCP server's verbs directly, without a client and without Neo4j:

```bash
"$PY" -c 'import sys; sys.path.insert(0, "mcp"); import airkg_tools as T; print(T.Tools(graph=None, run="out/my-site").get_body("MYSITE")["summary"])'
```

Every verdict can be re-derived from the stored evidence alone, with no network:

```bash
"$PY" assessment/harness/scan/rederive.py --from "out/my-site/state/$(cat out/my-site/LATEST).json" | tail -1
```

## 6. On demand, or on a schedule

The schedule is set in `params.yaml` under `schedule:`. `when: on_demand`, the default, installs nothing, and you scan with `make scan-now`. A five-field cron expression, with `frame:` naming your frame file, is installed on your machine by `make install-schedule`. That writes a cron line, or on macOS a launchd agent in `~/Library/LaunchAgents/`, and prints what it wrote. The gate runs it with the default:

```bash
make install-schedule
```

For example, to scan every Monday at 06:00:

```yaml
schedule:
  when: "0 6 * * 1"
  frame: frames/my_site.yaml
```

## 7. With Neo4j (optional; not run by the gate)

Without Neo4j you have every file above, and every verb the report uses. Neo4j adds the graph: `run_cypher`, and the projection-gate status. `make project RUN=out/my-site` puts the run on the event log of your checkout, then projects the framework and every cycle on the log into the database named in `seldon.yaml`. The run's evidence stays in `out/`, where the run left it. It needs `NEO4J_USER` and `NEO4J_PASS`.

The gate does not run this block. It would reset the projection in the one database this machine has, which is this project's.

```bash not-run-by-gate
make project RUN=out/my-site
"$PY" mcp/airkg_server.py --run out/my-site
```

To use the server from an MCP client, register the stdio command. Add `--no-graph` to run it without Neo4j:

```json
{"mcpServers": {"ai-readiness-kg": {"command": "python3",
  "args": ["/path/to/ai-readiness-kg/mcp/airkg_server.py", "--no-graph", "--run", "/path/to/ai-readiness-kg/out/my-site"]}}}
```

## What needs Neo4j and what does not

| | without Neo4j | with Neo4j |
|---|---|---|
| scan, payload, evidence, matrices, report | yes | yes |
| `score.py --run` | yes (it never reads the graph) | the same |
| `get_body`, `get_prescriptions`, `get_requirements` (`--run`) | yes. Finding reasons and bytes come from the run's payload | yes. They come from the projection |
| `get_evidence` (`--run`) | yes, from the payload | yes, from the projection |
| `get_indicator`'s verdict counts, `run_cypher`, the projection gate, supersession on `get_cycle_of_record` | no. Each says so in words and does not guess | yes |
