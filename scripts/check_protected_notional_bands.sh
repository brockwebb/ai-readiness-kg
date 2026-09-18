#!/usr/bin/env bash
. "$(dirname "$0")/check_protected_lib.sh"
# The write set of `cc_tasks/2026-09-17_notional_bands.md`, asserted against HEAD.
#
#   "Nothing else moves. No new actions, no rule, no matrix, no report" (decision 6), and the
#   write set the task file lists. `docs/` is byte-identical apart from the DN-005 addendum
#   decision 5 orders and the two published payloads a record write-back always makes stale.
#
# One path moved beyond the task file's list, and the RESULT reports it as a premise:
#
#   * kg/schema.yaml — the single type catalogue (invariant 4). Its `Action` entry states in
#     prose that the bands are EMPTY and their source reads `estimate:pending`; after this task
#     that sentence is false, and two properties (`technique_class`, `band_note`) exist on 45
#     nodes that the catalogue does not list. A catalogue that describes the record it no
#     longer matches is worse than one that is silent.
set -u
cd "$(dirname "$0")/.." || exit 2
fail=0
PY=/opt/anaconda3/bin/python3
ADDENDUM=docs/design/2026-09-15_DN-005_reorientation_the_framework_is_the_goal_ADDENDUM_03.md

changed_and_new() {
  { git diff --name-only HEAD -- "$@"; git ls-files --others --exclude-standard -- "$@"; } \
    | sed '/^$/d' | sort -u
}

# 1. Untouched outright: the evidence, the corpus, the harness, the controls, the reports.
#    `docs/design/` is NOT asserted empty here — decision 5 puts the addendum in it — and
#    section 2's allow-list holds it to that one file.
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
  'scripts/tag_prescriptions.py'
  'scripts/prescriptions.py'
  'scripts/check_protected_notional_bands.sh'
  'tests/test_prescriptions.py'
  "$ADDENDUM"
  'docs/data/ai_readiness_framework.json'
  'docs/data/index.json'
  'docs/data/CITATION.cff'
  'docs/data/zenodo.json'
  'CITATION.cff'
  '.zenodo.json'
  'cc_tasks/2026-09-17_notional_bands_RESULT.md'
)
while read -r f; do
  [ -z "$f" ] && continue
  ok=0
  for a in "${ALLOWED[@]}"; do [ "$f" = "$a" ] && ok=1; done
  if [ "$ok" -eq 0 ]; then echo "FAIL moved outside the write set: $f"; fail=1; fi
done <<< "$(changed_and_new .)"

# 3. The record: 45 Action nodes changed in the four band fields and the two new ones, and
#    NOTHING else — no node added or dropped, no edge touched, no counts key moved. The class
#    table is re-derived here from the task file's own decision 2 rather than imported from the
#    tagger, so a band edited in the tagger fails this check instead of validating itself.
git show HEAD:framework/ai_readiness_framework.json > /tmp/airkg_fw_head_bands.json
if ! $PY - <<'EOF'
import json, sys
a = json.load(open("/tmp/airkg_fw_head_bands.json"))
b = json.load(open("framework/ai_readiness_framework.json"))
BANDS = {"edit_existing": ("hours", "none"),
         "publish_new_file": ("days", "staff_time"),
         "change_server_behaviour": ("weeks", "staff_time"),
         "expose_api": ("quarter", "procurement"),
         "harness_side": ("hours", "none")}
MARKER = "notional:technique_class:{}, task 2026-09-17_notional_bands"
MAY_CHANGE = {"effort_band", "effort_source", "cost_band", "cost_source"}
MAY_APPEAR = {"technique_class", "band_note", "technique_class_reason"}
bad = []
SKIP = ("nodes", "edges")
if {k: v for k, v in a.items() if k not in SKIP} != {k: v for k, v in b.items() if k not in SKIP}:
    bad.append("counts, counts_basis or another top-level field moved; this task moves none")
an, bn = {n["id"]: n for n in a["nodes"]}, {n["id"]: n for n in b["nodes"]}
if set(an) != set(bn):
    bad.append(f"the node set moved: +{sorted(set(bn)-set(an))[:6]} -{sorted(set(an)-set(bn))[:6]}")
