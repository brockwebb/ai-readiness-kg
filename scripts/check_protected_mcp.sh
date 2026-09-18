#!/usr/bin/env bash
# The write set of `cc_tasks/2026-09-17_mcp_over_the_graph.md`, asserted against HEAD.
#
#   "**Write set:** `mcp/` (new: server module, tools, guard, `pyproject` entry or
#    `requirements` line), `tests/test_mcp_server.py` (new, in-process client against the
#    tools), `.mcp.json`, `docs/design/mcp_over_the_graph.md` (new, generated content),
#    `scripts/check_protected_mcp.sh` (new), `seldon_events.jsonl`, the RESULT. The framework
#    record is not written. `docs/` otherwise byte-identical."
#
# This server is an EXPOSURE layer: it reads and it measures nothing. So the strongest thing
# this check can assert is that nothing it could have measured moved — no event, no evidence
# file, no cycle payload, no matrix, no framework record — and that the one page it added is
# the page its generator produces rather than a page somebody typed.
set -u
cd "$(dirname "$0")/.." || exit 2
fail=0
PY=/opt/anaconda3/bin/python3

changed_and_new() {
  { git diff --name-only HEAD -- "$@"; git ls-files --others --exclude-standard -- "$@"; } \
    | sed '/^$/d' | sort -u
}

# 1. Untouched outright. Everything this task must not have measured, judged or republished.
for p in 'framework/' 'state/' 'corpus/' 'assessment/' 'events/' 'kg/' 'docs/reports/' \
         'docs/data/' 'docs/crosswalk/' 'LICENSE' 'LICENSE-DATA' 'controls.yaml' \
         'dixie_evidence.yaml' 'seldon.yaml' 'Makefile' 'CITATION.cff' '.zenodo.json' \
         'CLAUDE.md'; do
  moved=$(changed_and_new "$p")
  if [ -n "$moved" ]; then
    echo "FAIL protected path moved: $p"; echo "$moved" | sed 's/^/       /'; fail=1
  fi
done

# 2. `docs/` moved in exactly one place: the new page.
docs_moved=$(changed_and_new 'docs/')
if [ "$docs_moved" != "docs/design/mcp_over_the_graph.md" ]; then
  echo "FAIL docs/ is not byte-identical apart from the new page:"
  echo "$docs_moved" | sed 's/^/       /'; fail=1
fi

# 3. Every path that moved is on the list.
ALLOWED=(
  'mcp/airkg_guard.py'
  'mcp/airkg_tools.py'
  'mcp/airkg_server.py'
  'mcp/airkg_doc.py'
  'tests/test_mcp_server.py'
  '.mcp.json'
  'pyproject.toml'
  'docs/design/mcp_over_the_graph.md'
  'scripts/check_protected_mcp.sh'
  'seldon_events.jsonl'
  'cc_tasks/2026-09-17_mcp_over_the_graph_RESULT.md'
)
while read -r f; do
  [ -z "$f" ] && continue
  ok=0
  for a in "${ALLOWED[@]}"; do [ "$f" = "$a" ] && ok=1; done
  if [ "$ok" -eq 0 ]; then echo "FAIL moved outside the write set: $f"; fail=1; fi
done <<< "$(changed_and_new .)"

# 4. THE SHADOW GUARD. `mcp/` must not be a package: a top-level `mcp/__init__.py` in this
#    repository shadows the installed `mcp` distribution that fastmcp imports, and every test
#    in the suite that touches fastmcp dies with
#    `ImportError: cannot import name 'McpError' from 'mcp'`. A namespace directory does not
#    shadow a regular package, which is why this arrangement works — and why an `__init__.py`
#    added later would be a one-line change that breaks the suite for a reason nobody would
#    look for in `mcp/`.
if [ -e mcp/__init__.py ]; then
  echo "FAIL mcp/__init__.py exists; it shadows the installed 'mcp' package fastmcp imports"
  fail=1
fi
if ! $PY - <<'EOF'
import sys
sys.path.insert(0, ".")          # the shadow condition: repo root FIRST, as pytest puts it
import fastmcp, mcp, pathlib
ours = pathlib.Path("mcp").resolve()
if pathlib.Path(mcp.__file__).resolve().is_relative_to(ours):
    print(f"FAIL `import mcp` resolved to this repo's {mcp.__file__}, not the distribution")
    raise SystemExit(1)
print(f"   fastmcp {fastmcp.__version__} imports with the repo root on sys.path")
EOF
then fail=1; fi

# 5. The page is GENERATED, not typed: the generator re-renders and compares.
if ! $PY mcp/airkg_doc.py --check; then
  echo "FAIL docs/design/mcp_over_the_graph.md is not what the tools answer"; fail=1
fi

# 6. Read-only in fact, not only in the rail. No module under `mcp/` may open a write
#    transaction or run a write clause of its own: `Graph.read` is the ONE place a statement
#    reaches the database and it uses the driver's read transaction.
if grep -nE '\b(execute_write|begin_transaction)\b' mcp/*.py; then
  echo "FAIL a module under mcp/ opens a write transaction"; fail=1
fi
if [ "$(grep -c 'execute_read' mcp/airkg_tools.py)" -lt 1 ]; then
  echo "FAIL mcp/airkg_tools.py no longer runs its statements in a read transaction"; fail=1
fi

# 7. `.mcp.json` names an interpreter that exists and a server file that exists.
if ! $PY - <<'EOF'
import json, pathlib, sys
cfg = json.loads(pathlib.Path(".mcp.json").read_text(encoding="utf-8"))
e = cfg["mcpServers"]["ai-readiness-kg"]
bad = []
if not pathlib.Path(e["command"]).exists():
    bad.append(f"interpreter {e['command']} does not exist")
if not pathlib.Path(e["args"][-1]).exists():
    bad.append(f"server {e['args'][-1]} does not exist")
print("\n".join(f"FAIL {b}" for b in bad) or "   .mcp.json: interpreter and server both exist")
sys.exit(1 if bad else 0)
EOF
then fail=1; fi

# 8. Logs are append-only. This task writes only its own state transitions.
if git diff HEAD -- seldon_events.jsonl | grep -q '^-[^-]'; then
  echo "FAIL seldon_events.jsonl lost or changed a line; the log is append-only"; fail=1
fi

if [ "$fail" -eq 0 ]; then echo "PROTECTED PATHS OK"; fi
exit "$fail"
