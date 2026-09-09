#!/usr/bin/env python3
"""Per-leg rates, the agency × leg matrix, and the cycle's Results. **Zero model spend.**

Task `cc_tasks/2026-09-07_scan_run.md` §4. Three disciplines are wired in rather than
remembered, because each has already cost this project something when it was left to memory:

**1. Every denominator is stated, and unobservable hosts are never silently dropped.** A pass
rate over "the surfaces that answered" is a different measurement from a pass rate over "the
surfaces we targeted", and quoting the first while implying the second is how an accessibility
assessment ends up describing only the agencies that let it look. `pass_rate` is computed over
pass + fail on **observable, admitted** surfaces; `applicable_n`, `error_n` and
`surfaces_targeted` ride alongside on every leg, and the three refusing hosts have their own
Results.

**2. Wilson, not Wald.** `assessment/harness/rollup.wilson_interval` — the repo's own, reused
rather than re-derived. At these n (8-18 per leg) a normal-approximation interval on a
proportion near 0 or 1 is not merely imprecise, it runs off the end of the scale.

**3. No composite and no ranking.** The task forbids both and the reason is worth keeping on
the face of the code: a single number over legs that measure different constructs, weighted by
nothing in particular, would be read as a score of the agency, and this instrument has not
earned that reading. The matrix is published; the league table is not.

    /opt/anaconda3/bin/python3 scripts/scan_report.py [--dry-run]
"""
from __future__ import annotations

import argparse
import collections
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "assessment"))
sys.path.insert(0, str(REPO / "assessment" / "harness"))
sys.path.insert(0, str(REPO / "scripts"))

import cycle_results                                              # noqa: E402
from harness.rollup import wilson_interval                        # noqa: E402
from scan import errors as scan_errors                            # noqa: E402
from scan import load_params                                      # noqa: E402
from scan.rules import CANDIDATE_LEGS, CURRENT                    # noqa: E402

#: Which cycle this run REPORTS is read from `params.cycle.name`, never typed here. The cycle
#: name already drives the payload path, the Result suffix and `refuse_clobber`
#: (`assessment/harness/scan/run.py`); a second copy of it in the reporter is a second
#: definition of "which cycle", and the stale one is the one that would silently report last
#: week's numbers under this week's heading. `--cycle` overrides it for re-reporting a cycle
#: whose params have since moved on.
TASK = "cc_tasks/2026-09-07_scan_run_2.md"
VERDICTS = ("pass", "fail", "not_applicable", "error")


def cycle_name(override: str | None = None) -> str:
    return override or load_params()["cycle"]["name"]


def payload_path(cycle: str) -> Path:
    return REPO / "state" / f"{cycle}.json"


def matrix_path(cycle: str) -> Path:
    """`scan_matrix_<cycle>` — §4's DataFile name, derived from the same single source."""
    return REPO / "state" / f"scan_matrix_{cycle_results.cycle_suffix(cycle)}.json"


def load(cycle: str) -> dict:
    return json.loads(payload_path(cycle).read_text(encoding="utf-8"))


def tier_of(params: dict) -> dict:
    """`doc_id -> tier`, joined from the targets DataFile.

    The cycle payload's matrix rows do not carry the tier — the runner never needed it — and
    re-running a measured cycle to add a field would be re-measuring to gain bookkeeping. The
    targets file is the authority for which tier a surface belongs to and is keyed by the same
    `doc_id`, so the join is exact.
    """
    src = REPO / "state" / f"{params['cycle']['targets']}.json"
    if not src.is_file():
        return {}
    return {r["doc_id"]: r.get("tier", "A")
            for r in json.loads(src.read_text(encoding="utf-8"))["rows"] if r.get("doc_id")}


def blind_counts(payload: dict) -> dict:
    """Per leg, how much of the evidence the rules could not see.

    Read from the Finding FIELDS (`blind_links`, `blind_pointers`), which
    `cc_tasks/2026-09-08_a8_v4_blind_pointer_and_fixture_table.md` decision 3 added precisely so
    this number does not have to be parsed out of a reason string.
    """
    out: dict = {}
    for f in payload.get("findings_detail") or []:
        for key in ("blind_links", "blind_pointers"):
            if f.get(key):
                out.setdefault(f["leg"], {}).setdefault(key, 0)
                out[f["leg"]][key] += int(f[key])
    return out


