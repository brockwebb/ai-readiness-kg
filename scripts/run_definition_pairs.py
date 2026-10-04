#!/usr/bin/env python3
"""A cross-document conflict pass over the definitions of AI readiness. **Model spend, bounded.**

Task `cc_tasks/2026-10-04_definition_conflict_pass.md` (DN-009 decisions 2 and 8; closes the Q3
candidate task of the 48c74933 RESULT). Q3 of `run_kg_questions.py` could not answer whether
the literature's definitions conflict: every `CONFLICTS_WITH` edge was extracted inside one
document, so silence between two documents was not a comparison. This script makes the
comparison and records every pair, so an absence of a conflict edge becomes a recorded
"compared, no conflict".

    scripts/run_definition_pairs.py --dry-run                  pair list, controls, one prompt
    scripts/run_definition_pairs.py --run --ceiling-tokens N   controls (pilot + gate), then pairs
    scripts/run_definition_pairs.py --emit-edges               conflict rows -> grounding gate -> held shard
    scripts/run_definition_pairs.py --render                   docs/evidence/definition_pairs.{csv,md}
    scripts/run_definition_pairs.py --check                    no model call: pair list, controls and
                                                               both files re-derived; exit 1 on drift,
                                                               exit 2 when the Q1 set moved

**The set** (task decision 1) is Q1 as `run_kg_questions.py` wrote it to
`docs/evidence/kg_questions.yaml`; it is read from there and never recomputed. Full spans come
from the projection (Neo4j) at run time and are written onto every checkpoint row, so `--render`,
`--emit-edges` and `--check` need no database.

**Method and prior art** are in the README this script writes (`definition_pairs.md`). In short:
the decomposition is concept clarification's (collect the definitions of one construct, then
compare their focal object and their necessary attributes: Podsakoff, MacKenzie & Podsakoff
2016; MacKenzie, Podsakoff & Podsakoff 2011; Walker & Avant's defining attributes), and the
four outcomes are the correspondence relations of ontology matching (equivalence, subsumption
or overlap, disjointness; Euzenat & Shvaiko) restated for definitions. The judge is the
fss-policy-kg conflict adjudicator's shape (`icsp_notebook/docs/conflict_detection.md` §6-§8):
one pair per call, both verbatim spans, an ordered rubric whose early steps are the gate, a
confabulation guard on the rationale, every verdict persisted including the no-conflict ones,
`criteria_version` as a content hash of the rubric recomputed at runtime, `adjudicated: false`
on write. The prompt is an overlay of the adversarial-review baseline rubric v1.3.0 (role,
anti-anchoring, verbatim grounding), stamped on every row as `rubric_version`.

**Checkpoint** (`~/GitHub/CLAUDE.md` §15). Unit = one call on one pair (or control). Key =
sha1(pair key | model | criteria_version), so a changed rubric or model is a new unit and stale
verdicts are never reused. Every attempt is appended and fsynced to
`events/raw/definition_pairs/judgments.jsonl` before the next result is awaited; the raw
prompt and response sit beside it. Re-running `--run` is the resume command. Progress every
`PROGRESS_EVERY_UNITS` units or `PROGRESS_EVERY_SECONDS` s to stdout and the progress log. The
pilot is the control set, run first; its measured tokens per unit project the rest. The token
ceiling is the shared spend ledger's (DD-022, reserve before dispatch); the wall-clock ceiling
is `--max-wall-seconds`. A failed unit is a row and is retried at most `MAX_ATTEMPTS` times in a
second pass, after every unit has had its first attempt.

`--run` exits 0 when every unit is judged or has exhausted its attempts, 3 when a ceiling
(spend refusal, wall clock) or a model substitution stopped it — the checkpoint holds every
completed unit and `--render` reports the rest as `unjudged` — and 4 when the control gate
failed, in which case no pair is judged.

**Edges** (task decision 4). A `conflict` row's two spans go through `grounding.is_grounded`
against the text the extractor read (`run_bulk_extraction.doc_text` on the document's
`manifest_add` path). A miss goes to `edge_quarantine.jsonl` with its reason. A pass is written
through `eventlog.append` as an `edge_asserted` of type `conflicts_with` — into a TAGGED shard
(`batch-NNN_xdoc_conflict_held`), which `eventlog.replay()` never yields to the projection.
Reason: `build_projection.resolve_endpoint` scopes both endpoints of an `edge_asserted` to the
asserting document (`node_key(doc_id, id)`), so a cross-document edge on an untagged shard
would MERGE a label-less phantom node `<doc A>::<id B>` instead of reaching document B. The
held rows carry `quarantined: true` and that reason in the CSV; they are well-formed events a
projection change can replay without a model call.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import re
import sys
import threading
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
for _p in ("", "scripts", "mcp", "assessment"):
    if str(REPO / _p) not in sys.path:
        sys.path.insert(0, str(REPO / _p))

import yaml  # noqa: E402

TASK = "cc_tasks/2026-10-04_definition_conflict_pass.md"
GENERATOR = "scripts/run_definition_pairs.py"
Q1_YAML = REPO / "docs" / "evidence" / "kg_questions.yaml"
OUT_CSV = REPO / "docs" / "evidence" / "definition_pairs.csv"
OUT_MD = REPO / "docs" / "evidence" / "definition_pairs.md"
RAW_DIR = REPO / "events" / "raw" / "definition_pairs"
CHECKPOINT = RAW_DIR / "judgments.jsonl"
EDGE_QUARANTINE = RAW_DIR / "edge_quarantine.jsonl"
PROGRESS_DIR = REPO / "logs"

#: Tag of the off-graph shard that holds conflict edges the projection cannot place (module
#: docstring, "Edges"). `eventlog._TAG_RE`: lowercase, at most 32 characters.
HELD_TAG = "xdoc_conflict_held"
HELD_REASON = ("held_off_graph: build_projection.resolve_endpoint scopes both endpoints of an "
               "edge_asserted to the asserting document, so no standing path writes a "
               "cross-document edge")
EDGE_SOURCE = "cross_document_pass"

#: Closed vocabularies (task decision 3). `none` is the KIND line's value when the outcome
#: carries no kind; it is written to the CSV as an empty cell.
OUTCOMES = ("conflict", "differs_no_conflict", "consistent", "not_comparable")
KINDS = ("scope", "necessary_condition", "object_of_readiness")
KINDED = ("conflict", "differs_no_conflict")
#: Row status: `judged` carries an outcome; the other two say why a pair has none.
STATUSES = ("judged", "unparsed", "unjudged")

RUBRIC_VERSION = "v1.3.0"
OVERLAY = "definition-conflict (project-local, ai-readiness-kg)"
PROVIDER = "claude_max_oauth"
CLI = "claude"
CALL_CLASS = "judge"
RUN_ID_DEFAULT = "definition_pairs_2026-10-04"

#: One first attempt plus one retry, the bounded policy of §15 item 7 and of the fss-policy-kg
#: adjudicator ("retried once, then to failed/").
MAX_ATTEMPTS = 2
#: Concurrency cap of the fss-policy-kg adjudicator (conflict_detection.md §8).
WORKERS = 2
#: Progress cadence (§15 item 3).
PROGRESS_EVERY_UNITS = 10
PROGRESS_EVERY_SECONDS = 60
#: Back-off on a rate-limit rejection, which the stub releases rather than settles.
RATE_LIMIT_SLEEP_SECONDS = 60
RATE_LIMIT_MAX_WAITS = 5
#: Words of each span quoted in the CSV (task decision 3: "each under 15 words quoted").
QUOTE_MAX_WORDS = 14

#: Positive controls (task decision 5): cross-document pairs a prior artifact has already
#: characterised as differing. Pass criterion: none comes back `consistent`. Each is a real
#: pair of the set, judged once, flagged in the CSV and counted like any other pair.
_R48 = "cc_tasks/2026-10-02_kg_research_questions_RESULT.md §4"
POSITIVE_CONTROLS = (
    ("data-readiness-for-scientific-ai-at-scale::d_airready",
     "nao-216-128-artificial-intelligence-in-noaa::nao216-ai-ready-data",
     f"{_R48} s.2: the scientific source means cleaned, labeled, normalized data; NOAA means "
     f"discoverable, machine-readable, documented data"),
    ("ai-readiness-for-official-data-and-statistics-un-statistical::def_ai_readiness",
     "nao-216-128-artificial-intelligence-in-noaa::nao216-ai-ready-data",
     f"{_R48} s.2: the UN definition is the only one naming provenance and timeliness"),
    ("ai-readiness-for-official-data-and-statistics-un-statistical::def_ai_readiness",
     "data-readiness-for-scientific-ai-at-scale::d_airready",
     f"{_R48} s.2: the UN definition is the only one naming provenance and timeliness"),
    ("ai-readiness-building-the-bridge-from-higher-education-to-wo::def-ai-readiness",
     "artificial-intelligence-domain-ai-readiness-and-firm-product::d-domain-ai-readiness",
     f"{_R48} s.1: a human capability against an industry domain's integration of AI"),
    ("ai-readiness-building-the-bridge-from-higher-education-to-wo::def-ai-readiness",
     "from-school-ai-readiness-to-student-ai-literacy::def_inst_ai_readiness",
     f"{_R48} s.1: a human capability against an institution's collective capacity"),
    ("artificial-intelligence-domain-ai-readiness-and-firm-product::d-domain-ai-readiness",
     "from-school-ai-readiness-to-student-ai-literacy::def_inst_ai_readiness",
     f"{_R48} s.1: an industry domain against an institution's collective capacity"),
    ("ai-readiness-building-the-bridge-from-higher-education-to-wo::def-ai-readiness",
     "nao-216-128-artificial-intelligence-in-noaa::nao216-ai-ready-data",
     f"{_R48} s.1 and {TASK} decision 3: a human capability against a property of data"),
)
#: Negative controls (task decision 5): a definition against a script-made paraphrase of
#: itself (`script_paraphrase`, never the model). Pass criterion: all come back `consistent`.
#: One per kind of object in the set: a person's capability, an institution, data, data
#: development practice — so a judge that answers by object kind alone cannot pass them.
NEGATIVE_CONTROLS = (
    "ai-readiness-building-the-bridge-from-higher-education-to-wo::def-ai-readiness",
    "from-school-ai-readiness-to-student-ai-literacy::def_inst_ai_readiness",
    "nao-216-128-artificial-intelligence-in-noaa::nao216-ai-ready-data",
    "worldbank-blog-open-data-to-ai-ready-2025::def_airdd",
)
CONTROL_CRITERION = {
    "positive": "no positive control comes back `consistent` (any other outcome passes)",
    "negative": "every negative control comes back `consistent`",
}

INSTRUCTIONS = """You are an adversarial reviewer comparing TWO definitions. Each is copied verbatim from a different source document. Your question is exactly this: how do these two definitions relate?

