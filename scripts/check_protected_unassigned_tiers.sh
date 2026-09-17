#!/usr/bin/env bash
# The write set of `cc_tasks/2026-09-17_unassigned_indicators.md`, asserted against HEAD.
#
#   "No matrix, figure or report is rebuilt; the site's framework copy and manifest move as in
#    the predecessors" (decision 6), and the write set the task file lists.
#
# One path moved that the task file's write set does not name, and the RESULT reports it:
#
#   * docs/design/2026-09-15_DN-005_..._ADDENDUM_02.md — decision 2's basis. ADDENDUM_01 defines
#     `harness_leg` as "a rule in rules.CURRENT serves the indicator", and three gates outside
#     the tiering layer depend on that. The seven rows decision 2 reaches have a named field
#     and no rule, so they carry the sixth basis `structured_field`, recorded there.
#   * scripts/scan_tool_map.py — decision 2 puts the structured field and the collector entry
#     point ON the node. The generated §2 row printed "no collector reaches this yet" beside a
#     source naming one, so `verdict_for` reads the node's `tier_collector` and says which
#     entry point would read what, and that no rule wires it yet. Generator-only; §2 and §4 of
#     the tool map are otherwise regenerated unchanged.
#
# Two paths the predecessor moved and this task does NOT: docs/data/sources_per_check.json (its
# only tier-derived cell is G1-D's `measurement_level`, which no decision here touches) and the
# citation files (their date is today's already).
set -u
cd "$(dirname "$0")/.." || exit 2
fail=0
PY=/opt/anaconda3/bin/python3

changed_and_new() {
  { git diff --name-only HEAD -- "$@"; git ls-files --others --exclude-standard -- "$@"; } \
    | sed '/^$/d' | sort -u
}

# 1. Untouched outright: evidence, the corpus, the KG code, the harness, the reports, the
#    controls, and every prior RESULT.
for p in 'state/' 'corpus/' 'kg/' 'assessment/' 'docs/reports/' 'docs/research/' 'LICENSE' \
         'LICENSE-DATA' 'controls.yaml' 'dixie_evidence.yaml' 'seldon.yaml' 'CITATION.cff' \
         '.zenodo.json' 'docs/data/sources_per_check.json'; do
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
  'scripts/check_protected_unassigned_tiers.sh'
  'tests/test_measurement_tiers.py'
  'docs/design/scan_tool_map.md'
  'docs/design/2026-09-15_DN-005_reorientation_the_framework_is_the_goal_ADDENDUM_02.md'
  'docs/data/ai_readiness_framework.json'
  'docs/data/index.json'
  'cc_tasks/2026-09-17_unassigned_indicators_RESULT.md'
)
while read -r f; do
  [ -z "$f" ] && continue
  ok=0
  for a in "${ALLOWED[@]}"; do [ "$f" = "$a" ] && ok=1; done
  if [ "$ok" -eq 0 ]; then echo "FAIL moved outside the write set: $f"; fail=1; fi
done <<< "$(changed_and_new .)"

# 3. The record: only the tier properties, only on indicator nodes, only on the 20 rows the
#    predecessor left unassigned. Every other node, every edge and `counts` is HEAD's.
git show HEAD:framework/ai_readiness_framework.json > /tmp/airkg_fw_head_u.json
if ! $PY - <<'EOF'
import json, sys
a = json.load(open("/tmp/airkg_fw_head_u.json"))
b = json.load(open("framework/ai_readiness_framework.json"))
OK = {"measurement_tier", "measurement_basis", "tier_source", "tier_rule", "tier_note",
      "tier_field", "tier_collector", "tier_unassigned_reason", "open_tool_candidate"}
BASIS_TIER = {"harness_leg": "M", "structured_field": "M", "judged_reading": "M",
              "evaluation": "M", "open_tool": "O", "declaration": "D"}
THE_20 = {"A7", "B1", "B2", "B4", "B5", "B6", "C5", "D2", "D3", "E1", "E2", "E3", "E7",
          "F1", "F2", "F3", "F5", "G3", "G4", "G5"}
bad = []
if {k: v for k, v in a.items() if k != "nodes"} != {k: v for k, v in b.items() if k != "nodes"}:
    bad.append("something outside `nodes` moved")
an, bn = {n["id"]: n for n in a["nodes"]}, {n["id"]: n for n in b["nodes"]}
if set(an) != set(bn):
    bad.append("the node set moved")
