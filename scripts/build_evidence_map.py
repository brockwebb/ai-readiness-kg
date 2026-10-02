#!/usr/bin/env python3
"""The evidence map's record-derived claims. **Zero spend, no network, reads only.**

`cc_tasks/2026-10-02_evidence_map_record.md`, under DN-009 decisions 2, 5 and 6: every claim
the one-page summary or the brief will make is written down with its evidence before any prose
is drafted. This script asks the record six fixed questions (Q1 to Q6 of the task) and writes
the answers to `docs/evidence/claims.yaml` as claims with status `record` or
`needs_measurement`. It authors no summary text, and it creates or changes no indicator, rule,
verdict, Result, Finding or corpus document.

    scripts/build_evidence_map.py           write docs/evidence/claims.yaml (needs Neo4j)
    scripts/build_evidence_map.py --check   re-render into memory; exit 1 on any drift

**Sources, and only these.** The framework record (through `build_brief_pack.Sources`, so the
pack and the map read the same inputs the same way), the corpus manifest, the published
matrices of the cycle of record (`docs/reports/publication.yaml: snapshot_cycle`), the cycle's
event shard (`events/cycle-<cycle>.jsonl`, the source of truth for its Findings), the
projection for each Finding's Observations and for registered Results, `scripts/score.py` and
the MCP verbs (`mcp/airkg_tools.py`) as imported code.

**Other tasks' claims are kept.** The prior-art task (`56e5accb`) adds `prior_art` entries to
the same file. A claim belongs to this script when its `source_task` is `TASK`; every other
entry is carried through byte-for-byte in its position by id. Claim ids are stable: each claim
has a deterministic `key`, the id already on disk for that key is reused, and a new key takes
the next id after the highest in the file, so a regenerated map never renumbers a claim another
document cites.

**Numbers.** No numeral is typed into a claim. Every number in a claim's text goes through
`Claim.n(value, source)`, which records it on the claim's `numbers` list with its source;
`tests/test_evidence_map.py` fails on a numeral in a claim's text that the list does not hold.
Identifiers (indicator codes, legs, finding ids, cycle names, dates, HTTP statuses, URLs) are
backticked, and backticked spans are not prose numbers.

**Idempotence** is the regenerate-and-compare guard the other views use: nothing here reads a
clock, every collection is sorted, and `--check` is a byte-for-byte comparison.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
for p in ("", "scripts", "assessment/harness", "mcp"):
    sys.path.insert(0, str(REPO / p))

import yaml  # noqa: E402

import build_brief_pack as BP  # noqa: E402

OUT_DIR = REPO / "docs" / "evidence"
CLAIMS = OUT_DIR / "claims.yaml"
TASK = "cc_tasks/2026-10-02_evidence_map_record.md"
GENERATOR = "scripts/build_evidence_map.py"
SCHEMA_VERSION = 1
STATUSES = ("record", "prior_art", "needs_measurement", "unsupported")
EVIDENCE_KINDS = ("finding", "result", "document", "indicator", "query")

#: The body the Census questions (Q4, Q5's Census rows, Q6) are about. The pack's dogfood body,
#: read from the pack so the two cannot name different bodies.
CENSUS = BP.DOGFOOD_BODY

#: The commit that first wrote the framework record: "the assessment framework becomes a
#: graph". Q3's boundary between the corpus before the framework work and the corpus added
#: during it. Measured from git, never typed (see `framework_start`).
RECORD_PATH = "framework/ai_readiness_framework.json"

# ------------------------------------------------------------------------- Q1 classes
#
# DN-009 decision 6 names four classes of what blocks an unmeasured indicator. The order is
# the order in which an OUTSIDE party can remove the blocker on its own: with public tooling
# now; with money; by authoring a reference set or standard that does not exist yet; never,
# because only the publisher holds it. Requirements on one route are needed together (the
# MCP's `routes_mean`), so a route is blocked by its hardest requirement; two routes are
# alternatives, so an indicator is blocked by its easiest route.
Q1_ORDER = ("open_tooling", "funding", "no_standard", "agency_cooperation")
#: A fifth value, for an indicator whose record says nothing stands between it and a verdict.
#: It is not one of DN-009's four because it is not a blocker: the record's status lags or the
#: definition of `measured` does not apply. Recorded rather than forced into a class.
Q1_NOT_BLOCKED = "not_blocked"

#: Requirement `kind` (record `AssessmentTool` / `Precondition` nodes) -> class. Anything the
#: publisher provides is `agency_cooperation` whatever its kind (see `req_class`).
REQ_KIND_CLASS = {
    "open_source": "open_tooling",      # e.g. tool:aidrin, tool:slsa-verifier
    "hosted_free": "open_tooling",      # e.g. tool:wayback-cdx-server
    "second_cycle": "open_tooling",     # another run of this harness; no one else acts
    "hosted_paid": "funding",           # e.g. tool:perplexity-ai, cost band `procurement`
    "benchmark_set": "no_standard",     # a reference set that does not exist yet
    "site_owner_account": "agency_cooperation",
    "platform_account": "agency_cooperation",
    "agency_records": "agency_cooperation",
}

#: For an indicator with no REQUIRES edge, the record's own reason text decides the class.
#: Ordered; first match wins. Each pattern is a phrase the record uses, quoted.
REASON_CLASS = (
    (r"a rule this project would write", "open_tooling",
     "the record says the unmeasured half is a rule this project would write over the catalog "
     "records the harness already fetches"),
    (r"no collector reads it", "open_tooling",
     "the record says an admitted standard names the artifact and only a collector this "
     "project would write is missing"),
    (r"What is missing is a standard", "no_standard", ""),
    (r"an instrument this project has not specified", "no_standard", ""),
    (r"needs a different instrument", "no_standard", ""),
    (r"no admitted document names a machine-readable", "no_standard", ""),
    (r"definition of `measured`", Q1_NOT_BLOCKED, ""),
    (r"no tool, account or record stands between it and a verdict", Q1_NOT_BLOCKED, ""),
)

# ------------------------------------------------------------------------- Q2 classes
#
# An ACCESS DENIAL is the host declining to serve this client: an HTTP 401, 403 or 429 (RFC
# 9110 §15.5.2 and §15.5.4, RFC 6585 §4: statuses the server chose to send about the request),
# a robots.txt disallow (RFC 9309), or a connection reset by the host. In the harness's closed
# error map (`assessment/harness/scan/errors.py`) those are the classes below. `errors.py`
# deliberately has no class for a bot-detection challenge served with HTTP 200 (it would be
# read as an observed page) and resolves ECONNREFUSED to `unknown`, so neither can be counted
# here, and the README says so.
DENIAL_CLASSES = ("refused", "robots_disallowed", "connection_reset")

#: A `fail` whose reason reports the denial itself as what was measured (A12 reads a refusal
#: on purpose; A4 and A11-declared read a declared disallow).
DENIAL_REASON = (r"answered HTTP (401|403|429)\b", r"robots\.txt (DISALLOWS|disallows)")

#: A `fail` where something of the asked-for kind IS served but fails the rule's property test.
#: Checked before ABSENCE_REASON. Each pattern is the rule's own reason wording.
NONCONFORMANT_REASON = (
    r"^only PDF served",
    r"^soft-\d+",
    r"carries only \d+ visible characters before JavaScript",
    r"meta-robots directives restrict",
    r"does not parse as an API description",
    r"are filtered queries, not whole-product downloads",
    r"below the \d+-byte whole-product floor",
    r"^markup declares the vintage via dateModified, but",
    r"answer with HTML rather than a machine format",
    r"is not retrievable without JS",
    r"^a changelog page is served at .* but not in a machine-readable content type",
)

#: A `fail` where the record, field or file the rule asks for is not there (DN-009 decision 5:
#: "absence from a catalog is not blocked"). `only an HTTP Last-Modified header` is absence
#: because the rule's own reason says the header is not a declared vintage; `markup present
#: ... but no Dataset` is absence of the type the rule asks for.
ABSENCE_REASON = (
    r"^no probed link serves a structured content type",
    r"^no OpenAPI/JSON API description served",
    r"^no whole-product download linked",
    r"^no robots\.txt served",
    r"^nothing is DECLARED",
    r"^discovery files served .* but none lists the product URL",
    r"^no sitemap, llms\.txt or well-known discovery file served",
    r"^markup present .* but no Dataset/DataCatalog type",
    r"^no JSON-LD, microdata or RDFa",
    r"^no declared release or modification date",
    r"^only an HTTP Last-Modified header",
    r"^none of the \d+ probed machine-first paths is served",
    r"^variable-level metadata is not reachable by a machine",
    r"^no schema\.org `DefinedTerm`",
    r"^no link to a methodology document",
    r"holds no catalog record for the product",
    r"^no public data\.json catalog served",
    r"do not publish quality as metadata",
    r"^no term codes",
    r"^no licence in the product page",
    r"declares no Content-Signal",
    r"lack a lineage field",
    r"but the product is not in it",
    r"^no changelog or release-notes endpoint served",
    r"^none of the \d+ error-measure field tokens appears",
)

Q2_COLUMNS = ("access_denial", "absence", "nonconformant", "error_other", "pass")

#: Q4: a Census finding fails "for the reason that data.json holds no record for the probed
#: product" when its reason says one of these.
CATALOG_ABSENCE = (r"holds no catalog record for the product among its (\d+) record",
                   r"a catalog is served at https://www\.census\.gov/data\.json but the "
                   r"product is not in it")

#: Named queries: the `id` of every `query` evidence entry is a key here, and the test resolves
#: it against this table. The value says what was computed and from what.
QUERIES = {
    "record.indicator_nodes": "AssessmentIndicator nodes in framework/ai_readiness_framework.json",
    "record.counts": "framework/ai_readiness_framework.json `counts` and `counts_basis`",
    "record.candidates": "framework_writeback._candidate_ids over the record (DD-054)",
    "record.criteria": "AssessmentCriterion nodes in the record; USAFacts' four are "
                       "build_brief_pack.USAFACTS_CRITERIA (skeleton line 11)",
    "record.measurement_status": "Counter of measurement_status over the framework's "
                                 "indicators (candidate excluded)",
    "rules.current": "assessment/harness/scan/rules CURRENT, indicator code by parse_rule_id",
    "cycle.findings": "finding_derived events in events/cycle-<cycle>.jsonl",
    "cycle.legs": "distinct `leg` over the cycle's finding_derived events",
    "cycle.bodies": "scripts/prescriptions.py::bodies over the cycle's matrices",
    "cycle.observation_classes": "MATCH (o:Observation)-[:SUPPORTS]->(f:Finding {cycle}) "
                                 "RETURN f.finding_id, collect(o.error_class)",
    "cycle.client": "params manners.user_agent as quoted by the cycle's A12 findings; "
                    "assessment/harness/scan/manners.py builds the client with that one header",
    "score.compute": "scripts/score.py::compute(cycle): ranks, concentration, prescriptions",
    "mcp.get_body": "mcp/airkg_tools.py::Tools.get_body(CENSUS) over the published matrices",
    "mcp.get_requirements": "mcp/airkg_tools.py::Tools.get_requirements(indicator=...)",
    "traceability.locators": "scripts/report_traceability.py::locators over each indicator's "
                             "evidence_raw, as page C computes it",
    "manifest.included": "corpus/manifest.json entries with screening.decision included",
    "manifest.admission_dates": "date of the first manifest_add event in events/*.jsonl for "
                                "each included entry (build_evidence_map.admissions)",
    "git.framework_start": "git log --diff-filter=A on framework/ai_readiness_framework.json",
}

NUM_RX = re.compile(r"(?<![\w.\-])\d[\d,]*(?:\.\d+)?(?![\w])")


def prose(text: str) -> str:
    """The claim text with backticked spans removed: what the numeral test scans."""
    return re.sub(r"`[^`]*`", "", text)


def numerals(text: str) -> list:
    return NUM_RX.findall(prose(text))


# ------------------------------------------------------------------------------ claims

class Claim:
    def __init__(self, key: str, question: str, status: str):
        if status not in STATUSES:
            raise SystemExit(f"FATAL: status {status!r} is not one of {STATUSES}")
        self.key, self.question, self.status = key, question, status
        self.text = ""
        self.evidence: list = []
        self.nums: list = []

    def n(self, value, source: str, fmt: str | None = None) -> str:
        """A number in the claim's text, recorded with its source."""
        if isinstance(value, float):
            # A fixed format when the caller names one; otherwise the shortest form (0.2, not
            # 0.200), so the text reads as the score.py value does.
            shown = format(value, fmt) if fmt else format(value, "g")
        elif isinstance(value, int):
            shown = f"{value:,}"
        else:
            shown = str(value)
        if {"value": shown, "source": source} not in self.nums:
            self.nums.append({"value": shown, "source": source})
        return shown

    def ev(self, kind: str, id_: str, locator: str, note: str = "") -> "Claim":
        if kind not in EVIDENCE_KINDS:
            raise SystemExit(f"FATAL: evidence kind {kind!r} is not one of {EVIDENCE_KINDS}")
        if kind == "query" and id_ not in QUERIES:
            raise SystemExit(f"FATAL: query {id_!r} is not in QUERIES")
        e = {"kind": kind, "id": id_, "locator": locator}
        if note:
            e["note"] = note
        if e not in self.evidence:
            self.evidence.append(e)
        return self

    def q(self, id_: str, note: str = "") -> "Claim":
        return self.ev("query", id_, f"{GENERATOR}::QUERIES[{id_!r}]", note)

    def as_dict(self, cid: str) -> dict:
        stray = [x for x in numerals(self.text)
                 if x not in {d["value"] for d in self.nums}]
        if stray:
            raise SystemExit(f"FATAL: claim {self.key}: numerals {stray} in its text are not "
                             f"on its numbers list: {self.text!r}")
        return {"id": cid, "key": self.key, "question": self.question, "text": self.text,
                "status": self.status, "evidence": self.evidence, "numbers": self.nums,
                "source_task": TASK}


