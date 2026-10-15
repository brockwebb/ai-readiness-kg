#!/usr/bin/env python3
"""The hostile reader: the most hostile agency representative in the room reads every dictionary
entry and the preface and writes the objection. **Model spend, bounded.**

`cc_tasks/2026-10-15_readiness_diagnostic_package.md` Part C, under DN-016 §3 and ruling 6. The
diagnostic package's plain-language content — the sixteen dictionary entries (from the framework
record's `rf_*` fields) and the preface (from `reports/diagnostic/preface_source.yaml`) — is read
by a model of role `judge` (Step 0 resolved the hostile reader to `judge`: neither `judge` nor
`critic` is Opus 5.5, and the task's rule is to use `judge` and record the pin). Three questions:

1. what would I object to;
2. what word would I not understand;
3. what would I say we were secretly doing.

Round two runs only on a unit whose round one raised an objection (question 1). An entry whose
round-two objection matches round one is rewritten by the author and read a third time; a third
match is recorded, not rewritten again (the author's judgement, outside this script).

**Checkpoint** (`~/GitHub/CLAUDE.md` §15), reusing the machinery of `scripts/dcat_faq_run.py` and
`scripts/instrument_read.py`: unit = one item read in one round; key =
sha1(kind | item:round | item sha | model | template sha). Every attempt is appended and fsynced
before the next is awaited, the raw prompt and response beside it. Re-running the same command is
the resume. A pilot runs first and the projected total is checked against the ceiling. Ceilings:
the shared spend ledger's and `hostile_reader.max_wall_seconds`.

    /opt/anaconda3/bin/python3 scripts/instrument_hostile_read.py --dry-run
    /opt/anaconda3/bin/python3 scripts/instrument_hostile_read.py --round 1
    /opt/anaconda3/bin/python3 scripts/instrument_hostile_read.py --round 2 --only A2 preface
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
for _p in ("", "scripts"):
    if str(REPO / _p) not in sys.path:
        sys.path.insert(0, str(REPO / _p))

import dcat_faq_run as FR  # noqa: E402
import diagnostic_package as D  # noqa: E402
import instrument as INS  # noqa: E402
import instrument_read as IR  # noqa: E402
import diagnostic_package_build as B  # noqa: E402

GENERATOR = "scripts/instrument_hostile_read.py"
TASK = INS.TASK
VERIFY = "verify.json"

TEMPLATE = """You are the single most hostile representative of a U.S. federal statistical agency
in the room at a working group. Someone has built a "readiness diagnostic" that rates your
agency's public website on whether machines can reach, read and use the data you publish, and is
about to show the room the item below. Read it as that hostile representative — skeptical,
protective of your agency, alert to being made to look bad — and answer three questions bluntly
and specifically, quoting the item's words where you can:

1. What in this item would you OBJECT to: a claim you find unfair or wrong, or that makes your
   agency look bad for something you would say is not your fault or not your doing?
2. What WORD or phrase here would you, or a non-technical colleague, not understand?
3. What would you say we are SECRETLY DOING: what hidden agenda, trap, or gotcha would you
   suspect behind this item?

Answer only from the item. For each question, "raised" is "yes" if you have a real objection /
an unclear word / a suspicion, and "no" if you genuinely have none. Return ONLY a JSON object,
no prose before or after and no code fence:
{{"object_to": {{"raised": "yes" or "no", "text": "..."}}, "word_not_understood": {{"raised": "yes" or "no", "text": "..."}}, "secretly_doing": {{"raised": "yes" or "no", "text": "..."}}}}

