"""The Commerce guidance admission and its two reports (`cc_tasks/2026-10-02_commerce_guidance_admission.md`).

Stdlib + pyyaml. Nothing here needs Neo4j or the gitignored corpus binary: the one test that
re-derives the glossary from the PDF skips when the binary is absent, and says so.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import fss_airkg_reconciliation as R  # noqa: E402

DOC_ID = "generative-ai-and-open-data-guidelines-and-best-practices-de"
SHA = "87068818f5c4c86f1a211cd2375738646ed586c0ca7211d5bd9604636493bd91"
EPOCH = "commerce-guidance-2026-10-02"
ALLOWED_SCREENS = {"include_candidate", "excluded_by_rule", "off_topic"}


def _entries() -> dict:
    m = json.loads((REPO / "corpus" / "manifest.json").read_text(encoding="utf-8"))
    e = m["entries"]
    return e if isinstance(e, dict) else {d["doc_id"]: d for d in e}


def test_the_document_is_included_verified_at_the_fss_hash():
    e = _entries()[DOC_ID]
    assert e["screening"]["decision"] == "included"
    assert e["integrity"]["status"] == "verified"
    assert e["identity"]["sha256"] == SHA
    assert e["identity"]["canonical_path"] == f"corpus/bulk/{DOC_ID}.pdf"
    assert e["acquisition"]["method"] == "local_copy_from_fss_policy_kg"
    # The refetch fulfillment keeps the pending_refetch decision in the entry's history.
    assert any(h["decision"] == "pending_refetch" for h in e["screening"]["history"])


def test_the_manifest_add_event_carries_the_provenance():
    rows = [json.loads(l) for l in
            (REPO / "events" / "batch-001.jsonl").read_text(encoding="utf-8").splitlines()
            if DOC_ID in l]
    adds = [r for r in rows if r["event_type"] == "manifest_add"]
    assert len(adds) == 1
    p = adds[0]["payload"]
    assert p["content_hash"] == SHA and p["discovered_via"] == "fss-policy-kg ledger"
    acq = p["acquisition"]
    assert acq["verification"]["sha256"] == acq["verification"]["fss_ledger_sha256"] == SHA
    assert acq["fetch_log"] is None and "no fetch" in acq["fetch_log_note"]


def test_the_epoch_is_declared_with_this_one_member():
    ev = [json.loads(l) for l in
          (REPO / "corpus" / "evidence" / "decisions.jsonl").read_text(encoding="utf-8").splitlines()
          if EPOCH in l]
    decl = [e for e in ev if e["event_type"] == "corpus_epoch_declared"]
    assert len(decl) == 1 and decl[0]["payload"]["member_doc_ids"] == [DOC_ID]


def test_glossary_csv_is_49_terms_footnotes_80_to_129_without_123():
    rows = R.load_glossary()
    assert len(rows) == 49
    assert [int(r["footnote"]) for r in rows] == [n for n in range(80, 130) if n != 123]
    assert rows[0]["term"] == "AI-ready data"
    assert rows[0]["definition"].startswith("Data that is not just machine-readable, but "
                                            "machine-understandable;")
    ml = next(r for r in rows if r["term"] == "Machine learning")
    # The page-split entry is rejoined, with no footnote or running header inside it.
    assert ml["definition"].endswith("optimized for the training task")
    assert "NIST AI Glossary" not in ml["definition"] and "Generative Artificial" not in ml["definition"]


def test_glossary_parser_refuses_a_missing_entry():
    """Negative control: the parser's footnote guard is what makes N a measurement."""
    text = ("Appendix \nA1. Glossary and additional background information \n"
            "AI-ready data80: Data that is X. \n \nApache Parquet81: A format. \n \n"
            "Data92: Facts. \n \nA2. Frequently recommended things\n")
    terms = R.parse_glossary(text)
    assert [t["footnote"] for t in terms] == [80, 81, 92]
    assert [t["term"] for t in terms] == ["AI-ready data", "Apache Parquet", "Data"]


def test_glossary_rederives_from_the_admitted_pdf():
    src = REPO / "corpus" / "bulk" / f"{DOC_ID}.pdf"
    if not src.is_file():
        pytest.skip("corpus binary is gitignored and absent on this checkout")
    import run_bulk_extraction as rbe
    got = R.parse_glossary(rbe.doc_text(src, DOC_ID))
    on_disk = R.load_glossary()
    assert [(t["term"], t["definition"]) for t in got] == \
        [(r["term"], r["definition"]) for r in on_disk]


def test_cl085_is_prior_art_on_the_admitted_document():
    claims = yaml.safe_load((REPO / "docs" / "evidence" / "claims.yaml").read_text(encoding="utf-8"))
    c = next(x for x in claims["claims"] if x["id"] == "CL-085")
    assert c["status"] == "prior_art"
    docs = [e for e in c["evidence"] if e["kind"] == "document"]
    commerce = [e for e in docs if e["id"] == DOC_ID]
    assert commerce and "machine-understandable" in commerce[0]["quote"]
    assert "def_ai_ready_data" in commerce[0]["where"]
    # The comparators stay.
    assert {"nao-216-128-artificial-intelligence-in-noaa", "fcsm-25-03"} <= {e["id"] for e in docs}


def test_reconciliation_rows_cover_every_fss_document_and_screen_every_fss_only_one():
    with R.RECON_CSV.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 112
    only = {r["fss_doc_id"] for r in rows if not r["matched_by"]}
    assert all(r["screen"] in ALLOWED_SCREENS for r in rows if not r["matched_by"])
    assert all(not r["screen"] for r in rows if r["matched_by"])
    screen = yaml.safe_load(R.SCREEN.read_text(encoding="utf-8"))["documents"]
    assert set(screen) == only
    for doc, s in screen.items():
        assert s["screen"] in ALLOWED_SCREENS, doc
        assert s["reason"], doc
        assert (s["clause"] is None) == (s["screen"] == "off_topic"), doc


def test_phrase_regex_is_hyphen_and_whitespace_tolerant():
    import re
    rx = R.phrase_regex("machine-readable")
    assert re.match(rx, "the term  ''machine  readable'' means")
    assert re.match(rx, "Machine-readable data")
    assert not re.match(rx, "machine-learned")
    drx = R._definitional_regex("AI-ready data")
    assert re.match(drx, "AI-ready data 80 : Data that is not just machine-readable")
    assert not re.match(drx, "we publish AI-ready data to many users")
