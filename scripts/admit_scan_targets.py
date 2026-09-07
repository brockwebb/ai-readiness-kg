#!/usr/bin/env python3
"""Capture each selected scan target once and admit it to the corpus. **Zero model spend.**

Task `cc_tasks/2026-09-06_scan_targets.md` §3.2. `OBSERVED_ON` requires a `:Document`, so a
target that is not admitted cannot be scanned — admission is not bookkeeping here, it is the
precondition for the leg to produce a Finding at all.

The admission pattern is `g1sfc-2026-09-03`'s, deliberately: capture as served, store the
bytes under `corpus/scan/`, admit through `kg.manifest.add` (the only gate into the corpus,
invariant 2) with `source_type`, `construct_arm: publication_actionability` and the
`content_hash` of the first capture, then declare the epoch.

**A refused host's targets are admitted too.** `www.bls.gov`, `www.bts.gov` and `www.ssa.gov`
answer 403 to an identified, robots-compliant client; their surfaces will produce `error`
Findings and that is the measurement, not a reason to drop them. Dropping a surface because we
were refused would quietly restrict the instrument to the agencies that let us look, which is
the worst possible sampling frame for an accessibility assessment.

    /opt/anaconda3/bin/python3 scripts/admit_scan_targets.py --dry-run
    /opt/anaconda3/bin/python3 scripts/admit_scan_targets.py
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "assessment" / "harness"))

from scan import load_params                                       # noqa: E402
from scan.collectors import http                                   # noqa: E402
from scan.manners import Fetcher                                   # noqa: E402
from kg import eventlog, manifest                                  # noqa: E402
from dixie.evidence.config import load_config as dixie_config      # noqa: E402
from dixie.evidence.eventlog import EventLog as DixieLog           # noqa: E402

TASK = "cc_tasks/2026-09-06_scan_targets.md"
TARGETS = REPO / "state" / "scan_targets_2026-09.json"
CORPUS = REPO / "corpus" / "scan"
EPOCH = "scan-2026-09"
#: A refused capture still has to become a file so the document can be admitted; the file
#: records what the host said, verbatim, and never pretends to be the product.
REFUSED_NOTE = ("This surface was not served to an identified, robots-compliant client. The "
                "capture below is the host's own response. Task {task}.\n")

EXT = {"text/html": ".html", "application/json": ".json", "text/csv": ".csv",
       "application/xml": ".xml", "text/plain": ".txt", "application/pdf": ".pdf"}


SOURCE_ID = "scan_2026-09"


def dixie_log():
    """The corpus ledger. `corpus/manifest.json` is its PROJECTION, not the event log's —
    invariant 2, and the first pass of this script forgot it: 26 documents passed the
    `manifest.add` gate and none of them appeared in `manifest.json`, because admission has
    two halves and only the extraction-admission half had been written."""
    cfg = dixie_config(REPO / "dixie_evidence.yaml")
    if "scan" not in cfg["document_dirs"]:
        raise SystemExit("FATAL: dixie_evidence.yaml document_dirs must include 'scan'")
    return DixieLog(cfg["evidence_dir_abs"] / "decisions.jsonl")


def dixie_imported() -> set:
    import json as _json
    seen = set()
    p = REPO / "corpus" / "evidence" / "decisions.jsonl"
    if not p.is_file():
        return seen
    for line in p.read_text(encoding="utf-8").splitlines():
        if '"screening_imported"' not in line:
            continue
        try:
            ev = _json.loads(line)
        except ValueError:
            continue
        n = (ev.get("payload") or ev).get("normalized") or {}
        if n.get("doc_id"):
            seen.add(n["doc_id"])
    return seen


def manifest_entry_path(doc_id: str) -> str:
    return {e["doc_id"]: e for e in manifest._load_entries()}[doc_id]["local_path"]


def _sha256_of(path) -> str:
    import hashlib as _h
    return _h.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def _manifest_entries() -> dict:
    """`corpus/manifest.json`'s entries, or {} before the first rebuild. Read at call time so
    a document admitted in this same pass is visible to the next iteration."""
    p = REPO / "corpus" / "manifest.json"
    if not p.is_file():
        return {}
    return json.loads(p.read_text(encoding="utf-8")).get("entries") or {}


def capture(row: dict, fetcher, params: dict) -> dict:
    obs = http.fetch(fetcher, "admit", row["doc_id"], row["url"], params)[0]
    resp = obs.response or {}
    ctype = (obs.parsed or {}).get("content_type") or ""
    body = b""
    if resp.get("body_path"):
        body = (REPO / resp["body_path"]).read_bytes()
    path = CORPUS / f"{row['doc_id']}{EXT.get(ctype, '.html')}"
    if resp.get("status") and resp["status"] >= 400:
        body = REFUSED_NOTE.format(task=TASK).encode() + body
    path.write_bytes(body)
    import hashlib as _h
    return {"path": path, "status": resp.get("status"), "bytes": len(body),
            "sha256": _h.sha256(path.read_bytes()).hexdigest(),
            "content_type": ctype, "captured_at": obs.captured_at,
            "error_class": obs.error_class, "evidence_sha256": resp.get("body_sha256")}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    doc = json.loads(TARGETS.read_text(encoding="utf-8"))
    rows = [r for r in doc["rows"] if r["doc_id"]]
    if a.dry_run:
        print(json.dumps({"to_admit": len(rows),
                          "already": sum(1 for r in rows
                                         if r["doc_id"] in _manifest_entries())},
                         indent=1))
        return 0
    CORPUS.mkdir(parents=True, exist_ok=True)
    params = load_params()
    fetcher = Fetcher(params)
    have = set(_manifest_entries())
    dlog, already_dixie = dixie_log(), dixie_imported()
    # Half-admitted documents: through the manifest gate, absent from the corpus ledger.
    admitted_before = {e["doc_id"] for e in manifest._load_entries()
                       if e["doc_id"].startswith("scan-")}
    half = {e["doc_id"] for e in manifest._load_entries()
            if e["doc_id"].startswith("scan-")} - already_dixie
    admitted, skipped, failed = [], [], []
    for r in rows:
        if r["doc_id"] in have and r["doc_id"] in already_dixie:
            skipped.append((r["doc_id"], "already admitted in both halves"))
            continue
        # NEVER re-capture a document that is already admitted anywhere. The second pass did,
        # and cost two things: a live page that had changed since the first capture produced a
        # hash the admission event no longer matched, and the empty-capture guard DELETED the
        # supersession file of a document that was already on the ledger. A capture is a
        # measurement taken at a moment; re-taking it silently is drift, and re-taking it on a
        # document already admitted is drift with a gate wrapped around it.
        if r["doc_id"] in have or r["doc_id"] in admitted_before:
            print(f"  ledger-only {r['doc_id'][:50]:52s} (already captured; not re-fetched)",
                  flush=True)
            cap = {"path": REPO / manifest_entry_path(r["doc_id"]), "status": None,
                   "bytes": None, "sha256": None, "content_type": "", "error_class": None,
                   "captured_at": None, "evidence_sha256": None, "recaptured": False}
            cap["sha256"] = _sha256_of(cap["path"])
        else:
            cap = {**capture(r, fetcher, params), "recaptured": True}
        # A capture with no body is not a capture — but ONLY a capture can be judged that way.
        # Without this guard on the guard, an already-admitted document takes the not-admitted
        # branch (its `bytes` is None because nothing was fetched) and its stored file is
        # deleted. That happened twice to `scan-eia-flagship-1-open-data`. The first run admitted an EMPTY document
        # for `https://www.eia.gov/beta/api/` — EIA's robots.txt disallows /beta/ for this UA,
        # the fetcher obeyed it as it must, and a zero-byte file went through the admission
        # gate because `manifest.add` checks provenance and duplication, not extent. The
        # second EIA surface was refused only because it hashed to the SAME empty string,
        # which is duplicate detection doing accidental work that an extent check should have
        # done on purpose.
        if cap["recaptured"] and (cap["error_class"] or not cap["bytes"]):
            r["not_admitted"] = cap["error_class"] or "empty_capture"
            skipped.append((r["doc_id"], f"not admitted: {r['not_admitted']}"))
            print(f"  NOT ADMITTED {r['doc_id'][:48]:50s} {r['not_admitted']}", flush=True)
            cap["path"].unlink(missing_ok=True)
            continue
        try:
            if r["doc_id"] not in already_dixie:
                dlog.append("screening_imported", {
                    "import_key": r["doc_id"],
                    "normalized": {
                        "source_id": SOURCE_ID, "doc_id": r["doc_id"], "doc_id_exact": True,
                        "title": f"{r['agency_name']} — {r['selected_as']}",
                        "authors_or_org": [r["agency_name"]],
                        "pub_year": datetime.now(timezone.utc).date().isoformat()[:4],
                        "doc_type": "federal" if r["agency"] != "STATCAN" else "intergovernmental",
                        "source_url": r["url"],
                        "local_path": cap["path"].relative_to(REPO).as_posix(),
                        "expected_sha256": cap["sha256"],
                        "acquisition_method": "scripted_fetch",
                        "acquired_by": "scripts/admit_scan_targets.py",
                        "decision": "included",
                        "rationale": (f"Product surface of kind `{r['surface_kind']}` for "
                                      f"{r['agency']}, selected from {r['listing_url']} as "
                                      f"{r['selected_as']!r}. Epoch {EPOCH}, {TASK} §3.2."),
                        "decided_by": "cc", "decided_at": cap["captured_at"],
                        "notes": r["selection_source"]}})
            manifest.add(
                str(cap["path"]), doc_id=r["doc_id"],
                title=f"{r['agency_name']} — {r['selected_as']}",
                authors=[r["agency_name"]], pub_date=datetime.now(timezone.utc).date().isoformat(),
                source_type="federal" if r["agency"] != "STATCAN" else "intergovernmental",
                primary_url=r["url"], construct_arm=doc["construct_arm"],
                inclusion_rationale=(
                    f"{doc['source_type']} of surface kind `{r['surface_kind']}` for "
                    f"{r['agency']} ({r['agency_name']}), selected from the agency's own "
                    f"listing {r['listing_url']} as {r['selected_as']!r} "
                    f"({r['selection_source']}). Agency roster: OMB Statistical Policy "
                    f"Directive No. 1, segment {r.get('spd1_segment')}. Epoch {EPOCH}, "
                    f"{TASK} §3.2."),
                discovered_via=f"scripts/admit_scan_targets.py ({TASK})",
                acquisition={"task": TASK, "surface": {
                    "surface_kind": r["surface_kind"], "request_url": r["url"],
                    "surface_format": (cap["content_type"] or "unknown").split("/")[-1],
                    "status": cap["status"], "captured_at": cap["captured_at"],
                    "host_unobservable": r["unobservable"],
                    "error_class": cap["error_class"],
                    "evidence_sha256": cap["evidence_sha256"],
                    "selected_as": r["selected_as"],
                    "selection_source": r["selection_source"]}})
            admitted.append(r["doc_id"])
            print(f"  admitted {r['doc_id'][:52]:54s} HTTP {cap['status']}", flush=True)
        except manifest.ManifestError as exc:
            if r["doc_id"] in half and "duplicate doc_id" in str(exc):
                # The corpus-ledger half was just written; the extraction-admission half was
                # already there from the first pass. Both halves now exist.
                admitted.append(r["doc_id"])
                print(f"  ledger-only {r['doc_id'][:50]:52s} (manifest_add already on the log)",
                      flush=True)
                continue
            failed.append((r["doc_id"], f"{type(exc).__name__}: {exc}"))
            print(f"  REFUSED  {r['doc_id'][:52]:54s} {exc}", flush=True)
    if admitted:
        eventlog.append({"event_type": "corpus_epoch_declared", "payload": {
            "declared_by": "cc", "epoch": EPOCH, "member_doc_ids": sorted(admitted),
            "task": TASK,
            "note": ("Product surfaces of the 13 U.S. principal statistical agencies (OMB "
                     "Statistical Policy Directive No. 1) plus the StatCan comparator. NOT a "
                     "fixture epoch: these are the objects of measurement, and they are not "
                     "queued for extraction because a product surface carries no construct "
                     "claim to read — the same reason as DD-043, reached by a different "
                     "route.")}}, batch=30)
    print(json.dumps({"admitted": len(admitted), "skipped": len(skipped),
                      "failed": len(failed), "failures": failed[:8], "epoch": EPOCH}, indent=1))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
