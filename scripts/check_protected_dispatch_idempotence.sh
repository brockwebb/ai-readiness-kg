#!/bin/sh
. "$(dirname "$0")/check_protected_lib.sh"
# The protected-paths diff for cc_tasks/2026-09-16_dispatch_idempotence.md.
#
# This task's code lands in the SELDON checkout. What lands here is one test file, one design
# addendum and this check — so the strongest true claim about this repository is that nothing
# it measures, publishes or decides with moved at all, and that is what is asserted.
#
# `docs/` is the one place the task's own "zero edits to docs/" and its §2 ("DN-006
# ADDENDUM_03") disagree. §2 is the later and more specific instruction, so exactly one file
# under `docs/` may move and every other path in that tree must be byte-identical.
#
# The status prefix is stripped before matching, so the check answers the same before and
# after `git add`.
cd /Users/brock/GitHub/ai-readiness-kg || exit 2
echo "=== protected paths"
fail=0
ADDENDUM=docs/design/2026-09-15_DN-006_standing_dispatcher_ADDENDUM_03.md

say() { echo; echo "-- $1"; }
must_be_empty() {
  label="$1"; shift
  out=$(git status --porcelain -- "$@")
  [ -n "$out" ] && { echo "$out"; echo "   VIOLATION: $label"; fail=1; }
}

say "THE PUBLISHED TREE and the measurement tree — this task runs no builder and no rule"
# NOT `must_be_empty <expansion>`: an expansion that comes back empty leaves `git status`
# with no pathspec at all, which lists the WHOLE TREE and reports every path as a violation of
# a rule about `docs/`. A check that fails loudest when there is nothing wrong is worse than
# no check.
docs_moved=$(git status --porcelain -- docs/ | sed 's/^...//' | grep -vx "$ADDENDUM")
if [ -n "$docs_moved" ]; then
  echo "$docs_moved"; echo "   VIOLATION: something under docs/ other than the addendum moved"
  fail=1
else
  echo "   docs/ is byte-identical apart from the addendum §2 requires"
fi
must_be_empty "a stored payload changed" state/
must_be_empty "the KG event log changed" events/
must_be_empty "the rules or harness changed" assessment/
must_be_empty "kg/ changed" kg/
must_be_empty "the framework record or skeleton changed" framework/
must_be_empty "corpus changed" corpus/
must_be_empty "controls, the identity gate or the publication declaration changed" \
  controls.yaml dixie_evidence.yaml publication.yaml

say "THE BOOTLOADER and the decision record"
# The task licenses a CLAUDE.md edit only if decision 3 makes a sentence in the CC dispatch
# protocol FALSE. It does not: the protocol never said who commits a registered task file.
must_be_empty "CLAUDE.md changed and the task licensed no edit to it" CLAUDE.md
must_be_empty "a design DECISION moved; this task amends a design NOTE" docs/design_decisions.md

say "SCRIPTS — this check and nothing else"
git status --porcelain -- scripts/ | sed 's/^...//' \
  | grep -vx 'scripts/check_protected_dispatch_idempotence.sh' > /tmp/dispidem_scripts.txt
if [ -s /tmp/dispidem_scripts.txt ]; then
  cat /tmp/dispidem_scripts.txt; echo "   VIOLATION: a script outside the write set moved"
  fail=1
else
  echo "   only this check"
fi

say "PRIOR RESULTs — a prior execution record is not edited"
git status --porcelain -- cc_tasks/ | sed 's/^...//' \
  | grep -vx 'cc_tasks/2026-09-16_dispatch_idempotence.md' \
  | grep -vx 'cc_tasks/2026-09-16_dispatch_idempotence_RESULT.md' > /tmp/dispidem_tasks.txt
if [ -s /tmp/dispidem_tasks.txt ]; then
  cat /tmp/dispidem_tasks.txt; echo "   VIOLATION: a cc_task other than this one's pair moved"
  fail=1
else
  echo "   only this task and its RESULT"
fi

say "EVERY modified path is inside the write set"
git status --porcelain | sed 's/^...//' | sort > /tmp/dispidem_all.txt
cat > /tmp/dispidem_allowed.txt <<'EOF'
cc_tasks/2026-09-16_dispatch_idempotence.md
cc_tasks/2026-09-16_dispatch_idempotence_RESULT.md
docs/design/2026-09-15_DN-006_standing_dispatcher_ADDENDUM_03.md
scripts/check_protected_dispatch_idempotence.sh
seldon_events.jsonl
tests/test_dispatch_config.py
EOF
sort -o /tmp/dispidem_allowed.txt /tmp/dispidem_allowed.txt
stray=$(comm -23 /tmp/dispidem_all.txt /tmp/dispidem_allowed.txt)
if [ -n "$stray" ]; then
  echo "$stray"; echo "   VIOLATION: a path outside the write set moved"; fail=1
