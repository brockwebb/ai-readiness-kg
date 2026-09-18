"""The cycle template, and the one claim that has to be asserted on this side.

`cc_tasks/2026-09-16_cadence_and_enable.md` §2: *a test that the template renders to a file
`seldon dispatch status` reports as a candidate with `ok c5` by cadence.*

**Why here and not in Seldon.** Seldon's suite tests the cadence mechanism against fixture
templates it writes itself. What it cannot test is *this* template — the real one, with the real
headers, rendered under the real `seldon.yaml` entry. That claim is about this project's
artifacts, and it is the claim that matters: the mechanism being correct is worth nothing if the
file it renders every month is not a task the dispatcher will accept.

The evaluation runs against a **temporary git checkout** holding the rendered instance and this
project's own `dispatch:` block, rather than against the working tree. Writing a rendered
instance into `cc_tasks/` to test it would create a file the cadence's own instance check would
then read as "this period is already served" — a test that suppressed the thing it tests.

Zero spend, no network, no Neo4j: `D.evaluate` is the same function `seldon dispatch status`
prints, so asserting on it asserts on what `status` would say.

**Since 2026-09-18 the template is rendered on request, not on a schedule**
(`cc_tasks/2026-09-18_cadence_off.md`, DN-006 ADDENDUM_07). `dispatch.cadence` is empty, so the
render parameters the entry used to carry are stated below as `ON_REQUEST`. They are the values of
the command in `cc_tasks/2026-09-18_cadence_off_RESULT.md` §1, and this file tests that command's
output.
"""
from __future__ import annotations

import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, "/Users/brock/GitHub/seldon")

from seldon.core import cadence as C           # noqa: E402
from seldon.core import dispatch as D          # noqa: E402

DISPATCH = yaml.safe_load((REPO / "seldon.yaml").read_text(encoding="utf-8"))["dispatch"]

#: The entry the on-request render command uses: the four fields the scheduled `scan_cycle` entry
#: carried before 2026-09-18, less its rule. They are stated here because no config carries them
#: any more. `seldon cadence render` (Seldon issue `2026-09-18_cadence_render_on_request`) is the
#: fix that puts them back in config.
ON_REQUEST = {"name": "scan_cycle", "template": "cc_tasks/templates/scan_cycle.md",
              "instances_dir": "cc_tasks", "cycle_name_format": "scan_{date}"}
TEMPLATE_PATH = REPO / ON_REQUEST["template"]

#: A requested cycle's period is its UTC date, so two requested in one month cannot collide on
#: the instance glob. The instant is the day the schedule was turned off.
CREATED_AT = datetime(2026, 9, 18, 12, 0, tzinfo=timezone.utc)
PERIOD = "2026-09-18"


def _render() -> tuple[str, str]:
    """The template rendered as the cadence would render it. Returns (stem, text)."""
    stem = C.instance_stem(ON_REQUEST, PERIOD, CREATED_AT)
    text = C.render(
        TEMPLATE_PATH.read_text(encoding="utf-8"),
        cycle_name=C.cycle_name_for(ON_REQUEST, CREATED_AT), period=PERIOD,
        cadence_name=ON_REQUEST["name"],
        created_at=CREATED_AT.isoformat().replace("+00:00", "Z"),
        instance_stem=stem)
    return stem, text


# ============================================================== the entry and the template

def test_the_template_exists_under_cc_tasks_templates():
    assert TEMPLATE_PATH.is_file(), f"{ON_REQUEST['template']} does not exist"
    assert ON_REQUEST["template"].startswith("cc_tasks/templates/")


def test_the_cadence_list_is_empty_and_loads():
    """Decision 1 of `cc_tasks/2026-09-18_cadence_off.md`: the schedule is off. An empty list is
    a valid config, and the dispatcher stays enabled for hand-written and requested tasks."""
    assert DISPATCH["cadence"] == []
    cfg = D.load_dispatch_config(REPO)
    assert cfg["cadence"] == []
    assert cfg["enabled"] is True


