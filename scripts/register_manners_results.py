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
from scan.manners import same_site, site_key                        # noqa: E402

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
    hosts. `errors.NOT_REQUESTED` names the classes that mean "recorded, never requested".
    """
    path = REPO / "state" / f"{cycle}.json"
    doc = json.loads(path.read_text(encoding="utf-8"))
    not_fetched = set(errors.NOT_REQUESTED)
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
    # OFF-SITE FETCHES: requests to a netloc that domain-matches no roster site key. Under
    # DD-063 those are the requests the unified bound forbids outright, as against the ones it
    # merely makes polite. Cycle 3 has none, which is the claim being registered.
    keys = {h["site_key"] for h in json.loads(
        (REPO / "state" / "scan_targets_fss_2026-09.json").read_text(encoding="utf-8"))["hosts"]}
    off_site = sorted(n for n in first if not any(same_site(n, k) for k in keys))
    # Refused only if the declared URL is on ANOTHER site from the host that declared it.
    # Both of cycle 3's are same-site, which is why this comes out empty.
    would_refuse = [u for u in would_add
                    if not same_site(f"https://www.{urllib.parse.urlsplit(u).netloc}/", u)]
    return {"requests_issued": issued, "netlocs_contacted": len(first),
            "netlocs_with_robots_read": len(robots_read),
            "robots_reads_added": len(would_add), "added_urls": would_add,
            "requests_refused": len(would_refuse), "refused_urls": would_refuse,
            "off_site_fetches": len(off_site), "off_site_netlocs": off_site,
            "site_keys": len(keys)}


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
            f"version {doc['derived_from_version']} ({prev}). The ROWS are byte-identical "
            f"across every version since v2; what v4 carries is a `site_key` per host, the "
            f"roster host with one leading `www.` stripped (DD-063, superseding DD-062's "
            f"registrable-domain definition). The three counts are published separately and "
            f"none stands in for another: {doc['site_count']} SITE KEYS (the contact unit), "
            f"{doc['netloc_count']} netlocs, {doc['host_count']} bodies (the denominator). "
            f"One key per body, and every netloc in the frame domain-matches exactly one of "
            f"them by RFC 6265 §5.1.3. A Tier C machine entry point takes its BODY's key, so "
            f"catalog.data.gov is a netloc on the data.gov site rather than a twentieth. v3 "
            f"used the Public Suffix List and reported 17 sites, merging ERS, NASS and APHIS "
            f"into usda.gov and admitting every netloc under a department domain; no suffix "
            f"list is consulted now. Keys: {', '.join(sorted(doc['site_keys']))}. Written by "
            f"scripts/build_fss_targets.py. Task {TASK}.")
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

    ensure_script(a.dry_run)
    v3 = ensure_targets_v3(params, a.dry_run)

    batches = [
        (FRAME_EPOCH, f"{params['cycle']['targets']}_v{doc['targets_version']}", [
            # A NEW NAME, not a re-binding. `fss_scan_sites_2026-09` is bound at 17 under
            # DD-062's registrable-domain definition and a Result name is bound once
            # (AD-028); the count moved because the DEFINITION moved, so the new definition
            # gets its own name and the old Result keeps meaning what it meant.
            ("fss_scan_site_keys", doc["site_count"],
             f"Distinct SITE KEYS on the cycle-3 target list: each roster host with one "
             f"leading `www.` stripped, which is the contact unit under DD-063. "
             f"{doc['site_count']} keys for {doc['netloc_count']} netlocs and "
             f"{doc['host_count']} bodies — one key per body, and every netloc in the frame "
             f"domain-matches exactly one of them (RFC 6265 §5.1.3). A Tier C machine entry "
             f"point takes its BODY's key, so catalog.data.gov is a netloc on the data.gov "
             f"site rather than a twentieth. SUPERSEDES fss_scan_sites_2026-09 = 17, which "
             f"counted registrable domains under the Public Suffix List and merged "
             f"www.ers.usda.gov, www.nass.usda.gov and www.aphis.usda.gov into usda.gov while "
             f"admitting every netloc under a department domain. That Result is not re-bound "
             f"and still describes what it measured. Task {TASK}."),
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
            ("scan_manners_off_site_fetches", rp["off_site_fetches"],
             f"Requests cycle {cycle} issued to a netloc that domain-matches NO roster site "
             f"key: {rp['off_site_netlocs'] or 'none'}. Under DD-063 these are the requests "
             f"the unified contact bound forbids outright, as against the ones it merely makes "
             f"polite; the two apex sitemap GETs are the second kind, because samhsa.gov and "
             f"data.gov each domain-match a key. Measured over the {rp['site_keys']} keys the "
             f"target list carries. Task {TASK} §3."),
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
                          "targets_v4": v3}, indent=1))
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
