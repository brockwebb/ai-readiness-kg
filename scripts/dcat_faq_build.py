#!/usr/bin/env python3
"""Build the DCAT-US 3.0 FAQ and its evidence attachment from the checked answers. **Zero spend,
no network.**

`cc_tasks/2026-10-05_DCAT-003_dcat_us_3_faq_for_omb_meeting.md` step 4. Reads
`reports/dcat_us_3_faq/answers.json` (written by `scripts/dcat_faq_run.py`), the evidence files
and the element table, and writes, all under `reports/dcat_us_3_faq/`:

* `FAQ.md` / `FAQ.pdf`: each question, the kept sentences of its answer, what the sources do not
  state, and the sources as short citations (title, issuer, date, section, URL);
* `ATTACHMENT_evidence.md` / `ATTACHMENT_evidence.pdf`: per question, every passage a kept
  sentence cites, verbatim, with its location; and the element table for questions 4 and 6.

Nothing in either file is typed by hand: every sentence is one the check kept, every quote is a
passage from an evidence file, every table cell is read from a schema text. The PDFs are
converted by pandoc with the typst engine, the toolchain `scripts/build_report_pdf.py` already
pins. The files are written for a reader: no passage ids, record names or process words appear
in the prose; locations in the attachment use the source's own identifiers.

DCAT-003 ADDENDUM 01 (`cc_tasks/2026-10-05_DCAT-003_ADDENDUM_01_faq_shippability.md`) adds,
all by code:

* question 14 as a gap table and a list of documents not used (steps 1);
* "Not found in the sources:" with bare clauses (step 2);
* no em dash: titles in the issuer's punctuation, a dash in quoted source text shown as a
  spaced hyphen, and the one configured substitution in a kept sentence (step 3);
* version notes and the table's 5 October 2026 column (step 4): a sentence that states a
  requirement level without naming a version gets each named element's level in every
  version of the Dataset page; a sentence quoting a version that has since been superseded
  says whether the page as served on 5 October 2026 still carries the quoted text, by word
  5-gram coverage (measured on the shipped passages: 0.82 to 1.0 where the text survives and
  differs only in markup, 0.0 and 0.06 where it is gone; `PRESENT_AT`/`ABSENT_AT` sit in the gap);
* the framework indicator cited as the presenter's own unpublished draft, and the sentence cut
  if its quoted text is not the record's current text (step 6);
* the lint (`scripts/dcat_faq_lint.py`, step 7), run on both files before either is written.

What the code added is listed in `build_report.json`.

    /opt/anaconda3/bin/python3 scripts/dcat_faq_build.py [--no-pdf]
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import dcat_faq_evidence as EV  # noqa: E402
import dcat_faq_lint as LINT  # noqa: E402

OUT = EV.OUT
ANSWERS = OUT / "answers.json"
FAQ_MD, FAQ_PDF = OUT / "FAQ.md", OUT / "FAQ.pdf"
ATT_MD, ATT_PDF = OUT / "ATTACHMENT_evidence.md", OUT / "ATTACHMENT_evidence.pdf"
BUILD_REPORT = OUT / "build_report.json"
PREPARED = "5 October 2026"
LIVE_DATE = "5 October 2026"
#: Word 5-gram coverage of a quoted passage by the page as served on 2026-10-05 (module docstring).
PRESENT_AT, ABSENT_AT = 0.75, 0.25
EM_DASH = "\u2014"
TIER_RE = re.compile(r"\b(Mandatory|Recommended|Optional)\b")
_MONTHS = "January|February|March|April|May|June|July|August|September|October|November|December"
#: A sentence names the version of a published page it reads when it carries a dated reference
#: (a day and month, a month and year) or points back to the capture its previous sentence
#: names. Naming the draft (there is one working draft, the 2025 Candidate Recommendation)
#: dates a tier only when the sentence names no element a published page lists: "the published
#: Dataset pages list ..., all Optional" names the draft and still dates nothing it says of them.
DATE_RE = re.compile(rf"\b\d{{1,2}} (?:{_MONTHS}) \d{{4}}\b|\b(?:{_MONTHS}) \d{{4}}\b|\bsame capture\b")
DRAFT_RE = re.compile(r"\bworking draft\b|\bCandidate Recommendation\b")
VERSION_RE = re.compile(f"{DATE_RE.pattern}|{DRAFT_RE.pattern}")
BARE_RE = re.compile(r"^The sources do not (?:state|show|say|indicate|give|name|identify)\s+")
#: Everything the build added or removed by code, for the delivery report.
REPORT: dict = {"version_notes": [], "dash_substitutions": [], "indicator_checks": [], "cut_by_build": []}
NONE_KEPT = ("The documents collected for this briefing do not support an answer to this question "
             "that could be confirmed against their text.")

#: Plain names for the kinds of passage, so the attachment says what a passage is without
#: process vocabulary.
KIND_LABEL = {"passage": "passage", "document text": "text", "document text (table row)": "table row",
              "element table row": "table row", "catalog record (not admitted)": "catalog record",
              "indicator": "indicator text", "unanswered part of an earlier question": "earlier answer"}

#: The draft column's provenance: B3.3 slide 5 names the draft at doi-do.github.io/dcat-us as the
#: project's Task 1 deliverable. Shown under the table with that quotation.
DRAFT_SOURCE_QUOTE = ("Task 1, DCAT-US 3.0 Schema Update • Draft specification for review: "
                      "https://doi-do.github.io/dcat-us")


def kind_label(kind: str) -> str:
    if kind in KIND_LABEL:
        return KIND_LABEL[kind]
    if kind.endswith("(as extracted)"):
        return "requirement sentence"
    return "quoted sentence"


def anchor_links_as_text(text: str) -> str:
    """A link to an anchor in the same web page (`[Class X #](#x)`) is shown as its link text,
    without the page's "#" permalink marker: it points nowhere outside the page it came from,
    and the PDF engine refuses an anchor the document does not have."""
    text = re.sub(r"\[([^\]]*)\]\(#[^)]*\)", r"\1", text or "")
    return re.sub(r"\s+\\?#(?=[\s|.,;:)]|$)", "", text)


def _clean(part: str) -> str:
    """Drop markdown emphasis a heading carried (`*x*`, `_x_`, backticks) and trailing
    punctuation; underscores inside words and URLs (an archive's `id_`) are kept."""
    part = re.sub(r"[*`]", "", anchor_links_as_text(str(part or "")))
    part = re.sub(r"(?<![\w/])_([^_]+)_(?![\w/])", r"\1", part).strip()
    return part.rstrip(".?!:;, ")


def bare(text: str) -> str:
    """A "not found" item without its repeated lead-in, under the header "Not found in the
    sources:" (ADDENDUM 01 step 2). An item with another opening is printed as written."""
    m = BARE_RE.match(text)
    if not m:
        return text
    rest = text[m.end():]
    return rest[:1].upper() + rest[1:]


def quote_text(text: str) -> str:
    """Quoted source text as printed: links to the same page as their text, and a dash
    (U+2014) as a spaced hyphen, the operator's rule (ADDENDUM 01 step 3). Said in the
    attachment's preface."""
    text = re.sub(r"\s*\u2014\s*", " - ", anchor_links_as_text(text))
    # A run of hyphens in quoted page text is a markdown table rule from the page's conversion
    # ("Date | Change ---|--- May 2026"), not the source's words; typst prints "---" as an em
    # dash, so it is shown as one hyphen.
    return re.sub(r"-{2,}", "-", text)


def shown(text: str, qid: int, cfg: dict) -> str:
    """A kept sentence as printed. Verbatim, except the one configured question whose paired
    dashes become commas (`dash_substitution`), a change of punctuation and of no claim."""
    ds = cfg.get("dash_substitution") or {}
    if qid == ds.get("question") and text.count(EM_DASH) == 2:
        out = re.sub(r"\s*\u2014\s*", ds["pair"], text)
        rec = {"question": qid, "from": text, "to": out}
        if rec not in REPORT["dash_substitutions"]:
            REPORT["dash_substitutions"].append(rec)
        return out
    return text


def _words(text: str) -> list:
    text = re.sub(r"\]\([^)]*\)", "]", text or "")
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).split()


