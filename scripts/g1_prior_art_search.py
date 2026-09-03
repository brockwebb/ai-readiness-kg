#!/usr/bin/env python3
"""Logged prior-art search for the G1 EVAL tier (task 2026-09-02_g1_eval_prior_art §1).

Runs every query family in at least two phrasings against OpenAlex, arXiv and Semantic
Scholar, plus forward/backward citation walks from the two anchor works named in the task,
and writes one JSON log with every query string, source, UTC timestamp and hit count.
Zero model calls: metadata APIs only.

    python scripts/g1_prior_art_search.py --out docs/research/2026-09-02_g1_eval_prior_art_query_log.json

Auth: `OPENALEX_API_KEY` / `SEMANTIC_SCHOLAR_API_KEY` from the environment, else
~/.wintermute/.env (the idiom of scripts/t0_biblio_harvest.py; a missing OpenAlex key is a
429 that is indistinguishable from exhaustion, so it is checked before the first request).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

import requests

UA = "WintermuteAcceptance/0.1 (research; brockwebb45@gmail.com)"
TOP_N = 15
# Semantic Scholar's public tier is 1 req/s shared; even keyed calls 429 in bursts, so
# retries are spaced and a persistent 429 is *recorded* as a search failure, never hidden.
S2_RETRIES = 5
S2_BACKOFF = [3, 8, 15, 30, 60]

ANCHORS = {
    # "Possible or Definite?" — the clinical uncertainty-preservation benchmark named in the task.
    "arxiv_2606_18471": {"arxiv": "2606.18471", "doi": "10.48550/arXiv.2606.18471"},
    # van der Bles et al. 2019, Royal Society Open Science 6:181870.
    "vanderbles_2019": {"doi": "10.1098/rsos.181870"},
}

# Query families from the task (§1), each in >= 2 phrasings. Family 5 also runs on the web
# (WebSearch) because grey-literature audits (Pew, Reuters Institute, NIST) are not indexed
# by the scholarly APIs; those hits are logged in the memo's query table by hand.
#
# Each phrasing is (natural-language query for OpenAlex/Semantic Scholar, arXiv query).
# Run 1 (2026-09-02, kept as *_run1_fulltext.json) used OpenAlex's default full-text
# `search=` and an AND-of-every-token arXiv query; the former ranked 1987 AHP papers above
# anything on-topic and the latter returned 0 for most phrasings. Run 2 uses
# `title_and_abstract.search` and hand-written arXiv boolean queries over `abs:`/`ti:`.
FAMILIES = {
    "F1_numeric_uncertainty_preservation": [
        ("numeric uncertainty preservation large language model summarization",
         'abs:"uncertainty" AND abs:"preserv" AND (abs:summarization OR abs:paraphrase) AND (abs:LLM OR abs:"language model")'),
        ("margin of error confidence interval LLM paraphrase restatement",
         '(abs:"margin of error" OR abs:"confidence interval") AND (abs:LLM OR abs:"language model") AND (abs:summar OR abs:paraphras OR abs:restat OR abs:generat)'),
        ("standard error statistical estimate language model summary fidelity",
         '(abs:"standard error" OR abs:"sampling error") AND (abs:LLM OR abs:"large language model") AND (abs:summar OR abs:report)'),
        ("uncertainty interval retrieval-augmented generation numeric answer",
         'abs:"retrieval-augmented" AND (abs:"confidence interval" OR abs:"uncertainty interval" OR abs:"margin of error")'),
    ],
    "F2_quantitative_claim_fidelity": [
        ("numeric hallucination summarization",
         '(abs:"numeric hallucination" OR abs:"numerical hallucination" OR abs:"quantity hallucination" OR abs:"number hallucination")'),
        ("number faithfulness abstractive summarization",
         '(abs:numer OR abs:quantit OR abs:number) AND abs:faithful AND abs:summarization'),
        ("quantitative claim fidelity language model",
         '(abs:"numerical claim" OR abs:"quantitative claim" OR abs:"statistical claim") AND (abs:LLM OR abs:"language model" OR abs:"fact-check")'),
        ("numerical consistency factual summarization evaluation",
         'abs:"factual consistency" AND abs:summarization AND (abs:numer OR abs:number OR abs:quantit)'),
    ],
    "F3_hedging_epistemic_preservation": [
        ("hedging preservation summarization language model",
         '(abs:hedg OR abs:hedges) AND (abs:summar OR abs:generat) AND (abs:LLM OR abs:"language model")'),
        ("epistemic uncertainty preservation clinical text LLM",
         '(abs:"uncertainty preservation" OR abs:"preserve uncertainty" OR abs:"preserving uncertainty" OR abs:"certainty assertion")'),
        ("speculation cue certainty summarization evaluation",
         '(abs:speculat OR abs:"epistemic stance" OR abs:overgeneraliz OR abs:overclaim) AND abs:summar AND (abs:LLM OR abs:"language model")'),
    ],
    "F4_uncertainty_communication_statistics": [
        ("communicating uncertainty statistics margin of error public",
         'abs:"communicating uncertainty" AND (abs:statistic OR abs:"margin of error")'),
        ("sampling error communication official statistics guidance",
         'abs:"official statistics" AND (abs:uncertainty OR abs:"sampling error") AND (abs:communicat OR abs:report OR abs:user)'),
        ("communicating statistical uncertainty numeric verbal formats",
         'abs:uncertainty AND abs:communicat AND (abs:verbal OR abs:numeric OR abs:"margin of error") AND abs:public'),
    ],
    # F6 (added after run 2): the qualifier classes G1 actually carries — caveats/qualifiers,
    # coefficient of variation, differential-privacy noise parameters, vintage/as-of dates —
    # none of which the task's five families name directly.
    "F6_numeric_qualifier_preservation": [
        ("caveat qualifier preservation LLM summarization decontextualization",
         '(abs:caveat OR abs:qualifier OR abs:decontextualiz) AND (abs:summar OR abs:compress) AND (abs:LLM OR abs:"language model")'),
        ("coefficient of variation relative standard error LLM generated text statistics",
         '(abs:"coefficient of variation" OR abs:"relative standard error") AND (abs:LLM OR abs:"language model" OR abs:chatbot)'),
        ("differential privacy noise disclosure LLM answer official statistics",
         'abs:"differential privacy" AND (abs:"official statistics" OR abs:census) AND (abs:LLM OR abs:"language model" OR abs:chatbot)'),
        ("data vintage release date stale statistics LLM answer",
         '(abs:vintage OR abs:"as of" OR abs:stale OR abs:outdated) AND abs:statistic AND (abs:LLM OR abs:"language model") AND (abs:answer OR abs:retriev)'),
    ],
    # F7 (task 2026-09-02_g1_eval_probe_family_v0 step 0): the F6 evidence that DP noise
    # parameters and vintage are uncharted rested on 12 queries. F7 widens that with the
    # vocabulary of the neighbouring fields (disclosure-avoidance user guidance, temporal
    # validity / stale-answer benchmarks, rounding-precision preservation) so a falsifier
    # phrased in THEIR words would be reached. Run 4 log: *_query_log_f7.json.
    "F7_dp_vintage_rounding": [
        ("disclosure avoidance noise user guidance large language model",
         '(abs:"disclosure avoidance" OR abs:"differential privacy") AND abs:noise AND (abs:LLM OR abs:"language model") AND (abs:guidance OR abs:user)'),
        ("differential privacy communicating noisy statistics data users",
         'abs:"differential privacy" AND (abs:communicat OR abs:"data users" OR abs:"user expectations") AND (abs:statistic OR abs:census)'),
        ("temporal validity statistics answer large language model release date",
         '(abs:"temporal validity" OR abs:"time-sensitive") AND (abs:LLM OR abs:"language model") AND (abs:statistic OR abs:"release date" OR abs:answer)'),
        ("outdated statistic stale answer official data vintage",
         '(abs:outdated OR abs:stale) AND (abs:LLM OR abs:"language model") AND (abs:statistic OR abs:"official data" OR abs:vintage)'),
        ("data release version temporal misalignment retrieval augmented",
         'abs:"retrieval-augmented" AND (abs:"temporal misalignment" OR abs:"temporal" OR abs:version) AND (abs:release OR abs:vintage OR abs:outdated)'),
        ("number rounding precision preservation summarization",
         '(abs:rounding OR abs:precision) AND abs:number AND (abs:summariz OR abs:paraphras OR abs:restat) AND (abs:LLM OR abs:"language model")'),
    ],
    "F5_answer_engines_official_statistics": [
        ("generative search engine official statistics accuracy audit",
         '(abs:"generative search" OR abs:"answer engine" OR abs:"AI overview" OR abs:chatbot) AND (abs:"official statistics" OR abs:census OR abs:"statistical agency")'),
        ("AI answer engine citing statistics accuracy margin of error",
         '(abs:"generative search" OR abs:"answer engine" OR abs:"AI assistant") AND abs:audit AND (abs:accura OR abs:citation)'),
        ("LLM chatbot statistical data accuracy evaluation official statistics",
         '(abs:LLM OR abs:"language model") AND abs:"official statistics"'),
    ],
}

# Named works whose existence the task presupposes or that the standing literature names as
# the families to place (FActScore, SummaC, QAGS, FEQA, AlignScore, RAGAS, HHEM, …), plus
# candidates surfaced by run 1 that need resolving to a citable record. Looked up by title
# so the log carries the resolution rather than an assumption.
NAMED_LOOKUPS = [
    "Generalization bias in large language model summarization of scientific research",
    "Reducing Quantity Hallucinations in Abstractive Summarization",
    "QuanTemp: A real-world open-domain benchmark for fact-checking numerical claims",
    "Knowing When to Ask - Bridging Large Language Models and Data",
    "UNCLE: Benchmarking Uncertainty Expressions in Long-Form Generation",
    "LoGU: Long-form Generation with Uncertainty Expressions",
    "The effects of communicating uncertainty on public trust in facts and numbers",
    "The effects of communicating uncertainty around statistics, on public trust",
    "Communicating Uncertainty in Official Economic Statistics: An Appraisal Fifty Years after Morgenstern",
    "Measuring and Communicating the Uncertainty in Official Economic Statistics",
    "Should we include margins of error in public opinion polls?",
    "The Slop Paradox: How Synthetic Standardization Erodes Clinical Uncertainty",
    "LOOMSUM: Weaving Quantitative and Narrative Evidence for Faithful Long Text-Table Summarization",
    "FActScore: Fine-grained Atomic Evaluation of Factual Precision in Long Form Text Generation",
    "SummaC: Re-Visiting NLI-based Models for Inconsistency Detection in Summarization",
    "Asking and Answering Questions to Evaluate the Factual Consistency of Summaries",
    "FEQA: A Question Answering Evaluation Framework for Faithfulness Assessment in Abstractive Summarization",
    "AlignScore: Evaluating Factual Consistency with a Unified Alignment Function",
    "RAGAS: Automated Evaluation of Retrieval Augmented Generation",
    "FaithBench: A Diverse Hallucination Benchmark for Summarization by Modern LLMs",
    "Understanding and Using American Community Survey Data: What All Data Users Need to Know",
    "Are LLMs ready to help non-expert users to make charts of official statistics data?",
    "Moneyball with LLMs: Analyzing Tabular Summarization in Sports Narratives",
    "Hedges in scientific writing large language models",
    "Do large language models preserve hedges when summarizing scientific abstracts",
    "Numerical reasoning faithfulness in data-to-text generation hallucination",
]


# F7 named lookups (same task, step 0): temporal-knowledge benchmarks and DP user-expectation
# work, resolved by title so the log carries the resolution. Selected with --named-set f7.
F7_NAMED_LOOKUPS = [
    "FreshLLMs: Refreshing Large Language Models with Search Engine Augmentation",
    "A Dataset for Answering Time-Sensitive Questions",
    "RealTime QA: What's the Answer Right Now?",
    "I need a better description: An Investigation Into User Expectations For Differential Privacy",
    "Disclosure Avoidance for the 2020 Census: An Introduction",
    "The 2020 Census Disclosure Avoidance System TopDown Algorithm",
]
NAMED_SETS = {"all": NAMED_LOOKUPS + F7_NAMED_LOOKUPS, "base": NAMED_LOOKUPS, "f7": F7_NAMED_LOOKUPS}


def _env_key(name: str) -> str | None:
    v = os.environ.get(name)
    if v:
        return v
    p = Path.home() / ".wintermute" / ".env"
    if p.exists():
        for line in p.read_text().splitlines():
            if "=" in line and line.split("=", 1)[0].strip() == name:
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class Log:
    def __init__(self) -> None:
        self.entries: list[dict] = []

    def add(self, **kw) -> dict:
        kw.setdefault("ts_utc", _now())
        self.entries.append(kw)
        print(f"[{kw['source']}] {kw.get('family', '-')} | {kw['query']!r} -> "
              f"{kw.get('hit_count')} ({kw.get('status')})", file=sys.stderr)
        return kw


# ---------------------------------------------------------------- OpenAlex
class OpenAlex:
    base = "https://api.openalex.org"

    def __init__(self, key: str) -> None:
        self.key = key

    def _get(self, path: str, **params) -> dict:
        params["api_key"] = self.key
        r = requests.get(self.base + path, params=params, headers={"User-Agent": UA}, timeout=60)
        if r.status_code != 200:
            raise RuntimeError(f"openalex {r.status_code}: {r.text[:200]}")
        return r.json()

    @staticmethod
    def _row(w: dict) -> dict:
        return {"id": w.get("id"), "doi": w.get("doi"), "title": w.get("title") or w.get("display_name"),
                "year": w.get("publication_year"), "cited_by": w.get("cited_by_count"),
                "venue": ((w.get("primary_location") or {}).get("source") or {}).get("display_name"),
                "oa_url": ((w.get("best_oa_location") or {}).get("pdf_url")
                           or (w.get("best_oa_location") or {}).get("landing_page_url")),
                "type": w.get("type")}

    def search(self, q: str, mode: str = "title_abstract") -> tuple[int, list[dict]]:
        params = {"per-page": TOP_N,
                  "select": "id,doi,title,display_name,publication_year,cited_by_count,primary_location,best_oa_location,type"}
        if mode == "fulltext":
            params["search"] = q
        else:
            # Comma is OpenAlex's filter separator, so it cannot appear inside the value.
            params["filter"] = f"title_and_abstract.search:{q.replace(',', ' ')}"
            params["sort"] = "relevance_score:desc"
        d = self._get("/works", **params)
        return d["meta"]["count"], [self._row(w) for w in d["results"]]

    def by_title(self, title: str) -> tuple[int, list[dict]]:
        # Comma is the filter separator; '?' and ':' inside a title.search value returned
        # 400 in run 2 (two titles lost). All three are dropped from the value.
        cleaned = title.replace(",", " ").replace("?", "").replace(":", " ")
        d = self._get("/works", filter=f"title.search:{cleaned}", **{"per-page": 5},
                      select="id,doi,title,display_name,publication_year,cited_by_count,primary_location,best_oa_location,type")
        return d["meta"]["count"], [self._row(w) for w in d["results"]]

    def by_doi(self, doi: str) -> dict | None:
        try:
            return self._get(f"/works/https://doi.org/{doi}")
        except RuntimeError as e:
            if "404" in str(e):
                return None
            raise

    def cited_by(self, work_id: str, q: str | None = None) -> tuple[int, list[dict]]:
        wid = work_id.rsplit("/", 1)[-1]
        params = {"filter": f"cites:{wid}", "per-page": TOP_N, "sort": "cited_by_count:desc",
                  "select": "id,doi,title,display_name,publication_year,cited_by_count,primary_location,best_oa_location,type"}
        if q:
            params["search"] = q
        d = self._get("/works", **params)
        return d["meta"]["count"], [self._row(w) for w in d["results"]]

    def references(self, work: dict) -> tuple[int, list[dict]]:
        ids = work.get("referenced_works") or []
        rows = []
        for i in range(0, min(len(ids), 100), 50):
            chunk = "|".join(x.rsplit("/", 1)[-1] for x in ids[i:i + 50])
            d = self._get("/works", filter=f"openalex_id:{chunk}", **{"per-page": 50},
                          select="id,doi,title,display_name,publication_year,cited_by_count,primary_location,best_oa_location,type")
            rows += [self._row(w) for w in d["results"]]
        return len(ids), rows


# ---------------------------------------------------------------- arXiv
def arxiv_search(q: str, max_results: int = TOP_N) -> tuple[int, list[dict]]:
    r = requests.get("https://export.arxiv.org/api/query",
                     params={"search_query": q, "max_results": max_results,
                             "sortBy": "relevance"},
                     headers={"User-Agent": UA}, timeout=60)
    if r.status_code != 200:
        raise RuntimeError(f"arxiv {r.status_code}")
    ns = {"a": "http://www.w3.org/2005/Atom", "os": "http://a9.com/-/spec/opensearch/1.1/"}
    root = ET.fromstring(r.text)
    total = int(root.findtext("os:totalResults", default="0", namespaces=ns))
    rows = []
    for e in root.findall("a:entry", ns):
        aid = e.findtext("a:id", default="", namespaces=ns)
        rows.append({"id": aid, "title": " ".join((e.findtext("a:title", default="", namespaces=ns)).split()),
                     "year": (e.findtext("a:published", default="", namespaces=ns) or "")[:4],
                     "oa_url": aid.replace("/abs/", "/pdf/")})
    return total, rows


def arxiv_query(phrase: str) -> str:
    # Quoted-phrase AND-of-terms over all fields; arXiv's `all:` matches title+abstract.
    terms = [t for t in phrase.split() if len(t) > 2]
    return " AND ".join(f"all:{t}" for t in terms)


# ---------------------------------------------------------------- Semantic Scholar
class S2:
    base = "https://api.semanticscholar.org/graph/v1"

    def __init__(self, key: str | None) -> None:
        self.h = {"User-Agent": UA}
        if key:
            self.h["x-api-key"] = key

    def _get(self, path: str, **params) -> dict:
        last = None
        for i in range(S2_RETRIES):
            r = requests.get(self.base + path, params=params, headers=self.h, timeout=60)
            if r.status_code == 200:
                return r.json()
            last = f"s2 {r.status_code}: {r.text[:120]}"
            if r.status_code in (429, 500, 502, 503, 504):
                time.sleep(S2_BACKOFF[min(i, len(S2_BACKOFF) - 1)])
                continue
            break
        raise RuntimeError(last or "s2 unknown")

    @staticmethod
    def _row(p: dict) -> dict:
        ext = p.get("externalIds") or {}
        return {"id": p.get("paperId"), "doi": ext.get("DOI"), "arxiv": ext.get("ArXiv"),
                "title": p.get("title"), "year": p.get("year"), "cited_by": p.get("citationCount"),
                "venue": p.get("venue"), "oa_url": (p.get("openAccessPdf") or {}).get("url")}

    FIELDS = "title,year,citationCount,externalIds,venue,openAccessPdf"

    def search(self, q: str) -> tuple[int, list[dict]]:
        d = self._get("/paper/search", query=q, limit=TOP_N, fields=self.FIELDS)
        return d.get("total", 0), [self._row(p) for p in d.get("data", [])]

    def paper(self, pid: str) -> dict:
        return self._get(f"/paper/{pid}", fields=self.FIELDS + ",referenceCount")

    def citations(self, pid: str) -> tuple[int, list[dict]]:
        d = self._get(f"/paper/{pid}/citations", limit=100, fields=self.FIELDS)
        rows = [self._row(x["citingPaper"]) for x in d.get("data", [])]
        return len(rows), rows

    def references(self, pid: str) -> tuple[int, list[dict]]:
        d = self._get(f"/paper/{pid}/references", limit=100, fields=self.FIELDS)
        rows = [self._row(x["citedPaper"]) for x in d.get("data", []) if x.get("citedPaper")]
        return len(rows), rows


# ---------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--families", nargs="*", default=None)
    ap.add_argument("--skip-s2", action="store_true")
    ap.add_argument("--oa-mode", choices=["title_abstract", "fulltext"], default="title_abstract")
    ap.add_argument("--skip-named", action="store_true")
    ap.add_argument("--skip-citations", action="store_true")
    ap.add_argument("--named-set", choices=sorted(NAMED_SETS), default="base",
                    help="which named-lookup list to resolve (default: the run-2 list)")
    ap.add_argument("--task", default="cc_tasks/2026-09-02_g1_eval_prior_art.md",
                    help="task reference written into the log header")
    a = ap.parse_args()

    oa_key = _env_key("OPENALEX_API_KEY")
    if not oa_key:
        print("FATAL: OPENALEX_API_KEY missing (env or ~/.wintermute/.env)", file=sys.stderr)
        return 2
    oa = OpenAlex(oa_key)
    s2 = S2(_env_key("SEMANTIC_SCHOLAR_API_KEY"))
    log = Log()

    fams = {k: v for k, v in FAMILIES.items() if not a.families or k in a.families}
    for fam, phrasings in fams.items():
        for q, aq in phrasings:
            try:
                n, rows = oa.search(q, mode=a.oa_mode)
                log.add(source=f"openalex:{a.oa_mode}", family=fam, query=q, hit_count=n, status="ok", top=rows)
            except Exception as e:  # recorded, not swallowed: the log line carries the error
                log.add(source=f"openalex:{a.oa_mode}", family=fam, query=q, hit_count=None, status=f"error: {e}", top=[])
            try:
                n, rows = arxiv_search(aq)
                log.add(source="arxiv", family=fam, query=aq, hit_count=n, status="ok", top=rows)
            except Exception as e:
                log.add(source="arxiv", family=fam, query=aq, hit_count=None, status=f"error: {e}", top=[])
            time.sleep(3.1)  # arXiv asks for >= 3 s between requests
            if not a.skip_s2:
                try:
                    n, rows = s2.search(q)
                    log.add(source="semantic_scholar", family=fam, query=q, hit_count=n, status="ok", top=rows)
                except Exception as e:
                    log.add(source="semantic_scholar", family=fam, query=q, hit_count=None, status=f"error: {e}", top=[])
                time.sleep(1.2)

    # ---- named-work resolution ---------------------------------------------------
    if not a.skip_named:
        for t in NAMED_SETS[a.named_set]:
            try:
                n, rows = oa.by_title(t)
                log.add(source="openalex:title", family="NAMED", query=t, hit_count=n, status="ok", top=rows)
            except Exception as e:
                log.add(source="openalex:title", family="NAMED", query=t, hit_count=None, status=f"error: {e}", top=[])

    # ---- citation walks ---------------------------------------------------------
    anchor_ids = {}
    for name, ident in ({} if a.skip_citations else ANCHORS).items():
        w = oa.by_doi(ident["doi"])
        if w is None and ident.get("arxiv"):
            n, rows = oa.search(ident["arxiv"])
            w = None
        if w:
            anchor_ids[name] = w["id"]
            n, rows = oa.cited_by(w["id"])
            log.add(source="openalex", family=f"CIT_forward_{name}", query=f"cites:{w['id']}",
                    hit_count=n, status="ok", top=rows, anchor_title=w.get("title"))
            if name == "vanderbles_2019":
                for q in ("large language model", "numeric uncertainty communication",
                          "official statistics"):
                    n, rows = oa.cited_by(w["id"], q)
                    log.add(source="openalex", family=f"CIT_forward_{name}", query=f"cites:{w['id']} search={q}",
                            hit_count=n, status="ok", top=rows)
            n, rows = oa.references(w)
            log.add(source="openalex", family=f"CIT_backward_{name}", query=f"referenced_works of {w['id']}",
                    hit_count=n, status="ok", top=rows)
        else:
            log.add(source="openalex", family=f"CIT_anchor_{name}", query=ident["doi"], hit_count=0,
                    status="anchor not in OpenAlex", top=[])
        if not a.skip_s2:
            pid = f"arXiv:{ident['arxiv']}" if ident.get("arxiv") else f"DOI:{ident['doi']}"
            try:
                p = s2.paper(pid)
                n, rows = s2.citations(pid)
                log.add(source="semantic_scholar", family=f"CIT_forward_{name}", query=f"citations of {pid}",
                        hit_count=p.get("citationCount"), status="ok", top=rows, anchor_title=p.get("title"))
                n, rows = s2.references(pid)
                log.add(source="semantic_scholar", family=f"CIT_backward_{name}", query=f"references of {pid}",
                        hit_count=p.get("referenceCount"), status="ok", top=rows)
            except Exception as e:
                log.add(source="semantic_scholar", family=f"CIT_{name}", query=pid, hit_count=None,
                        status=f"error: {e}", top=[])

    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"task": a.task, "generated_at_utc": _now(),
                               "families_run": sorted(fams), "named_set": a.named_set,
                               "families": FAMILIES, "anchors": ANCHORS, "entries": log.entries},
                              indent=1, ensure_ascii=False))
    ok = sum(1 for e in log.entries if e["status"] == "ok")
    print(f"queries logged: {len(log.entries)} ok: {ok} -> {out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
