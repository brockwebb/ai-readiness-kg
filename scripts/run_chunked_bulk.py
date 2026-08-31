#!/usr/bin/env python3
"""Production chunked burn under the v0.3.8 contract.

Task `cc_tasks/2026-08-30_bulk_extraction_v038.md`.

Why this script exists at all, recorded here because the task assumed it already did:
`run_bulk_extraction.py` extracts WHOLE DOCUMENTS. The qualified profile is chunk-unit with
an anchor contract (DD-023), and the only code that has ever run that contract is
`scripts/chunked_pilot.py` — which was bound to five pilot documents. So this driver supplies
what production needs (queue-derived worklist, untagged shard, per-batch ledger declarations,
acceptance sampling) and delegates every extraction primitive to `chunked_pilot`, which is
imported, not copied.

That delegation is a scientific requirement, not a convenience. Phase A qualifies a harness;
if the burn ran different code, Phase A would have qualified something the burn does not use.
The pilot's own globals (`DOCS`, `DOC_PATHS`, `PURPOSE`) are rebound here; everything else —
prompt assembly, dispatch, anchor resolution, grounding re-validation, ingest — is untouched.

Phases:
  cut      Phase 0.3/0.4  extract/defer cut -> queue events        (no model calls)
  sprt     Phase B        sequential plan constants                (no model calls)
  sample   Phase A        seeded stratified confirmation draw      (no model calls)
  extract  Phase A/C      dispatch chunk calls
  ingest   Phase A/C      parse persisted responses onto the shard (no model calls)
  judge    Phase A        pooled faithfulness gate + yield bands
"""
from __future__ import annotations

import argparse
import collections
import datetime
import hashlib
import json
import math
import os
import pathlib
import random
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

import chunked_pilot as cp                                          # noqa: E402
import run_bulk_extraction as rbe                                   # noqa: E402
from kg import eventlog, queue, spend                               # noqa: E402
from kg.extraction import chunker, model_stub                       # noqa: E402

TASK = "cc_tasks/2026-08-30_bulk_extraction_v038.md"
PROFILE = "bulk_v038"
RUN_ID = "bulk_v038_phase_a"
JUDGE_RUN_ID = "bulk_v038_phase_a_judge"

STATE_DIR = REPO / "state"
PRIORITY_PATH = STATE_DIR / "t2_priority.json"
SAMPLE_PATH = STATE_DIR / "bulk_v038_confirmation.json"
SPRT_PATH = STATE_DIR / "bulk_v038_sprt.json"

#: Phase 0.3, verbatim from the task: extract iff a consumer wants it.
def wants_extraction(row: dict) -> bool:
    return int(row.get("crosswalk_demand") or 0) >= 1 or float(row.get("t0_centrality") or 0) > 0


#: Documents every chunked arm has already been measured on. ADDENDUM-06 §1 holds the
#: confirmation set out of these: a set the arms have seen is a dev set, not a held-out one.
ARM_DOCS = frozenset(cp.PILOT_DOCS)

# ---------------------------------------------------------------- strata
#: ADDENDUM-06 §1 collapses manifest `source_type` to {statute/regulatory},
#: {agency/framework report}, {academic/preprint}. That vocabulary is imported from a
#: statute-heavy corpus and does NOT fit this one: the live `doc_type` vocabulary is
#: {academic, industry, federal, standard, intergovernmental, practitioner, platform}, there
#: are no statutes at all, and {industry, practitioner, platform} — 56 of 194 documents
#: corpus-wide, 6 of 31 in the burn set — falls outside all three of the addendum's classes.
#: Leaving them unstratified would give the largest non-academic class in the corpus no
#: Phase C monitoring band, which is the one thing ADDENDUM-06 §3 exists to prevent. Four
#: strata, total n unchanged at 30, pooled gate unchanged. Departure recorded in the RESULT.
STRATUM_OF = {
    "standard": "normative_standard",
    "platform": "normative_standard",
    "federal": "agency_framework",
    "intergovernmental": "agency_framework",
    "academic": "academic",
    "industry": "industry_practitioner",
    "practitioner": "industry_practitioner",
}
CONFIRMATION_CHUNKS = 30
SAMPLE_SEED = "bulk_v038_confirmation:2026-08-31"
#: ADDENDUM-06 §1: distinct documents required only where the stratum is document-rich.
DISTINCT_DOC_STRATUM_MIN = 10

# ---------------------------------------------------------------- Phase B constants
# Fixed in the task before any Phase A data exists, so Phase A cannot tune them.
SPRT_P0, SPRT_P1 = 0.05, 0.10
SPRT_ALPHA, SPRT_BETA = 0.05, 0.05


def now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


# ---------------------------------------------------------------- documents
def priority_rows() -> list[dict]:
    doc = json.loads(PRIORITY_PATH.read_text(encoding="utf-8"))
    if doc.get("provisional"):
        raise SystemExit(f"FATAL: {PRIORITY_PATH} is provisional; the cut is not final")
    return doc["t2_priority"]


def document_paths() -> dict[str, pathlib.Path]:
    """{doc_id: source path} for every admitted document, from the MANIFEST, not from an
    epoch member list. 5 of the 31 burn documents (the corpus/crosswalk/ lane) belong to no
    `corpus_epoch_declared` event, so epoch-scoped resolution — which is what
    `run_bulk_extraction.corpus_members` does — cannot reach them at all."""
    out = {}
    for doc_id, entry in queue.included_documents().items():
        path = (entry.get("identity") or {}).get("canonical_path")
        if path:
            out[doc_id] = REPO / path
    return out