Work through the steps in order and stop at the first step that decides.

Step 1. For each definition, identify the term it defines and its OBJECT OF READINESS: the kind of thing the definition says is ready, or has readiness. Kinds include: a person or a person's capability; an organisation or institution; an industry or domain; data or a dataset; a data system or infrastructure; a process.

Step 2. If the two objects are of different kinds:
  - if both define the same unqualified term (for example both define "AI readiness", ignoring case, hyphenation and "ready" versus "readiness") and neither term names its object, answer `conflict` with kind `object_of_readiness`: one term is given to incompatible objects;
  - otherwise answer `not_comparable`, with kind `none`, and name the two objects in the reason.

Step 3. The objects are of the same kind, or one is a part or subset of the other (data and a dataset; data and open data). Look for an incompatibility in the words themselves:
  - `conflict` with kind `necessary_condition`: words in one definition exclude, contradict or declare insufficient something that words in the other definition state is required or sufficient;
  - `conflict` with kind `scope`: words in one definition confine readiness to a use, stage, user or setting that words in the other definition explicitly exclude or declare insufficient.

Step 4. No incompatibility. If the definitions differ, answer `differs_no_conflict` with the kind of the most important difference: `necessary_condition` (they require or emphasise different attributes), `scope` (different use, stage, user or setting), or `object_of_readiness` (related but different objects, such as data and a data system). If they say the same thing, or one restates the other with no material difference, answer `consistent` with kind `none`.

Rules, and they are the point of the exercise:
1. Silence is not conflict. An attribute one definition names and the other does not mention is a difference, never a conflict. A conflict needs words in one definition that are incompatible with words in the other.
2. Judge only from the two texts below. Do not use knowledge of who wrote them, of other definitions, or of the wider literature.
3. Surface similarity is not sameness, and different wording is not difference: two phrasings of one requirement are one requirement.
4. `consistent` and `differs_no_conflict` are real answers. Do not manufacture a conflict to look decisive.
5. The reason is ONE sentence. It quotes, in double quotes, at least one short fragment (at most eight words) from EACH definition, copied character for character. Quote nothing else.

