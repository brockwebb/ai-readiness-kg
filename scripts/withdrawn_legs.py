"""The report's sentence about a leg withdrawn from the host-level instrument. **No spend.**

`cc_tasks/2026-09-15_g1d_leaves_l0.md` decision 4 as amended by its ADDENDUM_01: the paragraph
that used to state a host-level G1-D rate is replaced by one sentence saying the leg was
measured in cycles 1 to 4 and the self cycle, withdrawn as not applicable to the surface, and
where the property is measured instead — **generated from a graph fact, not typed.**

Generated rather than written into `sections/20_matrix.md` for the reason every other generated
fragment in this report exists: the counts in it are measurements, and a measurement typed into
prose is one nobody re-derives. The withdrawal itself is a parameter
(`params.tier0.legs_withdrawn`), so the sentence says what the instrument says and cannot drift
from it.

**The sentence's own evidence is the argument for the withdrawal.** It reports the verdicts the
leg produced on host-level surfaces — every body, every reference host, every cycle — and the
verdicts the same rule produced on product surfaces in the same runs. A leg that never passes
on one surface kind and passes a hundred times on another is not measuring the agencies; it is
measuring which surface it was pointed at.

    /opt/anaconda3/bin/python3 scripts/withdrawn_legs.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "assessment"))
sys.path.insert(0, str(REPO / "assessment" / "harness"))
sys.path.insert(0, "/Users/brock/GitHub/seldon")

FRAGMENT = "withdrawn_legs"

#: Which stored surface kinds count as HOST-LEVEL for this count. The same two the withdrawal
#: names in `params.tier0.legs_withdrawn[].from_surfaces`, read from there rather than repeated,
#: so the sentence and the instrument cannot disagree about what "host level" means.
_HOST_DEFAULT = ("home", "well_known")


def surface_kinds(repo: Path = REPO) -> dict:
    """`doc_id -> surface_kind`, from the stored payloads' own matrix rows.

    The payloads are the only record of which surface a `doc_id` IS: the graph's Finding carries
    `target_doc_id` and no surface kind, because a surface kind is a property of the frame and
    not of a judgement. Read from every payload so a doc_id retired from the current frame is
    still classifiable.
    """
    out: dict = {}
    for path in sorted((repo / "state").glob("*.json")):
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(doc, dict):
            continue
        for row in (doc.get("matrix") or []):
            out.setdefault(row["doc_id"], row.get("surface_kind"))
    return out


def census(session, leg_rule_prefix: str, kinds: dict, host_kinds) -> dict:
    """Every Finding this rule ever made, split by surface kind and verdict.

    Keyed on `rule_id`, not on `indicator_code`: the graph stores the SPEC code (`G1`) on
    `Finding.indicator_code` and the leg name (`G1-D`) lives on the payload and in
    `params.tier0.legs`. A query written against the leg name returns nothing and reads exactly
    like a leg that was never measured.
    """
    rows = [dict(r) for r in session.run(
        "MATCH (f:Finding) WHERE f.rule_id STARTS WITH $p "
        "RETURN f.verdict AS verdict, f.target_doc_id AS doc, f.cycle AS cycle",
        p=leg_rule_prefix)]
    host, product = {}, {}
    for r in rows:
        kind = kinds.get(r["doc"])
        bucket = host if (kind in host_kinds or str(r["doc"]).startswith("host:")) else product
        bucket[r["verdict"]] = bucket.get(r["verdict"], 0) + 1
    return {"findings": len(rows), "host": host, "product": product,
            "host_total": sum(host.values()), "product_total": sum(product.values())}


def sentence(leg: dict, c: dict) -> str:
    """The paragraph, as it renders. Every numeral in it is a count from `census`."""
    h, p = c["host"], c["product"]
    return (
        f"**Uncertainty fields.** This column has been withdrawn. **{leg['leg']}** asks whether "
        f"a published figure carries, beside it and in machine-readable form, the fields that "
        f"make it interpretable — a measure of uncertainty, a suppression flag, a reliability "
        f"marker. The construct stands; the level was wrong. A body's home page carries no "
        f"estimate, so the check could not hold the property it measures there: across every "
        f"body, every reference host and every cycle it returned {h.get('fail', 0)} `fail` and "
        f"{h.get('error', 0)} `error` on host-level surfaces and **not one** `pass`, while the "
        f"same rule returned {p.get('pass', 0)} `pass` on product surfaces in the same runs. A "
        f"check that never passes on one kind of surface and passes {p.get('pass', 0)} times on "
        f"another is measuring which surface it was pointed at, not the publisher. It is "
        f"withdrawn from the host-level instrument effective {leg['effective']} "
        f"(`DD-066`); the cycles that measured it keep every observation and every verdict on "
        f"the append-only log, unchanged and un-re-judged, because it was not mis-scored — it "
        f"was asked of the wrong surface. Where the property does live is a data product, and "
        f"that is the January G1 pilot's instrument, not this one's.")


def build(session, params: dict, out_dir: Path | None = None) -> dict:
    """Write `generated/withdrawn_legs.md` for every withdrawn leg. Returns the summary."""
    out_dir = out_dir or (REPO / "docs" / "reports" / "generated")
    withdrawn = (params.get("tier0", {}).get("legs_withdrawn") or [])
    kinds = surface_kinds()
    parts, summary = [], []
    for leg in withdrawn:
        host_kinds = tuple(leg.get("from_surfaces") or _HOST_DEFAULT)
        c = census(session, f"RULE-{leg['leg']}", kinds, host_kinds)
        if c["host"].get("pass"):
            # The premise of the withdrawal, checked on every build rather than once. A pass on
            # a host-level surface would mean the surface CAN carry the property and the leg was
            # mis-scored, which is a re-judgement question and not a withdrawal one.
            raise SystemExit(
                f"FATAL: {leg['leg']} has {c['host']['pass']} host-level `pass` verdict(s) on "
                f"the graph. The withdrawal's premise is that the surface cannot carry the "
                f"property; a pass falsifies it and the report may not state it.")
        parts.append(sentence(leg, c))
        summary.append({"leg": leg["leg"], "effective": leg["effective"],
                        "decision": leg["decision"], **c})
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{FRAGMENT}.md"
    # The bare-numeral lint's own declared marker for a GENERATED prose region, which is what
    # `build_l0_report.lint_bare_numerals` reads and what the method appendix already uses. The
    # counts in this paragraph came out of the graph on this build; the alternative — writing
    # the resolver's value-marker control characters into a committed `.md` — would put
    # invisible bytes in a file a person reads.
    body = ("<!-- lint: numerals-exempt -->\n\n" + "\n\n".join(parts)
            + "\n\n<!-- lint: numerals-enforced -->\n") if parts else ""
    path.write_text(body, encoding="utf-8")
    return {"fragment": str(path.relative_to(REPO)), "legs": summary}


def main() -> int:
    from scan import load_params
    from seldon.config import get_neo4j_driver, load_project_config
    cfg = load_project_config(REPO)
    driver = get_neo4j_driver(cfg)
    try:
        with driver.session(database=cfg["neo4j"]["database"]) as s:
            out = build(s, load_params())
    finally:
        driver.close()
    print(json.dumps(out, indent=1))
    print()
    print((REPO / out["fragment"]).read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
