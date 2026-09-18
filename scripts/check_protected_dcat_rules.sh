#!/usr/bin/env bash
. "$(dirname "$0")/check_protected_lib.sh"
# The write set of `cc_tasks/2026-09-18_dcat_field_rules.md`, asserted against HEAD.
#
#   "`state/`, `corpus/`, `docs/reports/` byte-identical", and the write set the task file
#   lists: four rule modules, the registry, `rules.CURRENT`; fixtures and tests; the record
#   through the writer; `tag_prescriptions.py`, `tag_measurement_tiers.py`; the regenerated
#   tool map and site payloads; this script; `seldon_events.jsonl`; the RESULT.
#
# Paths that moved and the task file's write set does not name — each is reported in the
# RESULT §3 with the reason, and each is asserted below to have moved only as described:
#
#   * the harness beyond the rule modules. A rule is pure and cannot read a stored body, so the
#     fields must be on the Observation: `collectors/v2clauses.py` gains `dcat_record_fields`,
#     `runner.py` attaches it to D4's observation and returns [] for the four field legs,
#     `run.py` collects a leg that is both judged and consumed once, `params.yaml` gains the
#     `dcat_fields` block and a comment on `e5_control`, and `fixtures/passes_all/data.json`
#     carries the fields so the passing control can pass. `rules/_dcat_fields.py` is the four
#     rules' shared pure reader.
#   * the four `MeasurementSpec`s. `run.run_surface` judges a leg only when the record has a
#     spec for it, so without them cycle 5 would silently judge none of the four:
#     `scripts/build_measurement_specs.py` gains `--add-missing` and the four table rows.
#   * decision 6's D3 cell is AUTHORED by the skeleton, and `build_framework_graph.py` over HEAD
#     must stay a byte-for-byte no-op, so the correction is made in
#     `docs/crosswalk/usafacts_operationalization_skeleton.md` and regenerated.
#   * `--task` on four writers, so each write-back event names this task.
#   * three generated pages that read the moved counts: `docs/design/scoring_model.md`,
#     `docs/design/mcp_over_the_graph.md`, and the tool map's generator
#     (`scripts/scan_tool_map.py`, which now credits a leg with the collectors of the legs it
#     consumes).
#   * `scripts/exercise_dcat_field_rules.py`, decision 3's third leg, reproducible.
#   * seven tests whose literals this task moves, each with the reason beside the new value.
set -u
cd "$(dirname "$0")/.." || exit 2
fail=0
PY=/opt/anaconda3/bin/python3
TASK=cc_tasks/2026-09-18_dcat_field_rules.md

changed_and_new() {
  { git diff --name-only HEAD -- "$@"; git ls-files --others --exclude-standard -- "$@"; } \
    | sed '/^$/d' | sort -u
}

# 1. Untouched outright: the evidence, the corpus, the reports, the KG code, the controls.
for p in 'state/' 'corpus/' 'docs/reports/' 'docs/research/' 'kg/' 'LICENSE' 'LICENSE-DATA' \
         'controls.yaml' 'dixie_evidence.yaml' 'seldon.yaml' 'CITATION.cff' '.zenodo.json' \
         'docs/data/sources_per_check.json'; do
  moved=$(changed_and_new "$p")
  if [ -n "$moved" ]; then
    echo "FAIL protected path moved: $p"; echo "$moved" | sed 's/^/       /'; fail=1
  fi
done

# 2. Every path that moved is on the list.
ALLOWED=(
  'assessment/harness/scan/rules/__init__.py'
  'assessment/harness/scan/rules/_dcat_fields.py'
  'assessment/harness/scan/rules/rule_b1.py'
  'assessment/harness/scan/rules/rule_b4.py'
  'assessment/harness/scan/rules/rule_d3.py'
  'assessment/harness/scan/rules/rule_g4.py'
  'assessment/harness/scan/collectors/v2clauses.py'
  'assessment/harness/scan/runner.py'
  'assessment/harness/scan/run.py'
  'assessment/harness/scan/params.yaml'
  'assessment/harness/scan/fixtures/passes_all/data.json'
  'docs/crosswalk/usafacts_operationalization_skeleton.md'
  'framework/ai_readiness_framework.json'
  'events/batch-033_framework.jsonl'
  'seldon_events.jsonl'
  'scripts/tag_prescriptions.py'
  'scripts/tag_measurement_tiers.py'
  'scripts/build_framework_graph.py'
  'scripts/build_measurement_specs.py'
  'scripts/scan_tool_map.py'
  'scripts/exercise_dcat_field_rules.py'
  'scripts/check_protected_dcat_rules.sh'
  'tests/test_dcat_field_rules.py'
  'tests/test_framework_projection_roundtrip.py'
  'tests/test_framework_single_writer.py'
  'tests/test_mcp_server.py'
  'tests/test_measurement_tiers.py'
  'tests/test_prescriptions.py'
  'tests/test_rule_a12_v3.py'
  'tests/test_scan_harness.py'
  'tests/test_scan_harness_v3.py'
  'docs/design/scan_tool_map.md'
  'docs/design/scoring_model.md'
  'docs/design/mcp_over_the_graph.md'
  'docs/data/ai_readiness_framework.json'
  'docs/data/index.json'
  'cc_tasks/2026-09-18_dcat_field_rules_RESULT.md'
)
while read -r f; do
  [ -z "$f" ] && continue
  ok=0
  for a in "${ALLOWED[@]}"; do [ "$f" = "$a" ] && ok=1; done
  if [ "$ok" -eq 0 ]; then echo "FAIL moved outside the write set: $f"; fail=1; fi