def readable(path: pathlib.Path) -> bool:
    """Whether `doc_text` can read this source WITHOUT re-conversion (ADDENDUM-06 §1).

    2 of the 35 burn documents are .html with no markdown conversion in the store. Converting
    them here would be a silent re-conversion inside a run that pre-registered against not
    doing one, so they are reported and excluded rather than quietly handled."""
    return path.suffix.lower() in (".md", ".txt", ".pdf") and path.exists()


def apply_production_profile(run_id: str = RUN_ID) -> dict:
    """Point the pilot's extraction path at the production profile and the burn set."""
    prof = cp.apply_arm(PROFILE, None, run_id)
    if prof.get("shard_tag"):
        raise SystemExit(
            f"FATAL: profile {PROFILE!r} declares shard_tag={prof['shard_tag']!r}. "
            f"eventlog.replay() skips tagged shards, so a burn under it would never reach "
            f"the graph. A production profile declares no tag.")
    cp.PURPOSE = PROFILE
    cp.DOC_PATHS = document_paths()
    return prof


# ---------------------------------------------------------------- Phase 0.3 / 0.4 — the cut
def compute_cut() -> tuple[list[dict], list[dict]]:
    """(extract rows in t2_priority order, defer rows). Derived live, never cached."""
    included = set(queue.included_documents())
    rows = [r for r in priority_rows() if r["doc_id"] in included]
    return [r for r in rows if wants_extraction(r)], [r for r in rows if not wants_extraction(r)]


def cut_reason(row: dict) -> str:
    bits = []
    if int(row.get("crosswalk_demand") or 0) >= 1:
        bits.append(f"crosswalk_demand={row['crosswalk_demand']}")
    if float(row.get("t0_centrality") or 0) > 0:
        bits.append(f"t0_centrality={row['t0_centrality']}")
    return "consumer: " + ", ".join(bits)


def phase_cut(a) -> int:
    extract, defer = compute_cut()
    paths = document_paths()
    unreadable = [r["doc_id"] for r in extract
                  if r["doc_id"] not in paths or not readable(paths[r["doc_id"]])]
    print(f"t2_priority label={json.loads(PRIORITY_PATH.read_text())['label']!r}")
    print(f"EXTRACT {len(extract)}   DEFER {len(defer)}   (of {len(extract) + len(defer)} "
          f"manifest-included rows)")
    print(f"unconvertible sources in the extract set: {len(unreadable)} {unreadable}")
    proj = queue.project()
    already = [r["doc_id"] for r in extract
               if proj.get(r["doc_id"], {}).get("extraction_state") == "extracted"]
    print(f"already extracted under the pin: {len(already)}")
    if not a.commit:
        print("\nDRY RUN — no events emitted. Re-run with --commit.")
        return 0

    emitted = collections.Counter()
    # Both derivations replay the whole log; hoisted out of a 159-iteration loop, and the
    # local sets are kept in step with what we emit so the idempotency check stays honest.
    live = set(queue.live_requests())
    already_deferred = set(queue.deferrals())
    for row in defer:
        if row["doc_id"] in live:
            queue.withdraw(row["doc_id"], "no consumer (bulk_v038 Phase 0.3 cut)")
            live.discard(row["doc_id"])
            emitted["withdrawn"] += 1
        if row["doc_id"] in already_deferred:
            emitted["already_deferred"] += 1
            continue
        queue.defer(row["doc_id"], "no consumer")
        already_deferred.add(row["doc_id"])
        emitted["deferred"] += 1
    # `superseding` is not optional here. 29 of the 35 documents in the extract set were
    # already extracted under v1 / kernel-v03 / the triage epoch — under a different prompt
    # AND a different extraction unit. Without the flag the projection reads them `stale`
    # (extracted under something older) rather than `queued`, and the worklist reports 6
    # documents against 35 emitted requests.
    for i, row in enumerate(extract, start=1):
        queue.request(row["doc_id"], priority=i, requested_by="bulk_v038 Phase 0.4",
                      reason=cut_reason(row), profile=PROFILE, superseding=True)
        emitted["requested"] += 1
    for doc_id in unreadable:
        eventlog.append({"event_type": "bulk_doc_failed", "purpose": PROFILE, "doc_id": doc_id,
                         "stage": "unconvertible_source", "task": TASK,
                         "reason": f"{paths.get(doc_id)} has no markdown/pdf conversion; "
                                   f"ADDENDUM-06 §1 forbids re-conversion in this run",
                         "ts": now()}, batch=queue.QUEUE_BATCH)
        emitted["unconvertible"] += 1
    print("emitted:", dict(emitted))
    return 0


# ---------------------------------------------------------------- Phase B — the SPRT
def sprt_boundaries(p0=SPRT_P0, p1=SPRT_P1, alpha=SPRT_ALPHA, beta=SPRT_BETA) -> dict:
    """Wald (1945) sequential probability ratio test for a binomial fabrication rate.

    The decision lines are d = intercept + slope * n, where n is facts judged and d is
    fabrications seen. Both are pure functions of (p0, p1, alpha, beta), which the task fixed
    before Phase A ran; nothing measured enters here."""
    A = math.log((1 - beta) / alpha)          # reject-H0 (batch is bad) boundary
    B = math.log(beta / (1 - alpha))          # accept-H0 (batch is good) boundary
    s1 = math.log(p1 / p0)                    # log-LR contribution of one fabrication
    s0 = math.log((1 - p1) / (1 - p0))        # ... of one clean fact (negative)
    slope = -s0 / (s1 - s0)
    return {
        "p0": p0, "p1": p1, "alpha": alpha, "beta": beta,
        "log_A": A, "log_B": B, "slope": slope,
        "accept_intercept": B / (s1 - s0),    # d <= intercept + slope*n  -> ACCEPT
        "reject_intercept": A / (s1 - s0),    # d >= intercept + slope*n  -> REJECT
    }


