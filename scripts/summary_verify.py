#!/usr/bin/env python3
"""The executive summary's checks and its reader. **Model spend, bounded.**

`cc_tasks/2026-10-12_executive_summary_from_brief_v2.md` step 4. The summary's prose is written
by the author (Opus 4.8); this script runs the two checks the concise report's pipeline runs, as
checks and not as content, and Fable's reading.

* `--check`: one call to the checker (a model of a third family from the author and the reader,
  role `critic`). It sees every sentence of pages 1 and 2 that states a measured result, with
  the three planted controls interleaved (methodology 7.6), the claims each cites, and the NAMES
  table, and labels each `supported` (with claim ids), `unsupported` or `no_factual_content`.
  The run FAILS, and no verdict is trusted, unless every planted control is caught as
  `unsupported`. A real sentence the checker does not support, or whose number is not a value of
  a claim it cites (the digit check, by code), is reported for the author to fix, never reworded
  by a model. Every reader-facing number of pages 1 and 2 is digit-checked, including sentences
  with no marker (which must then carry no number).
* `--read N`: one reading round. Fable (role `judge`) reads pages 1 and 2 alone, in a fresh
  context, and answers the four questions in the source (DN-014 §4). Editorial review, not a
  measurement. If the harness refuses the reader call (`judge_uncalibrated` or any other named
  refusal) the run stops and reports; the read is NOT routed through another role.

**Checkpoint** (`~/GitHub/CLAUDE.md` §15, the machinery of `scripts/dcat_faq_run.py`, imported):
unit = one call; key = sha1(kind | round | input sha | model | template sha), so a revised draft,
prompt or model is a new unit and a stale verdict is never reused. Every attempt is appended and
fsynced to `run/checkpoint.jsonl` before the next is awaited, the raw prompt and response beside
it in `run/raw/`. Re-running is the resume. The check call is the pilot: its measured tokens
project the reader rounds against the ceiling before the first read. Ceilings: the shared spend
ledger's (`run.ceiling_tokens`, reserved before each dispatch) and `run.max_wall_seconds`.

    /opt/anaconda3/bin/python3 scripts/summary_verify.py --dry-run
    /opt/anaconda3/bin/python3 scripts/summary_verify.py --check
    /opt/anaconda3/bin/python3 scripts/summary_verify.py --read 1
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

import concise_report_gate as G  # noqa: E402
import dcat_faq_run as FR  # noqa: E402
import summary_build as SB  # noqa: E402

GENERATOR = "scripts/summary_verify.py"
TASK = "cc_tasks/2026-10-12_executive_summary_from_brief_v2.md"
OUT = REPO / "reports" / "summary"
SOURCE = OUT / "summary_source.yaml"
RUN_DIR = OUT / "run"
VERIFY = "verify.json"
PROGRESS_LOG = REPO / "logs" / "2026-10-12_executive_summary_progress.log"
LABELS = ("supported", "unsupported", "no_factual_content")

CHECK_TEMPLATE = """TASK: CHECK EACH SENTENCE AGAINST THE CLAIMS

You are an adversarial fact checker for a short executive summary. Your job is to find every sentence below that says something the CLAIMS do not support. Do not pass a sentence to be agreeable and do not fail one to look diligent. A sentence may read as confident or well written; that is evidence about its writer, not about the claims.

Label every sentence with exactly one of:
- "supported": every factual part of the sentence (each number, each name, each count, each comparison, each "most", "all", "only", "none") is stated by one or more of the claims, or follows from them directly with no new number. Give the ids of the claims that together support it.
- "unsupported": any factual part is not stated by the claims, contradicts them, changes a number, drops a qualification a claim carries ("at most", "a bound", "notional", "not established", "candidate"), or states a number no claim states. Say which part, in the reason.
- "no_factual_content": the sentence states nothing that could be true or false about the world: a transition, a statement of what the summary does, a definition of a word it uses.

The NAMES table maps a code in a claim to the name a sentence uses; a sentence that uses the name is read as if it used the code. A sentence that names a statistical body is checked against the claims for that body.