else
  echo "   $(wc -l < /tmp/dispidem_all.txt | tr -d ' ') modified path(s), all inside the write set"
fi

say "THE POINT OF THE TASK, asserted rather than assumed"
# Read-only, against the LIVE event log and the installed dispatcher. Nothing is run that
# could write an event: the suppression is asked the question a pass would ask it, with the
# payload the last real refusal carries, and must answer "already recorded".
/opt/anaconda3/bin/python3 - <<'PYCHK' || fail=1
import json, pathlib, sys
sys.path.insert(0, "/Users/brock/GitHub/seldon")
REPO = pathlib.Path("/Users/brock/GitHub/ai-readiness-kg")
from seldon.commands import dispatch as CMD
bad = 0

refusals = [json.loads(ln)["payload"]
            for ln in (REPO / "seldon_events.jsonl").read_text(encoding="utf-8").splitlines()
            if '"reason": "lease_held"' in ln]
keyed = [r for r in refusals if r.get("acquired_at")]
print(f"   lease_held refusals on the log: {len(refusals)}; "
      f"{len(keyed)} carry the acquisition they are about")
if not keyed:
    print("   VIOLATION: no refusal carries acquired_at; the suppression has nothing to key on")
    bad += 1
else:
    # Every acquisition that has been keyed appears exactly once. The unkeyed ones are the
    # defect's own record from 2026-09-16T04:2x — three lines for one acquisition — and they
    # stay, because they are a true record of what the dispatcher did (task decision 5).
    seen = {}
    for r in keyed:
        seen[(r["holder"], r["acquired_at"])] = seen.get((r["holder"], r["acquired_at"]), 0) + 1
    repeats = {k: n for k, n in seen.items() if n > 1}
    print(f"   {len(seen)} distinct acquisition(s) keyed, {len(repeats)} with more than one event")
    if repeats:
        print(f"   VIOLATION: an acquisition was refused more than once: {repeats}")
        bad += 1
    last = keyed[-1]
    if not CMD._lease_acquisition_already_refused(REPO, {"holder": last["holder"],
                                                         "acquired_at": last["acquired_at"]}):
        print("   VIOLATION: the suppression does not recognise the last refusal it wrote")
        bad += 1
    else:
        print(f"   a further pass over acquisition {last['acquired_at']} writes nothing")
    if CMD._lease_acquisition_already_refused(REPO, {"holder": last["holder"],
                                                     "acquired_at": "1999-01-01T00:00:00Z"}):
        print("   VIOLATION: a NEW acquisition would be suppressed; decision 1 says it is not")
        bad += 1
    else:
        print("   a new acquisition by the same holder is refused again, as the rule requires")

# Decision 3's code is in the pass, before candidacy, and it is the only writer of that commit.
src = (pathlib.Path("/Users/brock/GitHub/seldon")
       / "seldon" / "commands" / "dispatch.py").read_text(encoding="utf-8")
for needle in ("_commit_registered", "register: ", "if dry_run or claim is not None"):
    if needle not in src:
        print(f"   VIOLATION: the installed dispatcher has no {needle!r}")
        bad += 1
# The ARGUMENT `"-A"`, not the characters `-A`: the docstring of the function being checked
# quotes "`git add -A` is what the cadence already refuses", and a substring match reads the
# sentence forbidding the thing as the thing.
block = src.split("def _commit_registered")[1].split("def _pass")[0]
code = "\n".join(ln for ln in block.splitlines() if not ln.lstrip().startswith("#"))
if '"-A"' in code or "'-A'" in code:
    print("   VIOLATION: the registration commit is not pathspec-limited")
    bad += 1
elif "D.commit_paths(" not in code:
    print("   VIOLATION: the registration commit does not go through commit_paths")
    bad += 1
else:
    print("   the registration commit is pathspec-limited and gated on claim and branch")

sys.exit(1 if bad else 0)
PYCHK

echo
[ "$fail" = "0" ] && echo "=== protected paths: PASS" || echo "=== protected paths: FAIL"
exit "$fail"
