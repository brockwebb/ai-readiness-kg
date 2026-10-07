#!/usr/bin/env python3
"""DCAT-005: the brief's corrections before it goes to OMB. **Model spend, bounded.**

`cc_tasks/2026-10-07_DCAT-005_brief_corrections_before_omb.md`, implementing DN-011 ADDENDUM 01
R6 and R7 as written and DN-012 d1 (no absence verdict over a partial search). DCAT-004 v2's
record (`reports/dcat_us_3_brief/answers.json`) is read and never rewritten; what this task adds
is an overlay, `reports/dcat_us_3_brief/run/corrections.json`, that the build applies on top of
it, the way a correcting event is appended rather than an event edited. Phases:

* **controls**: both positive controls of `dcat_brief_run.BriefRunner`, re-run fresh under this
  task's epoch (a new unit key, so no verdict paid for by DCAT-004 is reused as this task's
  control). No verdict below is used unless both pass. They are also the pilot (§15 item 4):
  their measured tokens project the remaining calls against the run's ceiling.
* **full_read** (decision 1): for each of needs 1, 6 and 8, every passage of the eight asked
  documents that matches the need's `asked` terms, uncapped
  (`dcat_faq_evidence.full_read_evidence`), read in batches of the asked part's per-call
  budget by two independent readers from different model families. A passage either reader
  returns as an ask is a candidate; every candidate goes to the validator panel (instrument r3)
  as a sentence carrying its classification. A need is `asked` when the panel keeps one, else
  `not_found_in_full_read`: every matched passage read by both readers, none asks.
* **published** (decision 4): every validated landed sentence (other than a `dropped` one,
  which is a draft-versus-final statement by definition) and every validated literature
  sentence that says what 3.0 carries (`matches`, `carries_3_0_does_not`) that cites the 2025
  working draft is checked again by the panel with the draft passages removed from its
  citations and from the passages shown. Kept: it stands on the published pages. Cut: that
  part is no longer validated for that round. Need 4, whose landed part neither DCAT-004 round
  validated, is answered once more over its evidence without the draft's prose
  (`need_4_published.json`), so its row is re-placed from the published pages.
* **reader**: the fresh reader, once, on the rebuilt BRIEF.md, graded by the key the amendment
  block of `brief_config.yaml` fixed before it ran.
* **assemble**: no call. Rows by `dcat_brief_run.row_from_need` with the overlay applied, R7 as
  written (`dcat_brief_run.verdict`), into the overlay file.

**Prior art.** Two independent readers with the union of their inclusions is dual independent
screening, the systematic-review standard for not missing a relevant record (Cochrane Handbook
for Systematic Reviews of Interventions, v6.4, ch. 4.6.4; single screening misses a median of
5 to 13 percent of relevant records, Waffenschmidt et al. 2019, BMC Medical Research Methodology
19:132). Inclusive first-pass reading with every inclusion verified afterwards is the same
literature's two-stage screen. Batching by a fixed per-call budget rather than one long context
follows "Lost in the Middle" (Liu et al. 2024, TACL 12): recall of a fact falls with its depth in
a long context. The panel and keep-or-cut rule are `dcat_brief_run`'s (Verga et al. 2024).

**Checkpoint** (`~/GitHub/CLAUDE.md` §15): `dcat_faq_run.Runner._unit`, unchanged: one call per
unit, key sha1(kind | need | input hash | model | template hash), appended and fsynced to
`reports/dcat_us_3_brief/run/checkpoint.jsonl` before the next result is awaited, raws beside
it, resume by re-running the same phase. Ceilings: the amendment's `run.ceiling_tokens` on the
shared ledger (reserve before dispatch) and `run.max_wall_seconds`.

    /opt/anaconda3/bin/python3 scripts/dcat_brief_correct.py --phase controls
    /opt/anaconda3/bin/python3 scripts/dcat_brief_correct.py --phase full_read
    /opt/anaconda3/bin/python3 scripts/dcat_brief_correct.py --phase published
    /opt/anaconda3/bin/python3 scripts/dcat_brief_correct.py --phase assemble     # no call
    /opt/anaconda3/bin/python3 scripts/dcat_brief_correct.py --phase reader
"""
from __future__ import annotations

import argparse
import copy
import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
for _p in ("", "scripts", "assessment"):
    if str(REPO / _p) not in sys.path:
        sys.path.insert(0, str(REPO / _p))

import yaml  # noqa: E402

import dcat_brief_run as BR  # noqa: E402
import dcat_faq_evidence as EV  # noqa: E402
import dcat_faq_run as FR  # noqa: E402

