#!/usr/bin/env bash
. "$(dirname "$0")/check_protected_lib.sh"
# The ship set of `cc_tasks/2026-10-04_DCAT-002_ADDENDUM_01_base_standard_and_fairness_record.md`,
# asserted against HEAD.
#
# The addendum admits and extracts four documents, so it writes the corpus ledger, the manifest
# projection, the event shards their writers append to, the run's raws and state, the admission
# script, the extraction driver's cohort selector, and the views the generators regenerate from
# the corpus. It changes no framework record: `framework/ai_readiness_framework.json`,
# `assessment/harness/scan/rules/`, every stored scan payload under `state/scan_*` and every
# existing `cc_tasks/` file stay byte-identical to HEAD. `docs/brief/` is allowed whole because
# every page's header stamps the commit that last touched the framework record, and the base
# DCAT-002 commit (688451fb) became that commit after its generators ran.
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
    events/batch-024.jsonl) return 0 ;;
    events/raw/bulk_v038/fairness-project-wiki-home.*) return 0 ;;
    events/raw/bulk_v038/fairness-project-wiki-project-overview.*) return 0 ;;
    events/raw/bulk_v038/fcsm-2024-b3-3-fairness-project.*) return 0 ;;
    events/raw/bulk_v038/cdoc-dswg-findings-and-recommendations-2022.*) return 0 ;;
    state/spend_ledger.jsonl|state/dcat_us_3_a01_extraction_2026-10-05.json) return 0 ;;
    scripts/admit_dcat_002_a01.py|scripts/run_dcat_extraction.py) return 0 ;;
    scripts/check_protected_dcat_002_a01.sh) return 0 ;;
    tests/test_dcat_002_a01_intake.py) return 0 ;;
    docs/design/2026-10-04_DN-011_dcat_us_3_intake.md) return 0 ;;
    docs/brief/*) return 0 ;;
    docs/data/corpus_manifest.json|docs/data/index.json) return 0 ;;
    docs/evidence/claims.yaml|docs/evidence/kg_questions.md|docs/evidence/kg_questions.yaml) return 0 ;;
    docs/evidence/definition_pairs.md) return 0 ;;
    docs/figures/fig2_system_at_a_glance.png|docs/figures/fig2_system_at_a_glance.svg) return 0 ;;
    docs/figures/numbers.json) return 0 ;;
    cc_tasks/2026-10-04_DCAT-002_ADDENDUM_01_RESULT.md) return 0 ;;
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
         events/batch-024.jsonl; do
  removed=$(git diff HEAD -- "$f" | grep -c '^-[^-]' || true)
  if [ "$removed" -ne 0 ]; then echo "FAIL $f lost or changed $removed line(s)"; fail=1; fi
done

# The held items the addendum named keep their bytes: W3C DCAT 3 and FCSM 20-04 (R5).
for doc in w3c-dcat-3 fcsm-20-04-a-framework-for-data-quality; do
  before=$(git show HEAD:corpus/manifest.json | python3 -c "import json,sys; print(json.load(sys.stdin)['entries']['$doc']['identity']['sha256'])")
  after=$(python3 -c "import json; print(json.load(open('corpus/manifest.json'))['entries']['$doc']['identity']['sha256'])")
  [ "$before" = "$after" ] || { echo "FAIL $doc changed sha256 in the manifest"; fail=1; }
done

if [ "$fail" -eq 0 ]; then echo "PROTECTED PATHS: PASS"; else echo "PROTECTED PATHS: FAIL"; fi
exit "$fail"
