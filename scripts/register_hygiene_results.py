#!/usr/bin/env python3
"""Register the two counts `cc_tasks/2026-09-07_scan_hygiene.md` produced. **Zero spend.**

§1 and §2 each name a number the task must register. Neither is read out of a RESULT: this
script recounts both from the artifacts themselves — the event log for the annotations, the
quarantine directory for the blobs — so a number in the RESULT and a number in the registry
cannot disagree.

Idempotent in the only sense AD-028 allows: a name already bound AT THE SAME VALUE is this
script re-running; at a different value it is drift and stays an error.

    /opt/anaconda3/bin/python3 scripts/register_hygiene_results.py --dry-run
    /opt/anaconda3/bin/python3 scripts/register_hygiene_results.py
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "assessment" / "harness"))

import annotate_orphan_findings as ann                              # noqa: E402
import quarantine_fixture_evidence as qfe                           # noqa: E402
from seldon_artifacts import live_artifact                          # noqa: E402

TASK = "cc_tasks/2026-09-07_scan_hygiene.md"

#: Artifacts this task minted, created before the Results that cite them — `seldon result
#: register` resolves every reference BEFORE writing an event (AD-028), so an unregistered
#: Script is a hard failure rather than a dropped link.
ARTIFACTS = [
    ("Script", "annotate_orphan_findings", "scripts/annotate_orphan_findings.py",
     "Appends one `finding_evidence_unretained` event per Finding on the log whose cited "
     "obs_ids no observation_recorded event carries. Append-only correction, the pattern of "
     f"`extraction_superseded` and `edge_endpoint_alias`; never a deletion. Task {TASK}."),
    ("Script", "quarantine_fixture_evidence", "scripts/quarantine_fixture_evidence.py",
     "Moves control-fixture test litter out of the committed scan evidence store. A blob is "
     "litter only if it names the fixture host AND no Observation on the log cites its "
     f"digest; the control cycle's own fixture evidence is cited and stays. Task {TASK}."),
    ("Script", "framework_writeback", "scripts/framework_writeback.py",
     "The shared framework write-back helper: one definition of every `counts` denominator "
     "(candidate-excluded for the framework's own content per DD-054, candidate-inclusive for "
     "the instrument's), regenerated on every write-back, plus the `framework_writeback` "
     f"event that records who changed the record of record. Task {TASK}."),
    ("Script", "framework_writeback_normalize", "scripts/framework_writeback_normalize.py",
     "Normalises every EVIDENCED_BY_INTERNAL edge onto the `artifact_path` + `internal:` "
     "shape that seventeen of the twenty already used, and goes through the shared writer. "
     f"Task {TASK}."),
    ("DataFile", "scan_evidence_unretained_2026-09-06", "events/batch-032.jsonl",
     "One `finding_evidence_unretained` event per orphaned control Finding of the 2026-09-06 "
     "scaffold cycles, carrying the Finding's params_hash, whether any committed revision of "
     f"params.yaml hashes to it, and the obs_ids the log does not hold. Task {TASK}."),
    ("DataFile", "scan_evidence_fixture_quarantine",
     "corpus/quarantine/evidence_scan_fixture/reason.txt",
     "The swept control-fixture evidence blobs, one digest per line under a header giving the "
     f"discriminator, the date and the counts. Task {TASK}."),
]


def rows() -> list:
    """(name, value, script, data, description). Both values recounted from the artifact."""
    annotated = len(ann.annotated())
    orphans = len({ev["finding_id"] for ev in ann.orphans()})
    if annotated != orphans:
        raise SystemExit(f"FATAL: {orphans} orphan Findings on the log but {annotated} "
                         f"annotations; run scripts/annotate_orphan_findings.py first")
    quarantined = len([p for p in
                       (REPO / "corpus" / "quarantine" / "evidence_scan_fixture").iterdir()
                       if p.name != "reason.txt"])
    remaining = qfe.classify()
    if remaining["litter"]:
        raise SystemExit(f"FATAL: {len(remaining['litter'])} fixture blobs still uncited in "
                         f"the evidence store; run scripts/quarantine_fixture_evidence.py")
    return [
        ("scan_control_findings_evidence_unretained_2026-09-06", annotated,
         "annotate_orphan_findings", "scan_evidence_unretained_2026-09-06",
         f"Findings on the event log whose cited obs_ids no `observation_recorded` event "
         f"carries, all of them control Findings of the 2026-09-06 scaffold cycles, each now "
         f"carrying a `finding_evidence_unretained` annotation. 60 of the {annotated} were "
         f"derived under a params_hash that matches NO committed revision of "
         f"assessment/harness/scan/params.yaml, so they could not be re-derived even if their "
         f"Observations were recovered. None of them is in the denominator of any "
         f"re-derivation gate: `rederive.py:56-57` builds its `recorded` set from a cycle "
         f"payload's `findings_detail` + `control_findings_detail`, and zero of these ids "
         f"appear in any surviving payload. Not deleted — invariant 1 forbids it and "
         f"invariant 3 is why they are marked. Task {TASK}."),
        ("scan_evidence_fixture_blobs_quarantined", quarantined,
         "quarantine_fixture_evidence", "scan_evidence_fixture_quarantine",
         f"Committed evidence blobs moved to corpus/quarantine/evidence_scan_fixture/ because "
         f"they are control-fixture test output: the stored body names the fixture host and no "
         f"Observation on the event log cites its digest. Written by tests/test_scan_harness.py "
         f"at ~24 per run before tests/conftest.py redirected the evidence root under test; "
         f"content addressing did not dedupe them because the fixture server's ephemeral port "
         f"is substituted into every body carrying HOSTPORT. A further 48 blobs of the same "
         f"kind, written by this task's own diagnostic runs and never committed, were removed "
         f"rather than moved. 8 fixture-host blobs ARE cited by Observations on the log — the "
         f"control cycle's own evidence — and were left in place; quarantining those would "
         f"have stranded live Observations, which is the defect §1 of the same task exists to "
         f"annotate. Moved, never deleted (invariant 2). Task {TASK}."),
    ]


def ensure_artifacts(dry_run: bool) -> dict:
    """Create the artifacts this task mints, exactly once each.

    **Corrected 2026-09-07 by `cc_tasks/2026-09-07_scan_run_2.md` §1.4.** The guard used to be
    `name in $(seldon artifact list --type <kind>)`, and `seldon artifact list` does not print
    names — only type, state and UUID. The test was therefore always False, so every run of
    this script minted a twin of all six artifacts; `seldon artifact create` enforces name
    uniqueness only on Results (AD-028), so nothing refused it. The twin surfaces later, as
    `ValueError: Multiple Script artifacts with name=…`, when a Result tries to reference one.
    `scripts/seldon_artifacts.live_artifact` asks the graph, which is where the answer is.
    """
    made, present = [], []
    for kind, name, path, desc in ARTIFACTS:
        if live_artifact(name):
            present.append(name)
            continue
        if dry_run:
            made.append(name)
            continue
        r = subprocess.run(["seldon", "artifact", "create", kind, "-p", f"name={name}",
                            "-p", f"path={path}", "-p", f"description={desc}",
                            "--actor", "cc"], capture_output=True, text=True, cwd=REPO)
        if r.returncode:
            raise SystemExit(f"FATAL: cannot create {kind} {name}: {r.stderr.strip()[-400:]}")
        made.append(name)
    return {"created": made, "already_present": present}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    data = rows()
    arts = ensure_artifacts(a.dry_run)
    print(json.dumps(arts, indent=1))
    if a.dry_run:
        for n, v, sc, dn, note in data:
            print(f"{n}\t{v}\t{sc}\t{dn}")
        return 0
    ok, already, failed = 0, [], []
    for n, v, sc, dn, note in data:
        r = subprocess.run(["seldon", "result", "register", "--value", str(v), "--name", n,
                            "--units", n, "--description", f"{note}",
                            "--script-name", sc, "--data-name", dn],
                           capture_output=True, text=True, cwd=REPO)
        if r.returncode == 0:
            ok += 1
        elif "unique per project graph" in r.stderr and f"value={float(v)}" in r.stderr:
            already.append(n)
        else:
            failed.append(n)
            print("FAILED:", n, r.stderr.strip()[-400:])
    print(f"registered {ok}, already at this value {len(already)}, failed {len(failed)} "
          f"(of {len(data)})")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
