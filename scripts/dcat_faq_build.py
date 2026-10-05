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

OUT = EV.OUT
ANSWERS = OUT / "answers.json"
FAQ_MD, FAQ_PDF = OUT / "FAQ.md", OUT / "FAQ.pdf"
ATT_MD, ATT_PDF = OUT / "ATTACHMENT_evidence.md", OUT / "ATTACHMENT_evidence.pdf"
PREPARED = "5 October 2026"
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
        return "framework", {"title": "AI-readiness framework for federal statistical publishers, "
                                      "indicator text", "issuer": "", "date": "", "url": ""}
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


def doc_meta_for(ev: dict, it: dict) -> dict:
    m = ev["documents"].get(it["doc_id"])
    if m:
        return m
    if it.get("kind") == "catalog record (not admitted)":
        return {"title": it["text"].split(". ")[0], "issuer": "", "date": "", "url": ""}
    if it.get("kind") == "element table row":
        return {"title": "Requirement levels compared across DCAT-US versions (table in the attachment)",
                "issuer": "", "date": "", "url": ""}
    if it.get("kind") == "indicator":
        return {"title": "AI-readiness framework for federal statistical publishers", "issuer": "",
                "date": "", "url": ""}
    return {"title": it["doc_id"], "issuer": "", "date": "", "url": ""}


def load(qid: int) -> dict:
    return json.loads((EV.EVIDENCE_DIR / f"Q{qid}.json").read_text(encoding="utf-8"))


def build_faq(answers: dict, cfg: dict) -> str:
    out = ["# DCAT-US 3.0: questions and answers", "",
           f"Prepared {PREPARED} for a briefing to the Office of Management and Budget.", "",
           "How these answers were made. Each answer was drafted by one AI model reading only the "
           "passages quoted in the attachment, and each sentence was then checked against the "
           "passages it cites by a different AI model. A sentence the check could not confirm "
           "was removed, not reworded. The attachment quotes every passage the answers rely on.", "",
           "\u201cNot found\u201d lists what the documents collected for this briefing do not say. "
           "Each item was checked twice: against the passages gathered for its question, and "
           "against a second search of the same documents using the item's own words. An item "
           "means the search did not find it; it does not mean that no document anywhere says it.", ""]
    for q in answers["questions"]:
        ev = load(q["question_id"])
        by_id = {it["id"]: it for it in ev["items"]}
        out += [f"## {q['question_id']}. {q['question']}", ""]
        refs, metas, secs = {}, {}, {}
        sentences = []
        for s in q["kept"]:
            marks = []
            for eid in s["evidence"]:
                it = by_id[eid]
                key, meta = canonical(it, DOCS, cfg)
                if key not in refs:
                    refs[key], metas[key], secs[key] = len(refs) + 1, meta, []
                sec = it.get("section") or ""
                if sec and sec not in secs[key] and it["kind"] not in ("element table row",):
                    secs[key].append(sec)
                marks.append(refs[key])
            marks = sorted(set(marks))
            sentences.append(s["text"].rstrip() + " " + "".join(f"[{m}]" for m in marks))
        out += [" ".join(sentences) if sentences else NONE_KEPT, ""]
        if q["not_known_kept"]:
            out += ["Not found:", ""]
            out += [f"- {n['text']}" for n in q["not_known_kept"]]
            out.append("")
        if q["question_id"] == GAPS_QUESTION:
            out += gaps_listing(answers, ev)
        if refs:
            out += ["Sources:", ""]
            for key, n in refs.items():
                out.append(f"{n}. {citation(metas[key], secs[key])}")
            out.append("")
    return "\n".join(out).rstrip() + "\n"


GAPS_QUESTION = 14
DOCS: dict = {}


