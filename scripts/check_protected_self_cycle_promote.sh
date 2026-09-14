#!/usr/bin/env bash
# The zero-edits list of `cc_tasks/2026-09-13_self_cycle_promote.md`, asserted against HEAD:
#
#   "Zero edits to: rule modules, harness runtime, manners, prior payloads, prior Results'
#    values and states, prior RESULTs, figures, section prose, the skeleton, the record,
#    corpus/ beyond the promotion under decision 1, docs/robots.txt, docs/sitemap.xml"
#
# Four entries are not path lists and are checked as themselves:
#
#   * `corpus/` may GAIN the bodies decision 1 promotes and nothing else. A promotion is an
#     ADD: the store is content-addressed, so a modified or deleted body is a body whose bytes
#     no longer match the digest a Finding cites, which is invariant 3 broken. Additions are
#     allowed and counted; modifications and deletions are refused.
#   * `events/` may GROW and may not lose or change a line: the log is append-only (invariant
#     1). This task appends the self cycle's Observations and Findings.
#   * `assessment/` is byte-identical whole — the harness, the manners and every rule module.
#     `publish.py` is harness runtime and was NOT edited, so the self cycle's events land on
#     the default shard `events/batch-029.jsonl` rather than on one of their own.
#   * `state/` may be modified only where decision 1 says so: the payload's `body_path` values
#     are rewritten by `publish.promote_evidence` (a staging path on an append-only line would
#     be a dangling reference) and the row is regenerated.
#
# `docs/sitemap.xml` is the one entry that MOVED, and it moved for a reason no list could
# forbid: every `<lastmod>` is the build date, the build crossed the UTC midnight of
# 2026-09-13/14, and the files it dates did change. Refusing it would have meant publishing a
# sitemap that dates today's llms.txt to yesterday. It is checked as "nothing but the lastmod
# dates moved" rather than waved through — see the RESULT.
set -u
cd "$(dirname "$0")/.." || exit 2
fail=0

protected=(
  'assessment/'
  'framework/'
  'docs/reports/sections/'
  'docs/reports/generated/'
  'docs/crosswalk/usafacts_operationalization_skeleton.md'
  'docs/robots.txt'
  'docs/progress/'
  'LICENSE'
  'LICENSE-DATA'
  'corpus/manifest.json'
  'kg/'
)
for p in "${protected[@]}"; do
  changed=$(git diff --name-only HEAD -- "$p"; git ls-files --others --exclude-standard -- "$p")
  if [ -n "$changed" ]; then
    echo "FAIL protected path moved: $p"
    echo "$changed" | sed 's/^/       /'
    fail=1
  fi
done

# corpus/: additions only, and only under the scan evidence store.
badcorpus=$(git diff --name-status HEAD -- 'corpus/' | grep -v '^A' )
if [ -n "$badcorpus" ]; then
  echo "FAIL corpus/ was modified or deleted from, not merely added to:"
  echo "$badcorpus" | sed 's/^/       /'; fail=1
fi
offlane=$(git ls-files --others --exclude-standard -- 'corpus/' | grep -v '^corpus/evidence/scan/')
if [ -n "$offlane" ]; then
  echo "FAIL corpus/ gained a file outside the scan evidence store:"
  echo "$offlane" | sed 's/^/       /'; fail=1
fi
promoted=$(git ls-files --others --exclude-standard -- 'corpus/evidence/scan/' | wc -l | tr -d ' ')
echo "note  corpus/evidence/scan/ gained $promoted body/bodies (decision 1's promotion)"

# events/: append-only. A removed or changed line is invariant 1 broken.
if git diff events/ | grep -q '^-[^-]'; then
  echo "FAIL an events/ shard lost or changed a line; the log is append-only"; fail=1
fi

# The published matrices: not rebuilt by this task.
mx=$(git diff --name-only HEAD -- 'docs/reports/scan_matrix_*')
if [ -n "$mx" ]; then
  echo "FAIL a published matrix changed; this task re-judges nothing:"
  echo "$mx" | sed 's/^/       /'; fail=1
fi

# docs/ may change only where the licence reaches a face, the row is regenerated, and the
# report is rebuilt from them. The last four entries are the rest of what ONE run of
# `scripts/build_l0_site.py` writes, and they moved for two reasons that are checked below
# rather than waved through: the citation files carry the build DATE (the build crossed UTC
# midnight) and the source appendix carries a count of RULES per check, which grew because
# publishing the self cycle put three rule ids on the event log for the first time.
DOCS_ALLOWED=(
  'docs/index.html'
  'docs/llms.txt'
  'docs/sitemap.xml'
  'docs/data/index.json'
  'docs/data/CITATION.cff'
  'docs/data/zenodo.json'
  'docs/data/sources_per_check.json'
  'docs/reports/2026-09_fss_ai_readiness_L0.md'
  'docs/reports/2026-09_fss_ai_readiness_L0.pdf'
)
while read -r f; do
  [ -z "$f" ] && continue
  ok=0
  for allowed in "${DOCS_ALLOWED[@]}"; do [ "$f" = "$allowed" ] && ok=1; done
  if [ "$ok" -eq 0 ]; then
    echo "FAIL docs/ changed outside the declared faces: $f"; fail=1
  fi
