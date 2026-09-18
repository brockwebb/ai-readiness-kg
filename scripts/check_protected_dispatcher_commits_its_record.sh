#!/bin/sh
. "$(dirname "$0")/check_protected_lib.sh"
# The protected-paths diff for cc_tasks/2026-09-16_dispatcher_commits_its_record.md.
#
# The code lands in the SELDON checkout. What lands here: one test file, one sentence of
# CLAUDE.md (decision 4, "one sentence replaced, nothing else in the file"), DN-006
# ADDENDUM_04, this check, the RESULT, and the event store's own lines. The task's final
# sentence says `docs/` is byte-identical apart from the addendum; that is asserted, and so is
# the one-sentence limit on CLAUDE.md, as a line count.
#
# The status prefix is stripped before matching, so the check answers the same before and
# after `git add`. Run it BEFORE the RESULT's commit: once committed, every path is clean and
# the check passes vacuously.
cd /Users/brock/GitHub/ai-readiness-kg || exit 2
echo "=== protected paths"
fail=0
ADDENDUM=docs/design/2026-09-15_DN-006_standing_dispatcher_ADDENDUM_04.md
ME=scripts/check_protected_dispatcher_commits_its_record.sh

say() { echo; echo "-- $1"; }
must_be_empty() {
  label="$1"; shift
  out=$(git status --porcelain -- "$@")
  [ -n "$out" ] && { echo "$out"; echo "   VIOLATION: $label"; fail=1; }
}

say "THE PUBLISHED TREE and the measurement tree — this task runs no builder and no rule"
docs_moved=$(git status --porcelain -- docs/ | sed 's/^...//' | grep -vx "$ADDENDUM")
if [ -n "$docs_moved" ]; then
  echo "$docs_moved"; echo "   VIOLATION: something under docs/ other than the addendum moved"
  fail=1
else
  echo "   docs/ is byte-identical apart from ADDENDUM_04"
fi
must_be_empty "a stored payload changed" state/
must_be_empty "the KG event log changed" events/
must_be_empty "the rules or harness changed" assessment/
must_be_empty "kg/ changed" kg/
must_be_empty "the framework record or skeleton changed" framework/
must_be_empty "corpus changed" corpus/
must_be_empty "controls, seldon.yaml, the identity gate or the publication declaration changed" \
  controls.yaml seldon.yaml dixie_evidence.yaml publication.yaml

say "THE BOOTLOADER — exactly one line of CLAUDE.md, and it is the dispatch-protocol sentence"
numstat=$(git diff --numstat HEAD -- CLAUDE.md)
case "$numstat" in
  "")        echo "   VIOLATION: CLAUDE.md did not change; decision 4 requires it"; fail=1 ;;
  "1	1	CLAUDE.md") echo "   one line replaced" ;;
  *)         echo "   $numstat"; echo "   VIOLATION: more than one line of CLAUDE.md moved"; fail=1 ;;
esac
if ! grep -q "A Desktop session's registration turn ends with the registration" CLAUDE.md; then
  echo "   VIOLATION: the decision-4 sentence is not in CLAUDE.md"; fail=1
fi
must_be_empty "a design DECISION moved; this task amends a design NOTE" docs/design_decisions.md

say "EVERY modified path is inside the write set"
git status --porcelain | sed 's/^...//' | sort > /tmp/dcir_all.txt
cat > /tmp/dcir_allowed.txt <<EOF
CLAUDE.md
cc_tasks/2026-09-16_dispatcher_commits_its_record.md
cc_tasks/2026-09-16_dispatcher_commits_its_record_RESULT.md
$ADDENDUM
$ME
seldon_events.jsonl
tests/test_dispatch_config.py
EOF
sort -o /tmp/dcir_allowed.txt /tmp/dcir_allowed.txt
stray=$(comm -23 /tmp/dcir_all.txt /tmp/dcir_allowed.txt)
if [ -n "$stray" ]; then
  echo "$stray"; echo "   VIOLATION: a path outside the write set moved"; fail=1
else
  echo "   $(wc -l < /tmp/dcir_all.txt | tr -d ' ') modified path(s), all inside the write set"
fi

say "THE POINT OF THE TASK, asserted against the installed dispatcher"
# Read-only. Nothing here runs a pass.
/opt/anaconda3/bin/python3 - <<'PYCHK' || fail=1
import inspect, sys
sys.path.insert(0, "/Users/brock/GitHub/seldon")
from seldon.commands import dispatch as CMD
from seldon.core import dispatch as D
bad = 0
src = inspect.getsource(CMD._pass)
code = "\n".join(ln for ln in src.splitlines() if not ln.lstrip().startswith("#"))
# Decision 1: before the launch, after the finish (both branches), and the leftover sweep.
launch = code.index("_run(cmd")
before = code[:launch]
after = code[launch:]
checks = {
    "the leftover sweep precedes the cadence":
        code.index("_record_own_lines(") < code.index("_cadence("),
    "the launch lines are committed before the session runs":
        "_record_and_push(" in before[before.index("EVENT_LAUNCHED"):],
    "the finish is committed on both the ok and the blocked branch":
        after.count("_record_and_push(") == 2,
    "the nothing-eligible branch retries the push": "_push(project_dir, cfg)" in code,
}
for label, ok in checks.items():
    print(f"   {'ok ' if ok else 'NO '} {label}")
    bad += 0 if ok else 1
rec = inspect.getsource(CMD._record_own_lines)
if "D.commit_paths(project_dir, [store]" not in rec or "own_appended_lines" not in rec:
    print("   NO  the record commit is not pathspec-limited to the store and actor-gated")
    bad += 1
else:
    print("   ok  the record commit is pathspec-limited to the store and actor-gated")
if '"-A"' in rec or "'-A'" in rec:
    print("   NO  the record commit stages with -A")
    bad += 1
sys.exit(1 if bad else 0)
PYCHK

echo
[ "$fail" = "0" ] && echo "=== protected paths: PASS" || echo "=== protected paths: FAIL"
exit "$fail"
