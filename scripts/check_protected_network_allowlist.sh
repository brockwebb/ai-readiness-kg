#!/bin/sh
. "$(dirname "$0")/check_protected_lib.sh"
# The protected-paths diff for cc_tasks/2026-09-18_network_allowlist.md.
#
# The dispatcher change lands in the SELDON checkout. What lands here: the fetch helper and its
# test (decision 3), two CLAUDE.md sentences (the header grammar beside the three-header rule,
# and decision 5 in the corpus paragraph), DN-006 ADDENDUM_05 (decision 4), the event store's
# own lines, this check and the RESULT. The task file says `docs/` is otherwise byte-identical;
# that is asserted, and so is the limit on CLAUDE.md to added text.
#
# The status prefix is stripped before matching, so the check answers the same before and
# after `git add`. Run it BEFORE the RESULT's commit: once committed, every path is clean and
# the check passes vacuously.
cd /Users/brock/GitHub/ai-readiness-kg || exit 2
echo "=== protected paths"
fail=0
ME=scripts/check_protected_network_allowlist.sh
ADD=docs/design/2026-09-15_DN-006_standing_dispatcher_ADDENDUM_05.md

say() { echo; echo "-- $1"; }
must_be_empty() {
  label="$1"; shift
  out=$(git status --porcelain -- "$@")
  [ -n "$out" ] && { echo "$out"; echo "   VIOLATION: $label"; fail=1; }
}

say "THE PUBLISHED TREE and the measurement tree — this task runs no builder, no rule, no fetch"
# Not `must_be_empty` over a computed path list: an empty list would make it `git status --`
# with no pathspec, which reports the whole tree.
docs_moved=$(git status --porcelain -- docs/ | sed 's/^...//' | grep -vx "$ADD")
[ -n "$docs_moved" ] && { echo "$docs_moved"; echo "   VIOLATION: something under docs/ other than ADDENDUM_05 moved"; fail=1; }
must_be_empty "a stored payload changed" state/
must_be_empty "the KG event log changed" events/
must_be_empty "the rules or harness changed" assessment/
must_be_empty "kg/ changed" kg/
must_be_empty "the framework record or skeleton changed" framework/
must_be_empty "corpus changed" corpus/
must_be_empty "controls, the identity gate, seldon.yaml or the publication declaration changed" \
  controls.yaml dixie_evidence.yaml publication.yaml seldon.yaml
must_be_empty "the task file changed; it is immutable once written" \
  cc_tasks/2026-09-18_network_allowlist.md

say "CLAUDE.md — lines only added or extended, none removed outright"
# The corpus paragraph gains a trailing sentence, which git shows as one line replaced by a
# longer one that starts with the old one. Anything else removed is a violation.
py=/opt/anaconda3/bin/python3
$py - <<'PYCHK' || fail=1
import subprocess, sys
d = subprocess.run(["git", "diff", "HEAD", "--", "CLAUDE.md"], capture_output=True,
                   text=True, cwd="/Users/brock/GitHub/ai-readiness-kg").stdout.splitlines()
rem = [l[1:] for l in d if l.startswith("-") and not l.startswith("---")]
add = [l[1:] for l in d if l.startswith("+") and not l.startswith("+++")]
lost = [r for r in rem if not any(a.startswith(r) for a in add)]
if lost:
    print("\n".join(lost)); print("   VIOLATION: CLAUDE.md lost text"); sys.exit(1)
print(f"   {len(add)} line(s) added or extended, nothing removed")
PYCHK

say "EVERY modified path is inside the write set"
git status --porcelain | sed 's/^...//' | sort > /tmp/na_all.txt
cat > /tmp/na_allowed.txt <<EOF
CLAUDE.md
cc_tasks/2026-09-18_network_allowlist_RESULT.md
$ADD
$ME
scripts/fetch_allowlisted.py
seldon_events.jsonl
tests/test_fetch_allowlisted.py
EOF
sort -o /tmp/na_allowed.txt /tmp/na_allowed.txt
stray=$(comm -23 /tmp/na_all.txt /tmp/na_allowed.txt)
if [ -n "$stray" ]; then
  echo "$stray"; echo "   VIOLATION: a path outside the write set moved"; fail=1
else
  echo "   $(wc -l < /tmp/na_all.txt | tr -d ' ') modified path(s), all inside the write set"
fi

say "THE POINT OF THE TASK, asserted against the installed dispatcher (read-only)"
$py - <<'PYCHK' || fail=1
import inspect, sys
from pathlib import Path
sys.path.insert(0, "/Users/brock/GitHub/seldon")
from seldon.commands import dispatch as CMD
from seldon.core import dispatch as D
repo = Path("/Users/brock/GitHub/ai-readiness-kg")
sys.path.insert(0, str(repo / "scripts"))
import fetch_allowlisted as F
tool = D.candidacy(repo / "cc_tasks/2026-09-18_tool_docs_ingest.md")["headers"][D.HEADER_NETWORK]
run_src = inspect.getsource(CMD._run)
checks = {
    "`none beyond git push` parses as none": D.parse_network("none beyond `git push`.")["kind"] == "none",
    "an allowlist parses to exact lower-cased hosts":
        D.parse_network("allowlist: A.org, b.org")["hosts"] == ["a.org", "b.org"],
    "a wildcard is refused and the grammar quoted":
        D.NETWORK_GRAMMAR in (D.parse_network("allowlist: *.a.org")["error"] or ""),
    "the queued successor's header passes c5": D.parse_network(tool)["kind"] == "allowlist",
    "the child env strips an inherited allowlist": "k != D.NETWORK_ALLOWLIST_ENV" in run_src,
    "the helper reads the variable Seldon sets": F.ALLOWLIST_ENV == D.NETWORK_ALLOWLIST_ENV,
    "the pass records network_allowlist on dispatch_launched":
        '"network_allowlist": chosen["criteria"]["c5"]["network_allowlist"]'
        in inspect.getsource(CMD._pass),
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
