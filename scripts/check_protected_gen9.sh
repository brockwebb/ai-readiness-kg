#!/bin/sh
# The protected-paths diff for cc_tasks/2026-09-11_rejudge_1_2_3_4_gen9.md.
# "Zero edits to: rule modules, harness, stored payloads, prior Results, prior RESULTs, cycle
# evidence, targets, fixtures, docs/reports/, the historical invariant pins."
cd /Users/brock/GitHub/ai-readiness-kg || exit 2
echo "=== protected paths"
fail=0

say() { echo; echo "-- $1"; }
must_be_empty() {                       # $1 label, rest: pathspecs
  label="$1"; shift
  out=$(git status --porcelain -- "$@")
  [ -n "$out" ] && { echo "$out"; echo "   VIOLATION: $label"; fail=1; }
}

say "rule modules — no shipped rule module may change, and none is added here"
must_be_empty "rule modules changed" assessment/harness/scan/rules/

say "stored payloads — only the four new cycles and their matrices may appear"
git status --porcelain -- state/ | grep -vE 'state/(scan_(2026-09-07_rj2|2026-09-07b_rj3|2026-09-09_rj2|2026-09-10_rj2)\.json|scan_matrix(_tierc)?_(2026-09-07_rj2|2026-09-07b_rj3|2026-09-09_rj2|2026-09-10_rj2)\.json|rejudgement_diff_2026-09-11\.json|rejudgement_registration_2026-09-11\.json|l0_rejudged_registration_2026-09-11\.json|figure_inputs_registration_2026-09-11\.json)' \
  && { echo "   VIOLATION: a state file outside this task's set changed"; fail=1; }

say "prior RESULTs and prior cc_task files"
must_be_empty "a prior RESULT or task file changed" 'cc_tasks/*_RESULT.md' \
  'cc_tasks/2026-09-10*' 'cc_tasks/2026-09-09*' 'cc_tasks/2026-09-08*'

say "cycle evidence"
must_be_empty "evidence changed" corpus/evidence/

say "targets"
must_be_empty "targets changed" state/scan_targets_2026-09.json \
  state/scan_targets_fss_2026-09.json state/scan_targets_fss_2026-09_v5.json

say "docs/reports/ — the report is NOT rebuilt by this task"
must_be_empty "the report changed" docs/reports/

say "the eight control fixtures"
must_be_empty "a fixture changed" assessment/harness/scan/fixtures/

say "params.yaml and errors.py"
must_be_empty "params or the error map changed" assessment/harness/scan/params.yaml \
  assessment/harness/scan/errors.py

say "the harness runtime — collectors, runner, run, publish, rederive, model"
must_be_empty "the harness runtime changed" \
  assessment/harness/scan/collectors assessment/harness/scan/runner.py \
  assessment/harness/scan/run.py assessment/harness/scan/publish.py \
  assessment/harness/scan/rederive.py assessment/harness/scan/model.py \
  assessment/harness/scan/manners.py assessment/harness/scan/stats.py \
  assessment/harness/scan/frame.py assessment/harness/scan/errors.py \
  assessment/harness/probes assessment/harness/fetch.py

say "the historical invariant pins — the twelve cycles pinned before today, value for value"
/opt/anaconda3/bin/python3 - <<'PY' || fail=1
import ast, subprocess, sys
HEAD = subprocess.run(["git", "show", "HEAD:tests/test_invariants.py"],
                      capture_output=True, text=True).stdout
NOW = open("tests/test_invariants.py").read()

def pins(src):
    tree = ast.parse(src)
    out = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            if name in ("ABSENCE_UNDER_PARTIAL_BLINDNESS", "UNDER_V5", "UNDER_V5_ALL_RULES"):
                try:
                    out[name] = ast.literal_eval(node.value)
                except ValueError:
                    out[name] = {k.value: v.value for k, v in zip(node.value.keys,
                                                                 node.value.values)
                                 if k is not None}
    return out

a, b = pins(HEAD), pins(NOW)
bad = []
for table, was in a.items():
    now = b.get(table, {})
    for cycle, value in was.items():
        if now.get(cycle) != value:
            bad.append(f"{table}[{cycle}] was {value}, is {now.get(cycle)}")
if bad:
    print("\n".join(bad))
    print("   VIOLATION: a historical invariant pin was edited")
    sys.exit(1)
print(f"   {sum(len(v) for v in a.values())} historical pin(s) unchanged across "
      f"{len(a)} table(s)")
PY

echo
echo "-- what this task DOES change, declared rather than diffed away"
git status --porcelain -- assessment/harness/scan/figures.py assessment/harness/scan/figures.yaml \
  scripts/ tests/ Makefile docs/progress assessment/harness/scan/figures
echo
echo "protected paths: $([ $fail -eq 0 ] && echo PASS || echo FAIL)"
exit $fail