# ------------------------------------------------------------------------------ sources

class Map:
    """Every input, read once, on top of the brief pack's `Sources`."""

    def __init__(self, graph):
        self.s = BP.Sources(graph)
        self.graph = graph
        self.cycle = self.s.cycle
        self.shard = REPO / "events" / f"cycle-{self.cycle}.jsonl"
        self._findings = None
        self._obs = None

    # -- the cycle -------------------------------------------------------------------
    @property
    def findings(self) -> dict:
        """`{finding_id: event}` from the cycle's shard, each with its 1-based `_line`."""
        if self._findings is None:
            if not self.shard.is_file():
                raise SystemExit(f"FATAL: {BP.rel(self.shard)} is missing; the cycle of record "
                                 "has no event shard to read its Findings from")
            out = {}
            for i, line in enumerate(self.shard.read_text(encoding="utf-8").splitlines(), 1):
                if not line.strip():
                    continue
                e = json.loads(line)
                if e.get("event_type") == "finding_derived" and e.get("cycle") == self.cycle:
                    if e["finding_id"] in out:
                        raise SystemExit(f"FATAL: {e['finding_id']} derived twice in "
                                         f"{BP.rel(self.shard)}")
                    out[e["finding_id"]] = {**e, "_line": i}
            self._findings = out
        return self._findings

    def floc(self, fid: str) -> str:
        return f"{BP.rel(self.shard)}:{self.findings[fid]['_line']}"

    @property
    def obs_classes(self) -> dict:
        """`{finding_id: sorted error classes}` of the Observations supporting each Finding."""
        if self._obs is None:
            rows, truncated = self.graph.read(
                "MATCH (f:Finding {cycle: $c}) OPTIONAL MATCH (o:Observation)-[:SUPPORTS]->(f) "
                "RETURN f.finding_id AS f, collect(o.error_class) AS ec",
                limit=10 * len(self.findings) + 10, c=self.cycle)
            if truncated:
                raise SystemExit("FATAL: the Observation-class read was truncated")
            out = {r["f"]: sorted({x for x in r["ec"] if x}) for r in rows}
            missing = sorted(set(self.findings) - set(out))
            extra = sorted(set(out) - set(self.findings))
            if missing or extra:
                raise SystemExit(f"FATAL: the projection and {BP.rel(self.shard)} disagree on "
                                 f"the cycle's Findings: {len(missing)} only in the shard, "
                                 f"{len(extra)} only in the graph. Re-project before mapping.")
            self._obs = out
        return self._obs

    def body_of(self) -> dict:
        """`{target_doc_id: (body, tier)}` for every target on the cycle, from the published
        matrices. Fails loud on a target it cannot place: an unplaced finding would vanish
        from Q2's table without a trace."""
        surf, hosts = {}, {}
        for stem, (path, m) in self.s.matrices().items():
            for r in m["rows"]:
                tier = m.get("tier") if stem != "product" else "product"
                for k in ("host_surface", "candidate_surface", "surface"):
                    if r.get(k):
                        surf[r[k]] = (r["agency"], m.get("tier"))
                if r.get("host_surface"):
                    hosts[r["host_surface"].split(":", 1)[1]] = (r["agency"], m.get("tier"))
        out = {}
        for t in sorted({f["target_doc_id"] for f in self.findings.values()}):
            if t in surf:
                out[t] = surf[t]
                continue
            m = re.fullmatch(r"scan-(.+)-machine", t)
            if m:
                hit = {surf[k] for k in surf if k.startswith(f"scan-{m.group(1)}-flagship")}
            elif t.startswith("machine:"):
                dom = ".".join(t.split(":", 1)[1].split(".")[-2:])
                hit = {v for h, v in hosts.items() if ".".join(h.split(".")[-2:]) == dom}
            else:
                hit = set()
            if len(hit) != 1:
                raise SystemExit(f"FATAL: target {t!r} maps to {sorted(hit)} bodies; Q2 "
                                 "cannot place its findings")
            out[t] = hit.pop()
        return out