done <<< "$(changed_and_new .)"

# 3. No shipped rule module moved: every Finding recorded under one must keep re-deriving from
#    its bytes. The package moved only in `__init__.py` (the generation) and the new files.
moved=$(git diff --name-only HEAD -- assessment/harness/scan/rules/ \
        | grep -v '^assessment/harness/scan/rules/__init__.py$')
if [ -n "$moved" ]; then echo "FAIL a shipped rule module moved: $moved"; fail=1; fi
# ... and `__init__.py` only GAINED lines, apart from the one GENERATIONS tuple it extends.
x=$(git diff HEAD -U0 -- assessment/harness/scan/rules/__init__.py | grep -E '^-[^-]' \
    | grep -v '^-GENERATIONS = (V1, V2, V3, V4, V5, V6, V7, V8, V9, V10)$')
[ -n "$x" ] && { echo "FAIL rules/__init__.py removed a line: $x"; fail=1; }
# The harness files beyond the rules only gained lines, except `run.py`'s one collect call,
# which moved under the new `if leg in shared` branch.
for f in assessment/harness/scan/collectors/v2clauses.py assessment/harness/scan/runner.py \
         assessment/harness/scan/params.yaml; do
  x=$(git diff HEAD -U0 -- "$f" | grep -E '^-[^-]' \
      | grep -vE '^-            except Exception:$|^-                continue$')
  [ -n "$x" ] && { echo "FAIL $f removed a line:"; echo "$x" | cut -c1-120; fail=1; }
done
x=$(git diff HEAD -U0 -- assessment/harness/scan/run.py | grep -cE '^-[^-]')
[ "$x" != "2" ] && { echo "FAIL run.py removed $x line(s); expected the 2 re-indented"; fail=1; }

# 4. The record: exactly the additions and moves this task makes.
git show HEAD:framework/ai_readiness_framework.json > /tmp/airkg_fw_head_dcat.json
if ! $PY - <<'EOF'
import json, sys
a = json.load(open("/tmp/airkg_fw_head_dcat.json"))
b = json.load(open("framework/ai_readiness_framework.json"))
bad = []
an, bn = {n["id"]: n for n in a["nodes"]}, {n["id"]: n for n in b["nodes"]}
if set(an) - set(bn):
    bad.append(f"nodes dropped {sorted(set(an) - set(bn))}")
added = set(bn) - set(an)
SPECS = {f"spec:{c}" for c in ("B1", "B4", "D3", "G4")}
acts = {i for i in added if i.startswith("act:")}
if added - acts != SPECS:
    bad.append(f"added nodes are not the four specs and the actions: {sorted(added - acts)}")
if len(acts) != 9 or not all(bn[i]["properties"]["leg"] in ("B1", "B4", "D3", "G4")
                             for i in acts):
    bad.append(f"expected 9 actions on the four legs, got {sorted(acts)}")
TIER = {"measurement_tier", "measurement_basis", "tier_source", "tier_rule", "tier_note",
        "tier_field", "tier_collector", "tier_unassigned_reason", "open_tool_candidate"}
MAY = {"ind:B1": TIER | {"measurement_status"}, "ind:B4": TIER | {"measurement_status"},
       "ind:G4": TIER | {"measurement_status"},
       "ind:D3": TIER | {"measurement_status", "gap", "evidence_raw"},
       "ind:E1": TIER, "ind:E3": TIER}
for i in an:
    px, py = an[i]["properties"], bn[i]["properties"]
    moved = {k for k in set(px) | set(py) if px.get(k) != py.get(k)}
    if an[i]["labels"] != bn[i]["labels"]:
        bad.append(f"{i}: labels moved")
    if moved and not moved <= MAY.get(i, set()):
        bad.append(f"{i}: moved {sorted(moved - MAY.get(i, set()))}")
for c in ("B1", "B4", "D3", "G4"):
    p = bn[f"ind:{c}"]["properties"]
    if (p.get("measurement_basis"), p.get("measurement_status")) != ("harness_leg",
                                                                     "harness_built"):
        bad.append(f"{c}: not harness_leg / harness_built")
    if f"RULE-{c}-v1" not in p.get("tier_source", ""):
        bad.append(f"{c}: tier_source does not cite RULE-{c}-v1")
    if bn[f"spec:{c}"]["properties"]["rule_id"] != f"RULE-{c}-v1":
        bad.append(f"spec:{c}: rule_id is not RULE-{c}-v1")
