#!/usr/bin/env python3
"""Write a cycle's Observations and Findings to the event log, and project them. **Zero spend.**

Task §2.2 and §3. Observations are evidence and evidence belongs on the append-only log; the
graph is a projection of it, as everywhere else here. Idempotent on `obs_id` / `finding_id`,
both of which are DERIVED, so re-running a cycle that observed the same thing under the same
params adds nothing.

**Labelled Cypher only** — the lint from `230b282f` applies, and DD-020's
`<doc_id>::<item_id>` non-uniqueness is why.

    /opt/anaconda3/bin/python3 assessment/harness/scan/publish.py --from state/scan_smoke_2026-09-06.json
    /opt/anaconda3/bin/python3 assessment/harness/scan/publish.py --project
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

HARNESS = Path(__file__).resolve().parents[1]
REPO = HARNESS.parents[1]
sys.path.insert(0, str(HARNESS))
sys.path.insert(0, str(REPO))
sys.path.insert(0, "/Users/brock/GitHub/seldon")

#: The shard the 2026-09-06 scaffold and cycle 4 already sit on. Kept as the ONE numbered
#: shard this module still names, because `tests/test_scan_hygiene.py` replays the incident
#: that put Findings there; every cycle published from now on gets a NAMED shard instead
#: (`shard_for`).
SCAN_BATCH = 29
OBS_EVENT = "observation_recorded"
FIND_EVENT = "finding_derived"
#: DN-003 decision 3. Supersession is a FACT ABOUT TWO FINDINGS, so it goes on the log beside
#: them and the graph projects it, rather than being recomputed from `state/` at projection
#: time. One event per (re-judged Finding, the Finding it replaces on the same site and leg);
#: the pairing is computed once, here, from the two payloads, and the projection never reopens
#: the question. Same append-only shape as `finding_evidence_unretained` and
#: `edge_endpoint_alias`: the superseded Finding keeps its id, its line and its node.
SUPERSEDES_EVENT = "finding_supersedes"
#: `cc_tasks/2026-09-07_scan_hygiene.md` §1. A Finding whose `evidence` names `obs_id`s the log
#: does not hold is the same class of claim as a grounding span whose bytes are missing
#: (invariant 3). One of these events, written by `scripts/annotate_orphan_findings.py`, is the
#: append-only admission that the evidence is gone — and it is the ONLY thing that licenses
#: such a Finding to sit on the log. See `write_events`.
UNRETAINED_EVENT = "finding_evidence_unretained"
#: `cc_tasks/2026-09-07_scan_harness_v3.md` §1.2. The same append-only shape one layer down: an
#: Observation's `error_class` was misfiled by a fallback the closed set gave no better answer
#: to, and the line is never edited (its `obs_id` is DERIVED from that class, so an edit would
#: re-identify the record and orphan the Findings citing it). The overlay carries the class it
#: should have had; the projection reads it and keeps the recorded one beside it.
RECLASSIFIED_EVENT = "observation_error_reclassified"


_REJUDGE_SUFFIX_RE = re.compile(r"^(?P<base>.+)_rj(?P<gen>\d+)$")


def cycle_of(payload: dict, src: Path | None = None) -> str:
    """This cycle's name — the payload's FILE STEM when there is a file, and its `cycle` field
    otherwise.

    The file stem is authoritative because it is the name the rest of the repo uses for a
    cycle: `state/<cycle>.json`, `state/scan_matrix_<cycle>.json`, the figures, the report's
    `snapshot_cycle`, `PRIOR_CYCLES`, and every RESULT table. The `cycle` field agrees with it
    for every stored payload but one — `state/scan_2026-09-07b_rj2.json` says
    `scan_2026-09-07b_rj1`, a recorded defect of the tool that wrote it
    (`cc_tasks/2026-09-11_rejudge_1_2_3_4_gen9_RESULT.md` §8) — and a stored payload is
    immutable, so the disagreement is carried on the events rather than edited away. Naming the
    shard from the field instead would put two different judgements of cycle 2 in one file
    under the name of the older one.
    """
    return src.stem if src is not None else payload["cycle"]


def is_rejudgement(payload: dict) -> bool:
    """A judgement over another cycle's evidence. DN-003 decision 2 names the field
    `source_cycle`; every payload on disk carries it as `derived_from` and `cycle_kind`, which
    `rederive.rejudge` has written since 2026-09-08. Both are read, neither is assumed."""
    return bool(payload.get("source_cycle") or payload.get("derived_from")
                or payload.get("cycle_kind") == "rejudged")


def source_cycle_of(payload: dict) -> str | None:
    """The cycle whose Observations this payload's Findings cite."""
    return payload.get("source_cycle") or payload.get("derived_from")


def generation(cycle: str) -> int:
    """How many times this cycle has been judged again: 0 for the measurement, N for `_rjN`.

    DN-003 decisions 2 and 5 call this the generation and order publication by it. Read off the
    name rather than typed into a table, because the name is what every re-judgement tool
    already derives it from: `rederive.REJUDGE_SUFFIX`, `scripts/rejudge_gen9.py` and
    `scripts/rejudge_gen10.py` each continue the cycle's OWN sequence, so the suffix counts
    judgements of that cycle and never of the task that made them.
    """
    m = _REJUDGE_SUFFIX_RE.match(cycle)
    return int(m.group("gen")) if m else 0


