#!/usr/bin/env python3
"""Evidence for the DCAT-US 3.0 FAQ, by query, from the two graphs. **Zero spend, no network.**

`cc_tasks/2026-10-05_DCAT-003_dcat_us_3_faq_for_omb_meeting.md` step 1, implementing DN-011-R5
(`docs/design/2026-10-04_DN-011_dcat_us_3_intake.md`). For each question in
`reports/dcat_us_3_faq/faq_config.yaml` this writes `reports/dcat_us_3_faq/evidence/Q<n>.json`:
every passage that matched the question's terms in the question's documents, ranked, capped,
each with its locator and its verbatim text. The answer and validator calls
(`scripts/dcat_faq_run.py`) see that file and nothing else.

**Where passages come from**, all read-only:

* **fss-policy-kg** (local Neo4j database `fss-policy-kg`, release v7.18): `Segment.text` of the
  question's documents, and `Obligation.verbatim_span` with its force. Locator: document id and
  segment id. `CatalogEntry` rows that record a document as not public or not admitted.
* **ai-readiness-kg** (Neo4j database `seldon-ai-readiness-kg`): the `grounding_span` of
  extracted nodes, which `kg/extraction/grounding.py` verified verbatim against the document
  when it was admitted. Locator: node key and its `location`. For admitted web pages, the
  converted document text the extraction read (`state/substrate_md/<doc>.md`, hashed on its
  `substrate_converted` event), cut into paragraphs and table rows. Locator: document id, the
  nearest heading and the line number.
* **The framework record** (`framework/ai_readiness_framework.json`) for indicator text (Q11).
* **Computed tables** (Q4, Q6, Q7, Q10): the requirement level of every Dataset property, read
  by code from three versions of the schema and from the v1.1 schema, each cell carrying the
  verbatim line it was read from. Nothing in a table is typed by hand.

**Method, and the prior art it follows.** Evidence is retrieved before any model call and
frozen to a file; the model may cite only passage ids in that file; a separate call checks each
cited sentence against the cited passages. That is attribution as the field defines it:
"attributable to identified sources" (AIS, Rashkin et al. 2021, *Measuring Attribution in
Natural Language Generation Models*), with support judged per claim against the cited text
(FActScore, Min et al. 2023; citation precision and recall in ALCE, Gao et al. 2023, *Enabling
Large Language Models to Generate Text with Citations*). Retrieval here is lexical by design:
the questions name terms of art (property names, standard numbers), and a lexical match is a
locator a reader can re-run.

    /opt/anaconda3/bin/python3 scripts/dcat_faq_evidence.py [--only N]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
for _p in ("", "scripts"):
    if str(REPO / _p) not in sys.path:
        sys.path.insert(0, str(REPO / _p))

import yaml  # noqa: E402

OUT = REPO / "reports" / "dcat_us_3_faq"
CONFIG = OUT / "faq_config.yaml"
EVIDENCE_DIR = OUT / "evidence"
TABLE_JSON = OUT / "evidence" / "element_levels.json"
CATALOG_JSON = OUT / "evidence" / "catalog_entries.json"
FRAMEWORK = REPO / "framework" / "ai_readiness_framework.json"
GENERATOR = "scripts/dcat_faq_evidence.py"

#: The schema texts the element table is read from (ai-readiness-kg doc ids).
FINAL = "dcat-us-3-dataset-schema-2026-09-15"
EARLIER = "dcat-us-3-dataset-schema"
DRAFT = "dcat-us-3-candidate-recommendation-snapshot"
V11 = "dcat-us-1-1-schema"
#: The Dataset page as served on 2026-10-05, a dated version of EARLIER (DD-068), admitted by
#: `scripts/admit_dcat_us_3_live_2026_10_05.py` (DCAT-003 ADDENDUM 01 step 4). It is the fifth
#: column of the attachment's table. It is NOT part of a table row's evidence text
#: (`row_text`): the answers already written were checked against four-version rows, and a
#: row that changed under them would orphan their checked units.
LIVE = "dcat-us-3-dataset-schema-2026-10-05"
#: The four versions a row's evidence text quotes, in this order.
ROW_TEXT_DOCS = (FINAL, EARLIER, DRAFT, V11)

#: The working draft names a property by its RDF term; the published schema by a JSON key.
#: Most keys are the term's local name. These are the exceptions, each read off the two texts:
#: the draft's "other identifier" is `adms:identifier`, the published `otherIdentifier`; its
#: "category" is `dcterms:type`, the published `category`; its "documentation" is `foaf:page`,
#: the published `page`. Anything not matched is reported as draft-only, never guessed.
DRAFT_TERM_TO_KEY = {"adms:identifier": "otherIdentifier", "dcterms:type": "category",
                     "foaf:page": "page"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_config(path: Path = CONFIG) -> dict:
    cfg = yaml.safe_load(path.read_text(encoding="utf-8"))
    for q in cfg["questions"]:
        if not isinstance(q.get("id"), int) or not q.get("text"):
            raise SystemExit(f"FATAL: malformed question in {path}: {q}")
    return cfg


def expand(scope: list, groups: dict) -> list:
    out = []
    for s in scope or []:
        if isinstance(s, list):
            out += s
        elif s in groups:
            out += groups[s]
        else:
            raise SystemExit(f"FATAL: scope {s!r} is neither a group nor a list of doc ids")
    return list(dict.fromkeys(out))


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip()


def matched_terms(text: str, terms: list) -> list:
    low = (text or "").lower()
    return [t for t in terms if t in low]


# ----------------------------------------------------------------------------------- graphs

def driver():
    from neo4j import GraphDatabase
    import build_projection
    logging.getLogger("neo4j").setLevel(logging.ERROR)
    uri, user, pw = build_projection._neo4j_creds()
    return GraphDatabase.driver(uri, auth=(user, pw))


def q(drv, db: str, cypher: str, **params) -> list:
    with drv.session(database=db) as s:
        return [dict(r) for r in s.run(cypher, **params)]


def doc_meta(drv, cfg: dict) -> dict:
    """doc_id -> {title, issuer, date, url, graph} for every document either graph holds. Where a
    document is in both, each graph keeps its own entry under its own id."""
    meta = {}
    for r in q(drv, cfg["graphs"]["fss_database"],
               "MATCH (d:Document) OPTIONAL MATCH (d)-[:ISSUED_BY]->(a:Authority) "
               "RETURN d.id AS id, d.title AS title, d.baseline_date AS date, "
               "d.source_url AS url, collect(a.name) AS issuer"):
        meta[r["id"]] = {"title": r["title"], "issuer": "; ".join(x for x in r["issuer"] if x),
                         "date": r["date"], "url": r["url"], "graph": "fss-policy-kg"}
    entries = json.loads((REPO / "corpus" / "manifest.json").read_text(encoding="utf-8"))["entries"]
    for r in q(drv, cfg["graphs"]["airkg_database"],
               "MATCH (d:Document) RETURN d.doc_id AS id, d.title AS title, d.pub_date AS date, "
               "d.primary_url AS url"):
        ident = (entries.get(r["id"]) or {}).get("identity") or {}
        meta[r["id"]] = {"title": r["title"], "issuer": "; ".join(ident.get("authors_or_org") or []),
                         "date": r["date"], "url": r["url"] or ident.get("source_url"),
                         "graph": "ai-readiness-kg"}
    return meta


def fss_passages(drv, db: str, docs: list, terms: list) -> list:
    rows = q(drv, db,
             "MATCH (d:Document)-[:CONTAINS]->(s:Segment) WHERE d.id IN $docs "
             "AND any(t IN $terms WHERE toLower(s.text) CONTAINS t) "
             "RETURN d.id AS doc, s.seg_id AS seg, s.text AS text ORDER BY d.id, s.seg_id",
             docs=docs, terms=terms)
    out = [{"graph": "fss-policy-kg", "kind": "passage", "doc_id": r["doc"],
            "locator": {"segment": r["seg"]}, "section": f"passage {r['seg'].split('#s')[-1]}",
            "text": r["text"]} for r in rows]
    rows = q(drv, db,
             "MATCH (d:Document)-[:CONTAINS]->(s:Segment)-[:STATES]->(o:Obligation) "
             "WHERE d.id IN $docs AND any(t IN $terms WHERE toLower(o.verbatim_span) CONTAINS t) "
             "RETURN d.id AS doc, s.seg_id AS seg, o.obl_id AS obl, o.force AS force, "
             "o.verbatim_span AS text ORDER BY d.id, s.seg_id",
             docs=docs, terms=terms)
    out += [{"graph": "fss-policy-kg", "kind": f"{r['force']} (as extracted)", "doc_id": r["doc"],
             "locator": {"segment": r["seg"], "obligation": r["obl"]},
             "section": f"passage {r['seg'].split('#s')[-1]}", "text": r["text"]} for r in rows]
    return out


def airkg_node_passages(drv, db: str, labels: list, docs: list, terms: list) -> list:
    rows = q(drv, db,
             "MATCH (n) WHERE n.doc_id IN $docs AND n.grounding_span IS NOT NULL "
             "AND any(l IN labels(n) WHERE l IN $labels) "
             "AND any(t IN $terms WHERE toLower(n.grounding_span) CONTAINS t) "
             "RETURN n.doc_id AS doc, n.key AS key, labels(n)[0] AS label, n.location AS loc, "
             "n.grounding_span AS text ORDER BY n.doc_id, n.key",
             docs=docs, terms=terms, labels=labels)
    return [{"graph": "ai-readiness-kg", "kind": f"extracted {r['label'].lower()} span",
             "doc_id": r["doc"], "locator": {"node": r["key"], "location": r["loc"]},
             "section": human_location(r["loc"]), "text": r["text"]} for r in rows]


def human_location(loc: str | None) -> str:
    """`location` is a section or page when the extractor recorded one, else `doc#c0003` (the
    extraction chunk), which is pipeline vocabulary and is not shown to a reader."""
    if not loc or re.search(r"#c\d+$", loc):
        return ""
    return loc


def substrate_passages(docs: list, terms: list, substrate_dir: Path) -> list:
    out = []
    for doc in docs:
        p = substrate_dir / f"{doc}.md"
        if not p.is_file():
            continue
        heading = ""
        para, start = [], None
        lines = p.read_text(encoding="utf-8").splitlines()

        def flush():
            if para:
                text = "\n".join(para).strip()
                if matched_terms(text, terms):
                    out.append({"graph": "ai-readiness-kg", "kind": "document text",
                                "doc_id": doc, "locator": {"file": p.relative_to(REPO).as_posix(),
                                                           "line": start},
                                "section": heading, "text": text})

        for i, line in enumerate(lines, 1):
            if line.startswith("#"):
                flush()
                para, start = [], None
                heading = norm(re.sub(r"\[#\]\([^)]*\)", "", line.lstrip("#"))).strip("` ")
                continue
            is_row = line.lstrip().startswith("|") or line.count(" | ") >= 2
            if not line.strip() or is_row:
                flush()
                para, start = [], None
                if is_row and not set(line.strip()) <= set("|-: "):
                    if matched_terms(line, terms):
                        out.append({"graph": "ai-readiness-kg", "kind": "document text (table row)",
                                    "doc_id": doc,
                                    "locator": {"file": p.relative_to(REPO).as_posix(), "line": i},
                                    "section": heading, "text": norm(line)})
                continue
            if start is None:
                start = i
            para.append(line)
        flush()
    return out


def catalog_entries(drv, db: str, meta: dict) -> list:
    """fss-policy-kg's records of DCAT-related documents it looked for and did not admit, minus
    any document the collection holds anyway. ai-readiness-kg admitted the crosswalk, the B3.3
    slides and the DSWG report that fss-policy-kg declined as out of its scope; shown as "not
    admitted", those records read as "not available", which is false for the collection. A
    record is HELD when its source URL is a held document's URL, or its title is the start of a
    held document's title (the DSWG record names the landing page, the held copy the PDF)."""
    rows = q(drv, db,
             "MATCH (c:CatalogEntry) WHERE c.id =~ '(dcat|fairness|cdoc|fcsm_2024).*' "
             "RETURN c.id AS id, c.title AS title, c.disposition AS disp, c.source_url AS url, "
             "c.notes AS notes, c.agency_or_govwide AS issuer, c.effective_date AS date "
             "ORDER BY c.id")
    urls = {m.get("url") for m in meta.values() if m.get("url")}
    titles = [norm(m.get("title") or "").lower() for m in meta.values()]
    out = []
    for r in rows:
        t = norm(r["title"] or "").lower()
        held = (r["url"] and r["url"] in urls) or (t and any(x.startswith(t) for x in titles))
        if held:
            continue
        out.append({"graph": "fss-policy-kg", "kind": "catalog record (not admitted)", "doc_id": r["id"],
                    "locator": {"catalog_entry": r["id"]}, "section": r["disp"] or "",
                    "text": f"{r['title']}. {r['notes'] or ''}".strip(),
                    # The record's own fields, for the FAQ's list of documents not used
                    # (ADDENDUM 01 step 1, Part B). Not part of the evidence hash.
                    "record": {"title": r["title"], "issuer": r["issuer"], "date": r["date"],
                               "url": r["url"]}})
    return out