def min_facts_for_accept(b: dict) -> int:
    """Smallest n at which a PERFECT batch (0 fabrications) can cross the accept line.

    DD-026, applied to this plan: below this n no evidence can settle the batch, so a sample
    smaller than this buys a foregone `continue` — the same defect as judging a stratum that
    cannot reach its gate. Arithmetic: 0 <= accept_intercept + slope*n."""
    if b["slope"] <= 0:
        raise ValueError("degenerate plan: slope must be positive")
    return math.ceil(-b["accept_intercept"] / b["slope"])


def sprt_decide(fabrications: int, facts: int, b: dict) -> str:
    """`accept` | `reject` | `continue` for a batch sample, from the boundaries alone."""
    if fabrications >= b["reject_intercept"] + b["slope"] * facts:
        return "reject"
    if fabrications <= b["accept_intercept"] + b["slope"] * facts:
        return "accept"
    return "continue"


def expected_sample_number(b: dict, p: float) -> float:
    """Wald's ASN at true rate p — used to set each batch's sample budget (2x ASN)."""
    s1, s0 = math.log(b["p1"] / b["p0"]), math.log((1 - b["p1"]) / (1 - b["p0"]))
    den = p * s1 + (1 - p) * s0
    # E[z] = 0 exactly at p = -s0/(s1-s0) = the boundary slope. Wald's ratio is singular
    # there and the limit is the second-moment form; returning 0.0 (what a bare `if den`
    # guard did) would have put a nonsense sample budget into the Phase C rule.
    if abs(den) < 1e-9:
        ez2 = p * s1 * s1 + (1 - p) * s0 * s0
        return abs(-b["log_A"] * b["log_B"] / ez2)
    num = (1 - _prob_reject(b, p)) * b["log_B"] + _prob_reject(b, p) * b["log_A"]
    return abs(num / den)


def _prob_reject(b: dict, p: float) -> float:
    """Wald's OC-curve approximation for P(reject H0) at true rate p."""
    if abs(p - b["p0"]) < 1e-12:
        return b["alpha"]
    if abs(p - b["p1"]) < 1e-12:
        return 1 - b["beta"]
    lo, hi = -50.0, 50.0
    for _ in range(200):                       # solve for Wald's h: E[(LR)^h] = 1
        h = (lo + hi) / 2
        v = p * (b["p1"] / b["p0"]) ** h + (1 - p) * ((1 - b["p1"]) / (1 - b["p0"])) ** h
        if v > 1:
            hi = h
        else:
            lo = h
    h = (lo + hi) / 2
    if abs(h) < 1e-9:
        return 0.5
    return (1 - math.exp(b["log_B"] * h)) / (math.exp(b["log_A"] * h) - math.exp(b["log_B"] * h))


def phase_sprt(a) -> int:
    b = sprt_boundaries()
    n_min = min_facts_for_accept(b)
    # p* = the boundary slope: the rate at which the plan is least decisive and the ASN
    # peaks. Reporting the peak, not a convenient point, is what makes the budget honest.
    asn = {f"p={round(p, 5)}": round(expected_sample_number(b, p), 1)
           for p in (SPRT_P0, b["slope"], SPRT_P1)}
    out = {"task": TASK, "plan": "Wald SPRT on the batch fabrication rate", **b,
           "min_facts_for_accept": n_min, "expected_sample_number": asn,
           "sample_budget_rule": "2x ASN at p0; a batch still `continue` at the budget is "
                                 "accept-with-flag and counts toward the consecutive rule",
           "corpus_stop_rule": "2 consecutive rejects, or 3 rejects/inconclusives in any "
                               "rolling 5 batches",
           "derived_at": now()}
    SPRT_PATH.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    print(f"SPRT p0={b['p0']} p1={b['p1']} alpha={b['alpha']} beta={b['beta']}")
    print(f"  accept line   d <= {b['accept_intercept']:+.4f} + {b['slope']:.5f} n")
    print(f"  reject line   d >= {b['reject_intercept']:+.4f} + {b['slope']:.5f} n")
    print(f"  min facts before ACCEPT is reachable (0 fabrications): {n_min}")
    print(f"  expected sample number: {asn}")
    print(f"written: {SPRT_PATH}")
    return 0


# ---------------------------------------------------------------- Phase A — the draw
def burn_set() -> list[str]:
    extract, _ = compute_cut()
    return [r["doc_id"] for r in extract]


def confirmation_candidates() -> dict[str, list[str]]:
    """{stratum: [doc_id]} eligible for the confirmation draw.

    Drawn from the BURN SET, not corpus-wide. ADDENDUM-06 §1 says corpus-wide, but this
    task's own Phase 0.3 declares 159 documents deferred, `admitted, not extracted` — and a
    corpus-wide draw would extract some of them. Two binding instructions collide; the later
    and more specific one wins, and the confirmation chunks are then real burn output rather
    than spend on documents the same task just declined. Recorded in the RESULT."""
    proj = queue.project()
    paths = document_paths()
    out: dict[str, list[str]] = collections.defaultdict(list)
    for doc_id in burn_set():
        if doc_id in ARM_DOCS:
            continue                                   # held out: an arm has seen it
        if doc_id not in paths or not readable(paths[doc_id]):
            continue
        stratum = STRATUM_OF.get((proj.get(doc_id) or {}).get("doc_type"))
        if stratum:
            out[stratum].append(doc_id)
    return {s: sorted(v) for s, v in sorted(out.items())}