TASK = "cc_tasks/2026-10-07_DCAT-005_brief_corrections_before_omb.md"
GENERATOR = "scripts/dcat_brief_correct.py"
AMEND = "amendment_2026_10_07_dcat005"
OUT = EV.BRIEF_OUT
RUN_DIR = OUT / "run"
CORRECTIONS = RUN_DIR / "corrections.json"
CONTROL_OUT = RUN_DIR / "controls_dcat005.json"
PROGRESS_LOG = REPO / "logs" / "2026-10-07_DCAT-005_progress.log"
#: Unit-id question numbers for this task's units, clear of DCAT-004's (needs 1-8, 90, 100+,
#: 200+): a full-read unit is 300 + need, a candidate check 310 + need, a published re-check
#: 320 + need, the fresh reader 330.
READ_QID0, ASK_QID0, PUB_QID0, READER_QID = 300, 310, 320, 330

READ_TEMPLATE = """You are reading part of the public record of the federal statistical side, to find out whether it asks for one statistical need. The record is: the Federal Committee on Statistical Methodology (FCSM) papers, the FAIRness Project's wiki and conference slides (a project of the federal Chief Data Officers Council with FCSM), and the Chief Data Officers Council's data sharing report. Read every one of the {n} numbered passages below.

THE NEED: {name}: {plain}.

A passage ASKS for the need when it shows FCSM, the FAIRness Project or the Chief Data Officers Council recommending, calling for, requiring or proposing this need: for metadata, for catalogs, or for what is reported to data users. A passage does not ask when it uses the same word for a different thing (a "dimension" of data quality is not a statistical dimension; a software "version" is not a data revision; access to a system or a building is not a condition on using a dataset).

RULES
1. Use ONLY the passages below.
2. When in doubt, include the passage. Every passage you return is checked afterwards against its text; a passage you leave out is never looked at again.
3. For each passage that asks, return its id; a quote of at most 40 words copied exactly, character for character, from that passage, carrying the ask; and one plain sentence of at most {max_words} words that names the document and says what it asks for. Do not mention passage ids in the sentence. Do not use the em dash character.
4. If no passage asks, return an empty list.

Return ONLY a JSON object, with no prose before or after it and no code fence:
{{"asks": [{{"id": "E1", "quote": "...", "sentence": "..."}}]}}

PASSAGES
{passages}
"""
READ_TEMPLATE_SHA = FR.sha(READ_TEMPLATE)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_cfg() -> dict:
    """The brief's config with this task's amendment block applied over the keys it names."""
    bcfg = yaml.safe_load(EV.BRIEF_CONFIG.read_text(encoding="utf-8"))
    am = bcfg.get(AMEND)
    if not am:
        raise SystemExit(f"FATAL: brief_config.yaml has no {AMEND} block; it is written before any call")
    return bcfg


def run_cfg(bcfg: dict) -> dict:
    return {**bcfg["run"], **bcfg[AMEND]["run"]}


def write_json(p: Path, obj) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, p)


def load_corrections() -> dict:
    return json.loads(CORRECTIONS.read_text(encoding="utf-8")) if CORRECTIONS.is_file() else {}


def sub_evidence(ev: dict, ids: list) -> dict:
    """The passages `ids` of `ev`, in their order, as an evidence dict the check prompt reads."""
    keep = set(ids)
    items = [it for it in ev["items"] if it["id"] in keep]
    out = {"question_id": ev["question_id"], "question": ev["question"],
           "documents": {d: m for d, m in ev["documents"].items() if any(it["doc_id"] == d for it in items)},
           "items": items}
    out["evidence_sha256"] = EV.evidence_sha(out)
    return out


# ------------------------------------------------------------------------------- parsing

def parse_read(text: str, ev: dict, batch: list) -> dict:
    """A reader's answer for one batch. An ask must name a passage of the batch and quote it
    verbatim (`kg.extraction.grounding.is_grounded`); a quote the passage does not hold is a
    malformed answer and the unit is retried, never trusted."""
    from kg.extraction.grounding import is_grounded
    obj = FR._json_payload(text)
    if not isinstance(obj, dict) or not isinstance(obj.get("asks"), list):
        raise ValueError("reader answer is not {asks: [...]}")
    by = {it["id"]: it for it in ev["items"] if it["id"] in set(batch)}
    asks = []
    for a in obj["asks"]:
        if not isinstance(a, dict):
            raise ValueError("an ask is not an object")
        pid, quote, sent = str(a.get("id") or ""), str(a.get("quote") or ""), str(a.get("sentence") or "").strip()
        if pid not in by:
            raise ValueError(f"ask names {pid!r}, which is not a passage of this batch")
        if not is_grounded(quote, by[pid]["text"]):
            raise ValueError(f"ask {pid}: its quote is not in the passage")
        if not sent:
            raise ValueError(f"ask {pid}: no sentence")
        asks.append({"id": pid, "quote": quote, "sentence": sent})
    return {"asks": asks}


