#!/usr/bin/env python3
"""The instrument entries' reader: Fable reads each entry and answers DN-015 §7's three questions.
**Model spend, bounded.**

`cc_tasks/2026-10-15_instrument_specification_audit.md` Part B, under DN-015 §7. Each entry in
`assessment/instrument/RULE-*.yaml` was written by the session (role `primary`); a model of a
different family (role `judge`) reads it in a fresh context with the verbatim source quotes the
checker has verified (`scripts/instrument.py check`), and answers:

1. does the expected behavior come from the cited source and not from the writer;
2. could a reader who knows the agency misread a fail as a claim the test did not make;
3. is any term undefined.

A "no" on question 1 sends the entry back once (the writer revises it and runs `--round 2
--only <rule_id>`); a second "no" sets `state: invalid` with the reader's reason. Editorial
review, not a measurement. If the harness refuses a reader call by name, the run stops and
reports; the read is never routed through another role.

**Checkpoint** (`~/GitHub/CLAUDE.md` §15, the machinery of `scripts/dcat_faq_run.py`): unit = one
entry read in one round; key = sha1(kind | rule_id:round | entry sha | model | template sha), so
a revised entry, prompt or model is a new unit and a stale read is never reused. Every attempt is
appended and fsynced to `<run_dir>/checkpoint.jsonl` before the next result is awaited, the raw
prompt and response beside it in `<run_dir>/raw/`. Re-running the same command is the resume. A
pilot (`reader.pilot_units`) runs first and the projected total is printed and checked against
the ceiling before any other unit. Progress (done/total, rate, tokens, failures) goes to stdout
and to `reader.progress_log` after every `reader.progress_every_units` units. Ceilings: the shared
spend ledger's (`reader.ceiling_tokens`, reserved before each dispatch) and
`reader.max_wall_seconds`. A failed unit is a row, retried up to `reader.max_attempts`.

    /opt/anaconda3/bin/python3 scripts/instrument_read.py --dry-run
    /opt/anaconda3/bin/python3 scripts/instrument_read.py --round 1
    /opt/anaconda3/bin/python3 scripts/instrument_read.py --round 2 --only RULE-A2-v6
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
for _p in ("", "scripts", "assessment"):
    if str(REPO / _p) not in sys.path:
        sys.path.insert(0, str(REPO / _p))

import yaml  # noqa: E402

import dcat_faq_run as FR  # noqa: E402
import instrument as INS  # noqa: E402

GENERATOR = "scripts/instrument_read.py"
TASK = INS.TASK
VERIFY = "verify.json"

READER_TEMPLATE = """TASK: READ ONE INSTRUMENT ENTRY AND ANSWER THREE QUESTIONS

Below is one entry from the specification of a web measurement instrument. The instrument checks
public websites of U.S. federal statistical agencies and reports, per agency, whether each check
passed or failed. The entry states the check's question, the behavior a ready publisher is
expected to show (with verbatim quotes from the sources it cites), the test the instrument runs,
and what a pass and a fail claim.

Terms the project defines once for every entry (they are not undefined): {glossary}

Answer from the entry alone. For question 1, the QUOTED SOURCE PASSAGES are the only evidence of
what the sources say; do not use what you know of them from elsewhere.

1. Does the EXPECTED BEHAVIOR come from the cited sources and not from the writer? Answer "yes"
   if every requirement the expected-behavior text attributes to a source is supported by a
   quoted passage, and any part no source defines is said plainly to be undefined or the
   project's own. Answer "no" if it states as a source's requirement something the passages do
   not contain; name it.
2. Could a reader who knows the agency misread a FAIL on this check as a claim the test did not
   make? Answer "yes" if the CLAIMS leave such a misreading open (name it), "no" if they close it.
3. Is any term in the entry undefined for a technically literate reader new to this project?
   Answer "yes" and list the terms, or "no".

Return ONLY a JSON object, with no prose before or after it and no code fence:
{{"q1": {{"answer": "yes" or "no", "why": "..."}}, "q2": {{"answer": "yes" or "no", "why": "..."}}, "q3": {{"answer": "yes" or "no", "terms": ["..."], "why": "..."}}}}

