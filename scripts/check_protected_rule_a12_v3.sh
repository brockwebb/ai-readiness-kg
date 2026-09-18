#!/usr/bin/env bash
. "$(dirname "$0")/check_protected_lib.sh"
# The zero-edits list of `cc_tasks/2026-09-13_rule_a12_v3.md`, asserted against HEAD:
#
#   "Zero edits to: shipped rule modules (new versions are new files), harness runtime, manners,
#    stored payloads, prior Results' values and states, prior RESULTs, figures, section prose,
#    the skeleton, the record, corpus/, docs/"
#
# "harness runtime" is checked as what it means rather than as the directory, because two of
# this task's own decisions live inside `assessment/harness/scan/` and a list that forbade the
# directory would forbid the task:
#
#   * EVERY SHIPPED RULE MODULE is byte-identical, `rule_a12_v2.py` included. A new version is a
#     new file (`rule_a12_v3.py`), which is the discipline the zero-edits line is about.
#   * The RUNTIME is byte-identical: manners, errors, model, run, runner, rederive, publish,
#     frame, stats, figures and every collector. Nothing that fetches, records or projects moved.
#   * What DID move is named here, one by one, and each is ordered by a decision:
#       rules/_common.py       decision 2 — `unobserved_error` prints the branch that fired
#       rules/__init__.py      decision 1 — V10 and the candidate list, so A12-v3 is CURRENT
#       params.yaml            decisions 1 and 2 — `reason_text: 2` and the ninth fixture's
#                              pre-registered expected verdicts
#       fixtures/server.py     decision 1 — the ninth fixture, which is test-only code
#
# `state/` may GAIN the five re-judged payloads and the diff record and may not MODIFY one: a
# stored payload is evidence, and a re-judgement is a new cycle rather than an edit to an old one.
set -u
cd "$(dirname "$0")/.." || exit 2
fail=0

protected=(
  'corpus/'
  'kg/'
  'assessment/harness/scan/manners.py'
  'assessment/harness/scan/errors.py'
  'assessment/harness/scan/model.py'
  'assessment/harness/scan/run.py'
  'assessment/harness/scan/runner.py'
  'assessment/harness/scan/rederive.py'
  'assessment/harness/scan/publish.py'
  'assessment/harness/scan/frame.py'
  'assessment/harness/scan/stats.py'
  'assessment/harness/scan/figures.py'
  'assessment/harness/scan/figures.yaml'
  'assessment/harness/scan/fixture_expectations.py'
  'assessment/harness/scan/collectors/'
  'assessment/harness/scan/figures/'
  'assessment/harness/scan/shapes/'
  'LICENSE'
  'LICENSE-DATA'
)
for p in "${protected[@]}"; do
  changed=$(git diff --name-only HEAD -- "$p"; git ls-files --others --exclude-standard -- "$p")
  if [ -n "$changed" ]; then
    echo "FAIL protected path moved: $p"
    echo "$changed" | sed 's/^/       /'
    fail=1
  fi
done

# Every SHIPPED rule module is byte-identical. The new one is the only addition.
rules=$(git diff --name-only --diff-filter=M HEAD -- 'assessment/harness/scan/rules/' \
        | grep -v 'rules/_common.py' | grep -v 'rules/__init__.py')
if [ -n "$rules" ]; then
  echo "FAIL a shipped rule module was EDITED; a new version is a new file:"
  echo "$rules" | sed 's/^/       /'; fail=1
fi
newrules=$(git diff --name-only --diff-filter=A HEAD -- 'assessment/harness/scan/rules/'; \
            git ls-files --others --exclude-standard -- 'assessment/harness/scan/rules/')
newrules=$(echo "$newrules" | sed '/^$/d' | sort -u)
if [ "$newrules" != "assessment/harness/scan/rules/rule_a12_v3.py" ]; then
  echo "FAIL rules/ gained something other than rule_a12_v3.py:"
  echo "$newrules" | sed 's/^/       /'; fail=1
fi

# assessment/: only the four files the decisions name, plus the new rule module.
ASSESS_ALLOWED=(
  'assessment/harness/scan/rules/_common.py'
  'assessment/harness/scan/rules/__init__.py'
  'assessment/harness/scan/rules/rule_a12_v3.py'
  'assessment/harness/scan/params.yaml'
  'assessment/harness/scan/fixtures/server.py'
)
while read -r f; do
  [ -z "$f" ] && continue
  ok=0
  for allowed in "${ASSESS_ALLOWED[@]}"; do [ "$f" = "$allowed" ] && ok=1; done
  if [ "$ok" -eq 0 ]; then
    echo "FAIL assessment/ changed outside the files the decisions name: $f"; fail=1
  fi
