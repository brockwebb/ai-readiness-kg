"""A rebuild does not re-date the release; G4 is sourced to the standards that define its fields.

`cc_tasks/2026-09-21_g4_resourcing_reissue.md`, which executes
`cc_tasks/2026-09-20_g4_resourcing_release_date_grounding_fold.md` decisions 1 to 8 unchanged.

* **Part B, the release date** (decisions 4 to 6). Until 2026-09-21 `scripts/build_l0_site.py`
  wrote `datetime.now` into CITATION.cff `date-released`, the Zenodo `publication_date`, the
  sitemap `lastmod`, the index page and the data manifest's `built_at`; the report's version
  block and the PDF's `/CreationDate` did the same. A locator edit rebuilt the tree on
  2026-09-20 and moved the release date of record from 2026-09-19 with the version unchanged.
  The prior art is reproducible builds: every embedded date comes from the source, never the
  clock (reproducible-builds.org, `SOURCE_DATE_EPOCH`). The test is the one that definition
  implies — two builds of one tree with the clock set a day apart are byte-identical — plus the
  regenerate-and-compare gate against the committed tree (`go generate` then `git diff
  --exit-code`), which is what makes it a guard rather than a property of one afternoon.

* **Part A, G4's sources** (decisions 1 to 3). The quotes themselves are grounded by
  `tests/test_g4_locators_and_progress_drift.py`, whose `G4_DOCS` now names all nine documents
  and whose renderings now include the HTML substrate. What is asserted here is the shape the
  decisions require of the cell: the document the rule's own spec names as prior art is cited
  on the indicator; the DCAT-AP property is cited by analogy and says so; the AI-ranker clause
  is marked as the framework's own inference; and every cited document is admitted.
"""
from __future__ import annotations

import ast
import datetime as _dt
import importlib
import json
import re
import shutil
import sys
import time as _time
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "assessment" / "harness"))
sys.path.insert(0, "/Users/brock/GitHub/seldon")

PUB = yaml.safe_load((REPO / "docs" / "reports" / "publication.yaml").read_text(encoding="utf-8"))

#: The builders whose output is published. Each is read as source and must not consult the
#: clock; `build_report_pdf.render_env` imports `datetime` to turn the DECLARED date into an
#: epoch and calls nothing that reads the time.
BUILDERS = ["scripts/build_l0_site.py", "scripts/build_l0_report.py",
            "scripts/build_report_pdf.py"]

#: Calls that read the wall clock. `datetime.now`, `datetime.utcnow`, `datetime.today`,
#: `date.today`, `time.time`, `time.gmtime`/`localtime` with no argument, `time.strftime` with
#: one argument (it formats the current time).
CLOCK_ATTRS = {"now", "utcnow", "today", "time", "time_ns"}


def _clock_calls(path: Path) -> list:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    out = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        attr = node.func.attr
        if attr in CLOCK_ATTRS:
            out.append(f"{path.name}:{node.lineno} .{attr}()")
        elif attr in {"gmtime", "localtime"} and not node.args:
            out.append(f"{path.name}:{node.lineno} .{attr}()")
        elif attr == "strftime" and isinstance(node.func.value, ast.Name) \
                and node.func.value.id == "time" and len(node.args) == 1:
            out.append(f"{path.name}:{node.lineno} time.strftime(fmt)")
    return out


# ------------------------------------------------------------------ part B: no clock, anywhere
@pytest.mark.parametrize("rel", BUILDERS)
def test_no_published_builder_reads_the_clock(rel):
    """The structural half. Any date a builder writes must come from the declaration; a call
    that reads the time is how the release came to be re-dated by a locator edit."""
    calls = _clock_calls(REPO / rel)
    assert not calls, (f"{rel} reads the clock: {calls}. Every published date comes from "
                       f"publication.yaml's `released[version]` (build_l0_site.release_date)")


def test_the_clock_guard_sees_the_calls_it_was_built_for(tmp_path):
    """The negative control: the three spellings the builders used before 2026-09-21."""
    p = tmp_path / "old.py"
    p.write_text("from datetime import datetime, timezone\nimport time\n"
                 "a = datetime.now(timezone.utc).strftime('%Y-%m-%d')\n"
                 "b = datetime.now(timezone.utc).isoformat()\n"
                 "c = time.strftime('%Y', time.gmtime())\n"
                 "d = time.strftime('%Y')\n"
                 "e = time.strftime('%Y', time.gmtime(0))\n", encoding="utf-8")
    found = _clock_calls(p)
    # two .now(), one bare .gmtime(), one one-argument time.strftime; `gmtime(0)` and the
    # two-argument strftime format a GIVEN time and are not clock reads
    assert len(found) == 4, found


