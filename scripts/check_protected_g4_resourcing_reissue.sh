#!/usr/bin/env bash
. "$(dirname "$0")/check_protected_lib.sh"
# Write-set guard for cc_tasks/2026-09-21_g4_resourcing_reissue.md (spec: the superseded
# 2026-09-20 file's write set; decision 9 was skipped by operator amendment, so CLAUDE.md and
# docs/design/ are protected). Compared against BASE = the commit before the interrupted
# session's WIP commit, so the partial work and this session's are checked together.
set -u
cd "$(dirname "$0")/.." || exit 2
BASE=${BASE:-82090f4}
fail=0
touched=$({ git diff --name-only "$BASE"; git ls-files --others --exclude-standard; } | sed '/^$/d' | sort -u)

# Byte-identical outright: the grounding gate, the scan rules, every stored payload and Finding.
for p in kg/extraction/grounding.py assessment/harness/scan/rules/ state/ CLAUDE.md docs/design/; do
  # docs/design/mcp_over_the_graph.md is GENERATED (mcp/airkg_doc.py) from the record's counts;
  # the write-back moved edges 389 -> 396 and tests/test_mcp_server.py fails until it is
  # regenerated. It is the one docs/design/ path allowed to move.
  moved=$(echo "$touched" | grep -E "^${p}" | grep -v '^docs/design/mcp_over_the_graph\.md$' || true)
  [ -n "$moved" ] && { echo "FAIL protected path moved: $p"; echo "$moved" | sed 's/^/       /'; fail=1; }
done

# Events: committed shards must remain a byte prefix (append-only).
for f in $(git ls-files events/ | grep '\.jsonl$'); do
  git show "$BASE:$f" >/dev/null 2>&1 || continue
  n=$(git show "$BASE:$f" | wc -c)
  if ! cmp -s <(git show "$BASE:$f") <(head -c "$n" "$f"); then echo "FAIL events shard rewritten: $f"; fail=1; fi
done

ALLOWED='^(\.zenodo\.json|CITATION\.cff|corpus/(manifest\.json|evidence/|tools/|kernel/|staging/)|docs/(design/mcp_over_the_graph\.md|crosswalk/usafacts_operationalization_skeleton\.md|data/|index\.html|sitemap\.xml|reports/)|events/|framework/ai_readiness_framework\.json|scripts/(admit_dcat_ap|build_l0_report|build_l0_site|build_report_pdf|measure_grounding_punctuation|check_protected_g4_resourcing_reissue)\.(py|sh)|tests/|seldon_events\.jsonl|seldon\.yaml|cc_tasks/2026-09-21_g4_resourcing_reissue|logs/)'
while IFS= read -r path; do
  echo "$path" | grep -Eq "$ALLOWED" || { echo "FAIL not in the write set: $path"; fail=1; }
done <<< "$touched"
[ "$fail" = 0 ] && echo "PROTECTED PATHS OK"
exit "$fail"