if a["edges"] != b["edges"]:
    bad.append("an edge moved; this task writes no edge")
changed = []
for i in sorted(set(an) & set(bn)):
    if an[i] == bn[i]:
        continue
    changed.append(i)
    if bn[i]["labels"] != ["Action"]:
        bad.append(f"{i}: a node that is not an Action changed")
        continue
    ap_, bp = an[i]["properties"], bn[i]["properties"]
    appeared = set(bp) - set(ap_)
    if set(ap_) - set(bp):
        bad.append(f"{i}: lost propertie(s) {sorted(set(ap_) - set(bp))}")
    if appeared - MAY_APPEAR:
        bad.append(f"{i}: unexpected new propertie(s) {sorted(appeared - MAY_APPEAR)}")
    moved = {k for k in set(ap_) & set(bp) if ap_[k] != bp[k]}
    if moved - MAY_CHANGE:
        bad.append(f"{i}: propertie(s) outside the bands moved: {sorted(moved - MAY_CHANGE)}")
    cls = bp.get("technique_class")
    if cls not in BANDS:
        bad.append(f"{i}: technique_class {cls!r} is not one of the five")
        continue
    if (bp["effort_band"], bp["cost_band"]) != BANDS[cls]:
        bad.append(f"{i}: {cls} bands are {(bp['effort_band'], bp['cost_band'])}, "
                   f"not {BANDS[cls]}")
    for k in ("effort_source", "cost_source"):
        if bp[k] != MARKER.format(cls):
            bad.append(f"{i}.{k} is {bp[k]!r}, not the marker for {cls}")
if len(changed) != 45:
    bad.append(f"{len(changed)} node(s) changed; the layer is 45 actions")
notes = {n["properties"].get("band_note") for n in bn.values() if n["labels"] == ["Action"]}
if len(notes) != 1 or not (notes and next(iter(notes), "").startswith("Notional relative")):
    bad.append(f"the band_note is not one verbatim sentence on all 45: {len(notes)} distinct")
if "estimate:pending" in json.dumps(b):
    bad.append("`estimate:pending` still appears in the record")
print("\n".join(f"FAIL {m}" for m in bad)
      or "   record: 45 Action nodes took a class and two notional bands; nothing else moved")
sys.exit(1 if bad else 0)
EOF
then fail=1; fi

# 4. The catalogue moved only in its `Action` entry, and the literal is gone from the code.
if ! $PY - <<'EOF'
import subprocess, sys, yaml
head = yaml.safe_load(subprocess.run(["git", "show", "HEAD:kg/schema.yaml"],
                                     capture_output=True, text=True, check=True).stdout)
now = yaml.safe_load(open("kg/schema.yaml"))
bad = []
for d in (head, now):
    d["assessment_layer"]["node_types"].pop("Action", None)
if head != now:
    bad.append("kg/schema.yaml moved outside its `Action` entry")
for rel in ("scripts/tag_prescriptions.py", "scripts/prescriptions.py", "kg/schema.yaml"):
    if "estimate:pending" in open(rel).read():
        bad.append(f"`estimate:pending` still appears in {rel}")
print("\n".join(f"FAIL {m}" for m in bad) or "   catalogue: only the Action entry moved")
sys.exit(1 if bad else 0)
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

# 7. The generator over the new record is still a byte-for-byte no-op, and the table still
#    validates against the rules, the sources, the classes and the record.
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

if ! $PY scripts/tag_prescriptions.py --check > /dev/null; then
  echo "FAIL the prescription table no longer validates"; fail=1
fi

# 8. The addendum exists, is the third, and says what it amends.
if [ ! -f "$ADDENDUM" ]; then
  echo "FAIL the DN-005 addendum decision 5 orders is not on disk"; fail=1
else
  for s in 'ADDENDUM_03' 'Amends' 'notional' 'technique class' 'Flyvbjerg'; do
    grep -qi -- "$s" "$ADDENDUM" || { echo "FAIL the addendum does not mention: $s"; fail=1; }
  done
fi

# 9. Logs are append-only; the framework shard gains the one write-back event.
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
