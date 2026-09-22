"""The brief's material pack is a generated view: `cc_tasks/2026-09-22_brief_material_pack_v2.md`.

What is asserted, and why each is the right test:

* **Idempotence** (decision 1): regenerate and byte-compare, the guard every generated view here
  uses (`mcp/airkg_doc.py --check`, `scripts/score.py --check`; `go generate` + `git diff
  --exit-code` is the general form). The graph-free pages are compared in every run. The pages
  that read the projection are compared when Neo4j answers and SKIPPED with the reason when it
  does not, the same rule `tests/test_framework_projection_roundtrip.py` follows: a projection
  question cannot be answered without the projection, and answering it from nothing would pass.
* **Mermaid parses** (decision 4): every ```mermaid block is rendered by `mmdc`, the Mermaid
  project's own CLI, which is a parser and not a lint. Skipped, with the reason, if `mmdc` is
  not installed.
* **Every cited file exists**, and every `file:line` is inside its file.
* **No bare numeral in prose** that the page's number ledger does not hold. Prose is every line
  outside tables, code blocks, block quotes, headings and the generator comment, with
  backticked spans, URLs and identifiers (`§5b`, `DN-007`, dates) removed.
* **Every runbook command is copied from its source**: the source text is in the source file.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "mcp"))

import build_brief_pack as B  # noqa: E402

OUT = B.OUT


def _pack_files() -> dict:
    return {str(p.relative_to(OUT)): p for p in OUT.rglob("*") if p.is_file()}


@pytest.fixture(scope="module")
def graph():
    import airkg_tools as T
    g = T.Graph()
    if not g.available():
        pytest.skip(f"Neo4j unreachable, graph pages of the brief pack unverified: {g.error}")
    return g


@pytest.fixture(scope="module")
def full(graph):
    return B.render(graph)


def test_graph_free_pages_regenerate_byte_for_byte():
    files = B.render(None)
    assert files, "the graph-free render produced nothing"
    for name, text in files.items():
        assert (OUT / name).is_file(), f"{name} is generated but not on disk"
        assert (OUT / name).read_text(encoding="utf-8") == text, f"{name} drifted"


def test_a_second_render_is_identical():
    assert B.render(None) == B.render(None)


def test_full_pack_regenerates_byte_for_byte_and_nothing_else_is_there(full):
    on_disk = set(_pack_files()) - {B.CAPTURE.name}
    assert on_disk == set(full), (sorted(on_disk - set(full)), sorted(set(full) - on_disk))
    for name, text in full.items():
        assert (OUT / name).read_text(encoding="utf-8") == text, f"{name} drifted"


def test_every_page_names_its_generator_record_commit_and_cycle():
    s = B.Sources(None)
    for name, p in _pack_files().items():
        if name == B.CAPTURE.name or name.endswith(".json"):
            continue
        first = p.read_text(encoding="utf-8").splitlines()[0]
        assert B.GENERATOR in first and s.record_commit[:12] in first and s.cycle in first, name


def _mermaid_blocks():
    for name, p in sorted(_pack_files().items()):
        if not name.endswith(".md"):
            continue
        text = p.read_text(encoding="utf-8")
        for i, m in enumerate(re.finditer(r"```mermaid\n(.*?)```", text, re.S)):
            yield f"{name}#{i}", m.group(1)


def test_there_are_four_architecture_diagrams():
    assert len([k for k, _ in _mermaid_blocks() if k.startswith("E_architecture.md")]) == 4


@pytest.mark.parametrize("key,src", list(_mermaid_blocks()))
def test_every_mermaid_block_parses(key, src, tmp_path):
    mmdc = shutil.which("mmdc")
    if mmdc is None:
        pytest.skip("mmdc not installed; the Mermaid in the brief pack is not validated")
    i = tmp_path / "d.mmd"
    i.write_text(src, encoding="utf-8")
    r = subprocess.run([mmdc, "-i", str(i), "-o", str(tmp_path / "d.svg"), "-q"],
                       capture_output=True, text=True, timeout=120)
    assert r.returncode == 0 and (tmp_path / "d.svg").is_file(), f"{key}: {r.stderr[-800:]}"


_PATH = re.compile(r"`((?:seldon/)?[\w./-]+\.(?:py|md|json|jsonl|yaml|yml|csv|sh|pdf|html|cff))"
                   r"(?::(\d+)|::[\w]+)?`")


def _resolve(path: str) -> Path | None:
    if path.startswith("seldon/"):
        return B.SELDON_REPO.parent / path if B.SELDON_REPO.is_dir() else None
    if path.startswith("appendix/"):
        return OUT / path         # a link inside the pack
    return REPO / path


def _outside_fences(text: str) -> str:
    """Captured command output and diagrams are quoted, not cited: a path the report prints
    relative to its own directory is the report's, not the pack's."""
    return re.sub(r"```.*?```", "", text, flags=re.S)


def test_every_cited_file_exists_and_every_line_is_inside_it():
    bad = []
    for name, p in _pack_files().items():
        if not name.endswith(".md"):
            continue
        for m in _PATH.finditer(_outside_fences(p.read_text(encoding="utf-8"))):
            path, line = m.group(1), m.group(2)
            if "/" not in path and not (REPO / path).exists():
                continue          # a bare file name in prose, e.g. the page's own CSV
            target = _resolve(path)
            if target is None:
                continue          # the Seldon repository is not on this machine
            if not target.is_file():
                bad.append(f"{name}: {path} does not exist")
            elif line and int(line) > len(target.read_text(encoding="utf-8").splitlines()):
                bad.append(f"{name}: {path}:{line} is past the end of the file")
    assert not bad, "\n".join(bad)


def prose_numerals(text: str) -> list:
    out, fence = [], False
    for line in text.splitlines():
        if line.startswith("```"):
            fence = not fence
            continue
        s = line.lstrip()
        if fence or s.startswith(("|", ">", "<!--", "#")):
            continue
        line = re.sub(r"`[^`]*`", " ", line)
        line = re.sub(r"https?://\S+", " ", line)
        line = re.sub(r"§\d+[a-z]?", " ", line)
        line = re.sub(r"\b[A-Z]{2,}-\d+\b", " ", line)
        line = re.sub(r"\b\d{4}-\d{2}-\d{2}\b", " ", line)
        line = re.sub(r"^\s*(\d+\.|\*)\s", " ", line)
        out += re.findall(r"(?<![\w.])\d+(?:\.\d+)?(?![\w.])", line)
    return out


def test_no_bare_numeral_in_prose_that_the_ledger_does_not_hold():
    ledger_path = OUT / "numbers.json"
    ledger = json.loads(ledger_path.read_text(encoding="utf-8")) if ledger_path.is_file() else {}
    bad = []
    for name, p in _pack_files().items():
        if not name.endswith(".md"):
            continue
        held = {x["value"] for x in ledger.get(name, [])}
        for n in prose_numerals(p.read_text(encoding="utf-8")):
            if n not in held:
                bad.append(f"{name}: {n}")
    assert not bad, "numerals in prose with no ledger entry:\n" + "\n".join(bad)


def test_the_numeral_scan_sees_a_typed_number():
    assert prose_numerals("There are 12 checks.") == ["12"]
    assert prose_numerals("| 12 | table |\n`12` and DN-007 and §5b and 2026-09-22") == []


@pytest.mark.parametrize("step", B.DEMO_STEPS, ids=[s["id"] for s in B.DEMO_STEPS])
def test_every_runbook_command_is_copied_from_its_source(step):
    src = (REPO / step["source"]).read_text(encoding="utf-8")
    assert step["source_text"] in src, f"{step['source']} does not document {step['source_text']!r}"


def test_the_capture_covers_every_step_with_the_command_it_shows():
    cap = json.loads(B.CAPTURE.read_text(encoding="utf-8"))
    got = {x["id"]: x["run"] for x in cap["steps"]}
    assert got == {s["id"]: s["run"] for s in B.DEMO_STEPS}
