#!/usr/bin/env python3
"""Ground-truth yield re-derivation (task 2026-08-30_ground_truth_yield_floor).

The pilot's §3 closure recorded that the yield floor's target — 45.23 admitted items per chunk,
from the never-validated chunked v0.3.5 arm — is a tripwire and not a validity criterion, and
mandated this re-derivation before any further extraction arm runs. This script measures what a
chunk actually contains, under a rubric written and sha-pinned BEFORE any annotation existed,
and re-derives the floor from that.

Phases:
  sample     seeded deterministic draw of the 5 chunks. Zero model calls. Written to a TRACKED
             file and committed before annotation, so the draw cannot be re-rolled after seeing
             a result.
  annotate   two independent passes per chunk under two framings (rubric-as-checklist;
             consumer-simulation), neither seeing any arm's output. Raws persisted.
  reconcile  deterministic: agreed by both passes -> ground truth. In exactly one pass ->
             ONE third-pass re-score against the rubric's explicit rules, seeing only the item,
             the chunk and the rubric. Unresolvable -> excluded AND counted.
  score      ground-truth yield, the re-derived floor, and all four arms scored against it.

The rubric is IMMUTABLE for this task (task §5). Every phase verifies its sha and refuses to
run against a changed rubric — patching a rubric after seeing annotations measures the patch.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import random
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO)); sys.path.insert(0, str(REPO / "scripts"))

from kg import eventlog, spend                                    # noqa: E402
from kg.extraction import chunker, merge, model_stub, parser      # noqa: E402
import chunked_pilot as cp                                        # noqa: E402
import run_bulk_extraction as rbe                                 # noqa: E402

TASK = "cc_tasks/2026-08-30_ground_truth_yield_floor.md"
RUN_ID = "ground_truth_yield_floor"
RUBRIC = REPO / "docs/research/ground_truth_rubric.md"
#: Pinned at authoring time, before any annotation existed. A changed rubric is a stop.
RUBRIC_SHA = "c30924f6e13893de56d17cb66c9c9a9694807749c11dd8972856818fa73dfc1d"

SAMPLE_PATH = REPO / "docs/research/ground_truth_sample.json"     # TRACKED, committed pre-run
OUT_DIR = REPO / "corpus/staging/metrics"
RAW_DIR = REPO / "events/raw/ground_truth"
SHARD_NO, TAG = 21, "ground_truth"

#: Recorded in the RESULT. Changing it re-rolls the draw, which is why it is a constant here
#: and not a flag.
SAMPLE_SEED = "ground_truth_yield_floor:2026-08-30"
N_CHUNKS = 5
BASELINE_TAG = "chunked_v035"

#: task §3.4 — below this the rubric is underspecified and the task STOPS. Patching it mid-task
#: would be measuring the patch.
MIN_INTERPASS_AGREEMENT = 0.5

#: task §4.1 — the floor is this fraction of measured ground-truth yield. Same 0.60 the pilot
#: used, applied now to a validated target instead of an unvalidated one.
FLOOR_FRACTION = 0.60


def verify_rubric() -> str:
    sha = hashlib.sha256(RUBRIC.read_bytes()).hexdigest()
    if sha != RUBRIC_SHA:
        raise SystemExit(
            f"FATAL: rubric sha {sha} != pinned {RUBRIC_SHA}. The rubric is immutable for this "
            f"task (§5): a defect found mid-task is reported and the task stops, and a new task "
            f"re-derives. Refusing to annotate against a changed rubric.")
    return sha


def annotator_model() -> str:
    """Strongest model the harness has (task §3.1: Sonnet-class or better, NOT Haiku — the
    annotator must outclass the production extractor, which was claude-haiku-4-5)."""
    cfg = model_stub.load_model_config()
    m = cfg["model_id"]
    if "haiku" in m.lower():
        raise SystemExit(f"FATAL: annotator would be {m}; §3.1 forbids Haiku-class annotation")
    return m


# ------------------------------------------------------------------ sample
def comparator_chunks() -> list[str]:
    cp.apply_arm("v0_3_9", None, None)
    return sorted(set(cp.chunk_yield("v0_3_9")) & set(cp.chunk_yield(BASELINE_TAG)))


def phase_sample(a) -> int:
    """Seeded, stratified, deterministic. Zero model calls."""
    verify_rubric()
    ids = comparator_chunks()
    by_doc = collections.defaultdict(list)
    for c in ids:
        by_doc[c.split("#")[0]].append(c)
    docs = sorted(by_doc)
    # Proportional allocation, largest-remainder, so every represented document appears and the
    # mix follows the comparator set rather than an arbitrary per-document quota.
    total = len(ids)
    exact = {d: N_CHUNKS * len(by_doc[d]) / total for d in docs}
    alloc = {d: int(exact[d]) for d in docs}
    for d in sorted(docs, key=lambda d: (-(exact[d] - int(exact[d])), d)):
        if sum(alloc.values()) >= N_CHUNKS:
            break
        alloc[d] += 1
    rng = random.Random(SAMPLE_SEED)
    picked = []
    for d in docs:
        picked += sorted(rng.sample(by_doc[d], alloc[d]))
    picked.sort()
    payload = {
        "task": TASK, "seed": SAMPLE_SEED, "n": len(picked),
        "drawn_from": {"comparator_chunks": total,
                       "documents": {d: len(by_doc[d]) for d in docs}},
        "allocation": alloc, "chunks": picked,
        "rubric_sha256": RUBRIC_SHA,
        "note": ("Task §2 says one chunk per document across the pilot's five documents. The "
                 "44-chunk comparator set spans only TWO of them, so a per-document quota of "
                 "five is not constructible; allocation is proportional to comparator coverage "
                 "instead. Reported as a discrepancy, not reconciled silently."),
    }
    SAMPLE_PATH.write_text(json.dumps(payload, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=1))
    return 0


def sample_chunks() -> list[str]:
    if not SAMPLE_PATH.is_file():
        raise SystemExit("FATAL: run --phase sample first; the draw must be committed before "
                         "annotation so it cannot be re-rolled after seeing a result")
    return json.loads(SAMPLE_PATH.read_text())["chunks"]


def chunk_text_of(chunk_id: str) -> tuple[str, str]:
    """(document text, chunk grounding text) for one chunk id."""
    doc = chunk_id.split("#")[0]
    m = cp.members()
    text = rbe.doc_text(m[doc])
    for c in chunker.chunk_document(doc, text):
        if c.chunk_id == chunk_id:
            return text, c.grounding_text()
    raise SystemExit(f"FATAL: {chunk_id} not produced by the current chunker")


# ------------------------------------------------------------------ annotate
FRAMINGS = {
    "checklist": (
        "You are annotating ONE CHUNK of a primary-source document against a fixed rubric, to "
        "establish ground truth for what the chunk contains. Work the rubric as a CHECKLIST: "
        "read the chunk once end to end, then walk the rubric's positive rules P1-P8 in order "
        "and collect every item in this chunk that a cited rule admits. Then walk the negative "
        "rules N1-N10 and remove anything they exclude."),
    "consumer": (
        "You are annotating ONE CHUNK of a primary-source document against a fixed rubric, to "
        "establish ground truth for what the chunk contains. Work it as a CONSUMER SIMULATION: "
        "the only declared consumer of this graph is an indicator evidence cell that must cite "
        "a doc_id and a grounding span (rubric §2). For this chunk, ask what an evidence cell "
        "could legitimately cite from it — what could be queried and answered from this text — "
        "and collect exactly those items. Then check each against the rubric's negative rules "
        "N1-N10 and drop anything they exclude."),
}


def annotation_prompt(framing: str, chunk_id: str, text: str) -> str:
    return (
        f"{FRAMINGS[framing]}\n\n"
        f"You see ONLY the chunk text and the rubric. No extraction system's output is shown to "
        f"you, and you must not try to guess what one would produce. Do not use knowledge from "
        f"outside this chunk (rubric §3.3).\n\n"
        f"=== RUBRIC (authoritative; sha256 {RUBRIC_SHA[:12]}) ===\n"
        f"{RUBRIC.read_text(encoding='utf-8')}\n"
        f"=== END RUBRIC ===\n\n"
        f"=== CHUNK {chunk_id} ===\n{text}\n=== END CHUNK ===\n\n"
        f"Output strict JSON only, no prose and no markdown fences:\n"
        f'{{"items": [{{"name": "<the document\'s own surface form, verbatim>", '
        f'"type": "<one of Definition, Concept, Instrument, Measure, Claim, Standard, '
        f'Framework, Practice, Tool, Platform>", '
        f'"evidence": "<the sentence or clause from the chunk carrying the assertion, copied '
        f'exactly>", "rule": "<the P-number from rubric §5 that admits it>", '
        f'"uncertain": <true|false>, "uncertain_reason": "<omit unless uncertain>"}}]}}'
    )


def raw_path(kind: str, chunk_id: str, model_id: str) -> Path:
    cid = chunk_id.replace("#", ".")
    return RAW_DIR / f"{cid}.{kind}.{RUBRIC_SHA[:12]}.{model_id}.json"


def _invoke(kind: str, chunk_id: str, prompt: str, model_id: str) -> dict:
    rp = raw_path(kind, chunk_id, model_id)
    if rp.exists():
        return json.loads(rp.read_text())
    cfg = {**model_stub.load_model_config(), "model_id": model_id}
    meta = model_stub.invoke(chunk_id, "", prompt=prompt, timeout=900, config=cfg)
    rec = {"chunk_id": chunk_id, "kind": kind, "rubric_sha256": RUBRIC_SHA,
           "model_id": meta["model_id"], "usage": meta["usage"],
           "cost_usd": meta.get("cost_usd"), "raw_result": meta["raw_result"]}
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    rp.write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return rec


def items_of(rec: dict) -> list[dict]:
    out = model_stub._extract_json(rec.get("raw_result") or "")
    items = out.get("items") if isinstance(out, dict) else None
    return [i for i in (items or []) if isinstance(i, dict) and str(i.get("name") or "").strip()]


def phase_annotate(a) -> int:
    verify_rubric()
    model = annotator_model()
    spend.set_current_run(RUN_ID)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    for cid in sample_chunks():
        _, ctext = chunk_text_of(cid)
        for framing in FRAMINGS:
            rec = _invoke(framing, cid, annotation_prompt(framing, cid, ctext), model)
            print(f"  {cid} [{framing}] {len(items_of(rec))} items", flush=True)
    return 0


# ------------------------------------------------------------------ reconcile
def key(name: str) -> str:
    return merge.normalized_key(name)


def contains(a: str, b: str) -> bool:
    return bool(a) and bool(b) and (a in b or b in a)


def match(k: str, pool: list[str]) -> str | None:
    """Containment-key match, exact first. Containment is the pilot's own instrument for this
    question (a renamed entity is not a missing one); exact-first keeps it from being looser
    than it must be."""
    if k in pool:
        return k
    for other in pool:
        if contains(k, other):
            return other
    return None


ADJUDICATE = (
    "You are adjudicating ONE candidate item against a fixed annotation rubric. Two independent "
    "annotators read the chunk below; exactly one of them proposed this item. Decide whether the "
    "rubric ADMITS it.\n\nYou see only the item, the chunk, and the rubric — not which annotator "
    "proposed it, not any extraction system's output, and not the other annotator's list. Admit "
    "the item ONLY if you can cite a positive rule (P1-P8) that applies; if any negative rule "
    "(N1-N10) excludes it, reject. If neither applies cleanly, return unresolvable — do not "
    "guess.\n\n=== RUBRIC (authoritative; sha256 {sha}) ===\n{rubric}\n=== END RUBRIC ===\n\n"
    "=== CHUNK {cid} ===\n{text}\n=== END CHUNK ===\n\n"
    "=== CANDIDATE ITEMS ===\n{items}\n=== END CANDIDATES ===\n\n"
    'Output strict JSON only: {{"decisions": [{{"name": "<name as given>", '
    '"verdict": "<admit|reject|unresolvable>", "rule": "<the P- or N-number you cite>", '
    '"why": "<one clause>"}}]}}'
)


def phase_reconcile(a) -> int:
    verify_rubric()
    model = annotator_model()
    spend.set_current_run(RUN_ID)
    report = {"rubric_sha256": RUBRIC_SHA, "annotator_model": model, "chunks": {}}
    agreements = []
    for cid in sample_chunks():
        _, ctext = chunk_text_of(cid)
        passes = {f: items_of(_invoke(f, cid, annotation_prompt(f, cid, ctext), model))
                  for f in FRAMINGS}
        ka = {key(i["name"]): i for i in passes["checklist"]}
        kb = {key(i["name"]): i for i in passes["consumer"]}
        agreed, singles = {}, {}
        for k, it in ka.items():
            m = match(k, list(kb))
            (agreed if m else singles)[k] = it
        for k, it in kb.items():
            if match(k, list(ka)) is None:
                singles.setdefault(k, it)
        union = len(agreed) + len(singles)
        jac = len(agreed) / union if union else 0.0
        agreements.append(jac)
        # ONE adjudication pass per chunk over that chunk's singletons (task §3.3).
        decisions = []
        if singles:
            payload = json.dumps([{"name": it["name"], "type": it.get("type"),
                                   "evidence": it.get("evidence"), "rule": it.get("rule")}
                                  for it in singles.values()], ensure_ascii=False, indent=1)
            rec = _invoke("adjudicate", cid, ADJUDICATE.format(
                sha=RUBRIC_SHA[:12], rubric=RUBRIC.read_text(encoding="utf-8"),
                cid=cid, text=ctext, items=payload), model)
            out = model_stub._extract_json(rec.get("raw_result") or "")
            decisions = (out.get("decisions") or []) if isinstance(out, dict) else []
        verdicts = {key(d.get("name") or ""): (d.get("verdict") or "unresolvable")
                    for d in decisions if isinstance(d, dict)}
        admitted = dict(agreed)
        excluded_unresolvable, excluded_rejected = [], []
        for k, it in singles.items():
            v = verdicts.get(k) or verdicts.get(match(k, list(verdicts)) or "", "unresolvable")
            if v == "admit":
                admitted[k] = it
            elif v == "reject":
                excluded_rejected.append(it["name"])
            else:
                excluded_unresolvable.append(it["name"])
        report["chunks"][cid] = {
            "pass_checklist": len(ka), "pass_consumer": len(kb),
            "agreed": len(agreed), "singletons": len(singles),
            "jaccard": round(jac, 4),
            "adjudicated_admit": len(admitted) - len(agreed),
            "excluded_rejected": excluded_rejected,
            "excluded_unresolvable": excluded_unresolvable,
            "ground_truth": sorted(
                ({"name": it["name"], "type": it.get("type"), "rule": it.get("rule")}
                 for it in admitted.values()), key=lambda r: r["name"]),
            "n_ground_truth": len(admitted),
        }
        print(f"  {cid}: checklist {len(ka)} / consumer {len(kb)} / agreed {len(agreed)} "
              f"/ jaccard {jac:.3f} -> GT {len(admitted)} "
              f"(+{len(admitted)-len(agreed)} adjudicated, "
              f"{len(excluded_unresolvable)} unresolvable)", flush=True)
    mean_j = statistics.mean(agreements) if agreements else 0.0
    report["interpass_agreement"] = {
        "per_chunk": [round(x, 4) for x in agreements], "mean": round(mean_j, 4),
        "threshold": MIN_INTERPASS_AGREEMENT}
    (OUT_DIR / "ground_truth_reconciled.json").write_text(json.dumps(report, indent=1))
    print(f"\nmean inter-pass Jaccard {mean_j:.4f} (stop threshold {MIN_INTERPASS_AGREEMENT})")
    if mean_j < MIN_INTERPASS_AGREEMENT:
        print("INCIDENT: inter-pass agreement below threshold — the rubric is underspecified. "
              "Task §3.4 STOP: reported, not patched. Scoring is not run.")
        return 3
    return 0


# ------------------------------------------------------------------ score
def arm_items(tag: str, chunks: list[str]) -> dict[str, dict[str, dict]]:
    """{chunk_id: {merge_key: item}} of ADMITTED node items for one arm's shard."""
    cp.apply_arm({"v0_3_7": "v0_3_7", "v0_3_8": "v0_3_8", "v0_3_9": "v0_3_9",
                  BASELINE_TAG: BASELINE_TAG}[tag], None, None)
    nodes, _, _ = cp.shard_items()
    out: dict[str, dict[str, dict]] = collections.defaultdict(dict)
    for d in cp.PILOT_DOCS:
        for ev in nodes[d]:
            cid = ev.get("chunk_id")
            if cid not in chunks:
                continue
            item = ev["payload"]["item"]
            nm = item.get("name") or item.get("term") or item.get("text") or ""
            k = key(nm)
            if k:
                out[cid].setdefault(k, {"name": nm, "type": ev["payload"]["type"]})
    return out


