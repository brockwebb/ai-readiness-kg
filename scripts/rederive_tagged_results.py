#!/usr/bin/env python3
"""Re-derive every Result the L0 report tags, from the artifact that generated it.

`cc_tasks/2026-09-12_publish_l0.md` §1, implementing DN-002 decision 3: *a tagged Result moves
`proposed -> verified` on a FRESH re-derivation that reproduces its value, and one that cannot
be re-derived is a stop, not a footnote.* **Zero model spend, zero network.**

**The generator is re-run; the value is not re-implemented.** Re-deriving a number by writing
new code that computes the same thing tests the new code, not the registered claim. So every
adapter below drives the module the registry names in `GENERATED_BY`, over the file the
registry names in `COMPUTED_FROM`, and intercepts the registrar instead of re-implementing the
arithmetic. What is captured is exactly the `(name, value)` pairs that module would register
today.

The interception point is `cycle_results.register`, which is the single choke point every
registrar in this repo goes through (`scripts/cycle_results.py`). Replacing it captures the
rows and writes nothing to the graph, so a re-derivation can never mint or re-bind a Result.

**Three generators are not re-run, for reasons on their face:**

* `build_roster` FETCHES its two roster sources. Re-running it would contact statspolicy.gov,
  and this task's network budget is the published host alone. It retained both bodies
  content-addressed when it ran, and `sources[].retained_path` names them, so the adapter
  rebuilds its `caps` from those bytes and calls `build_roster.build()` — the same parse over
  the same bytes, off the network.
* `preflight` PROBES nineteen federal hosts. Same argument; its generating artifact is
  `state/fss_preflight_2026-09.json` and the value is recounted from the list it recorded.
* `build_l0_matrices` for the `_rj1` cycle writes a matrix pair and three report fragments.
  The rj2 cycle's outputs are shipped artifacts and are rebuilt in place ON PURPOSE — a
  difference there is a re-derivation failure and must show as one — but rj1's have never been
  shipped, so that run is pointed at a temporary directory through the module-path globals
  (`OUT_DIR`, `GEN_DIR`), which this repo reads at call time for exactly this reason.

**The tagged set is READ, never typed.** It comes from the `{{result:NAME:...}}` tags in
`docs/reports/sections/*.md`, so a Result the report starts quoting tomorrow is in the gate
tomorrow without anybody remembering to add it.

    /opt/anaconda3/bin/python3 scripts/rederive_tagged_results.py [--json PATH]

Exit 0 only when every tagged Result re-derived and every re-derived value equals the
registered one. Any missing derivation and any disagreement is a non-zero exit and a stop.
"""
from __future__ import annotations

import argparse
import contextlib
import io
import json
import re
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, "/Users/brock/GitHub/seldon")
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "assessment" / "harness"))

SECTIONS = REPO / "docs" / "reports" / "sections"

#: `{{result:NAME:field}}` — the same token family `seldon.paper.build` resolves. Only the
#: NAME is taken; which field the prose quotes does not change which Result must re-derive.
TAG = re.compile(r"\{\{result:([^:}]+):[^}]*\}\}")

#: The cycle whose re-judgement is the report's snapshot, and the earlier re-judgement two of
#: its numbers still quote. Read from the tags themselves would be circular (a name is not a
#: cycle), so they are named here — and asserted against the tagged set below, which is what
#: stops this pair going stale silently.
CYCLE_RJ2 = "scan_2026-09-10_rj2"
CYCLE_RJ1 = "scan_2026-09-10_rj1"

#: The measured cycle the two re-judgements rest on. Four tagged Results are facts about the
#: COLLECTION — observations, requests, netlocs contacted, error classes — and belong to it.
#:
#: Passed to `scan_report` EXPLICITLY rather than letting it default to `params.cycle.name`,
#: which is the same string. The default path additionally calls `rederived_count`, which
#: re-derives every Finding under the params ON DISK and refuses when they have moved — and
#: they have: `params.yaml` is at harness-v5 and this cycle was measured at
#: `4e0a92ba19ab...`. That refusal is correct and is the harness saying *do not compare across
#: a parameter change*. The Finding-level re-derivation of this payload is not skipped by
#: naming the cycle; it is done where it can be done properly, by
#: `tests/test_scan_harness_v4.py::..._re_derives...`, which recovers each payload's own
#: params from git BY HASH and which `make gate-task` runs. The four values below are counts
#: off the stored payload and do not depend on Finding identity at all.
CYCLE_BASE = "scan_2026-09-10"


def tagged_names() -> list:
    """Every Result name the report quotes, from the section sources."""
    names = set()
    for f in sorted(SECTIONS.glob("*.md")):
        names |= set(TAG.findall(f.read_text(encoding="utf-8")))
    if not names:
        raise SystemExit(f"FATAL: no {{{{result:...}}}} tags under {SECTIONS}; the gate would "
                         f"pass vacuously")
    return sorted(names)


