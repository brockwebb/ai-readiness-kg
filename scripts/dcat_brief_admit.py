#!/usr/bin/env python3
"""Admit the statistical information models DCAT-004 v2 names, and decline what could not be
fetched. **Zero model spend, no network.**

`cc_tasks/2026-10-07_DCAT-004_v2_plain_language_brief_and_verdict.md` decision 1 (as amended
in v2), under DN-011-R4 (`docs/design/2026-10-04_DN-011_dcat_us_3_intake.md`). Every file was
fetched by `scripts/fetch_allowlisted.py` into `corpus/staging/dcat_004/` (inert, CLAUDE.md
invariant 2) under the task's allowlist (sdmx.org, ddialliance.org, unece.org,
statswiki.unece.org), robots-first under the identified UA, and
`logs/2026-10-07_DCAT-004_fetch.jsonl` has one line per request. This script contacts nothing.

The path is `scripts/admit_dcat_002_a01.py`'s, unchanged: staged sha256 must equal the fetch
log's 200 body, copy to `corpus/kernel/` (where SDMX 3.0 section 1 and the W3C statistical
vocabularies already sit), dixie `screening_imported` (`included`), the sweep, one
`corpus_epoch_declared` (`dcat-us-3-brief-2026-10-07`), `manifest.rebuild()`, then
`kg.manifest.add` per document. The task names `kg/assess.py` as the admission path; no such
module exists in this repository (checked 2026-10-07), and this dixie-plus-manifest path is
the one every DCAT admission has used.

**Admitted:**

* SDMX Section 2, the information model, at its current version 3.1 (title page: "Version
  3.1 | May 2025"). The corpus holds SDMX 3.0 Section 1; the version mismatch is recorded on
  the ledger entry rather than admitting a superseded Section 2 to match it (v2 decision 1).
* DDI-CDI 1.0, the published specification (title page: "DDI - Cross Domain Integration:
  Specification Overview | Version 1.0 Release"), from ddialliance.org, which redirected the
  task's URL to `/hubfs/` on the same host.

**Declined, with the reason on the ledger** (`decision: excluded`, never a to-do): UNECE GSIM.
Both UNECE hosts answered 403 to every request from the identified client on 2026-10-07,
`robots.txt` included (`unece.org/statistics/modernstats/gsim`, `statswiki.unece.org/display/gsim`,
`statswiki.unece.org/`). The version could not be read from the publisher's page, so none is
recorded.

Each step is skipped when already done, so re-running the script is the resume.

    /opt/anaconda3/bin/python3 scripts/dcat_brief_admit.py --dry-run
    /opt/anaconda3/bin/python3 scripts/dcat_brief_admit.py
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

TASK = "cc_tasks/2026-10-07_DCAT-004_v2_plain_language_brief_and_verdict.md"
EPOCH = "dcat-us-3-brief-2026-10-07"
SOURCE_ID = "dcat_004_2026-10-07"
FETCH_LOG = REPO / "logs" / "2026-10-07_DCAT-004_fetch.jsonl"
STAGING = REPO / "corpus" / "staging" / "dcat_004"
DOCUMENT_DIR = "kernel"
RATIONALE = (f"{TASK} decision 1 (DN-011-R4): the statistical side's own information models, "
             f"so that 'how the literature carries it' (DN-011-R6 question 3) can be read for "
             f"series, dimensions, units, uncertainty, methodology, revisions, quality and "
             f"access terms. Criterion R1 (cc_tasks/2026-08-24_source_triage.md): metadata "
             f"standards and their record, err inclusive.")

#: `fetched_url` is the URL of the 200 response whose body is the staged file. Its sha256 is
#: read from the fetch log, never typed. `requested_url` is the URL the task names.
DOCS = [
    dict(doc_id="sdmx-3-1-section-2-information-model",
         staged="SDMX_3-1-0_SECTION_2_FINAL.pdf",
         requested_url="https://sdmx.org/wp-content/uploads/SDMX_3-1-0_SECTION_2_FINAL.pdf",
         fetched_url="https://sdmx.org/wp-content/uploads/SDMX_3-1-0_SECTION_2_FINAL.pdf",
         title="SDMX Standards, Section 2: Information Model: UML Conceptual Design, Version 3.1",
         authors=["SDMX Technical Working Group"], pub_date="2025-05", source_type="standard",
         fmt="pdf", arm="publication_actionability", surface="document",
         notes="163 pages. Title page: 'Version 3.1 | May 2025'; revision history: '1.0 May "
               "2025 Public Release for SDMX 3.1' (it also lists 'DRAFT 1.0 December 2025 "
               "Draft release updated for SDMX 3.1 for public consultation', as printed). "
               "VERSION MISMATCH, recorded and not reconciled: the corpus holds SDMX 3.0 "
               "Section 1 (sdmx-3-0-section-1-framework, 2021); Section 2 is admitted at its "
               "current version 3.1, which superseded 3.0, rather than a superseded 3.0 "
               "Section 2 to match it (DCAT-004 v2 decision 1)."),
    dict(doc_id="ddi-cdi-1-0-specification",
         staged="DDI-CDI_Model_Specification.pdf",
         requested_url="https://ddialliance.org/Specification/DDI-CDI/1.0/DDI-CDI_Model_Specification.pdf",
         fetched_url=("https://ddialliance.org/hubfs/Specification/DDI-CDI/1.0/"
                      "DDI-CDI_Model_Specification.pdf"),
         title="DDI - Cross Domain Integration (DDI-CDI): Specification Overview, Version 1.0",
         authors=["DDI Alliance"], pub_date="2025-01-24", source_type="standard",
         fmt="pdf", arm="publication_actionability", surface="document",
         notes="92 pages. Title page: 'DDI - Cross Domain Integration: Specification "
               "Overview | Version 1.0 Release', 'DDI Alliance 2025'; PDF created "
               "2025-01-24. The task's URL answered 301 to the /hubfs/ path on the same "
               "host (fetch log)."),
]

#: Declined: a `screening_imported` with `decision: excluded` and the reason, the ledger's
#: standing form for a document looked for and not admitted.
DECLINED = [
    dict(doc_id="unece-gsim", title="Generic Statistical Information Model (GSIM), UNECE",
         authors=["UNECE High-Level Group for the Modernisation of Official Statistics"],
         source_type="intergovernmental",
         source_url="https://unece.org/statistics/modernstats/gsim",
         urls=["https://unece.org/statistics/modernstats/gsim",
               "https://statswiki.unece.org/display/gsim", "https://statswiki.unece.org/"],
         rationale=("Declined, not fetchable from an allowlisted host: on 2026-10-07 both UNECE "
                    "hosts on the task's allowlist answered HTTP 403 to every request from the "
                    "identified client, robots.txt included (unece.org/robots.txt, "
                    "unece.org/statistics/modernstats/gsim, statswiki.unece.org/robots.txt, "
                    "statswiki.unece.org/display/gsim, statswiki.unece.org/). The current "
                    "version could not be read from the publisher's page, so none is recorded. "
                    f"{TASK} decision 1: a document that cannot be fetched from an allowlisted "
                    f"host is declined with the reason in the manifest, never a to-do.")),
]


def fetch_rows() -> list:
    return [json.loads(l) for l in FETCH_LOG.read_text(encoding="utf-8").splitlines() if l]


def fetched_sha(url: str) -> str:
    """The sha256 the fetch log recorded for the 200 response at `url`. Exactly one, or stop."""
    hits = {r["sha256"] for r in fetch_rows()
            if r.get("event") == "request" and r.get("url") == url and r.get("status") == 200}
    if len(hits) != 1:
        raise SystemExit(f"FATAL: {FETCH_LOG.name} records {len(hits)} distinct 200 bodies for "
                         f"{url}; admission needs exactly one")
    return hits.pop()


def refusals(urls: list) -> list:
    """The fetch log's status for each URL a decline names; every one must be a non-200."""
    out = []
    for u in urls:
        rows = [r for r in fetch_rows() if r.get("url") == u]
        if not rows:
            raise SystemExit(f"FATAL: {FETCH_LOG.name} has no request for {u}; a decline "
                             f"must rest on a logged attempt")
        if any(r.get("status") == 200 for r in rows):
            raise SystemExit(f"FATAL: {u} answered 200; it is not a decline")
        out.append({"url": u, "status": rows[-1]["status"], "ts": rows[-1]["ts"]})
    return out


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


