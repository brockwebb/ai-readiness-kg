#!/usr/bin/env bash
. "$(dirname "$0")/check_protected_lib.sh"
# The write set of `cc_tasks/2026-10-07_DCAT-004_v2_plain_language_brief_and_verdict.md`,
# asserted against HEAD.
#
# Decision 1 admits SDMX 3.1 Section 2 and DDI-CDI 1.0 and declines UNECE GSIM (the corpus
# ledger, the manifest projection, the admission shard), extracts the two (the extraction
# shards, their raw responses, the run's state file) and runs the DD-029 acceptance sample (the
# probe-judge shard and the probe's raw responses). Decisions 2 to 7 write the brief's report
# directory, the `dcat_brief_*` scripts, the extended evidence script and the new test.
# Decision 8 appends to the evidence map. The views every generator regenerates from the
# corpus count follow the admission, by generator. Byte-identical: the FAQ's report directory,
# every rule and matrix, and the framework record.
set -u
cd "$(dirname "$0")/.." || exit 2
fail=0

changed_and_new() {
  { git diff --name-only HEAD -- "$@"; git ls-files --others --exclude-standard -- "$@"; } \
    | sed '/^$/d' | sort -u
}

allowed() {
  case "$1" in
    reports/dcat_us_3_brief/*) return 0 ;;
    scripts/dcat_brief_*.py|scripts/dcat_faq_evidence.py|scripts/check_protected_dcat_004.sh) return 0 ;;
    tests/test_dcat_brief.py) return 0 ;;
    corpus/evidence/decisions.jsonl|corpus/manifest.json) return 0 ;;
    events/batch-001.jsonl|events/batch-009_probe_judge.jsonl|events/batch-022.jsonl|events/batch-023.jsonl) return 0 ;;
    events/raw/bulk_v038/ddi-cdi-1-0-specification.*|events/raw/bulk_v038/sdmx-3-1-section-2-information-model.*) return 0 ;;
    events/raw/burn_dcat_us_3_brief_2026-10-07_decompose/*|events/raw/burn_dcat_us_3_brief_2026-10-07_judge/*) return 0 ;;
    state/spend_ledger.jsonl|state/dcat_us_3_brief_extraction_2026-10-07.json) return 0 ;;
    docs/evidence/claims.yaml) return 0 ;;
    docs/brief/*|docs/data/*|docs/evidence/*|docs/figures/*|docs/catalog/*) return 0 ;;
    docs/reports/2026-09_fss_ai_readiness_L0.*|docs/reports/generated/*) return 0 ;;
    docs/index.html|docs/llms.txt|docs/sitemap.xml|mcp/*.md) return 0 ;;
    cc_tasks/2026-10-07_DCAT-004_v2_plain_language_brief_and_verdict_RESULT.md) return 0 ;;
    seldon_events.jsonl) return 0 ;;
  esac
  return 1
}

while IFS= read -r path; do
  [ -z "$path" ] && continue
  allowed "$path" || { echo "FAIL path outside the write set moved: $path"; fail=1; }
done < <(changed_and_new .)

# Byte-identical (the task's own list).
for p in reports/dcat_us_3_faq framework/ai_readiness_framework.json assessment/harness/scan/rules \
         docs/reports/scan_matrix_*; do
  if [ -n "$(changed_and_new "$p")" ]; then echo "FAIL $p must be byte-identical and moved"; fail=1; fi
done

# Append-only files.
for f in corpus/evidence/decisions.jsonl state/spend_ledger.jsonl seldon_events.jsonl events/batch-001.jsonl \
         events/batch-009_probe_judge.jsonl events/batch-022.jsonl events/batch-023.jsonl \
         reports/dcat_us_3_brief/run/checkpoint.jsonl; do
  removed=$(git diff HEAD -- "$f" | grep -c '^-[^-]' || true)
  if [ "$removed" -ne 0 ]; then echo "FAIL $f lost or changed $removed line(s)"; fail=1; fi
done

# The evidence map has two writers here: its generator (`scripts/build_evidence_map.py`, whose
# corpus-count claims move with the admission) and this task's `scripts/dcat_brief_claims.py`.
# The file must be exactly what both render: each one's `--check` re-renders and compares.
PY=/opt/anaconda3/bin/python3
"$PY" scripts/build_evidence_map.py --check >/dev/null 2>&1 || { echo "FAIL docs/evidence/claims.yaml drifts from build_evidence_map.py"; fail=1; }
"$PY" scripts/dcat_brief_claims.py --check >/dev/null 2>&1 || { echo "FAIL docs/evidence/claims.yaml drifts from dcat_brief_claims.py"; fail=1; }

if [ "$fail" -eq 0 ]; then echo "PROTECTED PATHS: PASS"; else echo "PROTECTED PATHS: FAIL"; fi
exit "$fail"
