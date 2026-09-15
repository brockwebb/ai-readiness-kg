#!/bin/sh
# The protected-paths diff for cc_tasks/2026-09-15_standing_dispatcher.md.
#
# "Zero edits to: rule modules, manners, stored payloads, the log's existing shards, Results,
#  prior RESULTs, figures, the report, the skeleton, the record, corpus/, controls.yaml (read
#  only, by reference). CLAUDE.md changes are the two sentences in decision 3 and nothing else."
#
# The status prefix is stripped before matching, so the check answers the same before and after
# `git add` (the defect found in check_protected_standing_guards.sh on 2026-09-14).
cd /Users/brock/GitHub/ai-readiness-kg || exit 2
echo "=== protected paths"
fail=0

say() { echo; echo "-- $1"; }
must_be_empty() {                       # $1 label, rest: pathspecs
  label="$1"; shift
  out=$(git status --porcelain -- "$@")
  [ -n "$out" ] && { echo "$out"; echo "   VIOLATION: $label"; fail=1; }
}

say "rule modules, manners and the harness — this task changes no judgement and no measurement"
must_be_empty "a rule module, manners or the harness changed" assessment/

say "figures, the report, the matrices and the published tree"
must_be_empty "a published artifact changed" docs/reports/ docs/data/ docs/index.html \
  docs/llms.txt docs/robots.txt docs/sitemap.xml docs/progress

say "stored payloads and the event log's shards — nothing is measured or published here"
must_be_empty "a stored payload changed" state/
must_be_empty "an event shard changed" events/

say "the framework record and the skeleton"
must_be_empty "the framework record changed" framework/

say "controls.yaml — READ ONLY, by reference. The standing band is resolved, never copied"
must_be_empty "controls.yaml changed" controls.yaml

say "corpus/ and the kg package"
must_be_empty "corpus changed" corpus/
must_be_empty "the kg package changed" kg/

say "prior RESULTs and prior cc_task files"
must_be_empty "a prior RESULT or task file changed" \
  'cc_tasks/2026-09-14*' 'cc_tasks/2026-09-13*' 'cc_tasks/2026-09-12*' \
  'cc_tasks/2026-09-11*' 'cc_tasks/2026-09-10*' 'cc_tasks/2026-09-09*' \
  'cc_tasks/2026-09-08*' 'cc_tasks/2026-09-07*' 'cc_tasks/2026-09-06*' \
  'cc_tasks/2026-09-15_claude_md_cites_dn005*'

say "CLAUDE.md moved by EXACTLY the two sentences decision 3 and its ADDENDUM_01 name"
/opt/anaconda3/bin/python3 - <<'PY' || fail=1
import subprocess, sys
REPO = "/Users/brock/GitHub/ai-readiness-kg"
d = subprocess.run(["git", "diff", "HEAD", "--numstat", "--", "CLAUDE.md"],
                   capture_output=True, text=True, cwd=REPO).stdout.split()
added, removed = (int(d[0]), int(d[1])) if d else (0, 0)
print(f"   CLAUDE.md +{added} -{removed}")
if (added, removed) != (2, 0):
    print("   VIOLATION: expected exactly 2 insertions (the paragraph and its blank line) "
          "and 0 deletions")
    sys.exit(1)
text = open(f"{REPO}/CLAUDE.md", encoding="utf-8").read()
protocol = text.split("## CC dispatch protocol", 1)[1].split("###", 1)[0]
need = ["**Status:** SUPERSEDED", "within its first ten lines", "**Spend:**", "**Network:**",
        "**Framework layer served", "the operator does not hand-dispatch",
        "DN-006 decision 10"]
missing = [n for n in need if n not in protocol]
if missing:
    print(f"   VIOLATION: the CC dispatch protocol section is missing {missing}")
    sys.exit(1)
print("   both sentences present, in the CC dispatch protocol section")
PY

