#!/usr/bin/env bash
# The zero-edits list of `cc_tasks/2026-09-12_a1_a8_b3_d4_sources.md`, asserted against HEAD:
#
#   "Zero edits to: rule modules, harness, payloads, prior Results, prior RESULTs, figures,
#    existing Document nodes, section prose, the record beyond the four evidence cells (and
#    A10's cell untouched)."
#
# Two clauses are not a path list and are checked as themselves, below: the record may move
# ONLY at the four indicators, and the skeleton may move ONLY on the four rows. `corpus/` is
# protected WHOLE, which is how the "at most the one acquisition under decision 4" clause is
# asserted: decision 4 resolved to "not acquired" (DCAT-US states the Public Data Listing
# requirement on its face), so the corpus must be byte-identical and no host was contacted.
set -u
cd "$(dirname "$0")/.." || exit 2
PY=/opt/anaconda3/bin/python3
fail=0

protected=(
  'assessment/'
  'state/'
  'corpus/'
  'docs/reports/sections/'
  'docs/reports/generated/matrix_tierA.md'
  'docs/reports/generated/matrix_tierC.md'
  'docs/reports/generated/matrix_product.md'
  'docs/reports/generated/rules_by_leg.md'
  'docs/reports/generated/requests_per_netloc.md'
  'docs/reports/scan_matrix_product_2026-09-10_rj2.csv'
  'docs/reports/scan_matrix_tierA_2026-09-10_rj2.csv'
  'docs/reports/scan_matrix_tierC_2026-09-10_rj2.csv'
  'tests/test_invariants.py'
)

for p in "${protected[@]}"; do
  changed=$(git diff --name-only HEAD -- "$p"; git ls-files --others --exclude-standard -- "$p")
  if [ -n "$changed" ]; then
    echo "FAIL protected path moved: $p"
    echo "$changed" | sed 's/^/       /'
    fail=1
  fi
done

prior=$(git diff --name-only HEAD -- 'cc_tasks/*_RESULT.md')
if [ -n "$prior" ]; then
  echo "FAIL a prior RESULT changed:"; echo "$prior" | sed 's/^/       /'; fail=1
fi

# Events: the ONE shard this task may append to is the tagged framework shard, and it may only
# have grown. Everything else under events/ is byte-identical.
ev=$(git diff --name-only HEAD -- 'events/' | grep -v '^events/batch-033_framework.jsonl$' || true)
if [ -n "$ev" ]; then
  echo "FAIL an event shard other than batch-033_framework.jsonl changed:"
  echo "$ev" | sed 's/^/       /'; fail=1
fi
if git diff HEAD -- events/batch-033_framework.jsonl | grep -q '^-[^-]'; then
  echo "FAIL events/batch-033_framework.jsonl lost a line; the log is append-only"; fail=1
fi

# The skeleton: only the four rows, and only their Evidence cell. A10's row is named in the
# task's zero-edits list and is covered by this because it is not one of the four.
"$PY" - <<'PYEOF' || fail=1
import subprocess, sys, re
CODES = {"A1", "A8", "B3", "D4"}
head = subprocess.run(
    ["git", "show", "HEAD:docs/crosswalk/usafacts_operationalization_skeleton.md"],
    capture_output=True, text=True, check=True).stdout.split("\n")
now = open("docs/crosswalk/usafacts_operationalization_skeleton.md",
           encoding="utf-8").read().split("\n")
bad = []
if len(head) != len(now):
    bad.append(f"line count moved {len(head)} -> {len(now)}")
for a, b in zip(head, now):
    if a == b:
        continue
    m = re.match(r"^\|\s*([A-G]\d{1,2})\s*\|", a)
    if not m or m.group(1) not in CODES:
        bad.append(f"a line outside the four rows changed: {a[:90]}")
        continue
    pa, pb = a.split("|"), b.split("|")
    if len(pa) != len(pb) or any(x != y for i, (x, y) in enumerate(zip(pa, pb)) if i != 5):
        bad.append(f"{m.group(1)}: a cell other than Evidence changed")
for x in bad:
    print(f"FAIL skeleton: {x}")
sys.exit(1 if bad else 0)
PYEOF

# The record: only the four indicator nodes moved, and nothing was removed.
"$PY" - <<'PYEOF' || fail=1
import subprocess, json, sys
CODES = {"A1", "A8", "B3", "D4"}
head = json.loads(subprocess.run(
    ["git", "show", "HEAD:framework/ai_readiness_framework.json"],
    capture_output=True, text=True, check=True).stdout)
now = json.load(open("framework/ai_readiness_framework.json", encoding="utf-8"))
ids = {c: f"ind:{c}" for c in CODES}
bad = []
hn = {n["id"]: n for n in head["nodes"]}
nn = {n["id"]: n for n in now["nodes"]}
if set(hn) != set(nn):
    bad.append(f"node set moved: -{sorted(set(hn)-set(nn))} +{sorted(set(nn)-set(hn))}")
for i in set(hn) & set(nn):
    if hn[i] != nn[i] and i not in ids.values():
        bad.append(f"a node outside the four indicators changed: {i}")
def key(e):
    return (e["from"], e["type"], e["to"])
he, ne = {key(e) for e in head["edges"]}, {key(e) for e in now["edges"]}
for e in sorted(he - ne):
    bad.append(f"an edge was REMOVED: {e}")
for e in sorted(ne - he):
    if e[0] not in ids.values():
        bad.append(f"an edge was added outside the four indicators: {e}")
for k in head["counts"]:
    if k not in now["counts"]:
        bad.append(f"a counts key was dropped: {k}")
for x in bad:
    print(f"FAIL record: {x}")
sys.exit(1 if bad else 0)
PYEOF

# **Existing Document nodes.** Nothing here writes one: corpus/ is protected whole above, so no
# manifest entry moved, and the framework loader only ever MATCHes a Document to hang an edge
# on. Asserted on the loader's source, because the graph holds no "before" to diff against.
if grep -nE '(SET|MERGE|CREATE)[^"]*:Document' scripts/load_framework_graph.py \
     | grep -v 'MATCH (d:Document' ; then
  echo "FAIL scripts/load_framework_graph.py writes to a Document node"; fail=1
fi

if [ "$fail" -eq 0 ]; then
  echo "PASS  corpus/, harness, payloads, figures, section prose and every prior RESULT are"
  echo "      byte-identical to HEAD; the skeleton moved only on the four Evidence cells; the"
  echo "      record moved only at ind:A1, ind:A8, ind:B3, ind:D4 with nothing removed; no"
  echo "      Document node is written"
fi

echo
echo "what DID change:"
{ git diff --name-only HEAD; git ls-files --others --exclude-standard; } | sort -u | sed 's/^/       /'
exit "$fail"