def allocate(strata: dict[str, list[str]], total: int = CONFIRMATION_CHUNKS) -> dict[str, int]:
    """As-equal-as-possible allocation of `total` chunks, remainder to the document-richest
    strata. Equal beats proportional here: each stratum's mean is a Phase C monitoring band
    and they need comparable precision, not precision proportional to corpus share."""
    names = sorted(strata, key=lambda s: (-len(strata[s]), s))
    base, extra = divmod(total, len(names))
    return {s: base + (1 if i < extra else 0) for i, s in enumerate(names)}


def draw_confirmation() -> dict:
    strata = confirmation_candidates()
    if not strata:
        raise SystemExit("FATAL: no eligible documents for the confirmation draw")
    quota = allocate(strata)
    rng = random.Random(SAMPLE_SEED)
    paths = document_paths()
    chosen, per_stratum = [], {}
    for stratum, docs in strata.items():
        want = quota[stratum]
        distinct_only = len(docs) >= DISTINCT_DOC_STRATUM_MIN
        pool = []                                       # (doc_id, chunk_id) round-robin
        by_doc = {}
        for doc_id in docs:
            text = rbe.doc_text(paths[doc_id])
            by_doc[doc_id] = [c.chunk_id for c in chunker.chunk_document(doc_id, text)]
        order = docs[:]
        rng.shuffle(order)
        for doc_id in order:
            ids = by_doc[doc_id][:]
            rng.shuffle(ids)
            pool.append((doc_id, ids))
        picked, round_i = [], 0
        while len(picked) < want and any(ids for _, ids in pool):
            progressed = False
            for doc_id, ids in pool:
                if len(picked) >= want or not ids:
                    continue
                if distinct_only and round_i > 0:
                    continue
                picked.append({"doc_id": doc_id, "chunk_id": ids.pop(0), "stratum": stratum})
                progressed = True
            round_i += 1
            if not progressed:
                break
        per_stratum[stratum] = {"documents": len(docs), "quota": want, "drawn": len(picked),
                                "distinct_documents_required": distinct_only}
        chosen += picked
    return {"task": TASK, "profile": PROFILE, "seed": SAMPLE_SEED,
            "requested_total": CONFIRMATION_CHUNKS, "drawn_total": len(chosen),
            "strata": per_stratum, "held_out_from": sorted(ARM_DOCS),
            "chunks": sorted(chosen, key=lambda c: (c["stratum"], c["doc_id"], c["chunk_id"])),
            "drawn_at": now()}


def phase_sample(a) -> int:
    apply_production_profile()
    payload = draw_confirmation()
    SAMPLE_PATH.write_text(json.dumps(payload, indent=1) + "\n", encoding="utf-8")
    print(f"seed {payload['seed']!r}   drawn {payload['drawn_total']}/"
          f"{payload['requested_total']} chunks")
    for s, r in payload["strata"].items():
        print(f"  {s:<24} docs {r['documents']:>3}  quota {r['quota']:>3}  "
              f"drawn {r['drawn']:>3}  distinct-docs={r['distinct_documents_required']}")
    print(f"written: {SAMPLE_PATH}")
    return 0


def confirmation_sample() -> dict:
    if not SAMPLE_PATH.is_file():
        raise SystemExit(f"FATAL: {SAMPLE_PATH} missing — run `--phase sample` first "
                         f"(ADDENDUM-06 §1: the draw script is committed BEFORE the run)")
    return json.loads(SAMPLE_PATH.read_text(encoding="utf-8"))


# ---------------------------------------------------------------- Phase A — extract/ingest
def bind_confirmation_run() -> dict:
    """Point the shared extraction path at exactly the committed draw."""
    payload = confirmation_sample()
    apply_production_profile()
    cp.DOCS = sorted({c["doc_id"] for c in payload["chunks"]})
    cp.CHUNK_FILTER = {c["chunk_id"] for c in payload["chunks"]}
    return payload


def phase_extract(a) -> int:
    payload = bind_confirmation_run()
    if not a.ceiling_tokens:
        raise SystemExit("FATAL: --ceiling-tokens required before any model call (DD-022)")
    spend.default_ledger().declare(RUN_ID, a.ceiling_tokens, declared_by=TASK,
                                   call_class="extraction_chunk")
    print(f"Phase A: {len(cp.CHUNK_FILTER)} chunks over {len(cp.DOCS)} documents, "
          f"profile {PROFILE}, ceiling {a.ceiling_tokens:,}")
    args = type("A", (), {"shared_with": None, "only": None, "limit": None,
                          "workers": a.workers})()
    return cp.phase_extract(args)


def phase_ingest(a) -> int:
    bind_confirmation_run()
    return cp.phase_ingest(type("A", (), {"reingest": bool(a.reingest)})())


# ---------------------------------------------------------------- Phase A — the gate
def document_strata() -> dict[str, str]:
    proj = queue.project()
    return {d: STRATUM_OF.get((proj.get(d) or {}).get("doc_type"), "unstratified")
            for d in cp.DOCS}


