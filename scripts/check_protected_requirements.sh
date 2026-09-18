#!/usr/bin/env bash
. "$(dirname "$0")/check_protected_lib.sh"
# The write set of `cc_tasks/2026-09-18_requirements_layer.md`, asserted against HEAD.
#
#   "`state/`, `corpus/`, `docs/reports/` byte-identical", and decision 6: "Nothing is
#   measured. The site's framework copy and manifest move as before; the MCP page regenerates."
#
# Paths beyond the task file's list, each reported as a premise in the RESULT:
#
#   * scripts/framework_writeback.py — `recount` is the one place a `counts` key is derived,
#     and decision 3 asks for the layer's counts; the RESULT names them.
#   * scripts/load_framework_graph.py — "the projection for the two node types and the edge"
#     is this file: the labels it owns and the edge types it may write are literal whitelists.
#   * tests/test_mcp_server.py, tests/test_framework_single_writer.py,
#     tests/test_framework_projection_roundtrip.py — each pins the record's or the server's
#     shape (nine tools, the preserved-node census, the projected labels) and moves with it.
set -u
cd "$(dirname "$0")/.." || exit 2
fail=0
PY=/opt/anaconda3/bin/python3

changed_and_new() {
  { git diff --name-only HEAD -- "$@"; git ls-files --others --exclude-standard -- "$@"; } \
    | sed '/^$/d' | sort -u
}

# 1. Untouched outright.
for p in 'state/' 'corpus/' 'assessment/' 'docs/reports/' 'docs/research/' 'docs/crosswalk/' \
         'framework/skeleton' 'LICENSE' 'LICENSE-DATA' 'controls.yaml' 'dixie_evidence.yaml' \
         'seldon.yaml' 'Makefile'; do
  moved=$(changed_and_new "$p")
  if [ -n "$moved" ]; then
    echo "FAIL protected path moved: $p"; echo "$moved" | sed 's/^/       /'; fail=1
  fi
done

# 2. Every path that moved is on the list.
ALLOWED=(
  'framework/ai_readiness_framework.json'
  'events/batch-033_framework.jsonl'
  'seldon_events.jsonl'
  'kg/schema.yaml'
  'scripts/tag_requirements.py'
  'scripts/framework_writeback.py'
  'scripts/load_framework_graph.py'
  'scripts/scan_tool_map.py'
  'scripts/check_protected_requirements.sh'
  'mcp/airkg_tools.py'
  'mcp/airkg_server.py'
  'mcp/airkg_doc.py'
  'tests/test_requirements.py'
  'tests/test_mcp_server.py'
  'tests/test_framework_single_writer.py'
  'tests/test_framework_projection_roundtrip.py'
  'docs/design/scan_tool_map.md'
  'docs/design/mcp_over_the_graph.md'
  'docs/data/ai_readiness_framework.json'
  'docs/data/index.json'
  'docs/data/CITATION.cff'
  'docs/data/zenodo.json'
  'CITATION.cff'
  '.zenodo.json'
  'cc_tasks/2026-09-18_requirements_layer_RESULT.md'
)
while read -r f; do
  [ -z "$f" ] && continue
  ok=0
  for a in "${ALLOWED[@]}"; do [ "$f" = "$a" ] && ok=1; done
  if [ "$ok" -eq 0 ]; then echo "FAIL moved outside the write set: $f"; fail=1; fi
done <<< "$(changed_and_new .)"

# 3. The record: the layer was ADDED and nothing else moved. New nodes are AssessmentTool and
#    Precondition only; changed nodes are indicators that gained `requirement_none_reason` and
#    nothing else; new edges are REQUIRES only; no node or edge dropped; `counts` gained the four
#    layer keys and moved no other; `counts_basis` is the only other top-level field to move.
git show HEAD:framework/ai_readiness_framework.json > /tmp/airkg_fw_head_requirements.json
if ! $PY - <<'EOF'
import json, sys
a = json.load(open("/tmp/airkg_fw_head_requirements.json"))
b = json.load(open("framework/ai_readiness_framework.json"))
bad = []
SKIP = ("nodes", "edges", "counts", "counts_basis")
if {k: v for k, v in a.items() if k not in SKIP} != {k: v for k, v in b.items() if k not in SKIP}:
    bad.append("a top-level field other than nodes, edges, counts and counts_basis moved")
NEW_KEYS = {"tools", "preconditions", "requires", "requires_on_candidate_indicators"}
if set(b["counts"]) - set(a["counts"]) != NEW_KEYS:
    bad.append(f"counts keys added: {sorted(set(b['counts']) - set(a['counts']))}")
if any(a["counts"][k] != b["counts"].get(k) for k in a["counts"]):
    bad.append("a counts key the record already held moved")
an, bn = {n["id"]: n for n in a["nodes"]}, {n["id"]: n for n in b["nodes"]}
if set(an) - set(bn):
    bad.append(f"node(s) dropped: {sorted(set(an) - set(bn))[:6]}")
added = [bn[i] for i in bn if i not in an]
if {n["labels"][0] for n in added} != {"AssessmentTool", "Precondition"}:
    bad.append(f"added labels {sorted({n['labels'][0] for n in added})}")
if any(n["labels"][0] == "Tool" for n in b["nodes"]):
    bad.append("a node carries the KG's `Tool` label")
