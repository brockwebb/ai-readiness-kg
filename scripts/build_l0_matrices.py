#!/usr/bin/env python3
"""The three L0 matrices, as data. **Zero model spend, no network.**

Task `cc_tasks/2026-09-09_report_draft.md` §1, under `docs/design/2026-09-08_l0_product_shape.md`.
The report is one matrix; these are the files it is rendered from, emitted as CSV and JSON
beside it so a reader who wants the numbers does not have to parse prose to get them.

**Every cell carries the Finding identity it came from.** That is what makes §3's gate possible
at all: a CSV row is checkable against the graph only if it says which Findings it summarises,
and a matrix whose cells cannot be walked back to a `finding_id` is a picture, not a
measurement.

**Which surface a host-level cell is measured on is a decision, and it is on the face of every
row.** The five non-A12 tier-0 legs are judged per SURFACE, not per host: a flagship page can
be disallowed by a `robots.txt` that permits the home. `surface_disagreements` counts how often
that happens in the cycle being reported, and the count is written into every matrix header
rather than into a docstring, because a number in a comment is a number nobody re-derives. So
the host-level matrix reads the `home:` surface (the host's own page, present for every body)
and A12 from the `host:` well-known surface, and every row names both. Pooling them into one
"host" cell would have had to pick a winner for the disagreements and would not have said so.

    /opt/anaconda3/bin/python3 scripts/build_l0_matrices.py [--dry-run] [--cycle CYCLE]
"""
from __future__ import annotations

import argparse
import csv
import functools
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "assessment"))
sys.path.insert(0, str(REPO / "assessment" / "harness"))
sys.path.insert(0, str(REPO / "scripts"))

import cycle_results                                                # noqa: E402
from harness.rollup import wilson_interval                          # noqa: E402
from scan import load_params                                        # noqa: E402

TASK = "cc_tasks/2026-09-09_report_draft.md"
SCRIPT_ARTIFACT = "build_l0_matrices"
OUT_DIR = REPO / "docs" / "reports"

#: The product-level legs, declared by the task. They are the framework's reportable set minus
#: the tier-0 legs: what a PRODUCT offers a machine, as against what a HOST declares.
PRODUCT_LEGS = ["A1", "A2", "A3", "A6", "A8", "A9", "B3", "D1", "D4", "F4"]

#: The surface kind each matrix reads. Named here rather than inline because it is the single
#: most consequential choice in this file (see the module docstring).
HOST_SURFACE = "home"
CANDIDATE_SURFACE = "well_known"
PRODUCT_SURFACE = "flagship"


def payload(cycle: str) -> dict:
    return json.loads((REPO / "state" / f"{cycle}.json").read_text(encoding="utf-8"))


@functools.lru_cache(maxsize=4)
def _cached_payload(cycle: str) -> dict:
    """Read-only. `evidence_payload` is asked once per matrix and the measured payloads are
    12 MB; nothing mutates what it returns."""
    return payload(cycle)


def evidence_payload(p: dict) -> dict:
    """The payload whose COLLECTION the cycle rests on: itself, or the measured cycle a
    re-judgement derives from.

    A re-judgement issues no requests and records no Observation — `requests_total: 0`,
    `requests_per_host: {}`, `observations_detail: []`, asserted per payload — because it
    re-judges Observations that already exist. Two things in these matrices are counted off the
    OBSERVATIONS rather than off the verdicts, and both read as an empty measurement when the
    payload is a re-judgement:

    * the appendix table "requests issued, per netloc", which comes out as a total of zero;
    * the matrix's last column, how many of a surface's probes the host answered with a refusal,
      which comes out as `0 of 0` for every body — including the three that refuse everything.

    Neither is what the cycle did; both are what re-judging it did. The evidence is the measured
    cycle's, and the payload names it.
    """
    src = p.get("derived_from") if p.get("cycle_kind") == "rejudged" else None
    return _cached_payload(src) if src else p


