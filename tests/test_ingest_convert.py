"""Guards for the T1 ingestion gate (task 2026-08-31_ingestion_conversion).

Every fixture is either a REAL file from the live corpus or a reduction of the exact damage
class measured there on 2026-08-31. The defect this suite exists for is not "conversion
failed" — it is **conversion succeeded and produced a table of contents**:
`slsa-specification-v1-0.html` is 16,566 bytes of markup carrying 2,016 characters of
visible text, 30% of it anchor text, and Docling converted it faithfully to 514 characters of
navigation. Nothing in the pipeline could see that, so it reached an extraction queue.

Mutation discipline (methodology §7.5, and the eighth instance arrived through a fixture with
a docstring that named the right principle): every guard below is driven through
`kg.ingest.gate.check`, the real admission entry point, and each has a mutation that must
break it.
"""
from __future__ import annotations

import json
import pathlib

import pytest

from kg.ingest import convert as C
from kg.ingest import gate as G

REPO = pathlib.Path(__file__).resolve().parent.parent

# A hub page: the shape of slsa-specification-v1-0.html, reduced. Links dominate the text.
NAV_HTML = """<html><body><h1>SLSA specification</h1>
<p>SLSA is a specification for describing supply chain security.</p>
<nav>""" + "".join(
    f'<a href="/spec/v1.0/{s}">{s.replace("-", " ")} section of the specification</a> '
    for s in ("requirements", "levels", "threats", "terminology", "provenance",
              "verifying-artifacts", "distributing-provenance", "producing-artifacts")
) + """</nav></body></html>"""

# A real document: prose with a few links in it.
_PARA = "This section states a normative requirement about data. " * 40
PROSE_HTML = ("<html><body><h1>A Real Specification</h1>"
              + "".join(f"<h2>Section {i}</h2><p>{_PARA}</p>" for i in range(1, 9))
              + '<p>See <a href="/x">the registry</a>.</p></body></html>')


@pytest.fixture(autouse=True)
def _isolate(tmp_path, monkeypatch):
    """Substrate and event log land in tmp_path — a test must never write the real store."""
    monkeypatch.setattr(C, "_SUBSTRATE_DIR", tmp_path / "substrate_md")
    monkeypatch.setattr(C, "_REPO", tmp_path)
    from kg import eventlog
    monkeypatch.setattr(eventlog, "_EVENTS_DIR", tmp_path / "events", raising=False)
    yield


# --- 1. the counterexample: conversion SUCCEEDS and the output is navigation --------------
def test_nav_page_is_a_gap_even_though_conversion_succeeds(tmp_path):
    src = tmp_path / "slsa.html"
    src.write_text(NAV_HTML)
    with pytest.raises(C.ConversionGap) as exc:
        C.convert("slsa", src, write=False)
    assert exc.value.gap_class == "thin_extent_suspected"
    assert exc.value.detail["converted_chars"] > 0, (
        "the point of this class: the converter WORKED and still produced nothing usable")


def test_real_prose_document_passes_the_same_gate(tmp_path):
    """The positive half of the control: the gate must let a genuine document through, or a
    passing suite would only prove it rejects everything."""
    src = tmp_path / "spec.html"
    src.write_text(PROSE_HTML)
    dest, report = C.convert("spec", src, write=False)
    assert report["adequate"], report["why"]
    assert report["link_density"] < C.MAX_LINK_DENSITY


def test_link_density_is_what_catches_slsa_not_the_text_floor():
    """Measured on the live file: slsa's visible text is 2,016 chars against a 2,000 floor —
    it clears the length test by 16 characters. A single-feature gate would have missed it.
    This pins WHY both Kohlschütter features are present, not just that they are."""
    live = REPO / "corpus" / "crosswalk" / "slsa-specification-v1-0.html"
    if not live.is_file():
        pytest.skip("live corpus file not present")
    markup = live.read_text("utf-8", "ignore")
    text = C.visible_text(markup)
    assert len(text) >= C.MIN_VISIBLE_CHARS, (
        f"slsa clears the text floor ({len(text)} >= {C.MIN_VISIBLE_CHARS}); if it no longer "
        f"does, this test's premise moved and the docstring is stale")
    assert C.link_density(markup) > C.MAX_LINK_DENSITY


def test_mutation_disabling_link_density_lets_the_nav_page_through(tmp_path, monkeypatch):
    """Positive control on the guard itself: raise the link-density ceiling to 1.0 and the
    nav page must be admitted. If it still fails, something other than link density is
    rejecting it and this suite is measuring the wrong thing."""
    src = tmp_path / "slsa.html"
    src.write_text(NAV_HTML)
    monkeypatch.setattr(C, "MAX_LINK_DENSITY", 1.0)
    monkeypatch.setattr(C, "MIN_VISIBLE_CHARS", 1)
    _, report = C.convert("slsa", src, write=False)
    assert report["adequate"], "with both features disabled the gate must pass it"


# --- 2. unsupported format at the ADMISSION entry point ----------------------------------
def test_unknown_format_emits_gap_and_launches_a_task(tmp_path, monkeypatch):
    src = tmp_path / "book.epub"
    src.write_bytes(b"PK\x03\x04 not really an epub")
    seen = {}

    def fake_register(doc_id, gap_class, detail):
        seen.update(doc_id=doc_id, gap_class=gap_class)
        return "task-abc123"

    monkeypatch.setattr(G, "register_gap_task", fake_register)
    r = G.check("book", src)
    assert r["ok"] is False and r["gap_class"] == "unknown_format"
    assert r["research_task_id"] == "task-abc123", "the auto-task is the improvement launch"
    assert seen["gap_class"] == "unknown_format"

    events = [json.loads(l) for l in
              (tmp_path / "events" / "batch-024.jsonl").read_text().splitlines()]
    assert [e["event_type"] for e in events] == ["conversion_gap"]
    assert events[0]["research_task_id"] == "task-abc123"