def test_the_release_date_is_declared_per_version_and_not_before_the_judgement():
    import build_l0_site as S
    assert S.release_date(PUB) == str(PUB["released"][PUB["version"]])
    with pytest.raises(SystemExit, match="declares no release date for version"):
        S.release_date({**PUB, "version": "9999-99-99_rj9"})
    with pytest.raises(SystemExit, match="release cannot precede the judgement"):
        S.release_date({**PUB, "released": {PUB["version"]: "2000-01-01"}})


def test_the_pdf_renders_under_the_declared_date(monkeypatch):
    """typst reads `SOURCE_DATE_EPOCH` for `/CreationDate` and `/ModDate`; the renderer sets it
    to midnight UTC of the release date."""
    import build_report_pdf as P
    env = P.render_env()
    day = _dt.datetime.fromtimestamp(int(env["SOURCE_DATE_EPOCH"]), tz=_dt.timezone.utc)
    assert day.strftime("%Y-%m-%d") == str(PUB["released"][PUB["version"]])
    assert (day.hour, day.minute, day.second) == (0, 0, 0)


def test_the_version_block_is_the_same_on_two_days(monkeypatch):
    import build_l0_report as B
    blocks = []
    for day in (_dt.datetime(2030, 1, 1, 12), _dt.datetime(2030, 1, 2, 12)):
        _freeze(monkeypatch, day)
        B2 = importlib.reload(B)
        blocks.append(B2.version_block(B2.load_publication()))
    monkeypatch.undo()
    importlib.reload(B)
    assert blocks[0] == blocks[1]
    assert f"released `{PUB['released'][PUB['version']]}`" in blocks[0]


def _freeze(monkeypatch, when: _dt.datetime) -> None:
    """Set the process clock to `when` for anything that asks `datetime` or `time`."""
    class Frozen(_dt.datetime):
        @classmethod
        def now(cls, tz=None):
            w = when.replace(tzinfo=_dt.timezone.utc)
            return w if tz is None else w.astimezone(tz)

        @classmethod
        def utcnow(cls):
            return when

        @classmethod
        def today(cls):
            return when

    class FrozenDate(_dt.date):
        @classmethod
        def today(cls):
            return when.date()

    monkeypatch.setattr(_dt, "datetime", Frozen)
    monkeypatch.setattr(_dt, "date", FrozenDate)
    monkeypatch.setattr(_time, "time", lambda: when.replace(tzinfo=_dt.timezone.utc).timestamp())


@pytest.fixture(scope="module")
def neo4j_up():
    try:
        from seldon.config import get_neo4j_driver, load_project_config
        cfg = load_project_config(REPO)
        driver = get_neo4j_driver(cfg)
        with driver.session(database=cfg["neo4j"]["database"]) as s:
            s.run("RETURN 1").single()
        driver.close()
    except Exception as exc:                                          # noqa: BLE001
        pytest.skip(f"Neo4j unavailable ({type(exc).__name__}); the site build reads the graph")


#: Everything `build_l0_site.build()` writes, relative to its output root. `ROOT/` is the
#: repository-root citation pair.
SITE_OUTPUTS = ["index.html", "robots.txt", "llms.txt", "sitemap.xml", ".nojekyll",
                "data/index.json", "data/sources_per_check.json", "data/results_tagged.json",
                "data/CITATION.cff", "data/zenodo.json", "data/ai_readiness_framework.json",
                "data/corpus_manifest.json", "ROOT/CITATION.cff", "ROOT/.zenodo.json"]