def rec_loc(node_id: str) -> str:
    return f"{RECORD_PATH}#{node_id}"


def first(patterns, text: str):
    for p in patterns:
        if re.search(p, text):
            return p
    return None


# ------------------------------------------------------------------------------ Q1

def req_class(req: dict) -> str:
    if req.get("who_provides") == "publisher":
        return "agency_cooperation"
    k = req.get("kind")
    if k not in REQ_KIND_CLASS:
        raise SystemExit(f"FATAL: requirement {req.get('id')} has kind {k!r}, which Q1 has no "
                         f"class for; add it to REQ_KIND_CLASS with its grounding")
    return REQ_KIND_CLASS[k]


def q1_rows(M: Map) -> list:
    s = M.s
    judged = set(BP.leg_counts(s))
    rows = []
    for n in s.inds:
        if n["id"] in s.candidates:
            continue
        p = n["properties"]
        if p["measurement_status"] == "measured":
            continue
        r = s.tools.get_requirements(indicator=p["code"])
        routes = []
        for t in r.get("tests") or []:
            reqs = [{"id": q["id"], "kind": q.get("kind"), "who": q.get("who_provides"),
                     "class": req_class(q)} for q in t["requires"]]
            cls = max((q["class"] for q in reqs), key=Q1_ORDER.index)
            routes.append({"route": t["route"], "test": t.get("test"), "class": cls,
                           "requires": reqs})
        # The record's own words, most specific field first.
        nmr = p.get("not_measured_reason")
        reason = (p.get("requirement_none_reason") or p.get("tier_unassigned_reason")
                  or (nmr.get("reason") if isinstance(nmr, dict) else nmr)
                  or r.get("reason") or "")
        if routes:
            cls = min((x["class"] for x in routes), key=Q1_ORDER.index)
            basis = "routes"
        else:
            pat = first([x for x, _, _ in REASON_CLASS], reason)
            if pat is None:
                raise SystemExit(f"FATAL: {p['code']} has no REQUIRES edge and its record "
                                 f"reason matches no REASON_CLASS pattern: {reason[:200]!r}")
            cls, phrase = next((k, ph) for x, k, ph in REASON_CLASS if x == pat)
            basis = f"record reason matches `{pat}`"
        rows.append({
            "indicator": p["code"], "node": n["id"], "status": p["measurement_status"],
            "tier": p.get("measurement_tier") or "unassigned", "class": cls, "basis": basis,
            "judged_on_cycle": any(leg in judged for leg, _ in s.rule_for(p["code"])),
            "record_text": reason, "routes": routes,
            "phrase": "" if routes else phrase,
        })
    return rows


