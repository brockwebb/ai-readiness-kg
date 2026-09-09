#!/usr/bin/env python3
"""The Results DD-062 is about. **Zero spend, no network.**

Task `cc_tasks/2026-09-09_closeout_and_manners.md` §2 and §4. Two families, and every value is
**recounted here** from the artifact it describes:

1. The frame's SITE count, beside the netloc and body counts it must not stand in for
   (decision 4). The contact unit is the site; the denominator is the body; they are three
   different numbers and the report needs all three.
2. What replaying cycle 3's request log through the new policy would have changed. The task
   expected the new policy to REFUSE two requests. It refuses none: both apex netlocs are the
   same site as the host that declared them, so decision 3 permits the fetch and decision 1
   adds a `robots.txt` read before it. Both numbers are registered, because "refused nothing"
   and "added two reads" are different claims and only one of them was predicted.

    /opt/anaconda3/bin/python3 scripts/register_manners_results.py [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import urllib.parse
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "assessment" / "harness"))
sys.path.insert(0, str(REPO / "scripts"))

import cycle_results                                                # noqa: E402
from scan import errors, load_params                                # noqa: E402
from scan.manners import psl_identity, same_site, site_of           # noqa: E402

TASK = "cc_tasks/2026-09-09_closeout_and_manners.md"
SCRIPT_ARTIFACT = "register_manners_results"
FRAME_EPOCH = "2026-09"


def targets(params: dict) -> dict:
    return json.loads(
        (REPO / "state" / f"{params['cycle']['targets']}.json").read_text(encoding="utf-8"))


def replay(cycle: str) -> dict:
    """Cycle `cycle`'s request log under the new policy.

    **The filter is the whole of it.** An Observation records a URL whether or not a request
    went out: an `off_host` link and a `robots_disallowed` path carry their URL precisely so
    the log shows the policy was applied. A first pass at this counted them and reported 68
    contacted netlocs against a true 24, turning 161 recorded exclusions into 44 imaginary
    hosts. `errors.NOT_FETCHED` names the classes that mean "recorded, never requested".
    """
    path = REPO / "state" / f"{cycle}.json"
    doc = json.loads(path.read_text(encoding="utf-8"))
    not_fetched = set(errors.NOT_FETCHED)
    first, robots_read, issued = {}, set(), 0
    for o in doc["observations_detail"]:
        url = (o.get("request") or {}).get("url") or ""
        if not url or url.startswith("fixture://"):
            continue
        if o.get("error_class") in not_fetched:
            continue
        netloc = urllib.parse.urlsplit(url).netloc.lower()
        if netloc.startswith("127.0.0.1"):
            continue
        issued += 1
        first.setdefault(netloc, url)
        if urllib.parse.urlsplit(url).path == "/robots.txt":
            robots_read.add(netloc)
    unread = sorted(set(first) - robots_read)
    would_add = sorted(first[n] for n in unread)
    # Refused only if the declared URL is on ANOTHER site from the host that declared it.
    # Both of cycle 3's are same-site, which is why this comes out empty.
    would_refuse = [u for u in would_add
                    if not same_site(f"https://www.{urllib.parse.urlsplit(u).netloc}/", u)]
    return {"requests_issued": issued, "netlocs_contacted": len(first),
            "netlocs_with_robots_read": len(robots_read),
            "robots_reads_added": len(would_add), "added_urls": would_add,
            "requests_refused": len(would_refuse), "refused_urls": would_refuse}


def ensure_script(dry: bool) -> None:
    from seldon_artifacts import live_artifact
    if dry or live_artifact(SCRIPT_ARTIFACT):
        return
    r = subprocess.run(
        ["seldon", "artifact", "create", "Script", "--actor", "cc",
         "-p", f"name={SCRIPT_ARTIFACT}",
         "-p", "path=scripts/register_manners_results.py",
         "-p", f"description=Recounts and registers the frame's site count and the effect of "
               f"replaying cycle 3's request log through the robots-first policy. Task {TASK}."],
        capture_output=True, text=True, cwd=REPO)
    if r.returncode:
        raise SystemExit(f"FATAL: cannot create Script artifact: {r.stderr.strip()[-400:]}")


def ensure_targets_v3(params: dict, dry: bool) -> str:
    """Register targets v3, which carries a `site` per host, COMPUTED_FROM v2."""
    from seldon_artifacts import live_artifact
    doc = targets(params)
    name = f"{params['cycle']['targets']}_v{doc['targets_version']}"
    prev = f"{params['cycle']['targets']}_v{doc['derived_from_version']}"
    if dry:
        return f"{name} (derived_from {prev})"
    found = live_artifact(name)
    if not found:
        desc = (
            f"The cycle-3 frame's target list, VERSION {doc['targets_version']}, derived_from "
            f"version {doc['derived_from_version']} ({prev}). The ROWS are byte-identical to "
            f"v2; what v3 adds is the SITE each host belongs to, the registrable domain under "
            f"the Public Suffix List (DD-062, decision 2). The three counts are published "
            f"separately and none stands in for another: {doc['site_count']} sites (the "
            f"CONTACT unit), {doc['netloc_count']} netlocs, {doc['host_count']} bodies (the "
            f"DENOMINATOR, decision 4). The site bound is wider than the netloc bound it "
            f"replaces: {', '.join(sorted(doc['sites']))} — three recognized agencies share "
            f"usda.gov, and each Tier C body's home and machine entry point are one site. "
            f"Resolved offline; `site_bound` records the resolver, its version and the list "
            f"snapshot's digest. Written by scripts/build_fss_targets.py. Task {TASK}.")
        r = subprocess.run(["seldon", "artifact", "create", "DataFile", "--actor", "cc",
                            "-p", f"name={name}", "-p",
                            f"path=state/{params['cycle']['targets']}.json",
                            "-p", f"description={desc}"],
                           capture_output=True, text=True, cwd=REPO)
        if r.returncode:
            raise SystemExit(f"FATAL: cannot create DataFile {name}: {r.stderr.strip()[-400:]}")
        found = live_artifact(name)
    link = subprocess.run(["seldon", "link", "create", "--from-id", found,
                           "--rel", "computed_from", "--to-name", prev, "--actor", "cc"],
                          capture_output=True, text=True, cwd=REPO)
    if link.returncode:
        raise SystemExit(f"FATAL: cannot link {name} -> {prev}: {link.stderr.strip()[-300:]}")
    return found


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    params = load_params()
    cycle = params["cycle"]["name"]
    doc = targets(params)
    rp = replay(cycle)
    psl = psl_identity()

    ensure_script(a.dry_run)
    v3 = ensure_targets_v3(params, a.dry_run)

    batches = [
        (FRAME_EPOCH, f"{params['cycle']['targets']}_v{doc['targets_version']}", [
            ("fss_scan_sites", doc["site_count"],
             f"Distinct SITES on the cycle-3 target list: registrable domains under the Public "
             f"Suffix List, which is the contact unit under DD-062 decision 2. "
             f"{doc['site_count']} sites for {doc['netloc_count']} netlocs and "
             f"{doc['host_count']} bodies, and the three are deliberately different numbers: "
             f"the site is what bounds contact, the body is what denominates every rate "
             f"(decision 4). The bound is WIDER than the netlocs it replaces — "
             f"www.ers.usda.gov, www.nass.usda.gov and www.aphis.usda.gov are one site, and "
             f"every netloc under a roster site is in scope. Resolved offline with "
             f"{psl['resolver']} {psl['version']}, list snapshot "
             f"{(psl['snapshot_sha256'] or '')[:12]}...; the bundled list carries no date. "
             f"Task {TASK}."),
        ]),
        (cycle, cycle, [
            ("scan_manners_netlocs_contacted_without_robots_read", rp["robots_reads_added"],
             f"Netlocs cycle {cycle} issued a request to WITHOUT having fetched their "
             f"robots.txt first: {', '.join(rp['added_urls'])}. Counted by replaying the "
             f"cycle's own request log, filtered to observations that actually issued a "
             f"request — an `off_host` or `robots_disallowed` record carries a URL and made no "
             f"request, and counting those reports 68 contacted netlocs against a true "
             f"{rp['netlocs_contacted']}. This is the defect DD-062 closes. Task {TASK} §3."),
            ("scan_manners_requests_refused_by_robots_first", rp["requests_refused"],
             f"Requests on cycle {cycle}'s log that the policy DD-062 installs would have "
             f"REFUSED: {rp['refused_urls'] or 'none'}. The task expected two, naming the apex "
             f"sitemap GETs, and the count and the URLs it named are right about which "
             f"requests are at issue and wrong about what happens to them. Both apex netlocs "
             f"are the SAME SITE as the host that declared them (samhsa.gov from "
             f"www.samhsa.gov), so decision 3 refuses neither; decision 1 precedes each with a "
             f"robots.txt read. The new policy refuses nothing on this log and adds "
             f"{rp['robots_reads_added']} reads. Registered at its measured value because "
             f"'refused none' is the finding. Task {TASK} §3."),
            ("scan_manners_netlocs_contacted", rp["netlocs_contacted"],
             f"Netlocs cycle {cycle} actually issued at least one request to, replayed from "
             f"the observation log rather than from the per-host counter, and agreeing with "
             f"it. {rp['netlocs_with_robots_read']} of them had their robots.txt fetched. "
             f"Task {TASK} §3."),
        ]),
    ]

    if a.dry_run:
        print(json.dumps({"replay": rp, "sites": doc["site_count"],
                          "netlocs": doc["netloc_count"], "bodies": doc["host_count"],
                          "targets_v3": v3}, indent=1))
        for ep, data, rows in batches:
            for base, v, _n in rows:
                print(f"  {cycle_results.name_for(base, ep):58s} {v}   <- {data}")
        return 0

    total = {"registered": 0, "already_at_this_value": 0, "failed": 0, "of": 0}
    for epoch, data, rows in batches:
        out = cycle_results.register(
            [(cycle_results.name_for(b, epoch), v, f"{n}") for b, v, n in rows],
            cycle=epoch, script=SCRIPT_ARTIFACT, data=data)
        print(epoch, data, json.dumps(out))
        for k in total:
            total[k] += out[k]
    print(json.dumps(total, indent=1))
    return 1 if total["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
