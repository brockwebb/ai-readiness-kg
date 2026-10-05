#!/usr/bin/env python3
"""Admit the DCAT-US 3.0 Dataset page and Overview as served on 2026-10-05, as dated versions of
the 2026-08-21 captures. **Zero model spend, no network.**

`cc_tasks/2026-10-05_DCAT-003_ADDENDUM_01_faq_shippability.md` step 4: "Fetch the live
DCAT-US 3.0 Dataset page and Overview through the document-admission path, as a new dated
version." Both files were fetched by `scripts/fetch_allowlisted.py` into
`corpus/staging/dcat_003a/` (inert, CLAUDE.md invariant 2), robots-first under the identified
UA, and `logs/2026-10-05_DCAT-003a_fetch.jsonl` has one line per request. This script contacts
nothing.

The path is `scripts/admit_dcat_us_3.py`'s (DCAT-002), for two documents, with one difference:
the corpus already holds both URLs (`dcat-us-3-dataset-schema`, `dcat-us-3-overview`, captured
2026-08-21), so each is admitted as a dated version of the held capture
(`manifest.add(version_of=..., retrieved_at=...)`, DD-068: RFC 7089's original resource with
dated mementos, and the WARC record's target URI plus capture date). The 2026-08-21 captures
are not touched; RULE-B4-v1 and RULE-D3-v1 cite the Dataset one.

  1. the staged file must hash to the sha256 the fetch log recorded for its 200 response, or
     nothing is admitted; `retrieved_at` is that response's log timestamp;
  2. it is copied to `corpus/crosswalk/<doc_id>.html`, the lane DCAT-002 used;
  3. dixie `screening_imported` (`included`, criterion R1 of
     `cc_tasks/2026-08-24_source_triage.md`), with `doc_id_exact` so the ledger never merges it
     with the held capture by URL; then the sweep observes and integrity-checks;
  4. one `corpus_epoch_declared`, `dcat-us-3-live-2026-10-05`;
  5. `manifest.rebuild()`, then `kg.manifest.add` per document, which runs the convertibility
     gate and writes the substrate the FAQ's element table reads.

Each step is skipped when already done, so re-running the script is the resume.

    /opt/anaconda3/bin/python3 scripts/admit_dcat_us_3_live_2026_10_05.py --dry-run
    /opt/anaconda3/bin/python3 scripts/admit_dcat_us_3_live_2026_10_05.py
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

TASK = "cc_tasks/2026-10-05_DCAT-003_ADDENDUM_01_faq_shippability.md"
EPOCH = "dcat-us-3-live-2026-10-05"
SOURCE_ID = "dcat_003a_2026-10-05"
FETCH_LOG = REPO / "logs" / "2026-10-05_DCAT-003a_fetch.jsonl"
STAGING = REPO / "corpus" / "staging" / "dcat_003a"
DOCUMENT_DIR = "crosswalk"
GSA = ["U.S. General Services Administration / Data.gov"]
RATIONALE = (f"{TASK} step 4: the DCAT-US 3.0 page as served on 2026-10-05, a dated version of "
             f"the corpus's 2026-08-21 capture (DD-068), so every requirement level the "
             f"briefing FAQ states can name the version it reads. Criterion R1 "
             f"(cc_tasks/2026-08-24_source_triage.md): a metadata standard.")

DOCS = [
    dict(doc_id="dcat-us-3-dataset-schema-2026-10-05", version_of="dcat-us-3-dataset-schema",
         staged="dataset", url="https://resources.data.gov/standards/catalog/dcat-us-3/dataset/",
         title="DCAT-US 3.0 Schema: Dataset (resources.data.gov; as served 2026-10-05)",
         notes="The Dataset page as served on 2026-10-05, byte-identical to the live fetch "
               "DCAT-002 logged at 02:14Z that day (sha256 3b5cbb2d...). Its per-property "
               "Requirement lines give the same level as the 2026-09-15 capture "
               "(dcat-us-3-dataset-schema-2026-09-15) for all 62 properties: Mandatory are "
               "contactPoint, description, identifier and title; publisher is Recommended."),
    dict(doc_id="dcat-us-3-overview-2026-10-05", version_of="dcat-us-3-overview",
         staged="dcat-us3", url="https://resources.data.gov/resources/dcat-us3/",
         title="DCAT-US 3.0 Overview (resources.data.gov; as served 2026-10-05)",
         notes="The Overview as served on 2026-10-05, after the rewrite its changelog dates "
               "September 2026. Against the corpus's 2026-08-21 capture, the 'Breaking "
               "changes', 'Fields replaced or removed' and 'Structural changes' tables are gone "
               "from 'Changes from v1.1'. The site's glossary is loaded by glossary.js from a "
               "separate resource and is not in this HTML; the 2026-08-21 capture was "
               "browser-rendered and carries it."),
]


def fetched(url: str) -> tuple[str, str]:
    """(sha256, timestamp) the fetch log recorded for the 200 response at `url`. Exactly one
    body, or stop."""
    rows = [json.loads(l) for l in FETCH_LOG.read_text(encoding="utf-8").splitlines() if l]
    hits = [r for r in rows if r.get("event") == "request" and r.get("url") == url
            and r.get("status") == 200]
    if len({r["sha256"] for r in hits}) != 1:
        raise SystemExit(f"FATAL: {FETCH_LOG.name} records {len({r['sha256'] for r in hits})} "
                         f"distinct 200 bodies for {url}; admission needs exactly one")
    return hits[0]["sha256"], hits[0]["ts"]


def dest_for(d: dict) -> Path:
    return REPO / "corpus" / DOCUMENT_DIR / f"{d['doc_id']}.html"


def record_for(d: dict, sha: str, now: str) -> dict:
    return {"import_key": d["doc_id"], "normalized": {
        "source_id": SOURCE_ID, "doc_id": d["doc_id"], "doc_id_exact": True,
        "title": d["title"], "authors_or_org": GSA, "pub_year": "2026",
        "doc_type": "standard", "source_url": d["url"],
        "local_path": dest_for(d).relative_to(REPO).as_posix(), "expected_sha256": sha,
        "acquisition_method": "scripted_fetch", "acquired_by": "scripts/fetch_allowlisted.py",
        "decision": "included", "rationale": RATIONALE, "decided_by": "cc", "decided_at": now,
        "notes": f"fetched robots-first under the identified UA ({FETCH_LOG.relative_to(REPO)}). "
                 f"Dated version of {d['version_of']} (DD-068). {d['notes']}"}}


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
        want, ts = fetched(d["url"])
        if sha != want:
            raise SystemExit(f"FATAL: {src} hashes to {sha}; the fetch log recorded {want}")
        if d["version_of"] not in in_stream:
            raise SystemExit(f"FATAL: {d['version_of']} is not admitted; nothing to version")
        plan.append((d, src, sha, ts))

    if a.dry_run:
        print(json.dumps({"epoch": EPOCH, "documents": [
            {"doc_id": d["doc_id"], "version_of": d["version_of"], "retrieved_at": ts,
             "sha256": sha, "dest": str(dest_for(d).relative_to(REPO)),
             "in_ledger": d["doc_id"] in ledger, "in_event_stream": d["doc_id"] in in_stream}
            for d, _, sha, ts in plan]}, indent=1))
        return 0

    fresh = []
    for d, src, sha, _ in plan:
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
            "note": ("The DCAT-US 3.0 Dataset page and Overview as served on 2026-10-05, dated "
                     "versions of the 2026-08-21 captures (DD-068), for the briefing FAQ.")})
        out = manifest.rebuild()
        print(json.dumps({"admitted": fresh, "epoch": EPOCH, "sweep_actions": actions,
                          "manifest": out}, indent=1, default=str))

    for d, _, sha, ts in plan:
        if d["doc_id"] in in_stream:
            print(f"event stream: {d['doc_id']} already has manifest_add")
            continue
        dest = dest_for(d)
        manifest.add(str(dest), doc_id=d["doc_id"], title=d["title"], authors=GSA,
                     pub_date="2026-10-05", source_type="standard", primary_url=d["url"],
                     inclusion_rationale=RATIONALE, discovered_via=SOURCE_ID,
                     construct_arm="publication_actionability", grounding_surface="document",
                     version_of=d["version_of"], retrieved_at=ts,
                     acquisition={"acquisition_method": "scripted_fetch",
                                  "acquired_by": "scripts/fetch_allowlisted.py",
                                  "fetch_log": FETCH_LOG.relative_to(REPO).as_posix(),
                                  "verification": {"sha256": sha},
                                  "validation": {"bytes": dest.stat().st_size, "format": "html"},
                                  "corpus_epoch": EPOCH, "task": TASK})
        print(f"event stream: manifest_add written for {d['doc_id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