ITEM ({kind})
{item}"""
TEMPLATE_SHA = FR.sha(TEMPLATE)


def preface_text() -> str:
    """The preface as a reader sees it, from the resolved source (the same content the Word and
    deck render)."""
    values = B.compute_values()
    pf = B.load_preface(values)
    L = [pf["title"], "", pf["what_it_is"], "", "HOW IT BEHAVES:"]
    L += [f"- {x}" for x in pf["how_it_behaves"]]
    L += ["", "WHAT IT NEVER DOES:"] + [f"- {x}" for x in pf["what_it_never_does"]]
    L += ["", "THE FOUR STATES:", pf["four_states_note"],
          "", "THE TWO RUNGS:", pf["two_rungs_note"],
          "", "WHAT THIS IS NOT:", pf["what_it_is_not"],
          "", "NOT A LEAGUE TABLE:", pf["not_a_league_table"],
          "", "A FEW TERMS:"] + [f"- {g['term']}: {g['plain']}" for g in pf["glossary"]]
    return "\n".join(L)


def entry_text(e: dict) -> str:
    """One dictionary entry as the agency representative sees it (plain language only)."""
    L = [f"CHECK: {e['plain_name']}" + (f"  ({e['marker']})" if e["marker"] else ""),
         "", f"How this check counts: {e['how_counts']}",
         f"The question: {e['question']}",
         f"Where we look: {e['where_we_look']}",
         f"What the client does: {e['what_client_does']}"]
    L += [f"{label}: {text}" for label, text in e["outcome"]]
    L += [f"Why it matters: {e['why_it_matters']}",
          f"Who else runs this check: {e['who_else']}",
          f"What rung two changes: {e['rung_two_changes']}"]
    return "\n".join(L)


def units() -> list[dict]:
    """The read units: one per dictionary entry (keyed by leg), then the preface."""
    vocab = D.load_vocab()
    out = [{"key": e["leg"], "kind": f"check {e['plain_name']}", "text": entry_text(e)}
           for e in B.dict_entries(vocab)]
    out.append({"key": "preface", "kind": "the preface (page one)", "text": preface_text()})
    return out


def parse(text: str) -> dict:
    obj = FR._json_payload(text)
    if not isinstance(obj, dict):
        raise ValueError("answer is not a JSON object")
    out = {}
    for k in ("object_to", "word_not_understood", "secretly_doing"):
        v = obj.get(k)
        if not isinstance(v, dict) or str(v.get("raised", "")).lower() not in ("yes", "no"):
            raise ValueError(f"answer lacks {k}.raised yes|no")
        out[k] = {"raised": v["raised"].lower(), "text": str(v.get("text") or "")}
    return out


def merge_verify(run_dir: Path, reads: list, model: str, extra: dict | None = None) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    p = run_dir / VERIFY
    cur = json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {"generated_by": GENERATOR, "task": TASK}
    keep = {(r["key"], r["round"]): r for r in cur.get("reads", [])}
    for r in reads:
        keep[(r["key"], r["round"])] = r
    cur["reads"] = sorted(keep.values(), key=lambda r: (r["key"], r["round"]))
    cur["model_id"] = model
    cur.update(extra or {})
    cur["updated_at"] = FR._now()
    p.write_text(json.dumps(cur, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--round", type=int)
    ap.add_argument("--only", nargs="*", default=None, help="unit keys (legs, or 'preface')")
    a = ap.parse_args(argv)
    cfg = INS.load_config()
    rc = cfg["hostile_reader"]
    us = units()
    if a.only:
        want = set(a.only)
        us = [u for u in us if u["key"] in want]
    run_dir = REPO / rc["run_dir"]
    plog = REPO / rc["progress_log"]
    plog.parent.mkdir(parents=True, exist_ok=True)

    def log(msg: str) -> None:
        print(msg, flush=True)
        with plog.open("a", encoding="utf-8") as fh:
            fh.write(f"{FR._now()} {msg}\n")

    if a.dry_run:
        for u in us:
            print(f"{u['key']}: {len(u['text'])} chars")
        print(f"hostile reader role {rc['role']}; ceiling {rc['ceiling_tokens']:,}; {len(us)} units")
        print("--- first unit ---")
        print(TEMPLATE.format(kind=us[0]["kind"], item=us[0]["text"]))
        return 0

    import os
    cons, model = IR.consumer(rc, os.environ.get("INSTRUMENT_READ_SCRIPTED_CONSUMER"))
    ck = FR.Checkpoint(run_dir / "checkpoint.jsonl")
    raw = run_dir / "raw"
    t0 = time.time()
    done = failed = tokens = 0
    reads = []
    try:
        for i, u in enumerate(us):
            uid = FR.unit_id("hostile", f"{u['key']}:{a.round}", FR.sha(u["text"]), model, TEMPLATE_SHA)
            prior = [r for r in ck.read() if r["unit_id"] == uid]
            hit = next((r for r in prior if r["status"] == "done"), None)
            if hit:
                r = {"key": u["key"], "round": a.round, "unit_id": uid, "model_id": model,
                     "answers": hit["parsed"], "resumed": True}
                reads.append(r)
                done += 1
                merge_verify(run_dir, [r], model)
                log(f"READ {u['key']} r{a.round} (resumed): object={r['answers']['object_to']['raised']}")
                continue
            prompt = TEMPLATE.format(kind=u["kind"], item=u["text"])
            attempt = max((p["attempt"] for p in prior), default=0)
            rec = None
            while attempt < rc["max_attempts"]:
                attempt += 1
                if time.time() - t0 > rc["max_wall_seconds"]:
                    raise FR.StopRun(f"wall_clock {rc['max_wall_seconds']}s")
                base = {"unit_id": uid, "kind": "hostile", "key": u["key"], "round": a.round,
                        "attempt": attempt, "model_id": model, "role": rc["role"],
                        "input_sha256": FR.sha(u["text"]), "template_sha256": TEMPLATE_SHA,
                        "run_id": rc["run_id"]}
                t = time.time()
                comp, err = FR.call(cons, model, prompt, f"hostile.{u['key']}.r{a.round}.a{attempt}")
                if comp is None:
                    failed += 1
                    ck.append({**base, "status": "error", "error": err, "tokens": 0, "ts": FR._now()})
                    continue
                raw.mkdir(parents=True, exist_ok=True)
                (raw / f"{uid}.a{attempt}.json").write_text(json.dumps(
                    {**base, "model_receipt": getattr(comp, "receipt", None), "prompt": prompt,
                     "response_text": comp.text, "usage": comp.usage}, indent=1, ensure_ascii=False),
                    encoding="utf-8")
                try:
                    parsed, status, error = parse(comp.text), "done", None
                except (ValueError, KeyError, TypeError) as exc:
                    parsed, status, error = None, "unparsed", str(exc)[:300]
                tok = FR._tokens(comp.usage)
                tokens += tok
                rec = {**base, "status": status, "error": error, "parsed": parsed,
                       "usage": comp.usage, "tokens": tok, "wall_s": round(time.time() - t, 2),
                       "ts": FR._now()}
                ck.append(rec)
                if status == "done":
                    break
                failed += 1
            if rec is None or rec["status"] != "done":
                raise FR.StopRun(f"{u['key']} r{a.round} not done: {rec and rec.get('error')}")
            r = {"key": u["key"], "round": a.round, "unit_id": uid, "model_id": model,
                 "answers": rec["parsed"], "tokens": rec["tokens"]}
            reads.append(r)
            done += 1
            merge_verify(run_dir, [r], model)
            ans = r["answers"]
            log(f"READ {u['key']} r{a.round}: object={ans['object_to']['raised']} "
                f"word={ans['word_not_understood']['raised']} secret={ans['secretly_doing']['raised']}")
            if i + 1 == rc["pilot_units"] and len(us) > i + 1 and not r.get("resumed"):
                proj = int(tokens / (i + 1) * len(us))
                log(f"PILOT: {tokens:,} tokens over {i+1} unit(s); projected {proj:,} for {len(us)} "
                    f"(measured); ceiling {rc['ceiling_tokens']:,}")
                if proj > rc["ceiling_tokens"]:
                    raise FR.StopRun(f"pilot projects {proj:,} past ceiling {rc['ceiling_tokens']:,}")
            el = time.time() - t0
            log(f"[hostile +{el:6.1f}s] {done}/{len(us)} done, tokens {tokens:,}, failures {failed}")
        return 0
    except FR.StopRun as exc:
        merge_verify(run_dir, reads, model, {"stopped": str(exc)})
        log(f"STOP: {exc}")
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