def framework_passages(terms: list) -> list:
    rec = json.loads(FRAMEWORK.read_text(encoding="utf-8"))
    out = []
    for n in rec["nodes"]:
        props = n.get("properties") or {}
        text = props.get("indicator")
        if n.get("type") != "AssessmentIndicator" and not n["id"].startswith("ind:"):
            continue
        if text and matched_terms(text, terms):
            out.append({"graph": "framework record", "kind": "indicator", "doc_id": "framework",
                        "locator": {"record_node": n["id"],
                                    "file": FRAMEWORK.relative_to(REPO).as_posix()},
                        "section": n["id"].replace("ind:", "indicator "), "text": text})
    return out


# ------------------------------------------------------------------------- computed: levels

def final_levels(doc: str, substrate_dir: Path) -> dict:
    """key -> {level, line, text}, from the page's per-property sections, a heading followed by
    "**Requirement:** Level". The two captures render the heading differently, so both forms
    are read: "## `Dataset > key` [#](...)" (2026-08-21) and "## [Dataset &gt; key #](#key)"
    (2026-09-15)."""
    lines = (substrate_dir / f"{doc}.md").read_text(encoding="utf-8").splitlines()
    out, cur = {}, None
    for i, line in enumerate(lines, 1):
        m = re.match(r"^##\s+\[?`?Dataset (?:>|&gt;) ([A-Za-z@_]+)", line)
        if m:
            cur = (m.group(1).strip(), i, norm(line))
            continue
        m = re.match(r"^\*\*Requirement:\*\*\s*(\w+)", line.strip())
        if m and cur:
            key, hl, htext = cur
            out[key] = {"level": m.group(1), "line": hl,
                        "text": f"{htext} {norm(line)}"}
            cur = None
    if not out:
        raise SystemExit(f"FATAL: no per-property requirement lines parsed from {doc}")
    return out