def targets(params: dict) -> dict:
    return json.loads(
        (REPO / "state" / f"{params['cycle']['targets']}.json").read_text(encoding="utf-8"))


def tier_of(params: dict) -> dict:
    return {r["doc_id"]: r.get("tier", "A") for r in targets(params)["rows"] if r.get("doc_id")}


def findings_index(p: dict) -> dict:
    """`(target_doc_id, leg) -> finding_id`. One Finding per surface per leg is the harness's
    own invariant (`cc_tasks/2026-09-08_scan_run_3b.md` §3 checks it), so a collision here
    would be that invariant breaking and is raised rather than resolved."""
    idx: dict = {}
    for f in p["findings_detail"]:
        key = (f["target_doc_id"], f["leg"])
        if key in idx and idx[key] != f["finding_id"]:
            raise SystemExit(f"FATAL: two Finding identities for {key}: "
                             f"{idx[key]} and {f['finding_id']}")
        idx[key] = f["finding_id"]
    return idx


def refusals(p: dict) -> dict:
    """`doc_id -> (refused, probed)`. How many of a surface's probes the host answered with a
    refusal status to the identified client, over how many it answered at all.

    Reported as a COUNT and not as a category. A yes/no column would need a cut-point, and a
    cut-point invented to make a column tidy is a threshold nobody registered: cycle 3's
    distribution is three surfaces near total (33/35, 32/33, 32/33) and two with a handful
    (4/60, 1/65), and the gap is obvious in the numbers without anyone drawing a line in them.
    """
    out: dict = {}
    for o in p["observations_detail"]:
        d = o["target_doc_id"]
        r, n = out.get(d, (0, 0))
        out[d] = (r + (1 if o.get("error_class") == "refused" else 0), n + 1)
    return out


def rows_for(p: dict, tiers: dict, tier: str, kind: str) -> list:
    return sorted((r for r in p["matrix"]
                   if tiers.get(r["doc_id"], "A") == tier and r["surface_kind"] == kind),
                  key=lambda r: (r["agency"], r["doc_id"]))


def host_matrix(p: dict, tiers: dict, tier: str, legs: list) -> list:
    """One row per body: the five surface-judged tier-0 legs from its `home:` surface and A12
    from its `host:` well-known surface, each cell naming the Finding it came from.

    The VERDICTS are this payload's — a re-judgement's whole point is that they are its own. The
    refusal column is not a verdict: it counts what the host answered, so it is counted off the
    evidence, which for a re-judgement is the measured cycle it derives from."""
    idx, ref = findings_index(p), refusals(evidence_payload(p))
    a12_by_agency = {r["agency"]: r for r in rows_for(p, tiers, tier, CANDIDATE_SURFACE)}
    out = []
    for r in rows_for(p, tiers, tier, HOST_SURFACE):
        wk = a12_by_agency.get(r["agency"])
        cells, fids = {}, {}
        for leg in legs:
            src = wk if leg == "A12" else r
            if src is None:
                cells[leg], fids[leg] = "not measured", None
                continue
            cells[leg] = src["verdicts"].get(leg, "not measured")
            fids[leg] = idx.get((src["doc_id"], leg))
        refused, probed = ref.get(r["doc_id"], (0, 0))
        out.append({
            "agency": r["agency"], "tier": tier,
            "host_surface": r["doc_id"], "host_url": r["url"],
            "candidate_surface": wk["doc_id"] if wk else None,
            "verdicts": cells, "finding_ids": fids,
            "refused_identified_client": refused, "probes_on_host_surface": probed,
        })
    return out


