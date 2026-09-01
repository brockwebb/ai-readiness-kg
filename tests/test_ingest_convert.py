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


FIXTURES = REPO / "tests" / "fixtures" / "extent"


def test_link_density_is_what_catches_slsa_not_the_text_floor():
    """Measured on the real capture: slsa's visible text is 2,016 chars against a 2,000 floor
    — it clears the length test by 16 characters. A single-feature gate would have missed it.
    This pins WHY both Kohlschütter features are present, not just that they are.

    Reads the VENDORED capture, not the live corpus file. It used to read
    `corpus/crosswalk/slsa-specification-v1-0.html` behind a `pytest.skip`, and the extent
    remediation quarantined exactly that file — so the control silently stopped running at
    the moment its subject was replaced. `corpus/` is gitignored, so a live-file control can
    never be durable; the captures are kept as fixtures precisely so they can go on failing."""
    markup = (FIXTURES / "slsa-toc.html").read_text("utf-8", "ignore")
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


# ------------------------------------------------- DD-030 AT THE ADMISSION ENTRY POINT
# The task's mutation (a) is "seeded unsupported format AT ADMISSION emits conversion_gap and
# the auto-task appears", and (d) is "drive admission entry points, not fixtures that cannot
# fail". The gate's own tests drive `gate.check`, which is the gate's entry, not admission's:
# `kg.manifest.add` is the only gate into the corpus (project invariant 2), and it did not
# call the gate at all. Every one of those tests passed with the two wholly unconnected.
# These drive `manifest.add`.

@pytest.fixture
def admission(tmp_path, monkeypatch):
    """A throwaway corpus + event log, with the manifest module repointed at it."""
    from kg import eventlog, manifest
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    schema = tmp_path / "schema.yaml"
    schema.write_text('schema_version: "0.1"\n', encoding="utf-8")
    monkeypatch.setattr(eventlog, "_EVENTS_DIR", tmp_path / "events")
    monkeypatch.setattr(eventlog, "_SCHEMA_PATH", schema)
    monkeypatch.setattr(manifest, "_REPO_ROOT", tmp_path)
    monkeypatch.setattr(manifest, "_CORPUS_DIR", corpus)
    monkeypatch.setattr(manifest, "_MANIFEST_PATH", corpus / "manifest.json")
    return tmp_path


def _admit(repo, name, content, monkeypatch, **over):
    from kg import manifest
    from kg.ingest import gate
    minted = []
    monkeypatch.setattr(gate, "register_gap_task",
                        lambda d, c, detail: minted.append((d, c)) or "task-xyz")
    path = repo / "corpus" / name
    path.write_bytes(content if isinstance(content, bytes) else content.encode())
    fields = dict(doc_id="probe-doc", title="T", authors=["A"], pub_date="2026",
                  source_type="federal", primary_url="https://example.gov/probe",
                  inclusion_rationale="r", discovered_via="manual")
    fields.update(over)
    doc_id = manifest.add(str(path), **fields)
    from kg import eventlog
    return doc_id, [e for e in eventlog.replay()], minted


def test_an_unsupported_format_gaps_at_admission_not_in_a_later_sweep(admission, monkeypatch):
    """Mutation (a) at the real boundary. Admission must ADMIT the document (rule (c) — a
    document the operator deliberately acquired is never lost) and, in the same call, say
    that no substrate exists and launch the task that fixes it."""
    doc_id, events, minted = _admit(admission, "book.epub", b"PK\x03\x04 nope", monkeypatch)
    assert doc_id == "probe-doc"
    kinds = [e["event_type"] for e in events]
    assert kinds == ["manifest_add", "conversion_gap"], kinds
    gap = events[1]
    assert gap["gap_class"] == "unknown_format"
    assert gap["research_task_id"] == "task-xyz", "the auto-task IS the improvement launch"
    assert minted == [("probe-doc", "unknown_format")]


