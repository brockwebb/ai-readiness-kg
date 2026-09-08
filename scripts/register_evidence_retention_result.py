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


def tracked_digests(rev: str | None = None) -> list:
    """Digests COMMITTED to the store, in the working tree or AT A COMMIT.

    `git ls-files`, not a directory walk: an untracked body in the working tree is this
    session's litter, not part of the retained set, and the two answers differ by exactly the
    thing being counted. With `rev`, `git ls-tree` answers the same question about the past —
    which is the only way to know what the store held BEFORE a cycle promoted into it.
    """
    cmd = (["git", "ls-tree", "-r", "--name-only", rev,
            str(EVIDENCE_ROOT.relative_to(REPO))] if rev else
           ["git", "ls-files", str(EVIDENCE_ROOT.relative_to(REPO))])
    out = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO)
    if out.returncode:
        raise SystemExit(f"FATAL: {' '.join(cmd[:3])} failed: {out.stderr.strip()[-300:]}")
    return [line.rsplit("/", 1)[-1] for line in out.stdout.split()]


def publishing_commit(cycle: str) -> str:
    """The commit that FIRST ADDED this cycle's payload — and therefore, by the repo's own
    commit convention, the commit that added the bodies it promoted.

    `cc_tasks/2026-09-08_scan_frame_fss.md` §0. The census's "before this cycle" figure needs
    the tracked set as it was BEFORE the cycle published, and that set is not recoverable from
    today's disk: `git ls-files` returns the store as it is now, which already contains
    everything the cycle promoted. Reading it at this commit's PARENT is the recoverable
    answer, and it is exact rather than approximate.

    The convention this rests on is stated in CLAUDE.md — "Event shards, raw model responses,
    sub-RESULTs, and the RESULT file are committed together with the code that produced them"
    — and a convention is not a guarantee, so `assert_evidence_committed_with_payload` checks
    it against the payload rather than trusting it.
    """
    out = subprocess.run(
        ["git", "log", "--diff-filter=A", "--format=%H", "--", f"state/{cycle}.json"],
        capture_output=True, text=True, cwd=REPO)
    revs = out.stdout.split()
    if not revs:
        raise SystemExit(
            f"FATAL: no commit adds state/{cycle}.json, so the store as it was before that "
            f"cycle published cannot be recovered. A cycle whose payload was never committed "
            f"has no 'before' to compare against.")
    return revs[-1]                     # the FIRST commit to add it; `git log` is newest-first


def assert_evidence_committed_with_payload(cycle: str, rev: str) -> None:
    """Every body this cycle's Observations cite is tracked at `rev`, or the census refuses.

    This is what makes `publishing_commit` a measurement rather than an assumption. If a cycle
    ever commits its payload in one commit and its promoted bodies in another, the parent of
    the payload commit is NOT the pre-cycle store, and the decomposition below would close on
    the wrong number — silently, because every quantity in it would still be an integer.
    """
    payload = json.loads((REPO / "state" / f"{cycle}.json").read_text(encoding="utf-8"))
    cited = {(o.get("response") or {}).get("body_sha256")
             for o in payload.get("observations_detail") or []}
    cited.discard(None)
    if not cited:
        return                          # a re-judged cycle cites bodies through its source
    missing = cited - set(tracked_digests(rev))
    if missing:
        raise SystemExit(
            f"REFUSING: {len(missing)} body digest(s) cited by {cycle} are not tracked at "
            f"{rev[:12]}, the commit that added its payload. The payload and its evidence were "
            f"committed apart, so that commit's parent is not the store as it was before this "
            f"cycle: {sorted(missing)[:3]}. Name the right commit rather than reporting a "
            f"decomposition that closes on the wrong number.")


def cycle_params_hash(cycle: str) -> str:
    """The `params_hash` a CYCLE was measured under, read off its own payload.

    Not `params_hash(load_params())`. That is the hash of the parameters ON DISK NOW, and it
    equals the cycle's only while `params.yaml` has not moved since the cycle ran — which stops
    being true the moment a task corrects a rule's parameters without re-measuring anything
    (`cc_tasks/2026-09-08_scan_harness_v4.md`). The census holds a cycle's observations OUT by
    matching this hash, so reading it from the wrong place does not error: it silently holds
    nothing out and reports a decomposition that does not close.
    """
    payload = REPO / "state" / f"{cycle}.json"
    if not payload.is_file():
        raise SystemExit(f"FATAL: no payload at {payload}; the census cannot hold out a cycle "
                         f"it cannot read the params_hash of")
    return json.loads(payload.read_text(encoding="utf-8"))["params_hash"]


def census(cycle: str | None = None) -> dict:
    """The uncited-tracked-body census, optionally decomposed by what a cycle cited.

    `cycle` names a cycle to hold OUT: the census then also reports what it read BEFORE that
    cycle published, and `newly_cited` is the count of already-retained bodies that cycle was
    the first to cite. That decomposition is what makes the drift checkable rather than merely
    noticed — `uncited_now + newly_cited == uncited_before` must hold exactly.

    **Two sets, two moments, and getting that wrong is what made this red.** The decomposition
    is about the bodies the store ALREADY HELD; a body the cycle itself promoted was in neither
    set before it ran. The first version measured `tracked` once, NOW, and subtracted the
    digests cited before the cycle — so all 160 bodies cycle 2 promoted counted as "uncited
    before this cycle", and 418 read as 578 = 418 + 160
    (`cc_tasks/2026-09-08_scan_harness_v4_RESULT.md` §7.2). Every quantity was still an
    integer, which is why it failed as a wrong number rather than as an error.

    So `before` is read at the PARENT of the commit that published the cycle
    (`publishing_commit`), which is the one recoverable answer — and the alternative,
    restating the invariant over a set recoverable from today's disk, was rejected because
    there is no such set: nothing on disk distinguishes a body the store held from one this
    cycle promoted, since content addressing makes them identical in every respect but history.
    Git IS the record of that history, and `assert_evidence_committed_with_payload` checks the
    commit actually is the one, rather than trusting the convention that it would be.

    A cycle takes ONE argument, not a hash and a revision: a caller that could pass a mismatched
    pair eventually would.
    """
    cited, tracked = cited_digests(), set(tracked_digests())
    out = {"tracked_bodies": len(tracked), "cited_digests_on_log": len(cited),
           "uncited_tracked_bodies": len(tracked - cited)}
    if cycle:
        rev = publishing_commit(cycle)
        assert_evidence_committed_with_payload(cycle, rev)
        before = set(tracked_digests(f"{rev}^"))
        prior = {(ev.get("response") or {}).get("body_sha256") for ev in eventlog.replay()
                 if ev.get("event_type") == OBS_EVENT
                 and ev.get("params_hash") != cycle_params_hash(cycle)}
        prior.discard(None)
        # Only bodies the store ALREADY HELD can leave the uncited set; one the cycle promoted
        # was never in it.
        newly = (before & cited) - prior
        out["published_at_commit"] = rev
        out["tracked_bodies_before_this_cycle"] = len(before)
        out["promoted_by_this_cycle"] = len(tracked - before)
        out["newly_cited_by_this_cycle"] = len(newly)
        out["uncited_before_this_cycle"] = len(before - prior)
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
    name = NAME
    if a.cycle:
        sys.path.insert(0, str(REPO / "scripts"))
        import cycle_results
        name = cycle_results.name_for(NAME, a.cycle)
    c = census(a.cycle)
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