def phase_score(a) -> int:
    verify_rubric()
    rec = json.loads((OUT_DIR / "ground_truth_reconciled.json").read_text())
    chunks = sample_chunks()
    gt = {cid: {key(i["name"]): i for i in rec["chunks"][cid]["ground_truth"]}
          for cid in chunks}
    per_chunk = [len(gt[c]) for c in chunks]
    mean_gt = statistics.mean(per_chunk)
    floor = FLOOR_FRACTION * mean_gt
    out = {"rubric_sha256": RUBRIC_SHA, "seed": SAMPLE_SEED, "chunks": chunks,
           "ground_truth_per_chunk": {c: len(gt[c]) for c in chunks},
           "ground_truth_mean": round(mean_gt, 3),
           "ground_truth_median": statistics.median(per_chunk),
           "ground_truth_min": min(per_chunk), "ground_truth_max": max(per_chunk),
           "ground_truth_stdev": round(statistics.stdev(per_chunk), 3) if len(per_chunk) > 1 else None,
           "floor_fraction": FLOOR_FRACTION,
           "rederived_floor": round(floor, 3),
           "old_floor": round(0.60 * 45.227, 3),
           "arms": {}}
    print(f"ground truth per chunk: {out['ground_truth_per_chunk']}")
    print(f"mean {mean_gt:.2f}  median {out['ground_truth_median']}  "
          f"range {min(per_chunk)}-{max(per_chunk)}  -> re-derived floor {floor:.2f}/chunk "
          f"(old floor {out['old_floor']:.2f})\n")
    for tag, label in ((BASELINE_TAG, "v0.3.5 chunked"), ("v0_3_7", "Arm A"),
                       ("v0_3_8", "Arm A2"), ("v0_3_9", "Arm A3")):
        items = arm_items(tag, chunks)
        tp = admitted = gt_total = 0
        for c in chunks:
            pool = list(items.get(c, {}))
            admitted += len(pool)
            gt_total += len(gt[c])
            tp += sum(1 for k in gt[c] if match(k, pool))
        yield_pc = admitted / len(chunks)
        out["arms"][tag] = {
            "label": label, "admitted": admitted, "admitted_per_chunk": round(yield_pc, 3),
            "ground_truth_items": gt_total, "recall_matched": tp,
            "recall": round(tp / gt_total, 4) if gt_total else 0.0,
            "precision_proxy": round(tp / admitted, 4) if admitted else 0.0,
            "vs_rederived_floor": round(yield_pc / floor, 4) if floor else None,
            "meets_floor": bool(floor and yield_pc >= floor),
            "over_extraction_factor": round(yield_pc / mean_gt, 4) if mean_gt else None,
        }
        r = out["arms"][tag]
        print(f"{label:<16} admitted/chunk {r['admitted_per_chunk']:>6}  "
              f"recall {r['recall']:.3f}  precision-proxy {r['precision_proxy']:.3f}  "
              f"vs floor {r['vs_rederived_floor']}  {'MEETS' if r['meets_floor'] else 'below'}"
              f"  (x ground truth: {r['over_extraction_factor']})")
    (OUT_DIR / "ground_truth_scores.json").write_text(json.dumps(out, indent=1))
    eventlog.append({"event_type": "ground_truth_floor", "purpose": "yield_floor_rederivation",
                     "task": TASK, "rubric_sha256": RUBRIC_SHA, "seed": SAMPLE_SEED,
                     "payload": out}, batch=SHARD_NO, tag=TAG)
    return 0


PHASES = {"sample": phase_sample, "annotate": phase_annotate,
          "reconcile": phase_reconcile, "score": phase_score}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", required=True)
    ap.add_argument("--ceiling-tokens", type=int)
    a = ap.parse_args()
    model_stub.guard_no_api_key()
    if a.phase not in PHASES:
        raise SystemExit(f"unknown phase {a.phase!r}; known: {sorted(PHASES)}")
    if a.phase in ("annotate", "reconcile"):
        if not a.ceiling_tokens:
            raise SystemExit("FATAL: --ceiling-tokens required before any model call (DD-022)")
        spend.default_ledger().declare(RUN_ID, a.ceiling_tokens, declared_by=TASK,
                                       call_class="judge")
    try:
        return PHASES[a.phase](a)
    except spend.SpendRefusalStop as exc:
        print(f"spend guard: {exc} — clean stop", flush=True)
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
