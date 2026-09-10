"""The ESIP crosswalk re-derives, and every row is grounded in the admitted document.

`cc_tasks/2026-09-10_corpus_noaa_esip.md` §3: *"Both crosswalk files re-derive from the graph
byte-identically."* One of the two exists — the NOAA crosswalk was not built, because
`www.noaa.gov` answered 403 to the identified client and no operator copy was in `corpus/inbox/`,
so there is no §3.01 text to crosswalk and no Definition node to key it to. The RESULT says so.

What "re-derives" means here, and why it is checked three ways:

* **byte-identical** — running the builder again produces the stored file, modulo the one field
  that is a clock (`generated_at`). A crosswalk that cannot be regenerated is a hand-edited table
  wearing a script's name.
* **grounded** — each row's `verbatim` is re-read from the admitted file at the line it names. A
  row that drifts off its source is worse than a missing row: it reads as evidence.
* **resolvable** — every indicator a row cites exists in the framework, and the `measured` claim
  rests on a leg the scan actually runs.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

CROSSWALK = REPO / "state" / "crosswalk_esip_ai_readiness_2026-09-10.json"
SOURCE = REPO / "corpus" / "noaa_esip" / "esip-ai-ready-data-checklist-v1.0.md"
MANIFEST = REPO / "corpus" / "manifest.json"
DOC_ID = "esip-ai-ready-data-checklist-v1-0"

#: The one field that moves on every run. Everything else must be reproducible or the file is
#: not a projection of anything.
CLOCK_FIELDS = ("generated_at",)


@pytest.fixture(scope="module")
def crosswalk():
    if not CROSSWALK.is_file():
        pytest.skip("the ESIP crosswalk has not been built")
    return json.loads(CROSSWALK.read_text(encoding="utf-8"))


def test_the_crosswalk_re_derives_byte_identically(crosswalk):
    import build_esip_crosswalk as b
    fresh = b.build()
    stored = dict(crosswalk)
    for f in CLOCK_FIELDS:
        fresh.pop(f, None)
        stored.pop(f, None)
    assert json.dumps(fresh, sort_keys=True) == json.dumps(stored, sort_keys=True), (
        "the stored crosswalk is not what the builder produces; it was edited by hand or the "
        "builder changed without a rebuild")


def test_the_source_is_the_admitted_document_by_hash(crosswalk):
    """Content addressing, not a filename. The crosswalk cites 12,831 specific bytes."""
    entries = json.loads(MANIFEST.read_text(encoding="utf-8"))["entries"]
    assert DOC_ID in entries, f"{DOC_ID} is not in the corpus; the crosswalk cites nothing"
    e = entries[DOC_ID]
    assert e["screening"]["decision"] == "included"
    assert e["integrity"]["status"] == "verified"
    on_disk = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    assert e["identity"]["sha256"] == on_disk == crosswalk["source_sha256"], (
        "the manifest, the file on disk and the crosswalk do not agree on which bytes were "
        "crosswalked")


def test_every_row_is_grounded_at_the_line_it_names(crosswalk):
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    drifted = [(r["line"], r["verbatim"][:60], lines[r["line"] - 1].strip()[:60])
               for r in crosswalk["rows"]
               if lines[r["line"] - 1].strip() != r["verbatim"]]
    assert drifted == [], f"rows no longer match their source line: {drifted}"


def test_every_cited_indicator_exists_in_the_framework(crosswalk):
    f = json.loads((REPO / "framework" / "ai_readiness_framework.json").read_text(encoding="utf-8"))
    codes = {n["properties"]["code"] for n in f["nodes"]
             if "AssessmentIndicator" in n["labels"]}
    cited = {i for r in crosswalk["rows"] for i in r["indicators"]}
    assert cited <= codes, f"the crosswalk cites indicators the framework does not define: "\
                           f"{sorted(cited - codes)}"


def test_a_coverage_claim_rests_on_a_leg_the_scan_runs(crosswalk):
    """`measured` is a claim about the INSTRUMENT. A row that cites only unmeasured indicators
    and still claims `full` or `partial` collapses "the framework covers this" into "we measure
    this", which is the distinction the crosswalk exists to hold open."""
    bad = [(r["line"], r["measured"], r["indicators"]) for r in crosswalk["rows"]
           if r["measured"] != "none" and not r["indicators_measured_by_the_scan"]]
    assert bad == [], f"coverage claimed with no measured leg: {bad}"


def test_the_totals_are_derived_from_the_rows_and_not_typed(crosswalk):
    rows = crosswalk["rows"]
    assert crosswalk["items"] == len(rows)
    for m in ("full", "partial", "none"):
        assert crosswalk["by_measured"][m] == sum(1 for r in rows if r["measured"] == m)
    for section, counts in crosswalk["by_section"].items():
        for m, n in counts.items():
            assert n == sum(1 for r in rows
                            if r["section"] == section and r["measured"] == m)


def test_the_apparatus_is_not_crosswalked(crosswalk):
    """The About/History/citation blocks, the appendix definitions and the references say what
    the checklist IS. They ask nothing about a dataset, and a crosswalk row against one of them
    would be a row about the document rather than about a measurement."""
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    appendix = next(i for i, l in enumerate(lines, 1) if l.startswith("## Appendix"))
    first_item = next(i for i, l in enumerate(lines, 1) if l.startswith("## General Information"))
    stray = [r["line"] for r in crosswalk["rows"]
             if r["line"] < first_item or r["line"] > appendix]
    assert stray == [], f"rows against the document's apparatus: {stray}"


