"""Observation and Finding — the evidence-first record types. **No network, no model calls.**

Task `cc_tasks/2026-09-06_harness_scaffold.md` §2.1, §3. Skeleton §6b.5: *"the instrument
stores raw observed facts separately from calculated warnings; warnings are produced by
deterministic, versioned rules so thresholds can change and history can be re-scored without
re-measurement."*

Prior art: OSCAL's assessment-results (observations are facts, findings are judgements over
them) and Lighthouse's `artifacts` / `audits` split — gather once, audit many times. F-UJI
(Devaraju & Huber 2021) for the metric → tests → evidence shape: every test records the
evidence it saw.

**A Finding's id is derived, never assigned.** `sha256(rule_id | rule_version | sorted obs_ids
| params_hash)`. That is what makes §3's re-derivation gate checkable: delete every Finding,
re-run every rule from stored Observations, and the output must be byte-identical. An id from
a counter or a clock would make the gate vacuous.
"""
from __future__ import annotations

import dataclasses
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[3]
#: Content-addressed evidence store. Whole bodies, never truncated (§2.1).
EVIDENCE_ROOT = REPO / "corpus" / "evidence" / "scan"

#: The closed set, defined once in `errors.py` beside the rule that resolves each class and
#: the flag saying whether it means "we did not observe". Re-exported here because the
#: dataclass validates against it and every collector already imports this module.
from .errors import ERROR_CLASSES                                    # noqa: E402
VERDICTS = ("pass", "fail", "not_applicable", "error")


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def params_hash(params: dict) -> str:
    """Stable hash of the whole parameter set. Rides on every Observation and every Finding,
    so a record always names the constants that shaped it."""
    return sha256_bytes(json.dumps(params, sort_keys=True, separators=(",", ":")).encode())


def store_evidence(body: bytes, root: Path | None = None) -> tuple:
    """(sha256, path-relative-to-repo). Content-addressed, so identical bodies are stored once
    and a stored body can always be verified against the hash a Finding cites."""
    root = root or EVIDENCE_ROOT
    digest = sha256_bytes(body)
    path = root / digest[:2] / digest
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_bytes(body)
    try:
        return digest, str(path.relative_to(REPO))
    except ValueError:
        return digest, str(path)


@dataclasses.dataclass
class Observation:
    """One raw fact captured against a surface. Stored BEFORE anything is scored."""
    obs_id: str
    spec_code: str
    leg: str
    target_doc_id: str
    target_url: str
    captured_at: str
    collector: str
    collector_version: str
    params_hash: str
    request: dict
    response: dict
    parsed: Any = None
    error_class: str | None = None

    def __post_init__(self) -> None:
        if self.error_class not in ERROR_CLASSES:
            raise ValueError(f"error_class {self.error_class!r} outside the closed set "
                             f"{ERROR_CLASSES}")

    @staticmethod
    def make(spec_code: str, leg: str, target_doc_id: str, target_url: str, collector: str,
             collector_version: str, params: dict, request: dict, response: dict,
             parsed: Any = None, error_class: str | None = None,
             captured_at: str | None = None) -> "Observation":
        ph = params_hash(params)
        captured_at = captured_at or now_utc()
        # The id is derived from WHAT was observed and under WHICH parameters, never from a
        # counter: two collectors observing the same URL under the same params for the same
        # leg produce the same id, which is what makes a re-run idempotent.
        obs_id = "obs_" + sha256_bytes(
            "|".join([leg, target_doc_id, target_url, collector, collector_version, ph,
                      str(response.get("body_sha256")), str(error_class)]).encode())[:24]
        return Observation(obs_id=obs_id, spec_code=spec_code, leg=leg,
                           target_doc_id=target_doc_id, target_url=target_url,
                           captured_at=captured_at, collector=collector,
                           collector_version=collector_version, params_hash=ph,
                           request=request, response=response, parsed=parsed,
                           error_class=error_class)

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


@dataclasses.dataclass
class Finding:
    """A verdict over Observations under a versioned rule. Pure output of `judge`."""
    finding_id: str
    rule_id: str
    rule_version: str
    spec_code: str
    leg: str
    target_doc_id: str
    verdict: str
    evidence: list
    reason: str
    params_hash: str
    #: How much of the evidence the rule could NOT see, as FIELDS rather than prose
    #: (`cc_tasks/2026-09-08_a8_v4_blind_pointer_and_fixture_table.md` decision 3, closing
    #: `cc_tasks/2026-09-08_scan_run_3_RESULT.md` §4.3: the counts lived only in the reason
    #: string, so registering them meant parsing prose).
    #:
    #: **Omitted from `to_dict` when unset**, and that is what keeps history re-derivable. A
    #: Finding recorded before these fields existed carries neither key; a re-judgement of it
    #: under its own rule sets neither; the two dicts are equal and the byte-identical gate
    #: still means what it meant. They are NOT inputs to `finding_id` — `make` hashes
    #: rule_id | rule_version | target | params_hash | sorted evidence and nothing else — so no
    #: stored Finding is re-identified by their existence.
    blind_links: int | None = None
    blind_pointers: int | None = None

    def __post_init__(self) -> None:
        if self.verdict not in VERDICTS:
            raise ValueError(f"verdict {self.verdict!r} outside {VERDICTS}")

    @staticmethod
    def make(rule_id: str, rule_version: str, leg: str, target_doc_id: str, verdict: str,
             evidence: list, reason: str, params: dict, spec_code: str | None = None,
             blind_links: int | None = None,
             blind_pointers: int | None = None) -> "Finding":
        ph = params_hash(params)
        ev = sorted(evidence)
        # The id inputs are UNCHANGED by the blind counts. They describe how much the rule
        # could see, not what it judged, and folding them in would re-identify every stored
        # Finding the moment a rule started reporting them.
        fid = "fnd_" + sha256_bytes(
            "|".join([rule_id, rule_version, target_doc_id, ph] + ev).encode())[:24]
        return Finding(finding_id=fid, rule_id=rule_id, rule_version=rule_version,
                       spec_code=spec_code or leg.split("-")[0], leg=leg,
                       target_doc_id=target_doc_id, verdict=verdict, evidence=ev,
                       reason=reason, params_hash=ph, blind_links=blind_links,
                       blind_pointers=blind_pointers)

    def to_dict(self) -> dict:
        """The record. A blind count that was never set is ABSENT, not `null`: a Finding made
        before these fields existed must produce the same dict it produced then, or the
        byte-identical re-derivation gate would fail for every prior cycle on a key nobody
        wrote."""
        d = dataclasses.asdict(self)
        for k in ("blind_links", "blind_pointers"):
            if d.get(k) is None:
                d.pop(k, None)
        return d
