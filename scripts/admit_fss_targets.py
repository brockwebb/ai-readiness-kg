#!/usr/bin/env python3
"""Admit the FSS target list's documents. **Zero model spend.**

Task `cc_tasks/2026-09-08_scan_frame_fss.md` §2, `..._ADDENDUM-05.md` step 1. `OBSERVED_ON`
requires a `:Document`, so a doc_id-bearing target that is not admitted cannot be scanned.

**Almost everything here is already admitted**, because ADDENDUM-05 makes the cycle-1 target
list the operator's declaration and those 23 surfaces went through this same gate in
`cc_tasks/2026-09-06_scan_targets.md` §3.2. This script exists for the remainder and for the
assertion: `purpose: scan_surface` on every one, and **zero new `conversion_gap` events**.

That last one is the point. A scan surface's extent IS the measurement — A10 exists to catch a
page with no document behind it, B3 scores whether the methodology is legible without
JavaScript — so DD-030's thin-extent gate must not fire on one. It fired 22 times on the
cycle-1 admissions and each had to be withdrawn by hand; `purpose: scan_surface` is what makes
`kg.manifest._convertibility_gate` return early, and this asserts that it did.

    /opt/anaconda3/bin/python3 scripts/admit_fss_targets.py --dry-run
    /opt/anaconda3/bin/python3 scripts/admit_fss_targets.py
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
sys.path.insert(0, str(REPO / "assessment" / "harness"))

from scan import load_params                                        # noqa: E402
from kg import manifest                                             # noqa: E402
from kg.ingest import gate as ingest_gate                           # noqa: E402

TASK = "cc_tasks/2026-09-08_scan_frame_fss.md"
ADDENDUM = "cc_tasks/2026-09-08_scan_frame_fss_ADDENDUM-05.md"
TARGETS = REPO / "state" / "scan_targets_fss_2026-09.json"
CORPUS = REPO / "corpus" / "scan"
PURPOSE = "scan_surface"
EXT = {"text/html": ".html", "application/json": ".json", "text/csv": ".csv",
       "application/xml": ".xml", "text/plain": ".txt", "application/pdf": ".pdf"}
REFUSED_NOTE = ("This surface was not served to an identified, robots-compliant client. The "
                "capture below is the host's own response. Task {task}.\n")


def gaps_for_scan() -> set:
    return {g for g in ingest_gate.gaps() if str(g).startswith("scan-")}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    doc = json.loads(TARGETS.read_text(encoding="utf-8"))
    rows = [r for r in doc["rows"] if r.get("doc_id")]
    entries = {e["doc_id"]: e for e in manifest._load_entries()}
    todo = [r for r in rows if r["doc_id"] not in entries]
    wrong_purpose = [r["doc_id"] for r in rows
                     if r["doc_id"] in entries
                     and entries[r["doc_id"]].get("purpose") != PURPOSE]
    gaps_before = gaps_for_scan()

    print(json.dumps({"doc_id_rows": len(rows), "already_admitted": len(rows) - len(todo),
                      "to_admit": [r["doc_id"] for r in todo],
                      "admitted_without_scan_surface_purpose": wrong_purpose,
                      "conversion_gaps_before": len(gaps_before)}, indent=1))
    if a.dry_run:
        return 0

    params = load_params()
    from scan.collectors import http
    from scan.manners import Fetcher
    fetcher = Fetcher(params)
    CORPUS.mkdir(parents=True, exist_ok=True)
    admitted, skipped = [], []
    for r in todo:
        obs = http.fetch(fetcher, "admit", r["doc_id"], r["url"], params)[0]
        resp = obs.response or {}
        ctype = (obs.parsed or {}).get("content_type") or ""
        body = (REPO / resp["body_path"]).read_bytes() if resp.get("body_path") else b""
        if obs.error_class or not body:
            # A refusal is a MEASUREMENT and the surface keeps its roster row; what it cannot
            # do is become a Document without bytes. Recorded, never silently dropped.
            skipped.append((r["doc_id"], obs.error_class or "empty_capture"))
            print(f"  NOT ADMITTED {r['doc_id'][:46]:48s} "
                  f"{obs.error_class or 'empty_capture'}", flush=True)
            continue
        if resp.get("status") and resp["status"] >= 400:
            body = REFUSED_NOTE.format(task=TASK).encode() + body
        path = CORPUS / f"{r['doc_id']}{EXT.get(ctype, '.html')}"
        path.write_bytes(body)
        try:
            manifest.add(
                str(path), doc_id=r["doc_id"],
                title=f"{r['agency_name']} — {r.get('selected_as')}",
                authors=[r["agency_name"]],
                pub_date=datetime.now(timezone.utc).date().isoformat(),
                source_type="federal", primary_url=r["url"],
                construct_arm=doc["construct_arm"], purpose=PURPOSE,
                inclusion_rationale=(
                    f"{doc['source_type']} of surface kind `{r['surface_kind']}` for "
                    f"{r['agency']} ({r['agency_name']}), {r['selection_source']}. Frame: "
                    f"{doc['frame']} Epoch {doc['epoch']}, {ADDENDUM} step 1."),
                discovered_via=f"scripts/admit_fss_targets.py ({TASK})",
                acquisition={"task": TASK, "addendum": ADDENDUM, "surface": {
                    "surface_kind": r["surface_kind"], "request_url": r["url"],
                    "status": resp.get("status"), "captured_at": obs.captured_at,
                    "evidence_sha256": resp.get("body_sha256"),
                    "selection_source": r["selection_source"]}})
            admitted.append(r["doc_id"])
            print(f"  admitted {r['doc_id'][:50]:52s} HTTP {resp.get('status')}", flush=True)
        except manifest.ManifestError as exc:
            skipped.append((r["doc_id"], f"{type(exc).__name__}: {exc}"))
            print(f"  REFUSED  {r['doc_id'][:50]:52s} {exc}", flush=True)

    new_gaps = sorted(gaps_for_scan() - gaps_before)
    out = {"admitted": admitted, "skipped": skipped,
           "conversion_gaps_emitted_by_this_admission": new_gaps,
           "assertion": "zero conversion-gap tasks emitted by admission"}
    print(json.dumps(out, indent=1))
    if new_gaps:
        raise SystemExit(
            f"REFUSING: admission emitted {len(new_gaps)} conversion_gap event(s) {new_gaps}. "
            f"A scan surface is admitted to be MEASURED, not read — its extent IS the "
            f"measurement (A10, B3) — so DD-030's convertibility gate must not fire on one. "
            f"`purpose: {PURPOSE}` is what makes it return early.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
