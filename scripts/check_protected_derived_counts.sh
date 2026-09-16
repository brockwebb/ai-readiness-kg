#!/bin/sh
# The protected-paths diff for cc_tasks/2026-09-15_derived_counts_and_appendix_guard.md.
#
# The task judges nothing and measures nothing: no rule runs, no host is contacted, no payload
# under state/ is written and no Observation or Finding is minted. What it DOES write that its
# "Zero edits to" list did not anticipate is one line on the framework shard of the event log —
# decision 4 has the appendix row read `withdrawn_from` off the framework record's indicator
# node, the node carried no such property, and `framework_writeback.save` is the only writer
# and cannot write without its event. So `events/` is not asserted empty here; it is asserted
# to have moved by EXACTLY one appended `framework_writeback` line on exactly that shard, with
# nothing removed. That is a narrower claim than "nothing moved" and a checkable one.
#
# The status prefix is stripped before matching, so the check answers the same before and after
# `git add`.
cd /Users/brock/GitHub/ai-readiness-kg || exit 2
echo "=== protected paths"
fail=0

say() { echo; echo "-- $1"; }
must_be_empty() {
  label="$1"; shift
  out=$(git status --porcelain -- "$@")
  [ -n "$out" ] && { echo "$out"; echo "   VIOLATION: $label"; fail=1; }
}

say "STORED PAYLOADS — this task measures nothing and judges nothing"
must_be_empty "a stored payload changed" state/

say "THE MEASUREMENT TREE — no rule, no harness, no schema, no corpus, no control"
must_be_empty "the rules or harness changed" assessment/
must_be_empty "kg/ changed" kg/
must_be_empty "corpus changed" corpus/
must_be_empty "controls or the identity gate changed" controls.yaml dixie_evidence.yaml

say "THE REPORT, its inputs and its declaration — the site is a VIEW of these, never a source"
must_be_empty "the report source or a section changed" docs/reports/2026-09_fss_ai_readiness_L0.md \
  docs/reports/sections/ docs/reports/generated/
must_be_empty "the declaration changed" docs/reports/publication.yaml
must_be_empty "a matrix changed" docs/reports/scan_matrix_tierA_2026-09-10_rj2.json \
  docs/reports/scan_matrix_tierA_2026-09-10_rj2.csv \
  docs/reports/scan_matrix_tierC_2026-09-10_rj2.json \
  docs/reports/scan_matrix_tierC_2026-09-10_rj2.csv \
  docs/reports/scan_matrix_product_2026-09-10_rj2.json \
  docs/reports/scan_matrix_product_2026-09-10_rj2.csv
must_be_empty "the PDF changed" docs/reports/2026-09_fss_ai_readiness_L0.pdf

say "DESIGN DECISIONS — this task takes none that are not already on the record"
must_be_empty "a design decision or design note changed" docs/design_decisions.md docs/design/ \
  docs/schema_v0.1.md CLAUDE.md

say "THE EVENT LOG — one appended framework_writeback, on the framework shard, nothing removed"
shards=$(git status --porcelain -- events/ | sed 's/^...//')
if [ "$shards" != "events/batch-033_framework.jsonl" ]; then
  echo "$shards"; echo "   VIOLATION: a shard other than events/batch-033_framework.jsonl moved"
  fail=1
else
  added=$(git diff -U0 -- events/batch-033_framework.jsonl | grep -c '^+[^+]')
  removed=$(git diff -U0 -- events/batch-033_framework.jsonl | grep -c '^-[^-]')
  echo "   +$added / -$removed line(s) on events/batch-033_framework.jsonl"
  [ "$added" = "1" ] || { echo "   VIOLATION: not exactly one appended event"; fail=1; }
  [ "$removed" = "0" ] || { echo "   VIOLATION: an event line was edited or deleted (invariant 1)"; fail=1; }
  git diff -U0 -- events/batch-033_framework.jsonl | grep '^+[^+]' \
    | grep -q '"event_type": "framework_writeback"' \
    || { echo "   VIOLATION: the appended event is not a framework_writeback"; fail=1; }
  git diff -U0 -- events/batch-033_framework.jsonl | grep '^+[^+]' \
    | grep -q '"script": "tag_g1d_withdrawn_from"' \
    || { echo "   VIOLATION: the appended event was not written by this task's script"; fail=1; }
fi

say "THE FRAMEWORK RECORD — one node's two new properties, nothing dropped"
/opt/anaconda3/bin/python3 - <<'PY' || fail=1
import json, subprocess, sys
REPO = "/Users/brock/GitHub/ai-readiness-kg"
def at(rev):
    r = subprocess.run(["git", "show", f"{rev}:framework/ai_readiness_framework.json"],
                       capture_output=True, text=True, cwd=REPO)
    r.returncode and sys.exit(f"   VIOLATION: cannot read the record at {rev}")
    return json.loads(r.stdout)
