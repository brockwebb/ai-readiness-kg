#!/usr/bin/env python3
"""Run the G1 DECLARED leg (probes/g1_declared.G1DeclaredProbe) on every captured product
surface of epoch g1sfc-2026-09-03 (task 2026-09-03_g1_eval_v2_product_surfaces_compression
step 3; zero model spend) and write the scores to the fixture metadata so the observed leg's
records carry `declared_leg_score` as a D11 covariate — the A11 triad's first two legs joined
on the surface file for the first time.

The probe evaluates a `Fetched`; here one is built from the captured file: the kernel's
one-line provenance header is stripped (it is the harvester's, not the surface's), the media
type comes from the manifest's `surface_format`, and `status = 200` because the capture
succeeded (the register carries the real status). PDF surfaces are passed as extracted text
(`unsupported_media` for a field-name probe — reported, never coerced).

    /opt/anaconda3/bin/python3 scripts/g1_declared_surfaces.py

Writes assessment/tests/fixtures/g1/v2/declared_leg.json.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "assessment"))
sys.path.insert(0, str(REPO))

from harness.config import load_harness_config  # noqa: E402
from harness.fetch import Fetched  # noqa: E402
from harness.probes.g1_declared import G1DeclaredProbe  # noqa: E402
from kg import eventlog  # noqa: E402

EPOCH = "g1sfc-2026-09-03"
OUT = REPO / "assessment" / "tests" / "fixtures" / "g1" / "v2" / "declared_leg.json"
MEDIA = {"json": "application/json", "csv": "text/csv", "html": "text/html", "pdf": "application/pdf", "text": "text/plain"}


def surfaces_from_events() -> list[dict]:
    """Every manifest_add of the epoch with its `acquisition.surface` block (the standing path
    recorded surface_type / surface_format / request_url there)."""
    out = []
    for ev in eventlog.replay():
        if ev.get("event_type") != "manifest_add":
            continue
        p = ev["payload"]
        acq = p.get("acquisition") or {}
        if acq.get("task", "").endswith("2026-09-03_g1_eval_v2_product_surfaces_compression.md") and acq.get("surface"):
            out.append({"doc_id": p["doc_id"], "local_path": p.get("local_path"), "primary_url": p.get("primary_url"),
                        **acq["surface"]})
    return out


def body_of(path: Path, fmt: str) -> str:
    if fmt == "pdf":
        import pypdf
        return "\n".join((pg.extract_text() or "") for pg in pypdf.PdfReader(str(path)).pages)
    text = path.read_text(encoding="utf-8")
    if text.startswith("<!-- kernel harvest:"):
        text = text.split("\n", 1)[1].lstrip("\n")     # the harvester's provenance line, not the surface
    return text.lstrip("﻿")


def main() -> int:
    cfg = load_harness_config(REPO / "assessment" / "config" / "harness.toml")
    probe = G1DeclaredProbe(cfg.g1_uncertainty_field_patterns, cfg.g1_footnote_field_patterns,
                            cfg.g1_id_field_patterns, cfg.g1_footnote_uncertainty_vocabulary)
    rows = surfaces_from_events()
    if not rows:
        raise SystemExit("FATAL: no manifest_add events carry a surface block for the v2 task")
    results = {}
    for s in rows:
        path = REPO / s["local_path"]
        if not path.exists():
            raise SystemExit(f"FATAL: corpus file missing for {s['doc_id']}: {path}")
        fmt = s.get("surface_format") or "text"
        fetched = Fetched(requested_url=s["request_url"], final_url=s["request_url"], status=200, headers={},
                          body=body_of(path, fmt), content_type=MEDIA.get(fmt, "text/plain"))
        score, evidence, obs = probe.evaluate(fetched, {"mediaType": MEDIA.get(fmt, "text/plain")})
        results[s["doc_id"]] = {"surface_type": s["surface_type"], "surface_format": fmt,
                                "surface_file": s["local_path"], "request_url": s["request_url"],
                                "score": int(score), "score_name": score.name, "evidence": evidence,
                                "observations": {k: v for k, v in obs.items() if k != "heuristic"}}
        print(f"{s['doc_id']:75s} {s['surface_type']:14s} {fmt:5s} -> {score.name:8s} {evidence[:90]}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"task": "cc_tasks/2026-09-03_g1_eval_v2_product_surfaces_compression.md step 3",
                               "probe": probe.probe_id, "epoch": EPOCH, "run_at": datetime.now(timezone.utc).isoformat(),
                               "heuristic": "field-name patterns from harness.toml [g1]; values not inspected",
                               "surfaces": results}, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"-> {OUT.relative_to(REPO)} ({len(results)} surfaces)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
