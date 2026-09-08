#!/usr/bin/env python3
"""Register the retained-uncited-body count DD-058 decides about. **Zero spend, no network.**

Task `cc_tasks/2026-09-07_scan_run_2.md` §1.4. The number is RECOUNTED here from the two
artifacts it is about — `git ls-files` over the committed evidence store, and the event log's
`observation_recorded` body digests — never read out of a RESULT or a task file, so the
registry and the record cannot disagree.

The bare name is the PRE-FLIGHT census: the bodies that were uncited before this cycle ran.
It carries no cycle because it is a one-time fact about what the store held when
`publish.promote_evidence` was installed. `--cycle` registers the same census AFTER a cycle,
under a cycle-suffixed name (DD-056), and the two are not the same number.

**The set can only shrink, and only by citation.** Staging means a cycle promotes only what it
cites, so no later cycle can ADD to it. But content addressing means a cycle that re-fetches
an unchanged page cites a digest the store already holds — and if that body was one of the
uncited ones, it stops being uncited without a byte moving. Cycle 2 did exactly this once:
`bjs.ojp.gov/data/topic` came back byte-identical to a body left by an earlier diagnostic run,
so the census went 418 -> 417. That is the census tracking its artifact, which is what a
recounted Result is for; DD-058's amendment records it.

    /opt/anaconda3/bin/python3 scripts/register_evidence_retention_result.py --dry-run
    /opt/anaconda3/bin/python3 scripts/register_evidence_retention_result.py
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "assessment" / "harness"))

sys.path.insert(0, str(REPO / "scripts"))

from kg import eventlog                                             # noqa: E402
from scan.model import EVIDENCE_ROOT                                # noqa: E402
from seldon_artifacts import live_artifact                          # noqa: E402

TASK = "cc_tasks/2026-09-07_scan_run_2.md"
OBS_EVENT = "observation_recorded"
NAME = "scan_evidence_uncited_real_host_bodies"

ARTIFACTS = [
    ("Script", "register_evidence_retention_result",
     "scripts/register_evidence_retention_result.py",
     "Recounts the committed scan evidence bodies that no Observation on the event log cites, "
     f"and registers the count DD-058's retention decision is about. Task {TASK}."),
    ("DataFile", "scan_evidence_store", "corpus/evidence/scan",
     "The content-addressed store holding the whole response bodies a scan Finding cites; the "
     "one corpus/ lane that is tracked, because a verdict whose evidence the repo does not "
     f"hold is not evidence (invariant 3). Task {TASK}."),
]


def cited_digests() -> set:
    """Every body digest an Observation on the log points at."""
    out = {(ev.get("response") or {}).get("body_sha256") for ev in eventlog.replay()
           if ev.get("event_type") == OBS_EVENT}
    out.discard(None)
    return out


def tracked_digests() -> list:
    """Digests COMMITTED to the store. `git ls-files`, not a directory walk: an untracked
    body in the working tree is this session's litter, not part of the retained set, and the
    two answers differ by exactly the thing being counted."""
    out = subprocess.run(["git", "ls-files", str(EVIDENCE_ROOT.relative_to(REPO))],
                         capture_output=True, text=True, cwd=REPO)
    if out.returncode:
        raise SystemExit(f"FATAL: git ls-files failed: {out.stderr.strip()[-300:]}")
    return [line.rsplit("/", 1)[-1] for line in out.stdout.split()]


def census(before_params_hash: str | None = None) -> dict:
    """The uncited-tracked-body census, optionally decomposed by what a cycle cited.

    `before_params_hash` names a cycle to hold OUT: the census then reads as it did before
    that cycle published, and `newly_cited` is the count of tracked bodies that cycle was the
    first to cite. That decomposition is what makes the drift checkable rather than merely
    noticed — `uncited + newly_cited` must equal the earlier census exactly.
    """
    cited, tracked = cited_digests(), set(tracked_digests())
    out = {"tracked_bodies": len(tracked), "cited_digests_on_log": len(cited),
           "uncited_tracked_bodies": len(tracked - cited)}
    if before_params_hash:
        prior = {(ev.get("response") or {}).get("body_sha256") for ev in eventlog.replay()
                 if ev.get("event_type") == OBS_EVENT
                 and ev.get("params_hash") != before_params_hash}
        prior.discard(None)
        newly = (tracked & cited) - prior
        out["newly_cited_by_this_cycle"] = len(newly)
        out["uncited_before_this_cycle"] = len(tracked - prior)
        out["newly_cited_digests"] = sorted(newly)
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--cycle", default=None,
                    help="register the census AFTER this cycle, under a cycle-suffixed name "
                         "(DD-056). Without it the bare pre-flight census is registered.")
    a = ap.parse_args(argv)
    name, ph = NAME, None
    if a.cycle:
        sys.path.insert(0, str(REPO / "scripts"))
        import cycle_results
        from scan import load_params
        from scan.model import params_hash
        ph = params_hash(load_params())
        name = cycle_results.name_for(NAME, a.cycle)
    c = census(ph)
    print(json.dumps({k: v for k, v in c.items() if k != "newly_cited_digests"}, indent=1))
    moved = ("" if not a.cycle else (
        f" Down from {c['uncited_before_this_cycle']} before cycle {a.cycle}: "
        f"{c['newly_cited_by_this_cycle']} of these bodies were re-fetched byte-identically "
        f"and are now CITED, so they left the set without a byte moving. The set is "
        f"monotonically non-increasing and every departure is a citation, never a deletion "
        f"(DD-058 as amended)."))
    desc = (
        f"Bodies committed to corpus/evidence/scan/ that no `observation_recorded` event on "
        f"the log cites: {c['uncited_tracked_bodies']} of {c['tracked_bodies']} tracked, "
        f"against {c['cited_digests_on_log']} distinct digests cited by Observations. They are "
        f"real-federal-host responses left by diagnostic runs, aborted runs and the preflight, "
        f"from before `run.py --evidence-root` staged captures and "
        f"`publish.promote_evidence` made citation the only way into the store. DD-058 retains "
        f"them where they are: a body fetched from a public host is the record that this "
        f"scanner contacted it, under that UA, on that day — the auditable half of the "
        f"harness's own RFC 9309 manners claim — and deleting it to tidy a count is the wrong "
        f"side of invariant 2. Excluded from the promoted-body integrity check, cited by "
        f"nothing. The set can only SHRINK, and only by citation: staging means a cycle "
        f"promotes only what it cites, so nothing can be added, while a cycle that re-fetches "
        f"an unchanged page cites a digest the store already holds and takes that body out of "
        f"the set without moving a byte (DD-058 as amended). "
        f"Separately, 260 fixture blobs were quarantined and 48 removed by "
        f"cc_tasks/2026-09-07_scan_hygiene.md — a fixture body is not an acquisition.{moved} "
        f"Task {TASK}.")
    if a.dry_run:
        print(f"{name}\t{c['uncited_tracked_bodies']}")
        print(desc)
        return 0
    # `art_name`, not `name`: `name` is the RESULT name computed above, and a loop variable
    # called `name` silently rebound it to the last artifact in the list — which registered
    # the cycle-2 census under the DataFile's name `scan_evidence_store`. That Result is bound
    # forever (AD-028) and had to be superseded by hand. The lesson is small and the cost was
    # not: a loop variable never reuses the name of a live binding.
    for kind, art_name, path, d in ARTIFACTS:
        if live_artifact(art_name):
            continue
        r = subprocess.run(["seldon", "artifact", "create", kind, "-p", f"name={art_name}",
                            "-p", f"path={path}", "-p", f"description={d}", "--actor", "cc"],
                           capture_output=True, text=True, cwd=REPO)
        if r.returncode:
            raise SystemExit(f"FATAL: cannot create {kind} {art_name}: "
                             f"{r.stderr.strip()[-400:]}")
    v = c["uncited_tracked_bodies"]
    # By UUID, not by name. `seldon result register --script-name` resolves over ALL artifacts
    # with that name, superseded ones included, so a name that was ever duplicated stays
    # unresolvable even after the twin is superseded — which is what happened here the first
    # time this ran. `live_artifact` already knows the one live id; passing it is both the fix
    # and the stricter reference.
    r = subprocess.run(["seldon", "result", "register", "--value", str(v), "--name", name,
                        "--units", name, "--description", desc,
                        "--script-id", live_artifact("register_evidence_retention_result"),
                        "--data-ids", live_artifact("scan_evidence_store")],
                       capture_output=True, text=True, cwd=REPO)
    if r.returncode == 0:
        print(f"registered {name} = {v}")
        return 0
    if "unique per project graph" in r.stderr and f"value={float(v)}" in r.stderr:
        print(f"{name} already bound at {v}")
        return 0
    print("FAILED:", r.stderr.strip()[-400:])
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