def product_matrix(p: dict, tiers: dict, legs: list) -> list:
    """Declared flagship surfaces only, product legs.

    An agency with no declared flagship gets a row marked `not declared` and no verdicts. It is
    neither omitted nor scored: omitting it would shrink the frame silently, and a `fail` cell
    would say the product lacks a property when what is missing is the declaration of which
    product to look at. Seven agencies are in that state and
    `docs/design/fss_flagship_shortlist.md` is where it gets resolved.
    """
    idx, out = findings_index(p), []
    have = {r["agency"] for r in rows_for(p, tiers, "A", PRODUCT_SURFACE)}
    for r in rows_for(p, tiers, "A", PRODUCT_SURFACE):
        out.append({"agency": r["agency"], "surface": r["doc_id"], "url": r["url"],
                    "declared": True,
                    "verdicts": {l: r["verdicts"].get(l, "not measured") for l in legs},
                    "finding_ids": {l: idx.get((r["doc_id"], l)) for l in legs}})
    for r in rows_for(p, tiers, "A", HOST_SURFACE):
        if r["agency"] in have:
            continue
        out.append({"agency": r["agency"], "surface": None, "url": None, "declared": False,
                    "verdicts": {l: "not declared" for l in legs},
                    "finding_ids": {l: None for l in legs}})
    return sorted(out, key=lambda r: (not r["declared"], r["agency"], r["surface"] or ""))


def surface_disagreements(p: dict, tiers: dict, legs: list) -> dict:
    """Cells where a body's HOME surface and one of its FLAGSHIP surfaces answer the same
    host-level check differently.

    This is the number that justifies naming a surface on every row. A `robots.txt` that
    permits the front door can disallow a particular product, so these checks are judged per
    surface and a single combined "host" cell would have to pick a winner. Counted rather than
    asserted: the report quotes it, and a count typed into prose is a count nobody can check.
    """
    five = [l for l in legs if l != "A12"]
    by: dict = {}
    for r in p["matrix"]:
        if tiers.get(r["doc_id"], "A") != "A":
            continue
        by.setdefault(r["agency"], {}).setdefault(r["surface_kind"], []).append(r)
    cells, bodies, comparable = 0, set(), 0
    for agency, kinds in by.items():
        homes, flags = kinds.get(HOST_SURFACE, []), kinds.get(PRODUCT_SURFACE, [])
        if not (homes and flags):
            continue
        comparable += 1
        for f in flags:
            for leg in five:
                if homes[0]["verdicts"].get(leg) != f["verdicts"].get(leg):
                    cells += 1
                    bodies.add(agency)
    return {"cells": cells, "bodies": len(bodies), "comparable_bodies": comparable}


VERDICTS = ("pass", "fail", "error", "not_applicable")


def leg_key(leg: str) -> str:
    return leg.replace("-", "_").lower()


def leg_counts(rows: list, legs: list) -> dict:
    """Per leg, the verdict counts over ONE row set, plus the applicable denominator.

    `error` is excluded from the denominator for the same reason it always is: the collector
    could not observe, which is ours and not the product's (DD-052 §6). `not declared` is
    excluded too and is not a verdict at all — an agency that has not said which product to
    look at has not been measured and has not failed.
    """
    out: dict = {}
    for leg in legs:
        c = {v: 0 for v in VERDICTS}
        for r in rows:
            v = r["verdicts"].get(leg)
            if v in c:
                c[v] += 1
        n = c["pass"] + c["fail"]
        lo, hi = wilson_interval(c["pass"], n)
        out[leg] = {**c, "applicable_n": n, "wilson_hi": hi, "wilson_lo": lo}
    return out