def gaps_listing(answers: dict, ev: dict) -> list:
    """For the "what can the sources not answer" question: every "not found" item kept on the
    earlier questions, by question, and the documents known to exist that the collection does
    not hold, quoted from their catalog records. All of it was checked upstream; nothing here is
    new text."""
    out = ["Every unanswered part of the earlier answers, by question:", ""]
    for q in answers["questions"]:
        if q["question_id"] == GAPS_QUESTION or not q["not_known_kept"]:
            continue
        out.append(f"- Question {q['question_id']}:")
        out += [f"    - {n['text']}" for n in q["not_known_kept"]]
    out.append("")
    cats = [it for it in ev["items"] if it["kind"] == "catalog record (not admitted)"]
    if cats:
        out += ["Documents known to exist that were not available for this briefing, as their "
                "catalog records describe them:", ""]
        for it in cats:
            out.append(f"- {catalog_plain(it['text'])}")
        out.append("")
    return out


def catalog_plain(text: str) -> str:
    """A catalog record's title and its stated reason, without the record's status code."""
    title, _, rest = text.partition(". ")
    rest = re.sub(r"NOT ADMITTED \([^)]*\)\.?\s*", "", rest).strip()
    return f"{title}. {rest}" if rest else title


def table_md(rows: list) -> list:
    head = ["| Element | DCAT-US v1.1: required? | 3.0 Dataset page, 15 Sep 2026 | "
            "3.0 Dataset page, 21 Aug 2026 | FAIRness Project draft (captured 4 May 2025) |",
            "|---|---|---|---|---|"]
    body = []
    for r in rows:
        cells = [f"`{r['element']}`", r["v11_required"] or "not listed",
                 r["level_2026_09_15"] or "not listed", r["level_2026_08_21"] or "not listed",
                 r["draft_level"] or "not listed"]
        body.append("| " + " | ".join(c.replace("|", "/") for c in cells) + " |")
    return head + body


def build_attachment(answers: dict) -> str:
    rows = json.loads(EV.TABLE_JSON.read_text(encoding="utf-8"))["rows"]
    out = ["# Attachment: the passages behind each answer", "",
           f"Prepared {PREPARED}. For each question, every passage an answer sentence cites, "
           "quoted as it appears in the source, with where to find it. Documents captured from "
           "the web are quoted as captured on the date shown; the DCAT-US 3.0 pages have been "
           "revised since some captures. In quoted web text, a link to another part of the same "
           "page is shown as its link text.", ""]
    for q in answers["questions"]:
        ev = load(q["question_id"])
        by_id = {it["id"]: it for it in ev["items"]}
        out += [f"## {q['question_id']}. {q['question']}", ""]
        if not q["kept"]:
            out += ["No sentence of this answer could be confirmed against the passages.", ""]
        for i, s in enumerate(q["kept"], 1):
            out += [f"**Sentence {i}.** {s['text']}", ""]
            for eid in s["evidence"]:
                it = by_id[eid]
                m = doc_meta_for(ev, it)
                out += [f"*{m.get('title')}* ({kind_label(it['kind'])}; {location(it)})"
                        + (f"; {m['url']}" if m.get("url") else ""), ""]
                quote = anchor_links_as_text(it["text"]).replace("\n", " ").strip()
                out += ["> " + quote + (" [quotation cut here]" if it.get("cut") else ""), ""]
        if q["question_id"] in (4, 6):
            out += ["### Requirement level of each Dataset element, by version", "",
                    "Read from each version's own text: the v1.1 schema's “Required” line per "
                    "field; the 3.0 Dataset page's “Requirement” line per property, in two "
                    "captures; and the working draft's “Requirement level” row per property. "
                    "The draft column is the level the FAIRness Project's public draft gave; the "
                    "project's 2024 FCSM conference slides name that draft as its first deliverable: "
                    f"“{DRAFT_SOURCE_QUOTE}”. “Not listed” means the version does not "
                    "list the element under that name. The draft gives `hasVersion` no level.", ""]
            out += table_md(rows) + [""]
    return "\n".join(out).rstrip() + "\n"


def render_pdf(md: Path, pdf: Path, title: str, landscape: bool = False) -> None:
    cmd = ["pandoc", str(md), "--from=markdown+pipe_tables", "--pdf-engine=typst",
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
    faq, att = build_faq(answers, cfg), build_attachment(answers)
    FAQ_MD.write_text(faq, encoding="utf-8")
    ATT_MD.write_text(att, encoding="utf-8")
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
