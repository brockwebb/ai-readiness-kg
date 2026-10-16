#!/usr/bin/env python3
"""The hostile reader's three questions on page one of the readiness brief. **Model spend.**

`cc_tasks/2026-10-16_readiness_brief.md` Part A, "Read": role `critic` reads page one ONCE with
three questions: what would I object to; what word would I not understand; what would I say we
were secretly doing. The answers are written verbatim to `reports/diagnostic/brief/critic_run/`
and quoted in the RESULT. A word flagged as not understood is replaced by the author; an
objection is recorded, not rewritten.

Page one is the Word document's first page as rendered (LibreOffice headless to a temporary PDF,
first page's text), so the reader sees exactly what the operator hands out.

**Checkpoint** (`~/GitHub/CLAUDE.md` §15), reusing `scripts/dcat_faq_run.py`: unit = one call;
key = sha1(kind | page sha | model | template sha). Re-running is the resume; a changed page is a
new unit. The run's ceiling is declared on the spend ledger before the call (DD-022).

    /opt/anaconda3/bin/python3 scripts/readiness_brief_critic.py [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
for _p in ("", "scripts"):
    if str(REPO / _p) not in sys.path:
        sys.path.insert(0, str(REPO / _p))

import dcat_faq_run as FR  # noqa: E402
import instrument_read as IR  # noqa: E402

GENERATOR = "scripts/readiness_brief_critic.py"
TASK = "cc_tasks/2026-10-16_readiness_brief.md"
DOCX = REPO / "reports" / "diagnostic" / "brief" / "READINESS_BRIEF.docx"
RUN_DIR = REPO / "reports" / "diagnostic" / "brief" / "critic_run"
#: The run's spend declaration (role critic -> the lock's Sonnet; billed under call_class judge,
#: whose floor is in controls.yaml, as the diagnostic package's checker was).
RUN = {"role": "critic", "call_class": "judge", "run_id": "readiness_brief_critic_2026-10-16",
       "ceiling_tokens": 200000, "timeout_seconds": 600, "max_attempts": 2}

TEMPLATE = """You are a hostile reader: a senior official at a federal statistical agency who has
just been handed the first page of a brief about a readiness diagnostic run against agencies'
public websites, including yours. Read it as that person would, looking for reasons to distrust
it. Answer three questions, each honestly and specifically; do not be agreeable and do not invent
objections you would not really raise.

1. What would I object to? Quote the passage each objection is about.
2. What word or phrase would I not understand? List each one exactly as it appears on the page.
   If every word is clear, say so.
3. What would I say they were secretly doing? Say it in the words you would use to a colleague.

Return ONLY a JSON object, no prose and no code fence:
{{"objections": [{{"passage": "...", "objection": "..."}}], "words_not_understood": ["..."], "secretly_doing": "..."}}

PAGE ONE
{page}"""
TEMPLATE_SHA = FR.sha(TEMPLATE)


def page_one(docx: Path = DOCX) -> str:
    from pypdf import PdfReader
    with tempfile.TemporaryDirectory() as td:
        r = subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", td, str(docx)],
                           capture_output=True, text=True, timeout=180)
        pdf = Path(td) / (docx.stem + ".pdf")
        if r.returncode != 0 or not pdf.is_file():
            raise SystemExit(f"FATAL: could not render {docx.name}: {r.stderr[-400:]}")
        return PdfReader(str(pdf)).pages[0].extract_text()


def parse(text: str) -> dict:
    t = text.strip()
    if t.startswith("```"):
        t = t.strip("`").split("\n", 1)[1] if "\n" in t else t
    a, b = t.find("{"), t.rfind("}")
    d = json.loads(t[a:b + 1])
    for k in ("objections", "words_not_understood", "secretly_doing"):
        if k not in d:
            raise KeyError(k)
    return d


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    page = page_one()
    prompt = TEMPLATE.format(page=page)
    if a.dry_run:
        print(prompt)
        return 0
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    cons, model = IR.consumer(RUN, None)
    ck = FR.Checkpoint(RUN_DIR / "checkpoint.jsonl")
    uid = FR.unit_id("critic", "brief_page_one", FR.sha(prompt), model, TEMPLATE_SHA)
    prior = [r for r in ck.read() if r["unit_id"] == uid]
    done = next((r for r in prior if r["status"] == "done"), None)
    if done:
        reading = done["parsed"]
    else:
        attempt = max((p["attempt"] for p in prior), default=0)
        reading = None
        while attempt < RUN["max_attempts"]:
            attempt += 1
            comp, err = FR.call(cons, model, prompt, f"critic.brief.a{attempt}")
            if comp is None:
                ck.append({"unit_id": uid, "status": "error", "error": err, "attempt": attempt, "ts": FR._now()})
                continue
            (RUN_DIR / "raw").mkdir(exist_ok=True)
            (RUN_DIR / "raw" / f"{uid}.a{attempt}.json").write_text(json.dumps(
                {"prompt": prompt, "response_text": comp.text, "usage": comp.usage,
                 "model_receipt": getattr(comp, "receipt", None)}, indent=1, ensure_ascii=False), encoding="utf-8")
            try:
                reading = parse(comp.text)
                ck.append({"unit_id": uid, "status": "done", "attempt": attempt, "model_id": model,
                           "parsed": reading, "usage": comp.usage, "tokens": FR._tokens(comp.usage), "ts": FR._now()})
                break
            except (ValueError, KeyError, TypeError) as exc:
                ck.append({"unit_id": uid, "status": "unparsed", "attempt": attempt, "error": str(exc)[:300], "ts": FR._now()})
        if reading is None:
            print(json.dumps({"stopped": "critic did not return a parseable reading", "model": model}))
            return 3
    out = {"generated_by": GENERATOR, "task": TASK, "model_id": model, "unit_id": uid,
           "page_one_sha": FR.sha(page), "page_one": page, "reading": reading}
    (RUN_DIR / "critic_reading.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"model_id": model, "reading": reading}, indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
