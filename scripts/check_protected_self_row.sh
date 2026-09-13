#!/usr/bin/env bash
# The zero-edits list of `cc_tasks/2026-09-13_self_row.md`, asserted against HEAD:
#
#   "Zero edits to: rule modules, harness runtime, manners, stored payloads, prior Results,
#    prior RESULTs, figures, section prose, the skeleton, the record, corpus/, docs/robots.txt,
#    docs/llms.txt, docs/sitemap.xml"
#
# Four entries are not path lists and are checked as themselves:
#
#   * `corpus/` IS byte-identical and gains nothing. That is worth saying explicitly, because a
#     cycle normally promotes its captured bodies into `corpus/evidence/scan/` and this one
#     deliberately did not: promotion is the one thing the zero-edits line forbids, so the self
#     cycle's bodies stay in the gitignored staging root, its Observations and Findings are NOT
#     written to `events/`, and the row's own record says so per read
#     (`body_in_committed_store`). See the RESULT; a task authorised to touch `corpus/` promotes
#     and publishes them together, which is the only order `publish.py` permits.
#   * DECISION 3, the whole point of the row: `docs/` may not change in a way that would IMPROVE
#     a verdict after it was measured. `robots.txt`, `llms.txt` and `sitemap.xml` are byte-
#     identical, and `docs/index.html` may change only by RENDERING the row.
#   * `assessment/` is byte-identical whole — the harness, the manners and every rule module.
#     The self cycle ran with its cycle identity overlaid IN MEMORY
#     (`scripts/run_self_scan.py`), precisely so `params.yaml` would not have to move.
#   * `state/` may not be MODIFIED; it may gain exactly the files in NEW_STATE.
set -u
cd "$(dirname "$0")/.." || exit 2
fail=0

protected=(
  'assessment/'
  'corpus/'
  'events/'
  'framework/'
  'docs/reports/sections/'
  'docs/reports/generated/'
  'docs/crosswalk/usafacts_operationalization_skeleton.md'
  'docs/robots.txt'
  'docs/llms.txt'
  'docs/sitemap.xml'
  'docs/progress/'
  'docs/reports/2026-09_fss_ai_readiness_L0.md'
  'docs/reports/2026-09_fss_ai_readiness_L0.pdf'
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

# The published matrices: not rebuilt by this task at all.
mx=$(git diff --name-only HEAD -- 'docs/reports/scan_matrix_*')
if [ -n "$mx" ]; then
  echo "FAIL a published matrix changed; this task reports a scan of ONE host and rebuilds none:"
  echo "$mx" | sed 's/^/       /'; fail=1
fi

# docs/ may change only where the row is rendered and where the declaration names its cycle.
DOCS_ALLOWED=(
  'docs/index.html'
  'docs/data/index.json'
  'docs/reports/publication.yaml'
)
while read -r f; do
  [ -z "$f" ] && continue
  ok=0
  for allowed in "${DOCS_ALLOWED[@]}"; do [ "$f" = "$allowed" ] && ok=1; done
  if [ "$ok" -eq 0 ]; then
    echo "FAIL docs/ changed outside rendering the row: $f"; fail=1
  fi
done <<< "$(git diff --name-only HEAD -- 'docs/'; git ls-files --others --exclude-standard -- 'docs/')"

# Prior RESULTs are execution records and are never edited.
prior=$(git diff --name-only HEAD -- 'cc_tasks/*_RESULT.md')
if [ -n "$prior" ]; then
  echo "FAIL a prior RESULT changed:"; echo "$prior" | sed 's/^/       /'; fail=1
fi

# state/: no modification, and only the declared additions.
NEW_STATE=(
  'state/scan_targets_self_2026-09-13.json'
  'state/self_2026-09-13.json'
  'state/self_l0_self_2026-09-13.json'
  'state/live_host_2026-09-13.json'
)
mod=$(git diff --name-only HEAD -- 'state/')
if [ -n "$mod" ]; then
  echo "FAIL a stored payload was MODIFIED:"; echo "$mod" | sed 's/^/       /'; fail=1
fi
while read -r f; do
  [ -z "$f" ] && continue
  ok=0
  for allowed in "${NEW_STATE[@]}"; do [ "$f" = "$allowed" ] && ok=1; done
  if [ "$ok" -eq 0 ]; then
    echo "FAIL an undeclared file appeared under state/: $f"; fail=1
  fi
done <<< "$(git ls-files --others --exclude-standard -- 'state/')"

# The two paths whose ABSENCE is the decision of record, carried forward from the previous task.
for ghost in 'state/scan_matrix_2026-09-10.json' 'state/scan_matrix_tierc_2026-09-10.json'; do
  if [ -e "$ghost" ]; then
    echo "FAIL $ghost EXISTS; its absence is a recorded decision (materialized: false)"; fail=1
  fi
done

# The Seldon event log is append-only: this task registers six Results and two artifacts.
if git diff seldon_events.jsonl | grep -q '^-[^-]'; then
  echo "FAIL seldon_events.jsonl lost a line; the log is append-only"; fail=1
fi

if [ "$fail" -eq 0 ]; then
  echo "PASS  the harness, the manners, every rule module, corpus/, events/, the record, the"
  echo "      skeleton, section prose, the report and its PDF, every published matrix,"
  echo "      robots.txt, llms.txt, the sitemap and both licences are byte-identical to HEAD;"
  echo "      docs/ changed only by rendering the measured row; state/ gained only the declared"
  echo "      files and lost nothing; the Seldon log only grew. No verdict was improved after"
  echo "      it was measured, because nothing it measures moved."
fi

echo
echo "what DID change:"
{ git diff --name-only HEAD; git ls-files --others --exclude-standard; } | sort -u | sed 's/^/       /'
exit "$fail"
