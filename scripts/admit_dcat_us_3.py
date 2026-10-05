#!/usr/bin/env python3
"""Admit the DCAT-US 3.0 documents and their statistical prior art. **Zero model spend, no
network.**

`cc_tasks/2026-10-04_DCAT-002_dcat_us_3_intake_and_g4.md` steps 1 and 2, implementing
DN-011-R2 (`docs/design/2026-10-04_DN-011_dcat_us_3_intake.md`). Every file was fetched by
`scripts/fetch_allowlisted.py` into `corpus/staging/dcat_002/` (inert, CLAUDE.md invariant 2),
robots-first under the identified UA, and `logs/2026-10-04_DCAT-002_fetch.jsonl` has one line
per request. This script contacts nothing.

The path is `scripts/admit_dcat_ap.py`'s, for nine documents instead of one:

  1. the staged file must hash to the sha256 the fetch log recorded for its 200 response, or
     nothing is admitted;
  2. it is copied to `corpus/crosswalk/<doc_id>.<ext>`, the lane for vocabularies an
     indicator's field is defined in (W3C DCAT 3's neighbours PROV-O, PROV-DM and the DCAT-AP
     r5r vocabulary already live there);
  3. dixie `screening_imported` (`included`, criterion R1 of
     `cc_tasks/2026-08-24_source_triage.md`: "metadata standards ... err inclusive"), then the
     sweep observes and integrity-checks;
  4. one `corpus_epoch_declared`, `dcat-us-3-2026-10-04`;
  5. `manifest.rebuild()`, then `kg.manifest.add` per document — the `manifest_add` event a
     `Document` node is projected from and the extraction queue admits against.

**Two documents are archived copies (RFC 7089 mementos), and say so.** The DCAT-US 3 working
draft at `https://doi-do.github.io/dcat-us/` answers 404 on every path of that host
(2026-10-05); the Internet Archive's capture of 2025-05-04 is admitted, with the memento URI as
`primary_url` and the original URI in the notes. The DCAT-US 3.0 Dataset page was REWRITTEN
after the corpus captured it on 2026-08-21 (`publisher` moved from Mandatory to Recommended);
the held `dcat-us-3-dataset-schema` is cited by the pre-registered rules RULE-B4-v1 and
RULE-D3-v1, so its bytes are not superseded in place (the task: "do not edit an accepted record
in place"), and the 2026-09-15 memento — word-for-word the page served live on 2026-10-05,
the same requirement levels — is admitted as its own dated document. A memento URI is a
distinct resource (RFC 7089 §1.2, URI-M), which is why `manifest.add`'s primary-URL dedupe
admits it without any change to the gate.

**One of the nine is not admitted here.** The overview (`https://resources.data.gov/resources/
dcat-us3/`) is held since 2026-08-21 as `dcat-us-3-overview`: R5 (dedupe by primary URL). Its
live page has since been rewritten twice and no archived capture of the current text exists;
the RESULT records that and the versioning question it raises.

Each step is skipped when already done, so re-running the script is the resume.

    /opt/anaconda3/bin/python3 scripts/admit_dcat_us_3.py --dry-run
    /opt/anaconda3/bin/python3 scripts/admit_dcat_us_3.py
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
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

TASK = "cc_tasks/2026-10-04_DCAT-002_dcat_us_3_intake_and_g4.md"
EPOCH = "dcat-us-3-2026-10-04"
SOURCE_ID = "dcat_002_2026-10-04"
FETCH_LOG = REPO / "logs" / "2026-10-04_DCAT-002_fetch.jsonl"
STAGING = REPO / "corpus" / "staging" / "dcat_002"
DOCUMENT_DIR = "crosswalk"
GSA = ["U.S. General Services Administration / Data.gov"]
RATIONALE = (f"{TASK} (DN-011-R2): DCAT-US 3.0 and its statistical prior art, so that "
             f"draft-against-final and US-against-EU can be queried. Criterion R1 "
             f"(cc_tasks/2026-08-24_source_triage.md): a metadata standard, the graph's "
             f"target construct.")

#: `fetched_url` is the URL of the 200 response whose body is the staged file (for a memento,
#: the capture the archive redirected to). Its sha256 is read from the fetch log, never typed.
DOCS = [
    dict(doc_id="dcat-us-3-implementation-guide", staged="02_impl_guide/dcat-us-3-implementation-guide.pdf",
         fetched_url="https://resources.data.gov/assets/documents/dcat-us-3-implementation-guide.pdf",
         title="DCAT-US v3.0 Schema Implementation Guide (version 1.1)", authors=GSA,
         pub_date="2026-09-09", source_type="federal", fmt="pdf",
         notes="78 pages. Version history: 1.0 2026-08-21 Final; 1.1 2026-09-09 updated "
               "reference to ISO 19115-1 and administrative edits."),
    dict(doc_id="dcat-us-3-m-25-05-crosswalk", staged="03_crosswalk/dcat-us-3-crosswalk",
         fetched_url="https://resources.data.gov/resources/dcat-us-3-crosswalk/",
         title="DCAT-US 3 / M-25-05 Crosswalk (resources.data.gov)", authors=GSA,
         pub_date="2026", source_type="federal", fmt="html",
         notes="Maps OMB M-25-05 Phase 2 metadata elements to DCAT-US 3.0 properties."),
    dict(doc_id="dcat-us-3-quality-governance", staged="04_quality_governance/quality-governance",
         fetched_url="https://resources.data.gov/standards/catalog/dcat-us-3/quality-governance/",
         title="DCAT-US 3.0: Quality and Governance (resources.data.gov)", authors=GSA,
         pub_date="2026", source_type="standard", fmt="html",
         notes="DCAT-US 3.0 supporting-class schema page."),
    dict(doc_id="dcat-us-3-temporal-spatial-metrics",
         staged="05_temporal_spatial_metrics/temporal-spatial-metrics",
         fetched_url="https://resources.data.gov/standards/catalog/dcat-us-3/temporal-spatial-metrics/",
         title="DCAT-US 3.0: Temporal, Spatial, and Metrics (resources.data.gov)", authors=GSA,
         pub_date="2026", source_type="standard", fmt="html",
         notes="DCAT-US 3.0 supporting-class schema page, including QualityMeasurement."),
    dict(doc_id="dcat-us-3-dataset-series", staged="06_dataset_series/dataset-series",
         fetched_url="https://resources.data.gov/standards/catalog/dcat-us-3/dataset-series/",
         title="DCAT-US 3.0: Dataset Series (resources.data.gov)", authors=GSA,
         pub_date="2026", source_type="standard", fmt="html",
         notes="DCAT-US 3.0 supporting-class schema page."),
    dict(doc_id="dcat-us-3-candidate-recommendation-snapshot",
         staged="07_working_draft_memento/dcat-us",
         fetched_url="https://web.archive.org/web/20250504194000id_/https://doi-do.github.io/dcat-us/",
         title="DCAT-US - Version 3: Data Catalog Application Profile for the United States of "
               "America (Candidate Recommendation Snapshot; Internet Archive capture "
               "2025-05-04)",
         authors=["DOI-DO DCAT-US working group (GitHub doi-do/dcat-us)"],
         pub_date="2025-05-04", source_type="standard", fmt="html",
         notes="The earlier DCAT-US 3 working draft, kept distinct from the final so the two "
               "can be compared. Original URI https://doi-do.github.io/dcat-us/ answers 404 "
               "(2026-10-05, every path of the host); this is the Internet Archive memento "
               "captured 2025-05-04T19:40:00Z (the archive redirected the 2025-08-19 request "
               "to it), fetched with the id_ modifier so the bytes are the original's."),
    dict(doc_id="statdcat-ap-1-0-1", staged="08_statdcat_pdf/StatDCAT-AP_1.0.1.pdf",
         fetched_url=("https://interoperable-europe.ec.europa.eu/sites/default/files/distribution/"
                      "access_url/2019-05/0812e528-c428-4832-b674-d5b9c68d1b42/"
                      "StatDCAT-AP_1.0.1.pdf"),
         title="StatDCAT-AP - DCAT Application Profile for description of statistical datasets, "
               "Version 1.0.1",
         authors=["European Commission, ISA2 programme / SEMIC Support Centre"],
         pub_date="2019-05-28", source_type="standard", fmt="pdf",
         notes="100 pages. The PDF distribution of release 1.0.1 on the Interoperable Europe "
               "portal (release page .../statdcat-application-profile-data-portals-europe/"
               "release/101, which marks it archived in favour of a later release). The task "
               "names 1.0.1 for its stat:dimension, stat:attribute, statUnitMeasure, "
               "numSeries, dqv:hasQualityAnnotation and SDMX mapping."),
    dict(doc_id="w3c-dqv", staged="09_dqv/vocab-dqv",
         fetched_url="https://www.w3.org/TR/vocab-dqv/",
         title="Data on the Web Best Practices: Data Quality Vocabulary (W3C Working Group Note)",
         authors=["W3C Data on the Web Best Practices Working Group"],
         pub_date="2016-12-15", source_type="standard", fmt="html",
         notes="W3C Working Group Note 15 December 2016."),
    dict(doc_id="dcat-us-3-dataset-schema-2026-09-15", staged="10_dataset_memento/dataset",
         fetched_url=("https://web.archive.org/web/20260915131436id_/"
                      "https://resources.data.gov/standards/catalog/dcat-us-3/dataset/"),
         title="DCAT-US 3.0 Schema: Dataset (resources.data.gov; Internet Archive capture "
               "2026-09-15, after the September 2026 rewrite)", authors=GSA,
         pub_date="2026-09-15", source_type="standard", fmt="html",
         notes="The Dataset page as rewritten in September 2026: Mandatory are contactPoint, "
               "description, identifier and title; publisher is Recommended; bureauCode and "
               "programCode are absent. The corpus's 2026-08-21 capture (doc "
               "dcat-us-3-dataset-schema) marks publisher Mandatory and stays as it is, "
               "because pre-registered rules RULE-B4-v1 and RULE-D3-v1 cite it. The live page "
               "fetched 2026-10-05 (fetch log, sha256 3b5cbb2d...) carries the same "
               "requirement levels and differs from this capture by page chrome only "
               "(word-sequence ratio 0.991)."),
]


def fetched_sha(url: str) -> str:
    """The sha256 the fetch log recorded for the 200 response at `url`. Exactly one, or stop."""
    rows = [json.loads(l) for l in FETCH_LOG.read_text(encoding="utf-8").splitlines() if l]
    hits = {r["sha256"] for r in rows
            if r.get("event") == "request" and r.get("url") == url and r.get("status") == 200}
    if len(hits) != 1:
        raise SystemExit(f"FATAL: {FETCH_LOG.name} records {len(hits)} distinct 200 bodies for "
                         f"{url}; admission needs exactly one")
    return hits.pop()


def dest_for(d: dict) -> Path:
    return REPO / "corpus" / DOCUMENT_DIR / f"{d['doc_id']}.{d['fmt']}"


def record_for(d: dict, sha: str, now: str) -> dict:
    return {"import_key": d["doc_id"], "normalized": {
        "source_id": SOURCE_ID, "doc_id": d["doc_id"], "doc_id_exact": True,
        "title": d["title"], "authors_or_org": d["authors"], "pub_year": d["pub_date"][:4],
        "doc_type": d["source_type"], "source_url": d["fetched_url"],
        "local_path": dest_for(d).relative_to(REPO).as_posix(), "expected_sha256": sha,
        "acquisition_method": "scripted_fetch", "acquired_by": "scripts/fetch_allowlisted.py",
        "decision": "included", "rationale": RATIONALE, "decided_by": "cc", "decided_at": now,
        "notes": f"fetched robots-first under the identified UA ({FETCH_LOG.relative_to(REPO)}). "
                 f"{d['notes']}"}}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)

    cfg = dixie_config(REPO / "dixie_evidence.yaml")
    if DOCUMENT_DIR not in cfg["document_dirs"]:
        raise SystemExit(f"FATAL: `{DOCUMENT_DIR}` is not a document_dir in dixie_evidence.yaml")
    dlog = DixieLog(cfg["evidence_dir_abs"] / "decisions.jsonl")
    ledger = build_manifest(dlog, gate_cfg=cfg.get("identity_gate"))
    in_stream = {e["doc_id"] for e in manifest._load_entries()}
    now = datetime.now(timezone.utc).isoformat()

    plan = []
    for d in DOCS:
        src = STAGING / d["staged"]
        if not src.is_file():
            raise SystemExit(f"FATAL: {src} is not in hand")
        sha = hashlib.sha256(src.read_bytes()).hexdigest()
        want = fetched_sha(d["fetched_url"])
        if sha != want:
            raise SystemExit(f"FATAL: {src} hashes to {sha}; the fetch log recorded {want}")
        plan.append((d, src, sha))

    if a.dry_run:
        print(json.dumps({"epoch": EPOCH, "documents": [
            {"doc_id": d["doc_id"], "sha256": sha, "dest": str(dest_for(d).relative_to(REPO)),
             "in_ledger": d["doc_id"] in ledger, "in_event_stream": d["doc_id"] in in_stream}
            for d, _, sha in plan]}, indent=1))
        return 0

    fresh = []
    for d, src, sha in plan:
        dest = dest_for(d)
        if d["doc_id"] in ledger:
            print(f"ledger: {d['doc_id']} already admitted; skipping its steps 2 to 3")
            continue
        if dest.exists() and hashlib.sha256(dest.read_bytes()).hexdigest() != sha:
            raise SystemExit(f"FATAL: {dest} exists with other bytes; refusing to overwrite")
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        dlog.append("screening_imported", record_for(d, sha, now))
        fresh.append(d["doc_id"])

    if fresh:
        actions = Sweep(cfg, dlog).run()
        entries = build_manifest(dlog, gate_cfg=cfg.get("identity_gate"))
        bad = {doc: (entries.get(doc) or {}).get("screening", {}).get("decision")
               for doc in fresh
               if not (entries.get(doc)
                       and entries[doc]["screening"]["decision"] == "included"
                       and entries[doc]["integrity"]["status"] == "verified"
                       and entries[doc]["identity"].get("canonical_path"))}
        if bad:
            raise SystemExit(f"FATAL: post-sweep, not included+verified: {bad}. Nothing is "
                             f"declared for an epoch they did not enter.")
        dlog.append("corpus_epoch_declared", {
            "epoch": EPOCH, "member_doc_ids": fresh, "declared_by": "cc", "task": TASK,
            "note": ("DCAT-US 3.0 (Implementation Guide, M-25-05 crosswalk, supporting-class "
                     "pages, the rewritten Dataset page, the candidate-recommendation draft) "
                     "with StatDCAT-AP 1.0.1 and W3C DQV, for DN-011-R2.")})
        out = manifest.rebuild()
        print(json.dumps({"admitted": fresh, "epoch": EPOCH, "sweep_actions": actions,
                          "manifest": out}, indent=1, default=str))

    for d, _, sha in plan:
        if d["doc_id"] in in_stream:
            print(f"event stream: {d['doc_id']} already has manifest_add")
            continue
        dest = dest_for(d)
        manifest.add(str(dest), doc_id=d["doc_id"], title=d["title"], authors=d["authors"],
                     pub_date=d["pub_date"], source_type=d["source_type"],
                     primary_url=d["fetched_url"], inclusion_rationale=RATIONALE,
                     discovered_via=SOURCE_ID, construct_arm="publication_actionability",
                     grounding_surface="document",
                     acquisition={"acquisition_method": "scripted_fetch",
                                  "acquired_by": "scripts/fetch_allowlisted.py",
                                  "fetch_log": FETCH_LOG.relative_to(REPO).as_posix(),
                                  "verification": {"sha256": sha},
                                  "validation": {"bytes": dest.stat().st_size,
                                                 "format": d["fmt"]},
                                  "corpus_epoch": EPOCH, "task": TASK})
        print(f"event stream: manifest_add written for {d['doc_id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