def registered(names: list) -> dict:
    """name -> {value, artifact_id, state, computed_from, generated_by} from the live graph."""
    from seldon.config import get_neo4j_driver, load_project_config
    cfg = load_project_config(REPO)
    db = cfg["neo4j"]["database"]
    driver = get_neo4j_driver(cfg)
    out = {}
    try:
        with driver.session(database=db) as s:
            for n in names:
                rows = s.run(
                    "MATCH (r:Result {name: $n}) WHERE r.state <> 'superseded' "
                    "OPTIONAL MATCH (r)-[:COMPUTED_FROM]->(d:DataFile) "
                    "OPTIONAL MATCH (r)-[:GENERATED_BY]->(sc:Script) "
                    "RETURN r.artifact_id AS id, r.state AS state, r.value AS value, "
                    "       collect(DISTINCT d.name) AS data, "
                    "       collect(DISTINCT sc.name) AS script", n=n).data()
                if len(rows) != 1:
                    raise SystemExit(
                        f"FATAL: {n!r} resolves to {len(rows)} live Results; a tagged name "
                        f"must resolve to exactly one or the report quotes an ambiguity")
                r = rows[0]
                out[n] = {"artifact_id": r["id"], "state": r["state"], "value": r["value"],
                          "computed_from": sorted(x for x in r["data"] if x),
                          "generated_by": sorted(x for x in r["script"] if x)}
    finally:
        driver.close()
    return out


# ---------------------------------------------------------------------------
# The capture harness
# ---------------------------------------------------------------------------

class Captured(dict):
    """name -> value, refusing a second derivation that disagrees with the first."""

    def absorb(self, rows, where: str) -> None:
        for name, value, *_ in rows:
            v = float(value)
            if name in self and self[name] != v:
                raise SystemExit(
                    f"FATAL: {where} re-derived {name} as {v}, and an earlier adapter derived "
                    f"{self[name]}. Two generators disagree about one Result; nothing is "
                    f"verified.")
            self[name] = v


@contextlib.contextmanager
def intercept(captured: Captured, where: str):
    """Swap `cycle_results.register` for a capture. Nothing reaches the graph."""
    import cycle_results
    real = cycle_results.register

    def fake(rows, cycle, script, data, data_path=None, data_description=None):
        captured.absorb(rows, where)
        return {"registered": 0, "already_at_this_value": len(rows), "failed": 0,
                "of": len(rows)}

    cycle_results.register = fake
    try:
        yield
    finally:
        cycle_results.register = real


def drive(module_name: str, argv: list, captured: Captured) -> None:
    """Run a registrar's own `main` with the registrar intercepted."""
    mod = __import__(module_name)
    where = f"{module_name} {' '.join(argv) or '(no args)'}"
    buf = io.StringIO()
    with intercept(captured, where), contextlib.redirect_stdout(buf):
        rc = mod.main(argv)
    if rc:
        raise SystemExit(f"FATAL: {where} exited {rc}; its tail:\n{buf.getvalue()[-1200:]}")


# ---------------------------------------------------------------------------
# The adapters that cannot just be driven
# ---------------------------------------------------------------------------

def rederive_matrices_rj1(captured: Captured) -> None:
    """`build_l0_matrices` over the rj1 cycle, writing into a temp tree.

    Only two rj1 Results are tagged, but the module registers a cycle's whole family at once,
    so the run is the whole family and the comparison picks out what the report quotes.
    """
    import build_l0_matrices as blm
    out_dir, gen_dir = blm.OUT_DIR, blm.GEN_DIR
    # Inside the repo, because the module reports its outputs with `Path.relative_to(REPO)`
    # and a directory outside the tree makes the REPORTING raise. `tmp/` is gitignored.
    scratch = REPO / "tmp"
    scratch.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=scratch) as tmp:
        blm.OUT_DIR = Path(tmp)
        blm.GEN_DIR = Path(tmp) / "generated"
        try:
            drive("build_l0_matrices", ["--cycle", CYCLE_RJ1], captured)
        finally:
            blm.OUT_DIR, blm.GEN_DIR = out_dir, gen_dir


def rederive_base_cycle_counts(captured: Captured) -> None:
    """`scan_report` over the MEASURED cycle, with its matrix written to a temp tree.

    Four tagged Results are facts about the collection rather than about a judgement, and they
    belong to `scan_2026-09-10`. Driving `scan_report` recomputes them from that cycle's stored
    payload, which is what a re-derivation is — but `scan_report.main` also WRITES
    `state/scan_matrix_<suffix>.json`, and for this cycle that file is *deliberately absent*:
    `scan_2026-09-10` was measured and never reported, the judgement of record is the
    re-judgement `_rj2`, and `tests/test_scan_figures.py::matrix` skips the whole figure suite
    on exactly that absence (`cc_tasks/2026-09-10_harness_v5_blind.md` decision 6). Materialising
    it turns eight documented skips into eight errors, because the base cycle never registered
    the pooled per-leg rates a figure resolves.

    So the write goes to a temporary directory. The ARITHMETIC is the generator's, unchanged;
    what is redirected is a side effect whose absence is a recorded decision.
    """
    import scan_report
    real = scan_report.matrix_path
    scratch = REPO / "tmp"
    scratch.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=scratch) as tmp:
        scan_report.matrix_path = lambda cycle: Path(tmp) / f"scan_matrix_{cycle}.json"
        # The Tier C sibling is built from `REPO / "state"` inside `main` and cannot be
        # redirected the same way, so it is removed afterwards if the run created it. Checked
        # BEFORE the run, so a file that already existed is never deleted.
        tierc = REPO / "state" / f"scan_matrix_tierc_{cycle_suffix(CYCLE_BASE)}.json"
        pre_existing = tierc.is_file()
        try:
            drive("scan_report", ["--cycle", CYCLE_BASE], captured)
        finally:
            scan_report.matrix_path = real
            if tierc.is_file() and not pre_existing:
                tierc.unlink()