def test_a_thin_page_gaps_at_admission_even_though_it_converts(admission, monkeypatch):
    """The class the whole rule exists for: conversion SUCCEEDS and the result is a table of
    contents. Exit status cannot see this; the extent gate can."""
    _, events, minted = _admit(admission, "nav.md", "# Contents\n\n- [a](a)\n", monkeypatch)
    assert [e["event_type"] for e in events] == ["manifest_add", "conversion_gap"]
    assert events[1]["gap_class"] == "thin_extent_suspected"
    assert minted and minted[0][1] == "thin_extent_suspected"


def test_a_pdf_is_delegated_at_admission_and_not_gapped_for_it(admission, monkeypatch):
    """PDFs are owned by the existing T1 path. Gapping every PDF admission would mint a
    ResearchTask per document for a conversion this module was never asked to do — 99 of them
    in this corpus."""
    _, events, minted = _admit(admission, "paper.pdf", b"%PDF-1.7 ...", monkeypatch)
    assert [e["event_type"] for e in events] == ["manifest_add"]
    assert minted == []


def test_admission_survives_the_gate_and_the_document_is_never_lost(admission, monkeypatch):
    """Rule (c) is load-bearing and easy to get backwards. A gap must not raise
    ManifestError: refusing admission would lose the document, which is the failure mode the
    rule rejects in favour of admitting loudly."""
    from kg import manifest
    doc_id, events, _ = _admit(admission, "x.epub", b"junk", monkeypatch)
    assert doc_id == "probe-doc"
    assert events[0]["payload"]["doc_id"] == "probe-doc"
    assert events[0]["payload"]["status"] == "active"


def test_the_conftest_guard_fires_when_a_test_forgets_to_stub_the_auto_task(admission):
    """Positive control for the guard added after this wiring minted 22 real ResearchTasks in
    the operator's Seldon graph from fixture doc_ids. Without a test that OMITS the stub, the
    guard could be deleted and the suite would not notice — it only ever runs on the path no
    passing test takes. This test takes it deliberately."""
    from kg import manifest
    path = admission / "corpus" / "thin.epub"
    path.write_bytes(b"junk")
    with pytest.raises(AssertionError, match="reached the real `seldon` CLI"):
        manifest.add(str(path), doc_id="guard-probe", title="T", authors=["A"],
                     pub_date="2026", source_type="federal",
                     primary_url="https://example.gov/guard", inclusion_rationale="r",
                     discovered_via="manual")


# ------------------------------------------------- extent remediation (2026-08-31_extent_remediation)
def test_every_superseded_capture_still_fails_the_gate():
    """The task's requirement, kept as a standing control: the six documents were replaced
    because their captures were navigation, and those captures must go on failing. If a
    threshold ever moves far enough to admit one of these, this test says so."""
    for name, why in (("slsa-toc.html", "link density"),
                      ("odcs-toc.html", "link density"),
                      ("digital-gov-hero.md", "text floor")):
        src = FIXTURES / name
        with pytest.raises(C.ConversionGap) as exc:
            C.convert(src.stem, src, write=False)
        assert exc.value.gap_class == "thin_extent_suspected", (name, why)


def test_a_reacquired_specification_passes_the_same_gate():
    """The positive control the negative one needs. A gate that rejects everything passes a
    suite of rejections, so this drives real bytes from a re-acquired document — an excerpt
    of the ODCS v3.1.0 markdown that replaced the 2,630-character site rendering — through
    the same `convert` path and requires it through."""
    src = FIXTURES / "odcs-reacquired-excerpt.md"
    _dest, report = C.convert("odcs-excerpt", src, write=False)
    assert report["adequate"], report.get("why")
    assert report["visible_chars"] > C.MIN_VISIBLE_CHARS
    assert report["link_density"] < C.MAX_LINK_DENSITY