def leg_results(counts: dict, prefix: str, cycle: str, population: str,
                with_upper95: bool = False, family: str | None = None) -> list:
    """(base, value, note) per leg. Bases are BARE; `cycle_results.name_for` stamps the cycle.

    These exist because the report may not type a number. The cycle already registers per-leg
    counts, and they are over a DIFFERENT population — every Tier A product surface — so
    quoting one of those in a sentence about the sixteen host-level rows would be a number that
    resolves, from a measurement of something else. A separate denominator needs a separate
    name.

    **`family` is required whenever `with_upper95` is set, and that is the fix this argument
    exists for** (`cc_tasks/2026-09-10_l0_figures_and_leg_rate_names.md` decision 2). The counts
    have always been family-distinct, because `prefix` distinguishes them. The upper bound was
    not: it was emitted as `scan_leg_rate_<leg>_upper95` by all three families, so host, product
    and Tier C competed for one string. The original run bound whichever reached the registry
    first and a later re-registration bound a different family's number under the same name —
    six Tier C values under host-family names, recorded in
    `cc_tasks/2026-09-10_rejudge_2_3_4_RESULT.md` §1 and unfixable, because a Result name binds
    once (AD-028).

    So the bound is now `scan_l0_<family>_leg_rate_<leg>_upper95`. The unprefixed name is never
    emitted again; the ones already registered stand, unedited, as what they are.
    """
    if with_upper95 and not family:
        raise ValueError(
            "leg_results(with_upper95=True) needs a `family`: the upper bound's name carries "
            "it, and an unnamed family is how three populations came to share one Result name")
    out = []
    for leg, s_ in sorted(counts.items()):
        k = leg_key(leg)
        base = (f"Cycle {cycle}, leg {leg}, over {population}. `error` means the COLLECTOR "
                f"could not observe and is excluded from the denominator, never counted as a "
                f"product failure (DD-052 §6).")
        for v in VERDICTS:
            out.append((f"{prefix}{k}_{v}", s_[v], f"{base} Verdicts of `{v}`: {s_[v]}."))
        out.append((f"{prefix}{k}_applicable_n", s_["applicable_n"],
                    f"{base} Denominator: pass + fail, which is {s_['applicable_n']}."))
        if with_upper95:
            out.append((
                f"scan_l0_{family}_leg_rate_{k}_upper95", s_["wilson_hi"],
                f"{base} Upper bound of the 95% Wilson score interval on the pass rate, "
                f"{s_['pass']}/{s_['applicable_n']}, from assessment/harness/rollup.py — the "
                f"repo's own interval, delegated and never re-derived. At {s_['applicable_n']} "
                f"and {s_['pass']} passes this is the number the Hanley and Lippman-Hand rule "
                f"of three approximates; it is registered rather than computed in prose so a "
                f"reader can check the bound against the count that produced it. Wilson (1927), "
                f"and Brown, Cai and DasGupta (2001) for why not Wald at a proportion this "
                f"close to the end of the scale."))
    return out


def write_pair(stem: str, header: dict, rows: list, legs: list, kind: str) -> tuple:
    """One JSON and one CSV per matrix, the CSV carrying the same `finding_id`s as the JSON.

    The CSV stays one row per body so it renders as the matrix the report shows; the identities
    ride in a single `finding_ids` column as `leg=fnd_...` pairs rather than as ten more
    columns, which keeps the file readable by eye and still walkable by machine.
    """
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    jpath, cpath = OUT_DIR / f"{stem}.json", OUT_DIR / f"{stem}.csv"
    jpath.write_text(json.dumps({**header, "legs": legs, "rows": rows}, indent=1) + "\n",
                     encoding="utf-8")
    if kind == "host":
        cols = (["agency", "tier", "host_surface", "host_url", "candidate_surface"] + legs
                + ["refused_identified_client", "probes_on_host_surface", "finding_ids"])
    else:
        cols = ["agency", "declared", "surface", "url"] + legs + ["finding_ids"]
    with cpath.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(cols)
        for r in rows:
            # Built by walking `cols` IN ORDER. Collecting the non-leg fields into one list
            # and concatenating put `refused_identified_client` — which sits after the legs in
            # the header — into the first leg's column, and the file still parsed and still had
            # the right number of fields. A header and a row that agree only in length agree
            # about nothing.
            fids = " ".join(f"{l}={r['finding_ids'][l]}" for l in legs
                            if r["finding_ids"].get(l))
            w.writerow([fids if c == "finding_ids"
                        else r["verdicts"][c] if c in legs
                        else r.get(c) for c in cols])
    return jpath, cpath