def control_fired(payload: dict) -> dict:
    """Per leg: how many control fixtures its rule returned the PRE-REGISTERED verdict on.

    Read out of the E5 control Observations, which record `expected` and `verdicts` per
    fixture — the same records E5 judges the cycle from. Derived rather than re-run: a
    reporter that re-ran the fixtures would be reporting a different set of controls from the
    ones the cycle's validity actually rests on.
    """
    fired: collections.Counter = collections.Counter()
    fixtures = 0
    for o in payload.get("observations_detail", []):
        if o.get("leg") != "E5" or o.get("collector") != "control_fixture":
            continue
        parsed = o.get("parsed") or {}
        verdicts, expected = parsed.get("verdicts") or {}, parsed.get("expected")
        fixtures += 1
        for leg, got in verdicts.items():
            want = (expected.get(leg, expected.get("default"))
                    if isinstance(expected, dict) else expected)
            if got == want:
                fired[leg] += 1
    return {"fired": fired, "fixtures": fixtures}


def per_leg(payload: dict, tiers: dict | None = None, tier: str = "A") -> dict:
    """Counts and a Wilson interval per leg, over one TIER's product surfaces.

    Tier A and Tier C never share a denominator (DD-059): a reference host is judged on tier-0
    legs only and is not a statistical product, so pooling them would put a catalog in a rate
    about agencies. `well_known` rows are excluded here as always — A12 judges a host and has
    its own block.
    """
    tiers = tiers or {}
    rows = [r for r in payload["matrix"]
            if r["surface_kind"] != "well_known"
            and tiers.get(r["doc_id"], "A") == tier]
    cf = control_fired(payload)
    out = {}
    for leg in sorted(l for l in CURRENT if l not in CANDIDATE_LEGS and l != "E5"):
        v = [r["verdicts"][leg] for r in rows if leg in r["verdicts"]]
        if not v:
            continue
        c = collections.Counter(v)
        k, n = c["pass"], c["pass"] + c["fail"]
        lo, hi = wilson_interval(k, n)
        out[leg] = {"pass": c["pass"], "fail": c["fail"],
                    "not_applicable": c["not_applicable"], "error": c["error"],
                    "applicable_n": n, "surfaces_targeted": len(v),
                    "pass_rate": round(k / n, 4) if n else None,
                    "ci95_low": lo, "ci95_high": hi,
                    # NOT named `control_fired`: that is a REGISTERED Result owned by
                    # `scripts/register_figure_results.py` with a different and narrower
                    # definition (1 iff passes_all->pass AND fails_all->fail, the
                    # ceiling-and-floor check F1 marks). This is the four-fixture count
                    # against the pre-registered table, kept in the matrix because a reader
                    # asking "was this leg's rule exercised" wants it — under its own name, so
                    # the two can never be mistaken for one number.
                    "control_expected_verdicts_met": cf["fired"].get(leg, 0),
                    "control_fixtures": cf["fixtures"],
                    "denominator": ("pass + fail on admitted surfaces that were observable; "
                                    "`error` is excluded because the collector could not "
                                    "observe, which is ours and not the product's")}
    return out


def a12(payload: dict) -> dict:
    rows = [r for r in payload["matrix"] if r["surface_kind"] == "well_known"]
    c = collections.Counter(r["verdicts"].get("A12") for r in rows)
    return {"by_verdict": {v: c[v] for v in VERDICTS},
            "hosts": len(rows),
            "by_host": {r["agency"]: r["verdicts"].get("A12") for r in sorted(
                rows, key=lambda x: x["agency"])}}