def q1_claims(M: Map, rows: list) -> list:
    out = []
    by = Counter(r["class"] for r in rows)
    c = Claim("q1.partition", "Q1", "record")
    parts = [f"{c.n(by.get(k, 0), f'Q1 rows classed {k}')} `{k}`"
             for k in Q1_ORDER + (Q1_NOT_BLOCKED,)]
    c.text = (f"Of the framework's indicators the record does not mark measured "
              f"({c.n(len(rows), 'framework indicators whose measurement_status is not measured')}), "
              f"what blocks each partitions as: {', '.join(parts)}.")
    c.q("record.measurement_status").q("mcp.get_requirements")
    for r in rows:
        c.ev("indicator", r["node"], rec_loc(r["node"]), r["class"])
    out.append(c)
    for r in rows:
        code = r["indicator"]
        if r["class"] == "open_tooling":
            c = Claim(f"q1.{code}", "Q1", "needs_measurement")
            how = "; ".join(
                f"route `{x['route']}` needs " + ", ".join(f"`{q['id']}`" for q in x["requires"])
                for x in r["routes"] if x["class"] == "open_tooling") or r["phrase"]
            c.text = (f"`{code}` has no measured verdict in the record and can be measured from "
                      f"outside with public tooling and no agency action ({how}); it is to be "
                      f"measured before the summary is drafted (`DN-009 decision 6`).")
        else:
            c = Claim(f"q1.{code}", "Q1", "record")
            if r["routes"]:
                why = "; ".join(
                    f"route `{x['route']}` is `{x['class']}` (" +
                    ", ".join(f"`{q['id']}` from `{q['who']}`" for q in x["requires"]) + ")"
                    for x in r["routes"])
            else:
                why = "the record's reason is quoted in this claim's evidence"
            c.text = (f"`{code}` (status `{r['status']}`) is not measured, and what blocks it is "
                      f"`{r['class']}`: {why}.")
        c.ev("indicator", r["node"], rec_loc(r["node"]),
             f"{r['basis']}; record: {r['record_text']}" if r["record_text"] else r["basis"])
        c.q("mcp.get_requirements", f"get_requirements(indicator={code!r})")
        for x in r["routes"]:
            for q in x["requires"]:
                c.ev("query", "mcp.get_requirements", f"{RECORD_PATH}#{q['id']}",
                     f"route {x['route']}: {q['kind']}, provided by {q['who']}")
        out.append(c)
    return out


# ------------------------------------------------------------------------------ Q2

def q2_category(f: dict, classes: list) -> str:
    v = f["verdict"]
    if v == "pass":
        return "pass"
    denied = bool(set(classes) & set(DENIAL_CLASSES))
    if v == "error":
        return "access_denial" if denied else "error_other"
    if v != "fail":
        raise SystemExit(f"FATAL: {f['finding_id']} has verdict {v!r}")
    reason = f["reason"]
    if first(DENIAL_REASON, reason):
        return "access_denial"
    if first(NONCONFORMANT_REASON, reason):
        return "nonconformant"
    if first(ABSENCE_REASON, reason):
        return "absence"
    raise SystemExit(f"FATAL: fail reason of {f['finding_id']} matches no Q2 pattern: "
                     f"{reason[:200]!r}")


def q2_table(M: Map) -> tuple:
    where = M.body_of()
    oc = M.obs_classes
    rows = defaultdict(lambda: {**{k: 0 for k in Q2_COLUMNS}, "absence_with_denied_obs": 0,
                                "findings": 0, "denial_findings": []})
    tiers = {}
    for fid in sorted(M.findings):
        f = M.findings[fid]
        body, tier = where[f["target_doc_id"]]
        tiers[body] = tier
        cat = q2_category(f, oc[fid])
        r = rows[body]
        r[cat] += 1
        r["findings"] += 1
        if cat == "access_denial":
            r["denial_findings"].append(fid)
        if cat == "absence" and set(oc[fid]) & set(DENIAL_CLASSES):
            r["absence_with_denied_obs"] += 1
    table = []
    for b in sorted(rows):
        r = rows[b]
        table.append({"body": b, "tier": tiers[b], "findings": r["findings"],
                      **{k: r[k] for k in Q2_COLUMNS},
                      "absence_with_denied_obs": r["absence_with_denied_obs"],
                      "denial_findings": r["denial_findings"]})
    return table


def client_config(M: Map) -> dict:
    """The harness's client as the cycle records it: the user agent quoted by its A12
    findings, which read the host's answer to that client."""
    uas = set()
    fids = []
    for fid, f in sorted(M.findings.items()):
        if f.get("leg") == "A12":
            m = re.search(r"for (ai-readiness-kg-scanner/\S+ \(\+[^)]*\))", f["reason"])
            if m:
                uas.add(m.group(1))
                fids.append(fid)
    if len(uas) != 1:
        raise SystemExit(f"FATAL: the cycle's A12 findings quote {sorted(uas)} user agents, "
                         "not exactly one")
    mpath = REPO / "assessment" / "harness" / "scan" / "manners.py"
    return {"user_agent": uas.pop(), "finding_ids": fids,
            "client_line": BP.sym(mpath, 'headers={"User-Agent": self.p["user_agent"]})'),
            "dd060_line": BP.sym(REPO / "assessment" / "harness" / "scan" / "params.yaml",
                                 "DD-060: the instrument never varies its identity")}


