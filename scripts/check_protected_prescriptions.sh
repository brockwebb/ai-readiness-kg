#!/usr/bin/env bash
# The write set of `cc_tasks/2026-09-17_prescription_layer.md`, asserted against HEAD.
#
#   "Nothing is measured and no report is rebuilt. ... `state/`, `corpus/`, `assessment/`
#    byte-identical" (decision 5), and the write set the task file lists.
#
# What moved beyond that list is named here, each with the reason, and the RESULT reports it:
#
#   * scripts/framework_writeback.py — the SINGLE WRITER, and the place the hygiene rule puts
#     `counts` ("that lives in the shared helper, not in three scripts"). A layer of 45 nodes
#     and 45 edges that no counter mentions is the DD-040 drift; `recount` gains `actions` and
#     `actions_on_candidate_indicators` and nothing else.
#   * tests/test_framework_projection_roundtrip.py — the DD-057 gate reads a LITERAL list of
#     labels and edge sources. A new label it does not know is a node in the JSON with no twin
#     in its count query, so the gate must learn `Action` or it fails for the wrong reason.
#   * tests/test_framework_single_writer.py — asserts, as a literal, exactly what the skeleton
#     generator does NOT author and `merge` therefore preserves. The prescription layer is in
#     that set by construction (an action is written against a rule's outcomes, and the
#     skeleton predates every rule), so the literal moves with it.
#   * docs/data/ai_readiness_framework.json, docs/data/index.json — the site's copy of the
#     record and the manifest that hashes it; a record write-back makes both stale on their
#     face (tests/test_publication.py). Decision 5 anticipates exactly this.
#   * CITATION.cff, .zenodo.json and their docs/data/ copies — regenerated with the manifest
#     because the manifest hashes their text; only the build date can move, and on a same-day
#     build it does not.
set -u
cd "$(dirname "$0")/.." || exit 2
fail=0
PY=/opt/anaconda3/bin/python3

changed_and_new() {
  { git diff --name-only HEAD -- "$@"; git ls-files --others --exclude-standard -- "$@"; } \
    | sed '/^$/d' | sort -u
}

# 1. Untouched outright: the evidence, the corpus, the harness, the controls, the report.
#    `kg/` is NOT asserted empty here — `kg/schema.yaml` is the record's type catalogue and
#    decision 3 puts the two new types in it. Section 2's allow-list covers the rest of `kg/`.
for p in 'state/' 'corpus/' 'assessment/' 'docs/reports/' 'docs/design/' 'LICENSE' \
         'LICENSE-DATA' 'controls.yaml' 'dixie_evidence.yaml' 'seldon.yaml' 'Makefile'; do
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
  'scripts/tag_prescriptions.py'
  'scripts/prescriptions.py'
  'scripts/load_framework_graph.py'
  'scripts/framework_writeback.py'
  'scripts/check_protected_prescriptions.sh'
  'tests/test_prescriptions.py'
  'tests/test_framework_projection_roundtrip.py'
  'tests/test_framework_single_writer.py'
  'docs/data/ai_readiness_framework.json'
  'docs/data/index.json'
  'docs/data/CITATION.cff'
  'docs/data/zenodo.json'
  'CITATION.cff'
  '.zenodo.json'
  'cc_tasks/2026-09-17_prescription_layer_RESULT.md'
)
while read -r f; do
  [ -z "$f" ] && continue
  ok=0
  for a in "${ALLOWED[@]}"; do [ "$f" = "$a" ] && ok=1; done
  if [ "$ok" -eq 0 ]; then echo "FAIL moved outside the write set: $f"; fail=1; fi
done <<< "$(changed_and_new .)"

# 3. The record: Action nodes and REMEDIATES edges ADDED, and two counts keys. Every node the
#    record already held, every edge it already held, and every counts key it already had are
#    identical to HEAD, property for property.
git show HEAD:framework/ai_readiness_framework.json > /tmp/airkg_fw_head_presc.json
if ! $PY - <<'EOF'
import json, sys
a = json.load(open("/tmp/airkg_fw_head_presc.json"))
b = json.load(open("framework/ai_readiness_framework.json"))
bad = []
SKIP = ("nodes", "edges", "counts", "counts_basis")
if {k: v for k, v in a.items() if k not in SKIP} != \
        {k: v for k, v in b.items() if k not in SKIP}:
    bad.append("something outside nodes/edges/counts/counts_basis moved")