def supersedes_of(cycle: str) -> str | None:
    """The judgement this one replaces: `_rjN` replaces `_rj(N-1)`, `_rj1` replaces the
    measurement, a measurement replaces nothing.

    DERIVED from the chain, never typed — task decision 2. It is also not read from the
    `rejudgement_diff` records, which are a diff and not a chain: the 2026-09-10 record pairs
    `scan_2026-09-07b_rj2` with the MEASURED cycle although `scan_2026-09-07b_rj1` was already
    published, because that task's question was "what did the harness-v5 reading change about
    the measurement". The predecessor doctrine both re-judgement scripts state — "the most
    recent judgement of the same cycle" — is the one that makes supersession one to one.
    """
    m = _REJUDGE_SUFFIX_RE.match(cycle)
    if not m:
        return None
    gen = int(m.group("gen"))
    return m.group("base") if gen <= 1 else f"{m.group('base')}_rj{gen - 1}"


def publication_order(cycles) -> list:
    """The cycles of `cycles`, oldest generation first, every predecessor before its successor.

    DN-003 decision 5: the log's sequence should be the sequence in which the project asserted
    its judgements. Sorted by `(generation, name)` rather than by a typed list, so a cycle
    cannot be published before the judgement it replaces and adding a cycle to the set cannot
    put it in the wrong place.
    """
    return sorted(cycles, key=lambda c: (generation(c), c))