def cycle_suffix(cycle: str) -> str:
    import cycle_results
    return cycle_results.cycle_suffix(cycle)


def rederive_roster(captured: Captured) -> None:
    """`build_roster.build()` over the two RETAINED source bodies. No network."""
    import build_roster
    from scan import load_params
    doc = json.loads((REPO / "state" / "fss_roster_2026-09.json").read_text(encoding="utf-8"))
    caps = {}
    for src in doc["sources"]:
        body_path = REPO / src["retained_path"]
        if not body_path.is_file():
            raise SystemExit(
                f"FATAL: the roster names {src['retained_path']} as the retained body of "
                f"{src['name']} and the repo does not hold it; the roster cannot be "
                f"re-derived without re-fetching, which this task may not do")
        cap = {k: v for k, v in src.items() if k != "retained_path"}
        cap["body"] = body_path.read_bytes()
        caps[src["name"]] = cap
    roster = build_roster.build(load_params(), caps)
    captured.absorb([
        ("fss_agencies_tier_a", len(roster["tier_a"]), ""),
        ("fss_tier_a_source_disagreements", len(roster["tier_a_disagreements"]), ""),
    ], "build_roster.build over retained bodies")


def rederive_preflight(captured: Captured) -> None:
    """Recount the refusals the pre-flight recorded. No host is probed again."""
    p = REPO / "state" / "fss_preflight_2026-09.json"
    d = json.loads(p.read_text(encoding="utf-8"))
    rows = d["rows"]
    recount = [r["host"] for r in rows if r["refuses_identified_client"]]
    if sorted(recount) != sorted(d["refusing_identified_client"]):
        raise SystemExit(
            f"FATAL: {p.name} summary lists {d['refusing_identified_client']} refusing and its "
            f"own rows say {recount}; the artifact disagrees with itself")
    captured.absorb([("fss_hosts_refusing_identified_client_2026-09", len(recount), "")],
                    "preflight payload recount")


# ---------------------------------------------------------------------------

def rederive_all() -> Captured:
    captured = Captured()
    # rj1 FIRST and into a temp tree, so the shipped fragments end the run at rj2.
    rederive_matrices_rj1(captured)
    drive("build_l0_matrices", ["--cycle", CYCLE_RJ2], captured)
    drive("scan_report", ["--cycle", CYCLE_RJ2], captured)
    rederive_base_cycle_counts(captured)
    drive("register_l0_report_results", ["--cycle", CYCLE_RJ2], captured)
    drive("register_l0_report_results", [], captured)
    drive("register_frame_v5_results", [], captured)
    drive("register_esip_crosswalk_results", [], captured)
    rederive_roster(captured)
    rederive_preflight(captured)
    return captured


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", default=None, metavar="PATH",
                    help="write the full comparison here as well as summarising it")
    a = ap.parse_args(argv)

    names = tagged_names()
    reg = registered(names)
    for cyc in (CYCLE_RJ1, CYCLE_RJ2):
        suffix = cyc[len("scan_"):]
        if not any(n.endswith(suffix) for n in names):
            raise SystemExit(
                f"FATAL: this gate drives the {cyc} cycle and the report tags nothing from "
                f"it; the cycle constants are stale and the gate is checking the wrong run")

    captured = rederive_all()

    rows, missing, disagree = [], [], []
    for n in names:
        r = reg[n]
        got = captured.get(n)
        row = {"name": n, "state": r["state"], "registered": r["value"], "rederived": got,
               "computed_from": r["computed_from"], "generated_by": r["generated_by"]}
        if got is None:
            missing.append(n)
            row["verdict"] = "not_rederived"
        elif float(r["value"]) != got:
            disagree.append(f"{n}: registered {r['value']}, re-derived {got}")
            row["verdict"] = "disagrees"
        else:
            row["verdict"] = "reproduces"
        rows.append(row)

    report = {"tagged": len(names), "rederived_names_available": len(captured),
              "reproduces": sum(1 for r in rows if r["verdict"] == "reproduces"),
              "not_rederived": missing, "disagrees": disagree,
              "states_before": sorted({r["state"] for r in rows}),
              "gate": "PASS" if not missing and not disagree else "BLOCKED",
              "rows": rows}
    if a.json:
        Path(a.json).write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "rows"}, indent=1))
    return 0 if report["gate"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