The GLOSSARY below gives the summary's plain words for the claims' own terms, which it may not use. Treat a glossary pair as equal: a surface difference is not an overstatement. Judge only the substance: numbers, quantifiers ("all", "every", "only", "most", "none"), scope, cause, and comparison. A sentence that keeps the claim's number and quantifier but says it in the glossary's plain words is "supported".

Return ONLY a JSON array, one object per sentence, in order, with no prose before or after it and no code fence:
[{{"sentence_id": "S1", "label": "supported", "claim_ids": ["CL-035"], "reason": "one short sentence"}}]

GLOSSARY (plain word = the claims' term; equal)
- "this measurement" or "this round" = the measurement cycle the claims name.
- "a federal statistical agency", "an agency", or "a body" = a statistical body the claims count; "all 16 federal statistical agencies" = the 16 statistical bodies on the cycle.
- "a check" = a finding.
- "met an access denial" or "was refused" = an access denial (an HTTP 401, 403 or 429, a robots.txt disallow, or a reset connection).
- "the data page" = the product page.
- "an object" or "a resource" = an API, the API's terms, a changelog (a change history), or an inventory.
- "an agency-and-object pair" or "a pair" = a body-and-object pair.
- "a machine that starts at the data page cannot reach it" = no product page of the body reaches it.
- "a published row" = a judged row on the published matrices.

NAMES
{names}

CLAIMS
{claims}

SENTENCES
{sentences}"""

READER_TEMPLATE = """TASK: READ AND ANSWER

Below is a two-page executive summary. Read it, and answer the questions using only what it says. Do not use anything you know from elsewhere.

1. {q1}
2. {q2}
3. {q3}
4. {q4}

Return ONLY a JSON object, with no prose before or after it and no code fence:
{{"q1": "...", "q2": "...", "q3": "...", "q4": "..."}}

SUMMARY
{report}"""

CHECK_SHA = FR.sha(CHECK_TEMPLATE)
READER_SHA = FR.sha(READER_TEMPLATE)


# --------------------------------------------------------------------------------- inputs

def load_source(path: Path = SOURCE) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_claims(src: dict) -> dict:
    doc = yaml.safe_load((REPO / src["inputs"]["claims"]).read_text(encoding="utf-8"))
    return {c["id"]: c for c in doc["claims"]}


def load_names(src: dict) -> dict:
    """code -> plain name: body codes from the scan frame, indicator codes from the record."""
    names = {}
    t = json.loads((REPO / src["inputs"]["body_names"]).read_text(encoding="utf-8"))
    for h in t.get("hosts", []):
        if h.get("agency") and h.get("agency_name"):
            names[h["agency"]] = h["agency_name"]
    rec = json.loads((REPO / src["inputs"]["framework_record"]).read_text(encoding="utf-8"))
    for n in rec["nodes"]:
        if "AssessmentIndicator" in n["labels"]:
            p = n["properties"]
            names[p["code"]] = f"the check for {p.get('construct', p['code']).lower()}"
    return names


def factual_sentences(src: dict) -> list[str]:
    """Every reader-facing sentence of pages 1 and 2 that carries a claim marker, in order: the
    page-1 result sentences, the page-2 intro, and the `found` cell of each table row."""
    out = []
    for b in src["page1"]:
        for s in b.get("para", []):
            if G.marker_ids(s):
                out.append(s)
    p2 = src["page2"]
    for s in p2.get("intro", []):
        if G.marker_ids(s):
            out.append(s)
    for r in p2["table"]["rows"]:
        if G.marker_ids(r["found"]):
            out.append(r["found"])
    return out


def all_body_sentences(src: dict) -> list[str]:
    """Every reader-facing sentence of pages 1 and 2 (for the digit sweep over markerless ones)."""
    out = []
    for b in src["page1"]:
        out += b.get("para", [])
    p2 = src["page2"]
    out += p2.get("intro", [])
    for r in p2["table"]["rows"]:
        out.append(r["found"])
    return out


def claim_block(ids: list, claims: dict) -> str:
    out = []
    for i in ids:
        c = claims[i]
        lines = [f"[{i}] ({c['status']}) {' '.join(c['text'].split())}"]
        if c.get("note"):
            lines.append(f"    note: {' '.join(str(c['note']).split())}")
        out.append("\n".join(lines))
    return "\n\n".join(out)


def names_block(text: str, names: dict) -> str:
    import re
    used = [k for k in names if re.search(rf"(?<![\w-]){re.escape(k)}(?![\w-])", text)]
    return "\n".join(f"{k}: {names[k]}" for k in sorted(used)) or "(none)"


# ------------------------------------------------------------------------------------ parse

def parse_labels(text: str, n: int) -> list:
    arr = FR._json_payload(text)
    if not isinstance(arr, list):
        raise ValueError("labels are not an array")
    by = {}
    for x in arr:
        sid = str(x.get("sentence_id", ""))
        lab = str(x.get("label", "")).strip().lower().replace(" ", "_")
        if lab not in LABELS:
            raise ValueError(f"label {lab!r} for {sid}")
        by[sid] = {"label": lab, "claim_ids": [str(i).upper() for i in x.get("claim_ids") or []],
                   "reason": str(x.get("reason") or "")}
    missing = [f"S{i}" for i in range(1, n + 1) if f"S{i}" not in by]
    if missing:
        raise ValueError(f"no label for {missing}")
    return [by[f"S{i}"] for i in range(1, n + 1)]


def parse_reader(text: str) -> dict:
    obj = FR._json_payload(text)
    if not isinstance(obj, dict) or not all(isinstance(obj.get(k), str) for k in ("q1", "q2", "q3", "q4")):
        raise ValueError("reader answer lacks q1, q2, q3 or q4")
    return {k: obj[k] for k in ("q1", "q2", "q3", "q4")}


# ----------------------------------------------------------------------- interleave controls

def interleaved(reals: list[str], controls: list[dict]) -> tuple[list[str], list[int]]:
    """The sentences the checker sees: the reals with the controls spread evenly through them, so
    no control is predictably first or last. Returns the combined list and the final 0-based
    positions of the controls (ascending, so inserting left to right keeps each one's index)."""
    combined, positions = list(reals), []
    n, k = len(reals), len(controls)
    for i, c in enumerate(controls):
        pos = min(((i + 1) * n) // (k + 1) + i, len(combined))
        combined.insert(pos, c["text"])
        positions.append(pos)
    return combined, positions


# ------------------------------------------------------------------------------------ runner

class Runner:
    def __init__(self, src: dict, claims: dict, names: dict, run_dir: Path,
                 consumers: dict, models: dict, log=print):
        self.src, self.rc = src, src["run"]
        self.claims, self.names = claims, names
        self.run_dir = run_dir
        self.ck = FR.Checkpoint(run_dir / "checkpoint.jsonl")
        self.raw = run_dir / "raw"
        self.cons, self.models = consumers, models
        self.log = log
        self.t0 = time.time()
        self.calls = 0

    def unit(self, kind: str, rnd: int, input_sha: str, prompt: str, role: str, tsha: str, parse) -> dict:
        model = self.models[role]
        uid = FR.unit_id(kind, rnd, input_sha, model, tsha)
        prior = [r for r in self.ck.read() if r["unit_id"] == uid]
        done = next((r for r in prior if r["status"] == "done"), None)
        if done:
            return done
        attempt = max((r["attempt"] for r in prior), default=0)
        cap = self.rc["max_attempts"]
        rec = max(prior, key=lambda r: r["attempt"]) if prior else None
        while attempt < cap:
            attempt += 1
            if time.time() - self.t0 > self.rc["max_wall_seconds"]:
                raise FR.StopRun(f"wall_clock: {self.rc['max_wall_seconds']} s")
            base = {"unit_id": uid, "kind": kind, "question_id": rnd, "attempt": attempt,
                    "model_id": model, "role": role, "input_sha256": input_sha,
                    "template_sha256": tsha, "prompt_sha256": FR.sha(prompt), "run_id": self.rc["run_id"]}
            t = time.time()
            comp, err = FR.call(self.cons[role], model, prompt, f"summary.{uid}.{kind}.r{rnd}.a{attempt}")
            self.calls += 1
            if comp is None:
                rec = {**base, "status": "error", "error": err, "tokens": 0, "usage": {}, "ts": FR._now()}
                self.ck.append(rec)
                continue
            self.raw.mkdir(parents=True, exist_ok=True)
            (self.raw / f"{uid}.a{attempt}.json").write_text(json.dumps(
                {**base, "model_receipt": getattr(comp, "receipt", None), "prompt": prompt,
                 "response_text": comp.text, "usage": comp.usage}, indent=1, ensure_ascii=False),
                encoding="utf-8")
            try:
                parsed, status, error = parse(comp.text), "done", None
            except (ValueError, KeyError, TypeError) as exc:
                parsed, status, error = None, "unparsed", str(exc)[:300]
            rec = {**base, "status": status, "error": error, "parsed": parsed, "usage": comp.usage,
                   "tokens": FR._tokens(comp.usage), "wall_s": round(time.time() - t, 2), "ts": FR._now()}
            self.ck.append(rec)
            self.log(f"[summary +{time.time() - self.t0:6.1f}s] {kind} r{rnd} {status} "
                     f"tokens {FR._tokens(comp.usage):,} calls {self.calls}")
            if status == "done":
                return rec
        if rec is None or rec["status"] != "done":
            raise FR.StopRun(f"unit {kind} r{rnd} not done in {cap} attempts: {rec and rec.get('error')}")
        return rec

    # -- the checks
    def check(self) -> dict:
        reals = factual_sentences(self.src)
        controls = self.src["controls"]
        combined, positions = interleaved(reals, controls)
        stripped = [G.strip_markers(s) for s in combined]
        lines = "\n".join(f"S{i}: {t}" for i, t in enumerate(stripped, 1))
        cited = []
        for s in combined:
            cited += G.marker_ids(s)
        for c in controls:
            cited += [i.upper() for i in c.get("cites", [])]
        cited = list(dict.fromkeys(cited))
        prompt = CHECK_TEMPLATE.format(names=names_block(" ".join(stripped), self.names),
                                       claims=claim_block(cited, self.claims), sentences=lines)
        rec = self.unit("check", 0, FR.sha(lines), prompt, "checker", CHECK_SHA,
                        lambda t: parse_labels(t, len(combined)))
        labels = rec["parsed"]
        control_rows, real_rows = [], []
        control_at = set(positions)
        ci = 0
        for idx, (sent, lab) in enumerate(zip(combined, labels)):
            if idx in control_at:
                c = controls[ci]
                ci += 1
                control_rows.append({"text": sent, "expect": c["expect"], "label": lab["label"],
                                     "caught": lab["label"] == "unsupported", "reason": lab["reason"]})
            else:
                dc = G.digit_check(sent, {k: self.claims[k] for k in G.marker_ids(sent) if k in self.claims})
                ok = lab["label"] == "supported" and bool(lab["claim_ids"]) and dc["ok"]
                real_rows.append({"text": G.strip_markers(sent), "marker_ids": G.marker_ids(sent),
                                  "label": lab["label"], "claim_ids": lab["claim_ids"],
                                  "reason": lab["reason"], "digit_check": dc, "supported": ok})
        # the digit sweep over every reader-facing sentence, markered or not
        stray = []
        for s in all_body_sentences(self.src):
            dc = G.digit_check(s, {k: self.claims[k] for k in G.marker_ids(s) if k in self.claims})
            if not dc["ok"]:
                stray.append({"text": G.strip_markers(s), "missing": dc["missing"], "unknown_ids": dc["unknown_ids"]})
        return {"control_unit": rec["unit_id"], "tokens": rec["tokens"],
                "controls_caught": all(r["caught"] for r in control_rows),
                "controls": control_rows,
                "unsupported_check_passed": all(r["supported"] for r in real_rows) and not stray,
                "reals": real_rows, "stray_digits": stray}

    def pilot(self, check_tokens: int) -> None:
        rounds = 3
        proj = check_tokens * (1 + rounds)
        self.log(f"PILOT: the check call measured {check_tokens:,} tokens; projected for up to "
                 f"{rounds} reader rounds: {proj:,}, ceiling {self.rc['ceiling_tokens']:,}")
        if proj > self.rc["ceiling_tokens"]:
            raise FR.StopRun(f"pilot projects {proj:,} tokens past the ceiling {self.rc['ceiling_tokens']:,}")

    def read(self, rnd: int) -> dict:
        body = SB.body_markdown(self.src)
        # The reader sees clean prose with the page boundary marked in words, not the build
        # directive: the typst page break renders in the PDF, but Fable must see where page 1 ends
        # (without it, a reader guesses the split and misjudges what is on page 1).
        reader_text = SB.FB.strip_title(body).replace(
            SB.PAGEBREAK, "\n\n----- PAGE 2 (everything above is page 1) -----\n")
        import re as _re
        reader_text = _re.sub(r"\n{3,}", "\n\n", reader_text).strip() + "\n"
        q = self.src["reader"]["questions"]
        prompt = READER_TEMPLATE.format(report=reader_text, **q)
        rec = self.unit("read", rnd, FR.sha(reader_text), prompt, "reader", READER_SHA, parse_reader)
        return {"round": rnd, "unit_id": rec["unit_id"], "model_id": rec["model_id"],
                "body_sha256": FR.sha(reader_text), "answers": rec["parsed"]}


# ----------------------------------------------------------------------------------- wiring

class SummaryScriptedConsumer:
    """Test double for the SIGKILL resume test (§15 item 8), selected by
    `SUMMARY_SCRIPTED_CONSUMER=<json spec>`: a CHECK prompt labels every sentence `supported`
    except the lines it is told are controls (by their leading words), which it labels
    `unsupported`; a READ prompt answers the four questions from fixed text. Each call id is
    appended to `calls_log` BEFORE answering. Never selected in production."""

    def __init__(self, spec_path: str):
        spec = json.loads(Path(spec_path).read_text(encoding="utf-8"))
        self.sleep_s = float(spec.get("sleep_s", 0))
        self.calls_log = Path(spec["calls_log"])
        self.control_prefixes = spec.get("control_prefixes", [])
        self.model_id = spec.get("model_id", "scripted-model")

    def complete(self, prompt: str, *, call_id: str):
        import re
        from harness.consumers import Completion
        with self.calls_log.open("a", encoding="utf-8") as fh:
            fh.write(call_id + "\n")
            fh.flush()
            os.fsync(fh.fileno())
        time.sleep(self.sleep_s)
        if prompt.split("\n", 1)[0].startswith("TASK: CHECK"):
            sents = re.findall(r"^(S\d+): (.*)$", prompt.split("\nSENTENCES\n", 1)[1], re.M)
            cid = re.findall(r"CL-\d+", prompt.split("\nCLAIMS\n", 1)[1])[:1]
            arr = []
            for sid, text in sents:
                is_ctl = any(text.startswith(p) for p in self.control_prefixes)
                arr.append({"sentence_id": sid, "label": "unsupported" if is_ctl else "supported",
                            "claim_ids": [] if is_ctl else cid, "reason": "scripted"})
            text = json.dumps(arr)
        else:
            text = json.dumps({"q1": "yes to all four.", "q2": "nothing.", "q3": "nothing.", "q4": "nothing."})
        return Completion(text=text, model_id=self.model_id, usage={"inputTokens": 1, "outputTokens": 1})


def consumers(src: dict, scripted: str | None) -> tuple:
    rc = src["run"]
    if scripted:
        c = SummaryScriptedConsumer(scripted)
        return {"checker": c, "reader": c}, {"checker": c.model_id, "reader": c.model_id}
    from kg import spend
    from kg.extraction import model_stub
    from harness.consumers import ClaudeCLIConsumer, ConsumerConfig
    model_stub.guard_no_api_key()
    ck = ConsumerConfig(role=rc["checker_role"], provider=FR.PROVIDER,
                        timeout_seconds=rc["timeout_seconds"], call_class=rc["call_class"])
    rd = ConsumerConfig(role=rc["reader_role"], provider=FR.PROVIDER,
                        timeout_seconds=rc["timeout_seconds"], call_class=rc["call_class"])
    if ck.model_id == rd.model_id:
        raise SystemExit(f"FATAL: checker and reader must be different models; both are {ck.model_id}")
    led = spend.default_ledger()
    st = led.status().get("runs", {}).get(rc["run_id"])
    if st is None or int(st.get("ceiling_tokens") or 0) != rc["ceiling_tokens"]:
        led.declare(rc["run_id"], rc["ceiling_tokens"], declared_by=f"{GENERATOR} ({TASK})",
                    call_class=rc["call_class"], **({"supersede": True} if st else {}))
    spend.set_current_run(rc["run_id"])
    return ({"checker": ClaudeCLIConsumer(ck), "reader": ClaudeCLIConsumer(rd)},
            {"checker": ck.model_id, "reader": rd.model_id})


def merge_verify(run_dir: Path, patch: dict) -> dict:
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
    g.add_argument("--check", action="store_true")
    g.add_argument("--read", type=int, metavar="ROUND")
    ap.add_argument("--run-dir", default=None, help="test seam (default: reports/summary/run)")
    ap.add_argument("--source", default=None)
    ap.add_argument("--progress-log", default=None)
    a = ap.parse_args(argv)
    src = load_source(Path(a.source) if a.source else SOURCE)
    claims, names = load_claims(src), None
    run_dir = Path(a.run_dir) if a.run_dir else RUN_DIR
    plog = Path(a.progress_log) if a.progress_log else PROGRESS_LOG
    plog.parent.mkdir(parents=True, exist_ok=True)

    def log(msg: str) -> None:
        print(msg, flush=True)
        with plog.open("a", encoding="utf-8") as fh:
            fh.write(f"{FR._now()} {msg}\n")

    if a.dry_run:
        names = load_names(src)
        reals = factual_sentences(src)
        combined, positions = interleaved(reals, src["controls"])
        print(f"factual sentences: {len(reals)}; controls: {len(src['controls'])} at {positions}")
        for i, s in enumerate(combined, 1):
            print(f"  S{i}: {G.strip_markers(s)[:90]}")
        print(json.dumps({"checker_role": src["run"]["checker_role"], "reader_role": src["run"]["reader_role"],
                          "ceiling_tokens": src["run"]["ceiling_tokens"]}, indent=1))
        return 0

    names = load_names(src)
    cons, models = consumers(src, os.environ.get("SUMMARY_SCRIPTED_CONSUMER"))
    runner = Runner(src, claims, names, run_dir, cons, models, log)
    try:
        if a.check:
            res = runner.check()
            merge_verify(run_dir, {"check": res, "models": models})
            if not res["controls_caught"]:
                log("STOP: a planted control was not caught; no verdict is trusted")
                return 3
            runner.pilot(res["tokens"])
            log(f"CHECK: controls_caught={res['controls_caught']} "
                f"unsupported_check_passed={res['unsupported_check_passed']}")
            return 0 if res["unsupported_check_passed"] else 3
        if a.read is not None:
            rd = runner.read(a.read)
            cur = merge_verify(run_dir, {})
            reads = cur.get("reads", [])
            reads = [r for r in reads if r["round"] != a.read] + [rd]
            merge_verify(run_dir, {"reads": sorted(reads, key=lambda r: r["round"]), "models": models})
            log(f"READ round {a.read}: " + json.dumps(rd["answers"], ensure_ascii=False)[:400])
            return 0
    except FR.StopRun as exc:
        merge_verify(run_dir, {"stopped": str(exc)})
        log(f"STOP: {exc}")
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