def draft_levels(doc: str, substrate_dir: Path) -> dict:
    """key -> {level, line, text, label, term}, from the draft's Dataset section only (between
    "## Dataset" and "## Dataset Series"): "#### Property: label", its "Requirement level" row
    and its "URI" row."""
    lines = (substrate_dir / f"{doc}.md").read_text(encoding="utf-8").splitlines()
    try:
        a = lines.index("## Dataset")
        b = lines.index("## Dataset Series")
    except ValueError as exc:
        raise SystemExit(f"FATAL: {doc}: Dataset section bounds not found ({exc})")
    out, cur = {}, None

    def close(c):
        """A block with a URI is recorded; one with no "Requirement level" row (the draft's
        `has version` has none) is recorded as listed with its level not stated, never dropped."""
        if not c or not c.get("term"):
            return
        term = c["term"]
        key = DRAFT_TERM_TO_KEY.get(term, term.split(":", 1)[1])
        level = c.get("level") or "not stated"
        lt = c.get("level_text") or "no Requirement level row"
        out.setdefault(key, {"level": level, "line": c["line"], "label": c["label"], "term": term,
                             "text": f"Property: {c['label']} | {lt} | URI {term}"})

    for i in range(a, b):
        line = lines[i]
        m = re.match(r"^#### Property:\s*(.+)$", line)
        if m:
            close(cur)
            cur = {"label": m.group(1).strip(), "line": i + 1, "level": None, "term": None}
            continue
        if cur is None:
            continue
        m = re.match(r"^\|\s*Requirement level\s*\|\s*\**(\w+)\**", line)
        if m and not cur.get("level"):
            cur["level"] = m.group(1)
            cur["level_text"] = norm(line)
        m = re.match(r"^\|\s*URI\s*\|\s*(.+?)\s*\|\s*$", line)
        if m and not cur.get("term"):
            t = re.search(r"`+\s*([A-Za-z-]+:[A-Za-z_]+)\s*`+", m.group(1))
            cur["term"] = t.group(1) if t else None
    close(cur)
    if not out:
        raise SystemExit(f"FATAL: no draft property levels parsed from {doc}")
    return out