def test_broken_html_takes_the_gap_path_not_silent_admission(tmp_path, monkeypatch):
    """Every registered converter fails -> `conversion_failed`, an event, and a task. The
    failure mode being excluded is a document that is admitted and simply has no substrate."""
    src = tmp_path / "broken.html"
    src.write_text("<html>")
    monkeypatch.setattr(G, "register_gap_task", lambda *a: "task-broken")
    monkeypatch.setattr(C, "TOOLS", {
        "passthrough": C._passthrough,
        "docling": lambda p: (_ for _ in ()).throw(RuntimeError("docling exploded")),
        "pandoc": lambda p: "",
    })
    r = G.check("broken", src)
    assert r["ok"] is False and r["gap_class"] == "conversion_failed"
    assert [a["outcome"] for a in r["detail"]["attempts"]] == ["error", "ok"]
    assert (tmp_path / "events" / "batch-024.jsonl").is_file(), "the gap must be recorded"


def test_mutation_removing_the_registry_entry_makes_html_an_unknown_format(tmp_path, monkeypatch):
    """Confirms the registry is what routes format decisions, not an incidental branch."""
    src = tmp_path / "x.html"
    src.write_text(PROSE_HTML)
    monkeypatch.setitem(C.REGISTRY, ".html", ())
    with pytest.raises(C.ConversionGap) as exc:
        C.convert("x", src, write=False)
    assert exc.value.gap_class == "unknown_format"


# --- 3. frontmatter and citability -------------------------------------------------------
def test_frontmatter_carries_the_citability_contract(tmp_path):
    src = tmp_path / "spec.html"
    src.write_text(PROSE_HTML)
    dest, _ = C.convert("spec", src, {"source_url": "https://example.org/spec",
                                      "version": "1.0", "acquired_at": "2026-08-29"})
    fm = C.read_frontmatter(dest)
    for key in ("doc_id", "source_path", "source_sha256", "source_url", "source_format",
                "version", "acquired_at", "converter", "converter_version", "converted_at"):
        assert fm.get(key), f"frontmatter lost {key}; citability must survive conversion"
    assert fm["source_sha256"] == C.sha256_file(src)


def test_frontmatter_sha_mismatch_is_detected(tmp_path):
    """The source changed under an existing substrate: every span located in that substrate is
    now a claim about text that is not the admitted text."""
    src = tmp_path / "spec.html"
    src.write_text(PROSE_HTML)
    dest, _ = C.convert("spec", src, {"source_url": "https://example.org/spec"})
    assert C.verify_substrate("spec", dest)["ok"] is True

    src.write_text(PROSE_HTML + "<p>a later edit to the source</p>")
    v = C.verify_substrate("spec", dest)
    assert v["ok"] is False and v["issue"] == "source_sha_mismatch"
    assert v["recorded"] != v["actual"]


def test_mutation_ignoring_the_recorded_sha_hides_the_mismatch(tmp_path, monkeypatch):
    """Positive control: make the comparison read the live file for both sides and the
    mismatch test must stop firing — proving the RECORDED hash is what does the work."""
    src = tmp_path / "spec.html"
    src.write_text(PROSE_HTML)
    dest, _ = C.convert("spec", src, {"source_url": "https://example.org/spec"})
    src.write_text(PROSE_HTML + "<p>edit</p>")
    real = C.read_frontmatter

    def blind(path):
        fm = dict(real(path))
        fm["source_sha256"] = C.sha256_file(tmp_path / fm["source_path"].split("/")[-1])
        return fm

    monkeypatch.setattr(C, "read_frontmatter", blind)
    assert C.verify_substrate("spec", dest)["ok"] is True, (
        "with the recorded hash ignored the guard must go blind")


# --- 4. delegation and the closed gap-class list ------------------------------------------
def test_pdfs_are_delegated_not_reconverted(tmp_path):
    """Re-conversion of the working PDF corpus is out of scope; routing PDFs here would
    re-convert ~170 documents to no benefit."""
    src = tmp_path / "doc.pdf"
    src.write_bytes(b"%PDF-1.4\n")
    with pytest.raises(C.ConversionGap) as exc:
        C.convert("doc", src, write=False)
    assert exc.value.gap_class == "unknown_format"
    assert "existing T1 path" in exc.value.detail["note"]


def test_gap_class_outside_the_closed_list_is_a_bug():
    with pytest.raises(ValueError):
        C.ConversionGap("d", "made_up_class", {})


def test_a_later_conversion_closes_an_earlier_gap(tmp_path, monkeypatch):
    """A re-acquired document stops being reported without any event being edited — the
    append-only correction path (invariant 1)."""
    src = tmp_path / "d.html"
    src.write_text(NAV_HTML)
    monkeypatch.setattr(G, "register_gap_task", lambda *a: "task-1")
    G.check("d", src)
    assert "d" in G.gaps()
    src.write_text(PROSE_HTML)
    G.check("d", src)
    assert "d" not in G.gaps(), "a successful conversion must close the gap by superseding it"