Answer with exactly four lines and nothing else:
OUTCOME: <one of conflict, differs_no_conflict, consistent, not_comparable>
KIND: <one of scope, necessary_condition, object_of_readiness, none>
CONFIDENCE: <a number between 0 and 1>
REASON: <one sentence>"""

#: fss-policy-kg §6.3: a 16-hex content hash of the rubric text, recomputed at runtime.
CRITERIA_VERSION = hashlib.sha256(INSTRUCTIONS.encode("utf-8")).hexdigest()[:16]

_O = re.compile(r"^\s*\**\s*OUTCOME\s*:\s*\**\s*`?([a-z_]+)`?", re.M | re.I)
_K = re.compile(r"^\s*\**\s*KIND\s*:\s*\**\s*`?([a-z_]+)`?", re.M | re.I)
_C = re.compile(r"^\s*\**\s*CONFIDENCE\s*:\s*\**\s*([01](?:\.\d+)?)", re.M | re.I)
_R = re.compile(r"^\s*\**\s*REASON\s*:\s*\**\s*(.*)$", re.M | re.I | re.S)
_QUOTED = re.compile(r"\"([^\"]+)\"|“([^”]+)”")


# ------------------------------------------------------------------------------- the set

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_q1(path: Path = Q1_YAML) -> tuple[list[dict], dict]:
    """The Q1 definition rows and the epoch they were answered at, as run_kg_questions wrote them."""
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    q1 = [q for q in doc["questions"] if q["id"] == "Q1"]
    if len(q1) != 1:
        raise SystemExit(f"FATAL: {path} holds {len(q1)} Q1 entries, expected 1")
    rows = q1[0].get("rows") or []
    if not rows:
        raise SystemExit(f"FATAL: {path} Q1 has no rows")
    keys = [r["node_key"] for r in rows]
    if len(set(keys)) != len(keys):
        raise SystemExit(f"FATAL: {path} Q1 repeats a node_key")
    return rows, doc["epoch"]


def pair_key(a: str, b: str) -> tuple[str, str]:
    """The unordered pair as an ordered tuple: lower key first."""
    return (a, b) if a < b else (b, a)


def pair_id(a: str, b: str) -> str:
    k = pair_key(a, b)
    return hashlib.sha1(f"{k[0]}|{k[1]}".encode()).hexdigest()[:16]


def build_pairs(rows: list[dict]) -> tuple[list[dict], int]:
    """Every unordered pair of definitions from DIFFERENT documents, sorted; and the number of
    same-document pairs skipped (task decision 3)."""
    by_key = {r["node_key"]: r for r in rows}
    keys = sorted(by_key)
    out, same_doc = [], 0
    for i, a in enumerate(keys):
        for b in keys[i + 1:]:
            if by_key[a]["doc_id"] == by_key[b]["doc_id"]:
                same_doc += 1
                continue
            out.append({"pair_id": pair_id(a, b), "key_a": a, "key_b": b,
                        "doc_a": by_key[a]["doc_id"], "doc_b": by_key[b]["doc_id"]})
    return out, same_doc


def positive_control_index() -> dict:
    return {pair_key(a, b): src for a, b, src in POSITIVE_CONTROLS}


def validate_controls(rows: list[dict]) -> None:
    keys = {r["node_key"]: r["doc_id"] for r in rows}
    for a, b, _ in POSITIVE_CONTROLS:
        if a not in keys or b not in keys or keys[a] == keys[b]:
            raise SystemExit(f"FATAL: positive control {a} x {b} is not a cross-document pair of the set")
    if len(set(pair_key(a, b) for a, b, _ in POSITIVE_CONTROLS)) != len(POSITIVE_CONTROLS):
        raise SystemExit("FATAL: a positive control is listed twice")
    for k in NEGATIVE_CONTROLS:
        if k not in keys:
            raise SystemExit(f"FATAL: negative control {k} is not in the set")


# ------------------------------------------------------------------------------- spans

def load_definitions_from_graph(keys: list[str]) -> dict:
    """key -> {term, span, doc_id, locator} from the projection, by key, through the MCP's
    own read-only driver."""
    import airkg_tools as T
    graph = T.Graph()
    if not graph.available():
        raise SystemExit(f"FATAL: Neo4j unreachable ({graph.error}); full spans live in the projection")
    rows, truncated = graph.read(
        "MATCH (d:Definition) WHERE d.key IN $keys RETURN d.key AS key, d.term AS term, "
        "d.grounding_span AS span, d.doc_id AS doc_id, d.location AS locator",
        limit=len(keys) + 1, keys=keys)
    if truncated or len(rows) != len(keys):
        raise SystemExit(f"FATAL: projection returned {len(rows)} Definitions for {len(keys)} keys")
    out = {r["key"]: r for r in rows}
    for k, r in out.items():
        if not (r.get("span") or "").strip():
            raise SystemExit(f"FATAL: {k} has no grounding_span (§4: no span, no write)")
    return out


_MD_EMPH = re.compile(r"(\*\*|\*)(?=\S)|(?<=\S)(\*\*|\*)")
_CITE = re.compile(r"\s*\[\d+(?:\s*[,–-]\s*\d+)*\]")
_DASH = re.compile(r"\s*[—–]\s*")
_SERIAL_COMMA = re.compile(r",\s+(and|or)\s")
#: British spellings rendered American: a respelling, never a different word.
_SPELLING = {"organisation": "organization", "organisational": "organizational",
             "conceptualised": "conceptualized", "standardised": "standardized",
             "optimised": "optimized", "utilise": "utilize", "prioritise": "prioritize",
             "behaviour": "behavior", "programme": "program", "modelling": "modeling"}
_SPELL_RX = re.compile(r"\b(" + "|".join(_SPELLING) + r")\b")


def script_paraphrase(text: str) -> tuple[str, list[str]]:
    """The negative control's second text: the same definition re-presented by a fixed chain of
    meaning-preserving surface transforms, applied by this script and never by a model. Returns
    the text and the transforms that changed something."""
    steps = [
        ("nfkc", lambda t: unicodedata.normalize("NFKC", t)),
        ("strip_markdown_emphasis", lambda t: _MD_EMPH.sub("", t)),
        ("strip_numeric_citations", lambda t: _CITE.sub("", t)),
        ("dash_to_comma", lambda t: _DASH.sub(", ", t)),
        ("drop_serial_comma", lambda t: _SERIAL_COMMA.sub(r" \1 ", t)),
        ("american_spelling", lambda t: _SPELL_RX.sub(lambda m: _SPELLING[m.group(1)], t)),
        ("collapse_whitespace", lambda t: " ".join(t.split())),
    ]
    applied = []
    for name, fn in steps:
        new = fn(text)
        if new != text:
            applied.append(name)
        text = new
    return text, applied


# ------------------------------------------------------------------------------- the judge

def build_prompt(term_a: str, span_a: str, term_b: str, span_b: str) -> str:
    """One pair and nothing else: no document ids, no prior characterisation, no other pair
    (anti-anchoring, rubric v1.3.0 §2), so the controls are blind."""
    return (f"{INSTRUCTIONS}\n\n---\n\n"
            f"DEFINITION 1\n  term: {term_a}\n  text: {span_a}\n\n"
            f"DEFINITION 2\n  term: {term_b}\n  text: {span_b}\n")


def parse_answer(text: str) -> dict:
    """The four lines, validated against the closed vocabularies. `status` is `judged` only
    when OUTCOME and KIND are both in vocabulary and agree (a kind exactly when kinded)."""
    o, k = _O.search(text or ""), _K.search(text or "")
    c, r = _C.search(text or ""), _R.search(text or "")
    outcome = o.group(1).lower() if o else None
    kind = k.group(1).lower() if k else None
    reason = " ".join((r.group(1) if r else "").split())
    rec = {"outcome": outcome, "kind": None if kind == "none" else kind,
           "confidence": float(c.group(1)) if c else None, "reason": reason or None}
    ok = (outcome in OUTCOMES and (kind == "none" or kind in KINDS)
          and ((outcome in KINDED) == (kind in KINDS)) and bool(reason))
    rec["status"] = "judged" if ok else "unparsed"
    return rec


def reason_check(reason: str | None, span_a: str, span_b: str) -> str:
    """Task decision 3: the reason cites only words present in the two spans. Every quoted
    fragment must be a verbatim substring of one span under the grounding gate's own
    normalization. `ok` | `no_quote` | `quote_not_in_spans`."""
    from kg.extraction import grounding
    frags = [m.group(1) or m.group(2) for m in _QUOTED.finditer(reason or "")]
    frags = [f.strip(" .,;:") for f in frags if f.strip(" .,;:")]
    if not frags:
        return "no_quote"
    for f in frags:
        if not (grounding.is_grounded(f, span_a) or grounding.is_grounded(f, span_b)):
            return "quote_not_in_spans"
    return "ok"


def unit_id(kind: str, ident: str, model: str) -> str:
    """§15 item 2: derived from the inputs, so a changed model or rubric is a new unit."""
    return hashlib.sha1(f"{kind}|{ident}|{model}|{CRITERIA_VERSION}".encode()).hexdigest()[:16]


def build_units(rows: list[dict], defs: dict, model: str) -> list[dict]:
    """Controls first (they are the pilot and the gate), then every remaining pair in sorted order."""
    pairs, _ = build_pairs(rows)
    pos = positive_control_index()
    units = []
    for k in NEGATIVE_CONTROLS:
        d = defs[k]
        para, applied = script_paraphrase(d["span"])
        units.append({"unit_kind": "negative_control", "pair_id": f"neg.{pair_id(k, k + '#para')}",
                      "key_a": k, "key_b": k, "doc_a": d["doc_id"], "doc_b": d["doc_id"],
                      "term_a": d["term"], "term_b": d["term"], "span_a": d["span"],
                      "span_b": para, "span_b_transforms": applied})
    ordered = sorted(pairs, key=lambda p: (pair_key(p["key_a"], p["key_b"]) not in pos, p["pair_id"]))
    for p in ordered:
        a, b = defs[p["key_a"]], defs[p["key_b"]]
        units.append({**p, "unit_kind": "positive_control" if (p["key_a"], p["key_b"]) in pos else "pair",
                      "term_a": a["term"], "term_b": b["term"], "span_a": a["span"],
                      "span_b": b["span"], "span_b_transforms": []})
    for u in units:
        u["unit_id"] = unit_id(u["unit_kind"], u["pair_id"], model)
    return units


# ------------------------------------------------------------------------------- checkpoint

def read_checkpoint(path: Path = CHECKPOINT) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def latest_by_unit(records: list[dict]) -> dict:
    """unit_id -> the record that decides it: the first `judged` attempt, else the last attempt."""
    out: dict = {}
    for r in records:
        cur = out.get(r["unit_id"])
        if cur is None or (cur["status"] != "judged" and (r["status"] == "judged" or r["attempt"] > cur["attempt"])):
            out[r["unit_id"]] = r
    return out


class Checkpoint:
    """Append-and-fsync, one line per attempt, under a lock (two workers)."""

    def __init__(self, path: Path):
        self.path = path
        self.lock = threading.Lock()
        path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, rec: dict) -> None:
        line = json.dumps(rec, ensure_ascii=False, sort_keys=True) + "\n"
        with self.lock:
            with self.path.open("a", encoding="utf-8") as fh:
                fh.write(line)
                fh.flush()
                os.fsync(fh.fileno())


class ScriptedFileConsumer:
    """Test double for the SIGKILL resume test (§15 item 8), selected by the environment
    variable `DEFPAIRS_SCRIPTED_CONSUMER=<json file>`. Answers a call with `answers[unit_id]`
    when the file has one and `answer` otherwise, sleeps `sleep_s`, and appends each call id to
    `calls_log` BEFORE answering, so a test can see every call made. Never selected in
    production: the flag is test-only."""

    def __init__(self, spec_path: str):
        spec = json.loads(Path(spec_path).read_text(encoding="utf-8"))
        self.answer, self.sleep_s = spec["answer"], float(spec.get("sleep_s", 0))
        self.answers = spec.get("answers") or {}
        self.calls_log, self.model_id = Path(spec["calls_log"]), spec.get("model_id", "scripted-model")

    def complete(self, prompt: str, *, call_id: str):
        with self.calls_log.open("a", encoding="utf-8") as fh:
            fh.write(call_id + "\n")
            fh.flush()
            os.fsync(fh.fileno())
        time.sleep(self.sleep_s)
        from harness.consumers import Completion
        uid = call_id.split(".")[1]
        return Completion(text=self.answers.get(uid, self.answer), model_id=self.model_id,
                          usage={"inputTokens": 1, "outputTokens": 1})


def _tokens(usage: dict) -> int:
    return sum(int((usage or {}).get(k, 0) or 0) for k in
               ("inputTokens", "outputTokens", "cacheCreationInputTokens", "cacheReadInputTokens"))


class StopRun(Exception):
    pass


def judge_unit(consumer, unit: dict, attempt: int, model: str, run_id: str, raw_dir: Path) -> dict:
    """One call; returns the checkpoint record. Raises StopRun on a spend refusal or a model
    substitution (the repo's STOP contract); every other failure is a row."""
    from kg import spend
    from kg.extraction import model_stub
    prompt = build_prompt(unit["term_a"], unit["span_a"], unit["term_b"], unit["span_b"])
    base = {k: unit[k] for k in ("unit_id", "unit_kind", "pair_id", "key_a", "key_b", "doc_a",
                                 "doc_b", "term_a", "term_b", "span_a", "span_b", "span_b_transforms")}
    base.update({"attempt": attempt, "model_id": model, "criteria_version": CRITERIA_VERSION,
                 "rubric_version": RUBRIC_VERSION, "overlay": OVERLAY, "run_id": run_id,
                 "adjudicator": model, "adjudicated": False,
                 "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest()})
    waits = 0
    while True:
        t0 = time.time()
        try:
            comp = consumer.complete(prompt, call_id=f"defpair.{unit['unit_id']}.{attempt}")
            break
        except spend.SpendRefusalStop as exc:
            raise StopRun(f"spend_refusal: {exc}") from exc
        except model_stub.ModelSubstitutionError as exc:
            raise StopRun(f"model_substitution: {exc}") from exc
        except model_stub.ModelRateLimitError as exc:
            waits += 1
            if waits > RATE_LIMIT_MAX_WAITS:
                return {**base, "status": "error", "error": f"rate_limited x{waits}: {exc}",
                        "outcome": None, "kind": None, "confidence": None, "reason": None,
                        "reason_check": None, "usage": {}, "tokens": 0, "ts": _now()}
            time.sleep(RATE_LIMIT_SLEEP_SECONDS)
        except model_stub.ModelInvocationError as exc:
            return {**base, "status": "error", "error": str(exc)[:500], "outcome": None,
                    "kind": None, "confidence": None, "reason": None, "reason_check": None,
                    "usage": {}, "tokens": 0, "ts": _now()}
    if comp.model_id != model:
        raise StopRun(f"model_substitution: envelope {comp.model_id!r}, expected {model!r}")
    parsed = parse_answer(comp.text)
    rec = {**base, **parsed, "error": None,
           "reason_check": reason_check(parsed["reason"], unit["span_a"], unit["span_b"]),
           "usage": comp.usage, "tokens": _tokens(comp.usage),
           "duration_ms": comp.duration_ms,
           "wall_s": round(time.time() - t0, 2), "ts": _now()}
    raw_dir.mkdir(parents=True, exist_ok=True)
    (raw_dir / f"{unit['unit_id']}.a{attempt}.json").write_text(
        json.dumps({"unit_id": unit["unit_id"], "attempt": attempt, "model_id": model,
                    "criteria_version": CRITERIA_VERSION, "prompt": prompt,
                    "response_text": comp.text, "usage": comp.usage}, indent=1, ensure_ascii=False),
        encoding="utf-8")
    return rec


def controls_verdict(decided: dict) -> dict:
    """The declared criterion, evaluated over whatever the checkpoint holds for the controls."""
    pos = [r for r in decided.values() if r["unit_kind"] == "positive_control"]
    neg = [r for r in decided.values() if r["unit_kind"] == "negative_control"]
    pos_ok = (len(pos) == len(POSITIVE_CONTROLS)
              and all(r["status"] == "judged" and r["outcome"] != "consistent" for r in pos))
    neg_ok = (len(neg) == len(NEGATIVE_CONTROLS)
              and all(r["status"] == "judged" and r["outcome"] == "consistent" for r in neg))
    return {"positive_pass": pos_ok, "negative_pass": neg_ok,
            "positive": sorted((r["key_a"], r["key_b"], r["outcome"], r["status"]) for r in pos),
            "negative": sorted((r["key_a"], r["outcome"], r["status"]) for r in neg)}


def run(rows: list[dict], defs: dict, consumer, model: str, run_id: str, checkpoint: Path,
        raw_dir: Path, workers: int, max_wall_s: float, progress_log: Path | None) -> int:
    units = build_units(rows, defs, model)
    ck = Checkpoint(checkpoint)
    t_start = time.time()
    state = {"done": 0, "fail": 0, "tokens": 0, "last": time.time(), "stop": None}

    def say(msg: str) -> None:
        print(msg, flush=True)
        if progress_log:
            progress_log.parent.mkdir(parents=True, exist_ok=True)
            with progress_log.open("a", encoding="utf-8") as fh:
                fh.write(msg + "\n")

    def progress(total: int, force: bool = False) -> None:
        now = time.time()
        if not force and state["done"] % PROGRESS_EVERY_UNITS and now - state["last"] < PROGRESS_EVERY_SECONDS:
            return
        state["last"] = now
        el = now - t_start
        rate = state["done"] / el if el else 0
        eta = (total - state["done"]) / rate if rate else float("nan")
        say(f"[{_now()}] {state['done']}/{total} units this pass, {rate * 60:.1f}/min, "
            f"eta {eta / 60:.1f} min, {state['tokens']:,} tokens, {state['fail']} failed")

    def pass_over(todo: list[tuple[dict, int]], label: str) -> None:
        state["done"] = 0
        say(f"[{_now()}] pass {label}: {len(todo)} units")
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futs, it = {}, iter(todo)

            def submit_next():
                if state["stop"] or time.time() - t_start > max_wall_s:
                    if not state["stop"] and time.time() - t_start > max_wall_s:
                        state["stop"] = f"wall_clock_ceiling {max_wall_s:.0f}s"
                    return
                nxt = next(it, None)
                if nxt is not None:
                    futs[ex.submit(judge_unit, consumer, nxt[0], nxt[1], model, run_id, raw_dir)] = nxt

            for _ in range(workers):
                submit_next()
            while futs:
                fut = next(as_completed(list(futs)))
                futs.pop(fut)
                try:
                    rec = fut.result()
                except StopRun as exc:
                    state["stop"] = str(exc)
                    continue
                ck.append(rec)
                state["done"] += 1
                state["tokens"] += rec.get("tokens") or 0
                state["fail"] += rec["status"] != "judged"
                progress(len(todo))
                submit_next()
        progress(len(todo), force=True)

    def todo_for(kinds: set, max_attempt: int) -> list:
        decided = latest_by_unit(read_checkpoint(checkpoint))
        out = []
        for u in units:
            if u["unit_kind"] not in kinds:
                continue
            r = decided.get(u["unit_id"])
            if r is None:
                out.append((u, 1))
            elif r["status"] != "judged" and r["attempt"] < max_attempt:
                out.append((u, r["attempt"] + 1))
        return out

    # 1. Pilot and gate: the controls, with their retry.
    ctrl = {"negative_control", "positive_control"}
    for attempt_cap in (1, MAX_ATTEMPTS):
        todo = todo_for(ctrl, attempt_cap)
        if todo:
            pass_over(todo, f"controls (attempt <= {attempt_cap})")
        if state["stop"]:
            say(f"STOP: {state['stop']}")
            return 3
    decided = latest_by_unit(read_checkpoint(checkpoint))
    verdict = controls_verdict(decided)
    say(f"controls: {json.dumps(verdict)}")
    if not (verdict["positive_pass"] and verdict["negative_pass"]):
        say("CONTROL GATE FAILED: the pair pass is not run; the judgments would not be usable")
        return 4
    measured = [r["tokens"] for r in decided.values() if r["unit_kind"] in ctrl and r.get("tokens")]
    remaining = len(todo_for({"pair"}, 1))
    if measured:
        per = sum(measured) / len(measured)
        say(f"pilot: {len(measured)} control units measured, {per:,.0f} tokens/unit; projected "
            f"{remaining} remaining units x {per:,.0f} = {remaining * per:,.0f} tokens")
    # 2. Every pair once, then the bounded retry.
    for attempt_cap in (1, MAX_ATTEMPTS):
        todo = todo_for({"pair"}, attempt_cap)
        if todo:
            pass_over(todo, f"pairs (attempt <= {attempt_cap})")
        if state["stop"]:
            say(f"STOP: {state['stop']}")
            return 3
    decided = latest_by_unit(read_checkpoint(checkpoint))
    n_j = sum(1 for r in decided.values() if r["status"] == "judged")
    say(f"done: {n_j}/{len(units)} units judged")
    return 0


# ------------------------------------------------------------------------------- edges

def held_shard_path() -> Path:
    from kg import eventlog
    existing = sorted(eventlog._events_dir().glob(f"batch-*_{HELD_TAG}.jsonl"))
    if existing:
        return existing[0]
    return eventlog._shard_path(eventlog.current_batch() + 1, HELD_TAG)


def held_events() -> dict:
    """pair_id -> event_id of every held conflict edge already on the tagged shard."""
    from kg import eventlog
    return {ev["payload"]["item"]["pair_id"]: ev["event_id"] for ev in eventlog.replay(tag=HELD_TAG)
            if ev.get("event_type") == "edge_asserted"}


def read_edge_quarantine() -> dict:
    if not EDGE_QUARANTINE.is_file():
        return {}
    return {json.loads(l)["pair_id"]: json.loads(l)
            for l in EDGE_QUARANTINE.read_text(encoding="utf-8").splitlines() if l.strip()}


def manifest_paths() -> dict:
    from kg import eventlog
    out = {}
    for ev in eventlog.replay():
        if ev.get("event_type") == "manifest_add":
            p = ev.get("payload") or {}
            if p.get("doc_id") and p.get("local_path"):
                out[p["doc_id"]] = p["local_path"]
    return out


def emit_edges() -> dict:
    """Task decision 4, idempotent: every `conflict` pair not yet held or quarantined goes
    through the grounding gate on BOTH spans, then onto the held shard or into quarantine."""
    from kg import eventlog
    from kg.extraction import grounding
    import run_bulk_extraction as rbe
    decided = latest_by_unit(read_checkpoint())
    conflicts = sorted((r for r in decided.values()
                        if r["unit_kind"] in ("pair", "positive_control") and r["status"] == "judged"
                        and r["outcome"] == "conflict"), key=lambda r: r["pair_id"])
    held, quarantined = held_events(), read_edge_quarantine()
    paths, texts = manifest_paths(), {}
    batch_n = int(re.match(r"batch-(\d+)_", held_shard_path().name).group(1))
    counts = {"conflict_rows": len(conflicts), "already_held": 0, "already_quarantined": 0,
              "held": 0, "quarantined": 0}
    for r in conflicts:
        if r["pair_id"] in held:
            counts["already_held"] += 1
            continue
        if r["pair_id"] in quarantined:
            counts["already_quarantined"] += 1
            continue
        miss = []
        for side in ("a", "b"):
            doc = r[f"doc_{side}"]
            if doc not in texts:
                lp = paths.get(doc)
                texts[doc] = rbe.doc_text(REPO / lp, doc) if lp and (REPO / lp).is_file() else None
            if texts[doc] is None:
                miss.append(f"{side}: source text for {doc} not on disk")
            elif not grounding.is_grounded(r[f"span_{side}"], texts[doc]):
                miss.append(f"{side}: grounding_span not found in source text of {doc}")
        if miss:
            with EDGE_QUARANTINE.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps({"pair_id": r["pair_id"], "unit_id": r["unit_id"],
                                     "reason": "; ".join(miss), "ts": _now()}) + "\n")
            counts["quarantined"] += 1
            continue
        a_doc, a_id = r["key_a"].split("::", 1)
        b_doc, b_id = r["key_b"].split("::", 1)
        eventlog.append({
            "event_type": "edge_asserted", "doc_id": a_doc, "task": TASK,
            "provenance": {"method": EDGE_SOURCE, "model_id": r["model_id"], "task": TASK,
                           "criteria_version": r["criteria_version"],
                           "rubric_version": r["rubric_version"], "run_id": r["run_id"],
                           "judgment_unit_id": r["unit_id"]},
            "payload": {"type": "conflicts_with", "from_id": a_id, "to_id": b_id,
                        "from_type": "Definition", "to_type": "Definition",
                        "from_key": r["key_a"], "to_key": r["key_b"],
                        "from_doc_id": a_doc, "to_doc_id": b_doc,
                        "item": {"type": "conflicts_with", "from_id": a_id, "to_id": b_id,
                                 "grounding_span": r["span_a"], "grounding_span_to": r["span_b"],
                                 "kind": r["kind"], "source": EDGE_SOURCE,
                                 "reason": r["reason"], "confidence": r["confidence"],
                                 "adjudicator": r["adjudicator"], "adjudicated": False,
                                 "pair_id": r["pair_id"], "held_reason": HELD_REASON}},
        }, batch=batch_n, tag=HELD_TAG)
        counts["held"] += 1
    return counts


# ------------------------------------------------------------------------------- render

def quote(span: str | None) -> str:
    words = (span or "").split()
    return " ".join(words[:QUOTE_MAX_WORDS]) + (" …" if len(words) > QUOTE_MAX_WORDS else "")


CSV_COLUMNS = ("pair_id", "key_a", "key_b", "doc_a", "doc_b", "term_a", "term_b",
               "quote_a", "quote_b", "locator_a", "locator_b", "status", "outcome", "kind",
               "reason", "reason_check", "confidence", "control", "control_source",
               "adjudicated", "quarantined", "quarantine_reason", "edge_event_id",
               "model_id", "criteria_version", "rubric_version", "attempt", "unit_id")


def csv_rows(rows: list[dict], decided: dict, held: dict, quarantine: dict) -> list[dict]:
    by_key = {r["node_key"]: r for r in rows}
    pos = positive_control_index()
    by_pair = {r["pair_id"]: r for r in decided.values() if r["unit_kind"] in ("pair", "positive_control")}
    pairs, _ = build_pairs(rows)
    out = []
    for p in pairs:
        r = by_pair.get(p["pair_id"])
        a, b = by_key[p["key_a"]], by_key[p["key_b"]]
        judged = bool(r) and r["status"] == "judged"
        is_q = p["pair_id"] in held or p["pair_id"] in quarantine
        out.append({
            "pair_id": p["pair_id"], "key_a": p["key_a"], "key_b": p["key_b"],
            "doc_a": p["doc_a"], "doc_b": p["doc_b"], "term_a": a["term"], "term_b": b["term"],
            "quote_a": quote(r["span_a"]) if r else a.get("quote") or "",
            "quote_b": quote(r["span_b"]) if r else b.get("quote") or "",
            "locator_a": a.get("locator") or "", "locator_b": b.get("locator") or "",
            "status": "judged" if judged else ("unparsed" if r else "unjudged"),
            "outcome": r["outcome"] if judged else "",
            "kind": (r["kind"] or "") if judged else "",
            "reason": (r["reason"] or "") if r else "",
            "reason_check": (r.get("reason_check") or "") if r else "",
            "confidence": "" if not r or r.get("confidence") is None else f"{r['confidence']:.2f}",
            "control": "positive" if (p["key_a"], p["key_b"]) in pos else "",
            "control_source": pos.get((p["key_a"], p["key_b"]), ""),
            "adjudicated": "false",
            "quarantined": "true" if is_q else "false",
            "quarantine_reason": (HELD_REASON if p["pair_id"] in held
                                  else quarantine[p["pair_id"]]["reason"] if p["pair_id"] in quarantine else ""),
            "edge_event_id": held.get(p["pair_id"], ""),
            "model_id": r["model_id"] if r else "", "criteria_version": r["criteria_version"] if r else "",
            "rubric_version": r["rubric_version"] if r else "",
            "attempt": str(r["attempt"]) if r else "", "unit_id": r["unit_id"] if r else "",
        })
    return out


def render_csv(out_rows: list[dict]) -> str:
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=CSV_COLUMNS, lineterminator="\n")
    w.writeheader()
    for r in out_rows:
        w.writerow(r)
    return buf.getvalue()


def _short(o: str) -> str:
    return {"conflict": "C", "differs_no_conflict": "D", "consistent": "S", "not_comparable": "N"}[o]


README = """# Cross-document conflict pass over the definitions of AI readiness

Generated by `{gen}` from `{ck}` and the held shard; do not edit by hand. Task `{task}`
(DN-009 decisions 2 and 8; DN-005 §2.4 exposure). Every unordered pair of Q1 definitions from
different documents has one row in `definition_pairs.csv`. A pair with no `conflict` row was
compared, not skipped. **Not adjudicated**: every row is one model's judgment (`adjudicated:
false`), and nothing here says what a conflict means for the framework.

## The set
Q1 as `scripts/run_kg_questions.py` wrote it to `docs/evidence/kg_questions.yaml` (epoch:
{n_docs_epoch} documents, {n_defs_epoch} Definitions): **{n_defs} definitions from {n_docs}
documents**. Unordered pairs {n_all}; same-document pairs skipped **{same_doc}**;
cross-document pairs **{n_pairs}**. Full spans come from the projection; the CSV quotes at most
{qw} words of each and gives the rest by locator.

**Coverage: {n_judged} of {n_pairs} cross-document pairs judged; {n_unjudged} unjudged, {n_unparsed}
unparsed.** {coverage_note}

## Method, and the prior art it adopts
- **Decomposition: concept clarification.** Collect the definitions of one construct, then
  compare the entity each says has the property and the attributes each makes necessary
  (Podsakoff, MacKenzie & Podsakoff 2016, *Organizational Research Methods* 19(2), the
  definition-construction stages; MacKenzie, Podsakoff & Podsakoff 2011, *MIS Quarterly*
  35(2), step 1, "the entity to which the property applies"; Walker & Avant's concept
  analysis, defining attributes). The three `kind` values map onto it: `object_of_readiness`
  is the entity, `necessary_condition` the attributes, `scope` the conceptual domain's bounds.
- **Outcomes: ontology-matching correspondences** restated for definitions (Euzenat &
  Shvaiko, *Ontology Matching*: equivalence, subsumption or overlap, disjointness):
  `consistent` ≈ equivalence; `differs_no_conflict` ≈ subsumption or overlap, where one object
  can satisfy both; `conflict` ≈ incompatibility stated in the words; `not_comparable` =
  different objects under different terms. Rule 1 of the rubric ("silence is not conflict")
  is the open-world reading: an attribute one definition omits is not denied by it.
- **Judge: the fss-policy-kg conflict adjudicator's shape** (`icsp_notebook/docs/
  conflict_detection.md` §6–§8, read for this task): one pair per call, both verbatim spans,
  an ordered rubric whose early steps are the gate, a confabulation guard on the rationale,
  every verdict persisted including the no-conflict ones, `criteria_version` a content hash of
  the rubric recomputed at runtime (`{cv}`), `adjudicated: false`. Prompt: an overlay of the
  adversarial-review baseline rubric {rv} (role, anti-anchoring, verbatim quoting). No
  document id or prior characterisation is shown, so the controls are blind.
- **Where it departs.** Single rater, no second adjudicator and no kappa (fss §6.5 parks the
  same extension); `adjudicator` is the full model id, not a normalized spelling; and the
  fss deontic classes (prohibition × permission) do not apply to definitions, so its
  verdict and basis vocabularies are replaced by this task's closed sets.
- **How the prior art was found.** This repository's corpus (MCP `search_text` "concept
  analysis", "conceptual definition": 0 hits; full-text grep of `corpus/bulk_md` and `docs/`
  for "concept analysis", "Walker and Avant", "Podsakoff", "construct clarity", "conceptual
  analysis", "MacKenzie": 0 method hits) and Wintermute (two queries, 0 results) hold none of
  it. The task's `Network: none` forbade the web search its decision 2 asked for, so the four
  citations above are **recalled, not retrieved**; they are named so a reader can check them.
- **The reason check.** Every quoted fragment in a reason must be a verbatim substring of one
  of the two spans under `kg/extraction/grounding.py` normalization: `reason_check` is `ok`,
  `no_quote` or `quote_not_in_spans`, computed by script, never by the judge.

## Controls (task decision 5), criterion declared before they ran
- **Positive** ({n_pos}, cross-document pairs a prior artifact characterised as differing;
  judged once as ordinary rows and counted): {crit_pos}. **Outcome: {pos_res}.**
- **Negative** ({n_neg}, a definition against a script-made paraphrase of itself, transforms
  NFKC, markdown emphasis, numeric citations, dashes, serial comma, British spelling,
  whitespace; not CSV rows, not counted):
  {crit_neg}. **Outcome: {neg_res}.**

| control | definition(s) | outcome | kind | reason_check | source of the characterisation / transforms |
|---|---|---|---|---|---|
{control_rows}

## Edges
Conflict rows: {n_conflict}. Held (grounding passed on both spans, written through
`kg.eventlog.append` as `edge_asserted` type `conflicts_with`, `source: {src}`, to the tagged
shard `{held_shard}`, which the projection never replays): **{n_held}**. Quarantined at the
grounding gate: **{n_q}**. Why held rather than projected: {held_reason} —
`scripts/build_projection.py::resolve_endpoint` would MERGE a label-less node
`<doc A>::<id B>`. Both counts are `quarantined: true` in the CSV.

The conflict rows, as judged (spans quoted to {qw} words; the reason is the judge's, unedited):

{conflict_rows}

## Table 1. Pair outcomes by document pair
Cell: C conflict, D differs_no_conflict, S consistent, N not_comparable, U unjudged or
unparsed; counts of definition pairs. Diagonal: same-document pairs skipped.

{doc_legend}

{matrix}

## Table 2. Counts by outcome and by kind

{counts}

## Table 3. Definitions ranked by `conflict` + `differs_no_conflict` rows
Order is by that count only, descending; ties in key order. No weighting.

{ranked}

## Reproduce
`/opt/anaconda3/bin/python3 {gen} --check` re-derives the pair list from Q1, re-evaluates the
controls from the checkpoint and compares both files byte for byte (no model call).
Judgments, prompts and responses: `{ck}` and `events/raw/definition_pairs/<unit_id>.a<n>.json`.
"""


#: Said whenever coverage is partial. Pairs run in `pair_id` order (a hash), so which pairs a
#: stop leaves unjudged is not chosen by their content.
COVERAGE_NOTE = ("An unjudged pair has no judgment record: the pass stopped before reaching it "
                 "(the RESULT names the stop). Pairs run in `pair_id` order, a hash, after the "
                 "positive controls, so which "
                 "pairs are unjudged was not chosen by their content, and every count below is "
                 "over the judged pairs only. Re-running `--run` resumes them by skip; a "
                 "changed rubric or model would start a new set of units instead.")


def render(rows: list[dict], epoch: dict, decided: dict, held: dict, quarantine: dict) -> tuple[str, str]:
    out_rows = csv_rows(rows, decided, held, quarantine)
    pairs, same_doc = build_pairs(rows)
    docs = sorted({r["doc_id"] for r in rows})
    label = {d: f"D{i + 1:02d}" for i, d in enumerate(docs)}
    # Table 1
    cell: dict = {}
    for r in out_rows:
        k = pair_key(r["doc_a"], r["doc_b"])
        c = cell.setdefault(k, {"C": 0, "D": 0, "S": 0, "N": 0, "U": 0})
        c[_short(r["outcome"]) if r["status"] == "judged" else "U"] += 1
    by_doc_n = {d: sum(1 for r in rows if r["doc_id"] == d) for d in docs}
    hdr = "| | " + " | ".join(label[d] for d in docs) + " |"
    lines = [hdr, "|---" * (len(docs) + 1) + "|"]
    for i, da in enumerate(docs):
        cells = []
        for j, db in enumerate(docs):
            if i == j:
                n = by_doc_n[da]
                cells.append(f"({n * (n - 1) // 2} skipped)" if n > 1 else "—")
            elif j < i:
                cells.append("")
            else:
                c = cell.get(pair_key(da, db), {})
                cells.append(" ".join(f"{k}{v}" for k, v in c.items() if v))
        lines.append(f"| {label[da]} | " + " | ".join(cells) + " |")
    legend = "\n".join(f"- {label[d]} `{d}` ({by_doc_n[d]} definition{'s' if by_doc_n[d] > 1 else ''})"
                       for d in docs)
    # Table 2
    judged = [r for r in out_rows if r["status"] == "judged"]
    t2 = ["| outcome | rows | " + " | ".join(KINDS) + " | no kind |", "|---|---|---|---|---|---|"]
    for o in OUTCOMES:
        rs = [r for r in judged if r["outcome"] == o]
        t2.append(f"| {o} | {len(rs)} | " + " | ".join(str(sum(1 for r in rs if r["kind"] == k)) for k in KINDS)
                  + f" | {sum(1 for r in rs if not r['kind'])} |")
    t2.append(f"| **all judged** | {len(judged)} | "
              + " | ".join(str(sum(1 for r in judged if r["kind"] == k)) for k in KINDS)
              + f" | {sum(1 for r in judged if not r['kind'])} |")
    for s in ("unparsed", "unjudged"):
        t2.append(f"| {s} | {sum(1 for r in out_rows if r['status'] == s)} | | | | |")
    t2 += ["", "| reason_check | rows |", "|---|---|"]
    for v in ("ok", "no_quote", "quote_not_in_spans"):
        t2.append(f"| {v} | {sum(1 for r in out_rows if r['reason_check'] == v)} |")
    # Table 3
    tally = {r["node_key"]: {"C": 0, "D": 0} for r in rows}
    for r in judged:
        if r["outcome"] in KINDED:
            for k in (r["key_a"], r["key_b"]):
                tally[k]["C" if r["outcome"] == "conflict" else "D"] += 1
    ranked = sorted(tally.items(), key=lambda kv: (-(kv[1]["C"] + kv[1]["D"]), kv[0]))
    by_key = {r["node_key"]: r for r in rows}
    n_in = {k: sum(1 for r in out_rows if k in (r["key_a"], r["key_b"])) for k in tally}
    n_jd = {k: sum(1 for r in judged if k in (r["key_a"], r["key_b"])) for k in tally}
    t3 = ["| rank | definition | term | conflict + differs | conflict | differs_no_conflict "
          "| pairs judged / in the pair list |",
          "|---|---|---|---|---|---|---|"]
    for i, (k, v) in enumerate(ranked, 1):
        t3.append(f"| {i} | `{k}` | {by_key[k]['term']} | {v['C'] + v['D']} | {v['C']} | {v['D']} "
                  f"| {n_jd[k]} / {n_in[k]} |")
    conf = [r for r in judged if r["outcome"] == "conflict"]
    crows = "\n".join(
        f"- `{r['key_a']}` ({r['term_a']}: \"{r['quote_a']}\") × `{r['key_b']}` ({r['term_b']}: "
        f"\"{r['quote_b']}\"). Kind `{r['kind']}`, confidence {r['confidence']}, reason_check "
        f"`{r['reason_check']}`. Reason: {r['reason']}" for r in conf) or "(none)"
    # controls
    ver = controls_verdict(decided)
    pos_i = positive_control_index()
    crow = []
    for r in sorted((r for r in decided.values() if r["unit_kind"] == "positive_control"), key=lambda r: r["pair_id"]):
        crow.append(f"| positive | `{r['key_a']}` × `{r['key_b']}` | {r['outcome'] if r['status'] == 'judged' else r['status']} "
                    f"| {r['kind'] or ''} | {r.get('reason_check') or ''} | {pos_i[(r['key_a'], r['key_b'])]} |")
    for r in sorted((r for r in decided.values() if r["unit_kind"] == "negative_control"), key=lambda r: r["key_a"]):
        crow.append(f"| negative | `{r['key_a']}` × its paraphrase | {r['outcome'] if r['status'] == 'judged' else r['status']} "
                    f"| {r['kind'] or ''} | {r.get('reason_check') or ''} | {', '.join(r['span_b_transforms']) or 'none changed the text'} |")
    n_pos_seen = sum(1 for r in decided.values() if r["unit_kind"] == "positive_control")
    n_neg_seen = sum(1 for r in decided.values() if r["unit_kind"] == "negative_control")
    res = lambda ok, seen, n: ("not run" if not seen else ("PASS" if ok else "FAIL")) + f" ({seen}/{n} judged)"
    held_shard = next(iter(sorted((REPO / "events").glob(f"batch-*_{HELD_TAG}.jsonl"))), None)
    md = README.format(
        gen=GENERATOR, ck=CHECKPOINT.relative_to(REPO).as_posix(), task=TASK,
        n_docs_epoch=epoch["documents"], n_defs_epoch=epoch["definitions"],
        n_defs=len(rows), n_docs=len(docs), n_all=len(rows) * (len(rows) - 1) // 2,
        same_doc=same_doc, n_pairs=len(pairs), qw=QUOTE_MAX_WORDS, cv=CRITERIA_VERSION,
        n_judged=len(judged), n_unjudged=sum(1 for r in out_rows if r["status"] == "unjudged"),
        n_unparsed=sum(1 for r in out_rows if r["status"] == "unparsed"),
        coverage_note=(COVERAGE_NOTE if len(judged) < len(pairs) else
                       "Every pair has a judgment."),
        rv=RUBRIC_VERSION, n_pos=len(POSITIVE_CONTROLS), n_neg=len(NEGATIVE_CONTROLS),
        crit_pos=CONTROL_CRITERION["positive"], crit_neg=CONTROL_CRITERION["negative"],
        pos_res=res(ver["positive_pass"], n_pos_seen, len(POSITIVE_CONTROLS)),
        neg_res=res(ver["negative_pass"], n_neg_seen, len(NEGATIVE_CONTROLS)),
        control_rows="\n".join(crow) or "| (none run) | | | | | |",
        n_conflict=sum(1 for r in judged if r["outcome"] == "conflict"),
        src=EDGE_SOURCE, held_shard=(held_shard.relative_to(REPO).as_posix() if held_shard else "none written"),
        n_held=len(held), n_q=len(quarantine), held_reason=HELD_REASON, conflict_rows=crows,
        doc_legend=legend, matrix="\n".join(lines), counts="\n".join(t2), ranked="\n".join(t3))
    return render_csv(out_rows), md


def load_state(q1_path: Path = Q1_YAML):
    rows, epoch = load_q1(q1_path)
    validate_controls(rows)
    return rows, epoch, latest_by_unit(read_checkpoint()), held_events(), read_edge_quarantine()


# ------------------------------------------------------------------------------- main

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--run", action="store_true")
    g.add_argument("--emit-edges", action="store_true")
    g.add_argument("--render", action="store_true")
    g.add_argument("--check", action="store_true")
    ap.add_argument("--model", default=None, help="default: model_config primary_judge_model_id")
    ap.add_argument("--ceiling-tokens", type=int, default=None)
    ap.add_argument("--run-id", default=RUN_ID_DEFAULT)
    ap.add_argument("--workers", type=int, default=WORKERS)
    ap.add_argument("--max-wall-seconds", type=float, default=4 * 3600)
    ap.add_argument("--defs-json", default=None,
                    help="definitions with spans (key -> {term, span, doc_id, locator}); default: the projection")
    ap.add_argument("--checkpoint", default=None, help="test seam: checkpoint path (default: CHECKPOINT)")
    ap.add_argument("--raw-dir", default=None, help="test seam: raw response dir (default: RAW_DIR)")
    a = ap.parse_args(argv)

    if a.check:
        rows, epoch = load_q1()
        stored = OUT_CSV.read_text(encoding="utf-8") if OUT_CSV.is_file() else None
        if stored is None or not OUT_MD.is_file():
            print("MISSING: definition_pairs.csv or .md")
            return 1
        pairs, _ = build_pairs(rows)
        stored_ids = [r["pair_id"] for r in csv.DictReader(io.StringIO(stored))]
        if stored_ids != [p["pair_id"] for p in pairs]:
            print("EPOCH MOVED or pair list drift: the CSV's pairs are not Q1's cross-document pairs")
            return 2
        _, _, decided, held, quarantine = load_state()
        text, md = render(rows, epoch, decided, held, quarantine)
        drift = [p.relative_to(REPO).as_posix() for p, t in ((OUT_CSV, text), (OUT_MD, md))
                 if p.read_text(encoding="utf-8") != t]
        ver = controls_verdict(decided)
        print(json.dumps({"pairs": len(pairs), "controls": {"positive_pass": ver["positive_pass"],
                                                            "negative_pass": ver["negative_pass"]},
                          "drift": drift}))
        return 1 if drift else 0

    if a.render:
        rows, epoch, decided, held, quarantine = load_state()
        text, md = render(rows, epoch, decided, held, quarantine)
        OUT_CSV.write_text(text, encoding="utf-8")
        OUT_MD.write_text(md, encoding="utf-8")
        print(f"wrote {OUT_CSV.relative_to(REPO)} and {OUT_MD.relative_to(REPO)}")
        return 0

    if a.emit_edges:
        load_state()
        print(json.dumps(emit_edges(), indent=1))
        return 0

    from kg.extraction import model_stub
    model = a.model or model_stub.load_model_config()["primary_judge_model_id"]
    rows, epoch = load_q1()
    validate_controls(rows)
    keys = [r["node_key"] for r in rows]
    if a.defs_json:
        defs = json.loads(Path(a.defs_json).read_text(encoding="utf-8"))
    else:
        defs = load_definitions_from_graph(keys)
    pairs, same_doc = build_pairs(rows)
    if a.dry_run:
        units = build_units(rows, defs, model)
        u = units[0]
        p = build_prompt(u["term_a"], u["span_a"], u["term_b"], u["span_b"])
        print(f"--- prompt for {u['unit_kind']} {u['pair_id']} ({len(p)} chars) ---\n{p}")
        print(json.dumps({"definitions": len(rows), "documents": len({r['doc_id'] for r in rows}),
                          "cross_document_pairs": len(pairs), "same_document_skipped": same_doc,
                          "units": len(units), "negative_controls": len(NEGATIVE_CONTROLS),
                          "positive_controls": len(POSITIVE_CONTROLS), "model": model,
                          "criteria_version": CRITERIA_VERSION}, indent=1))
        return 0

    scripted = os.environ.get("DEFPAIRS_SCRIPTED_CONSUMER")
    if scripted:
        consumer = ScriptedFileConsumer(scripted)
        model = consumer.model_id
    else:
        from kg import spend
        from harness.consumers import ClaudeCLIConsumer, ConsumerConfig
        model_stub.guard_no_api_key()
        if not a.ceiling_tokens:
            raise SystemExit("FATAL: --ceiling-tokens required before any model call (DD-022)")
        ledger = spend.default_ledger()
        ledger.declare(a.run_id, a.ceiling_tokens, declared_by=f"{GENERATOR} ({TASK})",
                       call_class=CALL_CLASS)
        spend.set_current_run(a.run_id)
        consumer = ClaudeCLIConsumer(ConsumerConfig(model_id=model, provider=PROVIDER, cli=CLI,
                                                    timeout_seconds=600, call_class=CALL_CLASS))
    rc = run(rows, defs, consumer, model, a.run_id, Path(a.checkpoint or CHECKPOINT),
             Path(a.raw_dir or RAW_DIR), a.workers,
             a.max_wall_seconds,
             (Path(a.checkpoint).parent if a.checkpoint else PROGRESS_DIR) / f"{a.run_id}.progress.log")
    if not scripted:
        from kg import spend
        st = spend.default_ledger().status().get("runs", {}).get(a.run_id, {})
        print(json.dumps({"run_id": a.run_id, "ledger": st}, default=str))
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