changed = [i for i in set(an) & set(bn) if an[i] != bn[i]]
for i in changed:
    ap_, bp = an[i]["properties"], bn[i]["properties"]
    if bn[i]["labels"] != ["AssessmentIndicator"] or set(bp) - set(ap_) != {"requirement_none_reason"} \
            or any(ap_[k] != bp.get(k) for k in ap_):
        bad.append(f"{i}: changed beyond gaining requirement_none_reason")
key = lambda e: (e["from"], e["type"], e["to"])
ae, be = {key(e): e for e in a["edges"]}, {key(e): e for e in b["edges"]}
if set(ae) - set(be):
    bad.append(f"edge(s) dropped: {len(set(ae) - set(be))}")
if any(ae[k] != be[k] for k in ae if k in be):
    bad.append("an existing edge changed")
if {k[1] for k in set(be) - set(ae)} != {"REQUIRES"}:
    bad.append(f"added edge types {sorted({k[1] for k in set(be) - set(ae)})}")
print("\n".join(f"FAIL {m}" for m in bad) or
      f"   record: +{len(added)} requirement nodes, +{len(set(be) - set(ae))} REQUIRES edges, "
      f"{len(changed)} indicators gained a none-reason; nothing else moved")
sys.exit(1 if bad else 0)
EOF
then fail=1; fi

# 4. The catalogue moved only by the two node types and the one edge type.
if ! $PY - <<'EOF'
import subprocess, sys, yaml
head = yaml.safe_load(subprocess.run(["git", "show", "HEAD:kg/schema.yaml"],
                                     capture_output=True, text=True, check=True).stdout)
now = yaml.safe_load(open("kg/schema.yaml"))
for n in ("AssessmentTool", "Precondition"):
    now["assessment_layer"]["node_types"].pop(n, None)
now["assessment_layer"]["edge_types"].pop("REQUIRES", None)
print("   catalogue: only AssessmentTool, Precondition and REQUIRES were added" if head == now
      else "FAIL kg/schema.yaml moved outside the requirements layer's three entries")
sys.exit(0 if head == now else 1)
EOF
then fail=1; fi

# 5. The site's copy is the record, byte for byte.
if ! cmp -s framework/ai_readiness_framework.json docs/data/ai_readiness_framework.json; then
  echo "FAIL docs/data/ai_readiness_framework.json is not the record"; fail=1
fi

# 6. The published payloads: only the lines a record write-back is allowed to move.
only_lines() {  # $1 path, $2 ERE of the only lines that may be added or removed
  git diff HEAD -U0 -- "$1" | grep -E '^[+-][^+-]' | grep -vE "$2"
}
x=$(only_lines docs/data/index.json '^[+-] *"(sha256|bytes|built_at|build_commit)": ')
[ -n "$x" ] && { echo "FAIL index.json moved outside digests and the build stamp:"; echo "$x" | cut -c1-160; fail=1; }
for f in CITATION.cff docs/data/CITATION.cff; do
  x=$(only_lines "$f" "^[+-]date-released: '[0-9-]+'\$")
  [ -n "$x" ] && { echo "FAIL $f moved outside its date:"; echo "$x"; fail=1; }
done
for f in .zenodo.json docs/data/zenodo.json; do
  x=$(only_lines "$f" '^[+-] *"publication_date": "[0-9-]+",$')
  [ -n "$x" ] && { echo "FAIL $f moved outside its date:"; echo "$x"; fail=1; }
done

# 7. The generator over the new record is still a byte-for-byte no-op; the tables validate; the
#    two generated pages are what their generators produce now.
if ! $PY - <<'EOF'
import subprocess, sys, json
r = subprocess.run(["/opt/anaconda3/bin/python3", "scripts/build_framework_graph.py",
                    "--dry-run"], capture_output=True, text=True)
if r.returncode != 0:
    print("FAIL build_framework_graph.py --dry-run exited", r.returncode); sys.exit(1)
out = json.loads(r.stdout[r.stdout.index("{"):])
d = out["delta"]
ok = out.get("unchanged") is True and d["nodes_changed"] == 0 and d["edges_changed"] == 0 \
    and not d["nodes_added"] and not d["edges_added"] \
    and not d["nodes_removed"] and not d["edges_removed"]
print("   generator over the new record: byte-for-byte no-op" if ok
      else f"FAIL the generator is no longer a no-op: {d}")
sys.exit(0 if ok else 1)
EOF
then fail=1; fi
$PY scripts/tag_requirements.py --check > /dev/null || { echo "FAIL the requirements tables no longer validate"; fail=1; }
$PY scripts/scan_tool_map.py --check > /dev/null || { echo "FAIL the tool map is not its generator's output"; fail=1; }
$PY mcp/airkg_doc.py --check > /dev/null || { echo "FAIL the MCP page is not what the tools answer"; fail=1; }

# 8. Logs are append-only; the framework shard gains exactly the two write-back events this task
#    made (the layer, then `who_provides` on the tools — RESULT §3).
for f in events/ seldon_events.jsonl; do
  if git diff HEAD -- "$f" | grep -q '^-[^-]'; then
    echo "FAIL $f lost or changed a line; the log is append-only"; fail=1
  fi
done
added=$(git diff HEAD -U0 -- events/batch-033_framework.jsonl | grep -cE '^\+[^+]')
if [ "$added" != "2" ]; then
  echo "FAIL the framework shard gained $added line(s); this task appends exactly 2"; fail=1
fi

if [ "$fail" -eq 0 ]; then echo "PROTECTED PATHS OK"; fi
exit "$fail"