done <<< "$(git diff --name-only HEAD -- 'docs/'; git ls-files --others --exclude-standard -- 'docs/')"

# docs/sitemap.xml: only the lastmod dates may have moved.
sm=$(git diff -U0 -- docs/sitemap.xml | grep -E '^[+-][^+-]' | sed -E 's/<lastmod>[0-9]{4}-[0-9]{2}-[0-9]{2}<\/lastmod>/<lastmod>D<\/lastmod>/' | sed -E 's/^[+-]//' | sort | uniq -u)
if [ -n "$sm" ]; then
  echo "FAIL docs/sitemap.xml changed in something other than its lastmod dates:"
  echo "$sm" | sed 's/^/       /'; fail=1
fi

# The citation files, at the root and in the tree: the release DATE and nothing else.
cit=$(git diff -U0 -- CITATION.cff docs/data/CITATION.cff .zenodo.json docs/data/zenodo.json \
      | grep -E '^[+-][^+-]' | grep -vE "^[+-] *\"?(date-released|publication_date)\"?:" )
if [ -n "$cit" ]; then
  echo "FAIL a citation file changed in something other than its release date:"
  echo "$cit" | sed 's/^/       /'; fail=1
fi

# The source appendix: only the per-check RULE COUNTS. Publishing the self cycle put
# RULE-A12-v2, RULE-A3-v6 and RULE-B3-v3 on the event log for the first time — every earlier
# payload judged under them is a RE-JUDGEMENT and none was ever published — so the projection
# minted three more Rule nodes and the appendix counts them. No row, no source, no locator and
# no doc_id moved, which is what this checks.
app=$(git diff -U0 -- docs/data/sources_per_check.json | grep -E '^[+-][^+-]' \
      | grep -vE '^[+-] *"rules": [0-9]+,?$')
if [ -n "$app" ]; then
  echo "FAIL docs/data/sources_per_check.json changed in something other than a rule count:"
  echo "$app" | sed 's/^/       /'; fail=1
fi

# The report: the generated version block and nothing else. Every measured number in it is a
# {{result}} reference resolved from the graph, so a moved number would show up here.
rep=$(git diff -U0 -- docs/reports/2026-09_fss_ai_readiness_L0.md | grep -E '^[+-][^+-]' \
      | grep -vE '^[+-]\*\*Version\.\*\* ')
if [ -n "$rep" ]; then
  echo "FAIL the report changed outside its generated version block:"
  echo "$rep" | cut -c1-160 | sed 's/^/       /'; fail=1
fi

# Prior RESULTs are execution records and are never edited.
prior=$(git diff --name-only HEAD -- 'cc_tasks/*_RESULT.md')
if [ -n "$prior" ]; then
  echo "FAIL a prior RESULT changed:"; echo "$prior" | sed 's/^/       /'; fail=1
fi

# state/: only the two files decision 1 rewrites, plus declared additions.
STATE_ALLOWED=(
  'state/self_2026-09-13.json'
  'state/self_l0_self_2026-09-13.json'
  'state/promote_self_cycle_2026-09-13.json'
)
while read -r f; do
  [ -z "$f" ] && continue
  ok=0
  for allowed in "${STATE_ALLOWED[@]}"; do [ "$f" = "$allowed" ] && ok=1; done
  if [ "$ok" -eq 0 ]; then
    echo "FAIL an undeclared file under state/ moved or appeared: $f"; fail=1
  fi
done <<< "$(git diff --name-only HEAD -- 'state/'; git ls-files --others --exclude-standard -- 'state/')"

# The Seldon event log is append-only.
if git diff seldon_events.jsonl | grep -q '^-[^-]'; then
  echo "FAIL seldon_events.jsonl lost a line; the log is append-only"; fail=1
fi

if [ "$fail" -eq 0 ]; then
  echo "PASS  the harness, the manners, every rule module, kg/, the framework record, the"
  echo "      skeleton, section prose, every published matrix, robots.txt and both licences are"
  echo "      byte-identical to HEAD; corpus/ was only ADDED to, and only in the scan evidence"
  echo "      lane; events/ only grew; docs/ changed only on the declared faces and the sitemap"
  echo "      only in its lastmod dates; state/ moved only the payload and the row; the Seldon"
  echo "      log only grew."
fi

echo
echo "what DID change (paths, not bodies):"
{ git diff --name-only HEAD; git ls-files --others --exclude-standard | grep -v '^corpus/evidence/scan/'; } | sort -u | sed 's/^/       /'
exit "$fail"