#: Where the rendered markdown fragments go. The report INCLUDES these; it does not retype
#: them. The design note is explicit that the matrix is rendered from the cycle's data rather
#: than typed, and a table typed into prose is a copy that drifts the first time a cell moves.
GEN_DIR = OUT_DIR / "generated"

#: How a verdict prints in the report's table. `pass` and `fail` are the measurement; `error`
#: says the collector could not observe and is never a product failure; `not declared` says
#: nobody has named a product to look at.
GLYPH = {"pass": "pass", "fail": "fail", "error": "error",
         "not_applicable": "n.a.", "not declared": "not declared",
         "not measured": "not measured"}


def markdown_table(rows: list, legs: list, kind: str) -> str:
    """The matrix as a markdown table, one row per body."""
    if kind == "host":
        head = ["Agency"] + legs + ["Refused of probed"]
        body = [[r["agency"]] + [GLYPH.get(r["verdicts"][l], r["verdicts"][l]) for l in legs]
                + [f"{r['refused_identified_client']} of {r['probes_on_host_surface']}"]
                for r in rows]
    else:
        head = ["Agency", "Surface"] + legs
        body = [[r["agency"], (r["surface"] or "not declared").replace("scan-", "")]
                + [GLYPH.get(r["verdicts"][l], r["verdicts"][l]) for l in legs]
                for r in rows]
    out = ["| " + " | ".join(head) + " |",
           "|" + "|".join(["---"] * len(head)) + "|"]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in body]
    return "\n".join(out) + "\n"


def write_fragment(stem: str, rows: list, legs: list, kind: str) -> Path:
    GEN_DIR.mkdir(parents=True, exist_ok=True)
    path = GEN_DIR / f"{stem}.md"
    path.write_text(markdown_table(rows, legs, kind), encoding="utf-8")
    return path


def rules_fragment(p: dict) -> str:
    """Which rule version judged each leg in this cycle, read from the cycle's own Findings.

    From the payload and not from `rules.CURRENT`: `CURRENT` is what the code would use TODAY,
    and this appendix is about what judged THIS cycle. The two agree now and will not after the
    next rule ships, and the version that judged a stored Finding is a property of the Finding.
    """
    seen: dict = {}
    for f in p["findings_detail"]:
        seen.setdefault(f["leg"], set()).add(f["rule_id"])
    out = ["| Check | Rule that judged this cycle |", "|---|---|"]
    for leg in sorted(seen):
        out.append(f"| {leg} | {', '.join(sorted(seen[leg]))} |")
    return "\n".join(out) + "\n"


