#!/usr/bin/env bash
. "$(dirname "$0")/check_protected_lib.sh"
# The ship set of `cc_tasks/2026-10-05_DCAT-003_ADDENDUM_01_faq_shippability.md`, asserted
# against HEAD.
#
# Step 4 admits the DCAT-US 3.0 Dataset page and Overview as served on 2026-10-05, as dated
# versions (DD-068: `kg/manifest.py`, its tests, the decision entry), which writes the corpus
# ledger, the manifest projection, the admission and conversion shards, and the views every
# generator regenerates from the corpus count. Steps 1 to 3 and 5 to 7 write the FAQ's report
# directory, its four scripts and their test. Nothing else may move: no framework record, no
# scan payload or rule, no existing `cc_tasks/` file, and not the 2026-08-21 captures.
set -u
cd "$(dirname "$0")/.." || exit 2
fail=0

changed_and_new() {
  { git diff --name-only HEAD -- "$@"; git ls-files --others --exclude-standard -- "$@"; } \
    | sed '/^$/d' | sort -u
}

allowed() {
  case "$1" in
    reports/dcat_us_3_faq/*) return 0 ;;
    scripts/dcat_faq_evidence.py|scripts/dcat_faq_run.py|scripts/dcat_faq_build.py) return 0 ;;
    scripts/dcat_faq_lint.py|tests/test_dcat_faq.py) return 0 ;;
    kg/manifest.py|tests/test_manifest.py|docs/design_decisions.md) return 0 ;;
    scripts/admit_dcat_us_3_live_2026_10_05.py|scripts/check_protected_dcat_003a.sh) return 0 ;;
    corpus/evidence/decisions.jsonl|corpus/manifest.json) return 0 ;;
    events/batch-001.jsonl|events/batch-024.jsonl) return 0 ;;
    state/spend_ledger.jsonl) return 0 ;;
    docs/brief/C_provenance.md|docs/data/corpus_manifest.json|docs/data/index.json) return 0 ;;
    docs/evidence/claims.yaml|docs/evidence/definition_pairs.md) return 0 ;;
    docs/evidence/kg_questions.md|docs/evidence/kg_questions.yaml) return 0 ;;
    docs/figures/fig2_system_at_a_glance.png|docs/figures/fig2_system_at_a_glance.svg) return 0 ;;
    docs/figures/numbers.json) return 0 ;;
    cc_tasks/2026-10-05_DCAT-003_ADDENDUM_01_RESULT.md) return 0 ;;
  esac
  return 1
}

while IFS= read -r path; do
  [ -z "$path" ] && continue
  allowed "$path" || { echo "FAIL path outside the ship set moved: $path"; fail=1; }
done < <(changed_and_new .)

# Event shards, the corpus ledger, the spend ledger, the Seldon store and the FAQ run's
# checkpoint are append-only.
for f in corpus/evidence/decisions.jsonl state/spend_ledger.jsonl seldon_events.jsonl \
         events/batch-001.jsonl events/batch-024.jsonl reports/dcat_us_3_faq/run/checkpoint.jsonl; do
  removed=$(git diff HEAD -- "$f" | grep -c '^-[^-]' || true)
  if [ "$removed" -ne 0 ]; then echo "FAIL $f lost or changed $removed line(s)"; fail=1; fi
done

# The captures the dated versions are versions OF keep their bytes (DD-068 section 4).
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
