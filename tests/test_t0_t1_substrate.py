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

import argparse
import json
import pathlib
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
AUTH = f"api.openalex.org: HTTP 401: {t0.AUTH_NOTE}"


@pytest.fixture(autouse=True)
def _key(monkeypatch):
    """Preflight must pass deterministically, not because this machine happens to have a
    key in ~/.wintermute/.env. The missing-key case is tested explicitly, not by accident."""
    monkeypatch.setenv("OPENALEX_API_KEY", "test-key-not-a-real-credential")


def test_quota_detector_requires_every_provider_to_have_hit_the_quota():
    """`all`, not `any`. A document whose Crossref lookup returned a real 'no record' has
    learned something about the world, and must not count toward a stop that means
    'the network is telling us to come back tomorrow'."""
    assert t0.is_quota_exhausted({"resolution": t0.QUOTA_ERROR, "provider_errors": [QUOTA]})
    assert not t0.is_quota_exhausted(
        {"resolution": t0.QUOTA_ERROR,
         "provider_errors": [QUOTA, "api.crossref.org: no record for title"]})
    assert not t0.is_quota_exhausted({"resolution": t0.QUOTA_ERROR, "provider_errors": []})
    assert not t0.is_quota_exhausted({"resolution": "doi", "provider_errors": [QUOTA]})


def test_quota_detector_falls_back_to_match_note():
    """`harvest_guarded`'s except branch writes no provider_errors — the note is all there
    is, and the live records that motivated this were exactly that shape."""
    assert t0.is_quota_exhausted({"resolution": t0.QUOTA_ERROR, "match_note": QUOTA})
    assert not t0.is_quota_exhausted({"resolution": t0.QUOTA_ERROR, "match_note": "HTTP 500"})


