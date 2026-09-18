#!/usr/bin/env python3
"""Admit the open-tool documents through the designed path. **Zero model spend, no network.**

Task `cc_tasks/2026-09-18_tool_docs_ingest.md` §1, decision 1. The files are already in hand:
`scripts/fetch_allowlisted.py` fetched them robots-first under the identified UA, from the hosts
the task's `**Network:**` header declared, and `logs/2026-09-18_tool_docs_ingest_fetch.jsonl`
has one line per request. This script contacts nothing.

The path is `scripts/admit_esip_checklist.py`'s, which is `scripts/manifest_triage.py`'s:

  1. each file sits in a `document_dir` (`corpus/tools/`, added to `dixie_evidence.yaml` with
     this task's citation, one subdirectory per tool because both files are a `README.md`);
  2. the dixie ledger gets `screening_imported` per document, then the sweep observes and
     integrity-checks;
  3. `corpus_epoch_declared`, so the admission names the task that ordered it;
  4. `manifest.rebuild()` — `corpus/manifest.json` is the ledger's projection.

No `manifest_add` event is written: these are reference documents for tiering, not extraction
inputs, and the event stream is the extraction-admission gate (CLAUDE.md invariant 2).

**`doc_type` is `industry`, not the task's `reference`.** `reference` is not a value of
`Document.source_type` in `kg/schema.yaml`, and the type catalogue changes only through its
review (invariant 4). The one tool README already in the ledger, `extruct-readme`, is
`industry`; these follow it.

    /opt/anaconda3/bin/python3 scripts/admit_tool_docs.py --dry-run
    /opt/anaconda3/bin/python3 scripts/admit_tool_docs.py
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

TASK = "cc_tasks/2026-09-18_tool_docs_ingest.md"
EPOCH = "tool-docs-2026-09-18"
SOURCE_ID = "tool_docs_2026-09-18"
FETCH_LOG = "logs/2026-09-18_tool_docs_ingest_fetch.jsonl"

#: One entry per admitted document. `sha256` is the digest the fetch log recorded for the
#: 200 response; the file on disk must still hash to it, or nothing is admitted.
DOCS = [
    dict(
        doc_id="oasdiff-readme",
        path=REPO / "corpus" / "tools" / "oasdiff" / "README.md",
        sha256="9ec7fc519ccca54867f545950bf1e2744223ea6a2bdd7b1ff860deeefe59cfbb",
        title="oasdiff README",
        authors_or_org=["oasdiff (github.com/oasdiff)"],
        source_url="https://github.com/oasdiff/oasdiff",
        fetched_from="https://raw.githubusercontent.com/oasdiff/oasdiff/main/docs/README.md",
        indicators=["F2"],
        notes=("The repository keeps its README at docs/README.md, not at the root: the root "
               "raw URL answered 404 on both `main` and `HEAD`, and the landing page "
               "github.com/oasdiff/oasdiff (fetched through the same helper) lists "
               "docs/README.md with defaultBranch `main` at currentOid "
               "322d7ae815e5fb80f415bd4e8ef16d4b30cd8bdf, 15 s before this fetch. The raw "
               "response itself carries no commit."),
    ),
    dict(
        doc_id="wayback-cdx-server-api-readme",
        path=REPO / "corpus" / "tools" / "wayback-cdx-server" / "README.md",
        sha256="e17a0e1f43c4dd887adbb1473a7be452bbc12f823b64ea3fda2105c8d27ee7dd",
        title="Wayback CDX Server API - BETA",
        authors_or_org=["Internet Archive"],
        source_url="https://github.com/internetarchive/wayback/tree/master/wayback-cdx-server",
        fetched_from=("https://raw.githubusercontent.com/internetarchive/wayback/master/"
                      "wayback-cdx-server/README.md"),
        indicators=["A7", "F3"],
        notes=("Undated; its changelist's latest entry is 2013-08-07. The Internet Archive's "
               "own page tried at https://archive.org/developers/wayback-cdx-server.html "
               "answered 404 and is not admitted; the failure is in the fetch log."),
    ),
]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)

    cfg = dixie_config(REPO / "dixie_evidence.yaml")
    if "tools" not in cfg["document_dirs"]:
        raise SystemExit("FATAL: `tools` is not a document_dir in dixie_evidence.yaml; the "
                         "sweep would never observe corpus/tools/")
    dlog = DixieLog(cfg["evidence_dir_abs"] / "decisions.jsonl")
    ledger = build_manifest(dlog, gate_cfg=cfg.get("identity_gate"))

    records = []
    for d in DOCS:
        if not d["path"].is_file():
            raise SystemExit(f"FATAL: {d['path']} is not in hand; admission requires the "
                             f"artifact and its hash, never a promise of one")
        sha = hashlib.sha256(d["path"].read_bytes()).hexdigest()
        if sha != d["sha256"]:
            raise SystemExit(f"FATAL: {d['path']} hashes to {sha}, and the fetch log "
                             f"recorded {d['sha256']}; the file is not the one fetched")
        if d["doc_id"] in ledger:
            raise SystemExit(f"FATAL: {d['doc_id']} is already in the ledger")
        records.append({
            "import_key": d["doc_id"],
            "normalized": {
                "source_id": SOURCE_ID, "doc_id": d["doc_id"], "doc_id_exact": True,
                "title": d["title"], "authors_or_org": d["authors_or_org"],
                "pub_year": "n.d.", "doc_type": "industry",
                "source_url": d["source_url"],
                "local_path": d["path"].relative_to(REPO).as_posix(),
                "expected_sha256": sha,
                "acquisition_method": "scripted_fetch",
                "acquired_by": "scripts/fetch_allowlisted.py",
                "decision": "included",
                "rationale": (
                    f"{TASK} decision 1: the documentation of the open tool that "
                    f"{', '.join(d['indicators'])} "
                    f"{'names' if len(d['indicators']) == 1 else 'name'} as "
                    f"`open_tool_candidate`, so that "
                    f"decision 2 can cite a section of it for tier O (DN-005 §2.2)."),
                "decided_by": "cc", "decided_at": datetime.now(timezone.utc).isoformat(),
                "notes": (f"fetched robots-first under the identified UA from "
                          f"{d['fetched_from']} ({FETCH_LOG}). {d['notes']}"),
            }})

    if a.dry_run:
        print(json.dumps({"epoch": EPOCH, "records": records}, indent=1, ensure_ascii=False))
        return 0

    for r in records:
        dlog.append("screening_imported", r)
    actions = Sweep(cfg, dlog).run()
    entries = build_manifest(dlog, gate_cfg=cfg.get("identity_gate"))
    for d in DOCS:
        e = entries.get(d["doc_id"])
        ok = (e and e["screening"]["decision"] == "included"
              and e["integrity"]["status"] == "verified"
              and e["identity"].get("canonical_path"))
        if not ok:
            raise SystemExit(f"FATAL: post-sweep, {d['doc_id']} is not included+verified: "
                             f"{e and (e['screening']['decision'], e['integrity']['status'])}. "
                             f"Nothing is declared for an epoch it did not enter.")
    dlog.append("corpus_epoch_declared", {
        "epoch": EPOCH, "member_doc_ids": [d["doc_id"] for d in DOCS], "declared_by": "cc",
        "task": TASK,
        "note": ("Open-tool documentation for tier O (DN-005 §2.2): oasdiff for F2, the "
                 "Wayback CDX Server API for A7 and F3. The Internet Archive's own API page "
                 "at archive.org/developers/ answered 404 and is not a member.")})
    out = manifest.rebuild()
    print(json.dumps({"admitted": [d["doc_id"] for d in DOCS], "epoch": EPOCH,
                      "sweep_actions": actions, "manifest": out}, indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