def bulk_records(texts: dict[str, str]) -> list[dict]:
    """One judgeable record per admitted NODE item, stratified by DOCUMENT class.

    Unit, stated because the 45.23 defect was a unit mismatch (DD-028): the Phase A gate's
    unit is atomic facts of admitted node items, and the probe protocol is the instrument
    that measures exactly that. Edges are not records here — DD-024 keeps semantic edges out
    of bulk entirely, and the `cites` layer is reported by defect count, not judged.

    Deduplicated per (document, normalized name, type): the same claim asserted from two
    chunks is one claim, and judging it twice would weight it twice in a pooled rate."""
    from kg.extraction import grounding
    nodes, _edges, _stubs = cp.shard_items()
    strata = document_strata()
    recs, seen = [], set()
    for doc_id in cp.DOCS:
        norm = grounding.normalize(texts[doc_id])
        for ev in nodes.get(doc_id, []):
            item = ev["payload"]["item"]
            name = item.get("name") or item.get("term") or item.get("text") or ""
            key = (doc_id, cp.norm_form(name), ev["payload"]["type"])
            if not name or key in seen:
                continue
            seen.add(key)
            span = item.get("grounding_span") or ""
            recs.append({"item_id": f"{ev['chunk_id']}:{ev['payload']['id']}",
                         "event_id": ev["event_id"], "kind": "node",
                         "type": ev["payload"]["type"], "stratum": strata[doc_id],
                         "doc_id": doc_id, "text": name, "grounding_span": span,
                         "extra": item, "window": cp.window_for(norm, span)})
    return recs


def yield_by_stratum() -> dict[str, dict]:
    """Admitted node items per chunk, per stratum — Phase C's monitoring bands.

    Report only. ADDENDUM-06 §2: the 45.23 comparator does not exist off the pilot documents
    and is not manufactured here, and the 5.16 ground-truth floor is qualification evidence,
    not a burn-time bar (task's binding facts). So this returns means and spreads, and no
    verdict."""
    strata = document_strata()
    per_chunk = collections.defaultdict(list)
    for chunk_id, counts in cp.chunk_yield(cp.TAG).items():
        doc_id = chunk_id.split("#")[0]
        if doc_id in strata:
            per_chunk[strata[doc_id]].append(counts.get("nodes", 0))
    out = {}
    for stratum, vals in sorted(per_chunk.items()):
        mean = sum(vals) / len(vals)
        var = sum((v - mean) ** 2 for v in vals) / (len(vals) - 1) if len(vals) > 1 else 0.0
        # ADDENDUM-01 §3.3: the envelope, NOT +/-3 sd. `agency_framework`'s +/-3 sd band was
        # -30 to +58 — a band that cannot flag anything, and a negative floor on a count.
        # Every stratum uses the same convention so the flags are comparable, and the label
        # says what it is: decoration at n = 7-8, gating nothing. The operative monitor is the
        # faithfulness SPRT (ADDENDUM-06 §2 unchanged).
        out[stratum] = {"chunks": len(vals), "mean_nodes_per_chunk": round(mean, 3),
                        "sd": round(math.sqrt(var), 3), "min": min(vals), "max": max(vals),
                        "envelope_low": min(vals), "envelope_high": max(vals),
                        "basis": f"observed min-max over {len(vals)} chunks; report-only, "
                                 f"gates nothing"}
    return out


class GateUnreadable(RuntimeError):
    """The aggregate does not carry a number the gate needs."""


def gate_inputs(agg: dict) -> tuple[float, float, int]:
    """(F_upper, item-faithful, facts) out of a probe aggregate, or refuse.

    Refusing is the point. The first version of this read `pooled["F_upper"]` and
    `pooled["item_faithful"]`, which are not the aggregator's key names; both came back None,
    the comparison `None < 0.10` was skipped, and the gate reported **FAIL** on a run whose
    real numbers PASS. A verdict function that cannot read its instrument must say so, not
    resolve to the conservative-looking answer — that is DD-028's defect wearing a safe face."""
    pooled = agg.get("pooled") or {}
    items = agg.get("items") or {}
    missing = [k for k, src in (("pooled.F_hi", pooled.get("F_hi")),
                                ("items.faithful_rate", items.get("faithful_rate")),
                                ("pooled.n_facts", pooled.get("n_facts"))) if src is None]
    if missing:
        raise GateUnreadable(
            f"probe aggregate is missing {missing}; the gate cannot be read from it. "
            f"Present keys: pooled={sorted(pooled)}, items={sorted(items)}")
    return float(pooled["F_hi"]), float(items["faithful_rate"]), int(pooled["n_facts"])


def gate_verdict(f_upper: float, item_faithful: float, n_facts: int, min_facts: int) -> str:
    if n_facts < min_facts:
        return "GATE UNREACHABLE"
    return "PASS" if (f_upper < cp.F_STOP and item_faithful >= cp.ITEM_FAITHFUL) else "FAIL"