def q2_claims(M: Map, table: list) -> list:
    out = []
    cfg = client_config(M)
    c = Claim("q2.client", "Q2", "record")
    c.text = (f"On cycle `{M.cycle}` the harness ran as one unauthenticated public client: it "
              f"identified itself as `{cfg['user_agent']}`, sent no credentials, cookies or "
              f"other identity (the client is built with the `User-Agent` header alone, "
              f"`{cfg['client_line']}`), and never varied that identity to get a better answer "
              f"(`DD-060`, `{cfg['dd060_line']}`).")
    c.q("cycle.client")
    for fid in cfg["finding_ids"]:
        c.ev("finding", fid, M.floc(fid), "A12 reason quotes the user agent")
    out.append(c)

    tot = {k: sum(r[k] for r in table) for k in Q2_COLUMNS}
    n = sum(r["findings"] for r in table)
    c = Claim("q2.totals", "Q2", "record")
    c.text = (f"Of the {c.n(n, 'finding_derived events on the cycle')} findings on cycle "
              f"`{M.cycle}`, {c.n(tot['access_denial'], 'Q2 access_denial, all bodies')} are "
              f"access denials to that client (an HTTP `401`, `403` or `429`, a robots.txt "
              f"disallow, or a connection reset by the host), {c.n(tot['absence'], 'Q2 absence, all bodies')} are "
              f"absences (the record, field or file is not served), "
              f"{c.n(tot['nonconformant'], 'Q2 nonconformant, all bodies')} find something "
              f"served that fails the rule's test, "
              f"{c.n(tot['error_other'], 'Q2 error_other, all bodies')} are other errors "
              f"(server errors, unparseable responses, a redirect loop), and "
              f"{c.n(tot['pass'], 'Q2 pass, all bodies')} pass.")
    c.q("cycle.findings").q("cycle.observation_classes")
    out.append(c)

    for r in table:
        if r["access_denial"] == 0:
            continue
        b = r["body"]
        c = Claim(f"q2.denial.{b}", "Q2", "record")
        tier = " (a tier C comparator, not a statistical body)" if r["tier"] == "C" else ""
        part = (f"; of its {c.n(r['absence'], f'Q2 absence for {b}')} absences, "
                f"{c.n(r['absence_with_denied_obs'], f'Q2 absences for {b} with denied observations excluded')} "
                f"were judged with some refused or disallowed probes excluded"
                if r["absence_with_denied_obs"] else
                f"; {c.n(r['absence'], f'Q2 absence for {b}')} "
                f"{'is an absence' if r['absence'] == 1 else 'are absences'}")
        c.text = (f"On cycle `{M.cycle}`, the harness's unauthenticated identified client met an "
                  f"access denial (a refusal by the host or a robots.txt disallow) on "
                  f"{c.n(r['access_denial'], f'Q2 access_denial for {b}')} of the "
                  f"{c.n(r['findings'], f'findings for {b}')} findings for `{b}`{tier}{part}, "
                  f"and {c.n(r['pass'], f'Q2 pass for {b}')} pass.")
        c.q("cycle.observation_classes")
        for fid in r["denial_findings"]:
            f = M.findings[fid]
            c.ev("finding", fid, M.floc(fid),
                 f"{f['leg']} {f['verdict']} on {f['target_doc_id']}: "
                 f"{', '.join(M.obs_classes[fid]) or 'reason'}")
        out.append(c)
    return out


# ------------------------------------------------------------------------------ Q3

def framework_start() -> tuple:
    line = BP.git_out("log", "--diff-filter=A", "--format=%H %ad", "--date=short", "--",
                      RECORD_PATH).splitlines()
    if not line:
        raise SystemExit(f"FATAL: git has no commit that added {RECORD_PATH}")
    sha, date = line[-1].split()
    return sha, date


def admissions() -> dict:
    """`{doc_id: (date, "shard:line")}`: the first `manifest_add` event for each document.
    The event log is the extraction-admission gate (CLAUDE.md invariant 2), so its first
    `manifest_add` is when a document entered the corpus. `screening.decided_at` on the
    manifest is NOT used: it carries the latest screening decision, and 49 admitted entries
    were re-screened after their first admission."""
    out = {}
    for f in sorted((REPO / "events").glob("*.jsonl")):
        for i, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            if '"manifest_add"' not in line:
                continue
            e = json.loads(line)
            if e.get("event_type") != "manifest_add":
                continue
            d = e.get("doc_id") or (e.get("payload") or {}).get("doc_id")
            ts = (e.get("timestamp") or "")[:10]
            if not d or not ts:
                raise SystemExit(f"FATAL: manifest_add at {BP.rel(f)}:{i} has no doc_id or "
                                 "timestamp")
            if d not in out or ts < out[d][0]:
                out[d] = (ts, f"{BP.rel(f)}:{i}")
    return out


def q3_claims(M: Map) -> tuple:
    inc = {k: v for k, v in M.s.manifest.items() if v["screening"]["decision"] == "included"}
    adm = admissions()
    missing = sorted(set(inc) - set(adm))
    if missing:
        raise SystemExit(f"FATAL: {len(missing)} admitted documents have no manifest_add "
                         f"event: {missing[:5]}")
    by_date = Counter(adm[k][0] for k in inc)
    v1 = sorted(k for k, v in inc.items() if "manifest_v1" in (v.get("provenance_sources") or []))
    v1_dates = sorted({adm[k][0] for k in v1})
    sha, start = framework_start()
    during = sorted(k for k in inc if adm[k][0] >= start and k not in v1)
    scans = [k for k in during if any(str(x).startswith("scan_")
                                      for x in inc[k].get("provenance_sources") or [])]
    c = Claim("q3.corpus_growth", "Q3", "record")
    c.text = (f"The corpus began as the v1 epoch of "
              f"{c.n(len(v1), 'included entries whose provenance_sources has manifest_v1')} "
              f"documents (first admitted `{v1_dates[0]}` to `{v1_dates[-1]}`) and holds "
              f"{c.n(len(inc), 'manifest entries with screening.decision included')} admitted "
              f"documents now; "
              f"{c.n(len(inc) - len(v1) - len(during), 'included, not v1, first admitted before the framework record')} "
              f"were added before the framework record was first committed (`{start}`, "
              f"`{sha[:12]}`) and {c.n(len(during), 'included, not v1, first admitted on or after the framework record')} "
              f"on or after it, of which {c.n(len(scans), 'of those, entries whose provenance is a scan epoch')} "
              f"are captured scan surfaces rather than literature.")
    c.q("manifest.included").q("manifest.admission_dates").q("git.framework_start", sha)
    for d in during:
        c.ev("document", d, adm[d][1],
             f"first manifest_add {adm[d][0]}; provenance "
             f"{', '.join(inc[d].get('provenance_sources') or [])}")
    table = [{"first_admitted": d, "documents": by_date[d]} for d in sorted(by_date)]
    return [c], table