ENTRY
{entry}"""

#: The project terms INSTRUMENT.md defines in its preamble (`instrument.GLOSSARY`); the reader is
#: given the same definitions, so question 3 asks about terms an entry leaves undefined.
GLOSSARY = "; ".join(f"{k}: {v}" for k, v in INS.GLOSSARY.items())
READER_SHA = FR.sha(READER_TEMPLATE + GLOSSARY)


def _src_name(s: dict) -> str:
    return s["doc_id"] if "doc_id" in s else s["url"]


def entry_text(e: dict) -> str:
    """The entry as the reader sees it: every field DN-015 §2 names, the verbatim quotes, and the
    branches. No state and no state reason: the reader judges the entry, not the writer's verdict
    on it."""
    def srcs(v):
        return "none" if v in (None, "none") else "; ".join(f"{_src_name(s)} ({s['section']})" for s in v)
    eb, t, c = e["expected_behavior"], e["test"], e["claims"]
    L = [f"CHECK: {e['leg']} ({e['rule_id']}){' — a declaration' if e.get('declaration') else ''}",
         "", "QUESTION:", e["question"]["text"], f"Established by: {srcs(e['question']['established_by'])}",
         "", "EXPECTED BEHAVIOR:", eb["text"], f"Cited sources: {srcs(eb['sources'])}",
         "", "QUOTED SOURCE PASSAGES (verbatim):"]
    for q in eb.get("quotes") or []:
        L.append(f'- [{q["source"]}] "{q["quote"]}"')
    if not eb.get("quotes"):
        L.append("- (none)")
    L += ["", "TEST:", f"Client: {t['client']}", f"Request: {t['request']}", f"Reads: {t['reads']}",
          "Decision rule:"] + [f"- {d}" for d in t["decision_rule"]] + \
         [f"Parameters: {'; '.join(t.get('parameters') or []) or 'none'}",
          f"Is it the recognized way to measure the behavior: {t['recognized_method']}",
          "", "BRANCHES (each verdict branch of the rule; the behavior it rewards or penalizes; its source):"]
    for b in e["branches"]:
        L.append(f"- {b['id']} ({b['verdict']}): {b['behavior']} Source: {srcs(b['sources'])}.")
    L += ["", "CLAIMS:", f"A pass claims: {c['pass']}", f"A fail claims: {c['fail']}",
          f"Neither claims: {c['neither']}", "", "CONFOUNDS:"]
    L += [f"- {x['cause']}. Distinguished: {x['distinguished']}." for x in e["confounds"]]
    if e.get("settles"):
        L += ["", "WHAT THE ENTRY SETTLES:"] + [f"- {k.replace('_', ' ')}: {v}" for k, v in e["settles"].items()]
    return "\n".join(str(x) for x in L) + "\n"


def parse_reader(text: str) -> dict:
    obj = FR._json_payload(text)
    if not isinstance(obj, dict):
        raise ValueError("reader answer is not a JSON object")
    out = {}
    for k in ("q1", "q2", "q3"):
        v = obj.get(k)
        if not isinstance(v, dict) or str(v.get("answer", "")).lower() not in ("yes", "no"):
            raise ValueError(f"reader answer lacks {k}.answer yes|no")
        out[k] = {"answer": v["answer"].lower(), "why": str(v.get("why") or ""),
                  **({"terms": [str(x) for x in v.get("terms") or []]} if k == "q3" else {})}
    return out


class Reader:
    def __init__(self, rc: dict, run_dir: Path, consumer, model: str, log=print):
        self.rc, self.run_dir = rc, run_dir
        self.ck = FR.Checkpoint(run_dir / "checkpoint.jsonl")
        self.raw = run_dir / "raw"
        self.consumer, self.model, self.log = consumer, model, log
        self.t0 = time.time()
        self.calls = self.done = self.failed = self.tokens = 0

    def read(self, e: dict, rnd: int) -> dict:
        text = entry_text(e)
        prompt = READER_TEMPLATE.format(entry=text, glossary=GLOSSARY)
        input_sha = FR.sha(text)
        uid = FR.unit_id("read", f"{e['rule_id']}:{rnd}", input_sha, self.model, READER_SHA)
        prior = [r for r in self.ck.read() if r["unit_id"] == uid]
        done = next((r for r in prior if r["status"] == "done"), None)
        if done:
            return {"rule_id": e["rule_id"], "round": rnd, "unit_id": uid, "model_id": self.model,
                    "entry_sha256": input_sha, "answers": done["parsed"], "resumed": True}
        attempt = max((r["attempt"] for r in prior), default=0)
        rec = None
        while attempt < self.rc["max_attempts"]:
            attempt += 1
            if time.time() - self.t0 > self.rc["max_wall_seconds"]:
                raise FR.StopRun(f"wall_clock: {self.rc['max_wall_seconds']} s")
            base = {"unit_id": uid, "kind": "read", "rule_id": e["rule_id"], "round": rnd, "attempt": attempt,
                    "model_id": self.model, "role": self.rc["role"], "input_sha256": input_sha,
                    "template_sha256": READER_SHA, "prompt_sha256": FR.sha(prompt), "run_id": self.rc["run_id"]}
            t = time.time()
            comp, err = FR.call(self.consumer, self.model, prompt, f"instrument.{uid}.r{rnd}.a{attempt}")
            self.calls += 1
            if comp is None:
                self.failed += 1
                self.ck.append({**base, "status": "error", "error": err, "tokens": 0, "usage": {}, "ts": FR._now()})
                continue
            self.raw.mkdir(parents=True, exist_ok=True)
            (self.raw / f"{uid}.a{attempt}.json").write_text(json.dumps(
                {**base, "model_receipt": getattr(comp, "receipt", None), "prompt": prompt,
                 "response_text": comp.text, "usage": comp.usage}, indent=1, ensure_ascii=False), encoding="utf-8")
            try:
                parsed, status, error = parse_reader(comp.text), "done", None
            except (ValueError, KeyError, TypeError) as exc:
                parsed, status, error = None, "unparsed", str(exc)[:300]
            tok = FR._tokens(comp.usage)
            self.tokens += tok
            rec = {**base, "status": status, "error": error, "parsed": parsed, "usage": comp.usage,
                   "tokens": tok, "wall_s": round(time.time() - t, 2), "ts": FR._now()}
            self.ck.append(rec)
            if status == "done":
                return {"rule_id": e["rule_id"], "round": rnd, "unit_id": uid, "model_id": self.model,
                        "entry_sha256": input_sha, "answers": parsed, "tokens": tok}
            self.failed += 1
        raise FR.StopRun(f"{e['rule_id']} round {rnd} not done in {self.rc['max_attempts']} attempts: "
                         f"{rec and rec.get('error')}")

    def progress(self, total: int) -> None:
        el = time.time() - self.t0
        rate = self.done / el if el else 0
        eta = (total - self.done) / rate if rate else float("nan")
        self.log(f"[instrument +{el:7.1f}s] {self.done}/{total} done, {rate * 60:.2f}/min, ETA {eta:.0f}s, "
                 f"tokens {self.tokens:,}, calls {self.calls}, failures {self.failed}")


class ScriptedReader:
    """Test double for the SIGKILL resume test (§15 item 8), selected by
    `INSTRUMENT_READ_SCRIPTED_CONSUMER=<json spec>`: answers yes/no/no from fixed text and appends
    its call id to `calls_log` BEFORE answering. Never selected in production."""

    def __init__(self, spec_path: str):
        spec = json.loads(Path(spec_path).read_text(encoding="utf-8"))
        self.sleep_s = float(spec.get("sleep_s", 0))
        self.calls_log = Path(spec["calls_log"])
        self.model_id = spec.get("model_id", "scripted-model")

    def complete(self, prompt: str, *, call_id: str):
        from harness.consumers import Completion
        with self.calls_log.open("a", encoding="utf-8") as fh:
            fh.write(call_id + "\n")
            fh.flush()
            os.fsync(fh.fileno())
        time.sleep(self.sleep_s)
        text = json.dumps({"q1": {"answer": "yes", "why": "scripted"}, "q2": {"answer": "no", "why": "scripted"},
                           "q3": {"answer": "no", "terms": [], "why": "scripted"}})
        return Completion(text=text, model_id=self.model_id, usage={"inputTokens": 1, "outputTokens": 1})


def consumer(rc: dict, scripted: str | None):
    if scripted:
        c = ScriptedReader(scripted)
        return c, c.model_id
    from kg import spend
    from kg.extraction import model_stub
    from harness.consumers import ClaudeCLIConsumer, ConsumerConfig
    model_stub.guard_no_api_key()
    cfg = ConsumerConfig(role=rc["role"], provider=FR.PROVIDER, timeout_seconds=rc["timeout_seconds"],
                         call_class=rc["call_class"])
    led = spend.default_ledger()
    st = led.status().get("runs", {}).get(rc["run_id"])
    if st is None or int(st.get("ceiling_tokens") or 0) != rc["ceiling_tokens"]:
        led.declare(rc["run_id"], rc["ceiling_tokens"], declared_by=f"{GENERATOR} ({TASK})",
                    call_class=rc["call_class"], **({"supersede": True} if st else {}))
    spend.set_current_run(rc["run_id"])
    return ClaudeCLIConsumer(cfg), cfg.model_id


def merge_verify(run_dir: Path, reads: list, model: str, extra: dict | None = None) -> dict:
    run_dir.mkdir(parents=True, exist_ok=True)
    p = run_dir / VERIFY
    cur = json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {"generated_by": GENERATOR, "task": TASK}
    keep = {(r["rule_id"], r["round"]): r for r in cur.get("reads", [])}
    for r in reads:
        keep[(r["rule_id"], r["round"])] = r
    cur["reads"] = sorted(keep.values(), key=lambda r: (r["rule_id"], r["round"]))
    cur["model_id"] = model
    cur.update(extra or {})
    cur["updated_at"] = FR._now()
    p.write_text(json.dumps(cur, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return cur


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--round", type=int)
    ap.add_argument("--only", nargs="*", default=None, help="rule ids to read (default: every entry)")
    ap.add_argument("--run-dir", default=None)
    ap.add_argument("--entries-dir", default=None, help="test seam (default: assessment/instrument)")
    ap.add_argument("--progress-log", default=None)
    a = ap.parse_args(argv)
    cfg = INS.load_config()
    rc = cfg["reader"]
    entries = INS.load_entries(Path(a.entries_dir) if a.entries_dir else INS.ENTRY_DIR)
    if a.only:
        entries = [e for e in entries if e["rule_id"] in set(a.only)]
    run_dir = Path(a.run_dir) if a.run_dir else REPO / rc["run_dir"]
    plog = Path(a.progress_log) if a.progress_log else REPO / rc["progress_log"]
    plog.parent.mkdir(parents=True, exist_ok=True)

    def log(msg: str) -> None:
        print(msg, flush=True)
        with plog.open("a", encoding="utf-8") as fh:
            fh.write(f"{FR._now()} {msg}\n")

    if a.dry_run:
        for e in entries:
            print(f"{e['rule_id']}: {len(entry_text(e))} chars")
        print(f"reader role {rc['role']}; ceiling {rc['ceiling_tokens']:,} tokens; {len(entries)} entries")
        print("--- first entry as read ---")
        print(entry_text(entries[0]))
        return 0

    cons, model = consumer(rc, os.environ.get("INSTRUMENT_READ_SCRIPTED_CONSUMER"))
    rd = Reader(rc, run_dir, cons, model, log)
    reads = []
    try:
        for i, e in enumerate(entries):
            r = rd.read(e, a.round)
            reads.append(r)
            rd.done += 1
            merge_verify(run_dir, [r], model)
            log(f"READ {e['rule_id']} r{a.round}: q1 {r['answers']['q1']['answer']}, "
                f"q2 {r['answers']['q2']['answer']}, q3 {r['answers']['q3']['answer']}")
            if i + 1 == rc["pilot_units"] and len(entries) > i + 1 and not r.get("resumed"):
                proj = int(rd.tokens / (i + 1) * len(entries))
                log(f"PILOT: {rd.tokens:,} tokens over {i + 1} unit(s), {time.time() - rd.t0:.0f}s; projected "
                    f"{proj:,} tokens for {len(entries)} (measured, not guessed); ceiling {rc['ceiling_tokens']:,}")
                if proj > rc["ceiling_tokens"]:
                    raise FR.StopRun(f"pilot projects {proj:,} tokens past the ceiling {rc['ceiling_tokens']:,}")
            if rd.done % rc["progress_every_units"] == 0:
                rd.progress(len(entries))
        return 0
    except FR.StopRun as exc:
        merge_verify(run_dir, reads, model, {"stopped": str(exc)})
        log(f"STOP: {exc}")
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