def ask_classification(need: dict) -> str:
    return BR.classification("asked", {"asked": {"code": "asked"}}, need)


# ---------------------------------------------------------------------------- the runner

class CorrectRunner(BR.BriefRunner):
    def max_attempts(self, qid: int) -> int:
        return 1 if qid in (FR.CONTROL_QID, BR.BRIEF_CONTROL_QID) else int(self.rc["max_attempts"])

    def progress(self, force: bool = False) -> None:
        """§15 item 3, over this task's run only (the checkpoint file also holds DCAT-004's)."""
        now = time.time()
        if not force and now - self.last_progress < self.rc["progress_every_seconds"]:
            return
        self.last_progress = now
        recs = [r for r in self.ck.read() if r.get("run_id") == self.rc["run_id"]]
        tok = sum(r.get("tokens", 0) for r in recs)
        done = sum(1 for r in FR.decided(recs).values() if r["status"] == "done")
        fails = sum(1 for r in recs if r["status"] != "done")
        self.log(f"[dcat005 +{now - self.t0:7.1f}s] units done {done} calls this run {self.calls} "
                 f"tokens so far {tok:,} of ceiling {self.rc['ceiling_tokens']:,} failures so far {fails}")

    # -- controls, fresh under this task's epoch
    def epoch(self) -> str:
        return str(self.bcfg[AMEND]["run"]["control_epoch"])

    def faq_control(self) -> dict:
        cc = self.faq_cfg["rerun"]["control"]
        ev = BR.load_ev(REPO / cc["evidence"])
        return self.run_plants("control", FR.CONTROL_QID,
                               FR.sha(ev["evidence_sha256"] + json.dumps(cc, sort_keys=True) + self.epoch()),
                               ev, cc["sentences"])

    def brief_control(self) -> dict:
        """The brief's control on need 4's evidence. The plants are the amendment's erratum
        (`controls_plants`) when it carries one: the first run's S1 rested on the working draft
        and was replaced after it failed (see the erratum in `brief_config.yaml`)."""
        cc = self.bcfg["controls"]
        plants = self.bcfg[AMEND].get("controls_plants") or cc["plants"]
        ev = BR.load_ev(EV.BRIEF_EVIDENCE_DIR / f"need_{cc['need']}.json")
        return self.run_plants("control", BR.BRIEF_CONTROL_QID,
                               FR.sha(ev["evidence_sha256"] + json.dumps(plants, sort_keys=True) + self.epoch()),
                               ev, plants)

    def controls(self) -> int:
        global_out = BR.CONTROL_OUT
        BR.CONTROL_OUT = CONTROL_OUT
        try:
            return super().controls()
        finally:
            BR.CONTROL_OUT = global_out

    def controls_passed(self) -> bool:
        if not CONTROL_OUT.is_file():
            return False
        c = json.loads(CONTROL_OUT.read_text(encoding="utf-8"))
        return bool(c["faq_item5_control"]["passed"] and c["brief_control"]["passed"])

    # -- decision 1
    def read_unit(self, nid: int, ev: dict, k: int, batch: list, consumer, model: str) -> dict:
        need = BR.need_cfg(self.bcfg, nid)
        sub = sub_evidence(ev, batch)
        prompt = READ_TEMPLATE.format(n=len(batch), name=need["name"], plain=need["plain"],
                                      max_words=self.rc["max_words"], passages=FR.passage_block(sub))
        rec = self._unit("full_read", READ_QID0 + nid, sub["evidence_sha256"], prompt, consumer, model,
                         lambda t: parse_read(t, ev, batch), READ_TEMPLATE_SHA)
        return {"need": nid, "batch": k, "passages": len(batch), "model_id": model, "unit_id": rec["unit_id"],
                "status": rec["status"], "asks": (rec.get("parsed") or {}).get("asks"),
                "tokens": rec.get("tokens", 0)}

    def reader_control(self, ev: dict, readers: list) -> dict:
        """The readers' positive control (amendment `reader_control`): one planted ask in the
        middle of the need's first batch. Passed when every reader returns it."""
        rc = self.bcfg[AMEND]["reader_control"]
        plant = {**rc["plant"], "kind": "document text", "part": "asked", "locator": {"control": True}}
        batch = list(ev["batches"][0])
        batch.insert(len(batch) // 2, plant["id"])
        evc = {**ev, "items": ev["items"] + [plant]}
        rows = []
        for consumer, model in readers:
            r = self.read_unit(int(rc["need"]), evc, 0, batch, consumer, model)
            got = [a["id"] for a in r["asks"] or []]
            rows.append({**r, "found_plant": plant["id"] in got, "other_asks": [g for g in got if g != plant["id"]]})
        return {"need": rc["need"], "plant": plant["id"], "position": batch.index(plant["id"]) + 1,
                "batch_size": len(batch), "rows": rows,
                "passed": all(r["status"] == "done" and r["found_plant"] for r in rows)}

    def full_read(self, nid: int, ev: dict, readers: list) -> dict:
        """Every batch by every reader, then one panel check of the union of their asks."""
        units = [(k, b, c, m) for k, b in enumerate(ev["batches"], 1) for c, m in readers]
        with ThreadPoolExecutor(max_workers=self.rc["workers"]) as ex:
            reads = list(ex.map(lambda u: self.read_unit(nid, ev, *u), units))
        out = {"need_id": nid, "evidence_file": f"need_{nid}_full_read.json", "matched": ev["matched"],
               "read": ev["read"], "dropped_by_cap": ev["dropped_by_cap"], "batches": len(ev["batches"]),
               "readers": [m for _, m in readers], "reads": reads}
        bad = [r for r in reads if r["status"] != "done"]
        if bad:
            # A batch not read by a reader is a partial search; DN-012 d1 forbids an absence
            # verdict over it.
            out.update(status="incomplete", verdict=None,
                       reason=f"{len(bad)} reading unit(s) did not complete: "
                              + ", ".join(f"batch {r['batch']} by {r['model_id']}" for r in bad))
            return out
        need = BR.need_cfg(self.bcfg, nid)
        cands, seen = [], set()
        for r in reads:
            for a in r["asks"]:
                key = (a["id"], a["sentence"])
                if key not in seen:
                    seen.add(key)
                    cands.append({**a, "reader": r["model_id"]})
        out["candidates"] = cands
        if not cands:
            out.update(status="done", verdict="not_found_in_full_read", kept=[])
            return out
        items = [{"item_id": f"S{i}", "kind": "SENTENCE", "part": "asked", "sentence": c["sentence"],
                  "evidence": [c["id"]], "reader": c["reader"],
                  "text": f"{c['sentence']} [Classification this sentence must support: {ask_classification(need)}]"}
                 for i, c in enumerate(cands, 1)]
        sub = sub_evidence(ev, sorted({c["id"] for c in cands}, key=lambda x: int(x[1:])))
        cs = self.panel("full_read_check", ASK_QID0 + nid, FR.sha(sub["evidence_sha256"] + json.dumps(
            [it["text"] for it in items], ensure_ascii=False)), FR.check_prompt(sub, items, "v2"),
            lambda t: FR.parse_check(t, items, "v2"))
        if len(cs) < 2 or any(c["status"] != "done" for c in cs):
            out.update(status="unchecked", verdict=None, reason="the panel check of the candidates did not complete",
                       check_units=[c["unit_id"] for c in cs])
            return out
        d = BR.panel_decide(sub, {"precut": []}, items, [c["parsed"] for c in cs], [self.cm, self.rm])
        kept_text = {r["text"] for r in d["kept"]}
        rows = []
        for it in items:
            row = next((r for r in d["kept"] + d["cut"] if r["text"] == it["text"]), {})
            rows.append({**{k: it[k] for k in ("item_id", "kind", "part", "sentence", "evidence", "reader")},
                         "evidence_file": out["evidence_file"], "kept": it["text"] in kept_text,
                         "verdict": row.get("verdict"), "responsive": row.get("responsive"),
                         "support_span": row.get("support_span"), "reason": row.get("reason"),
                         "cut_reason": row.get("cut_reason"), "panel": row.get("panel")})
        out.update(status="done", check_units=[c["unit_id"] for c in cs], checked=rows,
                   kept=[r for r in rows if r["kept"]],
                   verdict="asked" if any(r["kept"] for r in rows) else "not_found_in_full_read")
        return out

    # -- decision 4
    def recheck(self, nid: int, task: dict, ev_pub: dict) -> dict:
        """One validated sentence that cited the 2025 working draft, checked again by the panel
        with the draft's passages removed from its citations and from the passages shown."""
        items = [{"item_id": "S1", "kind": "SENTENCE", "part": task["part"], "sentence": task["sentence"],
                  "evidence": task["evidence_published"], "text": task["text"]}]
        if not task["evidence_published"]:
            return {**task, "kept": False, "cut_reason": "cites only the 2025 working draft", "check_units": []}
        cs = self.panel("published_recheck", PUB_QID0 + nid,
                        FR.sha(ev_pub["evidence_sha256"] + task["text"] + json.dumps(task["evidence_published"])),
                        FR.check_prompt(ev_pub, items, "v2"), lambda t: FR.parse_check(t, items, "v2"))
        if len(cs) < 2 or any(c["status"] != "done" for c in cs):
            return {**task, "kept": None, "cut_reason": "the panel check did not complete",
                    "check_units": [c["unit_id"] for c in cs]}
        d = BR.panel_decide(ev_pub, {"precut": []}, items, [c["parsed"] for c in cs], [self.cm, self.rm])
        row = (d["kept"] or d["cut"])[0]
        return {**task, "kept": bool(d["kept"]), "verdict": row.get("verdict"), "responsive": row.get("responsive"),
                "support_span": row.get("support_span"), "reason": row.get("reason"),
                "cut_reason": row.get("cut_reason"), "panel": row.get("panel"),
                "check_units": [c["unit_id"] for c in cs]}

    def reader(self, rnd: int, brief_text: str) -> dict:
        fr = self.bcfg["fresh_reader"]["questions"]
        prompt = READER_TEMPLATE.format(q1=fr[0], q2=fr[1], q3=fr[2], brief=brief_text)

        def parse(t):
            o = FR._json_payload(t)
            if not isinstance(o, dict) or not all(k in o for k in ("q1", "q2", "q3")):
                raise ValueError("reader answer lacks q1, q2 or q3")
            return o
        return self._unit("reader", READER_QID + rnd, FR.sha(brief_text), prompt, self.rc_consumer, self.rm,
                          parse, FR.sha(READER_TEMPLATE))


#: The fresh reader's template, DCAT-004's with one change: R7 as written can leave an answer
#: undecided, so "not decided" is offered beside yes, no and partly. The grading key is fixed in
#: the amendment block before the reader runs.
READER_TEMPLATE = BR.READER_TEMPLATE.replace('"finding": "yes|no|partly", "fitness_for_use": "yes|no|partly"',
                                             '"finding": "yes|no|partly|not decided", '
                                             '"fitness_for_use": "yes|no|partly|not decided"')
assert READER_TEMPLATE != BR.READER_TEMPLATE, "the reader template failed to patch"


# ------------------------------------------------------------------------ decision 4 inputs

def published_evidence(ev: dict) -> dict:
    """A need's evidence without the 2025 working draft's own passages. Element-table rows stay:
    each states every version's level and is read for the page as served on 5 October 2026."""
    items = [it for it in ev["items"] if not (it["doc_id"] == EV.DRAFT and it["kind"] != "element table row")]
    out = {**{k: v for k, v in ev.items() if k not in ("items", "evidence_sha256", "generated_at", "generated_by")},
           "generated_by": f"{GENERATOR} (decision 4: the need's evidence without the 2025 working draft)",
           "generated_at": _now(), "derived_from": f"need_{ev['question_id']}.json",
           "removed": [it["id"] for it in ev["items"] if it not in items],
           "documents": {d: m for d, m in ev["documents"].items() if d != EV.DRAFT}, "items": items}
    out["evidence_sha256"] = EV.evidence_sha(out)
    return out


def draft_ids(ev: dict) -> set:
    return {it["id"] for it in ev["items"] if it["doc_id"] == EV.DRAFT and it["kind"] != "element table row"}


def recheck_tasks(nid: int, res: dict, ev: dict, need: dict) -> list:
    """Every validated sentence of a DCAT-004 round that states what published 3.0 carries and
    cites the draft: landed sentences other than `dropped`, and literature sentences coded
    `matches` or `carries_3_0_does_not`."""
    drafts = draft_ids(ev)
    out = []
    for k, r in enumerate(res["rounds"], 1):
        if r.get("status") != "done":
            continue
        ans = r["answer"]
        for part in ("landed", "literature"):
            if not r["parts_validated"][part]:
                continue
            if part == "landed" and ans["landed"]["code"] in ("dropped", "absent"):
                continue
            if part == "literature" and ans["literature"]["code"] not in ("matches", "carries_3_0_does_not"):
                continue
            it = next(x for x in r["items"] if x["part"] == part and x["kind"] == "SENTENCE")
            if not set(it["evidence"]) & drafts:
                continue
            out.append({"need_id": nid, "round": k, "part": part, "code": ans[part]["code"],
                        "sentence": it["sentence"], "evidence": it["evidence"],
                        "evidence_published": [e for e in it["evidence"] if e not in drafts],
                        "text": f"{it['sentence']} [Classification this sentence must support: "
                                f"{BR.classification(part, ans, need)}]"})
    return out


# ------------------------------------------------------------------------------ assemble

def assemble(answers: dict, corr: dict, bcfg: dict) -> dict:
    """Rows and R7 from DCAT-004's needs with this task's overlay applied (no call)."""
    levels = BR.element_levels()
    rows = {}
    for nid, res in answers["needs"].items():
        rows[int(nid)] = BR.row_from_need(res, levels, overlay_for(corr, int(nid)))
    corr["rows"] = {str(k): v for k, v in sorted(rows.items())}
    corr["verdict"] = BR.verdict(rows, bcfg)
    for rnd, rd in (corr.get("readers") or {}).items():
        if rd.get("answers"):
            rd["grade"] = BR.grade_reader(rd["answers"], corr["rows"], corr["verdict"], bcfg)
    return corr


def overlay_for(corr: dict, nid: int) -> dict:
    return {"full_read": (corr.get("full_read") or {}).get(str(nid)),
            "rechecks": [x for x in corr.get("rechecks") or [] if x["need_id"] == nid],
            "rounds_added": (corr.get("rounds_added") or {}).get(str(nid)) or []}


# ---------------------------------------------------------------------------------- main

class ScriptedCorrectConsumer(BR.ScriptedBriefConsumer):
    """Test double for the SIGKILL resume test (§15 item 8), selected by
    `DCATFAQ_SCRIPTED_CONSUMER` as DCAT-004's is. A reading prompt gets no ask, except the
    readers' control plant, which it returns; every other prompt is answered by DCAT-004's
    double. Never selected in production."""

    def complete(self, prompt: str, *, call_id: str):
        if "THE NEED:" not in prompt or "\nITEMS\n" in prompt:
            return super().complete(prompt, call_id=call_id)
        with self.calls_log.open("a", encoding="utf-8") as fh:
            fh.write(call_id + "\n")
            fh.flush()
            os.fsync(fh.fileno())
        time.sleep(self.sleep_s)
        from harness.consumers import Completion
        asks = []
        m = re.search(r"^\[(P\d+)\][^\n]*\n([^\n]{30})", prompt, re.M)
        if m:
            asks = [{"id": m.group(1), "quote": m.group(2), "sentence": "Scripted ask."}]
        return Completion(text=json.dumps({"asks": asks}), model_id=self.model_id,
                          usage={"inputTokens": 1, "outputTokens": 1})


def consumers(bcfg: dict, scripted: str | None):
    """The answer model, the panel's two judges, and the readers (amendment `full_read.readers`,
    keys of `kg/extraction/model_config.yaml`). The run is declared on the shared ledger under
    this task's run id and ceiling before any call."""
    am_cfg = bcfg[AMEND]
    if scripted:
        c, c2 = ScriptedCorrectConsumer(scripted), ScriptedCorrectConsumer(scripted)
        c2.model_id = c.model_id + "-second-reader"
        return c, c, c.model_id, c.model_id, c, c.model_id, [(c, c.model_id), (c2, c2.model_id)]
    from kg.extraction import model_stub
    from kg import spend
    from harness.consumers import ClaudeCLIConsumer, ConsumerConfig
    mc = model_stub.load_model_config()
    rc = run_cfg(bcfg)
    am, cm, rm = mc[rc["answer_model_key"]], mc[rc["validator_model_key"]], mc["secondary_judge_model_id"]
    model_stub.guard_no_api_key()
    led = spend.default_ledger()
    st = led.status().get("runs", {}).get(rc["run_id"])
    if st is None or int(st.get("ceiling_tokens") or 0) != rc["ceiling_tokens"]:
        led.declare(rc["run_id"], rc["ceiling_tokens"], declared_by=f"{GENERATOR} ({TASK})",
                    call_class=rc["call_class"], **({"supersede": True} if st else {}))
    spend.set_current_run(rc["run_id"])

    def mk(m):
        return ClaudeCLIConsumer(ConsumerConfig(model_id=m, provider=FR.PROVIDER, cli=FR.CLI,
                                                timeout_seconds=rc["timeout_seconds"], call_class=rc["call_class"]))
    cons = {m: mk(m) for m in {am, cm, rm} | {mc[k] for k in am_cfg["full_read"]["readers"]}}
    readers = [(cons[mc[k]], mc[k]) for k in am_cfg["full_read"]["readers"]]
    return cons[am], cons[cm], am, cm, cons[rm], rm, readers


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--phase", choices=("controls", "full_read", "published", "reader", "assemble"), required=True)
    # Test seams (the SIGKILL resume test): scratch run directory, evidence, answers and overlay.
    ap.add_argument("--run-dir", default=None)
    ap.add_argument("--evidence-dir", default=None)
    ap.add_argument("--answers", default=None)
    ap.add_argument("--progress-log", default=None)
    ap.add_argument("--no-graph", action="store_true")
    a = ap.parse_args(argv)
    global RUN_DIR, CORRECTIONS, CONTROL_OUT, PROGRESS_LOG
    answers_path = BR.ANSWERS
    if a.run_dir:
        RUN_DIR = Path(a.run_dir)
        CORRECTIONS, CONTROL_OUT = RUN_DIR / "corrections.json", RUN_DIR / "controls_dcat005.json"
    if a.evidence_dir:
        EV.BRIEF_EVIDENCE_DIR = Path(a.evidence_dir)
    if a.answers:
        answers_path = Path(a.answers)
    if a.progress_log:
        PROGRESS_LOG = Path(a.progress_log)
    bcfg = load_cfg()
    rc = run_cfg(bcfg)
    faq_cfg = EV.load_config()
    PROGRESS_LOG.parent.mkdir(parents=True, exist_ok=True)

    def log(msg: str) -> None:
        print(msg, flush=True)
        with PROGRESS_LOG.open("a", encoding="utf-8") as fh:
            fh.write(f"{_now()} {msg}\n")

    FR.RUN_ID = rc["run_id"]
    answers = json.loads(answers_path.read_text(encoding="utf-8"))
    scripted = os.environ.get("DCATFAQ_SCRIPTED_CONSUMER")
    if a.phase == "assemble":
        ac = cc = rcons = None
        from kg.extraction import model_stub
        mc = model_stub.load_model_config()
        am, cm, rm = mc[rc["answer_model_key"]], mc[rc["validator_model_key"]], mc["secondary_judge_model_id"]
        readers = []
    else:
        ac, cc, am, cm, rcons, rm, readers = consumers(bcfg, scripted)
    runner = CorrectRunner({**bcfg, "run": rc}, faq_cfg, ac, cc, am, cm, log, rcons, rm)
    runner.ck = FR.Checkpoint(RUN_DIR / "checkpoint.jsonl")
    runner.raw = RUN_DIR / "raw"
    corr = load_corrections()
    corr.update(generated_by=GENERATOR, task=TASK, base=answers_path.relative_to(REPO).as_posix()
                if answers_path.is_relative_to(REPO) else str(answers_path))
    rc_ = 0
    try:
        if a.phase == "controls":
            rc_ = runner.controls()
            recs = [r for r in runner.ck.read() if r.get("run_id") == rc["run_id"] and r["status"] == "done"]
            if recs:
                per = sum(r["tokens"] for r in recs) / len(recs)
                plan = bcfg[AMEND]["run"]["planned_calls"]
                log(f"PILOT: {len(recs)} control calls, {per:,.0f} tokens per call measured; "
                    f"{plan} planned calls project {per * plan:,.0f} tokens against the ceiling "
                    f"{rc['ceiling_tokens']:,}")
        elif not runner.controls_passed():
            raise SystemExit("FATAL: this task's positive controls have not both passed; no verdict may be used")
        elif a.phase == "full_read":
            rcn = bcfg[AMEND]["reader_control"]["need"]
            ctl = runner.reader_control(BR.load_ev(EV.BRIEF_EVIDENCE_DIR / f"need_{rcn}_full_read.json"), readers)
            corr["reader_control"] = ctl
            write_json(CORRECTIONS, corr)
            log(f"READER CONTROL: {'PASS' if ctl['passed'] else 'FAIL'} plant at {ctl['position']} of "
                f"{ctl['batch_size']}: " + json.dumps([(r['model_id'], r['found_plant']) for r in ctl["rows"]]))
            if not ctl["passed"]:
                raise SystemExit("FATAL: the readers' positive control failed; no full-read verdict may be used")
            fr = corr.get("full_read") or {}
            for nid in bcfg[AMEND]["full_read"]["needs"]:
                ev = BR.load_ev(EV.BRIEF_EVIDENCE_DIR / f"need_{nid}_full_read.json")
                fr[str(nid)] = runner.full_read(nid, ev, readers)
                corr["full_read"] = fr
                write_json(CORRECTIONS, corr)
                r = fr[str(nid)]
                log(f"FULL READ need {nid}: {r['read']} passages read in {r['batches']} batches by "
                    f"{len(readers)} readers; candidates {len(r.get('candidates') or [])}; verdict {r.get('verdict')} "
                    f"({r.get('status')})")
        elif a.phase == "published":
            drv = None if a.no_graph else EV.driver()
            try:
                if drv is not None:
                    meta = EV.doc_meta(drv, bcfg)
                    sd = REPO / bcfg["graphs"]["substrate_dir"]
                    runner.absence_builder = lambda st: EV.brief_absence_evidence(st, bcfg, drv, meta, sd,
                                                                                  faq_cfg["absence"])
                tasks = []
                for nid in sorted(answers["needs"], key=int):
                    ev = BR.load_ev(EV.BRIEF_EVIDENCE_DIR / f"need_{nid}.json")
                    tasks += recheck_tasks(int(nid), answers["needs"][nid], ev, BR.need_cfg(bcfg, int(nid)))
                pubs = {}
                for nid in sorted({t["need_id"] for t in tasks} | set(bcfg[AMEND]["published"]["new_round"])):
                    p = EV.BRIEF_EVIDENCE_DIR / f"need_{nid}_published.json"
                    if not p.is_file():
                        write_json(p, published_evidence(BR.load_ev(EV.BRIEF_EVIDENCE_DIR / f"need_{nid}.json")))
                    pubs[nid] = BR.load_ev(p)
                with ThreadPoolExecutor(max_workers=rc["workers"]) as ex:
                    corr["rechecks"] = list(ex.map(lambda t: runner.recheck(t["need_id"], t, pubs[t["need_id"]]), tasks))
                write_json(CORRECTIONS, corr)
                for t in corr["rechecks"]:
                    log(f"RECHECK need {t['need_id']} round {t['round']} {t['part']}: kept {t['kept']}")
                added = corr.get("rounds_added") or {}
                for nid in bcfg[AMEND]["published"]["new_round"]:
                    need = BR.need_cfg(bcfg, nid)
                    r = runner.need_round(pubs[nid], need, "", "_published")
                    rounds = [{**r, "evidence_file": f"need_{nid}_published.json"}]
                    log(f"NEW ROUND need {nid}: {r.get('status')} cut parts {r.get('cut_parts')}")
                    if r.get("status") == "done" and r["cut_parts"]:
                        # DCAT-004's procedure (`dcat_brief_run.BriefRunner.need`): a row that lost a
                        # part is asked once more with the cut reasons shown, and never again.
                        cuts = "\n".join(f"- {c['part']}: {c['sentence']!r} was cut ({c['cut_reason']}; "
                                         f"validator: {c.get('reason')})"
                                         for c in r["cut_items"] if c["part"] in ("asked", "landed", "literature"))
                        r2 = runner.need_round(pubs[nid], need, BR.REASK_NOTE.format(cuts=cuts), "_published_r2")
                        rounds.append({**r2, "evidence_file": f"need_{nid}_published.json"})
                        log(f"RE-ASK need {nid}: {r2.get('status')} cut parts {r2.get('cut_parts')}")
                    added[str(nid)] = rounds
                corr["rounds_added"] = added
                write_json(CORRECTIONS, corr)
            finally:
                if drv is not None:
                    drv.close()
        elif a.phase == "reader":
            brief = (OUT / "BRIEF.md").read_text(encoding="utf-8")
            rec = runner.reader(1, brief)
            corr.setdefault("readers", {})["1"] = {"unit_id": rec["unit_id"], "status": rec["status"], "model_id": rm,
                                                   "brief_sha256": FR.sha(brief), "answers": rec.get("parsed"),
                                                   "tokens": rec.get("tokens")}
    except FR.StopRun as exc:
        log(f"STOP: {exc}")
        rc_ = 3
    if len(answers.get("needs") or {}) == len(bcfg["needs"]):
        corr = assemble(answers, corr, bcfg)
    recs = [r for r in runner.ck.read() if r.get("run_id") == rc["run_id"]]
    corr["spend"] = {"run_id": rc["run_id"], "calls": len(recs), "done": sum(1 for r in recs if r["status"] == "done"),
                     "tokens": sum(r.get("tokens", 0) for r in recs),
                     "by_model": {m: sum(r.get("tokens", 0) for r in recs if r["model_id"] == m)
                                  for m in sorted({r["model_id"] for r in recs})}}
    corr["generated_at"] = _now()
    write_json(CORRECTIONS, corr)
    runner.progress(force=True)
    if corr.get("rows"):
        log("rows: " + json.dumps({k: v["outcome"] for k, v in corr["rows"].items()})
            + " verdict: " + json.dumps({k: v["answer"] for k, v in corr["verdict"].items()}))
    return rc_


if __name__ == "__main__":
    raise SystemExit(main())