def matrix(payload: dict, cycle: str, tiers: dict | None = None, tier: str = "A") -> dict:
    """Agencies × legs. One row per agency per surface kind, so a reader can see that BEA's
    two flagships disagree rather than seeing an agency-level average that hides it."""
    # E5 judges the CYCLE, not a surface, so it has no column in a surfaces × legs matrix.
    # Leaving it in printed an empty column of "?" across every row, which reads as missing
    # data rather than as a leg with a different subject.
    # The legs this payload actually holds verdicts for. `CURRENT` minus the candidates and
    # E5 is the answer for a measured cycle; a RE-JUDGED cycle may hold fewer, because a leg
    # whose CURRENT rule consumes an observation the source cycle never collected is not
    # judged at all (`scan/rederive.py::rejudge`). Listing it here would put a column in the
    # matrix that every figure then looks up a Result for and does not find — "not measured is
    # a reason, not a zero" (DD-055), and a KeyError is not a reason either.
    reportable = [l for l in CURRENT if l not in CANDIDATE_LEGS and l != "E5"]
    judged = payload.get("legs_judged")
    # Intersected, never substituted. `legs_judged` is what the re-judgement DID judge and it
    # includes A12 — a candidate, which enters no fraction (DD-054) and has no `pass_rate`
    # Result — and would put a column on the matrix that F1 then looks up a rate for and does
    # not find. The reportable set is still the framework's; a re-judged cycle can only narrow
    # it.
    legs = [l for l in reportable if l in judged] if judged else reportable
    tiers = tiers or {}
    rows = []
    for r in sorted(payload["matrix"], key=lambda r: (r["agency"], r["surface_kind"],
                                                      r["doc_id"])):
        if tiers.get(r["doc_id"], "A") != tier:
            continue
        rows.append({"agency": r["agency"], "surface_kind": r["surface_kind"],
                     "doc_id": r["doc_id"], "url": r["url"], "admitted": r["admitted"],
                     "verdicts": r["verdicts"]})
    # Every agency figure on this matrix counts THIS TIER'S rows, not the payload's.
    # `rows` was filtered above and these three were not, so a Tier A matrix listed 19
    # agencies over 16 agencies' worth of rows — the three Tier C reference hosts, inside a
    # count that DD-059 says they are never inside. It surfaced as F2 "omitting" GSA: the
    # figure drew the 16 agencies it had rows for and the roster it was checked against was
    # the wrong one. A reference host cannot reach a Tier A figure because it is not in the
    # file the figure is drawn from, and that is only true if the file's own roster is the
    # tier's as well.
    mine = [r for r in payload["matrix"] if tiers.get(r["doc_id"], "A") == tier]
    unobservable = sorted({r["agency"] for r in mine
                           if r["surface_kind"] != "well_known"
                           and r["verdicts"] and all(v == "error"
                                                     for v in r["verdicts"].values())})
    with_surfaces = {r["agency"] for r in mine if r["surface_kind"] != "well_known"}
    all_agencies = {r["agency"] for r in mine}
    return {"task": TASK, "cycle": cycle, "tier": tier,
            "params_hash": payload["params_hash"],
            "agencies_without_surfaces": sorted(all_agencies - with_surfaces),
            "legs": legs, "candidate_legs": sorted(CANDIDATE_LEGS),
            "agencies": sorted(all_agencies),
            "agencies_wholly_unobservable": unobservable,
            "note": ("No composite and no ranking. These legs measure different constructs; a "
                     "single number over them, weighted by nothing in particular, would be "
                     "read as a score of the agency, and this instrument has not earned that "
                     "reading."),
            "rows": rows}


