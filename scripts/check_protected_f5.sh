#!/bin/sh
# The protected-paths diff for cc_tasks/2026-09-11_f5_membership_through_fallback.md.
#
# "Zero edits to: rule modules, harness runtime (collectors, runner.py, run.py, publish.py,
# rederive.py, model.py, errors.py, manners.py, stats.py, frame.py, probes, fetcher, fixtures,
# params.yaml), stored payloads, prior Results, prior RESULTs, cycle evidence, targets,
# registration records, invariant pins, docs/reports/."
#
# `figures.py` is the one file this task edits under assessment/harness/, and it is edited by
# decision 1. The zero-edits list names the harness RUNTIME file by file and figures.py is not
# among them: it is the presentation layer, and the same reading the previous task recorded.
cd /Users/brock/GitHub/ai-readiness-kg || exit 2
echo "=== protected paths"
fail=0

say() { echo; echo "-- $1"; }
must_be_empty() {
  label="$1"; shift
  out=$(git status --porcelain -- "$@")
  [ -n "$out" ] && { echo "$out"; echo "   VIOLATION: $label"; fail=1; }
}

say "rule modules"
must_be_empty "a rule module changed" assessment/harness/scan/rules/

say "the harness RUNTIME, file by file as the task lists it"
must_be_empty "the harness runtime changed" \
  assessment/harness/scan/collectors assessment/harness/scan/runner.py \
  assessment/harness/scan/run.py assessment/harness/scan/publish.py \
  assessment/harness/scan/rederive.py assessment/harness/scan/model.py \
  assessment/harness/scan/errors.py assessment/harness/scan/manners.py \
  assessment/harness/scan/stats.py assessment/harness/scan/frame.py \
  assessment/harness/scan/params.yaml assessment/harness/scan/fixtures \
  assessment/harness/probes assessment/harness/fetch.py

say "figures.yaml — this task changes no comparison declaration, only the membership test"
must_be_empty "figures.yaml changed" assessment/harness/scan/figures.yaml

say "stored payloads, matrices and registration records — NOTHING under state/ may change"
must_be_empty "a state file changed" state/

say "cycle evidence"
must_be_empty "evidence changed" corpus/evidence/

say "prior RESULTs and prior cc_task files"
must_be_empty "a prior RESULT or task file changed" 'cc_tasks/*_RESULT.md' \
  'cc_tasks/2026-09-10*' 'cc_tasks/2026-09-09*' 'cc_tasks/2026-09-08*' \
  cc_tasks/2026-09-11_rejudge_1_2_3_4_gen9.md \
  cc_tasks/2026-09-11_absence_claims_under_scope_limitation.md \
  cc_tasks/2026-09-11_control_fixture_robots_forbids_product.md

say "docs/reports/ — the report is NOT rebuilt by this task"
must_be_empty "the report changed" docs/reports/

say "the invariant pins — every value pinned before today, unchanged"
/opt/anaconda3/bin/python3 - <<'PY' || fail=1
import ast, subprocess, sys
HEAD = subprocess.run(["git", "show", "HEAD:tests/test_invariants.py"],
                      capture_output=True, text=True).stdout
NOW = open("tests/test_invariants.py").read()

def pins(src):
    out = {}
    for node in ast.parse(src).body:
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            if name in ("ABSENCE_UNDER_PARTIAL_BLINDNESS", "UNDER_V5", "UNDER_V5_ALL_RULES"):
                try:
                    out[name] = ast.literal_eval(node.value)
                except ValueError:
                    out[name] = {k.value: v.value
                                 for k, v in zip(node.value.keys, node.value.values)
                                 if k is not None}
    return out

a, b = pins(HEAD), pins(NOW)
bad = [f"{t}[{c}] was {v}, is {b.get(t, {}).get(c)}"
       for t, was in a.items() for c, v in was.items() if b.get(t, {}).get(c) != v]
if bad:
    print("\n".join(bad)); print("   VIOLATION: an invariant pin was edited"); sys.exit(1)
print(f"   {sum(len(v) for v in a.values())} pin(s) unchanged across {len(a)} table(s); "
      f"decision 5 adds a COMMENT beside one of them and no value")
PY

say "no host was contacted: this task ran no collector, so no payload and no Observation exists"
/opt/anaconda3/bin/python3 - <<'PY' || fail=1
import subprocess, sys
out = subprocess.run(["git", "status", "--porcelain", "--", "state/", "corpus/evidence/"],
                     capture_output=True, text=True).stdout.strip()
if out:
    print(out); print("   VIOLATION: something was measured"); sys.exit(1)
print("   0 changes under state/ and corpus/evidence/ — nothing was fetched or judged")
PY

echo
echo "-- what this task DOES change, declared rather than diffed away"
git status --porcelain -- assessment/harness/scan/figures.py \
  assessment/harness/scan/figures docs/progress scripts/ tests/ cc_tasks/ | head -40
echo
echo "protected paths: $([ $fail -eq 0 ] && echo PASS || echo FAIL)"
exit $fail