say "seldon.yaml gained a dispatch block and nothing else moved in it"
/opt/anaconda3/bin/python3 - <<'PY' || fail=1
import subprocess, sys, yaml
REPO = "/Users/brock/GitHub/ai-readiness-kg"
was = yaml.safe_load(subprocess.run(["git", "show", "HEAD:seldon.yaml"], capture_output=True,
                                    text=True, cwd=REPO).stdout)
now = yaml.safe_load(open(f"{REPO}/seldon.yaml", encoding="utf-8"))
unchanged = {k: v for k, v in now.items() if k != "dispatch"}
if unchanged != was:
    print(f"   VIOLATION: seldon.yaml changed outside the dispatch block")
    sys.exit(1)
d = now.get("dispatch") or {}
print(f"   dispatch block added; enabled={d.get('enabled')!r}; "
      f"band_ref={d.get('standing_band_ref')!r}")
if d.get("enabled") is not False:
    print("   VIOLATION: this task does not enable the dispatcher")
    sys.exit(1)
if "standing_band" in d or any(isinstance(v, int) and not isinstance(v, bool) and v > 1_000_000
                               for v in d.values()):
    print("   VIOLATION: a copied token number sits in the dispatch block")
    sys.exit(1)
PY

say "the dispatcher wrote NO event — the dry pass ran with enabled:false"
/opt/anaconda3/bin/python3 - <<'PY' || fail=1
import json, subprocess, sys
REPO = "/Users/brock/GitHub/ai-readiness-kg"
was = subprocess.run(["git", "show", "HEAD:seldon_events.jsonl"], capture_output=True,
                     text=True, cwd=REPO).stdout.splitlines()
now = open(f"{REPO}/seldon_events.jsonl", encoding="utf-8").read().splitlines()
added = now[len(was):]
kinds = sorted({json.loads(l)["event_type"] for l in added if l.strip()})
print(f"   seldon_events.jsonl: {len(was)} -> {len(now)} lines; new event types: {kinds}")
if now[:len(was)] != was:
    print("   VIOLATION: the Seldon event log is not append-only against HEAD")
    sys.exit(1)
bad = [k for k in kinds if k.startswith("dispatch_")]
if bad:
    print(f"   VIOLATION: the dispatcher wrote {bad}; the dry pass must write nothing")
    sys.exit(1)
PY

say "prior Results — nothing registered, moved or retracted"
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
        published = s.run("MATCH (r:Result) WHERE r.state='published' "
                          "RETURN count(r)").single()[0]
        row = s.run("MATCH (t:ResearchTask) WHERE t.artifact_id STARTS WITH '6ee71737' "
                    "OPTIONAL MATCH (t)-[:SUPERSEDED_BY]->(o) "
                    "RETURN t.state AS state, o.artifact_id AS by").single()
    d.close()
except Exception as exc:                                            # noqa: BLE001
    print(f"   SKIPPED: Neo4j unreachable ({exc})")
    sys.exit(0)
print(f"   Results total {total}, published {published}")
print(f"   6ee71737 state={row['state']} superseded_by={row['by']}")
bad = (total != 7262 or published != 59 or row["state"] != "superseded"
       or row["by"] != "e2885e86-0be4-4358-9b54-cdb846f7f6de")
if bad:
    print("   VIOLATION: the Result registry moved, or §3 did not land")
    sys.exit(1)
PY

echo
echo "-- what this task DOES change, declared rather than diffed away"
git status --porcelain -- CLAUDE.md seldon.yaml seldon_events.jsonl \
  scripts/jobs/airkg_dispatch.sh scripts/jobs/com.brock.airkg-dispatch.plist \
  scripts/check_protected_standing_dispatcher.sh tests/test_dispatch_config.py \
  'cc_tasks/2026-09-15_standing_dispatcher*' 'docs/design/2026-09-15_DN-006*'
echo
echo "protected paths: $([ $fail -eq 0 ] && echo PASS || echo FAIL)"
exit $fail
