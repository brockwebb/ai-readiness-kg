#!/bin/sh
. "$(dirname "$0")/check_protected_lib.sh"
# The protected-paths diff for cc_tasks/2026-09-19_seldon_hygiene_superseded_cadence_after.md
# and its ADDENDUM_01.
#
# Almost all of this task's code lands in the SELDON checkout. What lands HERE is three things
# and nothing else: one paragraph of CLAUDE.md (decision 5), one key with its comment in
# seldon.yaml (ADDENDUM_01 decision 6b), and the RESULT — plus this check and the event lines
# this task's own transitions wrote. `docs/`, `state/`, `framework/`, `corpus/`, `events/`,
# `assessment/` and `kg/` are byte-identical: this task runs no builder, no rule and no scan.
#
# The status prefix is stripped before matching, so the check answers the same before and
# after `git add`. Run it BEFORE the RESULT's commit: once committed every path is clean and
# the check passes vacuously.
cd /Users/brock/GitHub/ai-readiness-kg || exit 2
echo "=== protected paths"
fail=0
ME=scripts/check_protected_seldon_hygiene.sh

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
must_be_empty "the tests changed; this task adds none here" tests/
must_be_empty "controls, the identity gate or the publication declaration changed" \
  controls.yaml dixie_evidence.yaml publication.yaml
must_be_empty "a template changed; the spot template is explicitly NOT edited here" \
  cc_tasks/templates/
must_be_empty "the task file or its addendum changed; both are immutable once written" \
  cc_tasks/2026-09-19_seldon_hygiene_superseded_cadence_after.md \
  cc_tasks/2026-09-19_seldon_hygiene_superseded_cadence_after_ADDENDUM_01.md

say "scripts/ — only this check is new; render_spot_scan.py is explicitly NOT changed"
stray_scripts=$(git status --porcelain -- scripts/ | sed 's/^...//' | grep -v "^$ME$")
if [ -n "$stray_scripts" ]; then
  echo "$stray_scripts"; echo "   VIOLATION: a script other than this check moved"; fail=1
else
  echo "   only $ME"
fi

say "seldon.yaml — only stuck_after_passes and its comment were added, nothing removed"
removed=$(git diff HEAD -- seldon.yaml | grep -c '^-[^-]')
added_keys=$(git diff HEAD -- seldon.yaml | grep '^+[^+]' | grep -v '^+ *#' | grep -v '^+ *$' \
  | sed 's/^+//' | grep -Ev '^  stuck_after_passes: 3$')
if [ "$removed" != "0" ]; then
  echo "   VIOLATION: $removed line(s) removed from seldon.yaml"; fail=1
elif [ -n "$added_keys" ]; then
  echo "$added_keys"
  echo "   VIOLATION: seldon.yaml gained something other than stuck_after_passes"; fail=1
else
  echo "   only stuck_after_passes was added"
fi

say "CLAUDE.md — one paragraph added and one sentence replaced, per decision 5"
cmd_removed=$(git diff HEAD -- CLAUDE.md | grep '^-[^-]' | wc -l | tr -d ' ')
if [ "$cmd_removed" != "1" ]; then
  echo "   VIOLATION: $cmd_removed line(s) removed from CLAUDE.md; decision 5 replaces one"
  fail=1
else
  echo "   1 line replaced (the dispatch-line sentence), 1 paragraph added"
fi

say "EVERY modified path is inside the write set"
git status --porcelain | sed 's/^...//' | sort > /tmp/sh_all.txt
cat > /tmp/sh_allowed.txt <<EOF
CLAUDE.md
cc_tasks/2026-09-19_seldon_hygiene_superseded_cadence_after_RESULT.md
$ME
seldon.yaml
seldon_events.jsonl
EOF
sort -o /tmp/sh_allowed.txt /tmp/sh_allowed.txt
stray=$(comm -23 /tmp/sh_all.txt /tmp/sh_allowed.txt)
if [ -n "$stray" ]; then
  echo "$stray"; echo "   VIOLATION: a path outside the write set moved"; fail=1
else
  echo "   $(wc -l < /tmp/sh_all.txt | tr -d ' ') modified path(s), all inside the write set"
fi

say "THE POINT OF THE TASK, asserted against the installed Seldon (read-only)"
/opt/anaconda3/bin/python3 - <<'PYCHK' || fail=1
import inspect, sys
from pathlib import Path
sys.path.insert(0, "/Users/brock/GitHub/seldon")
from seldon.commands import cadence as CAD
from seldon.commands import cc as CC
from seldon.commands import dispatch as CMD
from seldon.commands import go, session, status, verify
from seldon.core import cadence as C
from seldon.core import dispatch as D
from seldon.core import staleness as S

repo = Path("/Users/brock/GitHub/ai-readiness-kg")
cfg = D.load_dispatch_config(repo)
claude_md = (repo / "CLAUDE.md").read_text(encoding="utf-8")
protocol = claude_md.split("## CC dispatch protocol", 1)[1].split("### The RESULT", 1)[0]
checks = {
    # Decision 1: one predicate, four surfaces.
    "the predicate exists and is exported": callable(S.decided_not_drifted),
    "verify, status, briefing and go all read it": all(
        "partition_stale" in inspect.getsource(m)
        for m in (verify.check_stale_artifacts, status.status_command.callback,
                  session.get_briefing_data)) and
        "stale_decided" in inspect.getsource(go._format_project_state),
    # Decision 2: the command group is registered and renders on request.
    "seldon cadence list|check|render is registered":
        set(CAD.cadence_group.commands) >= {"list", "check", "render"},
    "the CLI registers the cadence group":
        "cadence_group" in (repo.parent / "seldon" / "seldon" / "cli.py").read_text(
            encoding="utf-8"),
    # The IDENTIFIER, not the string: the module docstring explains `cadence_created` in
    # prose, and what must not be there is a reference that could emit it.
    "a hand render writes cadence_rendered, never cadence_created":
        "EVENT_CADENCE_RENDERED" in inspect.getsource(CAD._emit_rendered)
        and "EVENT_CADENCE_CREATED" not in inspect.getsource(CAD),
    # Decision 3: the header is read at registration, through the shared writer.
    "register_task_file reads **After:**": "read_after" in inspect.getsource(
        CC.register_task_file),
    "the After writer is add_chain, not a second one":
        "add_chain" in inspect.getsource(CC.write_after_edges)
        and "create_link" not in inspect.getsource(CC.write_after_edges),
    # Decision 4: the lint warns and does not refuse.
    "the SEQUENCING lint returns a warning string, never raises":
        "raise" not in inspect.getsource(CC.sequencing_lint),
    # Decision 5: CLAUDE.md says it, in the dispatch-protocol section.
    "CLAUDE.md names the After header in the dispatch protocol":
        "**After:**" in protocol,
    "CLAUDE.md no longer says sequencing is stated in the dispatch line":
        "stated in the dispatch line, not assumed" not in claude_md,
    # ADDENDUM_01 decision 6.
    "an MCP write tool commits its own append":
        "commit_journal_append" in inspect.getsource(
            __import__("seldon.mcp_server", fromlist=["x"])),
    "the sweep accepts dispatcher and desktop, never cc":
        D.COMMITTABLE_ACTORS == ("dispatcher", "desktop"),
    "seldon.yaml declares the stuck threshold": cfg["stuck_after_passes"] == 3,
    "the pass raises the alarm once per streak":
        "_stuck(" in inspect.getsource(CMD._pass)
        and "advance_stuck" in inspect.getsource(CMD._stuck),
    "the refusal line names the dirty paths":
        "_dirty_paths(tree)" in inspect.getsource(CMD._pass),
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
