#!/usr/bin/env bash
. "$(dirname "$0")/check_protected_lib.sh"
# The write set of `cc_tasks/2026-09-19_adopter_path.md`, asserted against HEAD.
#
#   "assessment/harness/scan/frames/fss16.yaml (new; the target list moves), run.py, params.yaml
#    (schedule, manners.user_agent unchanged in value), Makefile (scan-now, install-schedule,
#    project), scripts/render_run_report.py (new), scripts/score.py and mcp/ (--no-neo4j),
#    docs/adopt/run_on_your_site.md (new), tests, scripts/check_protected_adopt.sh (new),
#    seldon_events.jsonl, the RESULT. state/, corpus/, docs/reports/ byte-identical."
#
# Paths the write set does not name, each reported in the RESULT §3 with its reason, each listed
# in ALLOWED below and nowhere else:
#
#   * assessment/harness/scan/adopt.py (new): frames, the identity refusal and the out/ layout,
#     read by run.py, the renderer, the installer, score.py and the MCP tools alike.
#   * assessment/harness/scan/model.py: `UNHASHED_KEYS`, so `schedule:` moves no params_hash.
#   * assessment/harness/scan/rederive.py: `main` re-derives an overlaid run under its overlay.
#   * scripts/prescriptions.py: `use_run`, the one seam score.py and the MCP tools point through.
#   * scripts/install_schedule.py (new): what `make install-schedule` runs.
#   * .gitignore: `out/`, where every adopter run writes.
set -u
cd "$(dirname "$0")/.." || exit 2
fail=0

changed_and_new() {
  { git diff --name-only HEAD -- "$@"; git ls-files --others --exclude-standard -- "$@"; } \
    | sed '/^$/d' | sort -u
}

# 1. Byte-identical outright: every stored payload and target DataFile, the corpus, the log,
#    every published matrix and the report tree, the framework record, and the instrument
#    below run.py.
for p in 'kg/' 'assessment/harness/scan/rules/' 'assessment/harness/scan/runner.py' \
         'assessment/harness/scan/manners.py' 'assessment/harness/scan/collectors/' \
         'assessment/harness/scan/fixtures/' 'assessment/harness/scan/spot.py' \
         'assessment/harness/scan/publish.py' \
         'state/' 'corpus/' 'events/' 'docs/reports/' 'docs/data/' 'docs/index.html' \
         'framework/' 'controls.yaml' 'dixie_evidence.yaml' 'seldon.yaml' 'CLAUDE.md'; do
  moved=$(changed_and_new "$p")
  if [ -n "$moved" ]; then
    echo "FAIL protected path moved: $p"; echo "$moved" | sed 's/^/       /'; fail=1
  fi
done

# 2. No task file or earlier RESULT modified.
moved=$(git diff --name-only HEAD -- 'cc_tasks/')
if [ -n "$moved" ]; then
  echo "FAIL a tracked cc_tasks/ file changed:"; echo "$moved" | sed 's/^/       /'; fail=1
fi

# 3. params.yaml: lines ADDED only (the `schedule:` block), the identity unchanged in value, and
#    the parameter hash exactly HEAD's — this project's settings are unchanged (decision 6).
removed=$(git diff -U0 HEAD -- assessment/harness/scan/params.yaml | grep -E '^-[^-]' || true)
if [ -n "$removed" ]; then
  echo "FAIL params.yaml lost or changed a line:"; echo "$removed" | sed 's/^/       /'; fail=1
fi
hashes=$(/opt/anaconda3/bin/python3 - <<'EOF'
import subprocess, sys, yaml
sys.path.insert(0, "assessment/harness")
from scan import load_params
from scan.model import params_hash
head = yaml.safe_load(subprocess.run(["git", "show", "HEAD:assessment/harness/scan/params.yaml"],
                                     capture_output=True, text=True, check=True).stdout)
now = load_params()
print(params_hash(head) == params_hash(now),
      head["manners"]["user_agent"] == now["manners"]["user_agent"],
      now.get("schedule", {}).get("when") == "on_demand")
EOF
)
if [ "$hashes" != "True True True" ]; then
  echo "FAIL params.yaml: hash-equal, user_agent-equal, on_demand = $hashes"; fail=1
fi

# 4. Every path that moved is on the list.
ALLOWED=(
  'assessment/harness/scan/frames/fss16.yaml' 'assessment/harness/scan/run.py'
  'assessment/harness/scan/params.yaml' 'assessment/harness/scan/adopt.py'
  'assessment/harness/scan/model.py' 'assessment/harness/scan/rederive.py'
  'Makefile' '.gitignore'
  'scripts/render_run_report.py' 'scripts/install_schedule.py' 'scripts/score.py'
  'scripts/prescriptions.py' 'scripts/check_protected_adopt.sh'
  'mcp/airkg_tools.py' 'mcp/airkg_server.py' 'docs/design/mcp_over_the_graph.md'
  'docs/adopt/run_on_your_site.md' 'tests/test_adopter_path.py'
  'cc_tasks/2026-09-19_adopter_path_RESULT.md'
)
while IFS= read -r path; do
  [ -z "$path" ] && continue
  ok=0
  for a in "${ALLOWED[@]}"; do [ "$path" = "$a" ] && ok=1 && break; done
  if [ "$ok" = 0 ]; then echo "FAIL not in the write set: $path"; fail=1; fi
done < <({ git diff --name-only HEAD; git ls-files --others --exclude-standard; } | sort -u)

# 5. The runs left nothing in the tree: no adopter payload or compiled frame in state/, and
#    nothing under out/ tracked.
left=$(ls state/scan_my-site* state/frame_* state/spot_two_* 2>/dev/null; git ls-files out/)
if [ -n "$left" ]; then
  echo "FAIL an adopter run left files in the record:"; echo "$left" | sed 's/^/       /'
  fail=1
fi

if [ "$fail" = 0 ]; then echo "PROTECTED PATHS OK"; fi
exit "$fail"
