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
import os
import sys
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

#: Surface ids that are SYNTHETIC by construction: there is no `:Document` for them and none is
#: required, so an Observation carrying one is not an integrity failure.
#:
#: **Defined once, here, because a second copy is how this broke.** The list lived in
#: `publish.py`; `cc_tasks/2026-09-08_scan_run_3b.md` decision 3 added `home:` and `machine:` to
#: the id scheme, one copy learned about them and the other did not, and 957 observations of
#: perfectly ordinary host-level surfaces were counted as missing Documents. A prefix list that
#: lags the id scheme turns the integrity check into a counter of its own staleness. There were
#: three copies when `flagship:` was added; there is one now, and `publish.py`, `run.py` and the
#: target builders all read it.
#:
#: `host:` is the well-known row and keeps its spelling for continuity with three cycles of A12
#: Results. `flagship:` is `cc_tasks/2026-09-10_scan_frame_v5.md`: an operator-declared product
#: landing page with no corpus Document behind it, which is the ordinary case for a declaration
#: made after the corpus was frozen.
SYNTHETIC_PREFIXES = ("host:", "home:", "machine:", "flagship:")


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def params_hash(params: dict) -> str:
    """Stable hash of the whole parameter set. Rides on every Observation and every Finding,
    so a record always names the constants that shaped it."""
    return sha256_bytes(json.dumps(params, sort_keys=True, separators=(",", ":")).encode())


#: Set by the cycle runner, and by nothing else, for the duration of a cycle. Its presence is
#: what licenses a write into the COMMITTED evidence store.
CYCLE_TOKEN_ENV = "AIRKG_SCAN_CYCLE"

#: Where a write that is not part of a cycle goes instead. It is the same quarantine lane the
#: sweep already uses, so the litter lands where the tool that cleans it looks.
SCRIPT_QUARANTINE = REPO / "corpus" / "quarantine" / "evidence_scan_fixture" / "unlicensed"

#: Every redirect, appended here so the redirect is a record and not a silence.
REDIRECT_LOG = SCRIPT_QUARANTINE / "redirects.jsonl"


#: The lane the guard protects. `corpus/evidence/` and everything under it.
COMMITTED_EVIDENCE = REPO / "corpus" / "evidence"


def _under_committed_store(root: Path) -> bool:
    """Whether a write to `root` would land in the committed evidence store.

    **This, and not "the caller passed no root", is the condition decision 3 states.** The
    first implementation keyed on `root is None`, which redirected any defaulted write no
    matter where `EVIDENCE_ROOT` pointed — so a caller that had deliberately repointed the
    module global to a staging directory got its bytes sent to quarantine instead, and
    `tests/conftest.py`'s autouse redirect and `--evidence-root` were both defeated by the
    guard meant to sit beside them. A guard that fires on the wrong condition protects the
    wrong thing.
    """
    try:
        Path(root).resolve().relative_to(COMMITTED_EVIDENCE.resolve())
        return True
    except ValueError:
        return False


def _cycle_licensed() -> bool:
    """Whether this process is the cycle runner. `run.py` sets the token; nothing else does."""
    return bool(os.environ.get(CYCLE_TOKEN_ENV))


def _redirect_root(root: Path, why: str) -> Path:
    """Send an unlicensed write to quarantine and LOG that it was sent.

    `cc_tasks/2026-09-09_manners_closeout.md` decision 3. `corpus/evidence/scan/` is the one
    `corpus/` lane the repo commits, and twice in two consecutive tasks a fixture driver run
    from a script filled it with loopback bodies that no Observation cited. The standing guard
    is `tests/conftest.py`, which redirects the store under pytest and cannot see a script.

    A refusal would have been the wrong shape: the caller is usually a collector deep inside a
    driver, it has no way to choose another root, and raising would turn "you wrote litter"
    into "your script crashed". Redirecting keeps the driver working and puts the bytes where
    the sweep already looks; logging is what stops the redirect being a silence.
    """
    SCRIPT_QUARANTINE.mkdir(parents=True, exist_ok=True)
    rec = {"at": datetime.now(timezone.utc).isoformat(),
           "requested_root": str(root), "redirected_to": str(SCRIPT_QUARANTINE),
           "why": why, "argv": " ".join(sys.argv)[:400]}
    with REDIRECT_LOG.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, sort_keys=True) + "\n")
    return SCRIPT_QUARANTINE


def store_evidence(body: bytes, root: Path | None = None) -> tuple:
    """(sha256, path-relative-to-repo). Content-addressed, so identical bodies are stored once
    and a stored body can always be verified against the hash a Finding cites.

    **A write into the committed store requires a cycle** (decision 3). The guard fires on
    where the bytes would LAND, not on whether the caller named a root: a write aimed at
    `corpus/evidence/` from a process the cycle runner did not start is redirected to
    quarantine and the redirect is logged. A root pointing anywhere else — a staging
    directory, a tmp_path, whatever `tests/conftest.py` substitutes — is honoured untouched,
    because there is nothing there to protect.
    """
    chosen = root or EVIDENCE_ROOT
    if _under_committed_store(chosen) and not _cycle_licensed():
        chosen = _redirect_root(
            chosen, f"no {CYCLE_TOKEN_ENV} in the environment: this write is not part of a "
                    f"scan cycle, and only the cycle runner may add to the committed store")
    root = chosen
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
