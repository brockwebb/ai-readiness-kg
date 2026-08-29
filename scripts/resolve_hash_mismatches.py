#!/usr/bin/env python3
"""§-0.5 of task 2026-08-29_corpus_t0_t1_substrate ADDENDUM-01 — three-way hash reconciliation.

Four documents have reported `hash_mismatch` since July 2026. The addendum's decision tree
presumes drift ("the file on disk is the drifted party until proven otherwise"). The dixie
evidence ledger proves otherwise for all four: each was a DELIBERATE, operator-authorized
re-acquisition, recorded at the time with `superseded_sha256`, a reason, and the superseded
original preserved in `corpus/quarantine/`. Nothing drifted and nothing needs re-fetching.

What actually happened is a ledger-sync gap. `corpus/manifest.json` is projected from the
dixie ledger (CLAUDE.md invariant 2, post Stage-0 rewire) and so carries the corrected hash;
`kg.manifest.verify` replays the KG event log, which never received a supersession event and
so still carries the admission hash. The two layers diverged and nothing reconciled them.

The fix follows the addendum's own rule — never rewrite the original event, append a
supersession — via `kg.manifest.content_update`. Zero re-fetches, zero model calls.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from kg import manifest                                             # noqa: E402

TASK = "cc_tasks/2026-08-29_corpus_t0_t1_substrate.md ADDENDUM-01 §-0.5"
BATCH = 17

#: doc_id -> (reason, dixie evidence). Every hash and quotation below is read from
#: corpus/evidence/decisions.jsonl; nothing here is inferred.
CASES = {
    "advancing-american-ai-act-ndaa-fy2023-div-g": (
        "extent_corrected",
        {"dixie_events": ["quarantined", "screening_decided"],
         "superseded_reason": "wrong_extent: whole statute superseded by BILLS-117s1353rs",
         "superseded_original_preserved_at":
             "corpus/quarantine/advancing-american-ai-act-ndaa-fy2023-div-g.megastatute.pdf",
         "replacement_rationale": "refetch fulfillment: standalone BILLS-117s1353rs (BILLS) "
                                  "via govinfo_connector; extent corrected",
         "acquired_via": "govinfo_connector", "package_id": "BILLS-117s1353rs",
         "page_count": 36}),
    "ai-in-government-act-of-2020": (
        "extent_corrected",
        {"dixie_events": ["quarantined", "screening_decided"],
         "superseded_reason": "wrong_extent: whole statute superseded by BILLS-116hr2575pcs",
         "superseded_original_preserved_at":
             "corpus/quarantine/ai-in-government-act-of-2020.megastatute.pdf",
         "replacement_rationale": "refetch fulfillment: standalone BILLS-116hr2575pcs (BILLS) "
                                  "via govinfo_connector; extent corrected",
         "acquired_via": "govinfo_connector", "package_id": "BILLS-116hr2575pcs",
         "page_count": 10}),
    "fcsm-19-01-transparent-reporting-for-integrated-data-quality": (
        "corrupt_source_replaced",
        {"dixie_events": ["note (kind=acquisition_evidence)"],
         "superseded_reason": "PdfReadError: Unable to find 'endstream' marker for obj @811018",
         "corrupt_original_preserved_at":
             "corpus/quarantine/fcsm-19-01-transparent-reporting-for-integrated-data-quality"
             ".corrupt-no-endstream.pdf",
         "replacement_rationale": "Operator-authorized re-acquisition 2026-07-16. "
                                  "Content-smoke (10-page) passed on the corrupt copy; "
                                  "full-corpus extraction exposed the truncated object. "
                                  "Clean copy from NCES fcsm mirror.",
         "acquisition_method": "manual_browser", "retrieval_date": "2026-07-17",
         "download_url": "https://nces.ed.gov/fcsm/pdf/Transparent_Reporting_FCSM_19.01.pdf",
         "page_count": 143}),
    "information-quality-act-data-quality-act-sec-515-of-p-l-106": (
        "extent_corrected",
        {"dixie_events": ["note (kind=acquisition_evidence)"],
         "superseded_reason": "over-extent — whole P.L. 106-554 megastatute in place of "
                              "standalone §515",
         "superseded_original_preserved_at":
             "corpus/quarantine/information-quality-act-data-quality-act-sec-515-of-p-l-106"
             ".megastatute-over-extent-plaw-106-554.pdf",
         "replacement_rationale": "Operator-supplied clean standalone §515 excerpt, staged at "
                                  "corpus/inbox/data_quality_act.pdf. CORRECTS THE EXTENT of "
                                  "the original mis-acquisition.",
         "acquisition_method": "manual_browser", "retrieval_date": "2026-07-17",
         "page_count": 1}),
}


def three_way() -> list[dict]:
    """(event hash, dixie hash, disk hash) per mismatched doc — the addendum's §-0.5 table."""
    entries = {e["doc_id"]: e for e in manifest._load_entries()}
    mf = json.load((REPO / "corpus/manifest.json").open())["entries"]
    rows = []
    for doc_id in CASES:
        e = entries.get(doc_id)
        if e is None:
            rows.append({"doc_id": doc_id, "error": "not admitted"}); continue
        path = REPO / e["local_path"]
        rows.append({
            "doc_id": doc_id, "local_path": e["local_path"],
            "event": e["content_hash"],
            "dixie": (mf.get(doc_id, {}).get("identity") or {}).get("sha256"),
            "disk": manifest._sha256(path) if path.is_file() else None,
        })
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    manifest._MANIFEST_BATCH = BATCH

    rows = three_way()
    print(f"{'doc_id':<58}{'event':<14}{'dixie':<14}{'disk':<14}verdict")
    for r in rows:
        v = ("event==dixie==disk (already clean)" if r["event"] == r["dixie"] == r["disk"]
             else "dixie==disk, event stale -> supersession missing from KG log"
             if r["dixie"] == r["disk"] else "UNEXPECTED — investigate, do not write")
        print(f"{r['doc_id'][:56]:<58}{str(r['event'])[:12]:<14}{str(r['dixie'])[:12]:<14}"
              f"{str(r['disk'])[:12]:<14}{v}")

    unexpected = [r for r in rows if r.get("dixie") != r.get("disk")]
    if unexpected:
        print("\nFATAL: dixie and disk disagree for "
              f"{[r['doc_id'] for r in unexpected]}. That is real drift, not a sync gap, and "
              "this script's premise does not hold. Stopping without writing.")
        return 2
    if a.dry_run:
        print("\ndry run — no events written")
        return 0

    for r in rows:
        if r["event"] == r["disk"]:
            print(f"SKIP  {r['doc_id']} (already reconciled)"); continue
        reason, evidence = CASES[r["doc_id"]]
        new = manifest.content_update(
            r["doc_id"], reason=reason, superseded_content_hash=r["event"],
            evidence={**evidence, "ledger": "corpus/evidence/decisions.jsonl",
                      "note": "Re-acquisition was recorded in the dixie evidence ledger at "
                              "the time; this event mirrors it into the KG event log, which "
                              "never received it. No re-fetch: the ledger already answers "
                              "what a re-fetch would ask."},
            task=TASK)
        print(f"UPDATE {r['doc_id']}  {r['event'][:12]} -> {new[:12]}  ({reason})")

    problems = manifest.verify()
    print(f"\nkg.manifest verify: {len(problems)} problem(s)")
    for p in problems:
        print("   ", p["doc_id"], p["issue"])
    return 0 if not problems else 1


if __name__ == "__main__":
    raise SystemExit(main())