touched = set()
for i in an:
    x, y = an[i], bn.get(i, {})
    if x.get("labels") != y.get("labels"):
        bad.append(f"{i}: labels moved")
    px, py = x["properties"], y.get("properties", {})
    moved = {k for k in set(px) | set(py) if px.get(k) != py.get(k)}
    if not moved:
        continue
    if "AssessmentIndicator" not in x["labels"]:
        bad.append(f"{i}: a non-indicator node moved {sorted(moved)}")
        continue
    touched.add(px["code"])
    if moved - OK:
        bad.append(f"{i}: moved outside the tier keys {sorted(moved - OK)}")
if touched != THE_20:
    bad.append(f"the rows that moved are not the 20: extra {sorted(touched - THE_20)}, "
               f"untouched {sorted(THE_20 - touched)}")
# G1-D's surface level is the predecessor's fact and is not this task's to move.
g = bn["ind:G1-D"]["properties"]
if (g.get("measurement_level"), g.get("withdrawn_from")) != ("product", "host-level"):
    bad.append("G1-D's measurement_level or withdrawal moved")
# A tiered row carries no reason, an untiered row carries no tier, and the shopping list sits
# only on untiered rows: the record's own version of the suite's invariant.
for n in b["nodes"]:
    if "AssessmentIndicator" not in n["labels"]:
        continue
    p, c = n["properties"], n["properties"]["code"]
    tiered = bool(p.get("measurement_tier"))
    if tiered == bool(p.get("tier_unassigned_reason")):
        bad.append(f"{c}: tiered and unassigned, or neither")
    if p.get("open_tool_candidate") and tiered:
        bad.append(f"{c}: tiered and still on the shopping list")
    if tiered and BASIS_TIER.get(p.get("measurement_basis")) != p["measurement_tier"]:
        bad.append(f"{c}: basis {p.get('measurement_basis')!r} on tier "
                   f"{p['measurement_tier']!r}")
    # A field and a collector are the `structured_field` basis's evidence and go nowhere else.
    if bool(p.get("tier_field")) != (p.get("measurement_basis") == "structured_field"):
        bad.append(f"{c}: a field without the structured_field basis, or the reverse")
print("\n".join(f"FAIL {m}" for m in bad)
      or "   record: only tier keys, only on the 20 rows the predecessor left unassigned")
sys.exit(1 if bad else 0)
EOF
then fail=1; fi

# 4. The site's copy is the record, byte for byte.
if ! cmp -s framework/ai_readiness_framework.json docs/data/ai_readiness_framework.json; then
  echo "FAIL docs/data/ai_readiness_framework.json is not the record"; fail=1
fi

# 5. The manifest moved on digests and the build stamp alone.
x=$(git diff HEAD -U0 -- docs/data/index.json | grep -E '^[+-][^+-]' \
    | grep -vE '^[+-] *"(sha256|bytes|built_at|build_commit)": ')
[ -n "$x" ] && { echo "FAIL index.json moved outside digests and the build stamp:"; \
                 echo "$x" | cut -c1-160; fail=1; }

# 6. The tool map is what its generator produces, and the generator moved only in `verdict_for`.
if ! $PY scripts/scan_tool_map.py --check >/dev/null; then
  echo "FAIL docs/design/scan_tool_map.md is not its generator's output"; fail=1
fi
# The generator change is a pure INSERTION inside `verdict_for`: a branch ahead of the
# existing return, which stays. A removed line means something else moved with it.
x=$(git diff HEAD -U0 -- scripts/scan_tool_map.py | grep -cE '^-[^-]')
if [ "$x" != "0" ]; then
  echo "FAIL scripts/scan_tool_map.py removed $x line(s); the change only inserts a branch"
  fail=1
fi
if ! git diff HEAD -U0 -- scripts/scan_tool_map.py | grep -qE '^\+.*tier_collector'; then
  echo "FAIL the generator change is not the tier_collector branch"; fail=1
fi

# 7. Logs are append-only; the framework shard gains the one write-back event.
for f in events/ seldon_events.jsonl; do
  if git diff HEAD -- "$f" | grep -q '^-[^-]'; then
    echo "FAIL $f lost or changed a line; the log is append-only"; fail=1
  fi
done
# TWO write-back events, and the log keeps both: the first wrote decision 2's rows with basis
# `harness_leg` as the task file asked, the prescription layer's gates caught that the value
# means "a rule serves it", and the second re-based them to `structured_field` (ADDENDUM_02).
# A correction is a new event, never an edit (the event log's own rule).
added=$(git diff HEAD -U0 -- events/batch-033_framework.jsonl | grep -cE '^\+[^+]')
if [ "$added" != "2" ]; then
  echo "FAIL the framework shard gained $added line(s); this task appends exactly 2"
  fail=1
fi

if [ "$fail" -eq 0 ]; then echo "PROTECTED PATHS OK"; fi
exit "$fail"