def results(payload: dict, legs: dict, a12v: dict, mx: dict, cycle: str,
            rederived: int | None = None, legs_c: dict | None = None,
            blinds: dict | None = None) -> list:
    """(base name, value, note). Bases are BARE — `cycle_results.name_for` is the single point
    where a cycle is stamped onto a name, so no emitter here can forget one (DD-041's
    amendment, DD-056)."""
    ph = payload["params_hash"][:12]
    #: A RE-JUDGED cycle made no measurement: it judged another cycle's stored Observations
    #: under today's rules, fetched nothing and created no Observation
    #: (`scan/rederive.py::rejudge`). Its per-leg counts and rates are real and are the whole
    #: point; the Results that describe the MEASUREMENT — observations captured, requests
    #: issued per host, error classes recorded, control Findings published — are the source
    #: cycle's and are not re-registered under this cycle's name. Registering them at 0 would
    #: publish "this cycle issued 0 requests to www.census.gov" as a fact about a scan, which
    #: reads as a measurement of a host that was never asked.
    rejudged = payload.get("cycle_kind") == "rejudged"
    tag = (f"Cycle {cycle}, params_hash {ph}…. RE-JUDGED from the stored Observations of "
           f"{payload.get('derived_from')} under the rules current at "
           f"{payload.get('task')}; nothing was re-fetched."
           if rejudged else f"Cycle {cycle}, params_hash {ph}….")
    out = []
    for leg, s in legs.items():
        key = leg.replace("-", "_").lower()
        base = (f"{tag} Leg {leg} judged by {CURRENT[leg]} over {s['surfaces_targeted']} "
                f"admitted product surfaces.")
        out += [
            (f"scan_{key}_pass", s["pass"], f"{base} Findings of `pass`."),
            (f"scan_{key}_fail", s["fail"], f"{base} Findings of `fail` — the collector "
                                            f"observed and the property was not there."),
            (f"scan_{key}_not_applicable", s["not_applicable"],
             f"{base} Findings of `not_applicable` — there was nothing of that kind to check."),
            (f"scan_{key}_error", s["error"],
             f"{base} Findings of `error` — the COLLECTOR could not observe; never a product "
             f"failure."),
            (f"scan_{key}_applicable_n", s["applicable_n"],
             f"{base} Denominator for the pass rate: {s['denominator']}."),
        ]
        # `scan_<leg>_wilson_lo/_hi` and `scan_<leg>_control_fired` are NOT registered here.
        # `scripts/register_figure_results.py` owns those three families — it computes the
        # interval through `scan/stats.py` and cross-checks it against the matrix, and it
        # derives `control_fired` from the control Findings — and two scripts registering one
        # metric name under two definitions is the defect `scripts/framework_writeback.py`
        # exists to have fixed one layer up. This reporter owns the counts; that one owns the
        # figure inputs.
        if s["applicable_n"]:
            out.append((f"scan_{key}_pass_rate", s["pass_rate"],
                        f"{base} {s['pass']}/{s['applicable_n']} = {s['pass_rate']}, Wilson "
                        f"95% [{s['ci95_low']}, {s['ci95_high']}]. Denominator: "
                        f"{s['denominator']}. NOT a score of any agency and not comparable "
                        f"across legs — these legs measure different constructs."))
    for v in ("pass", "fail", "not_applicable", "error"):
        out.append((f"scan_a12_{v}", a12v["by_verdict"][v],
                    f"{tag} **CANDIDATE indicator A12** (DD-054): reported, adopted by "
                    f"nobody, and counted in no fraction. Hosts at `{v}` of {a12v['hosts']}: "
                    f"{sorted(h for h, x in a12v['by_host'].items() if x == v)}."))
    # A12 PER HOST (§4). A12's proposition is binary — the declared layer and the enforced
    # layer cohere, or they do not — so `pass`/`fail` register as 1/0 against a named claim.
    # `error` and `not_applicable` register NOTHING: DD-055 §5 is that "not measured" is a
    # reason and not a silence, and it is emphatically not a zero. A host that could not be
    # observed and a host measured to be incoherent are the same number under any encoding
    # that forces all four verdicts onto one scale, and this instrument's whole quarrel with
    # its first smoke run was exactly that conflation.
    coherent = {"pass": 1, "fail": 0}
    for agency in sorted(a12v["by_host"]):
        v = a12v["by_host"][agency]
        if v not in coherent:
            continue
        out.append((f"scan_a12_declared_enforced_cohere_{agency.replace('-', '_').lower()}",
                    coherent[v],
                    f"{tag} **CANDIDATE indicator A12** (DD-054), host surface for {agency}: "
                    f"1 when this host's robots.txt declaration and its enforced behaviour "
                    f"toward an identified, robots-compliant client AGREE, 0 when they do "
                    f"not. Verdict `{v}`. Counted in no framework fraction; the framework has "
                    f"not adopted A12 and measuring something is not agreeing to measure it."))
    out.append(("scan_a12_hosts_not_measured", a12v["by_verdict"]["error"]
                + a12v["by_verdict"]["not_applicable"],
                f"{tag} Hosts on which A12 registered NO per-host value, of {a12v['hosts']}: "
                f"{a12v['by_verdict']['error']} `error` (the pair could not be observed — "
                f"ours, not the host's) and {a12v['by_verdict']['not_applicable']} "
                f"`not_applicable` (robots.txt disallows this client, which is A4's "
                f"measurement; a host obeyed is not a host in conflict with itself). Not "
                f"measured is a reason, not a zero (DD-055)."))
    # ---- Tier C, in its own namespace and no shared denominator (DD-059) ----
    for leg, s_ in (legs_c or {}).items():
        key = leg.replace("-", "_").lower()
        base = (f"{tag} **TIER C reference host**, leg {leg} judged by {CURRENT[leg]} over "
                f"{s_['surfaces_targeted']} reference surfaces. Tier-0 legs only; a reference "
                f"host is not a statistical agency and enters NO Tier A denominator "
                f"(DD-059).")
        out += [
            (f"scan_tierc_{key}_pass", s_["pass"], f"{base} Findings of `pass`."),
            (f"scan_tierc_{key}_fail", s_["fail"], f"{base} Findings of `fail`."),
            (f"scan_tierc_{key}_error", s_["error"],
             f"{base} Findings of `error` — the COLLECTOR could not observe."),
            (f"scan_tierc_{key}_applicable_n", s_["applicable_n"],
             f"{base} Denominator: {s_['denominator']}."),
        ]
    # ---- how much of the evidence the rules could not see, per leg ----
    for leg, counts in sorted((blinds or {}).items()):
        key = leg.replace("-", "_").lower()
        for field, value in sorted(counts.items()):
            out.append((f"scan_{key}_{field}", value,
                        f"{tag} Probes on leg {leg} that were UNOBSERVED and therefore excluded "
                        f"from the verdict, summed over this cycle's Findings. Read from the "
                        f"Finding FIELD `{field}`, not parsed from a reason string "
                        f"(cc_tasks/2026-09-08_a8_v4_blind_pointer_and_fixture_table.md "
                        f"decision 3). A blind probe is not a product failure: it is evidence "
                        f"nobody saw (DD-052 §6)."))
    vc = payload["verdict_counts"]
    out += [
        ("scan_surfaces", payload["surfaces"], f"{tag} Surfaces scanned, of the 41 on "
                                               f"`scan_targets_2026-09`."),
        ("scan_findings", payload["findings"], f"{tag} Findings produced: {vc}."),
    ]
    if not rejudged:
        out += [
        ("scan_observations", payload["observations"], f"{tag} Observations captured, each "
                                                       f"with its whole response body stored "
                                                       f"content-addressed."),
        # DD-041: a rerun never overwrites a registered measurement. `scan_control_findings`
        # is already bound to the 2026-09-06 control cycle at 31, so this cycle's 33 gets the
        # date. §4 names the cycle-level Results bare, and bare names are not cycle-unique —
        # every one of them collides on the next cycle. Recorded as a premise this task got
        # wrong rather than papered over by renaming the earlier one.
        ("scan_control_findings", payload["control_findings"],
         f"{tag} Control Findings, including RULE-E5-v2's own verdict on the cycle and A12 on "
         f"every fixture. The gate ran before any real host was touched, and E5-v2 asserted "
         f"that ordering against the first surface timestamp."),
        ]
    out += [
        ("scan_agencies_unobservable", len(mx["agencies_wholly_unobservable"]),
         f"{tag} Agencies on which EVERY leg of EVERY ADMITTED surface returned `error`: "
         f"{mx['agencies_wholly_unobservable']}. Read this WITH "
         f"`scan_agencies_with_no_admitted_surface`: it is not the count of agencies that "
         f"refused us. An agency that refused the scanner early enough never got an admitted "
         f"surface, so it cannot appear in a product-surface metric at all."),
        ("scan_agencies_with_no_admitted_surface", len(mx["agencies_without_surfaces"]),
         f"{tag} Agencies contributing NO admitted product surface, and therefore absent from "
         f"every per-leg denominator on this page: {mx['agencies_without_surfaces']}. Three "
         f"of them refuse an identified robots-compliant client outright and one serves a "
         f"data listing that is unreadable without JavaScript, so their own listings could "
         f"not be read and no flagship could be selected. **A refusal upstream removes an "
         f"agency from the instrument's denominators entirely** — one layer earlier than the "
         f"guard that keeps unobservable surfaces in them, and the more consequential of the "
         f"two for an accessibility assessment."),
        ("scan_hosts_refusing_or_unreachable", sum(
            1 for r in payload["matrix"] if r["surface_kind"] == "well_known"
            and r["verdicts"].get("A12") in ("fail", "error")),
         f"{tag} Hosts whose declared and enforced layers disagree, or that could not be "
         f"reached at all, of 14 — measured by the CANDIDATE indicator A12 and therefore "
         f"counted in no framework fraction (DD-054). This is the only figure in the cycle "
         f"that sees the refusing agencies at all."),
        ("scan_surfaces_unobservable", sum(
            1 for r in payload["matrix"] if r["surface_kind"] != "well_known"
            and r["verdicts"] and all(v == "error" for v in r["verdicts"].values())),
         f"{tag} Admitted surfaces on which every leg returned `error`."),
    ]
    if rederived is not None:
        out.append(("scan_rederived_findings", rederived,
                    f"{tag} Findings re-derived BYTE-IDENTICALLY from this cycle's stored "
                    f"Observations alone, with every Finding deleted first and nothing "
                    f"fetched. This is skeleton §6b.5's claim — that thresholds can change "
                    f"and history be re-scored without re-measurement — tested rather than "
                    f"asserted, and it is a real test only because a `finding_id` is DERIVED "
                    f"(sha256 of rule_id | rule_version | target | params_hash | sorted "
                    f"evidence). An id from a counter or a clock would make the comparison "
                    f"vacuous."))
    if rejudged:
        # Everything below describes what the SCANNER did — requests per host, error classes
        # recorded on Observations. A re-judgement did none of it, and the source cycle's
        # numbers are registered under the source cycle's names. Stopping here is DD-055's
        # rule applied to a whole family: not measured is a reason, not a zero.
        return out
    # What this scanner ASKED of each host, one Result per host (§4). The manners claim
    # (RFC 9309, identified UA, 1 req/s) is auditable only against this number, and cycle 2's
    # shared `link_probe` is asserted against cycle 1's here rather than assumed: A1 and A3
    # each HEADed the same links in cycle 1, 559 duplicate requests over 559 distinct triples.
    for host, n in sorted((payload.get("requests_per_host") or {}).items()):
        out.append((f"scan_requests_{host.replace('.', '_').replace('-', '_')}", n,
                    f"{tag} HTTP requests issued to {host}, counted at the socket "
                    f"(`manners.Fetcher.requests`) and including robots.txt fetches, 429/503 "
                    f"retries and HEAD-refused GET fallbacks. Not the Observation count: a "
                    f"link probe issues one HEAD per link inside ONE Observation. Rate-limited "
                    f"to 1 req/s per host, identified UA, robots obeyed."))
    out.append(("scan_requests_total", payload.get("requests_total", 0),
                f"{tag} HTTP requests issued to all {len(payload.get('requests_per_host') or {})} "
                f"federal hosts in this cycle. Control fixtures are excluded: the fixture "
                f"server is us."))
    # Every class in the closed set, zeros included (`scan.errors.ERROR_CLASSES`). A class that
    # stopped appearing is as informative as one that appeared, and `unknown` is the only
    # remainder the map has — a cycle that produced any is a cycle whose map is missing a rule.
    ecc = payload.get("error_class_counts") or {}
    for cls in scan_errors.ERROR_CLASSES:
        if cls is None:
            continue
        out.append((f"scan_error_class_{cls}", ecc.get(cls, 0),
                    f"{tag} Observations recorded with `error_class: {cls}` — "
                    f"{scan_errors.CLASSES[cls]['note']}. "
                    f"{'Blind' if scan_errors.CLASSES[cls]['blind'] else 'Not blind'}: a rule "
                    f"reads this class as "
                    f"{'`error` (the collector could not observe)' if scan_errors.CLASSES[cls]['blind'] else 'a real observation'}."))
    out.append(("scan_error_class_observed", sum(
        1 for o in payload.get("observations_detail", []) if o.get("error_class") is None),
        f"{tag} Observations with NO error class — the collector observed the surface."))
    return out


