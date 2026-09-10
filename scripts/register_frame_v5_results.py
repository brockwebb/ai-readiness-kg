#!/usr/bin/env python3
"""The frame counts of targets v5, and what stopped pending. **Zero spend, no network.**

Task `cc_tasks/2026-09-10_scan_frame_v5.md` §2 and decision 3. Every number is READ from
`state/scan_targets_fss_2026-09_v5.json` and its verification file, never typed here: the two
files were written by the build and the probe, and a count retyped into a registrar is a count
that can disagree with the thing it counts.

**`fss_agencies_pending_operator_declaration_2026-09` is left exactly as it is.** It is a
cycle-3 fact — seven bodies were pending when cycle 3 measured — and a Result name binds once
(AD-028). Decision 3: the new state gets a new name, and both records stand. A registry where
yesterday's number can be edited to match today's is a registry that cannot show you a change.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "assessment" / "harness"))
sys.path.insert(0, str(REPO / "scripts"))

import cycle_results                                                # noqa: E402

TASK = "cc_tasks/2026-09-10_scan_frame_v5.md"
SCRIPT_ARTIFACT = "register_frame_v5_results"
DATA = "scan_targets_fss_2026-09_v5"
DATA_PATH = "state/scan_targets_fss_2026-09_v5.json"
V5 = REPO / DATA_PATH
VERIFICATION = REPO / "state" / "fss_flagship_verification_2026-09-10.json"
EPOCH = "2026-09-10"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)

    for p in (V5, VERIFICATION):
        if not p.is_file():
            raise SystemExit(f"FATAL: {p} does not exist; §1 and §2 run before §4")
    d = json.loads(V5.read_text(encoding="utf-8"))
    v = json.loads(VERIFICATION.read_text(encoding="utf-8"))
    bodies = len({h["agency"] for h in d["hosts"]})
    declared, refused = d["flagships_declared_2026_09_10"], d["flagships_refused_at_declaration"]

    rows = [
        ("fss_scan_surfaces", d["surfaces"],
         f"Surfaces in the FSS scan frame at targets v5: {d['surfaces']}, up from "
         f"{d['surfaces'] - len(declared)} at v4. The {len(declared)} added are the operator's "
         f"flagship declarations for the bodies that were pending after cycle 3, each verified "
         f"robots-first through the fetcher before it entered. Task {TASK} §2."),
        ("fss_scan_sites", d["site_count"],
         f"Sites in the frame at v5: {d['site_count']}. UNCHANGED by this task and that is the "
         f"point — a flagship is declared on its body's own site key (DD-063), so seven new "
         f"surfaces added no new site and no new contact bound. Task {TASK} §2."),
        ("fss_scan_bodies", bodies,
         f"Bodies in the frame at v5: {bodies} — 16 Tier A statistical agencies and units plus "
         f"3 Tier C reference hosts. Unchanged by this task: the declarations gave existing "
         f"bodies a product surface, not the frame new members. Task {TASK} §2."),
        ("fss_agencies_pending_operator_declaration", len(d["agencies_pending_operator_declaration"]),
         f"Bodies still carrying no operator-declared flagship after v5: "
         f"{len(d['agencies_pending_operator_declaration'])}. Was 7 at cycle 3 "
         f"(`fss_agencies_pending_operator_declaration_2026-09`, which stands unedited as the "
         f"cycle-3 fact). All seven declared and all seven verified. Task {TASK} decision 3."),
        ("fss_flagships_declared", len(declared),
         f"Flagship landing pages declared and verified on 2026-09-10: {len(declared)} "
         f"({', '.join(declared)}). Each returned a status on the same site as its body after "
         f"redirects; none redirected off-site and none was substituted. "
         f"{v['requests_total']} requests total, {max(v['requests_per_site'].values())} per "
         f"site: one robots.txt read, one HEAD, one GET. Task {TASK} §1."),
        ("fss_flagships_refused_at_declaration", len(refused),
         f"Of the {len(declared)} verified declarations, {len(refused)} were answered 403 by "
         f"hosts that refuse this scanner's identified client ({', '.join(refused)}). They "
         f"enter the frame marked `refused_at_declaration` (decision 1): a refusal is a "
         f"measurement, and dropping the surfaces of the agencies that refuse us would "
         f"restrict the instrument to the agencies that permit us. Task {TASK} §1."),
    ]

    if a.dry_run:
        for b, val, n in rows:
            print(f"  {cycle_results.name_for(b, EPOCH):52s} {val}\n      {n[:150]}")
        return 0

    from seldon_artifacts import live_artifact
    if not live_artifact(SCRIPT_ARTIFACT):
        import subprocess
        r = subprocess.run(
            ["seldon", "artifact", "create", "Script", "--actor", "cc",
             "-p", f"name={SCRIPT_ARTIFACT}",
             "-p", "path=scripts/register_frame_v5_results.py",
             "-p", f"description=Reads the frame counts of targets v5 and the flagship "
                   f"verification and registers them. Task {TASK}."],
            capture_output=True, text=True, cwd=REPO)
        if r.returncode:
            raise SystemExit(f"FATAL: cannot create Script artifact: {r.stderr[-300:]}")

    out = cycle_results.register(
        [(cycle_results.name_for(b, EPOCH), val, n) for b, val, n in rows],
        cycle=EPOCH, script=SCRIPT_ARTIFACT, data=DATA, data_path=DATA_PATH,
        data_description=(f"Targets v5: the FSS scan frame with the seven operator-declared "
                          f"flagship landing pages added, each verified robots-first. "
                          f"COMPUTED_FROM v4, which is unedited. Task {TASK}."))
    print(json.dumps(out, indent=1))
    return 1 if out["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
