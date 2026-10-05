"""DCAT-002 ADDENDUM_01: the FAIRness Project record and the CDO Council DSWG report
(`cc_tasks/2026-10-04_DCAT-002_ADDENDUM_01_base_standard_and_fairness_record.md`, DN-011-R4).

Stdlib + pyyaml. Nothing here needs Neo4j, the network or the gitignored corpus binaries.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

import admit_dcat_002_a01 as A  # noqa: E402

EPOCH = "dcat-us-3-a01-2026-10-05"
FOUR = {d["doc_id"] for d in A.DOCS}
#: Items 10 and 15 of the addendum, held before it was written (R5, dedupe): each must stay one
#: ledger entry, not gain a second admission under a new id.
HELD = {"w3c-dcat-3": "https://www.w3.org/TR/vocab-dcat-3/",
        "fcsm-20-04-a-framework-for-data-quality": None}


def _entries() -> dict:
    e = json.loads((REPO / "corpus" / "manifest.json").read_text(encoding="utf-8"))["entries"]
    return e if isinstance(e, dict) else {d["doc_id"]: d for d in e}


def _manifest_adds() -> list:
    out = []
    for shard in sorted((REPO / "events").glob("batch-*.jsonl")):
        for line in shard.read_text(encoding="utf-8").splitlines():
            if '"manifest_add"' in line:
                ev = json.loads(line)
                if ev.get("event_type") == "manifest_add":
                    out.append(ev)
    return out


def test_four_documents_are_included_and_verified_in_the_crosswalk_lane():
    e = _entries()
    assert len(FOUR) == 4
    for doc in FOUR:
        assert e[doc]["screening"]["decision"] == "included", doc
        assert e[doc]["integrity"]["status"] == "verified", doc
        assert e[doc]["identity"]["canonical_path"].startswith("corpus/crosswalk/"), doc
        assert e[doc]["acquisition"]["acquired_by"] == "scripts/fetch_allowlisted.py", doc


def test_each_has_exactly_one_manifest_add_naming_the_fetch_log_and_the_ledger_hash():
    adds = [ev for ev in _manifest_adds() if ev["payload"]["doc_id"] in FOUR]
    assert sorted(ev["payload"]["doc_id"] for ev in adds) == sorted(FOUR)
    e = _entries()
    by_id = {d["doc_id"]: d for d in A.DOCS}
    for ev in adds:
        p = ev["payload"]
        assert p["acquisition"]["fetch_log"] == "logs/2026-10-05_DCAT-002_A01_fetch.jsonl"
        assert p["acquisition"]["corpus_epoch"] == EPOCH
        assert p["acquisition"]["verification"]["sha256"] == p["content_hash"]
        assert p["content_hash"] == e[p["doc_id"]]["identity"]["sha256"], p["doc_id"]
        assert p["primary_url"] == by_id[p["doc_id"]]["fetched_url"], p["doc_id"]


def test_the_epoch_is_declared_once_with_the_four():
    rows = [json.loads(l) for l in
            (REPO / "corpus" / "evidence" / "decisions.jsonl").read_text(encoding="utf-8")
            .splitlines() if EPOCH in l]
    decl = [r for r in rows if r["event_type"] == "corpus_epoch_declared"]
    assert len(decl) == 1 and set(decl[0]["payload"]["member_doc_ids"]) == FOUR


def test_the_held_items_are_not_admitted_a_second_time():
    """R5: W3C DCAT 3 and FCSM 20-04 were already corpus. No entry other than the held one
    carries the same primary URL or hash, and neither held id gained a second manifest_add."""
    e = _entries()
    for doc, url in HELD.items():
        assert e[doc]["screening"]["decision"] == "included", doc
        sha = e[doc]["identity"]["sha256"]
        twins = [k for k, v in e.items() if k != doc and v.get("identity", {}).get("sha256") == sha]
        assert not twins, (doc, twins)
        if url:
            same_url = [k for k, v in e.items()
                        if k != doc and v.get("identity", {}).get("source_url") == url]
            assert not same_url, (doc, same_url)
    counts = {}
    for ev in _manifest_adds():
        d = ev["payload"]["doc_id"]
        if d in HELD:
            counts[d] = counts.get(d, 0) + 1
    assert all(n <= 1 for n in counts.values()), counts


def test_no_document_was_fetched_from_a_host_that_refused_by_robots():
    """fgdc.gov disallowed the NGAC deck and cdo.gov's robots.txt was unreachable (RFC 9309
    §2.3.1.4: complete disallow). Neither host may appear as an admitted document's source."""
    for d in A.DOCS:
        assert "fgdc.gov" not in d["fetched_url"] and "cdo.gov" not in d["fetched_url"], d


def test_the_extraction_driver_reads_the_addendum_epoch():
    import run_dcat_extraction as X
    run = X.COHORTS["a01"]
    assert run["EPOCH"] == EPOCH and run["RUN_ID"] != X.COHORTS["base"]["RUN_ID"]
    saved = {k: getattr(X, k) for k in run}
    try:
        for k, v in run.items():
            setattr(X, k, v)
        assert X.cohort() == sorted(FOUR)
        with pytest.raises(SystemExit):
            X.cohort("w3c-dcat-3")              # held, not a member of this epoch
    finally:
        for k, v in saved.items():
            setattr(X, k, v)
    assert X.cohort() == sorted(X.queue.corpus_epochs()["dcat-us-3-2026-10-04"])