def _grams(words: list, n: int = 5) -> set:
    return {tuple(words[i:i + n]) for i in range(len(words) - n + 1)}


_PAGE_GRAMS: dict = {}


def coverage(passage: str, doc: str) -> float:
    if doc not in _PAGE_GRAMS:
        _PAGE_GRAMS[doc] = _grams(_words((EV.REPO / "state" / "substrate_md" / f"{doc}.md")
                                         .read_text(encoding="utf-8")))
    g = _grams(_words(passage))
    return len(g & _PAGE_GRAMS[doc]) / len(g) if g else 1.0


def _join(names: list) -> str:
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]


def cited_elements(items: list) -> set:
    """Element names a cited passage names as elements: a table row's element, a "Dataset >
    key" heading, a backticked term, or a link's text."""
    out = set()
    for it in items:
        if (it.get("locator") or {}).get("element"):
            out.add(it["locator"]["element"])
        blob = f"{it.get('section') or ''} {it['text']}"
        out |= set(re.findall(r"Dataset (?:>|&gt;) (\w+)", blob))
        out |= set(re.findall(r"`(\w+)`", blob))
        out |= set(re.findall(r"\[(\w+)\]\(", blob))
    return out


def version_note(text: str, items: list, cfg: dict, rows: list, where: str) -> str:
    """The parenthetical the build adds after a kept sentence (module docstring), or ""."""
    parts = []
    by_el = {r["element"]: r for r in rows}
    named = []
    if TIER_RE.search(text) and not DATE_RE.search(text):
        named = [e for e in by_el if re.search(rf"(?<![\w-]){re.escape(e)}(?![\w-])", text)
                 and e in cited_elements(items)
                 and any(by_el[e][k] for k in ("level_2026_08_21", "level_2026_09_15", "level_2026_10_05"))]
        if not named and not DRAFT_RE.search(text):
            raise SystemExit(f"FATAL: {where} states a requirement level, names no version, and "
                             f"names no element the table can date: {text!r}")
    if named:
        groups: dict = {}
        for e in named:
            r = by_el[e]
            groups.setdefault((r["level_2026_08_21"], r["level_2026_09_15"], r["level_2026_10_05"]), []).append(e)
        for (a, b, c), els in groups.items():
            a, b, c = (x or "not listed" for x in (a, b, c))
            head = f"level by version, {_join(els)}: "
            if a == b == c:
                parts.append(f"{head}{a} on the Dataset page captured 21 August and 15 September "
                             f"2026 and as served {LIVE_DATE}")
            elif b == c:
                parts.append(f"{head}{a} on the Dataset page captured 21 August 2026, {b} on the "
                             f"15 September 2026 capture and as served {LIVE_DATE}")
            else:
                parts.append(f"{head}{a} on the Dataset page captured 21 August 2026, {b} on the "
                             f"15 September 2026 capture, {c} as served {LIVE_DATE}")
    sup = cfg.get("superseded_by") or {}
    checked = [(it, sup[it["doc_id"]]) for it in items
               if it["doc_id"] in sup and it["kind"] != "element table row"]
    if checked:
        covs = [(it, s, round(coverage(it["text"], s["by"]), 3)) for it, s in checked]
        gone = [(it, s) for it, s, c in covs if c <= ABSENT_AT]
        part_ = [(it, s) for it, s, c in covs if ABSENT_AT < c < PRESENT_AT]
        if gone:
            parts.append(f"quoted from {_join(sorted({s['label'] for _, s in gone}))}; the page as "
                         f"served {LIVE_DATE} does not contain this text")
        elif part_:
            parts.append(f"quoted from {_join(sorted({s['label'] for _, s in part_}))}; the page as "
                         f"served {LIVE_DATE} carries this text only in part")
        else:
            parts.append(f"the same text is on the page as served {LIVE_DATE}")
        REPORT["version_notes"].append({"where": where, "coverage": [
            {"passage": it["id"], "doc_id": it["doc_id"], "on": s["by"], "coverage": c} for it, s, c in covs]})
    if not parts:
        return ""
    note = "; ".join(parts)
    REPORT["version_notes"].append({"where": where, "note": note})
    return f" ({note[:1].upper()}{note[1:]}.)"


