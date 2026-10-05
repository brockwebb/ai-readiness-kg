"""The DCAT-US 3.0 intake and G4 brought current (`cc_tasks/2026-10-04_DCAT-002_dcat_us_3_intake_and_g4.md`).

Stdlib + pyyaml. Nothing here needs Neo4j, the network or the gitignored corpus binaries: the
tests that read a converted substrate skip when it is absent, and say how to rebuild it.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

import admit_dcat_us_3 as A  # noqa: E402
import report_traceability as RT  # noqa: E402
from kg.extraction.grounding import is_grounded  # noqa: E402

EPOCH = "dcat-us-3-2026-10-04"
NINE = {d["doc_id"] for d in A.DOCS}
#: The two captures this task must NOT supersede in place: RULE-B4-v1 and RULE-D3-v1 cite the
#: Dataset capture, and the overview is the held version of item 1 (R5).
HELD = {"dcat-us-3-dataset-schema":
        "7482b3170215046ff73ee2229d6e9305da7c5d676c32ec755c8784f8c3858e44",
        "dcat-us-3-overview":
        "87d3d2a8bb9d8ddc445e6674b4738e58f6b0d8629f6d19093dfc360b90175fa0"}
SUBSTRATE = REPO / "state" / "substrate_md"
REBUILD = "/opt/anaconda3/bin/python3 -m kg.ingest.gate --doc <doc_id> --no-task"


def _entries() -> dict:
    e = json.loads((REPO / "corpus" / "manifest.json").read_text(encoding="utf-8"))["entries"]
    return e if isinstance(e, dict) else {d["doc_id"]: d for d in e}


def _events(event_type: str) -> list:
    out = []
    for shard in sorted((REPO / "events").glob("batch-*.jsonl")):
        for line in shard.read_text(encoding="utf-8").splitlines():
            if f'"{event_type}"' in line:
                ev = json.loads(line)
                if ev.get("event_type") == event_type:
                    out.append(ev)
    return out


def _framework() -> dict:
    return json.loads((REPO / "framework" / "ai_readiness_framework.json")
                      .read_text(encoding="utf-8"))


def _g4() -> dict:
    return next(n["properties"] for n in _framework()["nodes"] if n["id"] == "ind:G4")


# ------------------------------------------------------------------ steps 1 and 2
def test_nine_documents_are_included_and_verified_in_the_crosswalk_lane():
    e = _entries()
    assert len(NINE) == 9
    for doc in NINE:
        assert doc in e, doc
        assert e[doc]["screening"]["decision"] == "included", doc
        assert e[doc]["integrity"]["status"] == "verified", doc
        assert e[doc]["identity"]["canonical_path"].startswith("corpus/crosswalk/"), doc
        assert e[doc]["acquisition"]["acquired_by"] == "scripts/fetch_allowlisted.py", doc


def test_each_has_exactly_one_manifest_add_naming_the_fetch_log_and_the_ledger_hash():
    adds = [ev for ev in _events("manifest_add") if ev["payload"]["doc_id"] in NINE]
    assert sorted(ev["payload"]["doc_id"] for ev in adds) == sorted(NINE)
    e = _entries()
    for ev in adds:
        p = ev["payload"]
        assert p["acquisition"]["fetch_log"] == "logs/2026-10-04_DCAT-002_fetch.jsonl"
        assert p["acquisition"]["verification"]["sha256"] == p["content_hash"]
        assert p["content_hash"] == e[p["doc_id"]]["identity"]["sha256"], p["doc_id"]


def test_the_epoch_is_declared_once_with_the_nine():
    rows = [json.loads(l) for l in
            (REPO / "corpus" / "evidence" / "decisions.jsonl").read_text(encoding="utf-8")
            .splitlines() if EPOCH in l]
    decl = [r for r in rows if r["event_type"] == "corpus_epoch_declared"]
    assert len(decl) == 1 and set(decl[0]["payload"]["member_doc_ids"]) == NINE


def test_the_two_archived_copies_cite_their_memento_uris():
    """RFC 7089: a memento URI names one capture. The working draft's original host answers
    404; the Dataset page was rewritten after the corpus captured it."""
    e = _entries()
    for doc, original in (("dcat-us-3-candidate-recommendation-snapshot",
                           "https://doi-do.github.io/dcat-us/"),
                          ("dcat-us-3-dataset-schema-2026-09-15",
                           "https://resources.data.gov/standards/catalog/dcat-us-3/dataset/")):
        url = e[doc]["identity"]["source_url"]
        assert re.fullmatch(r"https://web\.archive\.org/web/\d{14}id_/" + re.escape(original),
                            url), url


def test_the_held_captures_are_not_superseded_in_place():
    """'Do not edit an accepted record in place': the pre-registered rules' citation target and
    the held overview keep their bytes, and no content_update was written for either."""
    e = _entries()
    for doc, sha in HELD.items():
        assert e[doc]["identity"]["sha256"] == sha, doc
    assert not [ev for ev in _events("content_update") if ev["payload"]["doc_id"] in HELD]


def test_admission_refuses_a_url_the_fetch_log_has_no_single_200_body_for(tmp_path, monkeypatch):
    """Negative control: the hash an admission checks against is read from the log, so a URL
    with no 200 row, or with two different bodies, stops the admission."""
    log = tmp_path / "fetch.jsonl"
    rows = [{"event": "request", "url": "https://a.example/x", "status": 200, "sha256": "1"},
            {"event": "request", "url": "https://a.example/x", "status": 200, "sha256": "2"},
            {"event": "request", "url": "https://a.example/y", "status": 404, "sha256": "3"},
            {"event": "request", "url": "https://a.example/z", "status": 200, "sha256": "4"}]
    log.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    monkeypatch.setattr(A, "FETCH_LOG", log)
    assert A.fetched_sha("https://a.example/z") == "4"
    for url in ("https://a.example/x", "https://a.example/y", "https://a.example/w"):
        with pytest.raises(SystemExit):
            A.fetched_sha(url)


def test_the_extraction_driver_reads_the_declared_epoch():
    import run_dcat_extraction as X
    assert X.cohort() == sorted(NINE)
    with pytest.raises(SystemExit):
        X.cohort("dcat-us-3-overview")         # held, not a member of this epoch


# ------------------------------------------------------------------ step 3 (G4)
def test_g4_names_the_dcat_us_3_field_and_its_level():
    text = _g4()["indicator"]
    assert "DCAT-US 3.0" in text and "Recommended" in text and "`publisher`" in text
    assert "DCAT-US 1.1" in text and "`bureauCode`" in text and "`programCode`" in text


def test_g4_is_evidenced_by_the_rewritten_page_and_the_m_25_05_crosswalk():
    edged = {e["properties"]["doc_id"] for e in _framework()["edges"]
             if e["type"] == "EVIDENCED_BY" and e["from"] == "ind:G4"}
    assert {"dcat-us-3-dataset-schema-2026-09-15", "dcat-us-3-m-25-05-crosswalk",
            "dcat-us-3-dataset-schema"} <= edged


def test_the_level_g4_states_is_the_level_the_cited_page_states():
    """The word 'Recommended' sits outside the quoted span, so the span test cannot see it.
    This reads it off the cited capture: the publisher property's requirement line."""
    sub = SUBSTRATE / "dcat-us-3-dataset-schema-2026-09-15.md"
    if not sub.is_file():
        pytest.skip(f"no substrate on disk (gitignored); rebuild: {REBUILD}")
    text = sub.read_text(encoding="utf-8")
    m = re.search(r"Dataset &gt; publisher.*?\*\*Requirement:\*\*\s*(\w+)", text, re.S)
    assert m and m.group(1) == "Recommended", m and m.group(1)
    mandatory = re.findall(r"Dataset &gt; (\w+) #\]\([^)]*\)\s*\n\s*\*\*Requirement:\*\*\s*"
                           r"Mandatory", text)
    assert sorted(mandatory) == ["contactPoint", "description", "identifier", "title"]


@pytest.mark.parametrize("doc_id", ["dcat-us-3-dataset-schema-2026-09-15",
                                    "dcat-us-3-m-25-05-crosswalk"])
def test_the_new_g4_quotes_ground_in_the_substrate(doc_id):
    sub = SUBSTRATE / f"{doc_id}.md"
    if not sub.is_file():
        pytest.skip(f"no substrate on disk (gitignored); rebuild: {REBUILD}")
    loc = RT.locators(_g4()["evidence_raw"])[doc_id]
    spans = re.findall(r'"([^"]+)"', loc)
    assert spans
    text = sub.read_text(encoding="utf-8")
    assert all(is_grounded(s, text) for s in spans), [s for s in spans
                                                       if not is_grounded(s, text)]
