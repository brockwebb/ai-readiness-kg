#!/usr/bin/env bash
. "$(dirname "$0")/check_protected_lib.sh"
# The write set of `cc_tasks/2026-09-17_measurement_tiers.md`, asserted against HEAD.
#
#   "Nothing is measured, re-judged or rebuilt. No cycle runs. `state/`, `corpus/`,
#    `docs/reports/` byte-identical except the regenerated tool map and any report page that
#    prints the tier column" (decision 6), and the write set the task file lists.
#
# What moved beyond that list is named here, each with the reason, and the RESULT reports it:
#
#   * docs/reports/scan_matrix_product_2026-09-10_rj2.json — decision 5 moves the header off it;
#     the only lines that may change are the removed `legs_withdrawn` block.
#   * docs/data/sources_per_check.json — G1-D's rows are labelled off the indicator node, and the
#     label key moved from `measurement_tier` to `measurement_level` with the node's property.
#   * docs/data/ai_readiness_framework.json, docs/data/index.json — the site's copy of the record
#     and the manifest that hashes it; a record write-back makes both stale on their face.
#   * CITATION.cff, .zenodo.json and their docs/data/ copies — the manifest's build stamp and the
#     citation files' date are one stamp (tests/test_publication.py); only the date moves.
#   * scripts/build_l0_site.py, scripts/build_l0_matrices.py, tests/test_publication.py — the
#     readers of the two moved facts, and the manifest defect a narrow build exposed.
set -u
cd "$(dirname "$0")/.." || exit 2
fail=0
PY=/opt/anaconda3/bin/python3

changed_and_new() {
  { git diff --name-only HEAD -- "$@"; git ls-files --others --exclude-standard -- "$@"; } \
    | sed '/^$/d' | sort -u
}

# 1. Untouched outright: evidence, the corpus, the KG code, the harness, the prior RESULTs.
for p in 'state/' 'corpus/' 'kg/' 'assessment/' 'LICENSE' 'LICENSE-DATA' 'controls.yaml' \
         'dixie_evidence.yaml' 'seldon.yaml'; do
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
  'scripts/tag_measurement_tiers.py'
  'scripts/scan_tool_map.py'
  'scripts/build_l0_matrices.py'
  'scripts/build_l0_site.py'
  'scripts/check_protected_measurement_tiers.sh'
  'tests/test_measurement_tiers.py'
  'tests/test_publication.py'
  'docs/design/scan_tool_map.md'
  'docs/design/2026-09-15_DN-005_reorientation_the_framework_is_the_goal_ADDENDUM_01.md'
  'docs/reports/scan_matrix_product_2026-09-10_rj2.json'
  'docs/data/sources_per_check.json'
  'docs/data/ai_readiness_framework.json'
  'docs/data/index.json'
  'docs/data/CITATION.cff'
  'docs/data/zenodo.json'
  'CITATION.cff'
  '.zenodo.json'
  'cc_tasks/2026-09-17_measurement_tiers_RESULT.md'
)
while read -r f; do
  [ -z "$f" ] && continue
  ok=0
  for a in "${ALLOWED[@]}"; do [ "$f" = "$a" ] && ok=1; done
  if [ "$ok" -eq 0 ]; then echo "FAIL moved outside the write set: $f"; fail=1; fi
done <<< "$(changed_and_new .)"

# 3. The record: only the tier properties on indicator nodes, and G1-D's rename. Everything
#    else — every other node, every edge, `counts` — is identical to HEAD.
git show HEAD:framework/ai_readiness_framework.json > /tmp/airkg_fw_head.json
if ! $PY - <<'EOF'
import json, sys
a = json.load(open("/tmp/airkg_fw_head.json"))
b = json.load(open("framework/ai_readiness_framework.json"))
OK = {"measurement_tier", "measurement_basis", "tier_source", "tier_rule", "tier_note",
      "tier_unassigned_reason", "measurement_tier_source", "measurement_level",
      "measurement_level_source"}
bad = []
if {k: v for k, v in a.items() if k != "nodes"} != {k: v for k, v in b.items() if k != "nodes"}:
    bad.append("something outside `nodes` moved")
