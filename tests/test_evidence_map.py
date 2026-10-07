"""The evidence map (`cc_tasks/2026-10-02_evidence_map_record.md`, DN-009 decision 2).

Three things the task asks for, and the controls that show each check can fail:

* idempotence: `docs/evidence/claims.yaml` is what `scripts/build_evidence_map.py` renders now,
  byte for byte, and a second render is identical;
* every `record` and `needs_measurement` claim's evidence resolves: a Finding on the cycle of
  record (in the projection and at the line its locator names), a Result on the graph, an
  admitted corpus document, a framework record node, or a named query;
* every numeral in a claim's prose is on that claim's `numbers` list, and the list equals the
  script's freshly computed values;
* the prior-art entries (`cc_tasks/2026-10-02_evidence_map_prior_art_v2.md`, PA1 to PA9): every
  `citation` has an https URL recorded at search time, the same URL under its key in
  `docs/evidence/sources.bib`, and a quotation under the task's word limit; every `document`
  is an admitted corpus document located at its first `manifest_add` event.

The graph is required for a render; when Neo4j is down the graph tests skip, as the brief
pack's do, and the pure tests (the classifiers and the numeral scan) still run.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import build_evidence_map as E  # noqa: E402

TASK = E.TASK
#: The task that appends `prior_art` and `unsupported` entries (DN-009 decision 8).
PRIOR_ART_TASK = "cc_tasks/2026-10-02_evidence_map_prior_art_v2.md"
PRIOR_ART_KEYS = [f"prior_art.pa{i}" for i in range(1, 10)]
CITATION = "citation"
BIB = REPO / "docs" / "evidence" / "sources.bib"
#: The task's limit on a quotation from a third-party source ("under 15 words quoted").
QUOTE_WORD_LIMIT = 15


@pytest.fixture(scope="module")
def graph():
    import build_brief_pack as BP
    g = BP.graph_or_none(required=False)
    if g is None:
        pytest.skip("Neo4j unreachable; the evidence map's record claims are unverified")
    return g


@pytest.fixture(scope="module")
def rendered(graph):
    return E.render(graph)


@pytest.fixture(scope="module")
def on_disk():
    return yaml.safe_load(E.CLAIMS.read_text(encoding="utf-8"))


def ours(doc):
    return [c for c in doc["claims"] if c.get("source_task") == TASK]


# ------------------------------------------------------------------------ idempotence

def test_claims_file_regenerates_byte_for_byte(rendered):
    assert E.CLAIMS.read_text(encoding="utf-8") == rendered, (
        "docs/evidence/claims.yaml has drifted from the record; re-run "
        "scripts/build_evidence_map.py")


def test_a_second_render_is_identical(graph, rendered):
    assert E.render(graph) == rendered


# ------------------------------------------------------------------------ schema

def test_every_claim_has_the_schema(on_disk):
    ids = [c["id"] for c in on_disk["claims"]]
    assert len(ids) == len(set(ids)), "duplicate claim ids"
    for c in on_disk["claims"]:
        assert re.fullmatch(r"CL-\d{3,}", c["id"]), c["id"]
        assert c["status"] in E.STATUSES, c
        assert c["text"].strip() and c["source_task"], c
        for e in c["evidence"]:
            # `citation` is written only by the prior-art task; the generator never emits it.
            assert e["kind"] in E.EVIDENCE_KINDS + (CITATION,), e
            assert e["id"] and e["locator"], e
    # This task writes only record and needs_measurement entries (task decision 1).
    assert {c["status"] for c in ours(on_disk)} <= {"record", "needs_measurement"}
    assert all(c["evidence"] for c in ours(on_disk)), "a record claim with no evidence"


# ------------------------------------------------------------------------ evidence resolves

def test_every_record_claims_evidence_resolves(graph, on_disk):
    import json
    m = E.Map(graph)
    record_ids = {n["id"] for n in m.s.record["nodes"]}
    included = {k for k, v in m.s.manifest.items() if v["screening"]["decision"] == "included"}
    fids, rids = set(), set()
    for c in ours(on_disk):
        for e in c["evidence"]:
            k, i = e["kind"], e["id"]
            if k == "finding":
                fids.add(i)
                path, line = e["locator"].rsplit(":", 1)
                row = (REPO / path).read_text(encoding="utf-8").splitlines()[int(line) - 1]
                assert json.loads(row)["finding_id"] == i, f"{c['id']}: {e['locator']} is not {i}"
            elif k == "indicator":
                assert i in record_ids, f"{c['id']}: {i} is not a record node"
            elif k == "document":
                assert i in included, f"{c['id']}: {i} is not an admitted document"
                path, line = e["locator"].rsplit(":", 1)
                row = (REPO / path).read_text(encoding="utf-8").splitlines()[int(line) - 1]
                ev = json.loads(row)
                assert ev["event_type"] == "manifest_add"
                assert (ev.get("doc_id") or ev["payload"]["doc_id"]) == i
            elif k == "result":
                rids.add(i)
            elif k == "query":
                assert i in E.QUERIES, f"{c['id']}: query {i} is not named in QUERIES"
    # The cycle of record's Findings are under its own cycle, or, for a composite cycle of record,
    # under its parts' (`m.parts`), and then they must also be the ones its payload selects.
    rows, _ = graph.read("MATCH (f:Finding) WHERE f.cycle IN $cs AND f.finding_id IN $ids "
                         "RETURN f.finding_id AS id", limit=len(fids) + 1,
                         cs=[c for c, _, _ in m.parts], ids=sorted(fids))
    assert {r["id"] for r in rows} == fids, "a cited Finding is not on the cycle of record"
    if m.composite:
        assert fids <= m.payload_ids, "a cited Finding is not one the composite selects"
    rows, _ = graph.read("MATCH (r:Artifact:Result) WHERE r.artifact_id IN $ids "
                         "RETURN r.artifact_id AS id", limit=len(rids) + 1, ids=sorted(rids))
    assert {r["id"] for r in rows} == rids, "a cited Result is not on the graph"


# ------------------------------------------------------------------------ numbers

def test_every_numeral_in_a_claim_is_on_its_numbers_list(on_disk):
    for c in on_disk["claims"]:
        held = {d["value"] for d in c.get("numbers") or []}
        stray = [x for x in E.numerals(c["text"]) if x not in held]
        assert not stray, f"{c['id']}: numerals {stray} are not on its numbers list"


def test_every_number_equals_the_scripts_computed_value(rendered, on_disk):
    fresh = {c["key"]: c for c in ours(yaml.safe_load(rendered))}
    for c in ours(on_disk):
        assert c["key"] in fresh, f"{c['id']} ({c['key']}) is no longer computed"
        assert c["numbers"] == fresh[c["key"]]["numbers"], c["id"]
        assert c["text"] == fresh[c["key"]]["text"], c["id"]


def test_the_numeral_scan_sees_a_typed_number():
    """Positive control: a typed number in prose is seen; a backticked one is not."""
    assert E.numerals("there are 1,009 findings and 0.2 of it") == ["1,009", "0.2"]
    assert E.numerals("leg `A10` on `scan_2026-09-10_rj4` (`DN-009 decision 6`)") == []


# ------------------------------------------------------------------------ other tasks' claims

def test_other_tasks_claims_are_carried_through_and_ids_are_not_reused(graph, monkeypatch,
                                                                       tmp_path, on_disk):
    foreign = {"id": "CL-900", "key": "prior_art.example", "question": "prior art",
               "text": "A claim the prior-art task owns.", "status": "prior_art",
               "evidence": [{"kind": "document", "id": "x", "locator": "y"}],
               "numbers": [], "source_task": "cc_tasks/2026-10-02_evidence_map_prior_art.md"}
    dropped = dict(ours(on_disk)[0])
    kept = [c for c in on_disk["claims"] if c["key"] != dropped["key"]]
    p = tmp_path / "claims.yaml"
    p.write_text(yaml.safe_dump({"claims": kept + [foreign]}, sort_keys=False), encoding="utf-8")
    monkeypatch.setattr(E, "CLAIMS", p)
    out = yaml.safe_load(E.render(graph))
    by_id = {c["id"]: c for c in out["claims"]}
    assert by_id["CL-900"] == foreign, "another task's claim was not carried through"
    regained = next(c for c in out["claims"] if c["key"] == dropped["key"])
    assert int(regained["id"][3:]) > 900, "a new key reused an id below the file's highest"
    for c in kept:
        if c.get("source_task") == TASK:
            assert by_id[c["id"]]["key"] == c["key"], f"{c['id']} was renumbered"


# ------------------------------------------------------------------------ classifiers

@pytest.mark.parametrize("verdict, reason, classes, want", [
    ("error", "the surface could not be observed: refused", ["refused"], "access_denial"),
    ("error", "markup could not be extracted: robots_disallowed", ["robots_disallowed"],
     "access_denial"),
    ("error", "the catalog could not be observed: http_5xx", ["http_5xx"], "error_other"),
    ("fail", "the host answered HTTP 403 to /robots.txt itself for x", ["refused"],
     "access_denial"),
    ("fail", "robots.txt DISALLOWS the product path for 8 of 8 AI-crawler user agents", [],
     "access_denial"),
    ("fail", "no licence in the product page's markup, in an HTTP Link header", [], "absence"),
    ("fail", "a catalog is served at https://www.census.gov/data.json but the product is not "
             "in it: no record names it", [], "absence"),
    ("fail", "only PDF served; first: https://example.gov/a.pdf", [], "nonconformant"),
    ("pass", "anything", [], "pass"),
])
def test_q2_category(verdict, reason, classes, want):
    f = {"finding_id": "fnd_x", "verdict": verdict, "reason": reason}
    assert E.q2_category(f, classes) == want


def test_q2_category_refuses_a_reason_it_cannot_place():
    with pytest.raises(SystemExit):
        E.q2_category({"finding_id": "fnd_x", "verdict": "fail", "reason": "something new"}, [])


def test_q1_requirement_classes():
    assert E.req_class({"kind": "open_source", "who_provides": "this_project"}) == "open_tooling"
    assert E.req_class({"kind": "hosted_paid", "who_provides": "this_project"}) == "funding"
    assert E.req_class({"kind": "benchmark_set", "who_provides": "this_project"}) == "no_standard"
    assert E.req_class({"kind": "open_source", "who_provides": "publisher"}) == \
        "agency_cooperation"
    with pytest.raises(SystemExit):
        E.req_class({"id": "x", "kind": "telepathy", "who_provides": "this_project"})


def test_q1_partition_covers_every_unmeasured_framework_indicator(on_disk):
    rows = on_disk["tables"]["q1_measurement_boundary"]
    import json
    rec = json.loads((REPO / E.RECORD_PATH).read_text(encoding="utf-8"))
    from framework_writeback import _candidate_ids
    cand = _candidate_ids(rec)
    want = sorted(n["properties"]["code"] for n in rec["nodes"]
                  if "AssessmentIndicator" in n["labels"] and n["id"] not in cand
                  and n["properties"]["measurement_status"] != "measured")
    assert sorted(r["indicator"] for r in rows) == want
    assert {r["class"] for r in rows} <= set(E.Q1_ORDER) | {E.Q1_NOT_BLOCKED}


# ------------------------------------------------------------------------ prior art (PA1 to PA9)

def prior_art(doc):
    return [c for c in doc["claims"] if c.get("source_task") == PRIOR_ART_TASK]


def bib_entries(text: str) -> dict:
    """`{key: {field: value}}` for a BibTeX file whose field values are brace-delimited on one
    line, which is how `docs/evidence/sources.bib` is written."""
    out, key = {}, None
    for line in text.splitlines():
        m = re.match(r"\s*@\w+\{([^,\s]+),\s*$", line)
        if m:
            key = m.group(1)
            assert key not in out, f"duplicate bib key {key}"
            out[key] = {}
            continue
        m = re.match(r"\s*(\w+)\s*=\s*\{(.*)\},?\s*$", line)
        if m and key:
            out[key][m.group(1)] = m.group(2)
    return out


def citation_problems(e: dict, bib: dict) -> list:
    """Why a `citation` evidence entry is not a citation a stranger can follow, or []."""
    bad = []
    for f in ("author", "year", "title", "venue", "url", "where", "quote", "retrieved"):
        if not str(e.get(f) or "").strip():
            bad.append(f"no {f}")
    url = str(e.get("url") or "")
    if not re.fullmatch(r"https://[A-Za-z0-9.-]+\.[A-Za-z]{2,}(/\S*)?", url):
        bad.append(f"url {url!r} is not an absolute https URL")
    if not re.match(r"\d{4}-\d{2}-\d{2} ", str(e.get("retrieved") or "")):
        bad.append("retrieved does not open with the search date")
    if e.get("id") not in bib:
        bad.append(f"bib key {e.get('id')!r} is not in sources.bib")
    elif bib[e["id"]].get("url") != url:
        bad.append(f"sources.bib's url for {e['id']} is not the url the quote was read at")
    if url and url not in str(e.get("locator") or ""):
        bad.append("locator does not carry the url")
    if not e.get("own_text") and len(str(e.get("quote") or "").split()) >= QUOTE_WORD_LIMIT:
        bad.append(f"quote is {QUOTE_WORD_LIMIT} words or more")
    return bad


def test_the_prior_art_claim_set_is_pa1_to_pa9_once_each(on_disk):
    mine = prior_art(on_disk)
    assert sorted(c["key"] for c in mine) == sorted(PRIOR_ART_KEYS)
    for c in mine:
        assert c["question"] == c["key"].split(".")[1].upper(), c["id"]
        assert c["status"] in ("prior_art", "unsupported"), c["id"]
        assert c["evidence"] or c["status"] == "unsupported", f"{c['id']}: no evidence"
        assert {e["kind"] for e in c["evidence"]} <= {"document", CITATION}, c["id"]
        assert c["numbers"] == [], f"{c['id']}: a prior-art claim types no number"
        if c["status"] == "unsupported":
            assert len(c.get("note", "")) > 40, f"{c['id']}: unsupported without the searches"
        for e in c["evidence"]:
            assert e.get("quote", "").strip(), f"{c['id']}: {e['id']} quotes nothing"


def test_every_citation_has_a_url_recorded_at_search_time_and_a_bib_key(on_disk):
    bib = bib_entries(BIB.read_text(encoding="utf-8"))
    cited = set()
    for c in prior_art(on_disk):
        for e in c["evidence"]:
            if e["kind"] == CITATION:
                cited.add(e["id"])
                assert not citation_problems(e, bib), (c["id"], citation_problems(e, bib))
    assert cited, "no citation entries at all"
    assert set(bib) == cited, f"bib entries no claim cites: {sorted(set(bib) - cited)}"


def test_the_citation_check_can_fail():
    """Negative controls: each defect the check exists for is reported."""
    bib = {"k": {"url": "https://example.org/a"}}
    good = {"kind": CITATION, "id": "k", "locator": "https://example.org/a (p. 1)",
            "author": "A", "year": "2020", "title": "T", "venue": "V",
            "url": "https://example.org/a", "where": "p. 1", "quote": "a short quotation",
            "retrieved": "2026-10-02 (WebFetch)"}
    assert citation_problems(good, bib) == []
    assert "bib key 'x' is not in sources.bib" in citation_problems({**good, "id": "x"}, bib)
    assert any("absolute https" in p
               for p in citation_problems({**good, "url": "http://example.org/a"}, bib))
    assert any("not the url" in p
               for p in citation_problems({**good, "url": "https://example.org/b",
                                           "locator": "https://example.org/b"}, bib))
    long_quote = " ".join(["word"] * QUOTE_WORD_LIMIT)
    assert any("words or more" in p for p in citation_problems({**good, "quote": long_quote}, bib))
    assert citation_problems({**good, "quote": long_quote, "own_text": True}, bib) == []
    assert "no retrieved" in citation_problems({**good, "retrieved": ""}, bib)


def test_prior_art_document_evidence_is_an_admitted_document_at_its_manifest_add():
    import json
    on_disk = yaml.safe_load(E.CLAIMS.read_text(encoding="utf-8"))
    manifest = json.loads((REPO / "corpus" / "manifest.json").read_text(encoding="utf-8"))
    entries = manifest["entries"]
    if isinstance(entries, list):
        entries = {d["doc_id"]: d for d in entries}
    included = {k for k, v in entries.items() if v["screening"]["decision"] == "included"}
    n = 0
    for c in prior_art(on_disk):
        for e in c["evidence"]:
            if e["kind"] != "document":
                continue
            n += 1
            assert e["id"] in included, f"{c['id']}: {e['id']} is not an admitted document"
            path, line = e["locator"].rsplit(":", 1)
            ev = json.loads((REPO / path).read_text(encoding="utf-8").splitlines()[int(line) - 1])
            assert ev["event_type"] == "manifest_add", f"{c['id']}: {e['locator']}"
            assert (ev.get("doc_id") or ev["payload"]["doc_id"]) == e["id"], c["id"]
    assert n, "no document evidence at all"
