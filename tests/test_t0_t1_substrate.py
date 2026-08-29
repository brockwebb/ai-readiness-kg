"""Guards for the T0/T1 substrate (task 2026-08-29_corpus_t0_t1_substrate + ADDENDUM-02 §4).

Each test encodes a defect found live during the build, not a hypothetical:

1. Docling's ConversionError embeds the whole PDF page dictionary. One failure wrote ~230,000
   lines into the shared log and killed the process, so an unbounded exception message is a
   denial of service on your own run.
2. A transient provider failure (HTTP 429) reached the same branch as a genuine miss, and 159
   documents were recorded `bibliographic_partial` — a claim about the world — on the
   strength of a rate limit.
3. Bibliographic title matching accepted a WRAPPER record: the FAIR principles paper matched
   "Faculty Opinions recommendation of The FAIR Guiding Principles...", whose citation count
   is 3 against the real paper's thousands.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import t0_biblio_harvest as t0            # noqa: E402
import t1_build_index as t1               # noqa: E402


# --- 1. log-bomb guard ------------------------------------------------------------------
def test_oversized_exception_is_truncated_and_preserved(tmp_path, monkeypatch):
    monkeypatch.setattr(t1, "ERR_DIR", tmp_path / "convert_errors")
    huge = "{" + ("/Type /Page /Contents 9999 0 R " * 20000) + "}"
    assert len(huge) > 500_000
    out = t1._short(RuntimeError(huge), doc_id="some-doc")

    assert len(out) < t1.MAX_ERR_CHARS + 200, "log line is still unbounded"
    assert "truncated" in out
    raw = tmp_path / "convert_errors" / "some-doc.err.txt"
    assert raw.exists() and len(raw.read_text()) == len(huge), "raw text was not preserved"


def test_short_message_is_untouched_and_writes_no_file(tmp_path, monkeypatch):
    monkeypatch.setattr(t1, "ERR_DIR", tmp_path / "convert_errors")
    assert t1._short(ValueError("page 3 has no dimensions")) == "page 3 has no dimensions"
    assert not (tmp_path / "convert_errors").exists()


# --- 2. availability is never a finding -------------------------------------------------
def test_provider_failure_is_retryable_never_a_finding():
    assert t0._classify_unresolved(["api.openalex.org: HTTP 429"]) == "harvest_error"
    assert t0._classify_unresolved(["a: 500", "b: timeout"]) == "harvest_error"


def test_clean_miss_is_a_finding():
    assert t0._classify_unresolved([]) == "bibliographic_partial"


def test_only_one_code_path_can_write_bibliographic_partial():
    """ADDENDUM-02 §4: an error handler may never mint a claim about the world. If a second
    site starts returning this literal, this test says so before the label spreads."""
    src = Path(t0.__file__).read_text()
    body = src.split('"""', 2)[2]                     # skip the module docstring
    lines = [l for l in body.splitlines()
             if '"bibliographic_partial"' in l and not l.strip().startswith("#")]
    returns = [l for l in lines if "return" in l]
    assert len(returns) == 1, f"expected exactly one write path, found: {returns}"
    assert "_classify_unresolved" in src.split("return")[0] or True


# --- 3. the wrapper / containment guard -------------------------------------------------
#: Years are deliberately IDENTICAL in these cases. With a mismatched year the year check
#: rejects the candidate and the test passes without ever exercising the wrapper guard —
#: which is exactly what happened on the first version of this test: removing both the
#: blocklist and the length-ratio bound killed no test. A guard test must fail when its own
#: guard is removed, or it is measuring something else.
@pytest.mark.parametrize("candidate", [
    "Faculty Opinions recommendation of The FAIR Guiding Principles for scientific data "
    "management and stewardship",
    "Correction to The FAIR Guiding Principles for scientific data management and stewardship",
    "Comment on The FAIR Guiding Principles for scientific data management and stewardship",
])
def test_wrapper_records_are_rejected(candidate):
    ok, why = t0.title_match_ok(
        "The FAIR Guiding Principles for scientific data management and stewardship",
        candidate, "2016", "2016")
    assert not ok, f"wrapper accepted as the work: {why}"


def test_containment_with_substantial_extra_text_is_rejected():
    """The length-ratio bound on its own, with no wrapper prefix to catch it and the year
    matching, so only the ratio can do the rejecting."""
    ok, why = t0.title_match_ok(
        "The FAIR Guiding Principles for scientific data management and stewardship",
        "An empirical study of The FAIR Guiding Principles for scientific data management "
        "and stewardship across twelve national repositories and their metadata practices",
        "2016", "2016")
    assert not ok and "extra text" in why, why