def phase_judge(a) -> int:
    payload = bind_confirmation_run()
    cfg = model_stub.load_model_config()
    m = cp.members()
    texts = {d: rbe.doc_text(m[d]) for d in cp.DOCS}
    recs = bulk_records(texts)
    min_facts = cp.min_facts_for_gate()

    bands = yield_by_stratum()
    print("\n=== Phase A yield (report only; no floor verdict) ===")
    for s, r in bands.items():
        print(f"  {s:<24} chunks {r['chunks']:>3}  mean {r['mean_nodes_per_chunk']:>7} "
              f"sd {r['sd']:>7}  range {r['min']}-{r['max']}")

    by_stratum = collections.Counter(r["stratum"] for r in recs)
    print(f"\n=== pre-judge census: {len(recs)} admitted node items "
          f"(gate needs >= {min_facts} facts pooled) ===")
    for s, n in sorted(by_stratum.items()):
        print(f"  {s:<24} {n:>5} items")
    if not recs:
        print("GATE UNREACHABLE: no admitted node items to judge.")
        return 2

    if not a.ceiling_tokens:
        raise SystemExit("FATAL: --ceiling-tokens required before any model call (DD-022)")
    spend.default_ledger().declare(JUDGE_RUN_ID, a.ceiling_tokens, declared_by=TASK,
                                   call_class="judge")
    spend.set_current_run(JUDGE_RUN_ID)
    raters = [cfg["primary_judge_model_id"], cfg["secondary_judge_model_id"]]
    prefix = "bulk_v038_phase_a"
    cp.write_sample(prefix, recs)
    agg = cp.run_protocol(prefix, prefix, JUDGE_RUN_ID, raters, a.fact_cap)
    if not agg:
        print("FATAL: probe protocol failed")
        return 2

    f_upper, item_faithful, n_facts = gate_inputs(agg)
    verdict = gate_verdict(f_upper, item_faithful, n_facts, min_facts)
    out = {"task": TASK, "profile": PROFILE, "seed": payload["seed"],
           "chunks": payload["drawn_total"], "documents": len(cp.DOCS),
           "admitted_node_items": len(recs), "by_stratum": dict(by_stratum),
           "min_facts_for_gate": min_facts, "facts_judged": n_facts,
           "F_upper": f_upper, "item_faithful": item_faithful,
           "thresholds": {"F_upper<": cp.F_STOP, "item_faithful>=": cp.ITEM_FAITHFUL},
           "verdict": verdict, "yield_bands": bands, "aggregate": agg, "judged_at": now()}
    (STATE_DIR / "bulk_v038_phase_a.json").write_text(json.dumps(out, indent=1) + "\n",
                                                      encoding="utf-8")
    print(f"\n=== Phase A gate (pooled): {verdict} ===")
    print(f"  F_upper {f_upper} (< {cp.F_STOP})   item-faithful {item_faithful} "
          f"(>= {cp.ITEM_FAITHFUL})   facts {n_facts} (>= {min_facts})")
    return 0 if verdict == "PASS" else 1


# ---------------------------------------------------------------- Phase C — the burn
BATCH_MIN_CHUNKS = 40          # DD-019 dispatch unit: enough output to sample from
CEILING_HEADROOM = 1.3         # task: 1.3 x running mean settled tokens/chunk
LEDGER_WINDOW = 10             # ... over the ledger's last 10 measured settles


def document_chunk_counts() -> dict[str, int]:
    paths = document_paths()
    out = {}
    for doc_id in burn_set():
        path = paths.get(doc_id)
        if path and readable(path):
            out[doc_id] = len(chunker.chunk_document(doc_id, rbe.doc_text(path)))
    return out


def batches(worklist: list[str], counts: dict[str, int]) -> list[dict]:
    """Group the worklist into dispatch batches of >= BATCH_MIN_CHUNKS, in worklist order.

    A document is never split across batches: the acceptance verdict quarantines a batch's
    events, and half a document in the graph is worse than none. The final batch may be short
    — padding it by reordering would break the priority order Phase 0.4 established."""
    out, cur, n = [], [], 0
    for doc_id in worklist:
        # `not counts.get(...)` also drops a document with ZERO chunks left after the resume:
        # it would otherwise ride along in a batch's document list, be reported as burned, and
        # contribute nothing — a batch claiming work it did not do.
        if not counts.get(doc_id):
            continue
        cur.append(doc_id)
        n += counts[doc_id]
        if n >= BATCH_MIN_CHUNKS:
            out.append({"documents": cur, "chunks": n})
            cur, n = [], 0
    if cur:
        out.append({"documents": cur, "chunks": n})
    for i, b in enumerate(out, start=1):
        b["batch_id"] = f"bulk_v038_b{i:03d}"
    return out


def mean_settled_per_chunk(default: float) -> float:
    """Running mean settled tokens per chunk over the ledger's last LEDGER_WINDOW settles for
    this profile's runs. Bootstrapped from Phase A's mean when the ledger has none."""
    path = REPO / "state/spend_ledger.jsonl"
    if not path.is_file():
        return default
    settles = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        if r.get("record") == "settle" and str(r.get("run_id", "")).startswith("bulk_v038") \
                and r.get("actual_tokens"):
            settles.append(int(r["actual_tokens"]))
    if not settles:
        return default
    window = settles[-LEDGER_WINDOW:]
    return sum(window) / len(window)


def batch_ceiling(chunks: int, default_per_chunk: float) -> tuple[int, float]:
    per = mean_settled_per_chunk(default_per_chunk)
    return int(math.ceil(CEILING_HEADROOM * per * chunks)), per


def phase_a_mean_per_chunk() -> float:
    """Phase A's measured settled tokens per chunk — the bootstrap for batch 1's ceiling."""
    payload = confirmation_sample()
    per = mean_settled_per_chunk(0.0)
    if per:
        return per
    raise SystemExit("FATAL: no bulk_v038 settles on the ledger; Phase A must run before "
                     f"a batch ceiling can be derived ({payload['drawn_total']} chunks drawn)")


# ---------------------------------------------------------------- acceptance sampling
def batch_items(batch_id: str) -> list[dict]:
    """Admitted node items belonging to one batch, from the shard."""
    nodes, _e, _s = cp.shard_items()
    out = []
    for doc_id, evs in nodes.items():
        for ev in evs:
            if (ev.get("provenance") or {}).get("batch_id") == batch_id:
                out.append(ev)
    return out