def decline_record(d: dict, now: str) -> dict:
    tried = refusals(d["urls"])
    return {"import_key": d["doc_id"], "normalized": {
        "source_id": SOURCE_ID, "doc_id": d["doc_id"], "doc_id_exact": True,
        "title": d["title"], "authors_or_org": d["authors"], "doc_type": d["source_type"],
        "source_url": d["source_url"], "decision": "excluded", "status": "excluded",
        "rationale": d["rationale"], "decided_by": "cc", "decided_at": now,
        "notes": "attempts (fetch log " + FETCH_LOG.relative_to(REPO).as_posix() + "): "
                 + "; ".join(f"{t['url']} -> {t['status']} at {t['ts']}" for t in tried)}}


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
    declines = [(d, decline_record(d, now)) for d in DECLINED]

    if a.dry_run:
        print(json.dumps({"epoch": EPOCH, "documents": [
            {"doc_id": d["doc_id"], "sha256": sha, "dest": str(dest_for(d).relative_to(REPO)),
             "in_ledger": d["doc_id"] in ledger, "in_event_stream": d["doc_id"] in in_stream}
            for d, _, sha in plan],
            "declined": [{"doc_id": d["doc_id"], "in_ledger": d["doc_id"] in ledger,
                          "notes": r["normalized"]["notes"]} for d, r in declines]}, indent=1))
        return 0

    for d, rec in declines:
        if d["doc_id"] in ledger:
            print(f"ledger: {d['doc_id']} already recorded; skipping its decline")
            continue
        dlog.append("screening_imported", rec)
        print(f"ledger: {d['doc_id']} declined: {rec['normalized']['notes']}")

    fresh = []
    for d, src, sha in plan:
        dest = dest_for(d)
        if d["doc_id"] in ledger:
            print(f"ledger: {d['doc_id']} already admitted; skipping its ledger steps")
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
            "note": ("SDMX 3.1 Section 2 (information model) and DDI-CDI 1.0, the statistical "
                     "information models DCAT-004 v2 decision 1 names; UNECE GSIM declined "
                     "(publisher hosts refused the client).")})
    out = manifest.rebuild()
    if fresh:
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
                     discovered_via=SOURCE_ID, construct_arm=d["arm"],
                     grounding_surface=d["surface"],
                     acquisition={"acquisition_method": "scripted_fetch",
                                  "acquired_by": "scripts/fetch_allowlisted.py",
                                  "fetch_log": FETCH_LOG.relative_to(REPO).as_posix(),
                                  "requested_url": d["requested_url"],
                                  "verification": {"sha256": sha},
                                  "validation": {"bytes": dest.stat().st_size,
                                                 "format": d["fmt"]},
                                  "corpus_epoch": EPOCH, "task": TASK})
        print(f"event stream: manifest_add written for {d['doc_id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