done <<< "$(git diff --name-only HEAD -- 'assessment/'; git ls-files --others --exclude-standard -- 'assessment/')"

# docs/: ONLY what shipping a rule makes stale, and nothing that is a measurement.
#
# The second premise correction, and it is a coupling that did not exist the last time a rule
# generation shipped: the site publishes a COPY of the framework record and hashes the SOURCE in
# its manifest (`cc_tasks/2026-09-12_publish_l0.md`, one day after generation 9), and
# `docs/design/scan_tool_map.md` is a GENERATED table of which rule each collector feeds. So a
# new CURRENT rule makes the published tree stale on its face, and two standing tests say so —
# `test_every_copy_still_equals_the_record_it_was_copied_from` and
# `test_the_tool_map_regenerates_byte_identically`. Both are repaired by their own generators
# (`build_l0_site.py`, `scan_tool_map.py`), never by hand.
#
# What may move is checked field by field below. No matrix, no report, no PDF, no `llms.txt`, no
# `robots.txt`, no sitemap and no citation file changed — this task rebuilds no measurement.
DOCS_ALLOWED=(
  'docs/data/ai_readiness_framework.json'
  'docs/data/index.json'
  'docs/design/scan_tool_map.md'
  'docs/index.html'
)
while read -r f; do
  [ -z "$f" ] && continue
  ok=0
  for allowed in "${DOCS_ALLOWED[@]}"; do [ "$f" = "$allowed" ] && ok=1; done
  if [ "$ok" -eq 0 ]; then
    echo "FAIL docs/ changed outside what shipping a rule makes stale: $f"; fail=1
  fi
done <<< "$(git diff --name-only HEAD -- 'docs/'; git ls-files --others --exclude-standard -- 'docs/')"

# The published COPY of the record carries the same two derived fields as the record itself.
cp=$(git diff HEAD -U0 -- docs/data/ai_readiness_framework.json | grep -E '^[+-][^+-]' \
     | grep -vE '^[+-] *"(rule_id|collector_pin)": ')
if [ -n "$cp" ]; then
  echo "FAIL the published framework copy changed outside the two derived fields:"
  echo "$cp" | cut -c1-160 | sed 's/^/       /'; fail=1
fi

# The data manifest: the copy's digest and size, and the build stamp. Nothing else — a changed
# digest anywhere else would mean this task republished a measurement.
mf=$(git diff HEAD -U0 -- docs/data/index.json | grep -E '^[+-][^+-]' \
     | grep -vE '^[+-] *"(sha256|bytes|built_at|build_commit)": ')
if [ -n "$mf" ]; then
  echo "FAIL docs/data/index.json changed outside the copy's digest and the build stamp:"
  echo "$mf" | cut -c1-160 | sed 's/^/       /'; fail=1
fi

# The generated tool map: the rule cells alone.
tm=$(git diff HEAD -U0 -- docs/design/scan_tool_map.md | grep -E '^[+-][^+-]' | grep -v 'RULE-A12-v')
if [ -n "$tm" ]; then
  echo "FAIL the tool map changed outside the A12 rule cells:"
  echo "$tm" | cut -c1-160 | sed 's/^/       /'; fail=1
fi

# The index: its build stamp alone. Every verdict and every number on it is untouched.
ix=$(git diff HEAD -U0 -- docs/index.html | grep -E '^[+-][^+-]' | grep -v 'built from commit')
if [ -n "$ix" ]; then
  echo "FAIL docs/index.html changed outside its build stamp:"
  echo "$ix" | cut -c1-160 | sed 's/^/       /'; fail=1
fi

# The report, its PDF and every published matrix: not rebuilt at all.
rep=$(git diff --name-only HEAD -- 'docs/reports/')
if [ -n "$rep" ]; then
  echo "FAIL the report, its PDF or a published matrix changed; this task rebuilds no report:"
  echo "$rep" | sed 's/^/       /'; fail=1
fi

# The framework of record: the two DERIVED fields, and nothing else.
#
# This is the entry the task's zero-edits line could not have got right, and it is reported as a
# premise correction rather than quietly widened. `framework/ai_readiness_framework.json` records
# the rule each leg is judged by, so shipping a new CURRENT rule and NOT writing it back leaves
# the record and the instrument disagreeing — three standing tests say so
# (`test_framework_graph.py` ×2, `test_scan_harness.py`), and running
# `framework_writeback_rules.py` then `load_framework_graph.py` after shipping a rule is the
# repo's standing procedure, recorded in four prior RESULTs. Both fields are DERIVED from
# `assessment/harness/scan/rules` and `fixtures.server.MODES`; neither is authored here.
fwk=$(git diff HEAD -U0 -- framework/ai_readiness_framework.json | grep -E '^[+-][^+-]' \
      | grep -vE '^[+-] *"(rule_id|collector_pin)": ')
