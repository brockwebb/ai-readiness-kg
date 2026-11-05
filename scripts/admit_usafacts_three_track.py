#!/usr/bin/env python3
"""Admit USAFacts' three-track AI-ready data framework (the August 2026 roundtable deck and the
one-page project overview) from the operator's inbox. **Zero model spend. No network.**

Task `cc_tasks/2026-11-02_admit_usafacts_three_track_framework.md` Part A, under `ADDENDUM_01`
(the two PDFs sit at `corpus/staging/inbox/`, not `corpus/inbox/`). Both are unpublished drafts
distributed at the Partnership for Public Service Federal Data Excellence roundtable on
2026-08-26; the operator placed them in the inbox on 2026-11-02.

**`primary_url` for an unpublished document (premise correction, grounded).** The task directs
`source_url: none`, but an *included* corpus document must carry a `manifest_add` event
(`scripts/build_evidence_map.py::q3_claims` fails hard otherwise, and it uses the first
`manifest_add` date in its corpus-growth claim), and `kg.manifest.add` requires a non-empty,
UNIQUE `primary_url` (`_REQUIRED_FIELDS`, deduped on the normalized URL). Every one of the 289
included documents carries an http(s) URL; the Cisco inbox pages that have `source_url: None` are
`excluded`, not included, so they are not a precedent for an included URL-less doc. These two are
the first genuinely unpublished included documents. Per RFC 8141 a URN is the standard PERSISTENT,
LOCATION-INDEPENDENT identifier for a resource with no network location, so each document's
`primary_url` is a URN: honestly non-dereferenceable, unique, stable. The roundtable event page is
recorded as `discovered_via` exactly as the operator directed — not as the source_url. This is an
internal, reversible, under-cap decision; it is logged here and in the RESULT, not escalated.

Designed path (the pattern of `scripts/admit_measurement_theory_sources.py` / `admit_noaa_naos.py`):
copy each inbox PDF to `corpus/crosswalk/<doc_id>.pdf` -> `kg.manifest.add` (writes the `manifest_add`
event to the KG eventlog: the extraction-admission gate and the Document-node source for
`scripts/build_projection.py`) -> dixie `screening_imported` (decision included, `source_url` the
URN, `local_path` the crosswalk copy) -> `Sweep(cfg, dlog).run()` (observes the file, runs the PDF
integrity gate: magic bytes, size floor, `pdf_min_chars`) -> verify included+verified ->
`corpus_epoch_declared` -> `manifest.rebuild()` (projects manifest.json from the dixie ledger). The
docling markdown the record will quote is produced separately by the project's canonical converter,
`scripts/t1_build_index.py --phase convert` (DD-023 keeps the docling/pypdf-fallback + fidelity
labelling in one place; adopt-before-create).

    /opt/anaconda3/bin/python3 scripts/admit_usafacts_three_track.py --dry-run
    /opt/anaconda3/bin/python3 scripts/admit_usafacts_three_track.py
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

from kg import manifest                                             # noqa: E402
from kg import eventlog                                            # noqa: E402
from worktree_primary import assert_outputs_in_primary             # noqa: E402
from dixie.evidence.config import load_config as dixie_config       # noqa: E402
from dixie.evidence.eventlog import EventLog as DixieLog            # noqa: E402
from dixie.evidence.manifest import build_manifest                  # noqa: E402
from dixie.evidence.sweep import Sweep                              # noqa: E402

TASK = "cc_tasks/2026-11-02_admit_usafacts_three_track_framework.md"
ADDENDUM = "cc_tasks/2026-11-02_admit_usafacts_three_track_framework_ADDENDUM_01.md"
EPOCH = "usafacts-three-track-2026-11-02"
SOURCE_ID = "usafacts_three_track_2026-11-02"
INBOX = REPO / "corpus" / "staging" / "inbox"
DEST_DIR = REPO / "corpus" / "crosswalk"
EVENT_PAGE = ("https://ourpublicservice.org/events/"
              "framework-for-ai-ready-data-2026-federal-data-excellence-roundtable")
DISCOVERED_VIA = (f"operator inbox, per {ADDENDUM}; presented at the Partnership for Public "
                  f"Service Federal Data Excellence roundtable 2026-08-26 ({EVENT_PAGE})")
ACQUISITION_METHOD = "operator_inbox"
ACQUIRED_BY = "operator"
CONSTRUCT_ARM = "publication_actionability"   # the same arm as usafacts-ai-ready-data-guide

#: One entry per document. `expected_sha256` is the hash the operator handed over (task Part A
#: table), verified against the bytes in hand before anything moves. `primary_url` is a URN
#: (RFC 8141) because the document is unpublished and has no network location.
DOCS = [
    dict(
        doc_id="usafacts-ai-ready-framework-deck-2026-08",
        src=INBOX / "USAFacts AI-Ready Data Slide Deck.pdf",
        expected_sha256="9cbe6ae32203f9d015d486765d4b00202e1540c08a3f4a158a5780036abbfb0b",
        primary_url="urn:usafacts:ai-ready-data-framework:2026-08-roundtable:slide-deck",
        title=("AI-Ready Government Data: A Framework for Trust in the Age of AI "
               "(August 2026)"),
        authors=["USAFacts", "Ben Gitis", "Pieter van Noordennen"],
        pub_date="2026-08",
        source_type="practitioner",
        grounding_surface="slides",
        rationale=(
            "USAFacts' successor to usafacts-ai-ready-data-guide: a three-track framework "
            "(Agentic Access, Agentic Context, Agentic Evaluation), three levels within each "
            "track, modeled on SLSA (slsa.dev), with three prerequisites (open by default, "
            "discoverable, clearly licensed). It is the framework the readiness diagnostic "
            "re-parents the sixteen checks onto (DN-019 section 5; DN-020). Unpublished draft, "
            "distributed at the 2026-08-26 Federal Data Excellence roundtable; no public URL "
            "(URN primary_url; the event page is discovered_via). From the operator's inbox copy."),
    ),
    dict(
        doc_id="usafacts-ai-ready-framework-overview-2026",
        src=INBOX / "Overview of USAFacts AI-Ready Data Project.pdf",
        expected_sha256="e47c5bc63d3c70a0ab47a9b029f699ca21d1ea396e3d6dccfd5700747d7876fc",
        primary_url="urn:usafacts:ai-ready-data-framework:2026-08-roundtable:overview",
        title="Overview of USAFacts Project on AI-Ready Government Data",
        authors=["USAFacts"],
        pub_date="2026",
        source_type="practitioner",
        grounding_surface="document",
        rationale=(
            "The one-page overview of the USAFacts AI-ready government data project, distributed "
            "alongside the deck at the 2026-08-26 Federal Data Excellence roundtable. Unpublished "
            "draft, no public URL (URN primary_url; the event page is discovered_via). From the "
            "operator's inbox copy; the plain-language companion to "
            "usafacts-ai-ready-framework-deck-2026-08 that DN-020 cites."),
    ),
]


def plan() -> list:
    out = []
    for d in DOCS:
        if not d["src"].is_file():
            raise SystemExit(f"FATAL: {d['src']} is not in hand; admission requires the artifact "
                             f"and its hash, never a promise of one")
        body = d["src"].read_bytes()
        sha = hashlib.sha256(body).hexdigest()
        if sha != d["expected_sha256"]:
            raise SystemExit(f"FATAL: {d['src'].name} hashes {sha}, not the operator's "
                             f"{d['expected_sha256']}; refusing to admit a different file")
        mtime = datetime.fromtimestamp(os.path.getmtime(d["src"]), timezone.utc).isoformat()
        out.append({**d, "sha256": sha, "bytes": len(body), "inbox_mtime": mtime,
                    "dest": DEST_DIR / f"{d['doc_id']}.pdf"})
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)

    cfg = dixie_config(REPO / "dixie_evidence.yaml")
    if "crosswalk" not in cfg["document_dirs"]:
        raise SystemExit("FATAL: `crosswalk` is not a document_dir; the sweep would never "
                         "observe corpus/crosswalk/")
    # AR-001 guard: refuse before any side effect (not even the mkdir) if these gitignored outputs
    # would land in a worktree the merge discards rather than in the primary checkout. The
    # dispatcher's dispatch.worktree_links symlinks corpus/crosswalk into the worktree so the copy
    # lands in the primary; absent that link the admission would be lost at merge (Issue 2b5a296d;
    # squiddy SQ-109).
    assert_outputs_in_primary(REPO, [DEST_DIR / f"{d['doc_id']}.pdf" for d in DOCS])
    DEST_DIR.mkdir(parents=True, exist_ok=True)
    dlog = DixieLog(cfg["evidence_dir_abs"] / "decisions.jsonl")
    held = build_manifest(dlog, gate_cfg=cfg.get("identity_gate"))
    items = plan()
    for it in items:
        e = held.get(it["doc_id"])
        if e and e["screening"]["decision"] == "included" \
                and e["integrity"]["status"] == "verified" \
                and e["identity"].get("canonical_path"):
            raise SystemExit(f"FATAL: {it['doc_id']} is already admitted and verified; "
                             f"this task admits it for the first time")

    if a.dry_run:
        print(json.dumps([{"doc_id": it["doc_id"], "src": str(it["src"].relative_to(REPO)),
                           "dest": str(it["dest"].relative_to(REPO)), "sha256": it["sha256"],
                           "bytes": it["bytes"], "inbox_mtime": it["inbox_mtime"],
                           "primary_url": it["primary_url"], "source_type": it["source_type"],
                           "grounding_surface": it["grounding_surface"]}
                          for it in items], indent=1, ensure_ascii=False))
        return 0

    # Copy the inbox bytes to the corpus document dir the sweep observes. Verify the copy.
    for it in items:
        if it["dest"].exists():
            raise SystemExit(f"FATAL: {it['dest']} already exists; refusing to overwrite")
        shutil.copy2(it["src"], it["dest"])
        if hashlib.sha256(it["dest"].read_bytes()).hexdigest() != it["sha256"]:
            raise SystemExit(f"FATAL: {it['dest']} does not hash as the inbox original")

    # The manifest_add event (KG eventlog) is the extraction-admission gate and the Document-node
    # source for the projection. Idempotent: skip if one already landed (a run interrupted
    # between manifest.add and the dixie records must not double-write the event).
    already_evented = {ev["payload"]["doc_id"] for ev in eventlog.replay()
                       if ev.get("event_type") == "manifest_add"}
    for it in items:
        if it["doc_id"] in already_evented:
            print(f"  {it['doc_id']}: manifest_add event already on the log; not re-adding")
            continue
        manifest.add(str(it["dest"]), doc_id=it["doc_id"], title=it["title"],
                     authors=it["authors"], pub_date=it["pub_date"],
                     source_type=it["source_type"], primary_url=it["primary_url"],
                     inclusion_rationale=it["rationale"], discovered_via=DISCOVERED_VIA,
                     construct_arm=CONSTRUCT_ARM, grounding_surface=it["grounding_surface"])

    now = datetime.now(timezone.utc).isoformat()
    for it in items:
        dlog.append("screening_imported", {
            "import_key": it["doc_id"],
            "normalized": {
                "source_id": SOURCE_ID, "doc_id": it["doc_id"], "doc_id_exact": True,
                "title": it["title"], "authors_or_org": it["authors"],
                "pub_year": it["pub_date"][:4], "doc_type": it["source_type"],
                "source_url": it["primary_url"],
                "local_path": it["dest"].relative_to(REPO).as_posix(),
                "expected_sha256": it["sha256"],
                "acquisition_method": ACQUISITION_METHOD, "acquired_by": ACQUIRED_BY,
                "decision": "included", "rationale": it["rationale"],
                "decided_by": "cc", "decided_at": now,
                "notes": (f"operator inbox drop, {ADDENDUM}; acquired_at (inbox file mtime) "
                          f"{it['inbox_mtime']}; sha256 {it['sha256']} ({it['bytes']} bytes); "
                          f"grounding_surface {it['grounding_surface']}; unpublished draft, no "
                          f"public URL (URN primary_url {it['primary_url']}); "
                          f"discovered_via: {DISCOVERED_VIA}")}})

    Sweep(cfg, dlog).run()
    entries = build_manifest(dlog, gate_cfg=cfg.get("identity_gate"))
    for it in items:
        e = entries.get(it["doc_id"])
        ok = (e and e["screening"]["decision"] == "included"
              and e["integrity"]["status"] == "verified"
              and e["identity"].get("canonical_path") == it["dest"].relative_to(REPO).as_posix())
        if not ok:
            raise SystemExit(
                f"FATAL: post-sweep, {it['doc_id']} is not included+verified at its crosswalk "
                f"path: {e and (e['screening']['decision'], e['integrity']['status'], e['identity'].get('canonical_path'))}")

    dlog.append("corpus_epoch_declared", {
        "epoch": EPOCH, "member_doc_ids": [it["doc_id"] for it in items], "declared_by": "cc",
        "task": TASK,
        "note": ("USAFacts' three-track AI-ready data framework from the operator's inbox: the "
                 "August 2026 roundtable deck and the one-page project overview. Unpublished "
                 "drafts with no network location; each carries a URN primary_url (RFC 8141) and "
                 "the roundtable event page as discovered_via.")})
    out = manifest.rebuild()
    print(json.dumps({
        "admitted": [{"doc_id": it["doc_id"], "sha256": it["sha256"], "bytes": it["bytes"],
                      "primary_url": it["primary_url"],
                      "dest": str(it["dest"].relative_to(REPO)),
                      "source_type": it["source_type"],
                      "grounding_surface": it["grounding_surface"]} for it in items],
        "epoch": EPOCH, "manifest": out}, indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
