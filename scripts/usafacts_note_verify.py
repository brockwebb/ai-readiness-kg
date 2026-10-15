#!/usr/bin/env python3
"""The USAFacts note's reader: Fable reads the built note and answers two questions.
**Model spend, bounded.**

`cc_tasks/2026-10-14_usafacts_note.md` Part B/C (DN-014 ADDENDUM 01 §5). The note's prose is
written by the author (Opus 4.8) and gated for free by `scripts/usafacts_note_build.py`; this
script is Fable's reading only. Editorial review, not a measurement.

* `--read N`: one reading round. Fable (role `judge`) reads the built note in a fresh context and
  answers the two questions in the source: (1) does a reader who knows USAFacts' guide learn what
  this work did with it; (2) is any term on the page one a CIO new to SI would not know. At most
  two rounds (the task's cap). If the harness refuses the reader call (a named refusal) the run
  stops and reports; the read is not routed through another role.

**Checkpoint** (`~/GitHub/CLAUDE.md` §15, the machinery of `scripts/dcat_faq_run.py`): unit = one
call; key = sha1(kind | round | input sha | model | template sha), so a revised note, prompt or
model is a new unit and a stale read is never reused. Every attempt is appended and fsynced to
`run_usafacts_note/checkpoint.jsonl` before the next is awaited, the raw prompt and response
beside it in `run_usafacts_note/raw/`. Re-running is the resume. Ceilings: the shared spend
ledger's (`run.ceiling_tokens`, reserved before each dispatch) and `run.max_wall_seconds`.

    /opt/anaconda3/bin/python3 scripts/usafacts_note_verify.py --dry-run
    /opt/anaconda3/bin/python3 scripts/usafacts_note_verify.py --read 1
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
import usafacts_note_build as NB  # noqa: E402

GENERATOR = "scripts/usafacts_note_verify.py"
TASK = "cc_tasks/2026-10-14_usafacts_note.md"
OUT = REPO / "reports" / "summary"
SOURCE = OUT / "usafacts_note_source.yaml"
RUN_DIR = OUT / "run_usafacts_note"
VERIFY = "verify.json"
PROGRESS_LOG = REPO / "logs" / "2026-10-15_usafacts_note_progress.log"

READER_TEMPLATE = """TASK: READ AND ANSWER

Below is a short note. Read it, and answer the questions using only what it says. Do not use anything you know from elsewhere beyond the one background fact each question names.

1. {q1}
2. {q2}

Return ONLY a JSON object, with no prose before or after it and no code fence:
{{"q1": "...", "q2": "..."}}