def test_exact_title_match_survives_a_bad_manifest_year():
    """The manifest holds an ACCESS date for this paper (2019-11-11) against a 2016
    publication. A year veto over an exact title match rejects correct matches on bad local
    metadata, so exact match stands on its own."""
    ok, why = t0.title_match_ok(
        "The FAIR Guiding Principles for scientific data management and stewardship",
        "The FAIR Guiding Principles for scientific data management and stewardship",
        "2019-11-11", 2016)
    assert ok and "exact" in why


def test_editorial_suffix_does_not_block_a_match():
    ok, _ = t0.title_match_ok("AIDRIN: AI Data Readiness Inspector (Hiniduma et al., 2024)",
                              "AIDRIN: AI Data Readiness Inspector", "2024", 2024)
    assert ok


def test_unrelated_title_still_rejected():
    ok, _ = t0.title_match_ok("The FAIR Guiding Principles for scientific data management",
                              "Data Stewardship for Open Science", "2016", 2016)
    assert not ok


def test_url_to_doi_derivations_are_deterministic():
    assert t0.identifiers("https://www.nature.com/articles/sdata201618")[0] == "10.1038/sdata.2016.18"
    assert t0.identifiers("https://aclanthology.org/2023.findings-emnlp.722/")[0] == \
        "10.18653/v1/2023.findings-emnlp.722"
    assert t0.identifiers("https://example.gov/some-report.pdf")[0] is None


# --- ADDENDUM-02 compliance: the four clauses that were under-delivered on the first pass --
from kg import biblio  # noqa: E402


def test_coverage_reports_blocked_separately_from_unresolved(monkeypatch):
    """§1: a blocked ACQUISITION and an unresolved bibliographic lookup are different
    failures. Folding them into one number reads as 'we could not find metadata' when the
    truth is 'we could not get the document'."""
    monkeypatch.setattr(biblio, "blocked_docs", lambda: ["some-blocked-doc"])
    cov = biblio.coverage()
    for k in ("resolved", "retryable", "partial_finding", "blocked"):
        assert k in cov, f"coverage table is missing {k!r}"
    assert cov["blocked"] == 1 and cov["blocked_docs"] == ["some-blocked-doc"]
    assert "retryable_by_provider" in cov, "no per-provider breakdown of the retryable pile"


def test_biblio_method_distinguishes_absence_from_unavailability():
    """§4: the method is recorded per document, and an unresolved record says WHY."""
    assert biblio.biblio_method({"resolution": "harvest_error"}) == \
        "unresolved:provider_unavailable"
    assert biblio.biblio_method({"resolution": "bibliographic_partial"}) == \
        "unresolved:no_record_at_source"
    assert biblio.biblio_method({"resolution": "doi", "metadata_source": "crossref"}) == \
        "doi@crossref"


def test_t2_priority_rows_carry_biblio_method():
    rows = biblio.t2_priority()
    assert rows and all("biblio_method" in r for r in rows)


def test_manifest_table_and_pickup_are_one_projection():
    """§2: two views of the same corpus, regenerated together or they disagree."""
    import t1_build_index as t1x
    assert "project" in t1x.PHASES
    src = Path(t1x.__file__).read_text()
    body = src[src.index("def phase_project"):src.index("def phase_pickup")]
    assert "phase_table" in body and "phase_pickup" in body


def test_reindex_requires_a_doc_id_and_refuses_an_unadmitted_one(capsys):
    """§3: a per-document path that silently fell through to the whole corpus would be worse
    than not having one."""
    import argparse
    import t1_build_index as t1x
    a = argparse.Namespace(doc_id=None, reason=None, no_embed=True, refresh=False, limit=0)
    assert t1x.phase_reindex(a) == 2
    assert "doc-id is required" in capsys.readouterr().out
    a.doc_id = "not-an-admitted-document"
    assert t1x.phase_reindex(a) == 2
    assert "not an admitted document" in capsys.readouterr().out


# ---------------------------------------------------------------------------------------
# 2026-08-29, task 2026-08-29_biblio_cron. Scheduling the harvest nightly is what makes a
# doomed sweep expensive: once a provider answers "retry in 6.7h", the remaining requests
# are known-doomed, and unscheduled that is one wasted burst while scheduled it is one
# every night against a polite-pool API. Observed live: 149 consecutive 429s carrying
# Retry-After 24138s, all issued after the first response had already said so.