def test_the_two_features_split_the_superseded_captures_between_them():
    """Both Kohlschütter features are load-bearing and the remediation set proves it with
    real documents: slsa/odcs are HTML nav pages caught by LINK DENSITY (slsa clears the text
    floor by 16 chars), digital-gov is a markdown hero page whose anchors crawl4ai already
    stripped, so its link density is low and only the TEXT FLOOR catches it. Neither feature
    alone catches all three."""
    slsa = (FIXTURES / "slsa-toc.html").read_text("utf-8", "ignore")
    hero = (FIXTURES / "digital-gov-hero.md").read_text("utf-8", "ignore")
    assert len(C.visible_text(slsa)) >= C.MIN_VISIBLE_CHARS      # text floor MISSES slsa
    assert C.link_density(slsa) > C.MAX_LINK_DENSITY             # density catches it
    assert len(C.visible_text(hero)) < C.MIN_VISIBLE_CHARS       # text floor catches hero
    assert C.link_density(hero) <= C.MAX_LINK_DENSITY            # density MISSES it


# ------------------------------------------------- ADDENDUM-03: substrate wiring into doc_text
def test_a_document_with_substrate_is_read_from_substrate(tmp_path, monkeypatch):
    """ADDENDUM-03 item 1. The substrate is the canonical form, and for an HTML source it is the
    ONLY readable form: the suffix dispatch raises on `.html`, which is why five re-acquired
    standards were unextractable until this lookup existed."""
    import run_bulk_extraction as rbe
    from kg.ingest import gate
    sub = tmp_path / "d.md"
    sub.write_text('---\ndoc_id: "d"\nconverter: "docling"\n---\nthe real document text\n')
    monkeypatch.setattr(gate, "substrate_path", lambda doc_id: sub if doc_id == "d" else None)
    assert rbe.doc_text(tmp_path / "d.html", "d") == "the real document text\n"


def test_a_document_without_substrate_reads_exactly_what_it_read_before(tmp_path, monkeypatch):
    """The other half of ADDENDUM-03's test, and the one that protects the status quo. A PDF has
    no substrate by design, and a markdown source with no substrate must still read itself."""
    import run_bulk_extraction as rbe
    from kg.ingest import gate
    monkeypatch.setattr(gate, "substrate_path", lambda doc_id: None)
    src = tmp_path / "d.md"
    src.write_text("original bytes\n")
    assert rbe.doc_text(src, "d") == "original bytes\n"
    assert rbe.doc_text(src) == "original bytes\n"          # and with no doc_id at all


def test_the_frontmatter_never_reaches_the_extractor(tmp_path):
    """Chunk boundaries and grounding anchors are offsets into the text the extractor was given.
    Twelve lines of YAML at the top would shift every offset in the document and invalidate
    resume against chunks already ingested, silently."""
    from kg.ingest import convert as C
    sub = tmp_path / "d.md"
    body = "# Title\n\nbody text that the chunker will offset into.\n"
    sub.write_text('---\ndoc_id: "d"\nsource_sha256: "abc"\n---\n' + body)
    got = C.substrate_body(sub)
    assert got == body
    assert "doc_id" not in got and "source_sha256" not in got


def test_a_passthrough_substrate_is_byte_identical_to_its_source(tmp_path, monkeypatch):
    """The property that makes this wiring safe for the 92 documents already in the graph. A
    passthrough conversion writes frontmatter plus the source unchanged, so stripping the
    frontmatter must return the source byte for byte. If it ever does not, every already-ingested
    chunk_id stops lining up with the text it was cut from."""
    from kg.ingest import convert as C
    src = tmp_path / "src.md"
    # long enough to clear the extent gate: this test is about byte fidelity, not admission
    src.write_text("line one\n\nline two, with trailing spaces   \n\n\n"
                   + ("real prose that a specification would contain. " * 60) + "\n")
    dest, _report = C.convert("d", src, {}, write=True)
    assert C.substrate_body(dest) == src.read_text()
