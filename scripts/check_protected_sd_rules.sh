#!/usr/bin/env bash
# The write set of `cc_tasks/2026-09-18_schema_field_rules.md`, asserted against HEAD.
#
#   "`state/`, `corpus/`, `docs/reports/` byte-identical", and the write set the task file
#   lists: three (or four) rule modules, the registry, `rules.CURRENT`; fixtures and tests; the
#   record through the writer; the taggers; the regenerated tool map and site payloads; this
#   script; `seldon_events.jsonl`; the RESULT.
#
# Paths that moved and the task file's write set does not name — each is reported in the
# RESULT §3 with the reason, and each is asserted below to have moved only as described:
#
#   * the harness beyond the rule modules. B5 is judged per BODY (decision 5), which no rule
#     before it was: `run.py` gains `judge_bodies` and keeps body legs out of every per-surface
#     list, `rederive.py` re-derives and re-judges them over the same `rules.body_groups`.
#     D2's directive is not parsed by `protego`, so `collectors/v2clauses.py` gains
#     `content_signals` and `runner.py` attaches it to A4's observation and returns [] for the
#     legs that read other legs' observations. `params.yaml` gains three blocks and the
#     control-table derivation. `rules/_schema_terms.py` is the schema.org rules' pure reader.
#   * four control-fixture files: `passes_all`'s page gains a `variableMeasured` whose
#     `measurementTechnique` is a complete `DefinedTerm`, and four robots.txt files a
#     `Content-Signal` line, so the passing controls can pass the new legs.
#   * the three `MeasurementSpec`s, and `spec:B1`'s authored fields, through
#     `scripts/build_measurement_specs.py` (`--refresh`, new) — without a spec a leg is not
#     judged by `run.run_surface` or `run.judge_bodies`.
#   * `scripts/framework_writeback_rules.py` ran and moved B2, B5 and D2 to `harness_built`.
#   * two generated pages that read the moved counts: `docs/design/scoring_model.md` and
#     `docs/design/mcp_over_the_graph.md`.
#   * `scripts/exercise_schema_field_rules.py`, the third leg of decision 3, reproducible.
#   * tests whose literals this task moves, each with the reason beside the new value.
set -u
cd "$(dirname "$0")/.." || exit 2
fail=0
PY=/opt/anaconda3/bin/python3
TASK=cc_tasks/2026-09-18_schema_field_rules.md

changed_and_new() {
  { git diff --name-only HEAD -- "$@"; git ls-files --others --exclude-standard -- "$@"; } \
    | sed '/^$/d' | sort -u
}

# 1. Untouched outright: the evidence, the corpus, the reports, the KG code, the controls.
for p in 'state/' 'corpus/' 'docs/reports/' 'docs/research/' 'kg/' 'LICENSE' 'LICENSE-DATA' \
         'controls.yaml' 'dixie_evidence.yaml' 'seldon.yaml' 'CITATION.cff' '.zenodo.json' \
         'docs/data/sources_per_check.json' 'docs/crosswalk/'; do
  moved=$(changed_and_new "$p")
  if [ -n "$moved" ]; then
    echo "FAIL protected path moved: $p"; echo "$moved" | sed 's/^/       /'; fail=1
  fi
done

# 2. Every path that moved is on the list.
ALLOWED=(
  'assessment/harness/scan/rules/__init__.py'
  'assessment/harness/scan/rules/_schema_terms.py'
  'assessment/harness/scan/rules/rule_b1_v2.py'
  'assessment/harness/scan/rules/rule_b2.py'
  'assessment/harness/scan/rules/rule_b5.py'
  'assessment/harness/scan/rules/rule_d2.py'
  'assessment/harness/scan/collectors/v2clauses.py'
  'assessment/harness/scan/runner.py'
  'assessment/harness/scan/run.py'
  'assessment/harness/scan/rederive.py'
  'assessment/harness/scan/params.yaml'
  'assessment/harness/scan/fixtures/passes_all/index.html'
  'assessment/harness/scan/fixtures/passes_all/robots.txt'
  'assessment/harness/scan/fixtures/refuses_identified_client/robots.txt'
  'assessment/harness/scan/fixtures/robots_forbids_product/robots.txt'
  'assessment/harness/scan/fixtures/sitemap_on_sibling/robots.txt'
  'framework/ai_readiness_framework.json'
  'events/batch-033_framework.jsonl'
  'seldon_events.jsonl'
  'scripts/tag_prescriptions.py'
  'scripts/tag_measurement_tiers.py'
  'scripts/build_measurement_specs.py'
  'scripts/exercise_schema_field_rules.py'
  'scripts/exercise_dcat_field_rules.py'
  'scripts/check_protected_sd_rules.sh'
  'tests/test_schema_field_rules.py'
  'tests/test_framework_projection_roundtrip.py'
  'tests/test_framework_single_writer.py'
  'tests/test_mcp_server.py'
  'tests/test_measurement_tiers.py'
  'tests/test_prescriptions.py'
  'tests/test_invariants.py'
  'tests/test_scan_harness.py'
  'tests/test_scan_harness_v3.py'
  'tests/test_dcat_field_rules.py'
  'tests/test_rule_a12_v3.py'
  'tests/test_scoring_model.py'
  'docs/design/scan_tool_map.md'
  'docs/design/scoring_model.md'
  'docs/design/mcp_over_the_graph.md'
  'docs/data/ai_readiness_framework.json'
  'docs/data/index.json'
  'cc_tasks/2026-09-18_schema_field_rules_RESULT.md'
)
while read -r f; do
  [ -z "$f" ] && continue
  ok=0
  for a in "${ALLOWED[@]}"; do [ "$f" = "$a" ] && ok=1; done
  if [ "$ok" -eq 0 ]; then echo "FAIL moved outside the write set: $f"; fail=1; fi