# ------------------------------------------------------------------------------ Q4

def q4_claims(M: Map) -> list:
    where = M.body_of()
    hits, counts, urls = [], set(), {}
    for fid, f in sorted(M.findings.items()):
        if where[f["target_doc_id"]][0] != CENSUS:
            continue
        if not first(CATALOG_ABSENCE, f["reason"]):
            continue
        hits.append(fid)
        m = re.search(CATALOG_ABSENCE[0], f["reason"])
        if m:
            counts.add(int(m.group(1)))
        u = re.search(r"product page at (https://\S+?)[,;]? ", f["reason"])
        if u:
            urls.setdefault(f["target_doc_id"], set()).add(u.group(1).rstrip(","))
    if len(counts) != 1:
        raise SystemExit(f"FATAL: Census catalog-absence findings quote {sorted(counts)} "
                         "data.json record counts, not exactly one")
    # The product URL of each probed Census surface, from the published product matrix.
    pm = M.s.matrices()["product"][1]
    matrix_urls = {r["surface"]: r["url"] for r in pm["rows"] if r["agency"] == CENSUS}
    targets = sorted({M.findings[f]["target_doc_id"] for f in hits})
    probed = []
    for t in targets:
        u = matrix_urls.get(t) or ", ".join(sorted(urls.get(t, ()))) or "not recorded"
        probed.append(f"`{t}` (`{u}`)")
    legs = sorted({M.findings[f]["leg"] for f in hits}, key=BP.code_key)
    c = Claim("q4.census_catalog", "Q4", "record")
    c.text = (f"On cycle `{M.cycle}`, census.gov serves a catalog at "
              f"`https://www.census.gov/data.json` holding "
              f"{c.n(counts.pop(), 'data.json record count quoted by the Census catalog-absence findings')} "
              f"records, and {c.n(len(hits), 'Census findings whose reason is no data.json record for the product')} "
              f"Census findings on legs {', '.join(f'`{x}`' for x in legs)} "
              f"({c.n(len(legs), 'distinct legs among them')} legs) fail because no record in it "
              f"names the probed product; the surfaces probed were {'; '.join(probed)}.")
    c.q("cycle.findings")
    for fid in hits:
        f = M.findings[fid]
        c.ev("finding", fid, M.floc(fid), f"{f['leg']} on {f['target_doc_id']}")
    return [c]


# ------------------------------------------------------------------------------ Q5