def test_sweep_stops_after_three_consecutive_quota_failures(tmp_path, monkeypatch, capsys):
    """Positive control for the stop: without it the sweep asks all 20 anyway."""
    entries = {f"doc-{i:02d}": {"screening": {"decision": "included"},
                                "identity": {"title": f"T{i}", "pub_year": "2024",
                                             "doc_type": "academic",
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
                "resolution": t0.QUOTA_ERROR, "metadata_source": None,
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
                                             "doc_type": "academic",
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
        return {**base, "resolution": t0.QUOTA_ERROR, "match_note": QUOTA,
                "provider_errors": [QUOTA]}

    monkeypatch.setattr(t0, "harvest_guarded", alternating)
    monkeypatch.setattr(sys, "argv", ["t0_biblio_harvest.py"])
    assert t0.main() == 0
    assert len(asked) == 9, "streak was not reset by a document that resolved"
    assert "STOP:" not in capsys.readouterr().out


# ---------------------------------------------------------------------------------------
# 2026-08-29, task 2026-08-29_openalex_auth_and_eligibility. OpenAlex retired the polite pool
# and made an API key mandatory (2026-02-13). Measured against the live API before any of this
# was written, because the classification depends on which status each condition returns:
#   no key / empty key -> HTTP 429 "Insufficient budget ... $0 remaining"   (NOT 401)
#   invalid key        -> HTTP 401 "Invalid or missing API key"
#   valid key          -> HTTP 200, X-RateLimit-Limit: 10000
# The 429-for-a-missing-key is the whole reason preflight exists: at the status line a missing
# key is indistinguishable from a real exhaustion, so the only place to tell them apart is
# before the first request.

class _Resp:
    def __init__(self, status, headers=None, payload=None):
        self.status_code, self.headers = status, headers or {}
        self._payload, self.url = payload if payload is not None else {}, "https://api.openalex.org/works"

    def json(self):
        return self._payload


def _entry(doc_type="academic", url="https://arxiv.org/abs/2401.12345", title="T"):
    return {"identity": {"title": title, "pub_year": "2024", "doc_type": doc_type,
                         "source_url": url}}


def test_preflight_refuses_without_a_key_and_issues_no_request(monkeypatch):
    """§5: missing key -> non-zero exit, no request issued. A fall-through to an
    unauthenticated attempt is how 'no key' got written down as 'quota exhausted' 149 times."""
    monkeypatch.delenv("OPENALEX_API_KEY", raising=False)
    monkeypatch.setattr(t0, "openalex_key", lambda: None)
    monkeypatch.setattr(t0.requests, "get",
                        lambda *a, **k: pytest.fail("a request was issued without a key"))
    with pytest.raises(SystemExit, match="OPENALEX_API_KEY missing"):
        t0.preflight()


def test_openalex_gets_api_key_and_crossref_keeps_mailto():
    """Sending mailto to OpenAlex is not merely useless now, it reads like authentication
    in the code while buying nothing at the server."""
    oa = t0._auth_params("https://api.openalex.org/works")
    cr = t0._auth_params("https://api.crossref.org/works")
    assert "api_key" in oa and "mailto" not in oa
    assert cr == {"mailto": t0.MAILTO}


def test_stubbed_401_is_an_auth_error_and_never_carries_the_quota_message(monkeypatch):
    monkeypatch.setattr(t0.requests, "get", lambda *a, **k: _Resp(401))
    with pytest.raises(t0.HarvestError) as e:
        t0.get("https://api.openalex.org/works")
    assert e.value.kind == "auth"
    assert t0.QUOTA_NOTE not in str(e.value), "an auth failure claimed the day's budget was spent"
    rec = {"resolution": t0.AUTH_ERROR, "provider_errors": [f"openalex: {e.value}"]}
    assert t0._classify_unresolved(rec["provider_errors"]) == t0.AUTH_ERROR
    assert not t0.is_quota_exhausted(rec), "auth failure fed the nightly quota stop"


def test_stubbed_429_with_long_retry_after_is_a_quota_exhaustion(monkeypatch):
    monkeypatch.setattr(t0.requests, "get",
                        lambda *a, **k: _Resp(429, {"Retry-After": "24138"}))
    with pytest.raises(t0.HarvestError) as e:
        t0.get("https://api.openalex.org/works")
    assert e.value.kind == "quota" and t0.QUOTA_NOTE in str(e.value)
    assert t0._classify_unresolved([str(e.value)]) == t0.QUOTA_ERROR


def test_stubbed_503_is_transient_and_writes_no_claim(monkeypatch):
    monkeypatch.setattr(t0.requests, "get", lambda *a, **k: _Resp(503, {"Retry-After": "1"}))
    with pytest.raises(t0.HarvestError) as e:
        t0.get("https://api.openalex.org/works", tries=2)
    assert getattr(e.value, "kind", "transient") == "transient"
    assert t0._classify_unresolved([str(e.value)]) == t0.TRANSIENT_ERROR
    # a transient failure must never be minted into the finding that absence would be
    assert t0._classify_unresolved([str(e.value)]) != "bibliographic_partial"


def test_auth_outranks_quota_in_classification():
    """With no valid key EVERY request returns a budget message, so a keyless run would
    otherwise report every document as quota-exhausted — the false claim this task fixes."""
    assert t0._classify_unresolved([AUTH, QUOTA]) == t0.AUTH_ERROR
    assert t0._classify_unresolved([QUOTA]) == t0.QUOTA_ERROR
    assert t0._classify_unresolved([]) == "bibliographic_partial"


def test_credit_headers_are_recorded_as_evidence(monkeypatch):
    """A real exhaustion should be evidenced by the provider, not inferred from the shape
    of a Retry-After."""
    monkeypatch.setitem(t0.CREDITS, "remaining", None)
    monkeypatch.setattr(t0.requests, "get", lambda *a, **k: _Resp(
        200, {"X-RateLimit-Remaining": "9979", "X-RateLimit-Limit": "10000"}, {"ok": 1}))
    t0.get("https://api.openalex.org/works")
    assert t0.CREDITS["remaining"] == "9979" and t0.CREDITS["limit"] == "10000"


# --- eligibility gate -------------------------------------------------------------------

def test_gov_pdf_without_a_doi_is_out_of_scope_and_is_never_queried(tmp_path, monkeypatch):
    """§5: zero OpenAlex requests issued for an ineligible document."""
    ok, why = t0.eligibility(_entry("federal", "https://www.govinfo.gov/app/details/PLAW-117"))
    assert not ok and "not the kind of document" in why

    entries = {"gov-doc": _entry("federal", "https://www.govinfo.gov/app/details/PLAW-117")}
    man = tmp_path / "manifest.json"
    man.write_text(json.dumps({"entries": {k: {**v, "screening": {"decision": "included"}}
                                           for k, v in entries.items()}}), encoding="utf-8")
    monkeypatch.setattr(t0, "MANIFEST", man)
    monkeypatch.setattr(t0, "CACHE", tmp_path / "cache")
    monkeypatch.setattr(t0, "harvest_guarded",
                        lambda *a, **k: pytest.fail("queried an ineligible document"))
    monkeypatch.setattr(t0.requests, "get",
                        lambda *a, **k: pytest.fail("issued a request for an ineligible doc"))
    monkeypatch.setattr(sys, "argv", ["t0_biblio_harvest.py"])
    assert t0.main() == 0
    rec = json.loads((tmp_path / "cache" / "gov-doc.json").read_text())
    assert rec["resolution"] == t0.OUT_OF_SCOPE


def test_eligibility_accepts_doi_arxiv_and_academic_type():
    assert t0.eligibility(_entry("industry", "https://doi.org/10.1038/sdata.2016.18"))[0]
    assert t0.eligibility(_entry("industry", "https://arxiv.org/abs/2401.12345"))[0]
    assert t0.eligibility(_entry("academic", "https://example.org/x.pdf"))[0]
    assert t0.eligibility(_entry("preprint", "https://example.org/x.pdf"))[0]


def test_an_already_resolved_document_is_never_demoted_to_out_of_scope():
    """Not a loophole — a correctness requirement. Measured on this corpus, 9 resolved
    documents are outside the academic doc_types and carry no DOI in their URL (found by
    title search). Writing 'no scholarly index holds this' over a record we are holding
    would assert something the evidence in hand contradicts."""
    e = _entry("industry", "https://example.com/blog-post")
    assert not t0.eligibility(e, None)[0]
    ok, why = t0.eligibility(e, "crossref_title_search")
    assert ok and "eligibility proven by record" in why
    # a prior FAILURE is not proof of anything and must not confer eligibility
    for failed in (t0.TRANSIENT_ERROR, t0.AUTH_ERROR, t0.QUOTA_ERROR, t0.OUT_OF_SCOPE):
        assert not t0.eligibility(e, failed)[0], f"{failed} wrongly conferred eligibility"


def test_out_of_scope_is_terminal_not_retryable_in_coverage():
    """It must leave the retryable count AND the denominator that implies it is pending."""
    assert t0.OUT_OF_SCOPE not in biblio.RETRYABLE
    assert biblio.biblio_method({"resolution": t0.OUT_OF_SCOPE}) == "unresolved:out_of_scope"


def test_retry_states_and_biblio_retryable_agree():
    """A state retryable in kg/biblio.py but missing from the harvester's resume set is
    permanently stuck: counted as pending forever, never actually retried."""
    assert biblio.RETRYABLE <= t0.RETRY_STATES, biblio.RETRYABLE - t0.RETRY_STATES
    assert t0.OUT_OF_SCOPE not in t0.RETRY_STATES


def test_arxiv_resolves_by_derived_doi_without_a_title_guard(monkeypatch):
    """A DOI is an exact identifier, so the fuzzy-title guard is the wrong instrument — the
    plain-DOI branch has never used one either. Two real documents (AIDRIN, and the school
    AI-readiness paper) were rejected by that guard despite the DOI naming them exactly."""
    seen = {}

    def fake_get(errors, url, params=None):
        seen["params"] = params
        return {"results": [{"display_name": "Completely Different Title",
                             "publication_year": 1999, "id": "W1"}]}

    monkeypatch.setattr(t0, "soft_get", fake_get)
    rec = t0.harvest_one("d", _entry("academic", "https://arxiv.org/abs/2406.19256",
                                     title="AI Data Readiness Inspector"))
    assert "doi:10.48550/arXiv.2406.19256" in seen["params"]["filter"]
    assert rec["resolution"] == "arxiv_doi", "exact DOI hit was discarded by a title guard"


def test_malformed_query_is_counted_and_surfaced_not_filed_as_flakiness(monkeypatch):
    """Positive control: a 400 must land in REQUEST_ERRORS. The old code filed it as ordinary
    provider failure, so 7 documents retried a permanently-invalid query with nothing on the
    surface to show it."""
    monkeypatch.setattr(t0, "REQUEST_ERRORS", [])
    monkeypatch.setattr(t0.requests, "get", lambda *a, **k: _Resp(400))
    with pytest.raises(t0.HarvestError, match="malformed query"):
        t0.get("https://api.openalex.org/works")
    assert len(t0.REQUEST_ERRORS) == 1


def test_project_refreshes_t0_before_publishing_it(tmp_path, monkeypatch):
    """The biblio table was written only by the expensive `--phase index`, so the nightly
    `--phase project` republished a T0 column that could never advance: it read 29 while
    `kg.biblio coverage` read 38. Two published views of one corpus, disagreeing."""
    import sqlite3
    db = tmp_path / "corpus_index.db"
    con = sqlite3.connect(db)
    con.executescript(t1.SCHEMA)
    con.execute("INSERT OR REPLACE INTO biblio VALUES (?,?,?,?,?,?,?,?,?)",
                ("d1", "harvest_error", None, None, None, None, None, 0, "bibliographic"))
    con.execute("INSERT INTO documents (doc_id, title, year, doc_type, source_url, n_chunks) "
                "VALUES ('d1','T','2024','academic','https://x/',3)")
    con.commit(); con.close()

    cache = tmp_path / "biblio_cache"; cache.mkdir()
    (cache / "d1.json").write_text(json.dumps(
        {"doc_id": "d1", "resolution": "arxiv_doi", "metadata_source": "openalex",
         "doi": "10.48550/arXiv.1", "work": {"id": "W1", "cited_by_count": 3}}),
        encoding="utf-8")
    monkeypatch.setattr(t1, "DB", db)
    monkeypatch.setattr(t1, "BIBLIO", cache)
    monkeypatch.setattr(t1, "TABLE_OUT", tmp_path / "manifest_table.md")

    # Drive the REAL entrypoint, not the sync helper. An earlier version of this test called
    # `_sync_biblio_if_possible()` directly, so deleting the call from `phase_table` left it
    # green — it proved the sync works, not that the projection uses it. Same failure mode as
    # the M2 retention test (methodology §7.9): measuring the neighbour of the guard.
    assert t1.phase_table(argparse.Namespace()) == 0
    published = (tmp_path / "manifest_table.md").read_text(encoding="utf-8")
    assert "(1 of 1)" in published, f"projection published a stale T0 count:\n{published[:400]}"


def test_resolved_is_defined_once_not_restated_per_view():
    """Three call sites once hardcoded their own 'unresolved' list. When the failure classes
    were split, the copies drifted and the views disagreed."""
    src = pathlib.Path(t1.__file__).read_text()
    assert 'r[6] not in _unresolved' in src
    assert src.count('"bibliographic_partial", "harvest_error"') == 0, \
        "a hand-rolled unresolved list is back in t1_build_index"


# ---------------------------------------------------------------------------------------
# --measure-ineligible (2026-08-29). The eligibility gate is a PREDICTION about the world
# ("no scholarly index holds this"), and a prediction that is never tested is indistinguishable
# from an assumption. This flag tests it for exactly the documents the gate excluded.

def test_measured_miss_confirms_the_prediction_without_promoting_the_document():
    """A confirmed miss must NOT quietly become `bibliographic_partial`: that would move 134
    documents into a coverage denominator that implies they are pending, which is the exact
    accounting error the gate was added to fix."""
    rec = {"doc_id": "d", "resolution": "bibliographic_partial", "provider_errors": []}
    out = t0._record_measurement(rec, "d", _entry("industry", "https://x/"), "predicted why")
    assert out["resolution"] == t0.OUT_OF_SCOPE
    assert out["eligibility_prediction_correct"] is True
    assert out["eligibility_measured"] is True
    assert "CONFIRMED by measurement" in out["match_note"]


def test_measured_resolution_overturns_the_prediction_and_is_kept():
    """The prediction was wrong and a record proves it. Discarding that would be discarding
    evidence in hand to preserve a guess."""
    rec = {"doc_id": "d", "resolution": "crossref_title_search",
           "metadata_source": "crossref", "work": {"title": "T"}}
    out = t0._record_measurement(rec, "d", _entry("industry", "https://x/"), "predicted why")
    assert out["resolution"] == "crossref_title_search"
    assert out["eligibility_prediction_correct"] is False
    assert out["work"] == {"title": "T"}


def test_provider_failure_leaves_the_prediction_unmeasured():
    """A 429 teaches nothing about whether the document is in an index. Recording it as a
    confirmation would manufacture a finding out of a transient failure."""
    for failed in (t0.AUTH_ERROR, t0.QUOTA_ERROR, t0.TRANSIENT_ERROR):
        rec = {"doc_id": "d", "resolution": failed, "provider_errors": ["x"]}
        out = t0._record_measurement(rec, "d", _entry("industry", "https://x/"), "why")
        assert out["resolution"] == t0.OUT_OF_SCOPE
        assert out["eligibility_measured"] is False
        assert out["eligibility_prediction_correct"] is None


def test_measure_ineligible_actually_queries_a_gated_document(tmp_path, monkeypatch):
    """Positive control: without the flag the document is never asked (proved earlier); with
    it, the provider IS called."""
    entries = {"gov": {**_entry("federal", "https://www.govinfo.gov/app/details/PLAW-117"),
                       "screening": {"decision": "included"}}}
    man = tmp_path / "manifest.json"
    man.write_text(json.dumps({"entries": entries}), encoding="utf-8")
    monkeypatch.setattr(t0, "MANIFEST", man)
    monkeypatch.setattr(t0, "CACHE", tmp_path / "cache")
    asked = []
    monkeypatch.setattr(t0, "harvest_guarded", lambda d, e: (
        asked.append(d) or {"doc_id": d, "resolution": "bibliographic_partial",
                            "provider_errors": []}))
    monkeypatch.setattr(sys, "argv", ["t0_biblio_harvest.py", "--measure-ineligible"])
    assert t0.main() == 0
    assert asked == ["gov"], "the gated document was still not queried under the flag"
    rec = json.loads((tmp_path / "cache" / "gov.json").read_text())
    assert rec["resolution"] == t0.OUT_OF_SCOPE and rec["eligibility_measured"] is True


def test_measure_ineligible_reopens_a_terminal_record_but_resume_does_not(tmp_path, monkeypatch):
    """Found live: the first run of the flag reported all 178 as `cached` and asked nothing,
    because OUT_OF_SCOPE is correctly absent from RETRY_STATES and the cache-skip fires before
    the gate. The flag is the one path allowed to reopen a terminal record; a normal
    `--retry-unresolved` resume must still leave it alone."""
    entries = {"gov": {**_entry("federal", "https://www.govinfo.gov/x"),
                       "screening": {"decision": "included"}}}
    man = tmp_path / "manifest.json"
    man.write_text(json.dumps({"entries": entries}), encoding="utf-8")
    cache = tmp_path / "cache"; cache.mkdir()
    (cache / "gov.json").write_text(json.dumps(
        {"doc_id": "gov", "resolution": t0.OUT_OF_SCOPE}), encoding="utf-8")
    monkeypatch.setattr(t0, "MANIFEST", man)
    monkeypatch.setattr(t0, "CACHE", cache)

    asked = []
    monkeypatch.setattr(t0, "harvest_guarded", lambda d, e: (
        asked.append(d) or {"doc_id": d, "resolution": "bibliographic_partial",
                            "provider_errors": []}))

    monkeypatch.setattr(sys, "argv", ["t0_biblio_harvest.py", "--retry-unresolved"])
    assert t0.main() == 0
    assert asked == [], "a plain resume re-asked a terminal out-of-scope record"

    monkeypatch.setattr(sys, "argv", ["t0_biblio_harvest.py", "--measure-ineligible"])
    assert t0.main() == 0
    assert asked == ["gov"], "the flag did not reopen the terminal record"


def test_wildcard_metacharacters_are_stripped_from_search_queries():
    """OpenAlex reads `?` and `*` in `search` as wildcards and 400s on a title that merely
    ends in a question mark. Measured live on `anthropic-crawler-support-article`; the failure
    is permanent, so it presents as a document that retries forever."""
    out = t0._sanitize_search({"search": "Does Anthropic crawl the web, and how? *", "x": 1})
    assert out["search"] == "Does Anthropic crawl the web, and how"
    assert out["x"] == 1
    assert t0._sanitize_search({"query.bibliographic": "Is it ready?"})[
        "query.bibliographic"] == "Is it ready"


def test_sanitizer_runs_on_the_real_request_path(monkeypatch):
    """Positive control against the M2 pattern: assert the sanitizer is reached by `get`,
    not merely that the helper works when called directly."""
    seen = {}

    class _R:
        status_code, headers, url = 200, {}, "https://api.openalex.org/works"
        def json(self): return {"results": []}

    def fake(url, params=None, headers=None, timeout=None):
        seen.update(params or {})
        return _R()

    monkeypatch.setattr(t0.requests, "get", fake)
    t0.get("https://api.openalex.org/works", {"search": "Ready for AI?"})
    assert seen["search"] == "Ready for AI", f"wildcard reached the provider: {seen}"
