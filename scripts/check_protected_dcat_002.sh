#!/usr/bin/env bash
. "$(dirname "$0")/check_protected_lib.sh"
# The ship set of `cc_tasks/2026-10-04_DCAT-002_dcat_us_3_intake_and_g4.md`, asserted against HEAD.
#
# Steps 1-2 (admission and extraction) write the corpus ledger, the manifest projection, the
# event shards their writers append to, the run's raws and state, and the two scripts that did
# it. Step 3 (G4) writes the skeleton row, the record through `framework_writeback.save`, and
# the views every generator regenerates from the corpus and the record. Every other path is
# byte-identical to HEAD — in particular `assessment/harness/scan/rules/`, every stored scan
# payload under `state/scan_*`, and every existing `cc_tasks/` file.
set -u
cd "$(dirname "$0")/.." || exit 2
fail=0

changed_and_new() {
  { git diff --name-only HEAD -- "$@"; git ls-files --others --exclude-standard -- "$@"; } \
    | sed '/^$/d' | sort -u
}

allowed() {
  case "$1" in
    corpus/evidence/decisions.jsonl|corpus/manifest.json) return 0 ;;
    events/batch-001.jsonl|events/batch-022.jsonl|events/batch-023.jsonl) return 0 ;;
    events/batch-024.jsonl|events/batch-033_framework.jsonl) return 0 ;;
    events/raw/bulk_v038/dcat-us-3-*|events/raw/bulk_v038/statdcat-ap-1-0-1.*) return 0 ;;
    events/raw/bulk_v038/w3c-dqv.*) return 0 ;;
    state/spend_ledger.jsonl|state/dcat_us_3_extraction_2026-10-04.json) return 0 ;;
    scripts/admit_dcat_us_3.py|scripts/run_dcat_extraction.py) return 0 ;;
    scripts/check_protected_dcat_002.sh) return 0 ;;
    tests/test_dcat_us_3_intake.py|tests/test_g4_locators_and_progress_drift.py) return 0 ;;
    docs/design/2026-10-04_DN-011_dcat_us_3_intake.md) return 0 ;;
    docs/crosswalk/usafacts_operationalization_skeleton.md) return 0 ;;
    framework/ai_readiness_framework.json) return 0 ;;
    docs/brief/B_usafacts_delta.csv|docs/brief/B_usafacts_delta.md) return 0 ;;
    docs/brief/C_provenance.csv|docs/brief/C_provenance.md) return 0 ;;
    docs/brief/appendix/indicator_G4.md|docs/brief/numbers.json) return 0 ;;
    docs/catalog/README.md|docs/catalog/scan_catalog.csv) return 0 ;;
    docs/catalog/rollups/quick_wins.csv|docs/catalog/rollups/rollups.md) return 0 ;;
    docs/data/ai_readiness_framework.json|docs/data/corpus_manifest.json) return 0 ;;
    docs/data/index.json|docs/data/sources_per_check.json) return 0 ;;
    docs/design/mcp_over_the_graph.md) return 0 ;;
    docs/evidence/claims.yaml|docs/evidence/kg_questions.md|docs/evidence/kg_questions.yaml) return 0 ;;
    docs/evidence/definition_pairs.md) return 0 ;;
    docs/figures/fig2_system_at_a_glance.png|docs/figures/fig2_system_at_a_glance.svg) return 0 ;;
    docs/figures/numbers.json) return 0 ;;
    docs/reports/2026-09_fss_ai_readiness_L0.md|docs/reports/2026-09_fss_ai_readiness_L0.pdf) return 0 ;;
    docs/reports/generated/sources_per_check.md) return 0 ;;
    cc_tasks/2026-10-04_DCAT-002_dcat_us_3_intake_and_g4_RESULT.md) return 0 ;;
  esac
  return 1
}

while IFS= read -r path; do
  [ -z "$path" ] && continue
  allowed "$path" || { echo "FAIL path outside the ship set moved: $path"; fail=1; }
done < <(changed_and_new .)

# Event shards, the corpus ledger and the spend ledger are append-only.
for f in corpus/evidence/decisions.jsonl state/spend_ledger.jsonl seldon_events.jsonl \
         events/batch-001.jsonl events/batch-022.jsonl events/batch-023.jsonl \
         events/batch-024.jsonl events/batch-033_framework.jsonl; do
  removed=$(git diff HEAD -- "$f" | grep -c '^-[^-]' || true)
  if [ "$removed" -ne 0 ]; then echo "FAIL $f lost or changed $removed line(s)"; fail=1; fi
done

# The two captures the task must not supersede in place keep their bytes on disk.
for pair in "corpus/kernel/dcat-us-3-dataset-schema.md 7482b3170215046ff73ee2229d6e9305da7c5d676c32ec755c8784f8c3858e44" \
            "corpus/kernel/dcat-us-3-overview.md 87d3d2a8bb9d8ddc445e6674b4738e58f6b0d8629f6d19093dfc360b90175fa0"; do
  p=${pair%% *}; want=${pair##* }
  if [ -f "$p" ]; then
    got=$(shasum -a 256 "$p" | cut -d' ' -f1)
    [ "$got" = "$want" ] || { echo "FAIL $p no longer hashes to its admitted sha256"; fail=1; }
  fi
done

if [ "$fail" -eq 0 ]; then echo "PROTECTED PATHS: PASS"; else echo "PROTECTED PATHS: FAIL"; fi
exit "$fail"
