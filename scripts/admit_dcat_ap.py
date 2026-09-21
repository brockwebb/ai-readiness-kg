#!/usr/bin/env python3
"""Admit the DCAT-AP 3.0.0 `r5r` vocabulary through the designed path. **Zero model spend, no
network.**

`cc_tasks/2026-09-21_g4_resourcing_reissue.md`, executing decision 2 of
`cc_tasks/2026-09-20_g4_resourcing_release_date_grounding_fold.md`: DCAT-AP is admitted only if
the US documents leave G4's "statutory mandate" clause unsupported. They do — DCAT-US 1.1,
DCAT-US 3.0 (schema and overview), W3C DCAT 3, PROV-O and schema.org Dataset define no field
for the legislation a dataset is collected or held under (the searches are in the RESULT §2) —
so the vocabulary that DOES define one is admitted, and G4's cell cites it by analogy, in words.

The file is already in hand: `scripts/fetch_allowlisted.py` fetched it robots-first under the
identified UA from `semiceu.github.io`, a host the task's `**Network:**` header declared, and
`logs/2026-09-21_g4_resourcing_reissue_fetch.jsonl` has one line per request. This script
contacts nothing.

The path is `scripts/admit_tool_docs.py`'s, which is `scripts/admit_esip_checklist.py`'s:

  1. the file sits in a `document_dir` — `corpus/crosswalk/`, which already holds the W3C
     PROV-O and PROV-DM specifications admitted for the same purpose (a vocabulary an
     indicator's field is defined in);
  2. the dixie ledger gets `screening_imported`, then the sweep observes and integrity-checks;
  3. `corpus_epoch_declared`, so the admission names the task that ordered it;
  4. `manifest.rebuild()` — `corpus/manifest.json` is the ledger's projection;
  5. `kg.manifest.add` — ONE `manifest_add` event, because G4's evidence cell cites this
     document on an `EVIDENCED_BY` edge and `build_projection.py` creates `Document` nodes from
     `manifest_add` events only: without it the framework loader counts the edge as
     `evidenced_by_missing_document` and Cypher verification of G4 would silently miss a
     source. `scripts/manifest_crosswalk.py` did the same for PROV-O and PROV-DM. No
     `extraction_request` is written and `controls.yaml` has `extract: off`; admission to the
     event stream makes the document eligible for extraction, it does not spend.

Each step is skipped when already done, so re-running the script is the resume.

**What was fetched is the vocabulary, not the application profile.** The URL the task names,
`https://semiceu.github.io/DCAT-AP/r5r/releases/3.0.0/`, serves *DCAT-AP vocabulary, the r5r
namespace* — the normative definition of the three `dcatap:` terms, `applicableLegislation`
among them — and not the DCAT-AP 3.0.0 profile document (at `…/DCAT-AP/releases/3.0.0/`, which
the page links). The property's definition lives in the vocabulary, so that is the right
document to cite for it; the profile's per-class usage was not fetched and is not claimed.

    /opt/anaconda3/bin/python3 scripts/admit_dcat_ap.py --dry-run
    /opt/anaconda3/bin/python3 scripts/admit_dcat_ap.py
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

TASK = "cc_tasks/2026-09-21_g4_resourcing_reissue.md"
EPOCH = "g4-resourcing-2026-09-21"
SOURCE_ID = "g4_resourcing_2026-09-21"
FETCH_LOG = "logs/2026-09-21_g4_resourcing_reissue_fetch.jsonl"
DOCUMENT_DIR = "crosswalk"

#: `sha256` is the digest the fetch log recorded for the 200 response; the file on disk must
#: still hash to it, or nothing is admitted.
DOC = dict(
    doc_id="dcat-ap-3-0-0-r5r-vocabulary",
    path=REPO / "corpus" / DOCUMENT_DIR / "dcat-ap-3-0-0-r5r-vocabulary.html",
    sha256="2ebe9f6cd86df1d500d7764d0043fdc44ae5ec82317b9892d8609d7458c39e7e",
    title="DCAT-AP vocabulary, the r5r namespace (DCAT-AP 3.0.0 release)",
    authors_or_org=["SEMIC, Interoperable Europe (European Commission)"],
    # The page: "This vocabulary has the status SEMIC Recommendation published at 2024-06-16."
    pub_year="2024",
    source_url="https://semiceu.github.io/DCAT-AP/r5r/releases/3.0.0/",
    indicators=["G4"],
    notes=("The r5r namespace vocabulary page of the DCAT-AP 3.0.0 release, defining "
           "dcatap:applicableLegislation (range eli:LegalResource, domain rdfs:Resource), "
           "dcatap:availability and dcatap:hvdCategory. Not the DCAT-AP profile document, which "
           "the page links and which was not fetched."),
)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)

    cfg = dixie_config(REPO / "dixie_evidence.yaml")
    if DOCUMENT_DIR not in cfg["document_dirs"]:
        raise SystemExit(f"FATAL: `{DOCUMENT_DIR}` is not a document_dir in "
                         f"dixie_evidence.yaml; the sweep would never observe it")
    dlog = DixieLog(cfg["evidence_dir_abs"] / "decisions.jsonl")
    ledger = build_manifest(dlog, gate_cfg=cfg.get("identity_gate"))

    d = DOC
    if not d["path"].is_file():
        raise SystemExit(f"FATAL: {d['path']} is not in hand; admission requires the artifact "
                         f"and its hash, never a promise of one")
    sha = hashlib.sha256(d["path"].read_bytes()).hexdigest()
    if sha != d["sha256"]:
        raise SystemExit(f"FATAL: {d['path']} hashes to {sha}, and the fetch log recorded "
                         f"{d['sha256']}; the file is not the one fetched")
    in_ledger = d["doc_id"] in ledger
    record = {
        "import_key": d["doc_id"],
        "normalized": {
            "source_id": SOURCE_ID, "doc_id": d["doc_id"], "doc_id_exact": True,
            "title": d["title"], "authors_or_org": d["authors_or_org"],
            "pub_year": d["pub_year"], "doc_type": "standard",
            "source_url": d["source_url"],
            "local_path": d["path"].relative_to(REPO).as_posix(),
            "expected_sha256": sha,
            "acquisition_method": "scripted_fetch",
            "acquired_by": "scripts/fetch_allowlisted.py",
            "decision": "included",
            "rationale": (
                f"{TASK} (decision 2 of the task it re-issues): the US documents G4 could cite "
                f"define no field for the statutory mandate a dataset is collected under; this "
                f"vocabulary defines dcatap:applicableLegislation, the nearest standard "
                f"property, which G4's evidence cell cites by analogy and says so."),
            "decided_by": "cc", "decided_at": datetime.now(timezone.utc).isoformat(),
            "notes": (f"fetched robots-first under the identified UA from {d['source_url']} "
                      f"({FETCH_LOG}; semiceu.github.io/robots.txt answered 404). "
                      f"{d['notes']}"),
        }}

    in_stream = any(e["doc_id"] == d["doc_id"] for e in manifest._load_entries())
    if a.dry_run:
        print(json.dumps({"epoch": EPOCH, "in_ledger": in_ledger, "in_event_stream": in_stream,
                          "records": [record]}, indent=1, ensure_ascii=False))
        return 0
    if in_ledger:
        print(f"ledger: {d['doc_id']} already admitted; skipping steps 2 to 4")
        return _manifest_add(d, sha, record, in_stream)

    dlog.append("screening_imported", record)
    actions = Sweep(cfg, dlog).run()
    entries = build_manifest(dlog, gate_cfg=cfg.get("identity_gate"))
    e = entries.get(d["doc_id"])
    ok = (e and e["screening"]["decision"] == "included"
          and e["integrity"]["status"] == "verified"
          and e["identity"].get("canonical_path"))
    if not ok:
        raise SystemExit(f"FATAL: post-sweep, {d['doc_id']} is not included+verified: "
                         f"{e and (e['screening']['decision'], e['integrity']['status'])}. "
                         f"Nothing is declared for an epoch it did not enter.")
    dlog.append("corpus_epoch_declared", {
        "epoch": EPOCH, "member_doc_ids": [d["doc_id"]], "declared_by": "cc", "task": TASK,
        "note": ("The DCAT-AP r5r vocabulary, for G4's statutory-mandate clause: the one "
                 "standard property that links a resource to the legislation applicable to it. "
                 "Cited by analogy; G4's clause is a mandate, the property is applicability.")})
    out = manifest.rebuild()
    print(json.dumps({"admitted": [d["doc_id"]], "epoch": EPOCH, "sweep_actions": actions,
                      "manifest": out}, indent=1, default=str))
    return _manifest_add(d, sha, record, in_stream)


def _manifest_add(d: dict, sha: str, record: dict, in_stream: bool) -> int:
    """Step 5: the `manifest_add` event the Document node is projected from."""
    if in_stream:
        print(f"event stream: {d['doc_id']} already has manifest_add; nothing to do")
        return 0
    n = record["normalized"]
    manifest.add(str(d["path"]), doc_id=d["doc_id"], title=d["title"],
                 authors=d["authors_or_org"], pub_date=d["pub_year"], source_type="standard",
                 primary_url=d["source_url"], inclusion_rationale=n["rationale"],
                 discovered_via=SOURCE_ID, construct_arm="publication_actionability",
                 grounding_surface="document",
                 acquisition={"acquisition_method": "scripted_fetch",
                              "acquired_by": "scripts/fetch_allowlisted.py",
                              "fetch_log": FETCH_LOG,
                              "verification": {"sha256": sha},
                              "validation": {"bytes": d["path"].stat().st_size,
                                             "format": "html"},
                              "task": TASK})
    print(f"event stream: manifest_add written for {d['doc_id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
