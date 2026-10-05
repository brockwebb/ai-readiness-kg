#!/usr/bin/env python3
"""Admit the FAIRness Project record and the CDO Council Data Sharing Working Group report.
**Zero model spend, no network.**

`cc_tasks/2026-10-04_DCAT-002_ADDENDUM_01_base_standard_and_fairness_record.md`, items 10 to
15, implementing DN-011-R4 (`docs/design/2026-10-04_DN-011_dcat_us_3_intake.md`). Every file
was fetched by `scripts/fetch_allowlisted.py` into `corpus/staging/dcat_002_a01/` (inert,
CLAUDE.md invariant 2), robots-first under the identified UA, and
`logs/2026-10-05_DCAT-002_A01_fetch.jsonl` has one line per request. This script contacts
nothing.

The path is `scripts/admit_dcat_us_3.py`'s (DCAT-002's base admission), for four documents:
staged sha256 must equal the fetch log's 200 body, copy to `corpus/crosswalk/`, dixie
`screening_imported` (`included`, criterion R1 of `cc_tasks/2026-08-24_source_triage.md`),
the sweep, one `corpus_epoch_declared` (`dcat-us-3-a01-2026-10-05`), `manifest.rebuild()`,
then `kg.manifest.add` per document.

**What the addendum named and this script does not admit**, each recorded in the RESULT:

* item 10, W3C DCAT 3, and item 15, FCSM 20-04, are held already (`w3c-dcat-3`,
  `fcsm-20-04-a-framework-for-data-quality`): R5, dedupe;
* item 11, the CDOC/FCSM "Implementing DCAT-US 3.0 Sequencing Plan" of 2024-08-05 (the
  Implementation Guide's footnote 11), has no public copy: the B3.3 deck admitted here says
  of it "Status: Provided to Office of Management and Budget";
* item 12's findings, recommendations and sequencing plan are that same unpublished plan (B3.3
  slide 6: "The plan includes: Key findings and recommendations"). The wiki's Home and
  Project-Overview pages, which state the project's aims, problem and three deliverables, are
  admitted; its topic pages are not (explainers, one a ChatGPT transcript, three answer 404).

Each step is skipped when already done, so re-running the script is the resume.

    /opt/anaconda3/bin/python3 scripts/admit_dcat_002_a01.py --dry-run
    /opt/anaconda3/bin/python3 scripts/admit_dcat_002_a01.py
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

TASK = "cc_tasks/2026-10-04_DCAT-002_ADDENDUM_01_base_standard_and_fairness_record.md"
EPOCH = "dcat-us-3-a01-2026-10-05"
SOURCE_ID = "dcat_002_a01_2026-10-05"
FETCH_LOG = REPO / "logs" / "2026-10-05_DCAT-002_A01_fetch.jsonl"
STAGING = REPO / "corpus" / "staging" / "dcat_002_a01"
DOCUMENT_DIR = "crosswalk"
WIKI = ["CDOC/FCSM FAIRness Project (GitHub DOI-DO/dcat-us wiki)"]
RATIONALE = (f"{TASK} (DN-011-R4): the statistical side's own record of what the FAIRness "
             f"Project asked of DCAT-US 3.0, so that what FCSM advised can be set against what "
             f"3.0 delivers. Criterion R1 (cc_tasks/2026-08-24_source_triage.md): metadata "
             f"standards and their federal record, err inclusive.")

#: `fetched_url` is the URL of the 200 response whose body is the staged file. Its sha256 is
#: read from the fetch log, never typed.
DOCS = [
    dict(doc_id="fairness-project-wiki-home", staged="00_probe/Home.md",
         fetched_url="https://raw.githubusercontent.com/wiki/DOI-DO/dcat-us/Home.md",
         title="Welcome to the CDOC/FCSM FAIRness Project (DCAT-US 3 project wiki, Home)",
         authors=WIKI, pub_date="2023-10-26", source_type="federal", fmt="md",
         arm="publication_actionability", surface="document",
         notes="The wiki's source markdown; the rendered page is "
               "https://github.com/DOI-DO/dcat-us/wiki (last edited 2023-10-26T18:20:25Z, "
               "read from that page). States the project's aims and the key features of the "
               "draft DCAT-US v3.0 schema, during the 2023 comment period."),
    dict(doc_id="fairness-project-wiki-project-overview", staged="00_probe/Project-Overview.md",
         fetched_url="https://raw.githubusercontent.com/wiki/DOI-DO/dcat-us/Project-Overview.md",
         title="FAIRness Project: Project Overview (DCAT-US 3 project wiki)",
         authors=WIKI, pub_date="2023-09-12", source_type="federal", fmt="md",
         arm="publication_actionability", surface="document",
         notes="The wiki's source markdown; the rendered page is "
               "https://github.com/DOI-DO/dcat-us/wiki/Project-Overview (last edited "
               "2023-09-12T15:16:41Z). States the three deliverables (governance model, "
               "DCAT-US 3 profile, two-year sequencing plan), the problem and the three-phase "
               "schema governance process."),
    dict(doc_id="fcsm-2024-b3-3-fairness-project", staged="00_probe/B3.3_Dabolt.pdf",
         fetched_url=("https://statspolicy.gov/assets/fcsm/files/docs/2024-conference-docs/B/"
                      "B3.3_Dabolt.pdf"),
         title="The FAIRness Project: Building Trust and FAIRness into Finding and Using "
               "Government Data (FCSM 2024 Research and Policy Conference, session B3.3)",
         authors=["Thomas Dabolt (DOI)", "Michael Ratcliffe (U.S. Census Bureau)"],
         pub_date="2024-10-30", source_type="federal", fmt="pdf",
         arm="publication_actionability", surface="slides",
         notes="8 slides; PDF created 2024-10-30. The project co-chairs' status report: core "
               "team and advisory group, the three deliverables, and the status of each "
               "(schema finalized for OMB; sequencing plan, with its key findings and "
               "recommendations, and governance plan provided to OMB)."),
    dict(doc_id="cdoc-dswg-findings-and-recommendations-2022",
         staged="04_dswg/2021_DSWG_Recommendations_and_Findings_508.pdf",
         fetched_url=("https://resources.data.gov/assets/documents/"
                      "2021_DSWG_Recommendations_and_Findings_508.pdf"),
         title="Data Sharing Working Group: Findings & Recommendations (Federal CDO Council)",
         authors=["Federal Chief Data Officers Council, Data Sharing Working Group"],
         pub_date="2022-03-30", source_type="federal", fmt="pdf",
         arm="org_maturity", surface="document",
         notes="26 pages. PDF created 2022-03-28, modified 2022-03-30; the resources.data.gov "
               "landing page says 'Originally published 2022' and GAO-23-105514 dates it April "
               "2022. The file name's '2021' is the working group's year. cdo.gov's copy was "
               "not fetched: its robots.txt was unreachable, which RFC 9309 §2.3.1.4 reads as "
               "complete disallow."),
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
            "note": ("The FAIRness Project record (wiki Home and Project Overview, the FCSM "
                     "2024 B3.3 deck) and the CDO Council Data Sharing Working Group report, "
                     "for DN-011-R4.")})
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
                     discovered_via=SOURCE_ID, construct_arm=d["arm"],
                     grounding_surface=d["surface"],
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