def q5_claims(M: Map) -> tuple:
    s = M.s
    out, diffs = [], []
    pack = json.loads((BP.OUT / "numbers.json").read_text(encoding="utf-8"))

    def pack_value(page: str, source: str):
        for x in pack.get(page, []):
            if x["source"] == source:
                return x["value"]
        return None

    def compare(label, mine, page, source):
        theirs = pack_value(page, source)
        if theirs is not None and str(theirs).replace(",", "") != str(mine):
            diffs.append({"number": label, "pack": theirs, "pack_source": f"{page}: {source}",
                          "script": mine})

    inds = s.inds
    fw = [n for n in inds if n["id"] not in s.candidates]
    cand = sorted(n["properties"]["code"] for n in inds if n["id"] in s.candidates)
    counts = s.record["counts"]
    c = Claim("q5.indicators", "Q5", "record")
    c.text = (f"The framework record holds {c.n(len(inds), 'AssessmentIndicator nodes in the record')} "
              f"indicators, {c.n(len(fw), 'indicators not held out as candidates')} in the "
              f"framework and {c.n(len(cand), 'candidate indicators')} candidate "
              f"({', '.join(f'`{x}`' for x in cand)}), which enters no framework count until the "
              f"operator adopts it (`DD-054`).")
    if counts["indicators"] != len(fw) or counts["candidate_indicators"] != len(cand):
        raise SystemExit("FATAL: the record's counts disagree with its own nodes")
    c.q("record.indicator_nodes").q("record.counts").q("record.candidates")
    for n in inds:
        if n["id"] in s.candidates:
            c.ev("indicator", n["id"], rec_loc(n["id"]), "candidate")
    compare("indicator nodes", len(inds), "H_limits.md", "AssessmentIndicator nodes in the record")
    compare("framework indicators", len(fw), "H_limits.md", "record counts.indicators")
    out.append(c)

    crit = sorted(n["properties"]["code"] for n in s.record["nodes"]
                  if "AssessmentCriterion" in n["labels"])
    kept = [x for x in crit if x in BP.USAFACTS_CRITERIA]
    added = [x for x in crit if x not in BP.USAFACTS_CRITERIA]
    if sorted(kept) != sorted(BP.USAFACTS_CRITERIA):
        raise SystemExit("FATAL: a USAFacts criterion is missing from the record")
    c = Claim("q5.criteria", "Q5", "record")
    c.text = (f"The framework keeps USAFacts' {c.n(len(kept), 'USAfacts criteria in the record')} "
              f"criteria ({', '.join(f'`{x}`' for x in kept)}: accessible, understandable, "
              f"accurate, open) and adds {c.n(len(added), 'criteria added beyond USAFacts')} "
              f"({', '.join(f'`{x}`' for x in added)}), for "
              f"{c.n(len(crit), 'AssessmentCriterion nodes in the record')} in all.")
    c.q("record.criteria")
    out.append(c)

    fw_codes = {n["properties"]["code"] for n in fw}
    rule_codes = {s.R.parse_rule_id(r)["indicator_code"] for r in s.R.CURRENT.values()}
    with_rule = sorted(rule_codes & fw_codes, key=BP.code_key)
    outside = sorted(rule_codes - fw_codes, key=BP.code_key)
    c = Claim("q5.current_rules", "Q5", "record")
    c.text = (f"{c.n(len(with_rule), 'framework indicators with a current rule')} of the "
              f"framework's {c.n(len(fw), 'indicators not held out as candidates')} indicators "
              f"have a current rule, of "
              f"{c.n(len(set(s.R.CURRENT.values())), 'distinct current rules in rules.CURRENT')} "
              f"current rules in all; the others are on "
              f"{', '.join(f'`{x}`' for x in outside) or 'nothing'}, outside the framework count.")
    c.q("rules.current")
    compare("indicators with a current rule", len(with_rule), "B_usafacts_delta.md",
            "indicators with a current rule in rules.CURRENT")
    out.append(c)

    ms = Counter(n["properties"]["measurement_status"] for n in fw)
    c = Claim("q5.measurement_status", "Q5", "record")
    c.text = (f"Of the framework's {c.n(len(fw), 'indicators not held out as candidates')} "
              f"indicators the record marks {c.n(ms['measured'], 'measurement_status measured')} "
              f"measured, {c.n(ms['harness_built'], 'measurement_status harness_built')} with a "
              f"harness built but not marked measured, and "
              f"{c.n(ms['specified'], 'measurement_status specified')} specified only.")
    if counts["indicators_measured"] != ms["measured"]:
        raise SystemExit("FATAL: counts.indicators_measured disagrees with the nodes")
    c.q("record.measurement_status")
    out.append(c)

    sc = s.score
    bodies = __import__("prescriptions").bodies(M.cycle)
    ranked = sorted(b for b, v in sc["bodies"].items() if v.get("rank") is not None)
    unranked = sorted(set(bodies) - set(ranked))
    c = Claim("q5.bodies", "Q5", "record")
    c.text = (f"{c.n(len(bodies), 'bodies on the cycle (prescriptions.bodies)')} statistical "
              f"bodies are on cycle `{M.cycle}` and {c.n(len(ranked), 'bodies with a rank (score.py)')} "
              f"are ranked; {', '.join(f'`{x}`' for x in unranked)} have no scored leg with a "
              f"judged row.")
    c.q("cycle.bodies").q("score.compute")
    out.append(c)

    legs = sorted({f["leg"] for f in M.findings.values()}, key=BP.code_key)
    res = s.gread("MATCH (r:Artifact:Result) WHERE r.name = $n RETURN r.artifact_id AS id, "
                  "r.value AS v, r.state AS st", n=f"scan_findings_{M.cycle[len('scan_'):]}")
    c = Claim("q5.legs_findings", "Q5", "record")
    c.text = (f"Cycle `{M.cycle}` judged {c.n(len(legs), 'distinct legs on the cycle')} legs and "
              f"holds {c.n(len(M.findings), 'finding_derived events on the cycle')} findings.")
    c.q("cycle.legs").q("cycle.findings", BP.rel(M.shard))
    for r in res:
        if int(r["v"]) != len(M.findings):
            diffs.append({"number": "findings on the cycle", "pack": r["v"],
                          "pack_source": f"Result {r['id']}", "script": len(M.findings)})
        c.ev("result", r["id"], f"neo4j:Result{{artifact_id: '{r['id']}'}}",
             f"scan_findings, value {r['v']:g}, state {r['st']}")
    out.append(c)

    b = s.tools.get_body(CENSUS)
    where = M.body_of()
    n_all = sum(1 for f in M.findings.values() if where[f["target_doc_id"]][0] == CENSUS)
    c = Claim("q5.census_failing", "Q5", "record")
    c.text = (f"On the published matrices of cycle `{M.cycle}`, `{CENSUS}` has "
              f"{c.n(b['n_failing'], 'get_body n_failing')} failing of "
              f"{c.n(b['n_judged'], 'get_body n_judged')} judged rows; the matrices publish one "
              f"row per leg and surface they report, so they carry fewer rows than the "
              f"{c.n(n_all, f'findings for {CENSUS}')} findings the cycle holds for the body "
              f"across all its probed surfaces.")
    c.q("mcp.get_body")
    for leg in b["legs"]:
        if leg["verdict"] == "fail" and leg["finding_id"]:
            c.ev("finding", leg["finding_id"], M.floc(leg["finding_id"]),
                 f"{leg['leg']} fail on {leg['surface']}")
    out.append(c)

    conc = sc["bodies"][CENSUS]["concentration"]
    bs = sc["bodies"][CENSUS]
    c = Claim("q5.census_rank", "Q5", "record")
    c.text = (f"`{CENSUS}` ranks {c.n(conc['rank'], 'score.py concentration.rank')} of "
              f"{c.n(conc['of'], 'score.py concentration.of')} under the hierarchical "
              f"equal-weight score ({c.n(bs['score'], 'score.py bodies.CENSUS.score', '.3f')}), "
              f"and the rank rests on one leg, `{conc['leg']}`: "
              f"{c.n(conc['pass'], 'score.py concentration.pass')} pass of "
              f"{c.n(conc['judged'], 'score.py concentration.judged')} judged row; were that "
              f"verdict reversed it would rank {c.n(conc['rank_if_reversed'], 'score.py concentration.rank_if_reversed')}.")
    c.q("score.compute")
    for leg in b["legs"]:
        if leg["leg"] == conc["leg"] and leg["finding_id"]:
            c.ev("finding", leg["finding_id"], M.floc(leg["finding_id"]),
                 f"{leg['leg']} {leg['verdict']} on {leg['surface']}")
    out.append(c)

    from report_traceability import locators
    edges = [e for e in s.edges if e["type"] == "EVIDENCED_BY"]
    per = {}
    for n in inds:
        locs = locators(n["properties"].get("evidence_raw") or "")
        per[n["id"]] = locs
    located = [i for i, l in per.items() if any(l.values())]
    edges_loc = sum(1 for e in edges if per.get(e["from"], {}).get(e["properties"]["doc_id"]))
    no_edge = [n["id"] for n in inds if not any(e["from"] == n["id"] for e in edges)]
    inc = {k for k, v in s.manifest.items() if v["screening"]["decision"] == "included"}
    cited = {e["properties"]["doc_id"] for e in edges} & inc
    c = Claim("q5.evidence_coverage", "Q5", "record")
    c.text = (f"Evidence coverage in the record: {c.n(len(located), 'indicators whose evidence cell carries a locator')} "
              f"of {c.n(len(inds), 'AssessmentIndicator nodes in the record')} indicator evidence "
              f"cells carry a pinpoint locator; {c.n(edges_loc, 'EVIDENCED_BY edges whose document has a locator in the cell')} "
              f"of {c.n(len(edges), 'EVIDENCED_BY edges in the record')} `EVIDENCED_BY` edges point "
              f"at a located document; {c.n(len(no_edge), 'indicators with no EVIDENCED_BY edge')} "
              f"indicators have no `EVIDENCED_BY` edge; and "
              f"{c.n(len(cited), 'admitted documents cited by an EVIDENCED_BY edge')} of the "
              f"{c.n(len(inc), 'manifest entries with screening.decision included')} admitted "
              f"documents are cited by one.")
    c.q("traceability.locators").q("manifest.included")
    compare("located cells", len(located), "C_provenance.md",
            "indicators whose evidence cell carries a locator (report_traceability.locators)")
    compare("edges with locator", edges_loc, "C_provenance.md",
            "EVIDENCED_BY edges whose document has a locator in the cell")
    compare("EVIDENCED_BY edges", len(edges), "C_provenance.md", "EVIDENCED_BY edges in the record")
    compare("indicators with no edge", len(no_edge), "C_provenance.md",
            "indicators with no EVIDENCED_BY edge")
    for i in located:
        c.ev("indicator", i, rec_loc(i), "evidence cell carries a locator")
    out.append(c)
    return out, diffs


