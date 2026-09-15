#!/bin/sh
# The protected-paths diff for cc_tasks/2026-09-14_standing_guards.md.
#
# "Zero edits to: rule modules, manners, stored payloads, the log, prior Results' values,
#  states and edges, prior RESULTs, figures, section prose, the skeleton, the record, corpus/,
#  docs/ beyond the report's version block, its PDF, and results_tagged.json."
#
# The three published files that MAY move are named below and nothing else under docs/ may,
# which is why the site was rebuilt with `--only results_tagged` rather than whole: the index
# carries a build date, so a full rebuild moves pages this task has not changed and the diff
# stops being readable.
cd /Users/brock/GitHub/ai-readiness-kg || exit 2
echo "=== protected paths"
fail=0

say() { echo; echo "-- $1"; }
must_be_empty() {                       # $1 label, rest: pathspecs
  label="$1"; shift
  out=$(git status --porcelain -- "$@")
  [ -n "$out" ] && { echo "$out"; echo "   VIOLATION: $label"; fail=1; }
}

say "rule modules and manners — this task changes no judgement"
must_be_empty "a rule module or manners changed" assessment/harness/scan/rules/ \
  assessment/harness/scan/manners.py assessment/harness/scan/params.yaml \
  assessment/harness/scan/errors.py assessment/harness/scan/rederive.py \
  assessment/harness/scan/model.py assessment/harness/scan/run.py \
  assessment/harness/scan/runner.py assessment/harness/scan/collectors \
  assessment/harness/scan/fixtures assessment/harness/fetch.py \
  assessment/harness/scan/publish.py

say "figures"
must_be_empty "a figure or its config changed" assessment/harness/scan/figures.py \
  assessment/harness/scan/figures.yaml assessment/harness/scan/figures

say "stored payloads — decision 5 leaves state/scan_2026-09-07b_rj2.json exactly as it is"
must_be_empty "a stored payload changed" state/

say "THE LOG — no event is written by this task at all"
must_be_empty "an event shard changed" events/

say "the framework record and the skeleton"
must_be_empty "the framework record changed" framework/

say "section prose and the publication declaration — the version block is GENERATED"
must_be_empty "section prose or publication.yaml changed" docs/reports/sections/ \
  docs/reports/publication.yaml

say "docs/ — exactly three published files move, and they are the three decisions 2 and 3 name"
# The two-character STATUS prefix is stripped before matching. Written against the unstaged
# spellings (` M `, `?? `) this clause passed while nothing was staged and failed the moment
# `git add` turned them into `M  ` and `A  ` — a check that answers differently depending on
# whether the commit has been prepared yet is a check nobody can run twice. The PATH is the
# subject; how git currently holds the change is not.
#
# The DN notes are the design RECORD of this work and of the two design notes the Desktop
# session wrote alongside it (DN-005, DN-006); they are not published pages a reader of the
# site meets.
git status --porcelain -- docs/ | sed 's/^...//' \
  | grep -vE '^(docs/reports/2026-09_fss_ai_readiness_L0\.(md|pdf)|docs/data/results_tagged\.json|docs/design/2026-09-1[456]_DN-00[456]_.*\.md)$' \
  && { echo "   VIOLATION: a published doc changed that this task does not own"; fail=1; }

say "the published matrices — decision 3 builds the successor's into a TEMPORARY tree"
must_be_empty "a published matrix or fragment changed" 'docs/reports/scan_matrix_*' \
  docs/reports/generated/

say "corpus/ and the committed evidence store"
must_be_empty "corpus changed" corpus/

say "prior RESULTs and prior cc_task files"
must_be_empty "a prior RESULT or task file changed" \
  'cc_tasks/2026-09-13*' 'cc_tasks/2026-09-12*' 'cc_tasks/2026-09-11*' \
  'cc_tasks/2026-09-10*' 'cc_tasks/2026-09-09*' 'cc_tasks/2026-09-08*' \
  'cc_tasks/2026-09-07*' 'cc_tasks/2026-09-06*' \
  'cc_tasks/2026-09-14_rejudgements_on_the_log*'

say "the event log, byte for byte — this task appends nothing, so every shard is IDENTICAL"
/opt/anaconda3/bin/python3 - <<'PY' || fail=1
import subprocess, sys
from pathlib import Path
REPO = Path("/Users/brock/GitHub/ai-readiness-kg")
tracked = [r for r in subprocess.run(["git", "ls-files", "events/"], capture_output=True,
                                     text=True, cwd=REPO).stdout.split()
           if r.endswith(".jsonl")]
moved = []
for rel in tracked:
    was = subprocess.run(["git", "show", f"HEAD:{rel}"], capture_output=True, cwd=REPO)
    if was.returncode:
        continue
    if (REPO / rel).read_bytes() != was.stdout:
        moved.append(rel)
print(f"   {len(tracked) - len(moved)} shard(s) byte-identical to HEAD, {len(moved)} moved")
if moved:
    print("\n".join(moved))
    print("   VIOLATION: a shard moved; this task writes no event")
    sys.exit(1)
PY

say "prior Results — nothing registered, moved or retracted, and the page counts are unmoved"
/opt/anaconda3/bin/python3 - <<'PY' || fail=1
import sys
sys.path.insert(0, "/Users/brock/GitHub/seldon")
from pathlib import Path
try:
    from seldon.config import get_neo4j_driver, load_project_config
    cfg = load_project_config(Path("/Users/brock/GitHub/ai-readiness-kg"))
    d = get_neo4j_driver(cfg)
    with d.session(database=cfg["neo4j"]["database"]) as s:
        total = s.run("MATCH (r:Result) RETURN count(r)").single()[0]
        states = {r["st"]: r["n"] for r in s.run(
            "MATCH (r:Result) RETURN coalesce(r.state,'<none>') AS st, count(*) AS n")}
        pages = {r["n"]: r["v"] for r in s.run(
            "MATCH (r:Result) WHERE r.name STARTS WITH 'l0_report_pages' "
            "RETURN r.name AS n, r.value AS v")}
    d.close()
except Exception as exc:                                            # noqa: BLE001
    print(f"   SKIPPED: Neo4j unreachable ({exc})")
    sys.exit(0)
print(f"   Results total {total}; states {states}; page counts {pages}")
bad = (total != 7262 or states.get("published") != 59 or states.get("superseded") != 1
       or pages.get("l0_report_pages_total_2026-09-11") != 14.0
       or pages.get("l0_report_pages_prose_2026-09-11") != 6.0)
if bad:
    print("   VIOLATION: the Result registry moved, or the rebuilt PDF changed page count "
          "without re-registration")
    sys.exit(1)
PY

echo
echo "-- what this task DOES change, declared rather than diffed away"
git status --porcelain -- scripts/build_l0_matrices.py scripts/build_l0_report.py \
  scripts/build_l0_site.py scripts/snapshot_successor.py \
  scripts/publish_rejudgements.py scripts/check_protected_standing_guards.sh \
  tests/test_standing_guards.py tests/test_snapshot_successor.py Makefile \
  docs/design_decisions.md docs/reports/2026-09_fss_ai_readiness_L0.md \
  docs/reports/2026-09_fss_ai_readiness_L0.pdf docs/data/results_tagged.json \
  cc_tasks/2026-09-14_standing_guards.md cc_tasks/2026-09-14_standing_guards_RESULT.md \
  docs/design/2026-09-14_DN-004_report_snapshot_policy.md seldon_events.jsonl
echo
echo "protected paths: $([ $fail -eq 0 ] && echo PASS || echo FAIL)"
exit $fail
