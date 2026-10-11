#!/usr/bin/env bash
. "$(dirname "$0")/check_protected_lib.sh"
# The write set of `cc_tasks/2026-10-11_evidence_map_carries_discoverability_and_admits_a2_d1_
# a13_standards.md`, asserted against BASE, the commit the session started from (the session
# commits the admission and write-back before regenerating the views, because every view embeds
# the framework record's commit).
#
#   "Byte-identical: every rule, collector, `manners.py`, `score.py`, every payload,
#    `docs/evidence/FROZEN.md`, `reports/`."
#
# Paths that moved and that the task file's write set does not name, each reported in the RESULT:
#
#   * framework/ai_readiness_framework.json, events/batch-033_framework.jsonl,
#     docs/crosswalk/usafacts_operationalization_skeleton.md, scripts/add_candidate_indicator.py,
#     state/framework_roundtrip_2026-09-06.json — binding an admitted source to an indicator IS an
#     evidence cell through the single writer (DN-001 decision 5); there is no other way to do it.
#   * events/batch-024.jsonl — `substrate_converted`, written by `manifest.rebuild()` itself.
#   * scripts/dn001_floor.py, state/dn001_floor_2026-10-11_{before,after}.json — decision 3's
#     before and after floor count, measured by code.
#   * Regenerated views (the write set's "regenerated views"), each by its own generator and each
#     `--check` clean afterwards: docs/brief/ (build_brief_pack: the record commit in every
#     header, the corpus count), docs/catalog/ (build_scan_catalog), docs/figures/
#     (build_figures: fig2), docs/progress/ (framework_progress.py: A2 and D1 now cited),
#     docs/data/ (build_l0_site: the site's copies of the record and manifest),
#     docs/design/mcp_over_the_graph.md (mcp/airkg_doc.py). That last one is the only path under
#     docs/design/ allowed to move.
#   * tests/test_framework_single_writer.py — the pinned count of edges the skeleton does not
#     author: A13's sixth evidence edge (7 -> 8), with a dated comment.
#   * tests/test_concise_report_shipped.py — the shipped report is checked against the claims AT
#     the commit FROZEN.md names, as FROZEN.md says it cites them; read live, the guard failed on
#     the first corpus growth under the frozen report (CL-044).
#
# FOREIGN, not this session's and not committed: state/prior_art_queries.jsonl, appended by the
# prior-art tool another session runs (SQ-010, `"tool": "prior-art/1"`) into this checkout.
set -u
cd "$(dirname "$0")/.." || exit 2
fail=0
BASE=b9311e0f

changed_and_new() {
  { git diff --name-only "$BASE" -- "$@"; git ls-files --others --exclude-standard -- "$@"; } \
    | sed '/^$/d' | sort -u
}

# 1. Untouched outright.
for p in 'assessment/' 'scripts/score.py' 'docs/evidence/FROZEN.md' 'reports/' 'kg/' 'mcp/' \
         'state/scan_*' 'events/cycle-*' 'docs/reports/' 'controls.yaml' 'seldon.yaml' \
         'dixie_evidence.yaml' 'docs/design_decisions.md' \
         'state/seeded_delta_2026-10-11.json' 'docs/research/2026-10-11_seeded_delta.md' \
         'scripts/seeded_delta.py'; do
  moved=$(changed_and_new "$p")
  if [ -n "$moved" ]; then
    echo "FAIL protected path moved: $p"; echo "$moved" | sed 's/^/       /'; fail=1
  fi
done

moved=$(changed_and_new 'docs/design/' | grep -v '^docs/design/mcp_over_the_graph.md$' || true)
if [ -n "$moved" ]; then
  echo "FAIL protected path moved: docs/design/"; echo "$moved" | sed 's/^/       /'; fail=1
fi

# 2. Every path that moved is on the list.
ALLOWED=(
  'cc_tasks/2026-10-11_evidence_map_carries_discoverability_and_admits_a2_d1_a13_standards_RESULT.md'
  'corpus/evidence/decisions.jsonl'
  'corpus/manifest.json'
  'docs/crosswalk/usafacts_operationalization_skeleton.md'
  'docs/evidence/claims.yaml'
  'events/batch-001.jsonl'
  'events/batch-024.jsonl'
  'events/batch-033_framework.jsonl'
  'framework/ai_readiness_framework.json'
  'scripts/add_candidate_indicator.py'
  'scripts/admit_a2_d1_a13_standards.py'
  'scripts/build_evidence_map.py'
  'scripts/check_protected_a2_d1_a13_standards.sh'
  'scripts/dn001_floor.py'
  'scripts/register_seeded_delta_results.py'
  'state/dn001_floor_2026-10-11_after.json'
  'state/dn001_floor_2026-10-11_before.json'
  'state/framework_roundtrip_2026-09-06.json'
  'tests/test_a2_d1_a13_standards.py'
  'docs/design/mcp_over_the_graph.md'
  'tests/test_framework_single_writer.py'
  'tests/test_concise_report_shipped.py'
)
while IFS= read -r path; do
  [ -z "$path" ] && continue
  case "$path" in
    docs/brief/*|docs/catalog/*|docs/figures/*|docs/progress/*|docs/data/*) continue ;;
    state/prior_art_queries.jsonl) echo "NOTE foreign path, not committed: $path"; continue ;;
  esac
  ok=0
  for a in "${ALLOWED[@]}"; do [ "$path" = "$a" ] && ok=1 && break; done
  if [ "$ok" -eq 0 ]; then echo "FAIL path outside the write set moved: $path"; fail=1; fi
done < <(changed_and_new .)

# 3. Event shards and the ledgers are append-only: no line removed or changed.
for f in events/batch-001.jsonl events/batch-024.jsonl events/batch-033_framework.jsonl \
         corpus/evidence/decisions.jsonl seldon_events.jsonl; do
  removed=$(git diff "$BASE" -- "$f" | grep -c '^-[^-]' || true)
  if [ "$removed" -ne 0 ]; then echo "FAIL $f lost or changed $removed line(s)"; fail=1; fi
done

# 4. FROZEN.md names the composite and commit it named, byte for byte.
if ! git diff --quiet "$BASE" -- docs/evidence/FROZEN.md; then
  echo "FAIL docs/evidence/FROZEN.md moved"; fail=1
fi

# 5. Prior RESULTs and task files unchanged.
moved=$(git diff --name-only "$BASE" -- 'cc_tasks/' | grep -v '_standards_RESULT\.md$' || true)
if [ -n "$moved" ]; then echo "FAIL tracked cc_tasks files changed:"; echo "$moved"; fail=1; fi

if [ "$fail" -eq 0 ]; then echo "PROTECTED PATHS: PASS"; else echo "PROTECTED PATHS: FAIL"; fi
exit "$fail"
