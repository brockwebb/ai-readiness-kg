#!/usr/bin/env python3
"""The self row: six verdicts, the URL each one actually read, and which authority answered.

`cc_tasks/2026-09-13_self_row.md` decisions 1, 2 and 3. **Zero model spend, no network** — this
reads the payload the scan already wrote.

**Decision 2 is the whole point of this script.** On a project Pages site the six tier-0 legs do
not all read the same object and cannot: RFC 9309 §2.3 binds robots.txt to an AUTHORITY, so A4,
A5, A11-declared and A12 read `https://<authority>/robots.txt` — a path belonging to a user-site
repository this publication does not own — while A10 and G1-D read the published tree. A row that
printed six verdicts without saying which is which would report four measurements of the wrong
object as measurements of this publication. So every leg carries `urls_read`, the authority that
answered, and whether that authority **is** this publication.

**Decision 3: a `fail` stays visible.** Nothing here improves a verdict and nothing under `docs/`
is changed after measurement. A publisher who repairs a site after scanning it is what this
instrument measures publishers for.

**The invariant readings are computed on the payload, with `publish.py`'s own predicates.**
`observed_on_missing_document` (an Observation of a surface the graph has no Document for) and
`findings_evidence_unretained` (a Finding whose cited Observations are gone) are the two integrity
checks `scan.publish.project` counts. They are computed here from the payload, importing
`SYNTHETIC_PREFIXES` and `CONTROL_PREFIX` rather than restating them, because a second copy of
"which surfaces legitimately have no Document" is a second thing to be wrong.

**Why a Result's value is 1/0 and the verdict word is not.** A Seldon Result holds a number; a
verdict is categorical. So the value is `1.0` for `pass` and `0.0` for `fail`, and a leg whose
verdict is **neither** — `error` or `not_applicable` — is **refused** rather than filed as a 0
that would read as a fail. An encoding that can quietly lie about a verdict is worse than a stop.

    /opt/anaconda3/bin/python3 scripts/self_row_report.py --cycle self_2026-09-13 [--dry-run]

Writes `state/self_l0_<cycle>.json` and registers `self_l0_<leg>_<cycle>` for each leg.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "assessment" / "harness"))
sys.path.insert(0, str(REPO / "scripts"))

TASK = "cc_tasks/2026-09-13_self_row.md"

#: The verdicts a 1/0 Result may encode. Anything else is a stop — see the module docstring.
ENCODABLE = {"pass": 1.0, "fail": 0.0}


def payload_path(cycle: str) -> Path:
    return REPO / "state" / f"{cycle}.json"


def out_path(cycle: str) -> Path:
    """Where the site builder reads the row from. The name carries the SELF cycle, so a second
    self-scan is a second file rather than an overwrite of the first."""
    return REPO / "state" / f"self_l0_{cycle}.json"


def result_name(leg: str, cycle: str) -> str:
    """`self_l0_<leg>_<cycle>`, with the leg lowercased and non-alphanumerics collapsed.

    `A11-declared` and `G1-D` carry a hyphen and a case distinction that a Result name should
    not, and the mapping is done here rather than by each caller so one leg has one name.
    """
    slug = "".join(c if c.isalnum() else "_" for c in leg.lower())
    while "__" in slug:
        slug = slug.replace("__", "_")
    return f"self_l0_{slug.strip('_')}_{cycle}"


def invariant_readings(payload: dict) -> dict:
    """`observed_on_missing_document` and `findings_evidence_unretained`, on this payload.

    The same two integrity checks `scan.publish.project` keeps, with the same carve-outs, read
    off the payload instead of off the graph: a control fixture and a synthetic host surface
    legitimately have no `:Document`, and folding either in would leave the check permanently
    non-zero and therefore meaningless.
    """
    from kg import eventlog
    from scan.model import SYNTHETIC_PREFIXES
    from scan.publish import CONTROL_PREFIX, UNRETAINED_EVENT

    manifest = json.loads((REPO / "corpus" / "manifest.json")
                          .read_text(encoding="utf-8"))["entries"]
    missing_doc, control, synthetic, admitted = [], 0, 0, 0
    for o in payload["observations_detail"]:
        doc = str(o.get("target_doc_id") or "")
        if doc in manifest:
            admitted += 1
        elif doc.startswith(CONTROL_PREFIX):
            control += 1
        elif doc.startswith(SYNTHETIC_PREFIXES):
            synthetic += 1
        else:
            missing_doc.append(doc)

    annotated = {ev.get("finding_id") for ev in eventlog.replay()
                 if ev.get("event_type") == UNRETAINED_EVENT}
    findings = payload["findings_detail"] + payload.get("control_findings_detail", [])
    have = {o["obs_id"] for o in payload["observations_detail"]}
    unretained = [f["finding_id"] for f in findings
                  if f["finding_id"] in annotated
                  or not set(f.get("evidence") or []) <= have]
    return {"observed_on_missing_document": len(missing_doc),
            "observed_on_missing_document_doc_ids": sorted(set(missing_doc)),
            "findings_evidence_unretained": len(unretained),
            "findings_evidence_unretained_ids": sorted(unretained),
            "control_observations": control, "host_observations": synthetic,
            "admitted_document_observations": admitted,
            "note": ("The two integrity readings scan.publish.project keeps, computed on this "
                     "payload with that module's own predicates. A control fixture and a "
                     "synthetic host surface have no :Document by construction and are counted "
                     "apart, exactly as the projection counts them.")}


def legs(payload: dict, frame: dict) -> dict:
    """One entry per leg: the verdict, the reason, every URL read, and whose authority it was."""
    obs = {o["obs_id"]: o for o in payload["observations_detail"]}
    site_url = frame["site_url"]
    committed = REPO / "corpus" / "evidence"
    out = {}
    for f in payload["findings_detail"]:
        reads = []
        for oid in f.get("evidence") or []:
            o = obs.get(oid)
            if not o:
                reads.append({"obs_id": oid, "url": None,
                              "note": "cited Observation is not in this payload"})
                continue
            url = (o.get("request") or {}).get("url") or o.get("target_url")
            resp = o.get("response") or {}
            digest = resp.get("body_sha256")
            reads.append({
                "obs_id": oid, "url": url, "status": resp.get("status"),
                "collector": o.get("collector"),
                "error_class": o.get("error_class"),
                "body_sha256": digest,
                # Said rather than implied: the self cycle's bodies are STAGED, not promoted, so
                # a reader can see for each one whether the repository holds it (§ of the
                # RESULT). The published tree's own bodies are held under docs/ regardless.
                "body_in_committed_store": bool(
                    digest and (committed / "scan" / digest[:2] / digest).is_file()),
            })
        authorities = sorted({urllib.parse.urlsplit(r["url"]).netloc
                              for r in reads if r.get("url")})
        on_site = [r["url"] for r in reads
                   if r.get("url") and r["url"].startswith(site_url)]
        off_site = [r["url"] for r in reads
                    if r.get("url") and not r["url"].startswith(site_url)]
        out[f["leg"]] = {
            "verdict": f["verdict"], "reason": f["reason"],
            "rule_id": f["rule_id"], "rule_version": f["rule_version"],
            "finding_id": f["finding_id"], "target_doc_id": f["target_doc_id"],
            "urls_read": [r["url"] for r in reads if r.get("url")],
            "reads": reads,
            "authorities": authorities,
            # THE claim decision 2 asks each leg to make. A leg that read only paths under the
            # published site measured this publication; a leg that read the authority root
            # measured the authority, which on a project site is not this publication.
            "authority_is_this_publication": bool(on_site) and not off_site,
            "read_the_publication": sorted(set(on_site)),
            "read_the_authority_root_only": sorted(set(off_site)),
        }
    return out


#: The Script artifact the six Results are GENERATED_BY. Created on first use, the same way
#: every other registrar in this repo does it (`register_l0_report_results.ensure_script`):
#: `cycle_results.register` resolves both references before writing anything, so a missing one
#: refuses the whole batch — which is the right failure in the wrong place.
SCRIPT_ARTIFACT = "self_row_report"


def ensure_script(dry: bool) -> None:
    import subprocess
    from seldon_artifacts import live_artifact
    if dry or live_artifact(SCRIPT_ARTIFACT):
        return
    r = subprocess.run(
        ["seldon", "artifact", "create", "Script", "--actor", "cc",
         "-p", f"name={SCRIPT_ARTIFACT}",
         "-p", "path=scripts/self_row_report.py",
         "-p", f"description=Builds the self row from a self-scan payload: the six tier-0 "
               f"verdicts against the host that publishes this report, each with the URL it "
               f"actually read and whether the authority that answered is this publication. "
               f"Registers one Result per leg, 1.0 = pass and 0.0 = fail, and refuses a verdict "
               f"a 1/0 value cannot encode. Task {TASK}."],
        capture_output=True, text=True, cwd=REPO)
    if r.returncode:
        raise SystemExit(f"FATAL: cannot create Script artifact: {r.stderr.strip()[-400:]}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycle", required=True)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)

    import cycle_results
    from scan import load_params

    p = json.loads(payload_path(a.cycle).read_text(encoding="utf-8"))
    if p["cycle"] != a.cycle:
        raise SystemExit(f"FATAL: {payload_path(a.cycle).name} says cycle {p['cycle']!r}")
    frame = json.loads((REPO / "state" / f"{p['targets']}.json").read_text(encoding="utf-8"))
    tier0 = [l for l in (load_params().get("tier0") or {}).get("legs") or []]

    rows = legs(p, frame)
    absent = [l for l in tier0 if l not in rows]
    if absent:
        raise SystemExit(
            f"FATAL: the payload carries no Finding for {absent}; the row would print fewer than "
            f"the six tier-0 legs the instrument declares. Nothing written.")
    unencodable = {l: v["verdict"] for l, v in rows.items() if v["verdict"] not in ENCODABLE}
    if unencodable:
        raise SystemExit(
            f"FATAL: {unencodable} carry verdicts a 1/0 Result cannot encode without conflating "
            f"them with `fail`. The row is measured and the payload holds it; registering a 0 "
            f"here would file a claim nobody could read back. Nothing written.")

    inv = invariant_readings(p)
    doc = {
        "task": TASK, "cycle": a.cycle, "measured_cycle": a.cycle,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generated_by": "scripts/self_row_report.py",
        "params_hash": p["params_hash"], "base_params_hash": p.get("base_params_hash"),
        "harness_version": p.get("harness_version"),
        "control_verdict": p["control_verdict"], "control_reason": p["control_reason"],
        "site_url": frame["site_url"], "authority": frame["authority"],
        "authority_root": frame["authority_root"],
        "is_project_site": frame["is_project_site"],
        "authority_is_this_publication": frame["authority_is_this_publication"],
        "rfc_9309_note": frame["rfc_9309_note"],
        "user_agent": load_params()["manners"]["user_agent"],
        "requests_per_host": p["requests_per_host"],
        "requests_total": p["requests_total"],
        "tier0_legs": tier0,
        "legs": {l: rows[l] for l in tier0},
        "verdict_counts": {v: sum(1 for l in tier0 if rows[l]["verdict"] == v)
                           for v in ("pass", "fail", "not_applicable", "error")},
        "legs_measuring_this_publication": [l for l in tier0
                                           if rows[l]["authority_is_this_publication"]],
        "legs_measuring_the_authority": [l for l in tier0
                                        if not rows[l]["authority_is_this_publication"]],
        "invariants": inv,
        "note": ("The instrument's six host-level checks against the host that publishes it. A "
                 "fail is reported and left standing (decision 3): nothing under docs/ was "
                 "changed to improve a verdict after it was measured. Every leg carries the URL "
                 "it actually read, because on a project Pages site four of the six read the "
                 "AUTHORITY root and not this publication."),
    }

    result_rows = [
        (result_name(l, a.cycle), ENCODABLE[rows[l]["verdict"]],
         f"Self-scan verdict `{rows[l]['verdict']}` for {l} against "
         f"{', '.join(rows[l]['urls_read']) or '(no URL recorded)'} under "
         f"{rows[l]['rule_id']} {rows[l]['rule_version']}, cycle {a.cycle} "
         f"(params_hash {p['params_hash'][:12]}...), identified client "
         f"{doc['user_agent']}. 1.0 = pass, 0.0 = fail; the verdict word is authoritative and "
         f"is on this description and in state/{out_path(a.cycle).name}. Authority that "
         f"answered: {', '.join(rows[l]['authorities'])} — "
         f"{'THIS PUBLICATION' if rows[l]['authority_is_this_publication'] else 'NOT this publication: RFC 9309 binds robots.txt to an authority, and on a project Pages site the authority root belongs to a user-site repository this publication does not own'}. "
         f"Reason: {rows[l]['reason']} Task {TASK}.")
        for l in tier0]

    if a.dry_run:
        print(json.dumps({k: v for k, v in doc.items() if k != "legs"}, indent=1))
        for n, v, note in result_rows:
            print(f"  {n:44s} {v}  {note[:110]}…")
        return 0

    ensure_script(a.dry_run)
    out = out_path(a.cycle)
    out.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")
    res = cycle_results.register(
        result_rows, cycle=a.cycle, script="self_row_report",
        data=f"self_l0_{a.cycle}", data_path=str(out.relative_to(REPO)),
        data_description=(
            f"The self row: the instrument's six tier-0 verdicts against the host that publishes "
            f"it, cycle {a.cycle}. One entry per leg with the verdict, the rule and its version, "
            f"the Finding id, every URL read with its status, and whether the authority that "
            f"answered is this publication. Written by scripts/self_row_report.py from "
            f"state/{a.cycle}.json. Task {TASK}."))
    print(json.dumps({**res, "payload": str(out.relative_to(REPO)),
                      "verdict_counts": doc["verdict_counts"],
                      "legs_measuring_this_publication":
                          doc["legs_measuring_this_publication"],
                      "legs_measuring_the_authority": doc["legs_measuring_the_authority"],
                      "invariants": {k: inv[k] for k in
                                     ("observed_on_missing_document",
                                      "findings_evidence_unretained")}}, indent=1))
    return 1 if res["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