def shard_for(cycle: str, finding_ids=None) -> dict:
    """Where this cycle's events go, as kwargs for `eventlog.append`.

    **The shard a cycle's events are already on, if it has one; its own named shard otherwise.**
    That is the whole rule, and it replaces `CYCLE_BATCH`, a typed table of cycle → batch number
    that had to be edited before every publication and that silently sent an unlisted cycle to
    `SCAN_BATCH`, a shard three other cycles already owned.

    Discovering the shard rather than declaring it is what lets DN-003 decision 4 hold both
    halves at once: one shard per cycle, and cycles already on a numbered shard are not moved.
    Two shards holding one cycle's Findings is a REFUSAL rather than a choice — it means the
    cycle was published twice into different files, and appending to either would make "the
    events of this cycle" a query for good.
    """
    from kg import eventlog
    if finding_ids:
        wanted, found = set(finding_ids), {}
        for shard in eventlog.shards():
            with shard.open(encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line or '"finding_derived"' not in line:
                        continue
                    ev = json.loads(line)
                    if ev.get("event_type") == FIND_EVENT and ev.get("finding_id") in wanted:
                        found.setdefault(shard.name, 0)
                        found[shard.name] += 1
        if len(found) > 1:
            raise SystemExit(
                f"REFUSING: {cycle}'s Findings are split across {len(found)} shards {found}; "
                f"the events of one cycle must live in one file (DN-003 decision 4).")
        if found:
            name = next(iter(found))
            m = re.fullmatch(r"batch-(\d+)", Path(name).stem)
            return {"batch": int(m.group(1))} if m else {"cycle": Path(name).stem[len("cycle-"):]}
    return {"cycle": cycle}


def shard_name(where: dict) -> str:
    """The path `shard_for` named, for the record the caller returns."""
    return ("events/" + (f"batch-{where['batch']:03d}.jsonl" if "batch" in where
                         else f"cycle-{where['cycle']}.jsonl"))


def cycle_fields(payload: dict, cycle: str) -> dict:
    """The cycle-level fields every event of this cycle carries (DN-003 decision 2).

    A judgement that does not say which cycle asserted it, over whose evidence, in place of
    what, cannot be replayed into the instrument that published: a stranger reading the log
    would see 4,296 Findings and no way to tell the current judgement of a surface from the
    three it replaced. These fields are what make DN-003 decision 1 more than a file move.

    `params_hash` is already on every Observation and Finding and is not repeated; the OVERLAY
    pair is, because a cycle whose parameters existed only as a base plus an in-memory change
    (`self_2026-09-13`) is otherwise the one cycle nothing can re-derive from the log alone.
    """
    out = {"cycle": cycle, "cycle_kind": payload.get("cycle_kind")
           or ("rejudged" if is_rejudgement(payload) else "measured"),
           "generation": generation(cycle)}
    if cycle != payload.get("cycle"):
        # Carried, not corrected: `state/scan_2026-09-07b_rj2.json` names itself `_rj1`, the
        # payload is immutable, and a reader of the log is owed the discrepancy rather than
        # a silent choice between the two names. See `cycle_of`.
        out["cycle_recorded_on_payload"] = payload.get("cycle")
    if is_rejudgement(payload):
        out["source_cycle"] = source_cycle_of(payload)
        out["supersedes"] = supersedes_of(cycle)
    for k in ("base_params_hash", "params_overlay", "harness_version"):
        if payload.get(k) is not None:
            out[k] = payload[k]
    return out


def _log_index():
    """`(obs_ids, finding_ids, annotated finding_ids, superseded pairs)` currently on the log."""
    from kg import eventlog
    seen_obs, seen_fnd, annotated, paired = set(), set(), set(), set()
    for ev in eventlog.replay():
        t = ev.get("event_type")
        if t == OBS_EVENT:
            seen_obs.add(ev.get("obs_id"))
        elif t == FIND_EVENT:
            seen_fnd.add(ev.get("finding_id"))
        elif t == UNRETAINED_EVENT:
            annotated.add(ev.get("finding_id"))
        elif t == SUPERSEDES_EVENT:
            paired.add(ev.get("finding_id"))
    return seen_obs, seen_fnd, annotated, paired


def write_events(payload: dict, src: Path | None = None) -> dict:
    """Append this cycle's Observations and Findings, refusing any Finding whose evidence the
    log will not hold.

    The refusal (`cc_tasks/2026-09-07_scan_hygiene.md` §1) is the standing rule the 120 orphan
    control Findings of 2026-09-06 exist because nothing enforced: the scaffold published
    Findings derived from fixture Observations it had already dropped, and an append-only log
    then kept them forever. A Finding is admitted only if every `obs_id` it cites is on the log
    or in this same payload — or if it carries a `finding_evidence_unretained` annotation, the
    append-only way of saying "the evidence is gone and here is why".

    **A RE-JUDGEMENT is held to three more refusals** (DN-003 decision 2, task decision 1), and
    all three say the same thing from different sides: a re-judgement creates no evidence.

    1. It may carry NO Observation. A payload with one is a measurement wearing a
       re-judgement's name, and `rederive.rejudge` already guarantees the field is empty by
       construction — this is the check that the guarantee held.
    2. Every `obs_id` it cites must already be ON THE LOG. The measured cycle's admission that
       a Finding may cite evidence published in the same breath does not extend to a
       judgement whose whole claim is that the evidence was already sufficient; a re-judged
       payload citing an unpublished `obs_id` means its SOURCE cycle was never published, and
       that is named here rather than discovered as an orphan afterwards.
    3. The judgement it supersedes must itself be on the log, or the chain the graph projects
       has a hole in it and "the current judgement of this surface" stops being answerable.

    It fails LOUD and writes nothing: the observations are appended after the checks, so a
    refused payload leaves the log exactly as it found it.
    """
    from kg import eventlog
    cycle = cycle_of(payload, src)
    findings = payload["findings_detail"] + payload.get("control_findings_detail", [])
    where = shard_for(cycle, [f["finding_id"] for f in findings])
    seen_obs, seen_fnd, annotated, _ = _log_index()
    rejudged = is_rejudgement(payload)

    if rejudged:
        if payload.get("observations_detail"):
            raise SystemExit(
                f"REFUSING: {cycle} is a re-judgement and carries "
                f"{len(payload['observations_detail'])} Observation(s). A re-judgement creates "
                f"no evidence (DN-003 decision 2); a payload with one is a measurement.")
        admissible = seen_obs
        pred = supersedes_of(cycle)
        pred_path = REPO / "state" / f"{pred}.json" if pred else None
        if pred_path is not None:
            if not pred_path.is_file():
                raise SystemExit(
                    f"REFUSING: {cycle} supersedes {pred}, whose payload is not at "
                    f"{pred_path}. The judgement it replaces cannot be found, so the "
                    f"supersession chain cannot be written.")
            pred_payload = json.loads(pred_path.read_text(encoding="utf-8"))
            pred_ids = {f["finding_id"] for f in pred_payload["findings_detail"]}
            missing = sorted(pred_ids - seen_fnd)
            if missing:
                raise SystemExit(
                    f"REFUSING: {cycle} supersedes {pred}, of whose {len(pred_ids)} Findings "
                    f"{len(missing)} are not on the log (e.g. {missing[:3]}). Publish "
                    f"{pred} first — DN-003 decision 5 publishes in generation order for "
                    f"exactly this reason.")
    else:
        admissible = seen_obs | {o["obs_id"] for o in payload["observations_detail"]}

    ungrounded = [
        (f["finding_id"], sorted(set(f.get("evidence") or []) - admissible))
        for f in findings
        if f["finding_id"] not in annotated
        and not set(f.get("evidence") or []) <= admissible
    ]
    if ungrounded:
        detail = "; ".join(f"{fid} misses {ids}" for fid, ids in ungrounded[:5])
        raise SystemExit(
            f"REFUSING: {len(ungrounded)} Finding(s) cite obs_ids that are neither on the log "
            f"nor in this payload, and carry no `{UNRETAINED_EVENT}` annotation: {detail}"
            f"{' …' if len(ungrounded) > 5 else ''}. Publish the Observations with them, or "
            f"annotate the Findings (scripts/annotate_orphan_findings.py).")

    fields = cycle_fields(payload, cycle)
    n_o = n_f = 0
    for o in payload["observations_detail"]:
        if o["obs_id"] in seen_obs:
            continue
        eventlog.append({"event_type": OBS_EVENT, **o, **fields}, **where)
        n_o += 1
    for f in findings:
        if f["finding_id"] in seen_fnd:
            continue
        eventlog.append({"event_type": FIND_EVENT, **f, **fields}, **where)
        n_f += 1
    return {"cycle": cycle, "cycle_kind": fields["cycle_kind"],
            "generation": fields["generation"], "supersedes": fields.get("supersedes"),
            "observation_events_written": n_o, "finding_events_written": n_f,
            "findings_evidence_unretained": sum(1 for f in findings
                                                if f["finding_id"] in annotated),
            "shard": shard_name(where)}


def write_supersession(payload: dict, src: Path | None = None) -> dict:
    """Pair every Finding of this cycle with the one it replaces, and put the pairs on the log.

    **One to one on (site, leg)**, which is the key a matrix row is built on and the only key
    under which "the current judgement of this surface for this check" is a single Finding.
    The pairing is computed from the two payloads and NOT from the `rejudgement_diff` records:
    a diff lists what MOVED, so pairing from it would link the handful of Findings whose
    verdict or sentence changed and leave every unchanged judgement looking current at two
    generations at once.

    Nothing is recomputed about the judgements themselves — no verdict is compared, no diff is
    taken. A Finding of this cycle with no counterpart in the predecessor is simply not paired:
    that is a leg the predecessor did not judge (`legs_not_judged`), and a link to nothing is
    worse than no link.
    """
    from kg import eventlog
    cycle = cycle_of(payload, src)
    pred = supersedes_of(cycle)
    if not is_rejudgement(payload) or not pred:
        return {"supersession_events_written": 0, "supersession_pairs": 0,
                "supersedes": None, "unpaired": 0}
    pred_payload = json.loads((REPO / "state" / f"{pred}.json").read_text(encoding="utf-8"))
    by_key: dict = {}
    for f in pred_payload["findings_detail"]:
        key = (f["target_doc_id"], f["leg"])
        if key in by_key:
            raise SystemExit(
                f"REFUSING: {pred} holds two Findings on {key}; supersession is one to one "
                f"on (site, leg) and cannot be written against a predecessor that is not.")
        by_key[key] = f["finding_id"]

    _, _, _, paired = _log_index()
    findings = payload["findings_detail"]
    where = shard_for(cycle, [f["finding_id"] for f in findings])
    fields = cycle_fields(payload, cycle)
    n, unpaired = 0, 0
    for f in findings:
        old = by_key.get((f["target_doc_id"], f["leg"]))
        if old is None:
            unpaired += 1
            continue
        if f["finding_id"] in paired:
            continue
        eventlog.append({"event_type": SUPERSEDES_EVENT,
                         "finding_id": f["finding_id"], "supersedes_finding_id": old,
                         "target_doc_id": f["target_doc_id"], "leg": f["leg"],
                         "rule_id": f["rule_id"], "supersedes_cycle": pred, **fields}, **where)
        n += 1
    return {"supersession_events_written": n,
            "supersession_pairs": sum(1 for f in findings
                                      if (f["target_doc_id"], f["leg"]) in by_key),
            "supersedes": pred, "unpaired": unpaired, "shard": shard_name(where)}


#: `cc_tasks/2026-09-07_scan_run_2.md` §1.1. The one direction bytes may travel into the
#: committed evidence store.
def promote_evidence(payload: dict, staging: Path | None = None,
                     committed: Path | None = None) -> dict:
    """Copy into `corpus/evidence/scan/` exactly the bodies this payload's Observations cite,
    then delete the staging directory.

    Inverts the default that produced two separate hygiene defects: `run.py` used to write
    every body it fetched straight into the committed store, so a diagnostic run, an aborted
    run, and a fixture run all left bytes behind that nothing ever cited (418 tracked bodies
    cited by no Observation; 260 fixture blobs quarantined). Content-addressed storage makes
    that cheap to do and impossible to undo cleanly — the digest tells you nothing about who
    wanted the body.

    Promotion is CITATION-driven, which is the same rule invariant 3 states one layer up: no
    grounding span, no write. A body in the committed store is a claim that some Observation
    on the log points at it, and this is the only thing that makes the claim true.

    A cited digest with no body anywhere is a hard failure, not a warning: publishing a
    Finding whose evidence the repo does not hold is precisely the orphan-Finding defect
    `cc_tasks/2026-09-07_scan_hygiene.md` §1 had to annotate 120 of.

    Paths are REWRITTEN on the payload's observations, because a `body_path` pointing into a
    staging directory that this function then deletes is a dangling reference on an
    append-only log. Safe to rewrite: `body_path` is not an input to the derived `obs_id`
    (`model.Observation.make` hashes `body_sha256`), so the record keeps its identity.
    """
    from scan.model import EVIDENCE_ROOT
    committed = committed or EVIDENCE_ROOT
    staging = Path(staging or payload.get("evidence_root") or "")
    #: A payload with no `evidence_root` — every RE-JUDGED payload, which has no staging root
    #: because it fetched nothing — made `Path("")`, which is `.`, which `REPO / "."` resolves
    #: to the REPOSITORY, which the `shutil.rmtree` at the end of this function would then
    #: delete. Never fired only because the two re-judgements published so far were published
    #: with `--no-promote`; `main` now refuses promotion for a re-judgement outright and this
    #: is the second lock on the same door. Found 2026-09-14 while teaching this module the
    #: re-judgement shape.
    if not str(staging) or staging == Path("."):
        raise SystemExit(
            "REFUSING: this payload names no `evidence_root`, so there is no staging "
            "directory to promote from — and an empty one resolves to the repository root. "
            "A re-judgement promotes nothing (DN-003 decision 2); a measured cycle whose "
            "bodies are already committed is published with --no-promote.")
    if not staging.is_absolute():
        staging = REPO / staging
    if staging.resolve() == REPO.resolve():
        raise SystemExit(
            f"REFUSING: the staging root resolves to the repository root ({REPO}). "
            f"This function deletes the staging directory when it is done.")
    obs = payload.get("observations_detail") or []
    cited = {(o.get("response") or {}).get("body_sha256") for o in obs}
    cited.discard(None)

    promoted, already, missing = [], [], []
    for digest in sorted(cited):
        dest = committed / digest[:2] / digest
        if dest.exists():
            already.append(digest)
            continue
        src = staging / digest[:2] / digest
        if not src.is_file():
            missing.append(digest)
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(src.read_bytes())
        promoted.append(digest)
    if missing:
        raise SystemExit(
            f"REFUSING: {len(missing)} body digest(s) cited by this payload's Observations are "
            f"in neither the staging root ({staging}) nor the committed store: "
            f"{missing[:5]}{' …' if len(missing) > 5 else ''}. A Finding whose evidence the "
            f"repo does not hold is not evidence (invariant 3).")

    for o in obs:
        d = (o.get("response") or {}).get("body_sha256")
        if d:
            o["response"]["body_path"] = str(
                (committed / d[:2] / d).relative_to(REPO)
                if str(committed).startswith(str(REPO)) else committed / d[:2] / d)
    if staging.is_dir() and staging != committed:
        shutil.rmtree(staging)
    return {"evidence_promoted": len(promoted),
            "evidence_already_committed": len(already),
            "evidence_cited_digests": len(cited),
            "staging_removed": str(staging) if staging.name else None}


#: The synthetic id scheme, defined in `model.py` beside the rest of the id model.
#: Imported rather than repeated: see the comment there for the 957 observations a
#: second copy cost.
#:
#: ABSOLUTE, because this file is BOTH a module the tests import as `scan.publish` and a script
#: the cycle runs as `python assessment/harness/scan/publish.py`. A relative import works in the
#: first case and raises `ImportError: attempted relative import with no known parent package`
#: in the second — which is how cycle 4 found it, after the run and before the publish. The
#: `sys.path` inserts at the top of this file are what make the absolute form work either way.
from scan.model import SYNTHETIC_PREFIXES                            # noqa: E402
CONTROL_PREFIX = "control:"

SCAN_LABELS = ("Observation", "Finding", "Rule")


def link_rules_to_indicators(session) -> dict:
    """`Rule -[:MEASURES]-> AssessmentIndicator`, and the Rule properties that edge implies.

    The two layers are projected by two scripts with two sources — the scan layer from the
    event log (here), the framework layer from `framework/ai_readiness_framework.json`
    (`scripts/load_framework_graph.py`) — and each one's reset removes the edge BETWEEN them.
    So the bridge is rebuilt by whichever ran last: both projectors call this, and running
    either alone leaves the graph whole. That is the whole reason this is a function and not
    four lines inlined in `project()`.

    `Rule.version` is parsed from the rule id, never read from the Finding's `rule_version`:
    that field is the literal `"v1"` for every rule ever shipped (`rules/_common.py`) and it
    is an INPUT to the derived `finding_id`, so it cannot be corrected in the events without
    re-identifying all 1,353 stored Findings. See `rules.parse_rule_id`.

    An unresolvable rule id or an indicator code with no node is COUNTED, never skipped
    silently — a Rule with no MEASURES edge is the defect this exists to make visible.
    """
    from scan.rules import CURRENT, parse_rule_id
    counts = {"measures": 0, "rules_seen": 0, "rules_unparseable": [],
              "rules_without_indicator": []}
    current_ids = set(CURRENT.values())
    for rec in list(session.run("MATCH (r:Rule) RETURN r.rule_id AS rid ORDER BY rid")):
        rid = rec["rid"]
        counts["rules_seen"] += 1
        try:
            parsed = parse_rule_id(rid)
        except ValueError:
            counts["rules_unparseable"].append(rid)
            continue
        session.run("MATCH (r:Rule {rule_id: $rid}) SET r.version = $ver, "
                    "r.indicator_code = $code, r.qualifier = $q, r.current = $cur",
                    rid=rid, ver=parsed["version"], code=parsed["indicator_code"],
                    q=parsed["qualifier"], cur=rid in current_ids)
        n = session.run("MATCH (r:Rule {rule_id: $rid}) "
                        "MATCH (i:AssessmentIndicator {code: $code}) "
                        "MERGE (r)-[:MEASURES]->(i) RETURN count(*) AS n",
                        rid=rid, code=parsed["indicator_code"]).single()["n"]
        if n:
            counts["measures"] += 1
        else:
            counts["rules_without_indicator"].append(rid)
    return counts


def project() -> dict:
    from kg import eventlog
    from seldon.config import get_neo4j_driver, load_project_config
    cfg = load_project_config(REPO)
    driver = get_neo4j_driver(cfg)
    #: `observed_on_missing_document` is an INTEGRITY check — an observation of a surface the
    #: graph has no Document for. Control observations legitimately have none (a fixture is
    #: not a corpus document), so they are counted apart; folding them in would leave the
    #: check permanently non-zero and therefore meaningless.
    counts = {"observations": 0, "findings": 0, "rules": 0, "observed_on": 0, "supports": 0,
              "ruled_by": 0, "observed_on_missing_document": 0, "control_observations": 0,
              "host_observations": 0, "findings_evidence_unretained": 0,
              "observations_error_reclassified": 0, "supersedes": 0,
              "supersedes_unresolved": 0, "findings_current": 0, "findings_superseded": 0}
    # Read the annotations BEFORE the replay, because an annotation may be appended to a later
    # shard than the Finding it corrects — that is what an append-only correction is — and a
    # single forward pass would project the Finding before it had seen the event that qualifies
    # it. `edge_endpoint_alias` in batch-005 has the same shape for the same reason.
    unretained, reclassified, superseding = set(), {}, {}
    for ev in eventlog.replay():
        t = ev.get("event_type")
        if t == UNRETAINED_EVENT:
            unretained.add(ev.get("finding_id"))
        elif t == RECLASSIFIED_EVENT:
            reclassified[ev["obs_id"]] = ev["error_class"]
        elif t == SUPERSEDES_EVENT:
            superseding[ev["finding_id"]] = ev["supersedes_finding_id"]
    try:
        with driver.session(database=cfg["neo4j"]["database"]) as s:
            pred = " OR ".join(f"n:{l}" for l in SCAN_LABELS)
            s.run(f"MATCH (n) WHERE {pred} DETACH DELETE n")
            # Finding events are BUFFERED and written after the pass that writes the
            # Observations, so a Finding may cite evidence recorded on any shard. Ordering
            # across shards used to be guaranteed by arithmetic — a measured cycle always got a
            # lower batch number than the re-judgement citing it — and DN-003 decision 4's
            # named cycle shards end that: `cycle-scan_2026-09-07_rj1.jsonl` and
            # `cycle-scan_2026-09-07.jsonl` sort by name, not by what cites what. Buffering the
            # 4,296 Finding events costs nothing measurable and makes the projection
            # independent of shard order, which is a property worth having outright.
            find_events = []
            for ev in eventlog.replay():
                t = ev.get("event_type")
                if t == FIND_EVENT:
                    find_events.append(ev)
                elif t == OBS_EVENT:
                    s.run("MERGE (o:Observation {obs_id: $id}) SET o.leg = $leg, "
                          "o.indicator_code = $code, o.surface_doc_id = $doc, "
                          "o.captured_at = $at, o.collector = $col, "
                          "o.evidence_hash = $hash, o.raw_ref = $ref, "
                          "o.error_class = $err, o.error_class_recorded = $err0, "
                          "o.error_reclassified = $recl, o.params_hash = $ph, "
                          "o.cycle = $cyc",
                          id=ev["obs_id"], leg=ev["leg"], code=ev["spec_code"],
                          doc=ev["target_doc_id"], at=ev["captured_at"],
                          col=ev["collector"],
                          hash=(ev.get("response") or {}).get("body_sha256"),
                          ref=(ev.get("response") or {}).get("body_path"),
                          err=reclassified.get(ev["obs_id"], ev.get("error_class")),
                          err0=ev.get("error_class"),
                          recl=ev["obs_id"] in reclassified, ph=ev["params_hash"],
                          cyc=ev.get("cycle"))
                    counts["observations"] += 1
                    counts["observations_error_reclassified"] += int(
                        ev["obs_id"] in reclassified)
                    hit = s.run("MATCH (d:Document {doc_id: $d}) RETURN count(d) AS n",
                                d=ev["target_doc_id"]).single()["n"]
                    if hit:
                        s.run("MATCH (o:Observation {obs_id: $id}) "
                              "MATCH (d:Document {doc_id: $d}) MERGE (o)-[:OBSERVED_ON]->(d)",
                              id=ev["obs_id"], d=ev["target_doc_id"])
                        counts["observed_on"] += 1
                    elif str(ev["target_doc_id"]).startswith(CONTROL_PREFIX):
                        counts["control_observations"] += 1
                    # A well-known set is a SYNTHETIC host surface: nothing was admitted for
                    # it because there is nothing to admit. Same reasoning as the control
                    # observations above — folding either into the integrity check leaves it
                    # permanently non-zero and therefore meaningless.
                    elif str(ev["target_doc_id"]).startswith(SYNTHETIC_PREFIXES):
                        counts["host_observations"] += 1
                    else:
                        counts["observed_on_missing_document"] += 1
            for ev in find_events:
                # `evidence_unretained` is set on EVERY Finding, true or false, rather
                # than only on the annotated ones: a property that is absent and a property
                # that is false read the same way to `coalesce`, and the integrity check
                # this exists for ("a Finding with no SUPPORTS edge and no annotation")
                # deserves an answer that is stored rather than inferred from a missing key.
                unret = ev["finding_id"] in unretained
                s.run("MERGE (f:Finding {finding_id: $id}) SET f.rule_id = $rid, "
                      "f.indicator_code = $code, f.verdict = $v, f.reason = $r, "
                      "f.params_hash = $ph, f.target_doc_id = $doc, "
                      "f.evidence_unretained = $unret, f.cycle = $cyc, "
                      "f.cycle_kind = $kind, f.generation = $gen",
                      id=ev["finding_id"], rid=ev["rule_id"], code=ev["spec_code"],
                      v=ev["verdict"], r=ev["reason"], ph=ev["params_hash"],
                      doc=ev["target_doc_id"], unret=unret,
                      # Null for every event written before DN-003, and deliberately NOT
                      # backfilled from `state/`: the projection is a function of the log, and
                      # a property invented at projection time out of a file beside it is the
                      # convention DN-003 decision 3 replaced with an edge. `census()` answers
                      # for the older cycles, from the payloads, and says which is which.
                      #
                      # It matters because `params_hash` cannot: four cycles judged in one
                      # generation share one hash (gen 9 covers `scan_2026-09-07_rj2`,
                      # `_07b_rj3`, `_09_rj2` and `_10_rj2`, the report's own snapshot), so
                      # "the Findings of this cycle" was a question the graph could not answer
                      # before this field existed.
                      cyc=ev.get("cycle"), kind=ev.get("cycle_kind"),
                      gen=ev.get("generation"))
                counts["findings"] += 1
                counts["findings_evidence_unretained"] += int(unret)
                s.run("MERGE (r:Rule {rule_id: $rid}) SET r.version = $ver",
                      rid=ev["rule_id"], ver=ev["rule_version"])
                s.run("MATCH (f:Finding {finding_id: $id}) MATCH (r:Rule {rule_id: $rid}) "
                      "MERGE (f)-[:RULED_BY]->(r)", id=ev["finding_id"], rid=ev["rule_id"])
                counts["ruled_by"] += 1
                for oid in ev.get("evidence") or []:
                    s.run("MATCH (o:Observation {obs_id: $o}) "
                          "MATCH (f:Finding {finding_id: $f}) MERGE (o)-[:SUPPORTS]->(f)",
                          o=oid, f=ev["finding_id"])
                    counts["supports"] += 1
            # DN-003 decision 3. The pairing is READ from the log, never recomputed: these
            # edges say which judgement replaced which, and nothing here compares a verdict or
            # a reason. A pair whose endpoints are not both on the graph is COUNTED rather than
            # skipped — a supersession event naming a Finding the log does not hold is the same
            # class of claim as a Finding naming an Observation it does not hold.
            for new_id, old_id in superseding.items():
                n = s.run("MATCH (a:Finding {finding_id: $a}) "
                          "MATCH (b:Finding {finding_id: $b}) "
                          "MERGE (a)-[:SUPERSEDES]->(b) RETURN count(*) AS n",
                          a=new_id, b=old_id).single()["n"]
                counts["supersedes" if n else "supersedes_unresolved"] += 1
            # A Finding with no successor is CURRENT (DN-003 decision 3). Stored as a property
            # as well as answerable by query, because the report's snapshot has to be able to
            # say "this is the judgement of record, and here is whether anything has replaced
            # it" without the reader reconstructing the chain.
            s.run("MATCH (f:Finding) SET f.current = NOT EXISTS { "
                  "MATCH (:Finding)-[:SUPERSEDES]->(f) }")
            counts["findings_current"] = s.run(
                "MATCH (f:Finding) WHERE f.current RETURN count(f)").single()[0]
            counts["findings_superseded"] = s.run(
                "MATCH (f:Finding) WHERE NOT f.current RETURN count(f)").single()[0]
            counts["rules"] = s.run("MATCH (r:Rule) RETURN count(r)").single()[0]
            counts.update(link_rules_to_indicators(s))
    finally:
        driver.close()
    return counts


# ------------------------------------------------------------------ the census (decision 4)

#: A cycle's KIND, and the three are not a taxonomy for its own sake. `measured` fetched bytes
#: from federal hosts; `self` fetched them from the host that PUBLISHES this report, so its
#: verdicts are about the publication rather than about the subject; `rejudged` fetched nothing
#: at all and is a judgement over another cycle's evidence. Counting the three together is how
#: "the harness has recorded 4,296 Findings" becomes a number that answers nothing.
KINDS = ("measured", "self", "rejudged")


def cycle_kind(cycle: str, payload: dict) -> str:
    if is_rejudgement(payload):
        return "rejudged"
    return "self" if cycle.startswith("self_") else "measured"


def stored_cycles() -> dict:
    """`finding_id -> (cycle, kind)` for every payload still in `state/`.

    The join is the FINDING ID, not the `params_hash` two cycles can share
    (`scan_2026-09-07_rj1` and `scan_2026-09-07b_rj1` were judged in one run and carry one
    hash, which is why `annotate_orphan_findings.cycle_by_params_hash` can only answer for the
    cycles that are alone under theirs). A derived id is unique to the judgement that made it,
    so this answer is exact wherever the payload survives.
    """
    out = {}
    for path in sorted((REPO / "state").glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(payload, dict) or "findings_detail" not in payload:
            continue
        cycle = path.stem
        kind = cycle_kind(cycle, payload)
        for f in payload["findings_detail"] + (payload.get("control_findings_detail") or []):
            out.setdefault(f["finding_id"], (cycle, kind))
    return out


def census() -> dict:
    """What the log holds, per cycle kind. **Reads the log; touches no database.**

    Task decision 4. `findings_evidence_unretained` and the orphan count are reported PER KIND
    because they mean different things per kind: an orphan among the measured Findings is the
    2026-09-06 scaffold's 120, evidence discarded before publication and annotated as gone; an
    orphan among the RE-JUDGED Findings would be a judgement published ahead of the cycle whose
    evidence it cites, which is the defect DN-003 decision 5's publication order exists to make
    impossible. One number covering both would report the second as normal.
    """
    from kg import eventlog
    index = stored_cycles()
    obs_ids, per_kind, per_cycle, unretained = set(), {}, {}, set()
    findings = []
    for ev in eventlog.replay():
        t = ev.get("event_type")
        if t == OBS_EVENT:
            obs_ids.add(ev["obs_id"])
        elif t == FIND_EVENT:
            findings.append(ev)
        elif t == UNRETAINED_EVENT:
            unretained.add(ev["finding_id"])

    def row():
        return {"cycles": set(), "findings": 0, "findings_evidence_unretained": 0,
                "orphan_findings": 0, "orphan_findings_unannotated": 0}

    for ev in findings:
        fid = ev["finding_id"]
        # The event's own `cycle` when it has one (everything published from DN-003 onward),
        # the stored payload otherwise, and `unattributed` when neither can say — the 630
        # Findings the 2026-09-06 scaffold left on `batch-029.jsonl` under three `params_hash`
        # values, two of which match no committed revision of `params.yaml`. Never guessed:
        # `annotate_orphan_findings.cycle_by_params_hash` had to answer `None` for these too,
        # and a census that invented a cycle for them would be the only place in this repo
        # where an unrecoverable provenance reads as a recovered one.
        cycle, kind = index.get(fid, (None, None))
        cycle = ev.get("cycle") or cycle or "unattributed"
        kind = ev.get("cycle_kind") or kind or "unattributed"
        orphan = any(o not in obs_ids for o in (ev.get("evidence") or []))
        for bucket in (per_kind.setdefault(kind, row()), per_cycle.setdefault(cycle, row())):
            bucket["cycles"].add(cycle)
            bucket["findings"] += 1
            bucket["findings_evidence_unretained"] += int(fid in unretained)
            bucket["orphan_findings"] += int(orphan)
            bucket["orphan_findings_unannotated"] += int(orphan and fid not in unretained)
    for bucket in list(per_kind.values()) + list(per_cycle.values()):
        bucket["cycles"] = len(bucket["cycles"])
    for bucket in per_cycle.values():
        bucket.pop("cycles")
    return {"observations": len(obs_ids), "findings": len(findings),
            "by_kind": {k: per_kind[k] for k in sorted(per_kind)},
            "by_cycle": {c: per_cycle[c] for c in sorted(per_cycle)},
            "shards": [p.name for p in eventlog.shards()]}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--from", dest="src", default=None)
    ap.add_argument("--project", action="store_true")
    ap.add_argument("--no-promote", action="store_true",
                    help="publish without promoting staged bodies (for a payload whose "
                         "evidence is already in the committed store)")
    ap.add_argument("--census", action="store_true",
                    help="print what the log holds per cycle kind and per cycle; writes "
                         "nothing and reads no database")
    a = ap.parse_args(argv)
    out = {}
    if a.src:
        src = Path(a.src)
        payload = json.loads(src.read_text(encoding="utf-8"))
        # Promote BEFORE the events are written, so the `body_path` that lands on the
        # append-only log already points into the committed store. The other order would put
        # a staging path — a directory this run then deletes — on a line that can never be
        # edited. `--no-promote` exists for the four cycles published before staging existed,
        # whose bodies are already committed and have no staging root to find.
        #
        # **A re-judgement never promotes.** Not "promotes nothing" — is not asked. It cites
        # evidence another cycle published and has no staging root at all, and the promotion
        # path with no staging root resolves to the repository, which it then deletes
        # (`promote_evidence`). DN-003 decision 2 is the rule; this is where it binds, and
        # `--no-promote` is no longer the thing standing between the two.
        if is_rejudgement(payload):
            out["evidence_promotion"] = ("refused: a re-judgement creates no evidence and "
                                         "promotes none (DN-003 decision 2)")
        elif not a.no_promote:
            out.update(promote_evidence(payload))
            src.write_text(json.dumps(payload, indent=1, default=str) + "\n", encoding="utf-8")
        out.update(write_events(payload, src))
        out.update(write_supersession(payload, src))
    if a.project:
        out.update(project())
    if a.census:
        out["census"] = census()
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
