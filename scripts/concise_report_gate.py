#!/usr/bin/env python3
"""The concise report's checks by code: claim markers, the digit check and the prose gate.
**Zero spend, no network.**

`cc_tasks/2026-10-07_concise_report_prose.md` decisions 3 to 5, implementing DN-013-R6. Every
measure here is computed by code from the text; a model only writes and judges. Thresholds come
from `reports/concise/report_config.yaml` `gate`, which copies the task's numbers.

* **Markers.** A sentence that states a fact ends with `[c:<claim id>]` (several ids are
  comma-separated, or several markers follow one another). `strip_markers` removes them for the
  built report; `marker_ids` reads them.
* **Digit check** (decision 4). Every digit string in a sentence must equal a value in the
  claims that sentence cites: a claim's `numbers` values and every digit string in its text,
  compared with thousands separators removed. A sentence with a digit and no marker fails.
* **Dashes.** No U+2014 anywhere; no U+2013 except between two digits, a range.
* **Banned words.** The operator's list, read through `scripts/dcat_faq_lint.banned_rules`, so
  this gate and the briefs' lint answer to one file.
* **The pattern DN-013-R6 names** ("statement, short clarification"): for adjacent sentences,
  flag the pair when the second has at most 8 words, the first is at least twice as long, and
  the second has no finite verb or opens with a qualifier. More than two flagged pairs fails the
  section. Words are spaCy tokens that are not punctuation or space. A finite verb is a VERB or
  AUX token whose morphology says `VerbForm=Fin`, or whose Penn tag is VBD, VBP, VBZ or MD
  (spaCy `en_core_web_sm` 3.8; the tagger is named in `prose_gate.json`).
* **Reported, not gated.** Sentence-length standard deviation (population) and finite verbs per
  sentence (the clause proxy), per section; adjacent-sentence content-lemma overlap, as the mean
  Jaccard of the two sentences' content-lemma sets and the share of adjacent pairs sharing any,
  after Coh-Metrix's adjacent content-word overlap (Graesser, McNamara, Louwerse and Cai, 2004);
  the connective rate, as connectives per sentence and the share of sentences holding one, after
  TAACO (Crossley, Kyle and McNamara, 2016), with the list named in the config.
* **Repetition** (warnings). Every content 3-gram (three consecutive content lemmas within a
  sentence) that occurs twice or more in the report, and every content lemma used more than five
  times in one section.
"""
from __future__ import annotations

import re
import statistics
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO / "scripts"))

import dcat_faq_lint  # noqa: E402

TAGGER = "spaCy en_core_web_sm"
MARK_RE = re.compile(r"\s*\[c:\s*([A-Za-z]+-\d+(?:\s*,\s*[A-Za-z]+-\d+)*)\s*\]")
DIGIT_RE = re.compile(r"\d[\d,]*(?:\.\d+)?")
FINITE_TAGS = {"VBD", "VBP", "VBZ", "MD"}

_NLP = None


def nlp():
    global _NLP
    if _NLP is None:
        import spacy
        _NLP = spacy.load("en_core_web_sm")
    return _NLP


def tagger_name() -> str:
    import spacy
    return f"{TAGGER} {nlp().meta.get('version')} (spaCy {spacy.__version__})"


# ------------------------------------------------------------------------------ markers

def marker_ids(sentence: str) -> list:
    out = []
    for m in MARK_RE.finditer(sentence):
        out += [x.strip().upper() for x in m.group(1).split(",")]
    return list(dict.fromkeys(out))


def strip_markers(text: str) -> str:
    return MARK_RE.sub("", text).strip()


# ------------------------------------------------------------------------------ digits

def norm_number(s: str) -> str:
    s = s.replace(",", "").rstrip(".")
    return s


def digit_strings(text: str) -> list:
    return [norm_number(m.group(0)) for m in DIGIT_RE.finditer(text)]


def claim_values(claim: dict) -> set:
    vals = {norm_number(str(n["value"])) for n in claim.get("numbers") or []}
    return vals | set(digit_strings(claim["text"]))


def digit_check(sentence: str, claims: dict) -> dict:
    """{"ok", "digits", "missing", "ids"}: every digit string in the sentence (markers stripped)
    is a value of a claim it cites. `claims`: id -> claim."""
    ids = marker_ids(sentence)
    digits = digit_strings(strip_markers(sentence))
    allowed = set()
    unknown = [i for i in ids if i not in claims]
    for i in ids:
        if i in claims:
            allowed |= claim_values(claims[i])
    missing = [d for d in digits if d not in allowed]
    return {"ok": not missing and not unknown, "digits": digits, "missing": missing,
            "unknown_ids": unknown, "ids": ids}


# ------------------------------------------------------------------------------ dashes, words

def dash_findings(text: str) -> list:
    out = [{"rule": "em_dash", "at": m.start()} for m in re.finditer("\u2014", text)]
    for m in re.finditer("\u2013", text):
        before, after = text[m.start() - 1: m.start()], text[m.end(): m.end() + 1]
        if not (before.isdigit() and after.isdigit()):
            out.append({"rule": "en_dash_as_dash", "at": m.start()})
    return out


def banned_findings(text: str, path: Path | None = None) -> list:
    out = []
    for rule, pat, _ in dcat_faq_lint.banned_rules(path):
        for m in pat.finditer(text):
            out.append({"rule": rule, "match": m.group(0)})
    return out