done <<< "$(changed_and_new .)"

# 3. No shipped rule module moved: every Finding recorded under one must keep re-deriving from
#    its bytes. `RULE-B1-v1` in particular is superseded, not edited.
moved=$(git diff --name-only HEAD -- assessment/harness/scan/rules/ \
        | grep -v '^assessment/harness/scan/rules/__init__.py$')
if [ -n "$moved" ]; then echo "FAIL a shipped rule module moved: $moved"; fail=1; fi
# ... and `__init__.py` only GAINED lines, apart from the one GENERATIONS tuple it extends.
x=$(git diff HEAD -U0 -- assessment/harness/scan/rules/__init__.py | grep -E '^-[^-]' \
    | grep -v '^-GENERATIONS = (V1, V2, V3, V4, V5, V6, V7, V8, V9, V10, V11)$')
[ -n "$x" ] && { echo "FAIL rules/__init__.py removed a line: $x"; fail=1; }
# The collector and params only gained lines; the runner's A4 branch replaced its one return.
for f in assessment/harness/scan/collectors/v2clauses.py assessment/harness/scan/params.yaml; do
  x=$(git diff HEAD -U0 -- "$f" | grep -E '^-[^-]')
  [ -n "$x" ] && { echo "FAIL $f removed a line:"; echo "$x" | cut -c1-120; fail=1; }
done
x=$(git diff HEAD -U0 -- assessment/harness/scan/runner.py | grep -E '^-[^-]' \
    | grep -v '^-        return robots.fetch(f, leg, doc_id, url, params)$')
[ -n "$x" ] && { echo "FAIL runner.py removed a line: $x"; fail=1; }
# Fixtures only gained lines, except the one JSON-LD line the page's new property follows.
for f in $(git diff --name-only HEAD -- assessment/harness/scan/fixtures/); do
  x=$(git diff HEAD -U0 -- "$f" | grep -E '^-[^-]' \
      | grep -v '^-   "contentUrl":"http://HOSTPORT/estimates.csv"}\]}$')
  [ -n "$x" ] && { echo "FAIL fixture $f removed a line: $x"; fail=1; }
done

# 4. The record: exactly the additions and moves this task makes.
git show HEAD:framework/ai_readiness_framework.json > /tmp/airkg_fw_head_sd.json
if ! $PY - <<'EOF'
import json, sys
a = json.load(open("/tmp/airkg_fw_head_sd.json"))
b = json.load(open("framework/ai_readiness_framework.json"))
bad = []
an, bn = {n["id"]: n for n in a["nodes"]}, {n["id"]: n for n in b["nodes"]}
if set(an) - set(bn):
    bad.append(f"nodes dropped {sorted(set(an) - set(bn))}")
added = set(bn) - set(an)
SPECS = {f"spec:{c}" for c in ("B2", "B5", "D2")}
acts = {i for i in added if i.startswith("act:")}
if added - acts != SPECS:
    bad.append(f"added nodes are not the three specs and the actions: {sorted(added - acts)}")
if len(acts) != 9 or not all(bn[i]["properties"]["leg"] in ("B1", "B2", "B5", "D2")
                             for i in acts):
    bad.append(f"expected 9 actions on B1, B2, B5, D2, got {sorted(acts)}")
TIER = {"measurement_tier", "measurement_basis", "tier_source", "tier_rule", "tier_note",
        "tier_field", "tier_collector"}
SPEC_AUTHORED = {"signal", "collector", "collector_pin", "evidence_kind", "prior_art", "note",
                 "rule_id"}