def requests_fragment(p: dict) -> str:
    """Requests issued per netloc, counted at the socket, from the cycle's own counter."""
    per = p.get("requests_per_host") or {}
    out = ["| Netloc | Requests |", "|---|---|"]
    for h in sorted(per):
        out.append(f"| `{h}` | {per[h]} |")
    out.append(f"| **total** | **{sum(per.values())}** |")
    return "\n".join(out) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--cycle", default=None,
                    help="build a cycle other than params.cycle.name — a RE-JUDGEMENT, whose "
                         "matrices and Results are the judgement of record while the requests "
                         "it quotes remain the measured cycle's")
    a = ap.parse_args(argv)
    params = load_params()
    cycle = a.cycle or params["cycle"]["name"]
    suffix = cycle_results.cycle_suffix(cycle)
    p, tiers = payload(cycle), tier_of(params)
    tier0 = list(params["tier0"]["legs"])

    tier_a = host_matrix(p, tiers, "A", tier0)
    tier_c = host_matrix(p, tiers, "C", tier0)
    product = product_matrix(p, tiers, PRODUCT_LEGS)
    declared = sum(1 for r in product if r["declared"])
    declared_agencies = len({r["agency"] for r in product if r["declared"]})

    host_counts = leg_counts(tier_a, tier0)
    prod_counts = leg_counts([r for r in product if r["declared"]], PRODUCT_LEGS)
    tierc_counts = leg_counts(tier_c, tier0)
    dis = surface_disagreements(p, tiers, tier0)

    head = {"task": TASK, "cycle": cycle, "params_hash": p["params_hash"],
            "note": ("Every cell names the Finding it came from. The five surface-judged "
                     "tier-0 legs are read from the body's `home:` surface and A12 from its "
                     f"`host:` well-known surface; this cycle's home and flagship surfaces "
                     f"disagree on {dis['cells']} of those cells across {dis['bodies']} "
                     f"bodies, so the surface is named on every row."),
            "surface_disagreements": dis}
    files = [
        write_pair(f"scan_matrix_tierA_{suffix}", {**head, "tier": "A"}, tier_a, tier0, "host"),
        write_pair(f"scan_matrix_tierC_{suffix}",
                   {**head, "tier": "C",
                    "note": head["note"] + " Tier C reference hosts enter no Tier A "
                                           "denominator and appear on no agency matrix "
                                           "(DD-059)."},
                   tier_c, tier0, "host"),
        write_pair(f"scan_matrix_product_{suffix}",
                   {**head, "tier": "A", "partial": True,
                    "declared_agencies": declared_agencies, "declared_surfaces": declared,
                    "note": ("PARTIAL. Product-level legs over DECLARED flagship surfaces "
                             "only. An agency with no declared flagship carries `not "
                             "declared`, which is neither a fail nor an omission.")},
                   product, PRODUCT_LEGS, "product"),
    ]
    fragments = [write_fragment("matrix_tierA", tier_a, tier0, "host"),
                 write_fragment("matrix_tierC", tier_c, tier0, "host"),
                 write_fragment("matrix_product", product, PRODUCT_LEGS, "product")]
    GEN_DIR.mkdir(parents=True, exist_ok=True)
    for stem, text in (("rules_by_leg", rules_fragment(p)),
                       ("requests_per_netloc", requests_fragment(evidence_payload(p)))):
        path = GEN_DIR / f"{stem}.md"
        path.write_text(text, encoding="utf-8")
        fragments.append(path)

    summary = {"tier_a_rows": len(tier_a), "tier_c_rows": len(tier_c),
               "fragments": [str(f.relative_to(REPO)) for f in fragments],
               "product_rows": len(product), "declared_surfaces": declared,
               "declared_agencies": declared_agencies,
               "surface_disagreements": dis,
               "host_counts": {l: {k: v for k, v in c.items() if k != "wilson_lo"}
                               for l, c in host_counts.items()},
               "product_counts": {l: {k: v for k, v in c.items() if k != "wilson_lo"}
                                  for l, c in prod_counts.items()},
               "files": [str(f.relative_to(REPO)) for pair in files for f in pair]}
    if a.dry_run:
        print(json.dumps(summary, indent=1))
        return 0

    zero_legs = sorted(l for l, c in prod_counts.items() if c["applicable_n"] and not c["pass"])
    per_leg = ([
        ("scan_l0_product_legs", len(PRODUCT_LEGS),
         f"Product-level checks asked of every declared flagship surface in cycle {cycle}: "
         f"{', '.join(PRODUCT_LEGS)}. What a PRODUCT offers a machine, as against what a HOST "
         f"declares. Task {TASK} §1.3."),
        ("scan_l0_product_legs_at_zero", len(zero_legs),
         f"Product-level checks on which NO declared flagship surface passed in cycle "
         f"{cycle}: {', '.join(zero_legs)}. Counted over the "
         f"{declared} declared surfaces, which is a PARTIAL population; each of these has its "
         f"own registered upper bound (`scan_leg_rate_<check>_upper95_...`), and a zero at "
         f"this denominator is not evidence of universal absence. Task {TASK} §1.3."),
        ("scan_l0_home_flagship_disagreement_cells",
         dis["cells"],
         f"Cells in cycle {cycle} where a Tier A body's HOME surface and one of its FLAGSHIP "
         f"surfaces answer the SAME host-level check differently, over the "
         f"{dis['comparable_bodies']} bodies that have both. A `robots.txt` permitting the "
         f"front door can disallow a particular product, so these checks are judged per "
         f"surface and not per host. This is why the L0 matrix names the surface each cell "
         f"was measured on: a single combined host cell would have to pick a winner for these "
         f"and would not say which. Task {TASK} §1.1."),
        ("scan_l0_home_flagship_disagreement_bodies", dis["bodies"],
         f"Distinct Tier A bodies carrying at least one of those disagreements, of the "
         f"{dis['comparable_bodies']} with both a home and a flagship surface. Task {TASK} "
         f"§1.1."),
    ] +
        leg_results(host_counts, "scan_l0_", cycle,
                    "the 16 Tier A bodies' HOST-LEVEL surfaces (each body's `home:` page, and "
                    "its `host:` well-known set for A12)", with_upper95=True, family="host")
        + leg_results(prod_counts, "scan_l0_product_", cycle,
                      f"the {declared} DECLARED flagship surfaces of {declared_agencies} Tier "
                      f"A agencies — a PARTIAL population, because the other agencies have "
                      f"declared no product to look at", with_upper95=True, family="product")
        # Tier C emits its upper bound too, now that a family-prefixed name makes that safe.
        # It could not before: the unprefixed name was unambiguous in THIS builder only because
        # the host family's legs (tier 0) and the product family's are disjoint and Tier C was
        # never asked for the stat. A caller that asked it — `register_l0_rejudged.py` did —
        # got Tier C values competing for host-family names, which is how six Results came to
        # say the wrong thing. Naming the family removes the coincidence the old scheme
        # depended on.
        + leg_results(tierc_counts, "scan_l0_tierc_", cycle,
                      "the 3 Tier C reference hosts' host-level surfaces, which enter no Tier "
                      "A denominator (DD-059)", with_upper95=True, family="tierc"))

    out = cycle_results.register(
        [(cycle_results.name_for(b, cycle), v, f"{n} ({TASK})") for b, v, n in per_leg]
        + [(cycle_results.name_for("scan_l0_declared_flagship_agencies", cycle),
          declared_agencies,
          f"Tier A agencies with at least one operator-DECLARED flagship surface in cycle "
          f"{cycle}, of the 16 in the frame. The product-level matrix is denominated by these "
          f"and is labelled PARTIAL for that reason: the remaining agencies carry a host row "
          f"and its probes and nothing else, and a product leg cannot be asked of a product "
          f"nobody has named. `not declared` is not `fail`. "
          f"docs/design/fss_flagship_shortlist.md is where the declaration gets made. "
          f"Task {TASK} §1.3."),
         (cycle_results.name_for("scan_l0_declared_flagship_surfaces", cycle), declared,
          f"Declared flagship SURFACES in cycle {cycle}, across "
          f"{declared_agencies} agencies: some agencies declare more than one, and the "
          f"product matrix has one row per surface so two flagships of one agency that "
          f"disagree are visible as two rows rather than averaged into one. Task {TASK} §1.3.")],
        cycle=cycle, script=SCRIPT_ARTIFACT,
        data=f"scan_matrix_tierA_{suffix}",
        data_path=f"docs/reports/scan_matrix_tierA_{suffix}.json",
        data_description=(
            f"The L0 host-level matrix for cycle {cycle}: one row per Tier A body, one column "
            f"per tier-0 leg, every cell naming the Finding identity it came from, plus the "
            f"count of probes the host refused to the identified client. Written by "
            f"scripts/build_l0_matrices.py from state/{cycle}.json under params_hash "
            f"{p['params_hash'][:12]}.... Emitted as CSV and JSON beside the report so the "
            f"matrix is machine-readable without parsing prose. Task {TASK}."))
    print(json.dumps({**summary, "registered": out}, indent=1))
    return 1 if out["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
