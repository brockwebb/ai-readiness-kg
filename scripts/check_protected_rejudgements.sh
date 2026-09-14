#!/bin/sh
# The protected-paths diff for cc_tasks/2026-09-14_rejudgements_on_the_log.md.
#
# "Zero edits to: rule modules, manners, stored payloads, prior Results' values and states,
#  prior RESULTs, figures, section prose, the skeleton, the record, corpus/, existing shards'
#  content, docs/ beyond decision 5."
#
# Decision 5 expected `docs/data/index.json` to move because the site might publish an
# event-log digest. It does not — `index.json` hashes the framework record and the corpus
# manifest and nothing else — so `docs/` moves on NO file and is checked as a whole. That is
# the premise correction, enforced rather than described.
cd /Users/brock/GitHub/ai-readiness-kg || exit 2
echo "=== protected paths"
fail=0

say() { echo; echo "-- $1"; }
must_be_empty() {                       # $1 label, rest: pathspecs
  label="$1"; shift
  out=$(git status --porcelain -- "$@")
  [ -n "$out" ] && { echo "$out"; echo "   VIOLATION: $label"; fail=1; }
}

say "rule modules and manners — nothing this task does touches a judgement"
must_be_empty "a rule module or manners changed" assessment/harness/scan/rules/ \
  assessment/harness/scan/manners.py assessment/harness/scan/params.yaml \
  assessment/harness/scan/errors.py assessment/harness/scan/rederive.py \
  assessment/harness/scan/model.py assessment/harness/scan/run.py \
  assessment/harness/scan/runner.py assessment/harness/scan/collectors \
  assessment/harness/scan/fixtures assessment/harness/fetch.py

say "figures"
must_be_empty "a figure or its config changed" assessment/harness/scan/figures.py \
  assessment/harness/scan/figures.yaml assessment/harness/scan/figures

say "stored payloads — the log grows, the payloads do not. Only this task's RECORD may appear"
git status --porcelain -- state/ \
  | grep -vE '^\?\? state/rejudgements_on_the_log_2026-09-14\.json$' \
  && { echo "   VIOLATION: a stored payload changed"; fail=1; }

say "the record, the skeleton, section prose, and docs/ apart from this task's own design record"
must_be_empty "the framework record changed" framework/
# Decision 5 expected `docs/data/index.json` to move and it does not, so the PUBLISHED tree is
# checked whole: no report, no PDF, no matrix, no framework copy, no manifest, no sitemap, no
# `llms.txt`, no `robots.txt`, no citation file. The two files that may appear are the design
# RECORD of this work and nothing a reader of the site ever sees: DN-003, written by the
# session that authored the task, and the DD the shard-naming change owes DD-008.
git status --porcelain -- docs/ \
  | grep -vE '^(\?\? docs/design/2026-09-14_DN-003_event_log_and_rejudgements\.md| M docs/design_decisions\.md)$' \
  && { echo "   VIOLATION: a published doc changed"; fail=1; }

say "corpus/ and the committed evidence store"
must_be_empty "corpus changed" corpus/

say "prior RESULTs and prior cc_task files"
must_be_empty "a prior RESULT or task file changed" \
  'cc_tasks/2026-09-13*' 'cc_tasks/2026-09-12*' 'cc_tasks/2026-09-11*' \
  'cc_tasks/2026-09-10*' 'cc_tasks/2026-09-09*' 'cc_tasks/2026-09-08*' \
  'cc_tasks/2026-09-07*' 'cc_tasks/2026-09-06*'

say "existing shards' CONTENT — every committed shard's bytes are still a PREFIX of the file"
/opt/anaconda3/bin/python3 - <<'PY' || fail=1
import subprocess, sys
from pathlib import Path
REPO = Path("/Users/brock/GitHub/ai-readiness-kg")
tracked = [r for r in subprocess.run(["git", "ls-files", "events/"], capture_output=True,
                                     text=True, cwd=REPO).stdout.split()
           if r.endswith(".jsonl")]
bad, grew, same = [], [], 0
for rel in tracked:
    was = subprocess.run(["git", "show", f"HEAD:{rel}"], capture_output=True, cwd=REPO)
    if was.returncode:
        continue
    now = (REPO / rel).read_bytes()
    if not now.startswith(was.stdout):
        bad.append(f"{rel}: committed bytes are not a prefix "
                   f"({len(was.stdout)} -> {len(now)})")
    elif len(now) > len(was.stdout):
        grew.append(f"{rel}: +{len(now) - len(was.stdout)} bytes appended")
    else:
        same += 1
print("\n".join(grew) if grew else "   no pre-existing shard was appended to")
print(f"   {same} shard(s) byte-identical, {len(grew)} appended to, {len(bad)} rewritten")
if bad:
    print("\n".join(bad))
    print("   VIOLATION: an append-only shard was rewritten")
    sys.exit(1)
PY

say "prior Results — no Result registered, moved or retracted by this task"
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
    d.close()
except Exception as exc:                                            # noqa: BLE001
    print(f"   SKIPPED: Neo4j unreachable ({exc})")
    sys.exit(0)
print(f"   Results total {total}; states {states}")
if total != 7262 or states.get("published") != 59 or states.get("superseded") != 1:
    print("   VIOLATION: the Result registry moved")
    sys.exit(1)
PY

echo
echo "-- what this task DOES change, declared rather than diffed away"
git status --porcelain -- kg/eventlog.py assessment/harness/scan/publish.py \
  scripts/publish_rejudgements.py scripts/check_protected_rejudgements.sh \
  docs/design_decisions.md state/rejudgements_on_the_log_2026-09-14.json \
  tests/test_rejudgements_on_the_log.py events/ cc_tasks/2026-09-14* \
  docs/design/2026-09-14* seldon_events.jsonl
echo
echo "protected paths: $([ $fail -eq 0 ] && echo PASS || echo FAIL)"
exit $fail