def indicator_current(it: dict) -> bool:
    """The quoted indicator text is the framework record's current text for that node (ADDENDUM
    01 step 6: if it cannot be quoted from the record, the sentence is cut)."""
    rec = json.loads(EV.FRAMEWORK.read_text(encoding="utf-8"))
    node = next((n for n in rec["nodes"] if n["id"] == it["locator"]["record_node"]), None)
    cur = ((node or {}).get("properties") or {}).get("indicator") or ""
    ok = bool(cur) and (cur == it["text"] or (it.get("cut") and cur.startswith(it["text"])))
    rec_ = {"node": it["locator"]["record_node"], "matches_record": ok}
    if rec_ not in REPORT["indicator_checks"]:
        REPORT["indicator_checks"].append(rec_)
    return ok


def citation(meta: dict, sections: list) -> str:
    """Title. Issuer. Date. Section(s). <URL>, with no doubled punctuation."""
    parts = [_clean(meta.get("title")), _clean(meta.get("issuer")), _clean(meta.get("date"))]
    secs = [_clean(x) for x in sections if _clean(x)]
    if secs:
        parts.append(("Sections: " if len(secs) > 1 else "") + "; ".join(secs))
    head = ". ".join(p for p in parts if p) + "."
    if meta.get("url"):
        head += f" <{meta['url']}>"
    return head


