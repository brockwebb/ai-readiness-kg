"""The scan catalog (`cc_tasks/2026-10-02_scan_catalog.md` + ADDENDUM-01, DN-009, DN-010).

What the task file and its addendum ask the tests to hold, each with the control that shows the
check can fail:

* the generator is idempotent and the files on disk are what it renders now (`--check`);
* every row's indicator exists in the framework record; every Action in the record has a row;
* every `tool_*` row has a URL and a locator; every `none_known` row lists the searches that failed;
* no value lies outside the closed vocabularies (README "Closed vocabularies");
* every rated row has a `value_basis`, and an unrated row says `TBD`;
* the rollup counts and the DN-010 grids' cell counts equal the row counts;
* no score, rank or bound code path can read a value column (a static scan of the scoring
  modules and everything they import from this repository);
* every corpus quote in the declared inputs is verbatim in the admitted text, wherever the
  corpus file is on disk (`corpus/` is gitignored, so a fresh checkout skips that test only).

Pure file reads: no network, no graph, no model.
"""
from __future__ import annotations

import ast
import csv
import sys
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import build_scan_catalog as C  # noqa: E402
from kg.extraction.grounding import is_grounded  # noqa: E402

CAT = REPO / "docs" / "catalog"
ROLL = CAT / "rollups"
NUMERIC = {"1", "2", "3", "4", "5"}


def read(path: Path) -> list:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


@pytest.fixture(scope="module")
def built():
    return C.build()


@pytest.fixture(scope="module")
def scans():
    return read(CAT / "scan_catalog.csv")


@pytest.fixture(scope="module")
def actions():
    return read(CAT / "actions.csv")