def _build_into(monkeypatch, root: Path, when: _dt.datetime, clocked: bool = False) -> dict:
    import build_l0_site
    _freeze(monkeypatch, when)
    S = importlib.reload(build_l0_site)
    if clocked:
        # The pre-2026-09-21 builder, in one line: the release date read off the clock.
        monkeypatch.setattr(S, "release_date",
                            lambda pub: _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d"))
    site, out_root = root / "docs", root / "ROOT"
    (site / "reports").mkdir(parents=True)
    out_root.mkdir()
    for m in (REPO / "docs" / "reports").glob("scan_matrix_*"):
        shutil.copyfile(m, site / "reports" / m.name)
    monkeypatch.setattr(S, "SITE", site)
    monkeypatch.setattr(S, "DATA", site / "data")
    monkeypatch.setattr(S, "ROOT_OUT", out_root)
    assert S.build() == 0
    return {rel: ((out_root / rel[5:]) if rel.startswith("ROOT/") else (site / rel)).read_bytes()
            for rel in SITE_OUTPUTS}


def test_two_builds_a_day_apart_are_byte_identical_and_equal_the_committed_tree(
        neo4j_up, tmp_path, monkeypatch):
    """Decision 5's test. Two builds of an unchanged tree, the clock set to two different days,
    produce byte-identical output — and that output is the committed tree, which is what makes
    this a regenerate-and-compare guard (ResearchTask `34ccb843`) rather than a determinism
    check of one afternoon. The one field excused from the committed comparison is
    `index.json`'s `build_commit`: it names the commit the build read, and a committed file
    can never name the commit that contains it."""
    a = _build_into(monkeypatch, tmp_path / "a", _dt.datetime(2030, 1, 1, 12))
    b = _build_into(monkeypatch, tmp_path / "b", _dt.datetime(2030, 1, 2, 12))
    monkeypatch.undo()
    import build_l0_site
    importlib.reload(build_l0_site)
    moved = sorted(k for k in a if a[k] != b[k])
    assert not moved, f"these outputs differ between two builds a day apart: {moved}"

    def committed(rel):
        p = (REPO / rel[5:]) if rel.startswith("ROOT/") else (REPO / "docs" / rel)
        return p.read_bytes()

    def strip_commit(raw: bytes) -> dict:
        d = json.loads(raw)
        d.pop("build_commit", None)
        return d

    stale = []
    for rel, got in a.items():
        have = committed(rel)
        if rel == "data/index.json":
            if strip_commit(got) != strip_commit(have):
                stale.append(rel)
        elif got != have:
            stale.append(rel)
    assert not stale, (f"the committed tree is not what the builder produces today: {stale}; "
                       f"rebuild with /opt/anaconda3/bin/python3 scripts/build_l0_site.py")
    assert re.fullmatch(r"[0-9a-f]{12}", json.loads(committed("data/index.json"))["build_commit"])


def test_the_two_build_guard_reports_the_drift_it_was_built_for(neo4j_up, tmp_path, monkeypatch):
    """The negative control: the same two builds with the release date wired back to the clock
    must differ, in exactly the files that carried the date on 2026-09-20."""
    a = _build_into(monkeypatch, tmp_path / "a", _dt.datetime(2030, 1, 1, 12), clocked=True)
    b = _build_into(monkeypatch, tmp_path / "b", _dt.datetime(2030, 1, 2, 12), clocked=True)
    monkeypatch.undo()
    import build_l0_site
    importlib.reload(build_l0_site)
    moved = sorted(k for k in a if a[k] != b[k])
    assert moved == ["ROOT/.zenodo.json", "ROOT/CITATION.cff", "data/CITATION.cff",
                     "data/index.json", "data/zenodo.json", "index.html", "sitemap.xml"], moved


# ------------------------------------------------------------------ part A: G4's sources
FRAMEWORK = REPO / "framework" / "ai_readiness_framework.json"


def _node(node_id: str) -> dict:
    g = json.loads(FRAMEWORK.read_text(encoding="utf-8"))
    return next(n["properties"] for n in g["nodes"] if n["id"] == node_id)


def _g4_locators() -> dict:
    import report_traceability as RT
    return RT.locators(_node("ind:G4")["evidence_raw"])


def test_the_document_the_rule_measures_against_is_cited_on_the_indicator():
    """`spec:G4` names `dcat-us-1-1-schema` as prior art for the fields RULE-G4-v1 tests
    (bureau and program codes); until 2026-09-21 the indicator cited two FCSM documents that
    define neither field. A rule and the indicator it measures cite the same definition."""
    prior = re.findall(r"`([a-z0-9][a-z0-9._-]{6,})`", _node("spec:G4")["prior_art"])
    locs = _g4_locators()
    assert prior and set(prior) <= set(locs), (prior, sorted(locs))
    loc = locs["dcat-us-1-1-schema"]
    assert "bureau" in loc.lower() and "program" in loc.lower(), loc[:200]


def test_the_dcat_ap_property_is_cited_by_analogy_and_says_so():
    loc = _g4_locators()["dcat-ap-3-0-0-r5r-vocabulary"]
    assert "by analogy" in loc.lower(), loc
    assert "applicab" in loc.lower() and "mandate" in loc.lower(), loc


def test_the_ai_ranker_clause_is_marked_as_the_frameworks_own_inference():
    raw = _node("ind:G4")["evidence_raw"]
    assert "AI rankers" in raw and "own inference" in raw, raw[-300:]


def test_every_g4_source_is_an_admitted_verified_document():
    entries = json.loads((REPO / "corpus" / "manifest.json").read_text(encoding="utf-8"))["entries"]
    bad = {d: (entries.get(d) or {}).get("integrity", {}).get("status")
           for d in _g4_locators()
           if (entries.get(d) or {}).get("screening", {}).get("decision") != "included"
           or (entries.get(d) or {}).get("integrity", {}).get("status") != "verified"}
    assert not bad, bad
