"""Every indicator carries a measurement tier, sourced, or says why it does not.

`cc_tasks/2026-09-17_measurement_tiers.md` decisions 1 to 5, under DN-005 §2.2 and §4 item 2.

Three layers, each checked against the one before it:

1. **The record.** Every `AssessmentIndicator` in `framework/ai_readiness_framework.json`
   carries `measurement_tier` ∈ {M, O, D}, a `measurement_basis` legal for that tier and a
   non-empty `tier_source` — or it carries `tier_unassigned_reason` and none of the three. The
   distribution is a LITERAL here, for the reason `test_framework_projection_roundtrip.py`
   gives for its own: a gate that reads its expectation out of the artifact under test can
   only ever pass.
2. **The graph.** The same, by Cypher over the projection (decision 4). Skipped, never failed,
   when Neo4j is unreachable, as the round-trip gate beside it is.
3. **The views.** The tool map's §2 verdict is derived from the tier, never from a keyword
   (decision 3), and the product matrix does not carry the host-level withdrawal (decision 5).
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
RECORD = REPO / "framework" / "ai_readiness_framework.json"
TOOL_MAP = REPO / "docs" / "design" / "scan_tool_map.md"
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "assessment" / "harness"))

#: The distribution `cc_tasks/2026-09-17_measurement_tiers_RESULT.md` §2 reports. Moving an
#: indicator between tiers is a task's decision, and this literal is where the suite learns of
#: it.
EXPECTED_PER_TIER = {"M": 27, "O": 1, "D": 1}
EXPECTED_PER_BASIS = {"harness_leg": 17, "judged_reading": 2, "evaluation": 8,
                      "open_tool": 1, "declaration": 1}
EXPECTED_UNASSIGNED = {"A7", "B1", "B2", "B4", "B5", "B6", "C5", "D2", "D3", "E1", "E2",
                       "E3", "E7", "F1", "F2", "F3", "F5", "G3", "G4", "G5"}
BASIS_TIER = {"harness_leg": "M", "judged_reading": "M", "evaluation": "M",
              "open_tool": "O", "declaration": "D"}


def _tagger():
    spec = importlib.util.spec_from_file_location(
        "_tag_measurement_tiers", REPO / "scripts" / "tag_measurement_tiers.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def indicators():
    g = json.loads(RECORD.read_text(encoding="utf-8"))
    return {n["properties"]["code"]: n["properties"] for n in g["nodes"]
            if "AssessmentIndicator" in n["labels"]}


# ------------------------------------------------------------------ 1. the record

def test_every_indicator_is_tiered_or_says_why_not(indicators):
    bad = []
    for code, p in sorted(indicators.items()):
        tiered = all(p.get(k) for k in ("measurement_tier", "measurement_basis", "tier_source"))
        reason = bool(p.get("tier_unassigned_reason"))
        if tiered == reason:
            bad.append(f"{code}: tiered={tiered} unassigned_reason={reason}")
            continue
        if tiered:
            if p["measurement_tier"] not in BASIS_TIER.values():
                bad.append(f"{code}: measurement_tier {p['measurement_tier']!r}")
            elif BASIS_TIER.get(p["measurement_basis"]) != p["measurement_tier"]:
                bad.append(f"{code}: basis {p['measurement_basis']!r} on tier "
                           f"{p['measurement_tier']!r}")
        elif any(k in p for k in ("measurement_tier", "measurement_basis", "tier_source")):
            bad.append(f"{code}: unassigned and still carries a tier field")
    assert not bad, bad


def test_the_distribution_is_the_one_the_result_reports(indicators):
    from collections import Counter
    tiers = Counter(p["measurement_tier"] for p in indicators.values()
                    if p.get("measurement_tier"))
    bases = Counter(p["measurement_basis"] for p in indicators.values()
                    if p.get("measurement_basis"))
    unassigned = {c for c, p in indicators.items() if p.get("tier_unassigned_reason")}
    assert dict(tiers) == EXPECTED_PER_TIER
    assert dict(bases) == EXPECTED_PER_BASIS
    assert unassigned == EXPECTED_UNASSIGNED
    assert sum(tiers.values()) + len(unassigned) == len(indicators)


def test_every_rule_in_current_makes_its_indicator_harness_measured(indicators):
    """Decision 2 rule 1, re-derived from the registry: a rule shipped for a new leg must
    move its indicator, and this is where the suite notices it did not."""
    from scan.rules import CURRENT
    import report_traceability
    for leg in CURRENT:
        code = report_traceability.FRAMEWORK_CODE.get(leg, leg)
        p = indicators[code]
        assert (p.get("measurement_tier"), p.get("measurement_basis")) == ("M", "harness_leg"), (
            f"{leg} is served by {CURRENT[leg]} and {code} is not tiered M/harness_leg")


def test_the_record_is_what_the_tagger_would_write(indicators):
    """The tagger is the record's source for these fields: re-running it is a no-op."""
    tagger = _tagger()
    g = json.loads(RECORD.read_text(encoding="utf-8"))
    plan = tagger.assignments(g)
    for code, p in indicators.items():
        have = {k: p[k] for k in tagger.TIER_KEYS if k in p}
        assert have == plan[code], f"{code}: record {have} != tagger {plan[code]}"