def v11_levels(doc: str, substrate_dir: Path) -> dict:
    """field -> {status, line, text}, top-level Dataset fields from the "#### Dataset Fields"
    guidance section: "**Field[#](...)** | **name**" then "**Required** | value"."""
    lines = (substrate_dir / f"{doc}.md").read_text(encoding="utf-8").splitlines()
    try:
        a = lines.index("#### Dataset Fields")
    except ValueError:
        raise SystemExit(f"FATAL: {doc}: '#### Dataset Fields' not found")
    out, cur = {}, None
    for i in range(a, len(lines)):
        line = lines[i]
        if i > a and line.startswith("### "):
            break
        m = re.match(r"^\*\*Field\[#\]\([^)]*\)\*\*\s*\|\s*\*\*(.+?)\*\*", line)
        if m:
            cur = (m.group(1).strip(), i + 1)
            continue
        m = re.match(r"^\*\*Required\*\*\s*\|\s*(.+?)\s*$", line)
        if m and cur:
            name, ln = cur
            if "→" not in name:
                out[name] = {"status": m.group(1), "line": ln,
                             "text": f"Field {name} | Required | {m.group(1)}"}
            cur = None
    if not out:
        raise SystemExit(f"FATAL: no v1.1 dataset fields parsed from {doc}")
    return out


