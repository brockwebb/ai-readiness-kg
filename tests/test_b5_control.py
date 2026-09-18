"""B5 has a control the cycle fires: one body, two products, one port.

`cc_tasks/2026-09-18_manners_status_and_b5_control.md` decision 3. Every other fixture serves
one product on its own port and `run.CONTROL_LEGS` excludes body legs, so E5's "every declared
control fires" held for B5 vacuously. `body_two_products` (one concept, one code on both pages)
and `body_two_products_split` (the second page codes it differently) are scanned as two surfaces
each, and B5 is judged once over each body with the function a cycle uses (`run.judge_bodies`).

Loopback and a virtual clock: the fixtures are served over real sockets and the standing rate
limit is not paid in wall time (`cc_tasks/2026-09-10_virtual_time.md`).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "assessment" / "harness"))

from scan import load_params                                        # noqa: E402
from scan.clock import VirtualClock                                 # noqa: E402
from scan.fixtures.server import MODES                              # noqa: E402
from scan.rules import body_groups, control_body_member             # noqa: E402

BODIES = ("body_two_products", "body_two_products_split")


@pytest.fixture(scope="module")
def params():
    return load_params()


@pytest.fixture(scope="module")
def controls(params, tmp_path_factory):
    """One control cycle for the module. Module-scoped fixtures are set up BEFORE the
    function-scoped autouse redirect in `conftest.py`, so this points the evidence root at a
    tmp directory itself; without it the fixture bodies went to the guard's redirect and into
    `corpus/quarantine/evidence_scan_fixture/unlicensed/` (this task's RESULT §3)."""
    from scan import model, run
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(model, "EVIDENCE_ROOT", tmp_path_factory.mktemp("b5_control_evidence"))
        return run.run_controls(params, clock=VirtualClock())


def test_the_two_body_fixtures_declare_their_products_and_nothing_else_does():
    assert {f for f, m in MODES.items() if m.get("products")} == set(BODIES)
    for f in BODIES:
        assert MODES[f]["products"] == ("/index.html", "/second.html")


def test_their_tables_are_pre_registered_with_a_b5_row(params):
    t = params["e5_control"]["expected_verdicts"]
    assert t["body_two_products"] == {"default": "pass", "B5": "pass"}
    assert t["body_two_products_split"] == {"default": "pass", "B5": "fail"}


def test_the_variants_differ_in_one_attribute_of_one_page():
    fx = REPO / "assessment" / "harness" / "scan" / "fixtures"
    a = (fx / "body_two_products" / "second.html").read_text()
    b = (fx / "body_two_products_split" / "second.html").read_text()
    assert a.replace('"termCode":"HU-OCC"', '"termCode":"OCC-2"') == b
    index = (fx / "passes_all" / "index.html").read_text()
    assert a.replace(", Second Product", "") == index


def test_the_control_gate_passes_and_b5_fires_on_both_bodies(controls):
    cf, e5, obs, ok = controls
    assert ok, e5.reason
    b5 = {f.target_doc_id: f for f in cf if f.leg == "B5"}
    assert len(b5) == 2, sorted(b5)
    verdicts = sorted(f.verdict for f in b5.values())
    assert verdicts == ["fail", "pass"]
    fail = next(f for f in b5.values() if f.verdict == "fail")
    assert "codes not shared across products" in fail.reason
    assert "HU-OCC" in fail.reason and "OCC-2" in fail.reason


def test_each_body_is_judged_over_exactly_its_two_product_surfaces(controls, params):
    cf, _e5, obs, _ok = controls
    for fixture in BODIES:
        docs = {o.target_doc_id for o in obs if o.target_doc_id.startswith(f"control:{fixture}/")}
        assert docs == {f"control:{fixture}/index.html", f"control:{fixture}/second.html"}
    [e5_rows] = [[o for o in obs if o.leg == "E5" and o.parsed["fixture"] == f]
                 for f in ("body_two_products",)]
    assert e5_rows[0].parsed["products"] == ["/index.html", "/second.html"]
    assert e5_rows[0].parsed["verdicts"]["B5"] == "pass"
    groups = body_groups("RULE-B5-v1", obs, params)
    assert len(groups) == 2
    for group in groups.values():
        assert {o.target_doc_id.rsplit("/", 1)[-1] for o in group} == {"index.html",
                                                                       "second.html"}


def test_a_one_product_control_is_never_a_body(controls, params):
    _cf, _e5, obs, _ok = controls
    assert control_body_member("control:body_two_products/second.html")
    assert not control_body_member("control:passes_all")
    singles = [o for o in obs if o.target_doc_id == "control:passes_all"]
    assert singles and body_groups("RULE-B5-v1", singles, params) == {}


def test_the_control_b5_findings_re_derive_byte_identically(controls, params):
    """A controls-only payload built from this run re-derives: the body groups `rederive`
    rebuilds from stored observations are the ones `run_controls` judged."""
    from scan.model import params_hash
    import scan.rederive as rd
    cf, e5, obs, _ok = controls
    payload = {"params_hash": params_hash(params), "findings_detail": [],
               "control_findings_detail": [f.to_dict() for f in cf] + [e5.to_dict()],
               "observations_detail": [o.to_dict() for o in obs]}
    out = rd.rederive(payload, params)
    assert out["identical"], {k: out[k] for k in ("missing_after_rederive",
                                                  "unexpected_after_rederive",
                                                  "field_mismatches")}
