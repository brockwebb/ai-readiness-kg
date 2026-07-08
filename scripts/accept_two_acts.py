#!/usr/bin/env python3
"""Stage 5 acceptance — acquire the two Acts through the new lane, end to end.

Live: GovInfo connector resolves each Act's STANDALONE bill (correct extent) → identity
signals computed → Dixie gate → admitted as a refetch fulfillment (same doc_id, new
content_hash, provenance acquired_via=govinfo_connector). The mis-acquired megastatutes
are quarantined (move + reason, NEVER deleted). No force-admit: a doc admits only if it
passes the gate.
"""
from __future__ import annotations

import hashlib
import io
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(Path.home() / ".wintermute" / "harvester"))

import httpx  # noqa: E402
import yaml  # noqa: E402
from pypdf import PdfReader  # noqa: E402

from dixie.evidence import identity_gate  # noqa: E402
from dixie.evidence.eventlog import EventLog  # noqa: E402
from dixie.evidence.config import load_config  # noqa: E402
from harvester.fetchers import govinfo  # noqa: E402

_UA = "WintermuteAcceptance/0.1 (research; brockwebb45@gmail.com)"

ACTS = {
    "advancing-american-ai-act-ndaa-fy2023-div-g":
        {"congress": 117, "billtype": "s", "billnum": 1353,
         "requested_title": "Advancing American AI Act"},
    "ai-in-government-act-of-2020":
        {"congress": 116, "billtype": "hr", "billnum": 2575,
         "requested_title": "AI in Government Act of 2020"},
}


def _get(url: str) -> httpx.Response:
    with httpx.Client(headers={"User-Agent": _UA}, timeout=90,
                      follow_redirects=True) as c:
        r = c.get(url)
        r.raise_for_status()
        return r


def mods_titles(resolution) -> list[str]:
    """ALL titles GovInfo associates with the package (main + short/alternative).
    A bill's short title ('Advancing American AI Act') is an alternative titleInfo;
    the primary <title> is the long descriptive title. Identity must consider both —
    the megastatute has NO title matching the request, so best-of-titles still rejects
    it (not gaming; a correct signal)."""
    titles = []
    try:
        r = _get(f"https://www.govinfo.gov/metadata/pkg/{resolution.package_id}/mods.xml")
        root = ET.fromstring(r.text)
        for el in root.iter():
            if (el.tag.endswith("}title") or el.tag == "title") and el.text and el.text.strip():
                titles.append(el.text.strip())
    except Exception as exc:
        print(f"    (mods title fetch failed: {exc}; falling back to PDF page 1)")
    return titles


def best_resolved_title(resolution, requested: str, content: bytes) -> str:
    candidates = mods_titles(resolution)
    if not candidates:
        candidates = [(PdfReader(io.BytesIO(content)).pages[0].extract_text() or "")[:200]]
    return max(candidates, key=lambda t: identity_gate.title_token_overlap(requested, t))


def main() -> int:
    cfg = load_config(REPO / "dixie_evidence.yaml")
    gate_cfg = cfg["identity_gate"]
    log = EventLog(REPO / "corpus" / "evidence" / "decisions.jsonl")
    quarantine = REPO / "corpus" / "quarantine"
    quarantine.mkdir(parents=True, exist_ok=True)

    admitted, blocked = [], []
    for doc_id, cit in ACTS.items():
        print(f"\n### {doc_id}")
        citation = {k: cit[k] for k in ("congress", "billtype", "billnum")}
        res = govinfo.resolve_extent(citation)
        print(f"  resolved: {res.package_id} ({res.resolution_path}), over_extent={res.over_extent}")
        content = _get(res.pdf_url).content
        rtitle = best_resolved_title(res, cit["requested_title"], content)
        pages = govinfo.pdf_page_count(content)
        signals = govinfo.compute_signals(
            res, cit["requested_title"], resolved_title=rtitle,
            size_bytes=len(content), page_count=pages)
        verdict = identity_gate.evaluate(signals, gate_cfg)
        new_sha = hashlib.sha256(content).hexdigest()
        print(f"  resolved_title: {rtitle[:70]!r}")
        print(f"  signals: overlap={signals['title_token_overlap']} "
              f"size={signals['size_bytes']} pages={pages} -> gate {'PASS' if verdict['passed'] else 'FAIL'}")

        if not verdict["passed"]:
            blocked.append((doc_id, verdict["failures"]))
            log.append("screening_decided", {
                "doc_id": doc_id, "decision": "pending_refetch", "signals": signals,
                "rationale": "acceptance: connector artifact failed the gate — "
                             + "; ".join(verdict["failures"]),
                "decided_by": "accept_two_acts"})
            print(f"  BLOCKED (finding): {verdict['failures']}")
            continue

        # quarantine the mis-acquired megastatute (move + reason, never delete)
        canonical = REPO / "corpus" / "bulk" / f"{doc_id}.pdf"
        if canonical.exists():
            old_sha = hashlib.sha256(canonical.read_bytes()).hexdigest()
            dest = quarantine / f"{doc_id}.megastatute.pdf"
            canonical.rename(dest)
            (quarantine / f"{doc_id}.megastatute.reason.txt").write_text(
                f"mis-acquired whole enclosing statute; superseded by standalone "
                f"{res.package_id} via govinfo_connector on acceptance. sha256={old_sha}\n",
                encoding="utf-8")
            log.append("quarantined", {
                "path": str(canonical.relative_to(REPO)), "dest": str(dest.relative_to(REPO)),
                "reasons": [f"wrong_extent: whole statute superseded by {res.package_id}"]})
            print(f"  quarantined megastatute -> {dest.name} (sha {old_sha[:12]})")

        # write the correct-extent standalone bill as the new canonical
        canonical.write_bytes(content)
        # evidence bookkeeping: the quarantine nulled canonical_path, so the new file
        # must be OBSERVED + integrity-CHECKED or the manifest shows no verified file
        # (which broke the burn's frozen-baseline guard the first time). run_checks +
        # emit before the screening decision so the projection re-establishes canonical.
        from dixie.evidence import integrity as _integrity
        rel = str(canonical.relative_to(REPO))
        chk = _integrity.run_checks(canonical, cfg["integrity"])
        log.append("file_observed", {"path": rel, "sha256": chk["sha256"],
                                     "size": chk["size"], "claimed_type": chk["claimed_type"],
                                     "detected_type": chk["detected_type"]})
        log.append("integrity_checked", {"path": rel, "verdict": chk["verdict"],
                                         "checks": chk["checks"]})
        # admit as a refetch fulfillment: same doc_id, new content_hash, provenance
        log.append("screening_decided", {
            "doc_id": doc_id, "decision": "included", "signals": signals,
            "rationale": f"refetch fulfillment: standalone {res.package_id} "
                         f"({res.collection}) via govinfo_connector; extent corrected",
            "decided_by": "govinfo_connector",
            "content_hash": f"sha256:{new_sha}",
            "acquired_via": "govinfo_connector",
            "package_id": res.package_id})
        admitted.append((doc_id, res.package_id, new_sha))
        print(f"  ADMITTED (included) sha {new_sha[:12]} — {len(content):,} bytes, {pages} pp")

    print("\n=== summary ===")
    print(f"admitted: {len(admitted)}  blocked-as-finding: {len(blocked)}")
    for d, pkg, sha in admitted:
        print(f"  {d} <- {pkg} (sha {sha[:12]})")
    return 0 if not blocked else 1


if __name__ == "__main__":
    raise SystemExit(main())