def element_table(substrate_dir: Path) -> list:
    live = final_levels(LIVE, substrate_dir)
    fin = final_levels(FINAL, substrate_dir)
    ear = final_levels(EARLIER, substrate_dir)
    dra = draft_levels(DRAFT, substrate_dir)
    v11 = v11_levels(V11, substrate_dir)
    keys = list(dict.fromkeys([*fin, *ear, *dra, *v11, *live]))
    rows = []
    for k in keys:
        if k.startswith("@"):
            continue
        cells = {"element": k,
                 "level_2026_09_15": (fin.get(k) or {}).get("level"),
                 "level_2026_08_21": (ear.get(k) or {}).get("level"),
                 "draft_level": (dra.get(k) or {}).get("level"),
                 "v11_required": (v11.get(k) or {}).get("status"),
                 "level_2026_10_05": (live.get(k) or {}).get("level"),
                 "sources": {}}
        for doc, src in ((FINAL, fin), (EARLIER, ear), (DRAFT, dra), (V11, v11), (LIVE, live)):
            if k in src:
                cells["sources"][doc] = {"line": src[k]["line"], "text": src[k]["text"],
                                         "file": f"state/substrate_md/{doc}.md"}
        rows.append(cells)
    order = {"Mandatory": 0, "Recommended": 1, "Optional": 2, None: 3}
    rows.sort(key=lambda r: (order.get(r["level_2026_09_15"], 3), r["element"].lower()))
    return rows


def row_text(r: dict) -> str:
    """One evidence item per element: the verbatim line from each source that has it, labelled
    by the source. The labels are this script's; every quoted part is the source's own text."""
    names = {FINAL: "DCAT-US 3.0 Dataset page (2026-09-15)",
             EARLIER: "DCAT-US 3.0 Dataset page (2026-08-21)",
             DRAFT: "DCAT-US 3 working draft (Candidate Recommendation, 2025)",
             V11: "DCAT-US v1.1 schema"}
    parts = [f"{names[d]}: {s['text']}" for d, s in r["sources"].items() if d in ROW_TEXT_DOCS]
    absent = [names[d] for d in ROW_TEXT_DOCS if d not in r["sources"]]
    if absent:
        parts.append("Not listed in: " + "; ".join(absent))
    return f"Element {r['element']}. " + " || ".join(parts)