# ------------------------------------------------------- the NOAA half (ADDENDUM_01 unblocked it)

NOAA_CROSSWALK = REPO / "state" / "crosswalk_noaa_ai_ready_2026-09-10.json"
OCR = REPO / "corpus" / "noaa_esip" / "NAO_216-128.ocr.txt"
NOAA_DOC_ID = "nao-216-128-artificial-intelligence-in-noaa"


@pytest.fixture(scope="module")
def noaa():
    if not NOAA_CROSSWALK.is_file():
        pytest.skip("the NOAA crosswalk has not been built")
    return json.loads(NOAA_CROSSWALK.read_text(encoding="utf-8"))


def test_the_noaa_crosswalk_re_derives_byte_identically(noaa):
    import build_noaa_crosswalk as b
    fresh, stored = b.build(), dict(noaa)
    for f in CLOCK_FIELDS:
        fresh.pop(f, None)
        stored.pop(f, None)
    assert json.dumps(fresh, sort_keys=True) == json.dumps(stored, sort_keys=True)


def test_the_definition_verbatim_is_the_ocr_span_it_cites(noaa):
    """§3's gate clause. The span must be IN the OCR text, character for character under the
    parser's own normalisation — which is why it is stored as `Al-Ready` and not `AI-Ready`:
    that is what tesseract read, and correcting the source to match a prettier span would be
    editing evidence to pass a check about evidence."""
    sys.path.insert(0, str(REPO))
    from kg.extraction import grounding
    src = OCR.read_text(encoding="utf-8")
    assert grounding.is_grounded(noaa["definition_verbatim"], src)
    assert noaa["source_sha256"] == hashlib.sha256(OCR.read_bytes()).hexdigest()
    for r in noaa["rows"]:
        assert grounding.covers(noaa["definition_verbatim"], r["span_fragment"]), (
            f"component {r['component']!r} is not inside the definition it decomposes")


def test_the_definition_node_carries_the_same_verbatim(noaa):
    """The node on the event log and the crosswalk must quote the same text. Two records of one
    definition that disagree is worse than one record."""
    sys.path.insert(0, str(REPO))
    from kg import eventlog
    nodes = [ev for ev in eventlog.replay()
             if ev.get("event_type") == "node_asserted"
             and ev.get("payload", {}).get("id") == noaa["definition_node_id"]]
    assert nodes, f"no Definition node {noaa['definition_node_id']} on the log"
    item = nodes[-1]["payload"]["item"]
    assert item["verbatim_text"] == noaa["definition_verbatim"]
    assert item["grounding_span"] == noaa["definition_verbatim"]
    assert item["term"] == noaa["definition_term"] == "AI-Ready Data"


def test_the_two_directives_are_recorded_and_grounded():
    """Decision 2 asks for Obligations; `kg/schema.yaml` has no such type, so they are Claims
    with `claim_type: normative` and the request for a real Obligation type is staged for
    operator review. Whatever they are typed as, they must be grounded."""
    sys.path.insert(0, str(REPO))
    from kg import eventlog
    from kg.extraction import grounding
    src = OCR.read_text(encoding="utf-8")
    claims = {ev["payload"]["id"]: ev["payload"]["item"] for ev in eventlog.replay()
              if ev.get("event_type") == "node_asserted"
              and ev.get("doc_id") == NOAA_DOC_ID
              and ev.get("payload", {}).get("type") == "Claim"}
    assert set(claims) == {"nao216-4-05", "nao216-5-02-d"}
    for cid, item in claims.items():
        assert grounding.is_grounded(item["grounding_span"], src), cid
        assert item["claim_type"] == "normative"
    proposal = REPO / "corpus" / "staging" / "proposed_schema" / "obligation_node_type.jsonl"
    assert proposal.is_file(), (
        "the schema catalogue has no Obligation type and no proposal was staged; a type this "
        "repo cannot express has to reach the operator's review, not be silently substituted")


def test_the_noaa_headline_is_three_of_five(noaa):
    """Decision 5 states three-of-five coverage, and `docs/design/2026-09-08_l0_product_shape.md`
    now says so in prose. This is where that number comes from."""
    assert noaa["components"] == 5
    assert noaa["by_measured"] == {"full": 3, "partial": 1, "none": 1}


def test_the_fetch_record_still_says_the_fetcher_was_refused():
    """The documents are admitted from the operator's copies (`ADDENDUM_01`). That does NOT
    erase how the scanner's own attempt went: 403 to the identified client on both URLs, with
    robots.txt permitting the path. The refusal is a measurement and it stays on the record."""
    record = REPO / "state" / "noaa_esip_fetch_2026-09-10.json"
    assert record.is_file()
    fetch = json.loads(record.read_text(encoding="utf-8"))
    assert set(fetch["refused"]) == {"nao-216-128", "nao-201-118"}
    for row in fetch["sources"]:
        if row["key"].startswith("nao-"):
            assert row["robots_permits"] is True, "robots permitted; the host refused anyway"
            assert row["status"] == 403
    assert fetch["user_agent"].startswith("ai-readiness-kg-scanner/"), (
        "one identity, never varied (DD-060)")
