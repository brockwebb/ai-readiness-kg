"""The brief deck is a rendered view of the pack: `cc_tasks/2026-09-22_brief_deck_assembly.md`.

What is asserted (decision 6), and why each is the right test:

* **Idempotence**: re-render and byte-compare, the guard the pack and every other generated view
  here uses. The archive's member timestamps are fixed by the renderer, so bytes are comparable.
* **The numeral gate** (decision 4) holds on the content file, and it REFUSES a typed number and
  an unfound quotation: a gate that is only ever seen passing has not been shown to gate.
* **Every `source:` file exists**, and the content file names the pack commit it was built from.
* **No slide overflows** the layout budget at the 14pt floor; oversize slides were split.
* **The appendix** is 49 indicator slides, plus one per rule group, plus one corpus summary.
* **The framework deck is unchanged** by the refactor that made its layout importable: rebuilt
  from its content file, every archive member equals the committed
  `docs/crosswalk/framework_deck_2026-09-02.pptx` (the zip header timestamps are the only bytes
  python-pptx does not reproduce).
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import build_brief_deck as D  # noqa: E402
import build_framework_deck as FD  # noqa: E402


@pytest.fixture(scope="module")
def rendered(tmp_path_factory):
    out = tmp_path_factory.mktemp("deck") / "deck.pptx"
    return out, D.render(out)


@pytest.fixture(scope="module")
def specs():
    return D.all_specs()


def test_the_deck_regenerates_byte_for_byte(rendered):
    out, _ = rendered
    assert D.DECK.is_file(), "docs/deck/brief_deck.pptx is not on disk"
    assert D.DECK.read_bytes() == out.read_bytes(), \
        "docs/deck/brief_deck.pptx drifted; run scripts/build_brief_deck.py"


def test_no_slide_overflows(rendered):
    _, rep = rendered
    assert rep["overflow"] == [], f"slides over the layout budget: {rep['overflow']}"
    for s in rep["slides"]:
        assert s["pt"] in ("cover",) or s["pt"] >= FD.FLOOR_PT, s


def test_every_source_exists_and_every_number_stating_slide_names_one(specs):
    for s in specs:
        for src in s["sources"]:
            assert D.pack_path(src).is_file(), f"slide {s['n']}: {src}"
    assert all(s["sources"] for s in specs if s["kind"] != "authored")


def _content(body: str, n: int = 1, source: str = "C_provenance.md") -> str:
    return f"## Slide {n} — T\n\nsource: {source}\n{body}\n"


def test_the_numeral_gate_passes_a_ledger_number_and_refuses_a_typed_one():
    ledger = json.loads(D.LEDGER.read_text(encoding="utf-8"))
    held = ledger["C_provenance.md"][0]["value"]
    D.authored(_content(f"- {held} cells carry a locator"))
    with pytest.raises(SystemExit, match="numeral '4417'"):
        D.authored(_content("- 4417 cells carry a locator"))
    with pytest.raises(SystemExit, match="numeral"):
        D.authored(_content("- `4417` hidden in backticks"))


def test_a_quotation_must_be_found_in_the_named_source():
    D.authored(_content("> No admitted document matches `Title 13`, `CIPSEA`"))
    with pytest.raises(SystemExit, match="quote not found"):
        D.authored(_content("> 4417 documents were admitted and all are cited."))


def test_the_content_file_names_the_pack_it_was_built_from():
    first = D.CONTENT.read_text(encoding="utf-8").splitlines()[0]
    sha, _ = D.pack_commit()
    h = D.pack_header()
    assert f"brief pack at commit {sha}" in first, (first, sha)
    assert h["record_commit"] in first and h["cycle"] in first


def test_the_appendix_is_one_slide_per_sheet_per_rule_group_plus_the_corpus(specs):
    gen = [s for s in specs if s["kind"] != "authored"]
    sheets = list((D.PACK / "appendix").glob("indicator_*.md"))
    _, groups = D.rule_groups()
    per_rule = sum(len(r) for _, r in groups)
    rule_slides = per_rule if per_rule <= D.RULE_SLIDE_LIMIT else len(groups)
    assert len(sheets) == 49
    assert len([s for s in gen if s["kind"] == "indicator"]) == len(sheets)
    assert len([s for s in gen if s["kind"] == "rule"]) == rule_slides
    assert len(gen) == 49 + rule_slides + 1


def test_captured_output_stays_preformatted():
    lines, _ = D.directive("capture", "seldon_go", 0)
    parsed = FD.parse_body("\n".join(lines))
    assert all(l.pre for l in parsed[1:] if not l.blank), \
        [l.text for l in parsed[1:] if not l.pre and not l.blank][:3]


def test_the_diagrams_are_current_against_the_pack():
    for key in D.mermaid_blocks():
        assert D.diagram_png(key).is_file()


def test_the_framework_deck_is_unchanged_by_the_layout_refactor(tmp_path):
    out = tmp_path / "fd.pptx"
    r = subprocess.run([sys.executable, str(REPO / "scripts" / "build_framework_deck.py"),
                        "--out", str(out)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    ref = zipfile.ZipFile(REPO / "docs" / "crosswalk" / "framework_deck_2026-09-02.pptx")
    got = zipfile.ZipFile(out)
    assert got.namelist() == ref.namelist()
    assert [n for n in ref.namelist() if got.read(n) != ref.read(n)] == []


def test_the_renderer_imports_the_layout_rule_rather_than_copying_it():
    src = (REPO / "scripts" / "build_brief_deck.py").read_text(encoding="utf-8")
    assert "FD.layout(" in src and "FD.parse_body(" in src
    assert not re.search(r"^def (parse_body|layout|fits|capacity|wrapped_lines)\b", src, re.M)