def table_items(rows: list, only_changed: bool = False) -> list:
    out = []
    for r in rows:
        lv = {r["level_2026_09_15"], r["level_2026_08_21"], r["draft_level"]}
        if only_changed and len(lv) == 1:
            continue
        out.append({"graph": "computed from ai-readiness-kg documents", "kind": "element table row",
                    "doc_id": FINAL, "locator": {"element": r["element"],
                                                 "lines": {d: s["line"] for d, s in r["sources"].items()
                                                           if d in ROW_TEXT_DOCS}},
                    "section": f"element {r['element']}", "text": row_text(r),
                    "pinned": True})
    return out


def language_items(cfg: dict, drv, docs_airkg: list, docs_fss: list, substrate_dir: Path) -> list:
    terms = ["639", "bcp 47", "bcp47", "5646", "language code", "language tag"]
    items = substrate_passages(docs_airkg, terms, substrate_dir)
    items += airkg_node_passages(drv, cfg["graphs"]["airkg_database"], cfg["graphs"]["airkg_labels"],
                                 docs_airkg, terms)
    items += fss_passages(drv, cfg["graphs"]["fss_database"], docs_fss, terms)
    for it in items:
        it["pinned"] = True
    return items


# ------------------------------------------------------------------------------- assembling

def cut_passage(text: str, limit: int) -> tuple[str, bool]:
    if len(text) <= limit:
        return text, False
    head = text[:limit]
    m = re.search(r"^(.*[.;:])\s", head, re.S)
    return (m.group(1) if m else head), True


def select(items: list, terms: list, caps: dict) -> tuple[list, int]:
    """Rank by distinct terms matched (pinned items first, in their own order), drop exact and
    contained duplicates, apply the per-document, item and character caps (`max_items` counts
    retrieved passages only). Returns the kept
    items and how many matched but were dropped by a cap."""
    for i, it in enumerate(items):
        it["terms_matched"] = matched_terms(it["text"], terms)
        it["_order"] = i
    pool = [it for it in items if len(norm(it["text"])) >= caps["min_passage_chars"] or it.get("pinned")]
    pool.sort(key=lambda it: (0 if it.get("pinned") else 1, -len(it["terms_matched"]), it["_order"]))
    kept, seen, per_doc, chars, dropped = [], [], {}, 0, 0
    for it in pool:
        n = norm(it["text"]).lower()
        if any(n == s or (len(n) > 40 and n in s) for s in seen):
            continue
        k = (it["graph"], it["doc_id"], it["kind"].split(" ")[0])
        text, cut = cut_passage(it["text"], caps["max_passage_chars"])
        # Pinned items (computed table rows, catalog records, gap statements) are the
        # question's spine and are not ranked against retrieved passages: they count toward
        # the character cap, not the item cap or the per-document cap.
        retrieved = sum(1 for x in kept if not x.get("pinned"))
        over = (chars + len(text) > caps["max_chars"]
                or (not it.get("pinned") and (retrieved >= caps["max_items"]
                                              or per_doc.get(k, 0) >= caps["max_per_document"])))
        if over:
            dropped += 1
            continue
        it["text"], it["cut"] = text, cut
        per_doc[k] = per_doc.get(k, 0) + 1
        chars += len(text)
        seen.append(n)
        kept.append(it)
    for i, it in enumerate(kept, 1):
        it["id"] = f"E{i}"
        it.pop("_order", None)
    return kept, dropped