NOTE
{note}"""

READER_SHA = FR.sha(READER_TEMPLATE)


def load_source(path: Path = SOURCE) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def reader_text(src: dict) -> str:
    """The note as Fable reads it: the built Markdown with its H1 stripped (the summary's seam),
    so the reader sees the prose and the Sources, not a duplicated title."""
    manifest = json.loads((REPO / src["inputs"]["manifest"]).read_text(encoding="utf-8"))
    md = NB.note_markdown(src, manifest)
    import re as _re
    text = NB.FB.strip_title(md)
    return _re.sub(r"\n{3,}", "\n\n", text).strip() + "\n"


def parse_reader(text: str) -> dict:
    obj = FR._json_payload(text)
    if not isinstance(obj, dict) or not all(isinstance(obj.get(k), str) for k in ("q1", "q2")):
        raise ValueError("reader answer lacks q1 or q2")
    return {"q1": obj["q1"], "q2": obj["q2"]}


# ------------------------------------------------------------------------------------ runner

class Reader:
    def __init__(self, src: dict, run_dir: Path, consumer, model: str, log=print):
        self.src, self.rc = src, src["run"]
        self.run_dir = run_dir
        self.ck = FR.Checkpoint(run_dir / "checkpoint.jsonl")
        self.raw = run_dir / "raw"
        self.consumer, self.model = consumer, model
        self.log = log
        self.t0 = time.time()
        self.calls = 0

    def read(self, rnd: int) -> dict:
        text = reader_text(self.src)
        q = self.src["reader"]["questions"]
        prompt = READER_TEMPLATE.format(note=text, q1=q["q1"], q2=q["q2"])
        input_sha = FR.sha(text)
        uid = FR.unit_id("read", rnd, input_sha, self.model, READER_SHA)
        prior = [r for r in self.ck.read() if r["unit_id"] == uid]
        done = next((r for r in prior if r["status"] == "done"), None)
        if done:
            return {"round": rnd, "unit_id": uid, "model_id": self.model,
                    "note_sha256": input_sha, "answers": done["parsed"]}
        attempt = max((r["attempt"] for r in prior), default=0)
        rec = None
        while attempt < self.rc["max_attempts"]:
            attempt += 1
            if time.time() - self.t0 > self.rc["max_wall_seconds"]:
                raise FR.StopRun(f"wall_clock: {self.rc['max_wall_seconds']} s")
            base = {"unit_id": uid, "kind": "read", "question_id": rnd, "attempt": attempt,
                    "model_id": self.model, "role": self.rc["reader_role"], "input_sha256": input_sha,
                    "template_sha256": READER_SHA, "prompt_sha256": FR.sha(prompt),
                    "run_id": self.rc["run_id"]}
            t = time.time()
            comp, err = FR.call(self.consumer, self.model, prompt, f"usafacts_note.{uid}.read.r{rnd}.a{attempt}")
            self.calls += 1
            if comp is None:
                self.ck.append({**base, "status": "error", "error": err, "tokens": 0, "usage": {}, "ts": FR._now()})
                continue
            self.raw.mkdir(parents=True, exist_ok=True)
            (self.raw / f"{uid}.a{attempt}.json").write_text(json.dumps(
                {**base, "model_receipt": getattr(comp, "receipt", None), "prompt": prompt,
                 "response_text": comp.text, "usage": comp.usage}, indent=1, ensure_ascii=False),
                encoding="utf-8")
            try:
                parsed, status, error = parse_reader(comp.text), "done", None
            except (ValueError, KeyError, TypeError) as exc:
                parsed, status, error = None, "unparsed", str(exc)[:300]
            rec = {**base, "status": status, "error": error, "parsed": parsed, "usage": comp.usage,
                   "tokens": FR._tokens(comp.usage), "wall_s": round(time.time() - t, 2), "ts": FR._now()}
            self.ck.append(rec)
            self.log(f"[note +{time.time() - self.t0:6.1f}s] read r{rnd} {status} "
                     f"tokens {FR._tokens(comp.usage):,} calls {self.calls}")
            if status == "done":
                return {"round": rnd, "unit_id": uid, "model_id": self.model,
                        "note_sha256": input_sha, "answers": parsed}
        raise FR.StopRun(f"read r{rnd} not done in {self.rc['max_attempts']} attempts: {rec and rec.get('error')}")


# ----------------------------------------------------------------------------------- wiring

class ScriptedReader:
    """Test double for the SIGKILL resume test (§15 item 8), selected by
    `USAFACTS_NOTE_SCRIPTED_CONSUMER=<json spec>`: answers the two questions from fixed text and
    appends its call id to `calls_log` BEFORE answering. Never selected in production."""

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
        text = json.dumps({"q1": "Yes; the reader learns the four kept qualities, the three added, "
                                 "what became measurable, and that accuracy did not.",
                           "q2": "SI is defined; the rest are plain terms."})
        return Completion(text=text, model_id=self.model_id, usage={"inputTokens": 1, "outputTokens": 1})


def consumer(src: dict, scripted: str | None):
    rc = src["run"]
    if scripted:
        c = ScriptedReader(scripted)
        return c, c.model_id
    from kg import spend
    from kg.extraction import model_stub
    from harness.consumers import ClaudeCLIConsumer, ConsumerConfig
    model_stub.guard_no_api_key()
    cfg = ConsumerConfig(role=rc["reader_role"], provider=FR.PROVIDER,
                         timeout_seconds=rc["timeout_seconds"], call_class=rc["call_class"])
    led = spend.default_ledger()
    st = led.status().get("runs", {}).get(rc["run_id"])
    if st is None or int(st.get("ceiling_tokens") or 0) != rc["ceiling_tokens"]:
        led.declare(rc["run_id"], rc["ceiling_tokens"], declared_by=f"{GENERATOR} ({TASK})",
                    call_class=rc["call_class"], **({"supersede": True} if st else {}))
    spend.set_current_run(rc["run_id"])
    return ClaudeCLIConsumer(cfg), cfg.model_id


def merge_verify(run_dir: Path, patch: dict) -> dict:
    run_dir.mkdir(parents=True, exist_ok=True)
    p = run_dir / VERIFY
    cur = json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {"generated_by": GENERATOR, "task": TASK}
    cur.update(patch)
    cur["updated_at"] = FR._now()
    p.write_text(json.dumps(cur, indent=1, ensure_ascii=False, default=list) + "\n", encoding="utf-8")
    return cur


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--read", type=int, metavar="ROUND")
    ap.add_argument("--run-dir", default=None, help="test seam (default: reports/summary/run_usafacts_note)")
    ap.add_argument("--source", default=None)
    ap.add_argument("--progress-log", default=None)
    a = ap.parse_args(argv)
    src = load_source(Path(a.source) if a.source else SOURCE)
    run_dir = Path(a.run_dir) if a.run_dir else RUN_DIR
    plog = Path(a.progress_log) if a.progress_log else PROGRESS_LOG
    plog.parent.mkdir(parents=True, exist_ok=True)

    def log(msg: str) -> None:
        print(msg, flush=True)
        with plog.open("a", encoding="utf-8") as fh:
            fh.write(f"{FR._now()} {msg}\n")

    if a.dry_run:
        text = reader_text(src)
        print(f"note chars: {len(text)}; reader_role: {src['run']['reader_role']}; "
              f"ceiling_tokens: {src['run']['ceiling_tokens']}")
        print("--- reader text ---")
        print(text)
        return 0

    cons, model = consumer(src, os.environ.get("USAFACTS_NOTE_SCRIPTED_CONSUMER"))
    reader = Reader(src, run_dir, cons, model, log)
    try:
        rd = reader.read(a.read)
        cur = merge_verify(run_dir, {})
        reads = [r for r in cur.get("reads", []) if r["round"] != a.read] + [rd]
        merge_verify(run_dir, {"reads": sorted(reads, key=lambda r: r["round"]), "model_id": model})
        log(f"READ round {a.read}: " + json.dumps(rd["answers"], ensure_ascii=False)[:600])
        return 0
    except FR.StopRun as exc:
        merge_verify(run_dir, {"stopped": str(exc)})
        log(f"STOP: {exc}")
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
