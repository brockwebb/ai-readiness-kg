#!/usr/bin/env python3
"""Admit the two measurement-theory sources DN-019 cites into the corpus. **Zero model spend.**

`cc_tasks/2026-11-02_v3_measurement_sheet.md` Part A, under DN-019
(`handoffs/2026-11-02_staged_DN-019_measurement_view_and_the_view_ladder.md`, PASS sha256
d2a9152f197b). DN-019 section 2 cites ISO/IEC/IEEE 15939 and Basili, Caldiera and Rombach (1994)
unverified; this script backs both with a corpus document, through the same admission machinery
every other source goes through (fetch -> docling -> manifest_add -> dixie screening -> sweep ->
rebuild), and records which citation is now backed by a corpus document and which is abstract-only.

Both captures were fetched robots-first through `scripts/fetch_allowlisted.py` from the two hosts
the task declared (www.iso.org, www.cs.umd.edu); the fetch log is quoted whole in the RESULT.

* **ISO/IEC/IEEE 15939:2017** — the standard is paywalled, so only the public ISO catalogue and
  abstract page (`https://www.iso.org/standard/71197.html`) is admitted. docling renders it a
  navigation surface (link density > 0.25): that is the catalogue page's nature, and the
  convertibility gate's `thin_extent_suspected` finding is the system's truthful record that we
  hold the abstract, not the standard. ABSTRACT-ONLY by design.
* **The Goal Question Metric Approach** (Basili, Caldiera, Rombach) — the open University of
  Maryland copy (`https://www.cs.umd.edu/~mvz/handouts/gqm.pdf`), the full 10-page chapter.

The admitted file is a docling markdown rendering (the dixie sweep rejects a file that sniffs as
HTML or as a PDF-only navigation shell; markdown is what it verifies). The raw captures stay in
CAPTURE_DIR and both hashes ride on the `manifest_add` event.

    /opt/anaconda3/bin/python3 scripts/admit_measurement_theory_sources.py --dry-run
    /opt/anaconda3/bin/python3 scripts/admit_measurement_theory_sources.py
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
sys.path.insert(0, str(REPO / "scripts"))

from kg import manifest                                             # noqa: E402
from kg.ingest import convert as C                                 # noqa: E402
from worktree_primary import assert_outputs_in_primary             # noqa: E402
from dixie.evidence.config import load_config as dixie_config       # noqa: E402
from dixie.evidence.eventlog import EventLog as DixieLog            # noqa: E402
from dixie.evidence.manifest import build_manifest                  # noqa: E402
from dixie.evidence.sweep import Sweep                              # noqa: E402

TASK = "cc_tasks/2026-11-02_v3_measurement_sheet.md"
EPOCH = "measurement-theory-2026-11-02"
SOURCE_ID = "measurement_theory_2026-11-02"
FETCH_LOG = REPO / "logs" / "2026-11-02_v3_partA_fetch.jsonl"
CAPTURE_DIR = REPO / "corpus" / "measurement_theory"
DEST_DIR = REPO / "corpus" / "crosswalk"
ACQUISITION_METHOD = "scripted_fetch"
ACQUIRED_BY = "scripts/fetch_allowlisted.py"

#: One entry per document. `capture` is relative to CAPTURE_DIR. `licence`/`note` are quoted or
#: paraphrased from the capture itself. `backs` is the plain statement the RESULT needs.
DOCS = [
    dict(
        doc_id="iso-iec-ieee-15939-2017",
        title="ISO/IEC/IEEE 15939:2017 Systems and software engineering: measurement process",
        authors=["ISO/IEC/IEEE"],
        pub_date="2017-05",
        source_type="standard",
        doc_type="standard",
        url="https://www.iso.org/standard/71197.html",
        capture="71197.html",
        licence="ISO copyright; catalogue and abstract page is public, the standard is paywalled",
        extent="abstract_only",
        backs=("DN-019 section 2's citation of the ISO/IEC/IEEE 15939 measurement information "
               "model is now backed by a corpus document, abstract-only: the catalogue and "
               "abstract page, because the standard is paywalled."),
        rationale=(
            "DN-019 (staged 2026-11-02, PASS sha256 d2a9152f197b) section 2 cites ISO/IEC/IEEE "
            "15939's measurement information model as the field set under the V3 measurement "
            "sheet. The standard is paywalled; only the public ISO catalogue and abstract page is "
            "admitted (abstract-only). No rule cites it; it backs the design note's citation."),
    ),
    dict(
        doc_id="basili-caldiera-rombach-1994-gqm",
        title="The Goal Question Metric Approach",
        authors=["Victor R. Basili", "Gianluigi Caldiera", "H. Dieter Rombach"],
        pub_date="1994",
        source_type="academic",
        doc_type="academic",
        url="https://www.cs.umd.edu/~mvz/handouts/gqm.pdf",
        capture="gqm.pdf",
        licence="author copy hosted by the University of Maryland for teaching",
        extent="full",
        backs=("DN-019 section 2's citation of Goal Question Metric (Basili, Caldiera, Rombach "
               "1994) as the older, simpler form of the measurement information model is now "
               "backed by a corpus document: the full chapter, from the open University of "
               "Maryland copy."),
        rationale=(
            "DN-019 (staged 2026-11-02, PASS sha256 d2a9152f197b) section 2 cites Goal Question "
            "Metric as the older, simpler form of the measurement information model the V3 sheet "
            "renders. Admitted as the open University of Maryland copy, the full chapter. No rule "
            "cites it; it backs the design note's citation."),
    ),
]


def fetched() -> dict:
    """`{url: (sha256, ts, bytes)}` for every 200 response the fetch log holds."""
    if not FETCH_LOG.is_file():
        raise SystemExit(f"FATAL: {FETCH_LOG} is missing; nothing was fetched through the "
                         f"allowlisted helper, so nothing is admitted")
    out = {}
    for line in FETCH_LOG.read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        if r.get("event") == "request" and r.get("status") == 200:
            out[r["url"]] = (r["sha256"], r["ts"], r["bytes"])
    return out


def docling_markdown(cap: Path) -> str:
    """docling's markdown for the capture. HTML goes through the project's `_docling_html`
    (the convertibility path's own tool); a PDF goes straight through docling's DocumentConverter,
    which the project's gate delegates to the T1 path but which renders the chapter faithfully."""
    if cap.suffix.lower() in (".html", ".htm"):
        return C._docling_html(cap)
    if cap.suffix.lower() == ".pdf":
        from docling.document_converter import DocumentConverter
        return DocumentConverter().convert(str(cap)).document.export_to_markdown()
    raise SystemExit(f"FATAL: {cap.name}: no docling path for suffix {cap.suffix!r}")


def plan() -> list:
    log = fetched()
    out = []
    for d in DOCS:
        if d["url"] not in log:
            raise SystemExit(f"FATAL: {d['url']} has no 200 line in {FETCH_LOG}")
        sha, ts, n = log[d["url"]]
        cap = CAPTURE_DIR / d["capture"]
        if not cap.is_file():
            raise SystemExit(f"FATAL: {cap} is not in hand")
        body = cap.read_bytes()
        if hashlib.sha256(body).hexdigest() != sha or len(body) != n:
            raise SystemExit(f"FATAL: {cap} is not the body the fetch log recorded for "
                             f"{d['url']} ({sha})")
        md_text = docling_markdown(cap)
        header = (f"<!-- measurement-theory admission: {TASK}; primary_url={d['url']}; "
                  f"capture_sha256={sha}; retrieved_at={ts}; acquired_by={ACQUIRED_BY}; "
                  f"converter=docling; extent={d['extent']} -->\n\n")
        md = (header + md_text).encode("utf-8")
        out.append({**d, "capture_sha256": sha, "retrieved_at": ts, "capture_bytes": n,
                    "md": md, "md_sha256": hashlib.sha256(md).hexdigest(),
                    "docling_lines": md_text.count("\n") + 1, "docling_chars": len(md_text),
                    "dest": DEST_DIR / f"{d['doc_id']}.md"})
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
    # dispatcher's dispatch.worktree_links symlinks corpus/crosswalk into the worktree so the write
    # lands in the primary; absent that link the admission would be lost at merge (Issue 2b5a296d;
    # squiddy SQ-109).
    assert_outputs_in_primary(REPO, [DEST_DIR / f"{d['doc_id']}.md" for d in DOCS])
    DEST_DIR.mkdir(parents=True, exist_ok=True)
    dlog = DixieLog(cfg["evidence_dir_abs"] / "decisions.jsonl")
    ledger = build_manifest(dlog, gate_cfg=cfg.get("identity_gate"))
    items = plan()
    for it in items:
        if it["doc_id"] in ledger:
            raise SystemExit(f"FATAL: {it['doc_id']} is already in the ledger")
        if it["dest"].exists():
            raise SystemExit(f"FATAL: {it['dest']} already exists; refusing to overwrite")

    now = datetime.now(timezone.utc).isoformat()
    adds, records = [], []
    for it in items:
        acquisition = {
            "acquisition_method": ACQUISITION_METHOD, "acquired_by": ACQUIRED_BY,
            "acquired_at": it["retrieved_at"], "fetch_log": FETCH_LOG.relative_to(REPO).as_posix(),
            "fetched_from": it["url"],
            "capture_path": (CAPTURE_DIR / it["capture"]).relative_to(REPO).as_posix(),
            "capture_sha256": it["capture_sha256"], "capture_bytes": it["capture_bytes"],
            "rendered_by": "kg.ingest.convert docling (markdown for the sweep)",
            "licence": it["licence"], "extent": it["extent"],
            "verification": {"sha256": it["md_sha256"]},
            "evaluation": {"identity_check": "pass",
                           "note": "not previously admitted by doc_id, sha256 or primary_url"},
            "task": TASK,
        }
        adds.append(dict(doc_id=it["doc_id"], title=it["title"], authors=it["authors"],
                         pub_date=it["pub_date"], source_type=it["source_type"],
                         primary_url=it["url"], inclusion_rationale=it["rationale"],
                         discovered_via="DN-019 citation (manual)",
                         grounding_surface="document", acquisition=acquisition))
        records.append({"import_key": it["doc_id"], "normalized": {
            "source_id": SOURCE_ID, "doc_id": it["doc_id"], "doc_id_exact": True,
            "title": it["title"], "authors_or_org": it["authors"],
            "pub_year": it["pub_date"][:4] if it["pub_date"][:1].isdigit() else "n.d.",
            "doc_type": it["doc_type"], "source_url": it["url"],
            "local_path": it["dest"].relative_to(REPO).as_posix(),
            "expected_sha256": it["md_sha256"],
            "acquisition_method": ACQUISITION_METHOD, "acquired_by": ACQUIRED_BY,
            "decision": "included", "rationale": it["rationale"],
            "decided_by": "cc", "decided_at": now,
            "notes": (f"fetched robots-first under the identified UA from {it['url']} at "
                      f"{it['retrieved_at']} ({FETCH_LOG.relative_to(REPO).as_posix()}, capture "
                      f"sha256 {it['capture_sha256']}); docling-rendered to markdown "
                      f"({it['docling_lines']} lines, {it['docling_chars']} chars) for the sweep. "
                      f"Extent: {it['extent']}. Licence: {it['licence']}")}})

    if a.dry_run:
        print(json.dumps([{"doc_id": it["doc_id"], "dest": str(it["dest"].relative_to(REPO)),
                           "md_bytes": len(it["md"]), "md_sha256": it["md_sha256"],
                           "docling_lines": it["docling_lines"],
                           "docling_chars": it["docling_chars"], "extent": it["extent"]}
                          for it in items], indent=1, ensure_ascii=False))
        return 0

    for it, fields in zip(items, adds):
        it["dest"].write_bytes(it["md"])
        if hashlib.sha256(it["dest"].read_bytes()).hexdigest() != it["md_sha256"]:
            raise SystemExit(f"FATAL: {it['dest']} does not hash as rendered")
        manifest.add(it["dest"], **fields)
    for r in records:
        dlog.append("screening_imported", r)
    actions = Sweep(cfg, dlog).run()
    entries = build_manifest(dlog, gate_cfg=cfg.get("identity_gate"))
    for it in items:
        e = entries.get(it["doc_id"])
        ok = (e and e["screening"]["decision"] == "included"
              and e["integrity"]["status"] == "verified"
              and e["identity"].get("canonical_path") == it["dest"].relative_to(REPO).as_posix())
        if not ok:
            raise SystemExit(f"FATAL: post-sweep, {it['doc_id']} is not included+verified: "
                             f"{e and (e['screening']['decision'], e['integrity']['status'])}.")
    dlog.append("corpus_epoch_declared", {
        "epoch": EPOCH, "member_doc_ids": [it["doc_id"] for it in items], "declared_by": "cc",
        "task": TASK,
        "note": ("The two measurement-theory sources DN-019 section 2 cites. ISO/IEC/IEEE 15939 "
                 "is admitted abstract-only (the standard is paywalled); the GQM chapter is "
                 "admitted in full. Neither is cited by any rule; both back the design note.")})
    out = manifest.rebuild()
    print(json.dumps({"admitted": [{"doc_id": it["doc_id"], "extent": it["extent"],
                                    "docling_lines": it["docling_lines"],
                                    "docling_chars": it["docling_chars"],
                                    "md_sha256": it["md_sha256"]} for it in items],
                      "epoch": EPOCH, "sweep_actions": actions, "manifest": out,
                      "backs": {it["doc_id"]: it["backs"] for it in items}},
                     indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