def all_documents() -> dict:
    """Every document any evidence file names, so a merged citation can read both graphs'
    metadata whichever one a question happened to use."""
    out = {}
    for p in sorted(EV.EVIDENCE_DIR.glob("Q*.json")):
        out.update(json.loads(p.read_text(encoding="utf-8")).get("documents") or {})
    return out


def canonical(it: dict, docs: dict, cfg: dict) -> tuple:
    """(citation key, metadata) for an evidence item. A document held in both graphs is one key
    (`same_document` in the config); a computed table row cites the table and its four sources;
    a catalog record, an indicator and an earlier answer cite themselves."""
    d = it["doc_id"]
    if it["kind"] == "element table row":
        reads = "; ".join(f"{_clean(docs[x]['title'])}, {_clean(docs[x]['date'])} <{docs[x]['url']}>"
                          for x in (EV.FINAL, EV.EARLIER, EV.DRAFT, EV.V11) if x in docs)
        return "table", {"title": "Requirement level of each Dataset element in four versions of the "
                                  "schema, read from each version's text (table in the attachment). "
                                  f"Read from: {reads}", "issuer": "", "date": "", "url": ""}
    if it["kind"] == "catalog record (not admitted)":
        return f"catalog:{d}", {"title": catalog_plain(it["text"]), "issuer": "", "date": "", "url": ""}
    if it["kind"] == "indicator":
        # ADDENDUM 01 step 6: the presenter's own draft, unpublished, said in plain words.
        return "framework", {"title": "The presenter's own draft AI-readiness framework for federal "
                                      "statistical publishers (unpublished; the indicator's text is "
                                      "quoted in the attachment)", "issuer": "", "date": "", "url": ""}
    if it["kind"] == "unanswered part of an earlier question":
        return f"answer:{d}", {"title": f"Answer to {d}, above", "issuer": "", "date": "", "url": ""}
    for pair in cfg.get("same_document") or []:
        if d in (pair["fss"], pair["airkg"]):
            f, a = docs.get(pair["fss"]) or {}, docs.get(pair["airkg"]) or {}
            meta = {**a, **{k: v for k, v in f.items() if v}}
            meta["url"] = (a if pair["url_from"] == "airkg" else f).get("url") or meta.get("url")
            meta.update({k: pair[k] for k in ("title", "date") if pair.get(k)})
            return f"pair:{pair['fss']}", meta
    return f"doc:{d}", docs.get(d) or {"title": d}


def catalog_plain(text: str) -> str:
    """A catalog record's title and its stated reason, without the record's status code."""
    title, _, rest = text.partition(". ")
    rest = re.sub(r"NOT ADMITTED \([^)]*\)\.?\s*", "", rest).strip()
    return f"{title}. {rest}" if rest else title


def location(it: dict) -> str:
    loc = it.get("locator") or {}
    if "segment" in loc:
        s = f"passage {loc['segment'].split('#s')[-1]} (identifier {loc['segment']})"
    elif "file" in loc and "line" in loc:
        s = f"line {loc['line']} of the page text" + (f", under “{_clean(it['section'])}”" if it.get("section") else "")
    elif "node" in loc:
        s = (f"{_clean(it['section'])}, " if it.get("section") else "") + f"identifier {loc['node']}"
    elif "element" in loc:
        s = "lines " + ", ".join(f"{v} ({EV_NAMES.get(k, k)})" for k, v in loc["lines"].items())
    elif "catalog_entry" in loc:
        s = f"catalog record {loc['catalog_entry']}"
    elif "record_node" in loc:
        s = f"framework record {loc['record_node']}"
    elif "question" in loc:
        s = f"question {loc['question']}"
    else:
        s = json.dumps(loc)
    return s


