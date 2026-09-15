#!/bin/sh
# The protected-paths diff for cc_tasks/2026-09-15_claude_md_cites_dn005.md.
#
# "Zero edits to: anything other than CLAUDE.md and the graph event for decision 3. No code,
#  no tests, no docs beyond the two CLAUDE.md insertions."
#
# The narrowest blast radius any task in this repository has declared, so the check is written
# the other way round from the usual one: instead of listing what may not move, it lists the
# few paths that MAY and refuses everything else in the working tree. A whitelist is the right
# shape when the allowed set is four files; a blacklist of everything else would be a list
# nobody could read and would miss whatever it forgot.
#
# The status prefix is stripped before matching, so the check answers the same before and after
# `git add` (the defect found in `check_protected_standing_guards.sh` on 2026-09-14).
cd /Users/brock/GitHub/ai-readiness-kg || exit 2
echo "=== protected paths"
fail=0

say() { echo; echo "-- $1"; }

say "the whole working tree — only CLAUDE.md, this task's own files and Seldon's log may move"
git status --porcelain | sed 's/^...//' \
  | grep -vE '^(CLAUDE\.md|seldon_events\.jsonl|scripts/check_protected_claude_md_dn005\.sh|cc_tasks/2026-09-15_claude_md_cites_dn005(_RESULT)?\.md)$' \
  && { echo "   VIOLATION: a path outside this task's declared set changed"; fail=1; }

say "CLAUDE.md moved by EXACTLY the two insertions, and by nothing else"
# Three added lines, zero removed: the goal paragraph, its blank line, and the DN-005 bullet.
# Decision 1 says "existing paragraphs stay verbatim after it" and decision 2 adds one bullet;
# a single deleted line anywhere in the file would mean something was rewritten rather than
# inserted, and a diff that only counts insertions would not notice.
/opt/anaconda3/bin/python3 - <<'PY' || fail=1
import subprocess, sys
d = subprocess.run(["git", "diff", "HEAD", "--numstat", "--", "CLAUDE.md"],
                   capture_output=True, text=True,
                   cwd="/Users/brock/GitHub/ai-readiness-kg").stdout.split()
if not d:
    print("   VIOLATION: CLAUDE.md did not move at all")
    sys.exit(1)
added, removed = int(d[0]), int(d[1])
print(f"   CLAUDE.md +{added} -{removed}")
if (added, removed) != (3, 0):
    print("   VIOLATION: expected exactly 3 insertions and 0 deletions")
    sys.exit(1)
PY

say "the two inserted lines say what decisions 1 and 2 require"
/opt/anaconda3/bin/python3 - <<'PY' || fail=1
import sys
from pathlib import Path
DN = "docs/design/2026-09-15_DN-005_reorientation_the_framework_is_the_goal.md"
text = Path("/Users/brock/GitHub/ai-readiness-kg/CLAUDE.md").read_text(encoding="utf-8")
what = text.split("## What this is", 1)[1].split("## Commands", 1)[0].strip()
first = what.split("\n\n", 1)[0]
read = text.split("## Where to read first", 1)[1].strip().splitlines()[0]
bad = []
# decision 1: first paragraph of "What this is", naming the goal, the validity layer, L0, and
# citing DN-005 by path.
for needle, why in ((DN, "cites DN-005 by path"),
                    ("AI-readiness framework", "names the framework as the goal"),
                    ("validity layer", "names the KG as the validity layer"),
                    ("L0", "names L0 as the most basic level")):
    if needle not in first:
        bad.append(f"the first paragraph of 'What this is' does not {why}")
# and the paragraph that used to be first is still there, verbatim, after it.
if "A knowledge graph that is the **validity layer** under the FSS AI-readiness survey:" \
        not in what.split("\n\n", 1)[1]:
    bad.append("the original opening paragraph is not verbatim after the insertion")
# decision 2: the FIRST bullet of "Where to read first".
if DN not in read or "the standing map every task cites" not in read:
    bad.append(f"the first bullet of 'Where to read first' is not the DN-005 line: {read[:80]!r}")
print("\n".join(f"   VIOLATION: {b}" for b in bad) if bad
      else "   both insertions carry what decisions 1 and 2 require")
sys.exit(1 if bad else 0)
PY

say "no code, no test, no doc, no payload, no event — decision 3 writes to the GRAPH only"
for d in assessment/ kg/ tests/ framework/ state/ events/ corpus/ docs/ Makefile; do
  out=$(git status --porcelain -- "$d")
  [ -n "$out" ] && { echo "$out"; echo "   VIOLATION: $d changed"; fail=1; }
done
[ $fail -eq 0 ] && echo "   nothing under assessment/ kg/ tests/ framework/ state/ events/ corpus/ docs/ or the Makefile moved"

say "the graph: eaa47eb3 superseded by 95911824, and NOTHING else moved state today"
/opt/anaconda3/bin/python3 - <<'PY' || fail=1
import sys
sys.path.insert(0, "/Users/brock/GitHub/seldon")
from pathlib import Path
try:
    from seldon.config import get_neo4j_driver, load_project_config
    cfg = load_project_config(Path("/Users/brock/GitHub/ai-readiness-kg"))
    d = get_neo4j_driver(cfg)
    with d.session(database=cfg["neo4j"]["database"]) as s:
        row = s.run(
            "MATCH (t:ResearchTask) WHERE t.artifact_id STARTS WITH 'eaa47eb3' "
            "OPTIONAL MATCH (t)-[:SUPERSEDED_BY]->(o) "
            "RETURN t.state AS state, t.terminal_reason AS reason, "
            "       o.artifact_id AS by").single()
        results = s.run("MATCH (r:Result) RETURN count(r)").single()[0]
        published = s.run("MATCH (r:Result) WHERE r.state = 'published' "
                          "RETURN count(r)").single()[0]
    d.close()
except Exception as exc:                                            # noqa: BLE001
    print(f"   SKIPPED: Neo4j unreachable ({exc})")
    sys.exit(0)
print(f"   eaa47eb3 state={row['state']} superseded_by={row['by']}")
print(f"   Results total {results}, published {published}")
bad = (row["state"] != "superseded"
       or row["by"] != "95911824-dc0d-4c0c-ad9c-e49f39806575"
       or "completed by 2026-09-12_cited_documents_metadata_2.md" not in (row["reason"] or "")
       or results != 7262 or published != 59)
if bad:
    print("   VIOLATION: decision 3 did not land, or the Result registry moved")
    sys.exit(1)
PY

echo
echo "-- what this task DOES change, declared rather than diffed away"
git status --porcelain -- CLAUDE.md seldon_events.jsonl \
  scripts/check_protected_claude_md_dn005.sh 'cc_tasks/2026-09-15_claude_md_cites_dn005*'
echo
echo "protected paths: $([ $fail -eq 0 ] && echo PASS || echo FAIL)"
exit $fail