@pytest.fixture(scope="module")
def record():
    import json
    return json.loads(C.RECORD.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def inputs():
    return yaml.safe_load(C.INPUTS.read_text(encoding="utf-8"))


# ------------------------------------------------------------------------------ idempotence

def test_files_on_disk_are_what_the_generator_renders(built):
    drift = [str(p.relative_to(REPO)) for p, text in built.items()
             if not p.is_file() or p.read_text(encoding="utf-8") != text]
    assert drift == [], f"regenerate with scripts/build_scan_catalog.py: {drift}"


def test_a_second_render_is_identical(built):
    assert C.build() == built


# ------------------------------------------------------------------------------ the record

def test_every_row_indicator_exists_in_the_record(scans, actions, record):
    codes = {n["properties"]["code"] for n in record["nodes"]
             if "AssessmentIndicator" in n["labels"]}
    assert {r["indicator"] for r in scans} <= codes
    assert {r["indicator"] for r in actions} <= codes
    for r in actions:
        for c in filter(None, r["also_moves"].split(";")):
            assert c in codes


def test_every_indicator_has_at_least_one_scan_row(scans, record):
    codes = {n["properties"]["code"] for n in record["nodes"]
             if "AssessmentIndicator" in n["labels"]}
    assert codes - {r["indicator"] for r in scans} == set()


def test_every_action_in_the_record_has_a_row(actions, record):
    ids = {n["id"] for n in record["nodes"] if "Action" in n["labels"]}
    assert ids <= {r["action_id"] for r in actions}
    assert all(r["row_source"] == "record" for r in actions if r["action_id"] in ids)


def test_every_requires_route_has_a_row(scans, record):
    routes = {(e["from"].removeprefix("ind:"), e["properties"]["route"])
              for e in record["edges"] if e["type"] == "REQUIRES"}
    have = {(r["indicator"], r["route"]) for r in scans}
    assert routes <= have


def test_q6_bounds_are_read_not_recomputed(actions):
    claims = yaml.safe_load(C.CLAIMS.read_text(encoding="utf-8"))["claims"]
    q6 = {"act:" + c["key"].removeprefix("q6."): (c["numbers"][0]["value"], c["id"])
          for c in claims if c["question"] == "Q6"}
    assert q6, "the evidence map holds no Q6 claims"
    by_id = {r["action_id"]: r for r in actions}
    for act, (bound, cid) in q6.items():
        assert (by_id[act]["bound_equal_weights_census"], by_id[act]["bound_claim"]) == (bound, cid)
    for r in actions:
        if r["action_id"] not in q6:
            assert r["bound_equal_weights_census"] == "TBD" and "bound:" in r["basis"]


# ------------------------------------------------------------------------------ decision 3

def test_every_tool_row_has_a_url_and_a_locator(scans):
    tools = [r for r in scans if r["method_kind"].startswith("tool_")]
    assert tools
    for r in tools:
        assert r["url"].startswith("https://"), r["row_id"]
        assert r["locator"].strip(), r["row_id"]


def test_every_roll_your_own_row_names_its_specification(scans):
    for r in scans:
        if r["method_kind"] == "roll_your_own":
            assert r["method"].strip() and (r["spec_locator"] or r["locator"]).strip(), r["row_id"]


def test_every_none_known_row_lists_failed_searches(scans):
    nk = [r for r in scans if r["method_kind"] == "none_known"]
    assert nk
    for r in nk:
        assert r["failed_searches"].strip(), r["row_id"]


def test_every_built_rule_row_names_a_rule(scans):
    for r in scans:
        if r["method_kind"] == "built_rule":
            assert r["rule_id"].startswith("RULE-"), r["row_id"]


# ------------------------------------------------------------------------------ vocabularies

def test_no_value_outside_the_closed_vocabularies(scans, actions):
    for r in scans:
        assert r["who_can_run"] in C.WHO, r["row_id"]
        assert r["method_kind"] in C.METHOD, r["row_id"]
        assert r["row_source"] in C.ROW_SOURCE, r["row_id"]
        assert r["q1_class"] in C.Q1, r["row_id"]
    for r in scans + actions:
        rid = r.get("row_id") or r["action_id"]
        assert r["cheap_pass"] in C.CHEAP, rid
        assert r["evidence_grade"] in C.GRADE, rid
        assert r["value_basis"] in C.VALUE_BASIS, rid
        for col in ("staffing_band", "cost_band", "effort_level", "value_rating"):
            assert r[col] in C.BAND, (rid, col, r[col])
        assert r["operator_override"] == "", rid
        assert r["rated_by"].startswith("rubric v1"), rid
    assert {r["row_source"] for r in actions} <= set(C.ROW_SOURCE)


def test_blocked_is_never_a_who_value(scans):
    assert "blocked" not in {r["who_can_run"] for r in scans}


def test_enabler_links_are_in_the_vocabulary_and_status_follows_them():
    rows = read(CAT / "enablers.csv")
    assert rows
    by = {}
    for r in rows:
        assert r["link"] in C.LINK
        by.setdefault(r["enabler_id"], []).append(r)
    for eid, rs in by.items():
        supported = any(r["link"] in ("existing_node", "proposed_link") for r in rs)
        assert {r["status"] for r in rs} == {"supported" if supported else "unsupported"}, eid


def test_existing_node_links_join_through_a_requires_edge(record, inputs):
    rows = read(CAT / "enablers.csv")
    req = {(e["from"], e["to"]) for e in record["edges"] if e["type"] == "REQUIRES"}
    for r in rows:
        if r["link"] == "existing_node":
            nodes = r["requirement_nodes"].split(";")
            assert any((f"ind:{r['indicator']}", n) in req for n in nodes), r


# ------------------------------------------------------------------------------ value and effort

def test_every_rated_row_has_a_value_basis(scans, actions):
    for r in scans + actions:
        rid = r.get("row_id") or r["action_id"]
        if r["value_rating"] in NUMERIC:
            assert r["value_basis"] in ("evidence", "rubric"), rid
            assert r["value_reason"].strip(), rid
        else:
            assert r["value_basis"] == "TBD", rid


def test_effort_level_is_the_higher_band_or_tbd(scans, actions):
    for r in scans + actions:
        s, c = r["staffing_band"], r["cost_band"]
        want = "TBD" if "TBD" in (s, c) else str(max(int(s), int(c)))
        assert r["effort_level"] == want


def test_a_tbd_band_carries_a_basis(scans, actions):
    for r in scans + actions:
        if "TBD" in (r["staffing_band"], r["cost_band"]):
            assert r["band_basis"].strip()


def test_every_value_rating_is_declared_before_use(inputs, record):
    codes = {n["properties"]["code"] for n in record["nodes"]
             if "AssessmentIndicator" in n["labels"]}
    assert set(inputs["value"]) == codes


def test_llms_txt_row_reports_the_measurement_not_the_proposal(actions):
    row = next(r for r in actions if r["action_id"] == "named:llms-txt")
    assert row["evidence_grade"] == "unevidenced"
    assert row["value_basis"] == "evidence" and row["value_rating"] == "1"
    assert "ahrefs_llmstxt_2026" in row["evidence_sources"]


def test_robots_txt_rows_cite_rfc_9309_and_the_operators(actions, inputs):
    rows = [r for r in actions if r["named_row"] == "robots_txt"]
    assert len(rows) == len(inputs["named_rows"]["robots_txt"]["tags"])
    probed = set()
    for k in inputs["named_rows"]["robots_txt"]["citations"]:
        probed |= set(inputs["sources"][k].get("user_agents", []))
    params = C.load_params()
    uas = None
    for v in params.values():
        if isinstance(v, dict) and "user_agents" in v:
            uas = v["user_agents"]
    assert uas, "params.yaml names no AI-crawler user agents"
    missing = set(uas) - probed
    # Claude-Web is not named in the Anthropic article; the README and the inputs say so.
    assert missing <= {"Claude-Web"}, missing


# ------------------------------------------------------------------------------ rollups

def test_rollup_counts_equal_row_counts(scans, actions):
    cbw = read(ROLL / "criterion_by_who.csv")
    assert next(r for r in cbw if r["criterion"] == "total")["total"] == str(len(scans))
    assert sum(int(r["total"]) for r in cbw if r["criterion"] != "total") == len(scans)
    for w in C.WHO:
        assert sum(int(r[w]) for r in cbw if r["criterion"] != "total") == \
            sum(r["who_can_run"] == w for r in scans)
    sbc = read(ROLL / "staffing_by_cost.csv")
    for table, rows in (("scans", scans), ("actions", actions)):
        t = [r for r in sbc if r["table"] == table]
        assert next(r for r in t if r["staffing_band"] == "total")["total"] == str(len(rows))
        assert sum(int(r[b]) for r in t if r["staffing_band"] != "total" for b in C.BAND) == \
            len(rows)


def test_grid_cell_counts_equal_row_counts(scans, actions):
    for name, rows, key in (("matrix_scans.csv", scans, "row_id"),
                            ("matrix_actions.csv", actions, "action_id")):
        g = read(ROLL / name)
        placed = [r for r in g if "TBD" not in (r["effort_level"], r["value_rating"])]
        side = [r for r in g if "TBD" in (r["effort_level"], r["value_rating"])]
        assert len(placed) == 25
        assert sum(int(r["n"]) for r in placed) + len(side) == len(rows)
        ids = [i for r in placed for i in filter(None, r["row_ids"].split(";"))] + \
              [r["row_ids"] for r in side]
        assert sorted(ids) == sorted(r[key] for r in rows)
        for r in side:
            assert r["reason"].strip()


def test_unlocker_counts_equal_rows(scans):
    unl = read(ROLL / "unlockers.csv")
    for u in unl:
        rs = [r for r in scans if r["unlocked_by"] == u["unlocked_by"]]
        assert int(u["n_rows"]) == len(rs)
        assert set(u["indicators"].split(";")) == {r["indicator"] for r in rs}


def test_set_cover_covers_what_it_says(scans, record):
    steps = read(ROLL / "set_cover.csv")
    rest = read(ROLL / "set_cover_uncovered.csv")
    unmeasured = {n["properties"]["code"] for n in record["nodes"]
                  if "AssessmentIndicator" in n["labels"]
                  and n["properties"]["measurement_status"] != "measured"
                  and not n["properties"].get("candidate_rationale")}
    covered = set()
    for s in steps:
        new = set(s["newly_covered"].split(";"))
        assert not new & covered and new <= unmeasured
        covered |= new
        assert s["cumulative"] == str(len(covered))
    assert covered | {r["indicator"] for r in rest} == unmeasured
    assert not covered & {r["indicator"] for r in rest}


def test_quick_wins_obey_the_cell_definitions():
    for r in read(ROLL / "quick_wins.csv"):
        e, v = int(r["effort_level"]), int(r["value_rating"])
        assert e <= 2
        assert (v >= 4) if r["list"] == "quick_win" else (v <= 2)


def test_every_rendering_with_a_value_carries_the_dn010_label():
    for p in (CAT / "scan_catalog.md", CAT / "actions.md", ROLL / "rollups.md", CAT / "README.md"):
        text = p.read_text(encoding="utf-8")
        assert ("rated judgment under a stated rubric" in text), p


# ------------------------------------------------------------------------------ front door

def test_front_door_covers_every_body_and_infers_nothing():
    rows = read(CAT / "front_door.csv")
    assert len(rows) == 19 and sum(r["tier"] == "A" for r in rows) == 16
    for r in rows:
        if r["front_door_observed"] == "not_observed_in_record":
            assert r["n_observations_naming"] == "0" and r["observation_ids"] == ""
        else:
            assert int(r["n_observations_naming"]) > 0 and r["observation_ids"].startswith("obs_")
    text = (CAT / "front_door.csv").read_text(encoding="utf-8").lower()
    for word in ("because", "no cdn", "blocked"):
        assert word not in text


# ------------------------------------------------------------------------------ DN-010 §2.1

#: The modules that compute the score, the rank and the bound (DN-009 decision 3, Q6).
SCORING_ENTRY = ("scripts/score.py", "scripts/prescriptions.py", "scripts/build_evidence_map.py")
FORBIDDEN = ("value_rating", "value_basis", "catalog_inputs", "docs/catalog", "scan_catalog")
LOCAL_ROOTS = ("scripts", "assessment/harness", "mcp", "")


def _local_imports(path: Path) -> set:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names |= {a.name for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            names.add(node.module)
    out = set()
    for name in names:
        rel = Path(*name.split("."))
        for root in LOCAL_ROOTS:
            for cand in (REPO / root / rel.with_suffix(".py"), REPO / root / rel / "__init__.py"):
                if cand.is_file():
                    out.add(cand.resolve())
    return out


def scoring_closure() -> set:
    seen, todo = set(), [(REPO / p).resolve() for p in SCORING_ENTRY]
    while todo:
        p = todo.pop()
        if p in seen:
            continue
        seen.add(p)
        todo.extend(_local_imports(p) - seen)
    return seen


def mentions(text: str) -> list:
    return [w for w in FORBIDDEN if w in text]


def test_no_score_rank_or_bound_module_reads_a_value_column():
    closure = scoring_closure()
    assert (REPO / "scripts/score.py").resolve() in closure
    assert len(closure) > len(SCORING_ENTRY), "the import walk found nothing it imports"
    hits = {str(p.relative_to(REPO)): mentions(p.read_text(encoding="utf-8")) for p in closure}
    assert {k: v for k, v in hits.items() if v} == {}


def test_the_static_scan_would_catch_a_mention():
    """Negative control: the scan is not vacuous."""
    assert mentions("weights = row['value_rating']") == ["value_rating"]
    assert mentions("import yaml; yaml.safe_load(open('docs/catalog/catalog_inputs.yaml'))")


# ------------------------------------------------------------------------------ the quotes

def _corpus_quotes(inputs) -> list:
    out = []
    for key, s in inputs["sources"].items():
        if s["kind"] == "corpus":
            out.append((key, s["path"], s["quote"]))
    srcs = inputs["enabler_sources"]
    for en in inputs["enablers"]:
        for item in [en["step"]] + en["capabilities"]:
            s = srcs.get(item["source"]) or inputs["sources"].get(item["source"])
            if s["kind"] == "corpus" and item["quote"]:
                out.append((f"{en['id']}:{item['source']}", s["path"], item["quote"]))
    return out


def test_every_corpus_quote_is_verbatim(inputs):
    quotes = _corpus_quotes(inputs)
    assert quotes
    present = [(k, p, q) for k, p, q in quotes if (REPO / p).is_file()]
    if not present:
        pytest.skip("corpus/ is gitignored and not on disk in this checkout")
    misses = [(k, q) for k, p, q in present
              if not is_grounded(q, (REPO / p).read_text(encoding="utf-8"))]
    assert misses == []


def test_the_grounding_check_would_catch_a_paraphrase(inputs):
    """Negative control: a reworded quote fails."""
    k, p, q = _corpus_quotes(inputs)[0]
    if not (REPO / p).is_file():
        pytest.skip("corpus/ is not on disk in this checkout")
    assert not is_grounded(q.replace(" ", "  X ", 1), (REPO / p).read_text(encoding="utf-8"))


def test_every_third_party_quote_is_under_fifteen_words(inputs):
    for key, s in inputs["sources"].items():
        if s["kind"] in ("corpus", "corpus_pdf", "web"):
            assert len(s["quote"].split()) < 15, key
    for en in inputs["enablers"]:
        for item in [en["step"]] + en["capabilities"]:
            assert len(item["quote"].split()) < 15, (en["id"], item["quote"])
