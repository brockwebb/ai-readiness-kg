#!/bin/sh
# The protected-paths diff for cc_tasks/2026-09-16_publication_guards.md.
#
# The task writes TESTS and one shared function. It regenerates nothing: no builder is run, no
# matrix is rewritten, no page is re-rendered, nothing is measured and nothing is judged. So
# the strongest true claim about `docs/` is that the whole tree is byte-identical, and that is
# what is asserted here rather than a list of files that were allowed to move.
#
# That matters more than usual for this task. Every guard it adds compares a published file to
# the thing it was generated from; a task that quietly REGENERATED the published file would
# make its own guards pass by moving the evidence, and the diff is the only thing that can
# tell those two apart.
#
# The status prefix is stripped before matching, so the check answers the same before and
# after `git add`.
cd /Users/brock/GitHub/ai-readiness-kg || exit 2
echo "=== protected paths"
fail=0

say() { echo; echo "-- $1"; }
must_be_empty() {
  label="$1"; shift
  out=$(git status --porcelain -- "$@")
  [ -n "$out" ] && { echo "$out"; echo "   VIOLATION: $label"; fail=1; }
}

say "THE PUBLISHED TREE — this task compares it and regenerates no part of it"
must_be_empty "something under docs/ changed" docs/

say "STORED PAYLOADS and the event log — nothing is measured and nothing is judged"
must_be_empty "a stored payload changed" state/
must_be_empty "the event log changed" events/

say "THE MEASUREMENT TREE — no rule, no harness, no schema, no framework record, no corpus"
must_be_empty "the rules or harness changed" assessment/
must_be_empty "kg/ changed" kg/
must_be_empty "the framework record or skeleton changed" framework/
must_be_empty "corpus changed" corpus/
must_be_empty "controls or the identity gate changed" controls.yaml dixie_evidence.yaml

say "DESIGN DECISIONS and the standing map — a guard task decides nothing"
must_be_empty "a design decision or design note changed" docs/design_decisions.md docs/design/ \
  docs/schema_v0.1.md CLAUDE.md

say "SCRIPTS — the shared function, the gate that now calls it, and this check"
git status --porcelain -- scripts/ | sed 's/^...//' \
  | grep -vx 'scripts/build_l0_site.py' \
  | grep -vx 'scripts/check_protected_abstract_five_checks.sh' \
  | grep -vx 'scripts/check_protected_publication_guards.sh' > /tmp/pubg_scripts.txt
if [ -s /tmp/pubg_scripts.txt ]; then
  cat /tmp/pubg_scripts.txt; echo "   VIOLATION: a script outside the write set moved"; fail=1
else
  echo "   only build_l0_site.py, the abstract gate and this check"
fi

say "PRIOR RESULTs — a prior execution record is not edited"
git status --porcelain -- cc_tasks/ | sed 's/^...//' \
  | grep -vx 'cc_tasks/2026-09-16_publication_guards.md' \
  | grep -vx 'cc_tasks/2026-09-16_publication_guards_RESULT.md' > /tmp/pubg_tasks.txt
if [ -s /tmp/pubg_tasks.txt ]; then
  cat /tmp/pubg_tasks.txt; echo "   VIOLATION: a cc_task other than this one's pair moved"
  fail=1
else
  echo "   only this task and its RESULT"
fi

say "EVERY modified path is inside the write set"
git status --porcelain | sed 's/^...//' | sort > /tmp/pubg_all.txt
cat > /tmp/pubg_allowed.txt <<'EOF'
cc_tasks/2026-09-16_publication_guards.md
cc_tasks/2026-09-16_publication_guards_RESULT.md
scripts/build_l0_site.py
scripts/check_protected_abstract_five_checks.sh
scripts/check_protected_publication_guards.sh
seldon_events.jsonl
tests/test_publication.py
EOF
sort -o /tmp/pubg_allowed.txt /tmp/pubg_allowed.txt
stray=$(comm -23 /tmp/pubg_all.txt /tmp/pubg_allowed.txt)
if [ -n "$stray" ]; then
  echo "$stray"; echo "   VIOLATION: a path outside the write set moved"; fail=1
else
  echo "   $(wc -l < /tmp/pubg_all.txt | tr -d ' ') modified path(s), all inside the write set"
fi

say "build_l0_site.py — the diff is the shared function and its two module constants"
# Additive, and checkable as such: the task adds `abstract_leg_count_drift`, the consumer list,
# the sentence pattern and one stdlib import. A removed line in this file would mean the task
# changed what the builder WRITES, which is the one thing it must not do.
removed=$(git diff -U0 -- scripts/build_l0_site.py | grep -c '^-[^-]')
echo "   -$removed line(s) removed"
if [ "$removed" != "0" ]; then
  git diff -U0 -- scripts/build_l0_site.py | grep '^-[^-]'
  echo "   VIOLATION: the builder lost a line; this task only adds a comparison"; fail=1
fi

say "THE POINT OF THE TASK, asserted rather than assumed"
# Every guard the task adds, run against the tree, with the count of comparisons each makes.
# A guard that has stopped comparing anything passes; a guard that reports how many rows it
# compared cannot.
/opt/anaconda3/bin/python3 - <<'PYCHK' || fail=1
import json, pathlib, sys
REPO = pathlib.Path("/Users/brock/GitHub/ai-readiness-kg")
sys.path.insert(0, str(REPO / "scripts"))
import build_l0_site as site

pub = site.publication()
suffix = site.cycle_suffix(pub["snapshot_cycle"])
bad = 0

drift = site.abstract_leg_count_drift()
legs = site.matrix_legs("tierA", suffix)
print(f"   abstract: {len(legs)} legs, {len(site.ABSTRACT_CONSUMERS)} consumers compared")
for d in drift:
    print(f"   VIOLATION: {d}")
bad += len(drift)

manifest = json.loads((REPO / "docs/data/index.json").read_text(encoding="utf-8"))
listed = [e if isinstance(e, str) else e["published"]
          for k in ("copies", "citation_files", "generated", "matrices")
          for e in manifest.get(k) or []]
missing = [p for p in listed if not (REPO / "docs" / p).is_file()]
print(f"   index.json lists {len(listed)} published path(s); {len(missing)} absent")
for p in missing:
    print(f"   VIOLATION: {p} is listed and is not in the tree")
bad += len(missing)

matrices = [p for p in listed if p.startswith("reports/scan_matrix_")]
print(f"   {len(matrices)} matrix file(s) of cycle {suffix} published and listed")
off = [p for p in matrices if suffix not in p]
for p in off:
    print(f"   VIOLATION: {p} is listed and is not of the snapshot cycle")
bad += len(off)

sys.exit(1 if bad else 0)
PYCHK

echo
[ "$fail" = "0" ] && echo "=== protected paths: PASS" || echo "=== protected paths: FAIL"
exit "$fail"