def test_the_template_says_a_cycle_runs_on_request():
    """Decision 2: the sentence calling a human-dated cycle the defect is gone. The sentence that
    replaces it says a cycle's date is the day it was rendered."""
    text = TEMPLATE_PATH.read_text(encoding="utf-8")
    assert "dated by human attention" not in text
    assert ("A cycle runs when the operator asks for one,\nand its date is the day it was "
            "rendered.") in text


def test_the_template_names_no_placeholder_the_renderer_does_not_define():
    """A `{typo}` in a template is shipped silently and rendered unattended every month. The
    only chance anybody has to notice is a test."""
    assert C.unknown_placeholders(TEMPLATE_PATH.read_text(encoding="utf-8")) == []


def test_the_rendered_instance_has_no_unsubstituted_placeholder_left():
    _stem, text = _render()
    for field in C.TEMPLATE_FIELDS:
        assert "{" + field + "}" not in text


def test_the_rendered_instance_names_the_cycle_the_period_and_its_own_stem():
    stem, text = _render()
    assert stem == "2026-09-18_scan_cycle_2026-09-18"
    assert "scan_2026-09-18" in text
    assert PERIOD in text
    assert f"cc_tasks/{stem}_RESULT.md" in text


def test_the_result_path_in_the_template_is_the_one_the_finish_check_looks_for():
    """The dispatcher's finish check reads `cc_tasks/<stem>_RESULT.md`. A template that named
    its RESULT anything else would produce a cycle that ran, wrote its RESULT, and was marked
    `blocked` on a filename — every month, silently. DN-006 ADDENDUM_02 §2."""
    stem, text = _render()
    named = set(re.findall(r"cc_tasks/([\w\-.]+)_RESULT\.md", text))
    assert named == {stem}, f"the template names RESULT file(s) {named}, not {stem}"


# ===================================================== what `seldon dispatch status` would say

@pytest.fixture
def rendered_checkout(tmp_path) -> tuple[Path, str]:
    """A git checkout holding the rendered instance and this project's real dispatch block."""
    p = tmp_path / "repo"
    (p / "cc_tasks").mkdir(parents=True)
    for a in (["init", "-b", "main"], ["config", "user.email", "t@t"],
              ["config", "user.name", "t"]):
        subprocess.run(["git", *a], cwd=p, check=True, capture_output=True)
    (p / ".gitignore").write_text(".seldon/\nlogs/\n", encoding="utf-8")
    (p / "controls.yaml").write_text((REPO / "controls.yaml").read_text(encoding="utf-8"),
                                     encoding="utf-8")
    # The real block, with `enabled` forced true: c8 is a property of the switch, not of the
    # template, and `test_the_dispatch_block_is_complete_and_ships_disabled` in
    # `test_dispatch_config.py` is what asserts the switch's own value.
    (p / "seldon.yaml").write_text(
        yaml.safe_dump({"dispatch": {**DISPATCH, "enabled": True}}), encoding="utf-8")
    stem, text = _render()
    (p / "cc_tasks" / f"{stem}.md").write_text(text, encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=p, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "rendered"], cwd=p, check=True, capture_output=True)
    return p, stem


def _evaluate(checkout: Path, stem: str) -> dict:
    cfg = D.load_dispatch_config(checkout)
    band = D.resolve_standing_band(checkout, cfg["standing_band_ref"])
    row = {"artifact_id": "cycle5-task", "name": stem, "state": "proposed",
           "source_file": f"cc_tasks/{stem}.md", "created_at": "2026-09-18T12:00:00Z",
           "predecessors": []}
    return D.evaluate(checkout, row, cfg, band, D.tree_state(checkout), None, {})


def test_the_rendered_instance_is_a_candidate_on_all_three_headers(rendered_checkout):
    """DN-006 decision 2 plus its ADDENDUM_01. A task file without the three headers is NOT A
    CANDIDATE — the opt-in — so the first thing a monthly template has to be is a file that
    carries them."""
    checkout, stem = rendered_checkout
    cand = D.candidacy(checkout / "cc_tasks" / f"{stem}.md")
    assert cand["candidate"] is True, cand["reason"]
    assert cand["headers"][D.HEADER_SPEND] and cand["headers"][D.HEADER_NETWORK]
    assert cand["headers"][D.HEADER_LAYER].startswith("§2.2 Tier M")


