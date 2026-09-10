#!/usr/bin/env python3
"""Admit the ESIP AI-ready data checklist through the designed path. **Zero model spend.**

Task `cc_tasks/2026-09-10_corpus_noaa_esip.md` §1, decision 4. No network: the file is already
in hand (`scripts/fetch_noaa_esip_sources.py`, robots-first, identified UA, HTTP 200).

The path is `scripts/manifest_triage.py`'s, which is `scripts/manifest_kernel.py`'s before it:

  1. the file sits in a `document_dir` (`corpus/noaa_esip/`, added to `dixie_evidence.yaml`
     with its task citation the way every document directory here has been added);
  2. the dixie ledger gets `screening_imported`, then the sweep observes and integrity-checks;
  3. `kg.manifest.add` writes the `manifest_add` event — **already done from the CLI before
     this script existed**, which is the designed order reversed and is harmless: the two
     records are independent, the event log is the extraction-admission gate and the ledger is
     the corpus ledger (CLAUDE.md invariant 2). Re-running the add now would be refused as a
     duplicate, which is the check working;
  4. `corpus_epoch_declared`, so the admission names the task that ordered it;
  5. `manifest.rebuild()` — `corpus/manifest.json` is the ledger's PROJECTION, and an entry that
     is not in the ledger is not in the corpus however many events name it.

**Why this script exists at all.** `python -m kg.manifest add` alone left the document invisible
in `manifest.json`: the event was written and the projection did not move, because the projection
is rebuilt from `corpus/evidence/decisions.jsonl`. That is the Stage-0 rewire working exactly as
documented, and it is worth a script that does both halves rather than a habit of doing one.

    /opt/anaconda3/bin/python3 scripts/admit_esip_checklist.py --dry-run
    /opt/anaconda3/bin/python3 scripts/admit_esip_checklist.py
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
EPOCH = "noaa-esip-2026-09-10"
DOC_ID = "esip-ai-ready-data-checklist-v1-0"
DOC_PATH = REPO / "corpus" / "noaa_esip" / "esip-ai-ready-data-checklist-v1.0.md"
#: The citation AS FOUND, from the checklist's own "How to cite this checklist" block. §1 says
#: to record it as found and not as the task file writes it; §3 of the RESULT says how they
#: differ (year, version and author all move).
CITATION = ("ESIP Data Readiness Cluster (2023): Checklist to Examine AI-readiness for Open "
            "Environmental Datasets v.1.0. ESIP. Online resource. "
            "https://doi.org/10.6084/m9.figshare.19983722.v1")
SOURCE_URL = "https://doi.org/10.6084/m9.figshare.19983722.v1"
FETCHED_FROM = ("https://raw.githubusercontent.com/ESIPFed/data-readiness/main/"
                "checklist-published/ai-ready-data-checklist-v.1.0.md")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)

    if not DOC_PATH.is_file():
        raise SystemExit(f"FATAL: {DOC_PATH} is not in hand; admission requires the artifact "
                         f"and its hash, never a promise of one")
    sha = hashlib.sha256(DOC_PATH.read_bytes()).hexdigest()
    rel = DOC_PATH.relative_to(REPO).as_posix()

    cfg = dixie_config(REPO / "dixie_evidence.yaml")
    dlog = DixieLog(cfg["evidence_dir_abs"] / "decisions.jsonl")
    if DOC_ID in build_manifest(dlog, gate_cfg=cfg.get("identity_gate")):
        print(f"{DOC_ID} is already in the ledger; nothing to do")
        return 0

    record = {
        "import_key": DOC_ID,
        "normalized": {
            "source_id": "noaa_esip_2026-09-10", "doc_id": DOC_ID, "doc_id_exact": True,
            "title": "Checklist to Examine AI-readiness for Open Environmental Datasets v.1.0",
            "authors_or_org": ["ESIP Data Readiness Cluster"],
            "pub_year": "2023", "doc_type": "practitioner",
            "source_url": SOURCE_URL, "local_path": rel, "expected_sha256": sha,
            "acquisition_method": "scripted_fetch",
            "acquired_by": "scripts/fetch_noaa_esip_sources.py",
            "decision": "included",
            "rationale": (
                f"{TASK} decision 4. The corpus held the cluster's README "
                f"(`esip-data-readiness-checklist`, 3,351 B, the repository landing page) and "
                f"NOT the instrument; this is the published checklist itself, which the "
                f"crosswalk operationalizes item by item. Cited as found: {CITATION}"),
            "decided_by": "cc", "decided_at": datetime.now(timezone.utc).isoformat(),
            "notes": (f"fetched robots-first under the identified UA from {FETCHED_FROM}; the "
                      f"DOI above is the citation the document itself asks for"),
        }}

    if a.dry_run:
        print(json.dumps({"sha256": sha, "path": rel, "record": record}, indent=1)[:1800])
        return 0

    dlog.append("screening_imported", record)
    actions = Sweep(cfg, dlog).run()
    entries = build_manifest(dlog, gate_cfg=cfg.get("identity_gate"))
    e = entries.get(DOC_ID)
    ok = (e and e["screening"]["decision"] == "included"
          and e["integrity"]["status"] == "verified"
          and e["identity"].get("canonical_path"))
    if not ok:
        raise SystemExit(f"FATAL: post-sweep, {DOC_ID} is not included+verified: "
                         f"{e and (e['screening']['decision'], e['integrity']['status'])}. "
                         f"Nothing is declared for an epoch it did not enter.")
    dlog.append("corpus_epoch_declared", {
        "epoch": EPOCH, "member_doc_ids": [DOC_ID], "declared_by": "cc", "task": TASK,
        "note": ("The sources of the NOAA/ESIP crosswalk task. The two NOAA Administrative "
                 "Orders are NOT members: www.noaa.gov answered 403 to the identified client "
                 "and no operator copy was in `corpus/inbox/`, so they were never in hand. "
                 "Admission requires the artifact and its hash.")})
    out = manifest.rebuild()
    print(json.dumps({"admitted": DOC_ID, "sha256": sha[:16] + "…",
                      "sweep_actions": len(actions) if actions is not None else None,
                      "manifest": out}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