def test_g1d_keeps_its_surface_level_under_its_own_name(indicators):
    """DD-066 §6: the tiering task may rename the field and does not remove the value."""
    p = indicators["G1-D"]
    assert p["measurement_level"] == "product"
    assert p["measurement_level_source"].startswith("DD-066")
    assert p["withdrawn_from"] == "host-level"
    assert p["measurement_tier"] == "M"
    assert "measurement_tier_source" not in p


def test_a_quoted_definition_is_quoted_verbatim(indicators):
    tagger = _tagger()
    for code, t in tagger.TABLE.items():
        if t.get("quote"):
            assert t["quote"] in indicators[code]["indicator"], code
            assert t["quote"] in indicators[code]["tier_source"], code


# ------------------------------------------------------------------ 2. the graph

@pytest.fixture(scope="module")
def graph():
    try:
        sys.path.insert(0, "/Users/brock/GitHub/seldon")
        from seldon.config import get_neo4j_driver, load_project_config
        cfg = load_project_config(REPO)
        driver = get_neo4j_driver(cfg)
        with driver.session(database=cfg["neo4j"]["database"]) as s:
            s.run("RETURN 1").single()
    except Exception as exc:                                    # noqa: BLE001 - see docstring
        pytest.skip(f"Neo4j unreachable, tier projection unverified: {exc}")
    with driver.session(database=cfg["neo4j"]["database"]) as s:
        yield s
    driver.close()


def test_the_graph_carries_a_tier_or_a_reason_on_every_indicator(graph):
    missing = [r["code"] for r in graph.run(
        "MATCH (i:AssessmentIndicator) "
        "WHERE NOT ((i.measurement_tier IS NOT NULL AND i.measurement_basis IS NOT NULL "
        "            AND i.tier_source IS NOT NULL) "
        "           XOR i.tier_unassigned_reason IS NOT NULL) "
        "RETURN i.code AS code ORDER BY code")]
    assert not missing, missing


def test_the_graph_counts_per_tier_match_the_result(graph):
    per_tier = {r["tier"]: r["n"] for r in graph.run(
        "MATCH (i:AssessmentIndicator) WHERE i.measurement_tier IS NOT NULL "
        "RETURN i.measurement_tier AS tier, count(*) AS n")}
    per_basis = {r["basis"]: r["n"] for r in graph.run(
        "MATCH (i:AssessmentIndicator) WHERE i.measurement_basis IS NOT NULL "
        "RETURN i.measurement_basis AS basis, count(*) AS n")}
    unassigned = {r["code"] for r in graph.run(
        "MATCH (i:AssessmentIndicator) WHERE i.tier_unassigned_reason IS NOT NULL "
        "RETURN i.code AS code")}
    assert per_tier == EXPECTED_PER_TIER
    assert per_basis == EXPECTED_PER_BASIS
    assert unassigned == EXPECTED_UNASSIGNED


# ------------------------------------------------------------------ 3. the views

def test_the_tool_map_derives_its_verdicts_from_the_tier(indicators):
    text = TOOL_MAP.read_text(encoding="utf-8")
    section = text.split("## 2.")[1].split("\n## ")[0]
    rows = [line for line in section.splitlines() if line.startswith("| ") and
            not line.startswith("| code")]
    assert rows, "the tool map's §2 has no rows"
    for line in rows:
        cells = [c.strip() for c in line.strip("|").split("|")]
        code, verdict, why = cells[0], cells[3], cells[4]
        # The keyword default may be QUOTED by an unassigned reason, as the thing retired; it
        # may never again be a row's own reason.
        assert "would serve it" not in why.split("\"")[0], (code, why)
        p = indicators[code]
        basis = p.get("measurement_basis")
        want = {"harness_leg": "scan-observable", "open_tool": "scan-observable",
                "judged_reading": "content-evaluation", "evaluation": "content-evaluation",
                "declaration": "not web-observable", None: "unassigned"}[basis]
        assert verdict == f"**{want}**", f"{code}: {verdict} for basis {basis}"
        assert cells[2] == (p.get("measurement_tier") or "—"), code
        if want == "scan-observable":
            assert "reaches" in why or "no collector reaches this yet" in why, (code, why)


def test_the_tool_map_lists_every_indicator_with_its_tier(indicators):
    text = TOOL_MAP.read_text(encoding="utf-8")
    section = text.split("## 4.")[1]
    listed = {line.strip("|").split("|")[0].strip() for line in section.splitlines()
              if line.startswith("| ") and not line.startswith("| code")}
    assert listed == set(indicators)


def test_the_product_matrix_does_not_carry_the_host_level_withdrawal():
    """Decision 5. G1-D left the HOST-level instrument (DD-066) and is measured on product
    surfaces; a product matrix saying it withdrew G1-D says the opposite of the record."""
    import build_l0_site
    import yaml
    pub = yaml.safe_load((REPO / "docs" / "reports" / "publication.yaml")
                         .read_text(encoding="utf-8"))
    suffix = build_l0_site.cycle_suffix(pub["snapshot_cycle"])
    product = json.loads(build_l0_site.matrix_path("product", suffix).read_text("utf-8"))
    host = json.loads(build_l0_site.matrix_path("tierA", suffix).read_text("utf-8"))
    assert "legs_withdrawn" not in product
    assert [w["leg"] for w in host["legs_withdrawn"]] == ["G1-D"]
