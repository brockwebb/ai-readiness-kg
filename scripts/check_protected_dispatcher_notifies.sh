#!/bin/sh
# The protected-paths diff for cc_tasks/2026-09-17_dispatcher_notifies.md.
#
# The code lands in the SELDON checkout. What lands here: the `dispatch.notify` lines of
# seldon.yaml (decision 1), the wrapper's log-path line (decision 4), the fixture's environment
# in tests/test_dispatch_config.py, the event store's own lines, this check and the RESULT. The
# task file says `docs/` is byte-identical; that is asserted, and so is the limit on seldon.yaml
# to the dispatch block's notify keys.
#
# The status prefix is stripped before matching, so the check answers the same before and
# after `git add`. Run it BEFORE the RESULT's commit: once committed, every path is clean and
# the check passes vacuously.
cd /Users/brock/GitHub/ai-readiness-kg || exit 2
echo "=== protected paths"
fail=0
ME=scripts/check_protected_dispatcher_notifies.sh

say() { echo; echo "-- $1"; }
must_be_empty() {
  label="$1"; shift
  out=$(git status --porcelain -- "$@")
  [ -n "$out" ] && { echo "$out"; echo "   VIOLATION: $label"; fail=1; }
}

say "THE PUBLISHED TREE and the measurement tree — this task runs no builder and no rule"
must_be_empty "something under docs/ moved" docs/
must_be_empty "a stored payload changed" state/
must_be_empty "the KG event log changed" events/
must_be_empty "the rules or harness changed" assessment/
must_be_empty "kg/ changed" kg/
must_be_empty "the framework record or skeleton changed" framework/
must_be_empty "corpus changed" corpus/
must_be_empty "controls, the identity gate or the publication declaration changed" \
  controls.yaml dixie_evidence.yaml publication.yaml CLAUDE.md
must_be_empty "the plist changed; decision 4 is the wrapper's log line only" \
  scripts/jobs/com.brock.airkg-dispatch.plist
must_be_empty "the task file changed; it is immutable once written" \
  cc_tasks/2026-09-17_dispatcher_notifies.md

say "seldon.yaml — only notify/notify_timeout_s and their comment were added, nothing removed"
removed=$(git diff HEAD -- seldon.yaml | grep -c '^-[^-]')
added_keys=$(git diff HEAD -- seldon.yaml | grep '^+[^+]' | grep -v '^+ *#' | grep -v '^+ *$' \
  | sed 's/^+//' | grep -Ev '^  notify: >-$|^    osascript |^    -e .end run.|^  notify_timeout_s: 30$')
if [ "$removed" != "0" ]; then
  echo "   VIOLATION: $removed line(s) removed from seldon.yaml"; fail=1
elif [ -n "$added_keys" ]; then
  echo "$added_keys"; echo "   VIOLATION: seldon.yaml gained something other than the notify keys"; fail=1
else
  echo "   only the notify block was added"
fi

say "EVERY modified path is inside the write set"
git status --porcelain | sed 's/^...//' | sort > /tmp/dn_all.txt
cat > /tmp/dn_allowed.txt <<EOF
cc_tasks/2026-09-17_dispatcher_notifies_RESULT.md
$ME
scripts/jobs/airkg_dispatch.sh
seldon.yaml
seldon_events.jsonl
tests/test_dispatch_config.py
EOF
sort -o /tmp/dn_allowed.txt /tmp/dn_allowed.txt
stray=$(comm -23 /tmp/dn_all.txt /tmp/dn_allowed.txt)
if [ -n "$stray" ]; then
  echo "$stray"; echo "   VIOLATION: a path outside the write set moved"; fail=1
else
  echo "   $(wc -l < /tmp/dn_all.txt | tr -d ' ') modified path(s), all inside the write set"
fi

say "THE POINT OF THE TASK, asserted against the installed dispatcher (read-only)"
/opt/anaconda3/bin/python3 - <<'PYCHK' || fail=1
import inspect, sys
from pathlib import Path
sys.path.insert(0, "/Users/brock/GitHub/seldon")
from seldon.commands import dispatch as CMD
from seldon.core import dispatch as D
repo = Path("/Users/brock/GitHub/ai-readiness-kg")
cfg = D.load_dispatch_config(repo)
src = inspect.getsource(CMD._pass)
code = "\n".join(ln for ln in src.splitlines() if not ln.lstrip().startswith("#"))
after = code[code.index("EVENT_FINISHED"):]
wrapper = (repo / "scripts/jobs/airkg_dispatch.sh").read_text(encoding="utf-8")
checks = {
    "seldon.yaml names a notifier": bool(cfg["notify"]),
    "the notify timeout loads as 30 s": cfg["notify_timeout_s"] == 30,
    "the notifier runs after dispatch_finished on both branches": after.count("_notify(") == 2,
    "each notify precedes that branch's commit":
        all(a < b for a, b in zip(
            [i for i in range(len(after)) if after.startswith("_notify(", i)],
            [i for i in range(len(after)) if after.startswith("_record_and_push(", i)])),
    "the wrapper's log path comes from AIRKG_DISPATCH_LOG":
        'LOG="${AIRKG_DISPATCH_LOG:-$REPO/logs/airkg_dispatch.log}"' in wrapper,
}
bad = 0
for label, ok in checks.items():
    print(f"   {'ok ' if ok else 'NO '} {label}")
    bad += 0 if ok else 1
sys.exit(1 if bad else 0)
PYCHK

echo
[ "$fail" = "0" ] && echo "=== protected paths: PASS" || echo "=== protected paths: FAIL"
exit "$fail"
