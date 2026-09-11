#!/usr/bin/env python3
"""The Results the L0 report quotes that no earlier task registered. **Zero spend, no network.**

Task `cc_tasks/2026-09-09_report_draft.md` §0.2-§0.4. Four families, three sources, and every
value is **RECOUNTED here from the artifact it is about** — never read out of a RESULT, a task
file or a prior report. A number typed into a registrar is a number the registry can no longer
check, and the whole point of the report quoting Results by name is that a stranger can walk
back from the sentence to the bytes.

1. `fss_scan_netlocs_<frame>` — the target list names 22 NETLOCS for 19 agency-level HOSTS,
   because each of the three Tier C bodies declares a machine entry point on its own hostname.
   The roster stays 19; the two counts answer different questions and the report needs both.
2. `fss_scan_netlocs_contacted_<cycle>` — what the cycle actually touched, from the payload's
   own per-host request counter rather than from the target list, because the difference
   between the two IS the finding (`cc_tasks/2026-09-08_scan_run_3b_RESULT.md` §2).
3. `scan_a12_tier{A,C}_*_<cycle>` — A12 decomposed by tier. The pooled `scan_a12_pass` family
   is bound (AD-028) and pools 16 Tier A hosts with 3 Tier C reference hosts, which DD-059 says
   never share a denominator. Re-binding the pooled name at a tier-A value is refused by the
   registry and would be number mutation if it were not, so the decomposition gets NEW names
   and each description says which pooled Result it decomposes.
4. `scan_a5_fail_offroster_sitemap_<cycle>` — of this cycle's A5 failures, how many belong to a
   host whose `robots.txt` declares a sitemap on a netloc outside the frame that the scanner
   then did NOT fetch. **Measured, not assumed:** the prior RESULT asserted that no sitemap was
   retrieved from either sibling netloc, and the log says both were.

    /opt/anaconda3/bin/python3 scripts/register_l0_report_results.py [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import urllib.parse
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "assessment" / "harness"))
sys.path.insert(0, str(REPO / "scripts"))

import cycle_results                                                # noqa: E402
from scan import load_params                                        # noqa: E402

TASK = "cc_tasks/2026-09-09_report_draft.md"
SCRIPT_ARTIFACT = "register_l0_report_results"

#: The frame epoch, which is not the cycle. `fss_*_2026-09` is a family of facts about the
#: TARGET LIST; `scan_*_2026-09-09` is a family of facts about one measurement of it. Passing
#: the frame epoch as the "cycle" to the registrar is what makes `check_name` accept the frame
#: suffix, and the two families stay legible as two.
FRAME_EPOCH = "2026-09"

#: The fixture server binds an ephemeral port on loopback. Its netlocs are controls, not hosts.
_LOOPBACK = "127.0.0.1"


def payload(cycle: str) -> dict:
    return json.loads((REPO / "state" / f"{cycle}.json").read_text(encoding="utf-8"))


def evidence_payload(p: dict) -> dict:
    """The payload the COLLECTION is on — `build_l0_matrices`', which owns the rule and states
    why: a re-judgement issues no request and records no Observation, so anything counted off
    the observations has to be counted off the cycle it derives from."""
    import build_l0_matrices
    return build_l0_matrices.evidence_payload(p)


def targets(params: dict) -> dict:
    return json.loads(
        (REPO / "state" / f"{params['cycle']['targets']}.json").read_text(encoding="utf-8"))


def tier_of(params: dict) -> dict:
    return {r["doc_id"]: r.get("tier", "A") for r in targets(params)["rows"] if r.get("doc_id")}


def netlocs_declared(params: dict) -> int:
    """Distinct netlocs on the target list. Counted from the rows' URLs, not from the file's
    own `netloc_count` header: a header is a claim about the rows and this is the rows."""
    return len({urllib.parse.urlsplit(r["url"]).netloc.lower() for r in targets(params)["rows"]})


def netlocs_contacted(p: dict) -> int:
    """Netlocs this cycle issued at least one request to, from the payload's own socket-level
    counter. Loopback control fixtures are excluded: a fixture is not a host."""
    return len([h for h in (p.get("requests_per_host") or {})
                if not h.startswith(_LOOPBACK) and (p["requests_per_host"][h] or 0) > 0])


def a12_by_tier(p: dict, tiers: dict) -> dict:
    """A12's verdicts split by tier, from the cycle's own matrix rows. A12 judges a HOST, so
    the population is the `well_known` rows and nothing else."""
    out: dict = {"A": {}, "C": {}}
    for r in p["matrix"]:
        if r["surface_kind"] != "well_known":
            continue
        t = tiers.get(r["doc_id"], "A")
        v = r["verdicts"].get("A12")
        if v is None:
            continue
        out.setdefault(t, {}).setdefault(v, 0)
        out[t][v] += 1
    return out


def offroster_sitemap_fails(p: dict, params: dict, ev: dict | None = None) -> dict:
    """A5 failures attributable to a declared sitemap the scanner declined to follow.

    Read from the cycle's own bytes: every `robots.txt` body it retained is re-parsed for
    `Sitemap:` lines, each declaration's netloc is compared to the frame, and each declared URL
    is looked up in the set of URLs the cycle actually requested. A host counts only if it
    declares a sitemap OFF the frame AND that URL was never fetched AND its A5 verdict is
    `fail` — all three, because any one of them alone names a different thing.

    **Two payloads, because this asks two questions.** The VERDICT is `p`'s — a re-judgement's
    verdicts are its own. The DECLARATIONS and the requests are read off the retained bytes,
    which a re-judgement does not have (`observations_detail: []`); `ev` is the measured cycle it
    derives from. Read off the re-judged payload alone this returns "no host declared a sitemap
    anywhere", which is a caveat measured empty for the wrong reason.
    """
    ev = ev if ev is not None else p
    frame = {h["host"] for h in targets(params)["hosts"]}
    requested = {(o.get("request") or {}).get("url", "") for o in ev["observations_detail"]}
    a5_verdict = {f["target_doc_id"]: f["verdict"] for f in p["findings_detail"]
                  if f["leg"] == "A5"}
    doc_of_host = {}
    for r in p["matrix"]:
        nl = urllib.parse.urlsplit(r["url"]).netloc.lower()
        doc_of_host.setdefault(nl, []).append(r["doc_id"])

    # DISTINCT (host, declaration) pairs. `robots.txt` is fetched once per leg, so counting
    # declaration lines counts the same declaration a dozen times and reports a frame-wide
    # figure an order of magnitude too large.
    declared, off, unfollowed, fails = set(), [], [], []
    for o in ev["observations_detail"]:
        url = (o.get("request") or {}).get("url", "")
        body = (o.get("response") or {}).get("body_path")
        if not url.endswith("/robots.txt") or not body:
            continue
        host = urllib.parse.urlsplit(url).netloc.lower()
        if host.startswith(_LOOPBACK):
            continue
        path = REPO / body
        if not path.is_file():
            continue
        for decl in re.findall(r"(?im)^\s*sitemap\s*:\s*(\S+)", path.read_text(errors="replace")):
            declared.add((host, decl))
            dn = urllib.parse.urlsplit(decl).netloc.lower()
            if dn in frame:
                continue
            off.append((host, decl))
            if decl in requested:
                continue
            unfollowed.append((host, decl))
            for doc in doc_of_host.get(host, []):
                if a5_verdict.get(doc) == "fail":
                    fails.append((doc, decl))
    return {"declarations": len(declared), "declaring_hosts": len({h for h, _ in declared}),
            "off_frame": sorted(set(off)),
            "off_frame_unfollowed": sorted(set(unfollowed)), "fails": sorted(set(fails))}


#: The three bodies that have refused an identified, robots-compliant client every time this
#: instrument has looked. Named, because the claim is about these three and not about a
#: threshold: each returns a refusal status on effectively every probe.
REFUSING = ("www.bls.gov", "www.bts.gov", "www.ssa.gov")

#: The measurement artifacts that could carry the refusal, oldest first. DECLARED, because the
#: five record it under three different key names and two different error conventions, and a
#: sweep for one key name silently misses the others (this sweep did, and reported three).
#: Each is then CHECKED: the count is how many of these actually say all three bodies refused,
#: never how many files are listed here.
REFUSAL_ARTIFACTS = (
    ("state/scan_preflight_2026-09.json", "hosts_unobservable_ids"),
    ("state/scan_2026-09-07.json", "observations"),
    ("state/scan_2026-09-07b.json", "observations"),
    ("state/fss_preflight_2026-09.json", "refusing_identified_client"),
    ("state/scan_2026-09-09.json", "observations"),
    # Cycle 4, the sixth. Listed because it is a measurement that could carry the refusal, and
    # then CHECKED like the other five: the count is how many of these actually record all
    # three bodies refusing, never how many files are named here.
    ("state/scan_2026-09-10.json", "observations"),
)

#: Agency codes, for the pre-flight that records bodies by code rather than by host.
_CODE_OF = {"www.bls.gov": "BLS", "www.bts.gov": "BTS", "www.ssa.gov": "ORES"}


def refusal_measurements() -> dict:
    """How many measurement artifacts record ALL THREE bodies refusing an identified client.

    The refusal outlives two changes of convention and reading it needs both: cycle 1 filed a
    403 under `http_4xx`, because the closed error set had no member for a refusal until
    harness-v3 added one, and the two pre-flights record bodies rather than observations. A
    count that read only today's convention would report the refusal as newer than it is.
    """
    hit, missing = [], []
    for rel, key in REFUSAL_ARTIFACTS:
        path = REPO / rel
        if not path.is_file():
            missing.append(rel)
            continue
        doc = json.loads(path.read_text(encoding="utf-8"))
        if key == "observations":
            seen = {o["target_doc_id"].split(":")[-1]
                    for o in doc.get("observations_detail", [])
                    if o.get("error_class") in ("refused", "http_4xx")}
            ok = all(h in seen for h in REFUSING)
        else:
            listed = set(doc.get(key) or ())
            ok = all(h in listed or _CODE_OF[h] in listed for h in REFUSING)
        (hit if ok else missing).append(rel)
    return {"measurements": len(hit), "artifacts": hit, "not_recording_it": missing}


def ensure_targets_v2(params: dict, dry: bool) -> str:
    """Register the v2 target list as its own DataFile, building on v1.

    §0.2. v1 was registered on 2026-09-08 and its description is the record the frame RESULT
    cites: "19 hosts, 65 surfaces". The file on that path now carries `targets_version: 2` —
    the same 65 rows, but each with its own synthetic id (`host:` / `home:` / `machine:`) and a
    22-netloc host list, rewritten by `cc_tasks/2026-09-08_scan_run_3b.md` decision 1. Nothing
    registered that. v1 stays LIVE and is not superseded: four Results are COMPUTED_FROM it and
    its description is a true statement about the bytes it was registered against.
    """
    from seldon_artifacts import live_artifact
    doc = targets(params)
    name = f"{params['cycle']['targets']}_v{doc['targets_version']}"
    if dry:
        return name
    found = live_artifact(name)
    if found:
        _link_derived_from(found, params["cycle"]["targets"])
        return found
    by_kind = json.dumps(doc["by_kind"], sort_keys=True)
    desc = (
        f"The cycle-3 target list, VERSION {doc['targets_version']}, derived_from version "
        f"{doc['derived_from_version']} (DataFile {params['cycle']['targets']}, which stays "
        f"live and whose description is a true statement about the v1 bytes). Same "
        f"{doc['surfaces']} declared surfaces as v1 and the same {doc['tier_a_agencies']} Tier "
        f"A agencies plus {doc['tier_c_hosts']} Tier C reference hosts; what v2 changes is the "
        f"IDENTIFIERS and the host list. Every row now carries its own doc_id and the id says "
        f"what kind of surface it is: `host:` the well-known set (unchanged since cycle 1, so "
        f"A12's Findings stay comparable), `home:` the host's own page, `machine:` a declared "
        f"machine entry point, `scan-...` an admitted corpus Document. That is what makes 'one "
        f"leg asked once per host' checkable. The host list is {doc['netloc_count']} NETLOCS "
        f"for {doc['host_count']} agency-level hosts, because all three Tier C machine entry "
        f"points sit on their own hostname. By kind: {by_kind}. Written by "
        f"scripts/build_fss_targets.py under cc_tasks/2026-09-08_scan_run_3b.md; registered by "
        f"{TASK} §0.2, which found no v2 registration existed. Task {TASK}.")
    r = subprocess.run(["seldon", "artifact", "create", "DataFile", "--actor", "cc",
                        "-p", f"name={name}", "-p",
                        f"path=state/{params['cycle']['targets']}.json",
                        "-p", f"description={desc}"],
                       capture_output=True, text=True, cwd=REPO)
    if r.returncode:
        raise SystemExit(f"FATAL: cannot create DataFile {name}: {r.stderr.strip()[-400:]}")
    made = live_artifact(name)
    if not made:
        raise SystemExit(f"FATAL: created DataFile {name} but cannot resolve it")
    _link_derived_from(made, params["cycle"]["targets"])
    return made


#: The lineage edge from one version of a DataFile to the one it was built from.
#:
#: `derived_from` reads better and is what the task asked for, and the schema refuses it:
#: it may only originate from a Result. `supersedes` is ArchitecturalDecision-only,
#: `produces` is BuildRun-only. `computed_from` is the ONE edge a DataFile may originate,
#: and its meaning is right here — v2 was computed from v1's frame by re-running the target
#: build over it. Recorded as a constraint met rather than a preference, because the next
#: reader will reach for `derived_from` too; the phrase "derived_from version 1" is carried
#: verbatim in v2's description, where the schema cannot object to it.
LINEAGE_REL = "computed_from"


def _link_derived_from(from_id: str, to_name: str) -> None:
    """v2 -[COMPUTED_FROM]-> v1. Idempotent: `seldon link create` MERGEs, so re-running this
    registrar re-asserts the edge rather than duplicating it."""
    r = subprocess.run(["seldon", "link", "create", "--from-id", from_id,
                        "--rel", LINEAGE_REL, "--to-name", to_name, "--actor", "cc"],
                       capture_output=True, text=True, cwd=REPO)
    if r.returncode:
        raise SystemExit(f"FATAL: cannot link {LINEAGE_REL} {to_name}: "
                         f"{r.stderr.strip()[-300:]}")


def ensure_script(dry: bool) -> None:
    from seldon_artifacts import live_artifact
    if dry or live_artifact(SCRIPT_ARTIFACT):
        return
    r = subprocess.run(
        ["seldon", "artifact", "create", "Script", "--actor", "cc",
         "-p", f"name={SCRIPT_ARTIFACT}",
         "-p", "path=scripts/register_l0_report_results.py",
         "-p", f"description=Recounts and registers the Results the L0 report quotes that no "
               f"earlier task bound: the declared and contacted netloc counts, A12 decomposed "
               f"by tier, and the off-frame sitemap caveat. Every value is derived from the "
               f"artifact it describes. Task {TASK}."],
        capture_output=True, text=True, cwd=REPO)
    if r.returncode:
        raise SystemExit(f"FATAL: cannot create Script artifact: {r.stderr.strip()[-400:]}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--cycle", default=None,
                    help="register the CYCLE family for a cycle other than params.cycle.name — "
                         "a re-judgement included. The two other batches are skipped then; see "
                         "the module docstring for which registrar owns each.")
    a = ap.parse_args(argv)
    params = load_params()
    cycle = a.cycle or params["cycle"]["name"]
    p = payload(cycle)
    ev = evidence_payload(p)
    tiers = tier_of(params)

    nl_declared = netlocs_declared(params)
    nl_contacted = netlocs_contacted(ev)
    a12 = a12_by_tier(p, tiers)
    a5 = offroster_sitemap_fails(p, params, ev)
    refusal = refusal_measurements()
    ph = ev["params_hash"][:12]
    ev_cycle = ev["cycle"]
    #: Appended to every description whose value is counted off OBSERVATIONS, when the cycle
    #: being registered is a re-judgement. A re-judgement issues no request and records no
    #: Observation, so the number is the measured cycle's and the description has to say so —
    #: otherwise the Result reads as a claim that a re-judgement contacted 35 netlocs.
    evidence_note = ("" if ev_cycle == cycle else
                     f" Registered under {cycle}, which is a RE-JUDGEMENT and issued no "
                     f"request of its own: this counts {ev_cycle}'s collection, the evidence "
                     f"the re-judgement rests on, and the verdicts it is compared against are "
                     f"{cycle}'s.")

    ensure_script(a.dry_run)
    targets_v2 = ensure_targets_v2(params, a.dry_run)

    batches = [
        # ---- the frame family: facts about the TARGET LIST, on the frame epoch ----
        ("frame", FRAME_EPOCH, f"{params['cycle']['targets']}_v2", [
            ("fss_scan_netlocs", nl_declared,
             f"Distinct netlocs on the cycle-3 target list ({params['cycle']['targets']} v2), "
             f"counted from the rows' own URLs. The ROSTER is 19 hosts, one per recognized "
             f"body, and stays 19: this is larger because all three Tier C reference bodies "
             f"declare a machine entry point on its own hostname (catalog.data.gov, "
             f"data.nist.gov, open.gsa.gov). The two counts answer different questions and a "
             f"report that quotes one for the other overstates the frame. Task {TASK} §0.2."),
        ]),
        # ---- the cycle family: facts about the MEASUREMENT ----
        ("cycle", cycle, cycle, [
            ("fss_scan_netlocs_contacted", nl_contacted,
             f"Netlocs cycle {ev_cycle} (params_hash {ph}...) issued at least one HTTP request "
             f"to, counted at the socket from the payload's own per-host counter, loopback "
             f"control fixtures excluded. This EXCEEDS the {nl_declared} netlocs the target "
             f"list names, and the excess is the finding: two hosts declare their sitemap on a "
             f"sibling netloc and the scanner followed the declaration "
             f"(cc_tasks/2026-09-08_scan_run_3b_RESULT.md §2). A contact bound stated as a "
             f"closed list cannot hold while a discovery leg reads what the host actually "
             f"says.{evidence_note} Task {TASK} §0.2."),
            ("scan_a5_fail_offroster_sitemap", len(a5["fails"]),
             f"Of cycle {cycle}'s A5 `fail` verdicts, how many belong to a host whose "
             f"robots.txt declares a sitemap on a netloc OUTSIDE the frame that the scanner "
             f"then did not fetch. MEASURED from cycle {ev_cycle}'s retained robots.txt bodies "
             f"re-parsed for Sitemap: lines ({a5['declarations']} distinct declarations "
             f"from {a5['declaring_hosts']} of the frame's hosts, {len(a5['off_frame'])} of "
             f"them naming an off-frame netloc), compared against the set of "
             f"URLs the cycle actually requested. The scanner followed every declaration it "
             f"found, off-frame ones included, so no A5 failure is attributable to an "
             f"unfollowed declaration and this caveat is empty for this cycle. It is registered "
             f"at its measured value rather than omitted, because a caveat that is absent and "
             f"a caveat that is zero read the same in prose and are not the same claim."
             f"{evidence_note} Task {TASK} §0.4."),
            ("scan_refusal_consecutive_measurements", refusal["measurements"],
             f"Separate measurement artifacts in state/ that record ALL THREE of "
             f"{', '.join(REFUSING)} declining an identified, robots-compliant client: "
             f"{', '.join(refusal['artifacts'])}. Counted by re-reading each artifact rather "
             f"than by trusting a prior report, and the count spans two error conventions: "
             f"cycle 1 filed those refusals under `http_4xx` because the closed error set had "
             f"no member for a refusal until harness-v3 added one. Two of the "
             f"{refusal['measurements']} are pre-flights that record bodies rather than "
             f"observations, and one of those names them by agency code. This is the "
             f"persistence behind the report's accessibility finding: not a transient, and not "
             f"a sampling accident. Task {TASK} §2."),
        ]),
        # ---- A12 decomposed, from the matrix ----
        ("a12", cycle, f"scan_matrix_{cycle_results.cycle_suffix(cycle)}", [
            (f"scan_a12_tier{t}_{v}", a12.get(t, {}).get(v, 0),
             f"**CANDIDATE indicator A12** (DD-054, counted in no framework fraction), cycle "
             f"{cycle}, TIER {t} hosts only: verdicts of `{v}` among the "
             f"{sum(a12.get(t, {}).values())} tier-{t} well-known surfaces. Decomposes the "
             f"pooled `scan_a12_{v}_{cycle_results.cycle_suffix(cycle)}`, which is bound at "
             f"{sum(a12.get(x, {}).get(v, 0) for x in ('A', 'C'))} (AD-028) and pools the 16 "
             f"Tier A agencies with the 3 Tier C reference hosts. DD-059 is that a reference "
             f"host shares no denominator with an agency; the pooled name cannot be re-bound "
             f"at a tier value, so the split is registered under new names and the pooled "
             f"Result keeps its meaning. Task {TASK} §0.3.")
            for t, v in (("A", "pass"), ("A", "fail"), ("A", "error"), ("C", "pass"))
        ]),
    ]

    if a.cycle:
        # **Only the cycle family.** The other two are not this cycle's to register and both
        # would be refused rather than wrong: `fss_scan_netlocs_2026-09` is a fact about the
        # TARGET LIST, bound once on the frame epoch and unchanged at v5 (22 netlocs, same as
        # v4 — the seven declared flagships added surfaces on hosts already in the frame), and
        # the A12-by-tier decomposition was superseded by the family-prefixed
        # `scan_l0_tierc_a12_*` names that `build_l0_matrices` now emits
        # (`cc_tasks/2026-09-10_l0_figures_and_leg_rate_names.md` decision 4). Minting
        # `scan_a12_tierA_*_<cycle>` beside them would be the third name for one population.
        batches = [b for b in batches if b[0] == "cycle"]

    if a.dry_run:
        print(json.dumps({"netlocs_declared": nl_declared, "netlocs_contacted": nl_contacted,
                          "a12_by_tier": a12, "a5_offroster": a5, "refusal": refusal,
                          "targets_v2_artifact": targets_v2}, indent=1))
        for _fam, ep, data, rows in batches:
            for base, v, _note in rows:
                print(f"  {cycle_results.name_for(base, ep):48s} {v}   <- {data}")
        return 0

    total = {"registered": 0, "already_at_this_value": 0, "failed": 0, "of": 0}
    for _fam, epoch, data, rows in batches:
        out = cycle_results.register(
            [(cycle_results.name_for(b, epoch), v, f"{n} ({TASK})") for b, v, n in rows],
            cycle=epoch, script=SCRIPT_ARTIFACT, data=data)
        print(epoch, data, json.dumps(out))
        for k in total:
            total[k] += out[k]
    print(json.dumps(total, indent=1))
    return 1 if total["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
