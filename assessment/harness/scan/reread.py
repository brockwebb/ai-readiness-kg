"""Re-read a stored Observation's retained body for the parsed blocks its collector now adds.
**No network, no model, no clock.**

`cc_tasks/2026-09-18_rejudge_seven_legs.md` decision 1. Generations 11 to 13 added three blocks
that the collector computes from a body it has already fetched:

* `D4.parsed.dcat_fields`: the DCAT-US field profile of the product's records
  (`v2clauses.dcat_record_fields`, which `RULE-B1-v2`, `B4-v1`, `D3-v1` and `G4-v1` read);
* `D4.parsed.membership`: the DCAT-US URL-field membership count (`dcat.membership_block`,
  which `RULE-D4-v3` reads);
* `A4.parsed.content_signal`: the `Content-Signal` directives in robots.txt
  (`v2clauses.content_signals`, which `RULE-D2-v1` reads).

Every Observation of every stored cycle predates all three blocks, so each of those rules
returns `error` over it: "stored before the block existed". The bytes the blocks are computed
from are retained, though. They are content-addressed under `corpus/evidence/scan/`, and the
Observation on the log names their sha256. So this module does offline, at re-judgement time,
exactly what `runner.collect_leg` and `dcat.fetch_catalog` do at collection time, calling the
same functions with the same arguments.

**Why this is a re-judgement and not a new measurement.** Nothing is fetched, and no
Observation is created or re-identified. `obs_id` is derived from the leg, the target, the
collector, the params and the body's sha256, and never from `parsed`
(`model.Observation.make`). Every Finding therefore cites exactly the `obs_id`s already on the
log. What is new is a parse of evidence the log already holds. The prior art is ordinary
re-analysis of retained raw data under a corrected reader, the licence `rederive.py`'s
re-judgement section already cites. It is also the split DD-052 draws: an Observation is
evidence, and anything computed from its retained bytes is derivable.

**Why the re-derivation gate stays a real test (DD-041).** A payload judged over re-read
Observations records `observations_reread` (below). `rederive.observations_for` sees that key
and applies this same function before judging, so the gate re-derives from the same bytes
through the same code. A payload without the key is re-derived exactly as before, which keeps
every prior payload's gate untouched.

**Fail loud on the evidence.** A body whose bytes do not hash to the sha256 on the
Observation is not the body the Observation names. That raises; it is never read. A body that
is missing also raises, because a block silently left off would turn into `error` verdicts
that look like a scope limitation and are really a lost file.

**Only absent keys are filled.** A block the collector already recorded is the record, and it
is never overwritten. That matters for cycle 5 onwards: an Observation collected with the
blocks passes through unchanged, and the function is a no-op.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

from .collectors import dcat, v2clauses

#: The shape of the `observations_reread` record a payload carries. A reader checks it before
#: trusting any key, as the rules check `DCAT_FIELDS_SCHEME` and `CONTENT_SIGNAL_SCHEME`.
REREAD_SCHEME = 1

#: Which blocks are re-read, per leg. Named once so the record on the payload and the code that
#: fills the blocks cannot disagree about what was done.
BLOCKS = {"D4": ("membership", "dcat_fields"), "A4": ("content_signal",)}


class RetainedBodyError(RuntimeError):
    """The body an Observation names is missing, or its bytes are not the ones it names."""


def _repo_root() -> Path:
    from .manners import repo_root
    return repo_root()


def _retained_body(row: dict) -> bytes:
    resp = row.get("response") or {}
    rel, want = resp.get("body_path"), resp.get("body_sha256")
    if not rel or not want:
        raise RetainedBodyError(
            f"{row['obs_id']} ({row['leg']}, {row['target_doc_id']}) records a served body "
            f"but names no body_path/body_sha256; there is nothing to re-read")
    path = _repo_root() / rel
    if not path.is_file():
        raise RetainedBodyError(
            f"{row['obs_id']} ({row['leg']}, {row['target_doc_id']}): the retained body "
            f"{rel} is not on disk. A block left off here would be read as a scope "
            f"limitation, and it would really be a lost file.")
    body = path.read_bytes()
    got = hashlib.sha256(body).hexdigest()
    if got != want:
        raise RetainedBodyError(
            f"{row['obs_id']}: {rel} hashes to {got[:16]}…, and the Observation names "
            f"{want[:16]}…. It is not the body the Observation cites, so it is not read.")
    return body


def _d4(parsed: dict, body: bytes, product_url: str, params: dict) -> tuple:
    """`dcat.fetch_catalog`'s `membership` and `runner.collect_leg`'s `dcat_fields`, with the
    same parse and the same failure branches as each of them."""
    added = []
    try:
        doc = json.loads(body.decode("utf-8", "replace"))
    except Exception as exc:  # noqa: BLE001 — both callers catch exactly this breadth
        # `fetch_catalog` records a parse failure as `error: parse_error` and computes no
        # membership. `collect_leg` records `dcat_fields` as unparsed. Both are mirrored here.
        if "dcat_fields" not in parsed:
            parsed["dcat_fields"] = {"scheme": v2clauses.DCAT_FIELDS_SCHEME, "parsed": False,
                                     "reason": f"{type(exc).__name__}: {exc}"}
            added.append("dcat_fields")
        return parsed, added
    if "membership" not in parsed:
        datasets = doc.get("dataset") if isinstance(doc, dict) else None
        datasets = datasets if isinstance(datasets, list) else []
        parsed["membership"] = dcat.membership_block(datasets, product_url, params)
        added.append("membership")
    if "dcat_fields" not in parsed:
        parsed["dcat_fields"] = v2clauses.dcat_record_fields(doc, product_url, params)
        added.append("dcat_fields")
    return parsed, added


def _a4(parsed: dict, body: bytes, product_url: str, params: dict) -> tuple:
    if "content_signal" in parsed:
        return parsed, []
    parsed["content_signal"] = v2clauses.content_signals(body, product_url, params)
    return parsed, ["content_signal"]


def reread(rows: list, urls: dict, params: dict) -> tuple:
    """`(rows', record)`: deep copies of `rows` with the absent blocks filled from each
    Observation's retained body, and the record of what was filled.

    `urls` is `{doc_id: surface URL}`, the URL `run.py` passed to `collect_leg` for that row
    (the cycle's matrix `url`). D4's membership and A4's path scoping are both functions of the
    PRODUCT URL, and the Observation's own `target_url` is the catalog's or the robots file's.

    The input is never mutated. The rows are the stored payload's, and the payload is
    immutable.
    """
    out, counts = [], {leg: {b: 0 for b in blocks} for leg, blocks in BLOCKS.items()}
    for row in rows:
        leg = row.get("leg")
        parsed = row.get("parsed")
        if leg not in BLOCKS or not isinstance(parsed, dict) or not parsed.get("present"):
            # The collectors attach nothing when no document was served, so neither does this.
            out.append(copy.deepcopy(row))
            continue
        if all(b in parsed for b in BLOCKS[leg]):
            out.append(copy.deepcopy(row))
            continue
        doc_id = row["target_doc_id"]
        if doc_id not in urls or not urls[doc_id]:
            raise RetainedBodyError(
                f"{row['obs_id']} ({leg}, {doc_id}): no surface URL for the row. The block is "
                f"a function of the product URL, and guessing it would be a different reading")
        body = _retained_body(row)
        new = copy.deepcopy(row)
        fill = _d4 if leg == "D4" else _a4
        new["parsed"], added = fill(dict(new["parsed"]), body, urls[doc_id], params)
        for b in added:
            counts[leg][b] += 1
        out.append(new)
    record = {
        "scheme": REREAD_SCHEME,
        "blocks": {leg: list(b) for leg, b in BLOCKS.items()},
        "observations_reread": counts,
        "functions": ["scan.collectors.dcat.membership_block",
                      "scan.collectors.v2clauses.dcat_record_fields",
                      "scan.collectors.v2clauses.content_signals"],
        "product_url_from": "the payload's matrix row `url` for the Observation's target",
        "note": ("Blocks the collector now computes at collection were computed here, from each "
                 "Observation's retained, content-addressed body, and the sha256 was checked "
                 "first. No byte was fetched, no Observation was created, and no obs_id "
                 "changed. `rederive.observations_for` applies the same re-read, so the "
                 "re-derivation gate judges exactly what this payload judged."),
    }
    return out, record