def sample_for_batch(batch_id: str, items: list[dict], budget: int) -> list[dict]:
    """Seeded random sample of admitted items, drawn from the LIVE shard, never from a file.

    Seeded on the batch id so the draw is reproducible and stated; drawn from `items` — which
    `batch_items` reads out of the event log — because a sampler that reads a committed
    artifact reports on the artifact, not on what the burn actually produced. That defect has
    six recorded instances in this project."""
    rng = random.Random(f"bulk_v038_sample:{batch_id}")
    if len(items) <= budget:
        return list(items)
    return rng.sample(items, budget)


def yield_flag(stratum_mean: float, band: dict | None) -> str | None:
    """A report-only flag when a batch's per-stratum mean falls outside Phase A's observed
    envelope. Returns None (no flag) when there is no band, and never for a zero:

    ADDENDUM-01 §3.4 — a zero-yield chunk is HEALTHY. Bibliographies, navigation blocks and
    front matter legitimately contain nothing extractable, and every Phase A stratum contained
    at least one. A monitor that treats 0 as an anomaly fires constantly on correct output,
    and a monitor that cries wolf is worse than no monitor."""
    if not band:
        return None
    lo, hi = band["envelope_low"], band["envelope_high"]
    if stratum_mean < lo:
        return f"below Phase A envelope ({stratum_mean:.2f} < {lo})"
    if stratum_mean > hi:
        return f"above Phase A envelope ({stratum_mean:.2f} > {hi})"
    return None


class BurnState:
    """Rolling accept/reject history and the corpus stop rule (DD-029)."""

    def __init__(self):
        self.outcomes: list[str] = []

    def record(self, outcome: str) -> None:
        self.outcomes.append(outcome)

    def should_stop(self) -> str | None:
        bad = {"reject", "sampling_inconclusive"}
        if len(self.outcomes) >= 2 and self.outcomes[-1] == "reject" \
                and self.outcomes[-2] == "reject":
            return "2 consecutive rejects"
        window = self.outcomes[-5:]
        if sum(1 for o in window if o in bad) >= 3:
            return f"3 rejects/inconclusives in the last {len(window)} batches"
        return None


def quarantine_batch(batch_id: str, reason: str, evidence: dict) -> str:
    return eventlog.append({"event_type": "bulk_batch_quarantined", "purpose": PROFILE,
                            "batch_id": batch_id, "reason": reason, "evidence": evidence,
                            "task": TASK, "ts": now()}, batch=cp.SHARD_NO)


def judge_run_id(batch_id: str) -> str:
    """One judge ledger run PER BATCH. A single shared judge run would put 13 batches' worth
    of judging — ~6,000 facts at two raters — under one ceiling, and the guard would refuse
    batch 2 onwards for having spent batch 1's budget."""
    return f"{RUN_ID}_{batch_id}_judge"


def judge_batch(batch_id: str, items: list[dict], texts: dict[str, str],
                budget: int, raters: list[str], fact_cap: int) -> dict:
    """Draw, decompose, judge, decide. Returns the SPRT verdict and its evidence."""
    b = sprt_boundaries()
    sample = sample_for_batch(batch_id, items, budget)
    strata = document_strata()
    recs = []
    for ev in sample:
        item = ev["payload"]["item"]
        name = item.get("name") or item.get("term") or item.get("text") or ""
        span = item.get("grounding_span") or ""
        doc_id = ev["doc_id"]
        recs.append({"item_id": f"{ev['chunk_id']}:{ev['payload']['id']}",
                     "event_id": ev["event_id"], "kind": "node",
                     "type": ev["payload"]["type"],
                     "stratum": strata.get(doc_id, "unstratified"), "doc_id": doc_id,
                     "text": name, "grounding_span": span, "extra": item,
                     "window": cp.window_for(cp.grounding.normalize(texts[doc_id]), span)})
    prefix = f"burn_{batch_id}"
    cp.write_sample(prefix, recs)
    agg = cp.run_protocol(prefix, prefix, judge_run_id(batch_id), raters, fact_cap)
    if not agg:
        return {"outcome": "protocol_failed", "batch_id": batch_id}
    pooled = agg.get("pooled") or agg
    facts = int(pooled.get("facts") or pooled.get("n_facts") or 0)
    fabrications = int(pooled.get("fabrications") or pooled.get("unfaithful") or 0)
    decision = sprt_decide(fabrications, facts, b)
    if decision == "continue" and facts >= budget:
        decision = "sampling_inconclusive"
    return {"outcome": decision, "batch_id": batch_id, "facts": facts,
            "fabrications": fabrications, "items_sampled": len(sample),
            "items_available": len(items), "aggregate": agg}


def resume_plan() -> tuple[list[str], dict[str, int], int]:
    """(worklist, chunks REMAINING per document, chunks already extracted).

    ADDENDUM-01 §3.1: chunk-level resume. Phase A's 30 chunks are already extracted and in the
    graph; no chunk runs twice under the same profile. `chunk_coverage` derives what is done
    from `chunk_metrics` events — the ledger — not from a file and not by counting raws on
    disk, so a resume cannot be fooled by a stray directory."""
    counts = document_chunk_counts()
    work = [d for d in queue.worklist(PROFILE) if d in counts]
    done = queue.chunk_coverage(PROFILE)
    remaining = {d: max(0, counts[d] - len(done.get(d, ()))) for d in work}
    return work, remaining, sum(len(done.get(d, ())) for d in work)