# ------------------------------------------------------------------------------ spaCy measures

def analyse(sentence: str) -> dict:
    doc = nlp()(strip_markers(sentence))
    words = [t for t in doc if not t.is_punct and not t.is_space]
    finite = [t.text for t in doc if t.pos_ in ("VERB", "AUX")
              and ("Fin" in t.morph.get("VerbForm") or t.tag_ in FINITE_TAGS)]
    return {"words": len(words), "finite_verbs": finite, "doc": doc}


def content_lemmas(doc, content_pos) -> list:
    return [t.lemma_.lower() for t in doc if t.pos_ in content_pos and t.is_alpha and not t.is_stop]


def opens_with_qualifier(sentence: str, openers) -> str | None:
    s = strip_markers(sentence).lstrip("\"'([*_ ")
    for q in sorted(openers, key=len, reverse=True):
        if re.match(rf"{re.escape(q)}\b", s):
            return q
    return None


def flagged_pairs(sentences: list, pair_cfg: dict, analysed: list | None = None) -> list:
    an = analysed or [analyse(s) for s in sentences]
    out = []
    for i in range(1, len(sentences)):
        a, b = an[i - 1], an[i]
        if b["words"] > pair_cfg["max_short_words"] or a["words"] < pair_cfg["long_to_short_ratio"] * b["words"]:
            continue
        q = opens_with_qualifier(sentences[i], pair_cfg["qualifier_openers"])
        if not b["finite_verbs"] or q:
            out.append({"first": strip_markers(sentences[i - 1]), "second": strip_markers(sentences[i]),
                        "first_words": a["words"], "second_words": b["words"],
                        "why": f"opens with qualifier {q!r}" if q else "no finite verb"})
    return out


def connective_hits(sentence: str, conn_cfg: dict) -> list:
    s = strip_markers(sentence).lower()
    hits = []
    for cat, items in conn_cfg.items():
        if cat == "list_name":
            continue
        for c in items:
            if re.search(rf"(?<![\w-]){re.escape(c.lower())}(?![\w-])", s):
                hits.append(c)
    return hits


def section_measures(sentences: list, gate_cfg: dict) -> dict:
    an = [analyse(s) for s in sentences]
    pairs = flagged_pairs(sentences, gate_cfg["pair"], an)
    lengths = [a["words"] for a in an]
    cpos = set(gate_cfg["content_pos"])
    lem = [content_lemmas(a["doc"], cpos) for a in an]
    jac, any_overlap = [], 0
    for i in range(1, len(lem)):
        A, B = set(lem[i - 1]), set(lem[i])
        u = A | B
        jac.append(len(A & B) / len(u) if u else 0.0)
        any_overlap += bool(A & B)
    conns = [connective_hits(s, gate_cfg["connectives"]) for s in sentences]
    counts = Counter(x for l in lem for x in l)
    over = {k: v for k, v in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
            if v > gate_cfg["repetition"]["max_lemma_per_section"]}
    n = len(sentences)
    return {
        "sentences": n,
        "flagged_pairs": pairs,
        "flagged_pair_count": len(pairs),
        "pass": len(pairs) <= gate_cfg["pair"]["max_flagged_pairs_per_section"],
        "sentence_length_sd": round(statistics.pstdev(lengths), 2) if n else 0.0,
        "sentence_length_mean": round(statistics.mean(lengths), 2) if n else 0.0,
        "finite_verbs_per_sentence": round(sum(len(a["finite_verbs"]) for a in an) / n, 2) if n else 0.0,
        "adjacent_content_overlap_mean_jaccard": round(statistics.mean(jac), 3) if jac else 0.0,
        "adjacent_pairs_sharing_a_content_lemma": round(any_overlap / len(jac), 3) if jac else 0.0,
        "connectives_per_sentence": round(sum(len(c) for c in conns) / n, 2) if n else 0.0,
        "sentences_with_a_connective": round(sum(1 for c in conns if c) / n, 3) if n else 0.0,
        "lemmas_over_limit": over,
        "_lemmas": lem,
    }


def repeated_ngrams(section_lemmas: dict, min_count: int) -> dict:
    """section_lemmas: section id -> list of per-sentence content-lemma lists. Returns
    '<a b c>' -> {"count", "sections"} for every content 3-gram at or above min_count."""
    c, where = Counter(), {}
    for sid, sents in section_lemmas.items():
        for lem in sents:
            for i in range(len(lem) - 2):
                g = " ".join(lem[i:i + 3])
                c[g] += 1
                where.setdefault(g, set()).add(sid)
    return {g: {"count": n, "sections": sorted(where[g])} for g, n in sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))
            if n >= min_count}


def gate_report(sections: dict, gate_cfg: dict) -> dict:
    """sections: id -> list of sentences (markers in place). The prose gate over the report."""
    out, lems = {}, {}
    for sid, sents in sections.items():
        m = section_measures(sents, gate_cfg)
        lems[sid] = m.pop("_lemmas")
        text = " ".join(strip_markers(s) for s in sents)
        m["dashes"] = dash_findings(text)
        m["banned"] = banned_findings(text)
        m["pass"] = m["pass"] and not m["dashes"] and not m["banned"]
        out[sid] = m
    return {"tagger": tagger_name(), "sections": out,
            "repeated_3grams": repeated_ngrams(lems, gate_cfg["repetition"]["min_ngram_count"])}