MAY = {"ind:B1": {"tier_source", "tier_note"}, "spec:B1": SPEC_AUTHORED,
       "ind:B2": TIER | {"measurement_status"}, "ind:B5": TIER | {"measurement_status"},
       "ind:D2": TIER | {"measurement_status"},
       # B1's two generation-11 actions now verify by `RULE-B1-v2`, and their per-leg caveat
       # counts three failing outcomes instead of two. Nothing else on them moves.
       "act:b1-publish-the-products-record-with-its-data-dictionary": {"value", "verifies_by"},
       "act:b1-link-the-data-dictionary-from-the-catalog-record": {"value", "verifies_by"}}
for i in an:
    px, py = an[i]["properties"], bn[i]["properties"]
    moved = {k for k in set(px) | set(py) if px.get(k) != py.get(k)}
    if an[i]["labels"] != bn[i]["labels"]:
        bad.append(f"{i}: labels moved")
    if moved and not moved <= MAY.get(i, set()):
        bad.append(f"{i}: moved {sorted(moved - MAY.get(i, set()))}")
RULES = {"B1": "RULE-B1-v2", "B2": "RULE-B2-v1", "B5": "RULE-B5-v1", "D2": "RULE-D2-v1"}
for c, rid in RULES.items():
    p = bn[f"ind:{c}"]["properties"]
    if (p.get("measurement_basis"), p.get("measurement_status")) != ("harness_leg",
                                                                     "harness_built"):
        bad.append(f"{c}: not harness_leg / harness_built")
    if rid not in p.get("tier_source", ""):
        bad.append(f"{c}: tier_source does not cite {rid}")
    if "tier_field" in p or "tier_collector" in p:
        bad.append(f"{c}: still carries a structured_field locator")
    if bn[f"spec:{c}"]["properties"]["rule_id"] != rid:
        bad.append(f"spec:{c}: rule_id is not {rid}")
if "unmeasured_until: second cycle with term codes" not in bn["ind:B5"]["properties"]["tier_note"]:
    bad.append("ind:B5's tier_note does not declare the cross-vintage clause unmeasured_until")
left = sorted(n["properties"]["code"] for n in b["nodes"] if "AssessmentIndicator" in n["labels"]
              and n["properties"].get("measurement_basis") == "structured_field")
if left:
    bad.append(f"structured_field rows remain: {left}")
key = lambda e: (e["from"], e["type"], e["to"])
ae, be = {key(e): e for e in a["edges"]}, {key(e): e for e in b["edges"]}
if set(ae) - set(be):
    bad.append(f"edges dropped {sorted(set(ae) - set(be))}")
B1_EDGES = {("act:b1-publish-the-products-record-with-its-data-dictionary", "REMEDIATES", "ind:B1"),
            ("act:b1-link-the-data-dictionary-from-the-catalog-record", "REMEDIATES", "ind:B1")}
for k in ae:
    if k not in be or ae[k] == be[k]:
        continue
    pa, pb = ae[k].get("properties") or {}, be[k].get("properties") or {}
    moved = {x for x in set(pa) | set(pb) if pa.get(x) != pb.get(x)}
    if k not in B1_EDGES or moved != {"rule_id"} or pb["rule_id"] != "RULE-B1-v2":
        bad.append(f"an existing edge changed: {k} {sorted(moved)}")
from collections import Counter
new = Counter(k[1] for k in set(be) - set(ae))
if new != Counter({"REMEDIATES": 9, "MEASURED_BY": 3}):
    bad.append(f"edges added {dict(new)}")
WANT = {"measurement_specs": (26, 29), "rules_built": (21, 24), "actions": (51, 60)}
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
      or "   record: 3 specs, 9 actions, 12 edges, B2/B5/D2 to harness_leg, B1 on v2, "
         "0 structured_field")
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
$PY scripts/build_measurement_specs.py --add-missing --refresh B1 --dry-run 2>&1 \
  | grep -q '"unchanged": true' \
  || { echo "FAIL build_measurement_specs --add-missing --refresh B1 is not a no-op"; fail=1; }

# 7. Logs are append-only; the framework shard gains this task's four write-back events, each
#    naming this task.
for f in events/ seldon_events.jsonl; do
  if git diff HEAD -- "$f" | grep -q '^-[^-]'; then
    echo "FAIL $f lost or changed a line; the log is append-only"; fail=1
  fi
done
added=$(git diff HEAD -U0 -- events/batch-033_framework.jsonl | grep -E '^\+[^+]')
n=$(printf '%s\n' "$added" | sed '/^$/d' | wc -l | tr -d ' ')
if [ "$n" != "4" ]; then
  echo "FAIL the framework shard gained $n line(s); this task appends exactly 4"; fail=1
fi
if [ "$(printf '%s\n' "$added" | grep -c "\"task\": \"$TASK\"")" != "4" ]; then
  echo "FAIL a write-back event on the shard does not name $TASK"; fail=1
fi

if [ "$fail" -eq 0 ]; then echo "PROTECTED PATHS OK"; fi
exit "$fail"