def phase_burn(a) -> int:
    apply_production_profile(RUN_ID)
    b = sprt_boundaries()
    n_min = min_facts_for_accept(b)
    budget = int(math.ceil(2 * expected_sample_number(b, b["slope"])))
    cfg = model_stub.load_model_config()
    raters = [cfg["primary_judge_model_id"], cfg["secondary_judge_model_id"]]

    work, remaining, already = resume_plan()
    plan = batches(work, remaining)
    print(f"burn plan: {len(work)} documents, {sum(remaining.values())} chunks to extract "
          f"({already} already extracted under {PROFILE}, resumed not repeated), "
          f"{len(plan)} batches; sample budget {budget} facts/batch, accept needs "
          f">= {n_min}")
    for bt in plan:
        print(f"  {bt['batch_id']}  {len(bt['documents']):>2} docs  "
              f"{bt['chunks']:>4} chunks")
    if a.plan_only:
        return 0

    boot = phase_a_mean_per_chunk()
    phase_a_bands = json.loads((STATE_DIR / "bulk_v038_phase_a.json").read_text(
        encoding="utf-8")).get("yield_bands", {}) if (
        STATE_DIR / "bulk_v038_phase_a.json").is_file() else {}
    state = BurnState()
    ledger_rows = []
    for bt in plan[: a.max_batches] if a.max_batches else plan:
        bid = bt["batch_id"]
        ceiling, per = batch_ceiling(bt["chunks"], boot)
        run_id = f"{RUN_ID}_{bid}"
        print(f"\n=== {bid}: {len(bt['documents'])} docs, {bt['chunks']} chunks, "
              f"ceiling {ceiling:,} (1.3 x {per:,.0f}/chunk)", flush=True)
        spend.default_ledger().declare(run_id, ceiling, declared_by=TASK,
                                       call_class="extraction_chunk")
        cp.DOCS = list(bt["documents"])
        # The extractor already skips a chunk whose raw exists; the resume above is what keeps
        # an already-extracted chunk out of the batch SIZE and therefore out of the ceiling.
        cp.CHUNK_FILTER = None
        cp.BATCH_ID = bid
        cp.RUN_ID = run_id
        spend.set_current_run(run_id)
        rc = cp.phase_extract(type("A", (), {"shared_with": None, "only": None,
                                             "limit": None, "workers": a.workers})())
        if rc != 0:
            print(f"{bid}: extraction returned {rc}; stopping the burn.")
            return rc
        cp.phase_ingest(type("A", (), {"reingest": False})())

        m = cp.members()
        texts = {d: rbe.doc_text(m[d]) for d in cp.DOCS}
        items = batch_items(bid)
        if len(items) < n_min:
            verdict = {"outcome": "sampling_inconclusive", "batch_id": bid,
                       "items_available": len(items),
                       "why": f"{len(items)} admitted items < {n_min} facts needed for a "
                              f"decision; the plan cannot settle this batch"}
        else:
            spend.default_ledger().declare(judge_run_id(bid), a.judge_ceiling,
                                           declared_by=TASK, call_class="judge")
            verdict = judge_batch(bid, items, texts, budget, raters, a.fact_cap)
        # Report-only yield flags against Phase A's envelope (ADDENDUM-01 §3.3). Computed
        # AFTER the verdict and never fed into it.
        flags = {}
        for stratum, r in yield_by_stratum().items():
            f = yield_flag(r["mean_nodes_per_chunk"], phase_a_bands.get(stratum))
            if f:
                flags[stratum] = f
        if flags:
            print(f"{bid}: yield flags (report-only, gate nothing): {flags}")
        verdict["yield_flags"] = flags
        state.record(verdict["outcome"])
        if verdict["outcome"] == "reject":
            quarantine_batch(bid, "SPRT reject boundary crossed", verdict)
            print(f"{bid}: REJECT — shard quarantined out of the projection")
        print(f"{bid}: {verdict['outcome']}")
        ledger_rows.append(verdict)
        stop = state.should_stop()
        if stop:
            print(f"\nCORPUS STOP: {stop}. Incident-class report; burn halted.")
            break
    out = {"task": TASK, "profile": PROFILE, "batches": ledger_rows,
           "outcomes": state.outcomes, "stopped": state.should_stop(),
           "sprt": b, "sample_budget": budget, "min_facts_for_accept": n_min,
           "ran_at": now()}
    (STATE_DIR / "bulk_v038_burn.json").write_text(json.dumps(out, indent=1) + "\n",
                                                   encoding="utf-8")
    return 0


PHASES = {"cut": phase_cut, "sprt": phase_sprt, "sample": phase_sample,
          "extract": phase_extract, "ingest": phase_ingest, "judge": phase_judge,
          "burn": phase_burn}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--phase", required=True, choices=sorted(PHASES))
    ap.add_argument("--commit", action="store_true",
                    help="cut: actually emit the queue events (default is a dry run)")
    ap.add_argument("--ceiling-tokens", type=int, default=None)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--reingest", action="store_true")
    ap.add_argument("--plan-only", action="store_true",
                    help="burn: print the batch plan and stop, no spend")
    ap.add_argument("--max-batches", type=int, default=None)
    ap.add_argument("--judge-ceiling", type=int, default=2_000_000)
    ap.add_argument("--fact-cap", type=int, default=40,
                    help="max facts judged per stratum; a cap widens the interval, which "
                         "makes PASS harder, never easier")
    a = ap.parse_args()
    model_stub.guard_no_api_key()
    return PHASES[a.phase](a)


if __name__ == "__main__":
    raise SystemExit(main())