def rederived_count(payload: dict, params: dict) -> int:
    """How many Findings re-derive byte-identically from this cycle's stored Observations.

    Runs `rederive.rederive` in-process rather than shelling out, and RAISES on a mismatch:
    §3 makes re-derivation a gate, and a reporter that registered "437 of 437 except the ones
    that differed" would turn a gate into a statistic.
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "scan_rederive_report", REPO / "assessment" / "harness" / "scan" / "rederive.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    out = mod.rederive(payload, params)
    if not out["identical"]:
        raise SystemExit(f"REFUSING to report: this cycle does not re-derive: "
                         f"{json.dumps(out, indent=1)}")
    return out["rederived"]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--cycle", default=None,
                    help="report a cycle other than params.cycle.name (for re-reporting a "
                         "cycle whose parameters have since moved on)")
    a = ap.parse_args(argv)
    cycle = cycle_name(a.cycle)
    payload = load(cycle)
    tiers = tier_of(load_params())
    legs, a12v = per_leg(payload, tiers, "A"), a12(payload)
    legs_c = per_leg(payload, tiers, "C")
    blinds = blind_counts(payload)
    mx = matrix(payload, cycle, tiers, "A")
    mx_c = matrix(payload, cycle, tiers, "C")
    rederived = rederived_count(payload, load_params()) if not a.cycle else None
    data = [(cycle_results.name_for(base, cycle), v, note)
            for base, v, note in results(payload, legs, a12v, mx, cycle, rederived,
                                         legs_c, blinds)]
    matrix_file = matrix_path(cycle)
    if a.dry_run:
        for n, v, note in data:
            print(f"{n}\t{v}\t{note[:70]}")
        print(len(data), "Results ->", matrix_file.relative_to(REPO))
        return 0
    tierc_file = REPO / "state" / f"scan_matrix_tierc_{cycle_results.cycle_suffix(cycle)}.json"
    tierc_file.write_text(json.dumps({**mx_c, "per_leg": legs_c,
                                      "note": ("Tier C reference hosts, tier-0 legs only. In "
                                               "no Tier A denominator and on no agencies x "
                                               "legs matrix (DD-059).")},
                                     indent=1) + "\n", encoding="utf-8")
    matrix_file.write_text(json.dumps({**mx, "per_leg": legs, "a12": a12v,
                                       "requests_per_host": payload.get("requests_per_host"),
                                       "error_class_counts": payload.get("error_class_counts")},
                                      indent=1) + "\n", encoding="utf-8")
    # Through the shared registrar, which refuses a per-cycle name that does not carry its
    # cycle BEFORE anything is registered (DD-056, `cc_tasks/2026-09-07_scan_harness_v3.md`
    # §1.6). `scan_control_findings` was refused mid-run on 2026-09-07 for exactly this, after
    # the measurement; the check now happens before the first write.
    data_name = f"scan_matrix_{cycle_results.cycle_suffix(cycle)}"
    out = cycle_results.register(
        [(n, v, f"{note} ({TASK})") for n, v, note in data],
        cycle=cycle, script="scan_report", data=data_name,
        data_path=str(matrix_file.relative_to(REPO)),
        data_description=(
            f"The {cycle} cycle's agency x leg matrix: one row per admitted surface with its "
            f"verdict on every leg, plus the per-leg counts, Wilson intervals and "
            f"denominators, A12 by host, this cycle's requests per host and its error-class "
            f"counts. Written by scripts/scan_report.py from state/{cycle}.json under "
            f"params_hash {payload['params_hash'][:12]}...; the denominator for every rate is "
            f"stated on the row. No composite and no ranking. Task {TASK}."))
    print(json.dumps({**out, "matrix": str(matrix_file.relative_to(REPO))}, indent=1))
    return 1 if out["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