EV_NAMES = {EV.FINAL: "Dataset page, 2026-09-15", EV.EARLIER: "Dataset page, 2026-08-21",
            EV.DRAFT: "working draft", EV.V11: "v1.1 schema"}


def doc_meta_for(ev: dict, it: dict, cfg: dict | None = None) -> dict:
    """A passage's document as the attachment names it: the same title the FAQ's citation uses
    (a `same_document` pair's title, in the issuer's punctuation), else the graph's."""
    m = ev["documents"].get(it["doc_id"])
    if m and cfg is not None and it["kind"] not in ("element table row", "indicator"):
        key, meta = canonical(it, {**DOCS, **ev["documents"]}, cfg)
        if key.startswith("pair:"):
            return {**m, "title": meta.get("title") or m.get("title")}
    if m:
        return m
    if it.get("kind") == "catalog record (not admitted)":
        return {"title": it["text"].split(". ")[0], "issuer": "", "date": "", "url": ""}
    if it.get("kind") == "element table row":
        return {"title": "Requirement levels compared across DCAT-US versions (table in the attachment)",
                "issuer": "", "date": "", "url": ""}
    if it.get("kind") == "indicator":
        return {"title": "The presenter's own draft AI-readiness framework (unpublished)", "issuer": "",
                "date": "", "url": ""}
    return {"title": it["doc_id"], "issuer": "", "date": "", "url": ""}


def load(qid: int) -> dict:
    return json.loads((EV.EVIDENCE_DIR / f"Q{qid}.json").read_text(encoding="utf-8"))


def live_summary(rows: list) -> str:
    """One computed sentence on what the Dataset page says now, against the 15 September 2026
    capture (ADDENDUM 01 step 4: "the operator may be asked 'what is it now'")."""
    diff = [r for r in rows if r["level_2026_09_15"] != r["level_2026_10_05"]]
    if not diff:
        return (f"The DCAT-US 3.0 Dataset page as served on {LIVE_DATE} gives every element the same "
                f"requirement level as the 15 September 2026 capture (table in the attachment).")
    return (f"The DCAT-US 3.0 Dataset page as served on {LIVE_DATE} differs from the 15 September 2026 "
            f"capture for " + _join([f"{r['element']} ({r['level_2026_09_15'] or 'not listed'} then, "
                                     f"{r['level_2026_10_05'] or 'not listed'} now)" for r in diff])
            + " (table in the attachment).")


def kept_rows(q: dict, ev: dict, cfg: dict) -> list:
    """(sentence as printed, its items) for each kept sentence the build prints. A sentence
    whose framework indicator is not the record's current text is cut here (step 6)."""
    by_id = {it["id"]: it for it in ev["items"]}
    out = []
    for s in q["kept"]:
        items = [by_id[e] for e in s["evidence"]]
        if any(it["kind"] == "indicator" and not indicator_current(it) for it in items):
            REPORT["cut_by_build"].append({"question": q["question_id"], "text": s["text"],
                                           "reason": "indicator text is not the record's current text"})
            continue
        out.append((s, shown(s["text"], q["question_id"], cfg), items))
    return out