# ------------------------------------------------------------------------------ Q6

def q6_claims(M: Map) -> list:
    sc = M.s.score
    bs = sc["bodies"][CENSUS]
    b = M.s.tools.get_body(CENSUS)
    failing = defaultdict(list)
    for leg in b["legs"]:
        if leg["verdict"] == "fail" and leg["finding_id"]:
            failing[leg["leg"]].append(leg)
    out = []
    acts = [a for a in bs["prescriptions"] if a["effort"] == "hours" and a["cost"] == "none"]
    for a in acts:
        slug = a["action"][len("act:"):]
        c = Claim(f"q6.{slug}", "Q6", "record")
        c.text = (f"For `{CENSUS}`, the action \"{a['title']}\" (`{a['action']}`, leg `{a['leg']}`) "
                  f"is in the notional `hours` effort band with no cost, and under equal weights it "
                  f"can raise the body's hierarchical score by at most "
                  f"{c.n(round(a['delta'], 3), 'score.py prescription delta for ' + a['action'])}, "
                  f"the bound if every failing row on `{a['leg']}` passed; no weighting is "
                  f"asserted, so this is a bound, not a value.")
        c.q("score.compute", f"bodies.{CENSUS}.prescriptions")
        c.ev("query", "score.compute", rec_loc(a["action"]), "the Action node on the record")
        for leg in failing.get(a["leg"], []):
            c.ev("finding", leg["finding_id"], M.floc(leg["finding_id"]),
                 f"{leg['leg']} fail on {leg['surface']}")
        out.append(c)
    return out


# ------------------------------------------------------------------------------ render

def existing() -> dict:
    if not CLAIMS.is_file():
        return {"claims": []}
    return yaml.safe_load(CLAIMS.read_text(encoding="utf-8")) or {"claims": []}


def assign_ids(mine: list, prior: dict) -> list:
    """`[(id, claim)]`. Reuse the id this script gave the same key before; a new key takes
    the next id after the highest in the file, so no id is ever reused for a different claim."""
    held = {c["key"]: c["id"] for c in prior.get("claims", [])
            if c.get("source_task") == TASK and c.get("key")}
    taken = [int(c["id"][3:]) for c in prior.get("claims", []) if re.fullmatch(r"CL-\d{3,}", c.get("id", ""))]
    nxt = max(taken, default=0) + 1
    out = []
    for c in mine:
        if c.key in held:
            cid = held[c.key]
        else:
            cid = f"CL-{nxt:03d}"
            nxt += 1
        out.append((cid, c))
    return out


def render(graph) -> str:
    M = Map(graph)
    q1 = q1_rows(M)
    q2 = q2_table(M)
    q3c, q3t = q3_claims(M)
    q5c, diffs = q5_claims(M)
    mine = (q1_claims(M, q1) + q2_claims(M, q2) + q3c + q4_claims(M) + q5c + q6_claims(M))
    keys = [c.key for c in mine]
    if len(keys) != len(set(keys)):
        raise SystemExit(f"FATAL: duplicate claim keys {[k for k in keys if keys.count(k) > 1]}")
    prior = existing()
    ours = {cid: c.as_dict(cid) for cid, c in assign_ids(mine, prior)}
    others = {c["id"]: c for c in prior.get("claims", []) if c.get("source_task") != TASK}
    clash = set(ours) & set(others)
    if clash:
        raise SystemExit(f"FATAL: ids {sorted(clash)} are held by another task's claims")
    allc = {**others, **ours}
    claims = [allc[k] for k in sorted(allc, key=lambda x: int(x[3:]))]
    doc = {
        "schema_version": SCHEMA_VERSION,
        "generated_by": f"{GENERATOR} ({TASK}) for the entries whose source_task is that task; "
                        "other entries are carried through. Do not edit generated entries: "
                        "re-run the generator.",
        "cycle_of_record": M.cycle,
        "framework_record_commit": M.s.record_commit[:12],
        "claims": claims,
        "tables": {
            "q1_measurement_boundary": [
                {k: (v if k != "routes" else [
                    {"route": x["route"], "class": x["class"],
                     "requires": [f"{q['id']} ({q['kind']}, {q['who']})" for q in x["requires"]]}
                    for x in v]) for k, v in r.items() if k not in ("node", "phrase")} for r in q1],
            "q2_findings_by_body": [{k: v for k, v in r.items() if k != "denial_findings"}
                                    for r in q2],
            "q3_admissions_by_date": q3t,
            "q5_numbers_that_differ_from_the_pack": diffs,
        },
    }
    return yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, width=100,
                          default_flow_style=False)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    graph = BP.graph_or_none(required=True)
    text = render(graph)
    if a.check:
        ok = CLAIMS.is_file() and CLAIMS.read_text(encoding="utf-8") == text
        print(f"{BP.rel(CLAIMS)}: {'no drift' if ok else 'DRIFT'}")
        return 0 if ok else 1
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if not CLAIMS.is_file() or CLAIMS.read_text(encoding="utf-8") != text:
        CLAIMS.write_text(text, encoding="utf-8")
    print(f"wrote {BP.rel(CLAIMS)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