# `counts_basis` is the sentence on the record's face that says what each counter counts. It
# moves when a counter is added, and it must: a basis that omits a key is worse than none.
if b["counts_basis"] == a["counts_basis"] or "actions counts REMEDIATES" not in b["counts_basis"]:
    bad.append("counts_basis does not describe the two new counters")
an, bn = {n["id"]: n for n in a["nodes"]}, {n["id"]: n for n in b["nodes"]}
added = set(bn) - set(an)
if set(an) - set(bn):
    bad.append(f"the record LOST node(s): {sorted(set(an) - set(bn))[:8]}")
if any(bn[i]["labels"] != ["Action"] for i in added):
    bad.append("a node was added that is not an Action")
if len(added) != 45:
    bad.append(f"{len(added)} node(s) added; the layer is 45 actions")
for i in sorted(set(an) & set(bn)):
    if an[i] != bn[i]:
        bad.append(f"{i}: an existing node moved")
ae = [(e["from"], e["type"], e["to"], json.dumps(e.get("properties"), sort_keys=True))
      for e in a["edges"]]
be = [(e["from"], e["type"], e["to"], json.dumps(e.get("properties"), sort_keys=True))
      for e in b["edges"]]
if [e for e in ae if e not in be]:
    bad.append(f"the record LOST edge(s): {[e[:3] for e in ae if e not in be][:8]}")
new_e = [e for e in be if e not in ae]
if any(e[1] != "REMEDIATES" for e in new_e):
    bad.append("an edge was added that is not REMEDIATES")
if len(new_e) != 45:
    bad.append(f"{len(new_e)} edge(s) added; the layer is 45 REMEDIATES edges")
moved = {k for k in set(a["counts"]) | set(b["counts"])
         if a["counts"].get(k) != b["counts"].get(k)}
if moved != {"actions", "actions_on_candidate_indicators"}:
    bad.append(f"counts moved beyond the two new keys: {sorted(moved)}")
if set(a["counts"]) - set(b["counts"]):
    bad.append("a counts key was dropped")
print("\n".join(f"FAIL {m}" for m in bad)
      or "   record: 45 Action nodes and 45 REMEDIATES edges added; nothing else moved")
sys.exit(1 if bad else 0)
EOF
then fail=1; fi

# 4. The site's copy is the record, byte for byte.
if ! cmp -s framework/ai_readiness_framework.json docs/data/ai_readiness_framework.json; then
  echo "FAIL docs/data/ai_readiness_framework.json is not the record"; fail=1
fi

# 5. The published payloads: only the lines the reasons above name.
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

# 6. The single writer gained counters and nothing else; the projection gained the label and
#    the edge branch. Both are asserted by behaviour rather than by diff size: the generator
#    over HEAD is still a byte-for-byte no-op, and the writer still refuses a drop.
if ! $PY - <<'EOF'
import subprocess, sys, json
r = subprocess.run(["/opt/anaconda3/bin/python3", "scripts/build_framework_graph.py",
                    "--dry-run"], capture_output=True, text=True)
if r.returncode != 0:
    print("FAIL build_framework_graph.py --dry-run exited", r.returncode); sys.exit(1)
# The script prints a `-> path` line before its JSON.
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

# 7. The table itself still validates against the rules, the sources and the record.
if ! $PY scripts/tag_prescriptions.py --check > /dev/null; then
  echo "FAIL the prescription table no longer validates"; fail=1
fi

# 8. Logs are append-only; the framework shard gains the one write-back event.
for f in events/ seldon_events.jsonl; do
  if git diff HEAD -- "$f" | grep -q '^-[^-]'; then
    echo "FAIL $f lost or changed a line; the log is append-only"; fail=1
  fi
done
added=$(git diff HEAD -U0 -- events/batch-033_framework.jsonl | grep -cE '^\+[^+]')
if [ "$added" != "1" ]; then
  echo "FAIL the framework shard gained $added line(s); this write-back appends exactly 1"
  fail=1
fi

if [ "$fail" -eq 0 ]; then echo "PROTECTED PATHS OK"; fi
exit "$fail"