head = at("HEAD")
now = json.loads(open(f"{REPO}/framework/ai_readiness_framework.json").read())
if len(head["nodes"]) != len(now["nodes"]) or len(head["edges"]) != len(now["edges"]):
    print(f"   VIOLATION: nodes {len(head['nodes'])}->{len(now['nodes'])}, "
          f"edges {len(head['edges'])}->{len(now['edges'])}"); sys.exit(1)
before = {n["id"]: n["properties"] for n in head["nodes"]}
moved = {}
for n in now["nodes"]:
    b = before.get(n["id"], {})
    d = sorted(k for k in set(b) | set(n["properties"]) if b.get(k) != n["properties"].get(k))
    if d:
        moved[n["id"]] = d
print(f"   nodes changed: {moved}")
if moved != {"ind:G1-D": ["withdrawn_from", "withdrawn_from_source"]}:
    print("   VIOLATION: the record moved somewhere other than ind:G1-D's two new properties")
    sys.exit(1)
dropped = [k for k in before.get("ind:G1-D", {}) if k not in
           next(n["properties"] for n in now["nodes"] if n["id"] == "ind:G1-D")]
if dropped:
    print(f"   VIOLATION: ind:G1-D lost {dropped}"); sys.exit(1)
print("   ind:G1-D gained withdrawn_from and withdrawn_from_source; nothing else moved")
PY

say "EVERY modified path is in this task's write set"
git status --porcelain | sed 's/^...//' | sort > /tmp/dcag_all.txt
cat > /tmp/dcag_allowed.txt <<'EOF'
.zenodo.json
CITATION.cff
cc_tasks/2026-09-15_derived_counts_and_appendix_guard.md
cc_tasks/2026-09-15_derived_counts_and_appendix_guard_RESULT.md
docs/data/CITATION.cff
docs/data/ai_readiness_framework.json
docs/data/index.json
docs/data/sources_per_check.json
docs/data/zenodo.json
docs/index.html
docs/llms.txt
docs/sitemap.xml
events/batch-033_framework.jsonl
framework/ai_readiness_framework.json
scripts/build_l0_site.py
scripts/check_protected_abstract_five_checks.sh
scripts/check_protected_derived_counts.sh
scripts/numerals.py
scripts/report_traceability.py
scripts/tag_g1d_withdrawn_from.py
seldon_events.jsonl
tests/test_publication.py
tests/test_report_traceability.py
EOF
sort -o /tmp/dcag_allowed.txt /tmp/dcag_allowed.txt
stray=$(comm -23 /tmp/dcag_all.txt /tmp/dcag_allowed.txt)
if [ -n "$stray" ]; then
  echo "$stray"; echo "   VIOLATION: a path outside the write set moved"; fail=1
else
  echo "   $(wc -l < /tmp/dcag_all.txt | tr -d ' ') modified path(s), all inside the write set"
fi

say "THE POINT OF THE TASK, asserted rather than assumed"
/opt/anaconda3/bin/python3 - <<'PY' || fail=1
import json, pathlib, sys
REPO = pathlib.Path("/Users/brock/GitHub/ai-readiness-kg")
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "assessment" / "harness"))
sys.path.insert(0, "/Users/brock/GitHub/seldon")
from numerals import word
import build_l0_site as B

legs = B.matrix_legs("tierA", "2026-09-10_rj2")
label = B.matrix_label(dict(B.MATRICES)["tierA"], legs)
print(f"   the tier-A matrix has {len(legs)} legs: {legs}")
print(f"   the rendered label is: {label!r}")
html = (REPO / "docs/index.html").read_text()
txt = (REPO / "docs/llms.txt").read_text()
n = html.count(label) + txt.count(label)
if n != 4:
    print(f"   VIOLATION: {n} of the four label renderings carry it, not 4"); sys.exit(1)
print("   all four renderings (index.html x2, llms.txt x2) carry it")
stale = [f"{w} host-level checks" for w in ("six", "seven", "four")
         if f"{w} host-level checks" in html.lower() or f"{w} host-level checks" in txt.lower()]
if stale:
    print(f"   VIOLATION: a published page still states {stale}"); sys.exit(1)
print(f"   no published page states a leg count other than {word(len(legs))!r}")

# The appendix, against the graph it was derived from.
drift = B.appendix_drift_against_published(B.sources_per_check())
if drift:
    print(f"   VIOLATION: the published appendix has drifted: {drift[:5]}"); sys.exit(1)
print("   docs/data/sources_per_check.json matches what the graph produces now")

doc = json.loads((REPO / "docs/data/sources_per_check.json").read_text())
g1d = [r for r in doc["rows"] if r["check"] == "G1-D"]
bad = [r["doc_id"] for r in g1d
       if r.get("measurement_tier") != "product" or r.get("withdrawn_from") != "host-level"]
if not g1d or bad:
    print(f"   VIOLATION: {len(bad)} of {len(g1d)} G1-D rows are unlabelled"); sys.exit(1)
print(f"   all {len(g1d)} G1-D rows carry measurement_tier=product, withdrawn_from=host-level")
PY

echo
[ "$fail" = "0" ] && echo "=== protected paths: PASS" || echo "=== protected paths: FAIL"
exit "$fail"