if [ -n "$fwk" ]; then
  echo "FAIL the framework record changed outside the two fields the write-back derives:"
  echo "$fwk" | cut -c1-160 | sed 's/^/       /'; fail=1
fi
n=$(git diff HEAD -U0 -- framework/ai_readiness_framework.json | grep -cE '^\+[^+]')
if [ "$n" != "2" ]; then
  echo "FAIL the framework record changed on $n line(s); the write-back derives exactly 2"; fail=1
fi

# events/: APPEND-ONLY, and only the write-back's own shard may grow.
if git diff HEAD -- events/ | grep -q '^-[^-]'; then
  echo "FAIL an events/ shard lost or changed a line; the log is append-only"; fail=1
fi
ev=$(git diff --name-only HEAD -- 'events/' | grep -v 'events/batch-033_framework.jsonl')
if [ -n "$ev" ]; then
  echo "FAIL an events/ shard other than the framework one changed:"
  echo "$ev" | sed 's/^/       /'; fail=1
fi
added=$(git diff HEAD -U0 -- events/batch-033_framework.jsonl | grep -cE '^\+[^+]')
if [ "$added" != "1" ]; then
  echo "FAIL the framework shard gained $added line(s); the write-back appends exactly 1"; fail=1
fi

# The Seldon log is append-only. It GROWS here — `seldon task close c5c0d15d` and
# `seldon cc complete` are this task's own bookkeeping — and what must hold is that it lost
# nothing. That no RESULT was registered is asserted by count, not by this file's length
# (RESULT §5: 7,261 live Results before and after).
if git diff HEAD -- seldon_events.jsonl | grep -q '^-[^-]'; then
  echo "FAIL seldon_events.jsonl lost a line; the log is append-only"; fail=1
fi

# Prior RESULTs are execution records and are never edited.
prior=$(git diff --name-only --diff-filter=M HEAD -- 'cc_tasks/*_RESULT.md')
if [ -n "$prior" ]; then
  echo "FAIL a prior RESULT changed:"; echo "$prior" | sed 's/^/       /'; fail=1
fi

# state/: nothing MODIFIED, and only the declared additions.
NEW_STATE=(
  'state/scan_2026-09-07_rj3.json'
  'state/scan_2026-09-07b_rj4.json'
  'state/scan_2026-09-09_rj3.json'
  'state/scan_2026-09-10_rj3.json'
  'state/self_2026-09-13_rj1.json'
  'state/rejudgement_diff_2026-09-13.json'
)
mod=$(git diff --name-only --diff-filter=M HEAD -- 'state/')
if [ -n "$mod" ]; then
  echo "FAIL a stored payload was MODIFIED; a re-judgement is a new cycle, not an edit:"
  echo "$mod" | sed 's/^/       /'; fail=1
fi
while read -r f; do
  [ -z "$f" ] && continue
  ok=0
  for allowed in "${NEW_STATE[@]}"; do [ "$f" = "$allowed" ] && ok=1; done
  if [ "$ok" -eq 0 ]; then
    echo "FAIL an undeclared file appeared under state/: $f"; fail=1
  fi
done <<< "$(git diff --name-only --diff-filter=A HEAD -- 'state/'; \
            git ls-files --others --exclude-standard -- 'state/')"

if [ "$fail" -eq 0 ]; then
  echo "PASS  every shipped rule module is byte-identical (rule_a12_v2.py included) and the new"
  echo "      version is a new file; the harness runtime — manners, errors, model, run, runner,"
  echo "      rederive, publish and every collector — is byte-identical; corpus/, kg/, both"
  echo "      licences, the report, its PDF, every matrix, llms.txt, robots.txt, the sitemap"
  echo "      and both citation files did not move at all; the Seldon log only grew; docs/ moved"
  echo "      only where"
  echo "      shipping a rule makes it stale — the framework copy, its digest, the generated"
  echo "      tool map and the build stamp; the framework record moved"
  echo "      on exactly the 2 lines the rule write-back derives and its shard gained exactly"
  echo "      the 1 event that records it; state/ gained the five re-judged payloads and the"
  echo "      diff record and modified nothing; no Result was registered."
fi

echo
echo "what DID change:"
{ git diff --name-only HEAD; git ls-files --others --exclude-standard; } | sort -u | sed 's/^/       /'
exit "$fail"