for c in ("E1", "E3"):
    p = bn[f"ind:{c}"]["properties"]
    if (p.get("measurement_tier"), p.get("measurement_basis")) != ("M", "judged_reading"):
        bad.append(f"{c}: not M / judged_reading")
if bn["ind:D3"]["properties"].get("gap") is not None:
    bad.append("ind:D3 still carries a gap cell")
key = lambda e: (e["from"], e["type"], e["to"])
ae, be = {key(e): e for e in a["edges"]}, {key(e): e for e in b["edges"]}
if set(ae) - set(be):
    bad.append(f"edges dropped {sorted(set(ae) - set(be))}")
if any(ae[k] != be[k] for k in ae if k in be):
    bad.append("an existing edge changed")
from collections import Counter
new = Counter(k[1] for k in set(be) - set(ae))
if new != Counter({"REMEDIATES": 9, "MEASURED_BY": 4, "EVIDENCED_BY": 2}):
    bad.append(f"edges added {dict(new)}")
if {k for k in set(be) - set(ae) if k[1] == "EVIDENCED_BY"} != {
        ("ind:D3", "EVIDENCED_BY", "doc:w3c-prov-dm-data-model"),
        ("ind:D3", "EVIDENCED_BY", "doc:w3c-prov-o-ontology")}:
    bad.append("the EVIDENCED_BY edges added are not D3's two PROV documents")
WANT = {"evidenced_by": (139, 141), "gaps": (14, 13), "measurement_specs": (22, 26),
        "rules_built": (17, 21), "actions": (42, 51)}
ca, cb = a["counts"], b["counts"]
if set(ca) != set(cb):
    bad.append("a counts key was added or dropped")
got = {k: (ca[k], cb[k]) for k in ca if ca[k] != cb.get(k)}
if got != WANT:
    bad.append(f"counts moved {got}, expected {WANT}")
for k in set(a) - {"nodes", "edges", "counts"}:
    if a[k] != b.get(k):
        bad.append(f"top-level {k!r} moved")
print("\n".join(f"FAIL {m}" for m in bad)
      or "   record: 4 specs, 9 actions, 15 edges, B1/B4/D3/G4 to harness_leg, E1/E3 tiered, "
         "D3's gap corrected")
sys.exit(1 if bad else 0)
EOF
then fail=1; fi

# 5. The site's copy is the record, byte for byte; the manifest moved on digests alone.
if ! cmp -s framework/ai_readiness_framework.json docs/data/ai_readiness_framework.json; then
  echo "FAIL docs/data/ai_readiness_framework.json is not the record"; fail=1
fi
x=$(git diff HEAD -U0 -- docs/data/index.json | grep -E '^[+-][^+-]' \
    | grep -vE '^[+-] *"(sha256|bytes|built_at|build_commit)": ')
[ -n "$x" ] && { echo "FAIL index.json moved outside digests and the build stamp:"; \
                 echo "$x" | cut -c1-160; fail=1; }

# 6. Every generated page is its generator's output, and every writer is a no-op over HEAD+1.
$PY scripts/scan_tool_map.py --check >/dev/null || { echo "FAIL tool map drift"; fail=1; }
$PY scripts/score.py --check >/dev/null || { echo "FAIL scoring_model.md drift"; fail=1; }
$PY mcp/airkg_doc.py --check >/dev/null 2>&1 || { echo "FAIL mcp page drift"; fail=1; }
$PY scripts/build_framework_graph.py --dry-run 2>/dev/null | grep -q '"unchanged": true' \
  || { echo "FAIL build_framework_graph is not a no-op over the record"; fail=1; }
$PY scripts/tag_prescriptions.py --dry-run 2>/dev/null | grep -q '"unchanged": true' \
  || { echo "FAIL tag_prescriptions is not a no-op over the record"; fail=1; }
$PY scripts/framework_writeback_rules.py --dry-run 2>&1 | grep -q '"unchanged": true' \
  || { echo "FAIL framework_writeback_rules is not a no-op over the record"; fail=1; }

# 7. Logs are append-only; the framework shard gains this task's five write-back events, each
#    naming this task.
for f in events/ seldon_events.jsonl; do
  if git diff HEAD -- "$f" | grep -q '^-[^-]'; then
    echo "FAIL $f lost or changed a line; the log is append-only"; fail=1
  fi
done
added=$(git diff HEAD -U0 -- events/batch-033_framework.jsonl | grep -E '^\+[^+]')
n=$(printf '%s\n' "$added" | sed '/^$/d' | wc -l | tr -d ' ')
if [ "$n" != "5" ]; then
  echo "FAIL the framework shard gained $n line(s); this task appends exactly 5"; fail=1
fi
if [ "$(printf '%s\n' "$added" | grep -c "\"task\": \"$TASK\"")" != "5" ]; then
  echo "FAIL a write-back event on the shard does not name $TASK"; fail=1
fi

if [ "$fail" -eq 0 ]; then echo "PROTECTED PATHS OK"; fi
exit "$fail"