an, bn = {n["id"]: n for n in a["nodes"]}, {n["id"]: n for n in b["nodes"]}
if set(an) != set(bn):
    bad.append("the node set moved")
for i in an:
    x, y = an[i], bn.get(i, {})
    if x.get("labels") != y.get("labels"):
        bad.append(f"{i}: labels moved")
    px, py = x["properties"], y.get("properties", {})
    moved = {k for k in set(px) | set(py) if px.get(k) != py.get(k)}
    if moved and "AssessmentIndicator" not in x["labels"]:
        bad.append(f"{i}: a non-indicator node moved {sorted(moved)}")
    if moved - OK:
        bad.append(f"{i}: moved outside the tier keys {sorted(moved - OK)}")
g1 = (an["ind:G1-D"]["properties"], bn["ind:G1-D"]["properties"])
if (g1[0].get("measurement_tier"), g1[0].get("measurement_tier_source")) != \
        (g1[1].get("measurement_level"), g1[1].get("measurement_level_source")):
    bad.append("G1-D's level did not move verbatim")
print("\n".join(f"FAIL {m}" for m in bad) or "   record: only tier keys and G1-D's rename moved")
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
x=$(only_lines docs/data/sources_per_check.json '^[+-] *"measurement_(tier|level)": "product",$')
[ -n "$x" ] && { echo "FAIL sources_per_check.json moved outside the G1-D label key:"; echo "$x" | cut -c1-160; fail=1; }
x=$(only_lines docs/data/index.json '^[+-] *"(sha256|bytes|built_at|build_commit)": ')
[ -n "$x" ] && { echo "FAIL index.json moved outside digests and the build stamp:"; echo "$x" | cut -c1-160; fail=1; }
for f in CITATION.cff docs/data/CITATION.cff; do
  x=$(only_lines "$f" "^[+-]date-released: '[0-9-]+'$")
  [ -n "$x" ] && { echo "FAIL $f moved outside its date:"; echo "$x"; fail=1; }
done
for f in .zenodo.json docs/data/zenodo.json; do
  x=$(only_lines "$f" '^[+-] *"publication_date": "[0-9-]+",$')
  [ -n "$x" ] && { echo "FAIL $f moved outside its date:"; echo "$x"; fail=1; }
done
# The product matrix only LOSES lines, and only the withdrawal block.
if git diff HEAD -- docs/reports/scan_matrix_product_2026-09-10_rj2.json | grep -qE '^\+[^+]'; then
  echo "FAIL the product matrix GAINED a line; decision 5 only removes its header"; fail=1
fi
if git show HEAD:docs/reports/scan_matrix_product_2026-09-10_rj2.json \
   | $PY -c 'import json,sys; d=json.load(sys.stdin); d.pop("legs_withdrawn"); print(json.dumps(d, sort_keys=True))' \
   > /tmp/airkg_pm_head.json && \
   $PY -c 'import json; print(json.dumps(json.load(open("docs/reports/scan_matrix_product_2026-09-10_rj2.json")), sort_keys=True))' \
   > /tmp/airkg_pm_now.json && ! cmp -s /tmp/airkg_pm_head.json /tmp/airkg_pm_now.json; then
  echo "FAIL the product matrix moved outside its legs_withdrawn header"; fail=1
fi

# 6. The tool map is what its generator produces.
if ! $PY scripts/scan_tool_map.py --check >/dev/null; then
  echo "FAIL docs/design/scan_tool_map.md is not its generator's output"; fail=1
fi

# 7. Logs are append-only; the framework shard gains the one write-back event.
for f in events/ seldon_events.jsonl; do
  if git diff HEAD -- "$f" | grep -q '^-[^-]'; then
    echo "FAIL $f lost or changed a line; the log is append-only"; fail=1
  fi
done
added=$(git diff HEAD -U0 -- events/batch-033_framework.jsonl | grep -cE '^\+[^+]')
if [ "$added" != "1" ]; then
  echo "FAIL the framework shard gained $added line(s); the tier write-back appends exactly 1"
  fail=1
fi

if [ "$fail" -eq 0 ]; then echo "PROTECTED PATHS OK"; fi
exit "$fail"