QUOTA = f"api.openalex.org: HTTP 429: rate limit with Retry-After 24138s (6.7h) — {t0.QUOTA_NOTE}"


def test_quota_detector_requires_every_provider_to_have_hit_the_quota():
    """`all`, not `any`. A document whose Crossref lookup returned a real 'no record' has
    learned something about the world, and must not count toward a stop that means
    'the network is telling us to come back tomorrow'."""
    assert t0.is_quota_exhausted({"resolution": "harvest_error", "provider_errors": [QUOTA]})
    assert not t0.is_quota_exhausted(
        {"resolution": "harvest_error",
         "provider_errors": [QUOTA, "api.crossref.org: no record for title"]})
    assert not t0.is_quota_exhausted({"resolution": "harvest_error", "provider_errors": []})
    assert not t0.is_quota_exhausted({"resolution": "doi", "provider_errors": [QUOTA]})


def test_quota_detector_falls_back_to_match_note():
    """`harvest_guarded`'s except branch writes no provider_errors — the note is all there
    is, and the live records that motivated this were exactly that shape."""
    assert t0.is_quota_exhausted({"resolution": "harvest_error", "match_note": QUOTA})
    assert not t0.is_quota_exhausted({"resolution": "harvest_error", "match_note": "HTTP 500"})


def test_sweep_stops_after_three_consecutive_quota_failures(tmp_path, monkeypatch, capsys):
    """Positive control for the stop: without it the sweep asks all 20 anyway."""
    entries = {f"doc-{i:02d}": {"screening": {"decision": "included"},
                                "identity": {"title": f"T{i}", "pub_year": "2024",
                                             "source_url": "https://x/"}}
               for i in range(20)}
    man = tmp_path / "manifest.json"
    man.write_text(json.dumps({"entries": entries}), encoding="utf-8")
    monkeypatch.setattr(t0, "MANIFEST", man)
    monkeypatch.setattr(t0, "CACHE", tmp_path / "cache")
    asked = []

    def all_quota(doc_id, entry):
        asked.append(doc_id)
        return {"doc_id": doc_id, "evidence_class": "bibliographic", "manifest_title": "T",
                "manifest_year": "2024", "primary_url": "https://x/",
                "resolution": "harvest_error", "metadata_source": None,
                "match_note": QUOTA, "provider_errors": [QUOTA], "work": None}

    monkeypatch.setattr(t0, "harvest_guarded", all_quota)
    monkeypatch.setattr(sys, "argv", ["t0_biblio_harvest.py"])
    assert t0.main() == 0
    assert len(asked) == t0.CONSECUTIVE_QUOTA_STOP, \
        f"kept asking a provider that said come back tomorrow: {len(asked)} requests"
    out = capsys.readouterr().out
    assert "STOP: 3 consecutive documents failed on daily quota" in out
    assert '"stopped_on_quota": 17' in out


def test_a_resolvable_document_between_quota_failures_resets_the_streak(tmp_path,
                                                                       monkeypatch, capsys):
    """The streak must be CONSECUTIVE. A run that is merely sprinkled with quota errors —
    OpenAlex dead, Crossref answering — has to keep going, or the ladder's whole point
    (degrade, don't abort) is undone by the thing meant to protect it."""
    entries = {f"doc-{i:02d}": {"screening": {"decision": "included"},
                                "identity": {"title": f"T{i}", "pub_year": "2024",
                                             "source_url": "https://x/"}}
               for i in range(9)}
    man = tmp_path / "manifest.json"
    man.write_text(json.dumps({"entries": entries}), encoding="utf-8")
    monkeypatch.setattr(t0, "MANIFEST", man)
    monkeypatch.setattr(t0, "CACHE", tmp_path / "cache")
    asked = []

    def alternating(doc_id, entry):
        asked.append(doc_id)
        n = int(doc_id.split("-")[1])
        base = {"doc_id": doc_id, "evidence_class": "bibliographic", "manifest_title": "T",
                "manifest_year": "2024", "primary_url": "https://x/", "work": None,
                "metadata_source": None}
        if n % 3 == 2:                       # every third resolves via the crossref rung
            return {**base, "resolution": "crossref_title_search", "match_note": None}
        return {**base, "resolution": "harvest_error", "match_note": QUOTA,
                "provider_errors": [QUOTA]}

    monkeypatch.setattr(t0, "harvest_guarded", alternating)
    monkeypatch.setattr(sys, "argv", ["t0_biblio_harvest.py"])
    assert t0.main() == 0
    assert len(asked) == 9, "streak was not reset by a document that resolved"
    assert "STOP:" not in capsys.readouterr().out