def build_question(qcfg: dict, cfg: dict, drv, meta: dict, table: list, substrate_dir: Path) -> dict:
    groups, caps = cfg["groups"], cfg["caps"]
    terms = [str(t).lower() for t in qcfg.get("terms") or []]
    docs_a = expand(qcfg.get("airkg"), groups)
    docs_f = expand(qcfg.get("fss"), groups)
    items = []
    for comp in qcfg.get("computed") or []:
        if comp == "element_levels":
            items += table_items(table, only_changed=(qcfg["id"] == 7))
        elif comp == "level_changes":
            items += table_items(table, only_changed=True)
        elif comp == "language_statements":
            items += language_items(cfg, drv, docs_a, docs_f, substrate_dir)
        else:
            raise SystemExit(f"FATAL: unknown computed evidence {comp!r}")
    if qcfg.get("catalog_entries"):
        for it in catalog_entries(drv, cfg["graphs"]["fss_database"], meta):
            it["pinned"] = True
            items.append(it)
    if terms:
        items += substrate_passages(docs_a, terms, substrate_dir)
        items += airkg_node_passages(drv, cfg["graphs"]["airkg_database"],
                                     cfg["graphs"]["airkg_labels"], docs_a, terms)
        items += fss_passages(drv, cfg["graphs"]["fss_database"], docs_f, terms)
    if qcfg.get("framework_terms"):
        items += framework_passages([str(t).lower() for t in qcfg["framework_terms"]])
    kept, dropped = select(items, terms, caps)
    missing = sorted({d for d in docs_a + docs_f if d not in meta})
    if missing:
        raise SystemExit(f"FATAL: Q{qcfg['id']}: no document in either graph for {missing}")
    used = {it["doc_id"] for it in kept if it["doc_id"] in meta}
    if any(it["kind"] == "element table row" for it in kept):
        used |= {FINAL, EARLIER, DRAFT, V11}     # each row quotes all four versions
    used = sorted(used)
    return {"question_id": qcfg["id"], "question": qcfg["text"], "generated_by": GENERATOR,
            "generated_at": _now(), "terms": terms, "documents_searched": {"ai-readiness-kg": docs_a,
                                                                         "fss-policy-kg": docs_f},
            "matched": len(items), "dropped_by_cap": dropped, "caps": caps,
            "documents": {d: meta[d] for d in used}, "items": kept}


def build_gaps_question(qcfg: dict, cfg: dict, gaps: list, catalog: list) -> dict:
    """Q14: the "not known" statements the validator kept on the earlier questions, plus the
    catalog records of documents that were looked for and are not public or not admitted
    (`catalog_entries.json`, written by `main` from fss-policy-kg). No database is read here,
    so the runner can build it after the earlier questions are checked."""
    items = [{"graph": "this FAQ", "kind": "unanswered part of an earlier question",
              "doc_id": f"question {g['question_id']}", "locator": {"question": g["question_id"],
                                                                     "not_known": g["n"]},
              "section": f"question {g['question_id']}", "text": g["text"], "pinned": True}
             for g in gaps]
    items += [dict(it, pinned=True) for it in catalog]
    kept, dropped = select(items, [], cfg["caps"])
    return {"question_id": qcfg["id"], "question": qcfg["text"], "generated_by": GENERATOR,
            "generated_at": _now(), "terms": [], "documents_searched": {},
            "matched": len(items), "dropped_by_cap": dropped, "caps": cfg["caps"],
            "documents": {}, "items": kept}


def stem(t: str) -> str:
    """A crude suffix strip, so "requires" finds "requirements" and "elements" finds "element".
    Used by the absence search only; the questions' own evidence matches terms as written."""
    for suf in ("ments", "ment", "ing", "ies", "es", "ed", "s"):
        if len(t) - len(suf) >= 4 and t.endswith(suf):
            return t[: -len(suf)]
    return t


def content_terms(statement: str, stopwords: set) -> list:
    """The words of a "not known" statement that carry its content: lowercased tokens of four or
    more characters (hyphenated identifiers such as m-25-05 kept whole), minus the stop list,
    stemmed (`stem`)."""
    toks = re.findall(r"[a-z0-9][a-z0-9.\-]*[a-z0-9]", statement.lower())
    return list(dict.fromkeys(stem(t) for t in toks if len(t) >= 4 and t not in stopwords))