def test_status_would_report_it_eligible_with_ok_c5_by_cadence(rendered_checkout):
    """§2's assertion. c5 admits `**Network:** none` **or** a task created by the cadence rule
    (DN-006 decision 2, c5's second limb). A measurement cycle contacts federal hosts and may
    not claim `none`; the licensed form is `hosts, under cadence <name>`, and that is what
    makes this eligible."""
    checkout, stem = rendered_checkout
    row = _evaluate(checkout, stem)
    assert row["candidate"] is True
    assert row["criteria"]["c5"]["ok"] is True
    assert "under cadence scan_cycle" in row["criteria"]["c5"]["network_header"]
    assert row["eligible"] is True, row.get("failed")


def test_the_cycle_declares_zero_spend_and_sits_under_the_standing_band(rendered_checkout):
    """A cycle is a fetch, a judgement and a projection. Nothing in it calls a model, and c4
    reads that off the header rather than trusting the prose."""
    checkout, stem = rendered_checkout
    c4 = _evaluate(checkout, stem)["criteria"]["c4"]
    assert c4["declared_tokens"] == 0 and c4["ok"] is True
    assert c4["band_ref"] == "controls.yaml#spend.daily_tokens"


def test_no_addendum_makes_the_rendered_instance_superseded(rendered_checkout):
    checkout, stem = rendered_checkout
    c3 = _evaluate(checkout, stem)["criteria"]["c3"]
    assert c3["superseding"] is None and c3["ok"] is True


# ============================================ what the template promises it will NOT do (DN-004)

def test_the_template_says_in_its_own_body_that_it_moves_no_published_view():
    """Decision 2 of the task: a reader of cycle 5's task file must be able to see what it will
    not do without going to DN-004 to find out. A new measured cycle lands on the log and in the
    matrices; promoting it to the published snapshot is a decision that stays with the Desktop
    OODA until DN-005 §4 items 2 and 3 exist."""
    _stem, text = _render()
    lowered = text.lower()
    assert "dn-004" in lowered
    assert "does not move the published report's snapshot" in lowered
    for promise in ("the site's published results", "the abstract"):
        assert promise in lowered, promise


def test_the_template_carries_the_immutability_line_and_the_addendum_glob():
    _stem, text = _render()
    assert "Immutable once written" in text
    assert "_ADDENDUM*.md" in text
    assert "SEQUENCING:" in text


def test_the_template_cites_the_decisions_it_implements():
    """AD-030-R11: the dispatcher is a gated actor, so a task it files owes a design-note
    reference. A template that cited none would be refused at registration — every month, after
    rendering, with the file then removed — and the cadence would silently never produce a
    cycle."""
    _stem, text = _render()
    for ref in ("DD-060", "DN-006", "DN-003", "DN-004", "DN-005"):
        assert ref in text, ref
    from seldon.core.governed import references_a_design_note
    assert references_a_design_note(text)


def test_the_template_runs_the_instrument_as_params_binds_it_and_changes_no_rule():
    """Decision 1 of the template: a cycle is a measurement, not an instrument change. The
    five-leg host-level instrument after DD-066 is named in the body so a reader of any
    instance knows what was measured without opening `params.yaml` for that month."""
    _stem, text = _render()
    assert "DD-066" in text
    params = yaml.safe_load((REPO / "assessment" / "harness" / "scan" / "params.yaml")
                            .read_text(encoding="utf-8"))
    legs = params["tier0"]["legs"]
    assert len(legs) == 5, f"the template names five host-level legs; params binds {legs}"
    for leg in legs:
        assert leg in text, f"{leg} is in params.tier0.legs and not in the template"
    assert "G1-D" in text and "legs_withdrawn" in text