def build_faq(answers: dict, cfg: dict, rows: list) -> str:
    rerun = sorted((cfg.get("rerun") or {}).get("questions") or [])
    out = ["# DCAT-US 3.0: questions and answers", "",
           f"Prepared {PREPARED} for a briefing to the Office of Management and Budget.", "",
           "How these answers were made. Each answer was drafted by one AI model reading only the "
           "passages quoted in the attachment, and each sentence was then checked against the "
           "passages it cites by a different AI model. A sentence the check could not confirm "
           "was removed, not reworded."
           + (f" For questions {_join([str(x) for x in rerun])}, the check also asked whether each "
              f"sentence answers the question, and a sentence that does not was removed too."
              if rerun else "")
           + " The attachment quotes every passage the answers rely on.", "",
           "\u201cNot found in the sources\u201d lists what the documents collected for this briefing "
           "do not say. Each item was checked against the passages gathered for its question and "
           "against a second search of the same documents using the item's own words. An item "
           "means the search did not find it; it does not mean that no document anywhere says it.", "",
           "Requirement levels name the version of the page they were read from. "
           + live_summary(rows) + " Text in parentheses after an answer sentence was added by code, "
           "not by a model: it gives each named element's level in every version of the Dataset "
           "page, or says whether a passage quoted from an earlier capture is still on the page as "
           f"served on {LIVE_DATE}.", ""]
    for q in answers["questions"]:
        qid = q["question_id"]
        ev = load(qid)
        out += [f"## {qid}. {q['question']}", ""]
        if q.get("built_by_code"):
            out += gaps_section(answers, cfg)
            continue
        refs, metas, secs = {}, {}, {}
        sentences = []
        for s, text, items in kept_rows(q, ev, cfg):
            marks = []
            for it in items:
                key, meta = canonical(it, DOCS, cfg)
                if key not in refs:
                    refs[key], metas[key], secs[key] = len(refs) + 1, meta, []
                sec = it.get("section") or ""
                if it["kind"] == "indicator":
                    sec = sec[:1].upper() + sec[1:]
                if sec and sec not in secs[key] and it["kind"] not in ("element table row",):
                    secs[key].append(sec)
                marks.append(refs[key])
            marks = sorted(set(marks))
            note = version_note(text, items, cfg, rows, f"Q{qid}: {s['text'][:60]}")
            sentences.append(text.rstrip() + " " + "".join(f"[{m}]" for m in marks) + note)
        out += [" ".join(sentences) if sentences else NONE_KEPT, ""]
        if q["not_known_kept"]:
            out += ["Not found in the sources:", ""]
            out += [f"- {bare(n['text'])}" for n in q["not_known_kept"]]
            out.append("")
        if refs:
            out += ["Sources:", ""]
            for key, n in refs.items():
                out.append(f"{n}. {citation(metas[key], secs[key])}")
            out.append("")
    return "\n".join(out).rstrip() + "\n"


GAPS_QUESTION = 14
DOCS: dict = {}


def _matches(spec: list, qid: int, text: str) -> bool:
    return qid == spec[0] and bare(text).lower().startswith(spec[1].lower())


def _plain_date(d: str | None) -> str:
    m = re.fullmatch(r"(\d{4})-(\d{2})(?:-(\d{2}))?", d or "")
    if not m:
        return d or ""
    month = _MONTHS.split("|")[int(m.group(2)) - 1]
    return f"{int(m.group(3))} {month} {m.group(1)}" if m.group(3) else f"{month} {m.group(1)}"


def catalog_records() -> dict:
    items = json.loads(EV.CATALOG_JSON.read_text(encoding="utf-8"))["items"]
    out = {}
    for it in items:
        if not it.get("record"):
            raise SystemExit(f"FATAL: {EV.CATALOG_JSON.name} has no record fields for {it['doc_id']}; "
                             f"re-run scripts/dcat_faq_evidence.py")
        out[it["doc_id"]] = it["record"]
    return out


def gap_rows(answers: dict, cfg: dict, records: dict) -> list:
    """Question 14's table (ADDENDUM 01 step 1, Part A): one row per distinct gap. Every item is
    a kept "not found" item of questions 1 to 13; `gap_groups` merges items that are one gap;
    `gap_documents` names the document that would answer one. A config entry that matches no
    item, or more than one, stops the build: the config is stale."""
    items = [(q["question_id"], n["text"]) for q in answers["questions"]
             if q["question_id"] != GAPS_QUESTION for n in q["not_known_kept"]]

    def find(spec):
        hits = [x for x in items if _matches(spec, *x)]
        if len(hits) != 1:
            raise SystemExit(f"FATAL: gap config {spec} matches {len(hits)} kept items; it must match one")
        return hits[0]

    group_of = {}
    for g in cfg.get("gap_groups") or []:
        members = [find(spec) for spec in g]
        for m in members:
            group_of[m] = members
    doc_of = {}
    for d in cfg.get("gap_documents") or []:
        rec = records[d["catalog_entry"]]
        short = rec["title"].rsplit(": ", 1)[-1]
        label = f"{short} ({rec['issuer']}, {_plain_date(rec['date'])}; not published, see below)"
        for spec in d["items"]:
            doc_of[find(spec)] = label
    rows, seen = [], set()
    for it in items:
        if it in seen:
            continue
        members = group_of.get(it, [it])
        seen |= set(members)
        docs = sorted({doc_of[m] for m in members if m in doc_of})
        rows.append({"gap": bare(members[0][1]), "questions": sorted({m[0] for m in members}),
                     "document": "; ".join(docs) if docs else "None known"})
    return rows