def absence_evidence(qcfg: dict, cfg: dict, drv, meta: dict, statements: list, substrate_dir: Path) -> dict:
    """Passages for checking "not known" statements against the collection rather than against
    one question's capped passages. For each statement, every passage in the question's
    documents (all groups, for a question with no scope of its own) is ranked by how many of the
    statement's content terms it contains, and the top `absence.per_document` of each document
    are kept. The
    union is one evidence file, so the check reads every statement against all of it."""
    groups, ab = cfg["groups"], cfg["absence"]
    if qcfg.get("airkg") or qcfg.get("fss"):
        docs_a, docs_f = expand(qcfg.get("airkg"), groups), expand(qcfg.get("fss"), groups)
    else:
        docs_a = list(dict.fromkeys(d for k, v in groups.items() if not k.endswith("_fss") for d in v))
        docs_f = list(dict.fromkeys(d for k, v in groups.items() if k.endswith("_fss") for d in v))
    stop = set(ab["stopwords"])
    pool, per_statement = [], []
    for st in statements:
        terms = content_terms(st, stop)
        cands = substrate_passages(docs_a, terms, substrate_dir)
        cands += airkg_node_passages(drv, cfg["graphs"]["airkg_database"], cfg["graphs"]["airkg_labels"],
                                     docs_a, terms)
        cands += fss_passages(drv, cfg["graphs"]["fss_database"], docs_f, terms)
        for c in cands:
            c["terms_matched"] = matched_terms(c["text"], terms)
        cands = [c for c in cands if len(c["terms_matched"]) >= ab["min_terms"]]
        cands.sort(key=lambda c: -len(c["terms_matched"]))
        # Top passages PER DOCUMENT, so the document that answers a statement is heard even when
        # another document matches more of its words (M-25-05's own element list matches three
        # of five terms; glossaries and crosswalks match four).
        top, per = [], {}
        for c in cands:
            if per.get(c["doc_id"], 0) < ab["per_document"]:
                per[c["doc_id"]] = per.get(c["doc_id"], 0) + 1
                top.append(c)
        per_statement.append({"statement": st, "terms": terms, "candidates": len(cands)})
        for c in top:
            c["pinned"] = True
            pool.append(c)
    caps = dict(cfg["caps"], max_chars=ab["max_chars"])
    union = list(dict.fromkeys(t for x in per_statement for t in x["terms"]))
    kept, dropped = select(pool, union, caps)
    return {"question_id": qcfg["id"], "question": qcfg["text"], "generated_by": GENERATOR,
            "generated_at": _now(), "purpose": "absence check", "statements": per_statement,
            "documents_searched": {"ai-readiness-kg": docs_a, "fss-policy-kg": docs_f},
            "matched": len(pool), "dropped_by_cap": dropped, "caps": caps,
            "documents": {it["doc_id"]: meta[it["doc_id"]] for it in kept if it["doc_id"] in meta},
            "items": kept}


def evidence_sha(ev: dict) -> str:
    """Content hash of what a model call is shown: the question and the items. Generation time
    is excluded, so a rebuild that finds the same evidence is the same unit."""
    body = {"question": ev["question"], "items": [{k: it[k] for k in ("id", "doc_id", "locator", "text")}
                                                  for it in ev["items"]]}
    return hashlib.sha256(json.dumps(body, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def write(ev: dict) -> Path:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    ev["evidence_sha256"] = evidence_sha(ev)
    p = EVIDENCE_DIR / f"Q{ev['question_id']}.json"
    p.write_text(json.dumps(ev, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return p


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", type=int, default=None)
    a = ap.parse_args(argv)
    cfg = load_config()
    substrate_dir = REPO / cfg["graphs"]["substrate_dir"]
    drv = driver()
    try:
        meta = doc_meta(drv, cfg)
        table = element_table(substrate_dir)
        TABLE_JSON.parent.mkdir(parents=True, exist_ok=True)
        TABLE_JSON.write_text(json.dumps({"generated_by": GENERATOR, "sources": [FINAL, EARLIER, DRAFT, V11],
                                          "rows": table}, indent=1, ensure_ascii=False) + "\n",
                              encoding="utf-8")
        catalog = catalog_entries(drv, cfg["graphs"]["fss_database"], meta)
        CATALOG_JSON.write_text(json.dumps({"generated_by": GENERATOR, "items": catalog}, indent=1,
                                           ensure_ascii=False) + "\n", encoding="utf-8")
        summary = {}
        for qcfg in cfg["questions"]:
            if qcfg.get("gaps_from_questions") or (a.only and qcfg["id"] != a.only):
                continue
            ev = build_question(qcfg, cfg, drv, meta, table, substrate_dir)
            p = write(ev)
            summary[qcfg["id"]] = {"items": len(ev["items"]), "matched": ev["matched"],
                                   "dropped_by_cap": ev["dropped_by_cap"],
                                   "chars": sum(len(i["text"]) for i in ev["items"]),
                                   "documents": len(ev["documents"]), "file": p.relative_to(REPO).as_posix()}
    finally:
        drv.close()
    print(json.dumps({"element_rows": len(table), "questions": summary}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
