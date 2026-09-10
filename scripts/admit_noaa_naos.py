#!/usr/bin/env python3
"""Admit the two NOAA Administrative Orders. **Zero model spend. No network.**

Task `cc_tasks/2026-09-10_corpus_noaa_esip.md` §1 decision 1, under `ADDENDUM_01`: the operator's
copies are at `corpus/staging/inbox/nao216.pdf` and `nao201.pdf`, not `corpus/inbox/`. The
fetcher's own attempt was refused — `www.noaa.gov` answered HTTP 403 to the identified client on
both URLs, with robots.txt PERMITTING the path — and that refusal stands in
`state/noaa_esip_fetch_2026-09-10.json` as the record of how these bytes did NOT arrive. No
retry under another identity was made or will be (DD-060).

Same designed path as `scripts/admit_esip_checklist.py`: ledger `screening_imported` → sweep →
`kg.manifest.add` → `corpus_epoch_declared` → `manifest.rebuild()`.

**Both are `in_force`, and the citation for that differs from the task file's.**
216-128's §8 EFFECT ON OTHER ISSUANCES reads "None" — nothing superseded, nothing superseding.
201-118's supersession section is **§9**, not §8 (§8 is RESPONSIBILITIES), and it carries no
supersession text at all. So neither is superseded; that is the ground, and it is weaker than
"per its own §8" implies.

    /opt/anaconda3/bin/python3 scripts/admit_noaa_naos.py --dry-run
    /opt/anaconda3/bin/python3 scripts/admit_noaa_naos.py
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from kg import manifest                                             # noqa: E402
from dixie.evidence.config import load_config as dixie_config       # noqa: E402
from dixie.evidence.eventlog import EventLog as DixieLog            # noqa: E402
from dixie.evidence.manifest import build_manifest                  # noqa: E402
from dixie.evidence.sweep import Sweep                              # noqa: E402

TASK = "cc_tasks/2026-09-10_corpus_noaa_esip.md"
ADDENDUM = "cc_tasks/2026-09-10_corpus_noaa_esip_ADDENDUM_01.md"
EPOCH = "noaa-esip-2026-09-10"
DIR = REPO / "corpus" / "noaa_esip"

DOCS = [
    # The OCR TEXT is the canonical artifact and the image PDF is its source. The corpus
    # integrity gate requires 200 readable characters in a PDF (`dixie_evidence.yaml`
    # `pdf_min_chars`) and this one's native text layer is 36 bytes, so it fails — correctly,
    # because there is nothing in it to read. Lowering the floor was available and refused: it is
    # an operator threshold, it exists to catch HTML stubs and empty captures, and it is doing
    # that job. The readable artifact IS the OCR text, it is what every span from this document
    # is grounded against, and the image rides beside it with its hash in the sidecar. Operator
    # overrides by lowering the floor and re-admitting the PDF as canonical.
    {"doc_id": "nao-216-128-artificial-intelligence-in-noaa",
     "path": DIR / "NAO_216-128.ocr.txt",
     "title": "NAO 216-128: Artificial Intelligence in NOAA",
     "authors": ["National Oceanic and Atmospheric Administration"],
     "pub_date": "2026-04-16",
     "url": "https://www.noaa.gov/sites/default/files/2026-04/NAO_216-128.pdf",
     "rationale": (
         "The NOAA AI policy. §3.01 defines AI-Ready Data in five components and is the "
         "definition the crosswalk measures the instrument against; §4.05 and §5.02.d are its "
         "operative directives. Signed and effective 2026-04-16 per its own form; §8 EFFECT ON "
         "OTHER ISSUANCES reads None, so it is in force and supersedes nothing. SCANNED IMAGE: "
         "the admitted artifact is the OCR reading (NAO_216-128.ocr.txt, tesseract 5.5.0, mean "
         "word confidence 94.52 over 1,110 words); the image PDF sits beside it as "
         "NAO_216-128.pdf with its sha256 in NAO_216-128.ocr.json."),
     "note": ("in_force. The PDF's native text layer is 36 bytes — below the corpus's "
              "`pdf_min_chars` floor of 200 and rightly so — which is why the OCR text is the "
              "canonical artifact. Every span from this document is grounded against a machine "
              "reading of an image, and NAO_216-128.ocr.json says so with the engine, the "
              "rasterisation, the per-word confidence and the one known substitution "
              "(tesseract reads body-text 'AI' as 'Al')."),
     "source_pdf": "corpus/noaa_esip/NAO_216-128.pdf"},
    {"doc_id": "nao-201-118-software-governance-and-public-release",
     "path": DIR / "NAO_201-118_Software_Governance_and_Public_Release_Policy.pdf",
     "title": "NAO 201-118: Software Governance and Public Release Policy",
     "authors": ["National Oceanic and Atmospheric Administration"],
     "pub_date": "2024-11",
     "url": ("https://www.noaa.gov/sites/default/files/2024-11/"
             "NAO_201-118-Software_Governance_and_Public_Release_Policy.pdf"),
     "rationale": (
         "NOAA's software governance and public-release policy, the release-engineering "
         "counterpart to 216-128's data policy. Admitted for the crosswalk's F-criterion rows. "
         "Text PDF, no OCR needed."),
     "note": ("in_force: §9 EFFECT ON OTHER ISSUANCES carries no supersession text. The "
              "document's own form reads 'DATE OF ISSUANCE: TBD / EFFECTIVE DATE: TBD' even "
              "though it is signed, so the 2024-11 date is the publication path on noaa.gov, "
              "NOT a date the document states. Recorded as found.")},
]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)

    cfg = dixie_config(REPO / "dixie_evidence.yaml")
    dlog = DixieLog(cfg["evidence_dir_abs"] / "decisions.jsonl")
    held = build_manifest(dlog, gate_cfg=cfg.get("identity_gate"))

    plan, done = [], []
    for d in DOCS:
        if not d["path"].is_file():
            raise SystemExit(f"FATAL: {d['path']} is not in hand; admission requires the "
                             f"artifact and its hash, never a promise of one")
        # "in the ledger" is NOT "admitted". 216-128's first record pointed at the image PDF
        # and the integrity gate failed it; the correction is a LATER record naming the OCR
        # text, never an edit to the first. So the skip is on a record that actually landed.
        e = held.get(d["doc_id"])
        if e and e["screening"]["decision"] == "included" \
                and e["integrity"]["status"] == "verified" \
                and e["identity"].get("canonical_path"):
            print(f"{d['doc_id']} already admitted and verified; skipping the ledger record")
            done.append(d["doc_id"])
            continue
        plan.append({**d, "sha256": hashlib.sha256(d["path"].read_bytes()).hexdigest()})

    if a.dry_run:
        print(json.dumps([{k: (str(v) if isinstance(v, Path) else v)
                           for k, v in p.items()} for p in plan], indent=1)[:2500])
        return 0
    if not plan and not done:
        return 0

    for p in plan:
        dlog.append("screening_imported", {
            "import_key": p["doc_id"],
            "normalized": {
                "source_id": "noaa_esip_2026-09-10", "doc_id": p["doc_id"],
                "doc_id_exact": True, "title": p["title"],
                "authors_or_org": p["authors"], "pub_year": p["pub_date"][:4],
                "doc_type": "federal", "source_url": p["url"],
                "local_path": p["path"].relative_to(REPO).as_posix(),
                "expected_sha256": p["sha256"],
                "acquisition_method": "operator_drop",
                "acquired_by": f"operator, per {ADDENDUM}",
                "decision": "included", "rationale": p["rationale"],
                "decided_by": "cc", "decided_at": datetime.now(timezone.utc).isoformat(),
                "notes": p["note"], "source_pdf": p.get("source_pdf")}})

    Sweep(cfg, dlog).run()
    entries = build_manifest(dlog, gate_cfg=cfg.get("identity_gate"))
    # The event log is the extraction-admission gate and the ledger is the corpus ledger
    # (CLAUDE.md invariant 2). They are written separately, so a run interrupted between them
    # must not write the second one twice.
    from kg import eventlog
    already_evented = {ev["payload"]["doc_id"] for ev in eventlog.replay()
                       if ev.get("event_type") == "manifest_add"}
    members = list(done)
    for p in plan + [d for d in DOCS if d["doc_id"] in done]:
        e = entries.get(p["doc_id"])
        ok = (e and e["screening"]["decision"] == "included"
              and e["integrity"]["status"] == "verified"
              and e["identity"].get("canonical_path"))
        if not ok:
            raise SystemExit(f"FATAL: post-sweep, {p['doc_id']} is not included+verified: "
                             f"{e and (e['screening']['decision'], e['integrity']['status'])}")
        if p["doc_id"] not in members:
            members.append(p["doc_id"])
        if p["doc_id"] in already_evented:
            print(f"  {p['doc_id']}: manifest_add event already on the log")
            continue
        manifest.add(str(p["path"]), doc_id=p["doc_id"], title=p["title"],
                     authors=p["authors"], pub_date=p["pub_date"], source_type="federal",
                     primary_url=p["url"], inclusion_rationale=p["rationale"],
                     discovered_via=f"operator drop, {ADDENDUM}",
                     construct_arm="publication_actionability",
                     grounding_surface="document")

    dlog.append("corpus_epoch_declared", {
        "epoch": EPOCH, "member_doc_ids": sorted(members), "declared_by": "cc", "task": TASK,
        "note": ("The two NOAA Administrative Orders, from the operator's copies. The fetcher's "
                 "own attempt was refused 403 by www.noaa.gov under the identified client and "
                 "the refusal is recorded in state/noaa_esip_fetch_2026-09-10.json.")})
    out = manifest.rebuild()
    print(json.dumps({"admitted": members, "manifest": out}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