def gaps_section(answers: dict, cfg: dict) -> list:
    records = catalog_records()
    out = ["Each row is one gap left in the answers above, with the questions it affects and the "
           "document that would answer it, where one is known.", "",
           "| Gap | Questions | Document that would answer it |", "|---|---|---|"]
    for r in gap_rows(answers, cfg, records):
        out.append("| " + " | ".join(c.replace("|", "/") for c in
                                     (r["gap"], ", ".join(map(str, r["questions"])), r["document"])) + " |")
    out += ["", "Documents known to exist and not used:", ""]
    for cid, why in (cfg.get("documents_not_used") or {}).items():
        rec = records.get(cid)
        if rec is None:
            raise SystemExit(f"FATAL: documents_not_used names {cid!r}, which has no catalog record")
        out.append(f"- *{rec['title']}*. {rec['issuer']}, {_plain_date(rec['date'])}. {why}")
    out.append("")
    return out


def table_md(rows: list) -> list:
    head = ["| Element | DCAT-US v1.1: required? | 3.0 Dataset page, as served 5 Oct 2026 | "
            "3.0 Dataset page, 15 Sep 2026 | 3.0 Dataset page, 21 Aug 2026 | "
            "FAIRness Project draft (captured 4 May 2025) |",
            "|---|---|---|---|---|---|"]
    body = []
    for r in rows:
        cells = [f"`{r['element']}`", r["v11_required"] or "not listed",
                 r["level_2026_10_05"] or "not listed",
                 r["level_2026_09_15"] or "not listed", r["level_2026_08_21"] or "not listed",
                 r["draft_level"] or "not listed"]
        body.append("| " + " | ".join(c.replace("|", "/") for c in cells) + " |")
    return head + body


def build_attachment(answers: dict, cfg: dict, rows: list) -> str:
    out = ["# Attachment: the passages behind each answer", "",
           f"Prepared {PREPARED}. For each question, every passage an answer sentence cites, "
           "quoted as it appears in the source, with where to find it. Documents captured from "
           "the web are quoted as captured on the date shown; the DCAT-US 3.0 pages have been "
           f"revised since some captures, and the Dataset page and Overview as served on {LIVE_DATE} "
           "are held as well. In quoted web text, a link to another part of the same page is shown "
           "as its link text, and a long dash is shown as a spaced hyphen. The site's glossary is "
           "loaded separately from each page, so a glossary passage quoted from an earlier capture "
           "is not part of the page as served.", ""]
    for q in answers["questions"]:
        qid = q["question_id"]
        ev = load(qid)
        out += [f"## {qid}. {q['question']}", ""]
        if q.get("built_by_code"):
            out += ["This answer is built from the \u201cnot found\u201d items of questions 1 to 13 and "
                    "from the records of documents not used; it quotes no passage.", ""]
            continue
        krows = kept_rows(q, ev, cfg)
        if not krows:
            out += ["No sentence of this answer could be confirmed against the passages.", ""]
        for i, (s, text, items) in enumerate(krows, 1):
            out += [f"**Sentence {i}.** {text}", ""]
            for it in items:
                m = doc_meta_for(ev, it, cfg)
                out += [f"*{m.get('title')}* ({kind_label(it['kind'])}; {location(it)})"
                        + (f"; {m['url']}" if m.get("url") else ""), ""]
                quote = quote_text(it["text"]).replace("\n", " ").strip()
                out += ["> " + quote + (" [quotation cut here]" if it.get("cut") else ""), ""]
        if qid in (4, 6):
            out += ["### Requirement level of each Dataset element, by version", "",
                    "Read from each version's own text: the v1.1 schema's \u201cRequired\u201d line per "
                    "field; the 3.0 Dataset page's \u201cRequirement\u201d line per property, in three "
                    "versions; and the working draft's \u201cRequirement level\u201d row per property. "
                    "The draft column is the level the FAIRness Project's public draft gave; the "
                    "project's 2024 FCSM conference slides name that draft as its first deliverable: "
                    f"\u201c{DRAFT_SOURCE_QUOTE}\u201d. \u201cNot listed\u201d means the version does not "
                    "list the element under that name. The draft gives `hasVersion` no level.", ""]
            out += table_md(rows) + [""]
    return "\n".join(out).rstrip() + "\n"


def render_pdf(md: Path, pdf: Path, title: str, landscape: bool = False) -> None:
    # `-smart`: pandoc's smart typography turns "---" into an em dash, and a quoted source's
    # markdown table rule ("---|---") came out as one in the PDF (ADDENDUM 01 step 3). The PDF
    # prints the markdown's own characters, which the lint has already checked.
    cmd = ["pandoc", str(md), "--from=markdown+pipe_tables-smart", "--pdf-engine=typst",
           "--metadata", f"title={title}", "--variable", "papersize=us-letter",
           # pandoc wraps a table in a typst figure, and a figure does not break across pages
           # by default: the element table ran off its page and overprinted its last rows.
           "--variable", "header-includes=#set text(hyphenate: false)\n"
                         "#show figure: set block(breakable: true)"
                         + ("\n#set page(flipped: true)" if landscape else ""),
           "--variable", "margin-x=1.6cm", "--variable", "margin-y=1.8cm",
           "--variable", "fontsize=10pt", "-o", str(pdf)]
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO)
    if r.returncode:
        raise SystemExit(f"FATAL: pandoc/typst failed for {md.name}:\n{r.stderr[-1500:]}")


def strip_title(md: str) -> str:
    """pandoc takes the title from metadata; the markdown's own H1 would print twice."""
    return re.sub(r"\A# .*\n\n", "", md)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--no-pdf", action="store_true")
    a = ap.parse_args(argv)
    global DOCS
    answers = json.loads(ANSWERS.read_text(encoding="utf-8"))
    cfg = EV.load_config()
    DOCS = all_documents()
    bad = [q["question_id"] for q in answers["questions"] if q["status"] != "done"]
    if bad:
        raise SystemExit(f"FATAL: questions not answered and checked: {bad}")
    rows = json.loads(EV.TABLE_JSON.read_text(encoding="utf-8"))["rows"]
    if any("level_2026_10_05" not in r for r in rows):
        raise SystemExit("FATAL: the element table has no 2026-10-05 column; re-run scripts/dcat_faq_evidence.py")
    faq = build_faq(answers, cfg, rows)
    att = build_attachment(answers, cfg, rows)
    # Step 7: the lint runs on both texts before either file is written.
    found = {name: LINT.lint(text) for name, text in (("FAQ.md", faq), ("ATTACHMENT_evidence.md", att))}
    if any(found.values()):
        raise SystemExit("FATAL: lint (scripts/dcat_faq_lint.py) refuses the build:\n" + "\n".join(
            f"  {name}:{f['line']} [{f['rule']}] {f['match']!r} in {f['context']!r}"
            for name, fs in found.items() for f in fs))
    FAQ_MD.write_text(faq, encoding="utf-8")
    ATT_MD.write_text(att, encoding="utf-8")
    BUILD_REPORT.write_text(json.dumps({"generated_by": "scripts/dcat_faq_build.py", **REPORT},
                                       indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    if not a.no_pdf:
        build = OUT / "build"
        build.mkdir(exist_ok=True)
        (build / "faq.md").write_text(strip_title(faq), encoding="utf-8")
        (build / "attachment.md").write_text(strip_title(att), encoding="utf-8")
        render_pdf(build / "faq.md", FAQ_PDF, "DCAT-US 3.0: questions and answers")
        render_pdf(build / "attachment.md", ATT_PDF, "Attachment: the passages behind each answer",
                   landscape=True)
        for f in (build / "faq.md", build / "attachment.md"):
            f.unlink()
        build.rmdir()
    print(json.dumps({"faq": str(FAQ_MD.relative_to(REPO)), "attachment": str(ATT_MD.relative_to(REPO)),
                      "pdf": not a.no_pdf}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
