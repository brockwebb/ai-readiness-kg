#!/usr/bin/env python3
"""Seed the controlled vocabulary — epoch 1. **Zero model spend.**

Task `cc_tasks/2026-09-05_vocabulary_and_entity_linking.md` §1.2. Five sources, in precedence
order; a term claimed by an earlier source keeps that source's preferred label and scope note,
and a later source contributes only aliases. Every term carries a `dcterms:source`, because a
term whose provenance is "someone typed it" is the drift vector the vocabulary exists against.

    S1  framework constructs and indicator groups (docs/crosswalk/*)
    S2  discovery-stack standards and frontier candidates, already in the graph
    S3  the search-optimisation lineage SEO -> AEO -> GEO -> AIO, dated, web-sourced
    S4  Concept name groups under kg.vocab.normalize (the duplicate groups themselves)
    S5  the model-asserted `aliases` property on Concept nodes

**S5 is admitted with a guard, and the guard is the interesting part.** The extractor's
`aliases` list is not always an alias list: `AI-ready data -> ['high-quality data']` is a
model-asserted equivalence between two things this corpus must keep apart, and §3a of the
previous task exists because that phrase is a homonym. So a model-asserted alias is refused
when its normalised form is already the PREFERRED LABEL of a different term — the term that
owns a name is not overridden by another term's guess about it. Where the alias survives and
is wrong, `vocab.resolve` still refuses it, because two claimants resolve to neither; the
guard only stops the case where a wrong alias would be the *sole* claimant and would therefore
link silently.

**Which node labels S4/S5 read, and why it is not only Concept.** §1.2.4 names "the 1,486
exact-name Concept groups", which is the figure the diagnostic reports; but §4's acceptance
requires every ENUMERATION-category CQ — `measure_lookup`, `instrument_coverage`,
`discovery_stack`, `frontier_candidate` — to answer `yes` in the canonical view, and those
questions enumerate `Instrument`, `Measure`, `Standard` and `Platform` nodes, not Concepts.
CQ-10 alone returns 502 raw Instrument rows collapsing to 377. A Concept-only vocabulary
cannot move any of them, so the task's own acceptance criterion requires the wider read. Every
term records the label(s) its members carried, and §1.3 blocks on that label — an `Instrument`
node is never linked to a term seeded from `Concept` nodes.

    /opt/anaconda3/bin/python3 scripts/seed_vocabulary.py --dry-run
    /opt/anaconda3/bin/python3 scripts/seed_vocabulary.py --emit      # first run, epoch 1
    /opt/anaconda3/bin/python3 scripts/seed_vocabulary.py --extend    # append terms not yet on the log
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, "/Users/brock/GitHub/seldon")

from kg import vocab  # noqa: E402

TASK = "cc_tasks/2026-09-05_vocabulary_and_entity_linking.md"
STATE = REPO / "state" / "vocabulary_seed_2026-09-05.json"

#: The entity labels S4/S5 group over: every KG label that (a) carries a `name` property and
#: (b) some CQ collapses on.
#:
#: `Definition` and `Claim` are deliberately absent — a definition or a claim is a SENTENCE,
#: not a named entity, so grouping them by name would build a vocabulary of prose.
#:
#: `Measure` and `Practice` are absent for a measured reason rather than a design one: **not
#: one of the 1,429 Measure nodes or the 1,347 Practice nodes carries a `name` property at
#: all.** They are keyed by `id` and carry only `grounding_span` and provenance, and the CQs
#: that touch them read `m.text` and collapse on the joined `Concept` instead (CQ-05, CQ-07).
#: Including them would have grouped 2,776 nodes on a property that does not exist and
#: reported a confident zero. That absence is itself a finding and the RESULT says so.
ENTITY_LABELS = ("Concept", "Instrument", "Standard", "Framework", "Platform", "Tool")

PROTOCOL = "docs/crosswalk/assessment_protocol.md"
SKELETON = "docs/crosswalk/usafacts_operationalization_skeleton.md"

#: §1.2.1 — the four dimensions, named in prose in the protocol §7 rather than in a table.
DIMENSIONS = [
    ("Discovery", "Whether a machine can find that a data product exists at all. Indicator "
                  "group A. Protocol §7 names the dimension spelled out and refuses `D1`-`D4` "
                  "because the letter D is already load-bearing twice."),
    ("Retrieval", "Whether a machine that knows a product exists can obtain it. Indicator "
                  "group A."),
    ("Interpretability", "Whether a machine that has the bytes can tell what they mean. "
                         "Indicator groups B and G."),
    ("Trust", "Whether a machine can tell where the product came from and under what terms it "
              "may be used. Indicator groups D and F."),
]

#: §1.2.2 — the established discovery stack and the dated frontier candidates. `source` is the
#: doc_id already admitted to the corpus, so the seed cites the corpus and not a memory.
STACK = [
    ("robots.txt", "The Robots Exclusion Protocol: a site-root file declaring which paths a "
     "named user-agent may fetch. Standardised as RFC 9309 (2022); the declared layer of "
     "indicator A4/A11.", "rfc-9309-robots-exclusion-protocol", ("Robots Exclusion Protocol", "RFC 9309")),
    ("Sitemaps", "An XML file enumerating a site's URLs for crawlers, with optional change "
     "frequency and last-modified hints. Indicator A5.", "sitemaps-protocol", ("XML Sitemaps", "sitemap.xml")),
    ("Well-known URIs", "RFC 8615: the `/.well-known/` path prefix reserving a site-root "
     "namespace for machine-discoverable metadata files.", "llmstxt-proposal", ("RFC 8615", "/.well-known/")),
    ("schema.org Dataset", "The schema.org vocabulary type for a dataset, embedded as JSON-LD "
     "or microdata on a product page so a crawler can parse it. Indicator A6.",
     "schema-org-dataset", ("schema.org/Dataset", "Dataset markup")),
    ("DCAT", "W3C Data Catalog Vocabulary: an RDF vocabulary for describing catalogs of "
     "datasets and their distributions. Indicator A6.", "w3c-dcat-3",
     ("Data Catalog Vocabulary", "DCAT-3", "DCAT-US")),
    ("data.json", "The Project Open Data catalog file a US federal agency publishes at "
     "`/data.json`, enumerating its public data assets. Indicator D4.", "dcat-us-1-1-schema",
     ("Project Open Data catalog", "public data inventory")),
    ("Content negotiation", "HTTP `Accept`-header negotiation, by which one URL serves a "
     "human page or a machine representation depending on what the client asks for.",
     "w3c-dwbp-2017", ("HTTP content negotiation",)),
    ("Persistent identifier", "A durable, resolvable identifier for a product or vintage (DOI, "
     "ARK, w3id) that survives site reorganisation. Indicator A7.",
     "wilkinson-2016-fair-guiding-principles", ("PID", "persistent URL", "DOI")),
    ("Croissant", "MLCommons' JSON-LD metadata format for machine-learning datasets, layered "
     "on schema.org. Indicator A6.", "mlcommons-croissant-spec", ("MLCommons Croissant",)),
    ("Model Context Protocol", "An open protocol by which a model client discovers and calls "
     "tools and data sources at inference time. FRONTIER CANDIDATE, as_of 2026-01: postdates "
     "the policy corpus, so protocol §4 reports it on the frontier track and never in the core "
     "score.", "fcsm-25-03", ("MCP", "Model Context Protocols")),
    ("llms.txt", "A proposed site-root markdown file offering an LLM-oriented map of a site's "
     "content. FRONTIER CANDIDATE, as_of 2026-01; the proposal is open for community input and "
     "is not an established practice.", "llmstxt-proposal", ("/llms.txt",)),
    ("SDMX", "Statistical Data and Metadata eXchange: the ISO 17369 standard for exchanging "
     "statistical data and its structural metadata, including break-in-series class metadata. "
     "Indicator G6.", "sdmx-3-0-section-1-framework", ("Statistical Data and Metadata eXchange", "ISO 17369")),
]

#: §1.2.3 — the search-optimisation lineage, with dated first use and canonical source. The
#: scope notes say what each term claims to optimise FOR, which is the only thing that
#: separates them; the trade press uses them interchangeably and the RESULT says so.
LINEAGE = [
    ("Search engine optimization",
     "Optimising a page to RANK in a search engine's list of links, where the user then clicks "
     "through. First documented use attributed to John Audette (Multimedia Marketing Group), "
     "1997; the attribution is contested — Bruce Clay, Bob Heyman and Leland Harden are all "
     "credited around the same date. Optimises for: position in a ranked list of destinations.",
     "https://searchengineland.com/seven-questions-for-seo-pioneer-john-audette-53978 (first use, 1997)",
     ("SEO",)),
    ("Answer engine optimization",
     "Optimising content to be the SOURCE a direct-answer engine cites when it returns one "
     "answer rather than a list. Industry origin, no academic paper; in circulation by "
     "2023-05. Optimises for: being the cited source of a single returned answer (Google AI "
     "Overviews, Perplexity).",
     "https://nogood.io/2023/05/26/future-of-search-aeo (dated first use, 2023-05-26)",
     ("AEO",)),
    ("Generative engine optimization",
     "Optimising content for visibility inside a response a generative engine COMPOSES from "
     "many sources. The only member of this lineage with an academic origin: Aggarwal, "
     "Murahari, Rajpurohit, Kalyan, Narasimhan and Deshpande, arXiv:2311.09735 (2023-11-16), "
     "published at KDD 2024. It models a generative engine as retrieval plus synthesis and "
     "proposes metrics for citations dispersed through a composed text. Optimises for: share "
     "of a synthesised answer, not position in a list.",
     "aggarwal-2024-geo-generative-engine-optimization (arXiv:2311.09735, KDD 2024)",
     ("GEO",)),
    ("AI optimization",
     "AMBIGUOUS BY CONSTRUCTION — recorded with its ambiguity rather than resolved. At least "
     "three live senses in trade use: (a) making a brand or content absorbable by an LLM; "
     "(b) optimising specifically for Google AI Overviews, launched 2024-05-14, sometimes "
     "written `AI Overview Optimization`; (c) using AI inside one's own SEO workflow. Industry "
     "origin, 2024-2025, no consensus definition in the literature as of 2026. Optimises for: "
     "whichever of the three the writer meant, which is why an assessment must say which.",
     "https://en.wikipedia.org/wiki/Artificial_intelligence_optimization (no consensus definition, 2026)",
     ("AIO", "AI Overview Optimization")),
]

_ROW = re.compile(r"^\|\s*([A-G]\d{1,2})\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|")


def framework_terms() -> list:
    """S1: the indicator rows of the operationalisation skeleton, parsed from the table the
    framework already maintains rather than retyped here — a retyped list drifts."""
    out = []
    text = (REPO / SKELETON).read_text(encoding="utf-8")
    for line in text.splitlines():
        m = _ROW.match(line)
        if not m:
            continue
        code, name, definition = m.group(1), m.group(2), m.group(3)
        name = re.sub(r"\s*\(.*?\)\s*$", "", name.strip())
        out.append((f"{name}", f"Indicator {code} of the AI-ready data framework. "
                               f"{definition.strip()[:400]}", f"{SKELETON} row {code}", (code,)))
    for name, note in DIMENSIONS:
        out.append((name, note, f"{PROTOCOL} §7", ()))
    return out


def graph_groups(session) -> tuple:
    """S4 + S5: name groups per LABEL, and the model-asserted alias lists.

    The group key is `(label, normalized name)`. Keying on the name alone would put an
    `Instrument` called "Coverage" in the same group as a `Concept` called "Coverage", which
    is the §1.3 blocking rule violated at seed time rather than at link time."""
    rows = []
    for label in ENTITY_LABELS:
        rows += [dict(r, label=label) for r in session.run(
            f"MATCH (n:{label}) RETURN n.name AS name, n.doc_id AS doc, n.aliases AS aliases, "
            f"n.grounding_span AS span").data()]
    groups = collections.defaultdict(list)
    for r in rows:
        k = vocab.normalize(r["name"])
        if k:
            groups[(r["label"], k)].append(r)
    return rows, groups


def slug(label: str) -> str:
    k = vocab.normalize(label) or "term"
    return f"{vocab.NS}:{re.sub(r'[^a-z0-9]+', '-', k).strip('-')[:80]}"


def build() -> dict:
    from seldon.config import get_neo4j_driver, load_project_config
    cfg = load_project_config(REPO)
    driver = get_neo4j_driver(cfg)
    try:
        with driver.session(database=cfg["neo4j"]["database"]) as s:
            rows, groups = graph_groups(s)
    finally:
        driver.close()

    terms: dict = {}            # term_id -> dict
    # Two indexes, because they answer two different questions.
    #  `by_key`       curated terms (S1-S3) by normalised label. A human authored these to
    #                 name a thing, so they are label-agnostic and a graph group of ANY label
    #                 that matches one folds into it — `DCAT` typed once as a Standard and
    #                 once as a Concept is one term because a person said so.
    #  `by_label_key` graph-derived terms (S4) by (node label, normalised label). Keying these
    #                 on the name alone would put an Instrument named "Coverage" and a Concept
    #                 named "Coverage" in ONE term, which is precisely the merge §1.3's
    #                 blocking rule exists to refuse — and worse, it would refuse it at seed
    #                 time where no reviewer ever sees it.
    by_key: dict = {}
    by_label_key: dict = {}
    counts = collections.Counter()

    def add(label, note, source, aliases=(), src_tag="", node_labels=(),
            key_override=None, index=None):
        k = vocab.normalize(label)
        if not k:
            return None
        index = by_key if index is None else index
        ikey = k if key_override is None else key_override
        tid = index.get(ikey)
        if tid is None:
            tid = slug(label)
            if key_override is not None:
                # A per-label term id has to be distinct from the Concept term of the same
                # name, and readable: `air:coverage` vs `air:instrument/coverage`.
                tid = f"{vocab.NS}:{key_override[0].lower()}/{tid.split(':', 1)[1]}"
            while tid in terms:
                tid += "-x"
            index[ikey] = tid
            terms[tid] = {"term_id": tid, "pref_label": label.strip(), "scope_note": note,
                          "source": source, "alt_labels": [], "alias_sources": [],
                          "seed_source": src_tag, "node_labels": sorted(node_labels)}
            counts[src_tag + "_terms"] += 1
        for a in aliases:
            if vocab.normalize(a) and a not in terms[tid]["alt_labels"]:
                terms[tid]["alt_labels"].append(a)
                terms[tid]["alias_sources"].append(source)
                counts[src_tag + "_aliases"] += 1
        return tid

    # ---- S1 framework
    for label, note, source, aliases in framework_terms():
        add(label, note, source, aliases, "s1_framework")
    # ---- S2 stack
    for label, note, source, aliases in STACK:
        add(label, note, f"corpus doc_id {source}", aliases, "s2_stack")
    # ---- S3 lineage
    for label, note, source, aliases in LINEAGE:
        add(label, note, source, aliases, "s3_lineage")

    # ---- S4 duplicate groups. Only groups of size > 1: a name asserted once is not evidence
    # of a shared term, and seeding 6,333 singletons would make the vocabulary a copy of the
    # graph rather than a curation of it.
    for (node_label, key), members in sorted(groups.items()):
        if len(members) < 2:
            counts["s4_singletons_skipped"] += 1
            continue
        spans = collections.Counter(m["span"] for m in members if m.get("span"))
        note = (spans.most_common(1)[0][0] if spans else "")[:600]
        label = collections.Counter(m["name"] for m in members).most_common(1)[0][0]
        docs = sorted({m["doc"] for m in members if m.get("doc")})
        tid = by_key.get(key) or by_label_key.get((node_label, key))
        if tid:
            counts["s4_folded_into_earlier_source"] += 1
            if node_label not in terms[tid]["node_labels"]:
                terms[tid]["node_labels"] = sorted(terms[tid]["node_labels"] + [node_label])
        else:
            tid = add(label, f"DRAFT scope note, the most-cited grounding span of the "
                             f"{len(members)} nodes named {label!r}: {note}",
                      f"graph: {len(members)} {node_label} nodes across {len(docs)} "
                      f"document(s), kg_snapshot_2026-09-05", (), "s4_groups", (node_label,),
                      key_override=(node_label, key), index=by_label_key)
            counts[f"s4_terms_{node_label}"] += 1
        # Every distinct SURFACE form in the group becomes an altLabel, compared as a raw
        # string rather than a normalised key. Comparing keys would record nothing at all —
        # the group is DEFINED by normalised equality — and the surface variants are exactly
        # what `skos:altLabel` is for: a reader of the Turtle needs to see that this term is
        # written `AI-readiness`, `AI readiness` and `AI Readiness` in the corpus.
        for name in sorted({m["name"] for m in members if m.get("name")}):
            if name != terms[tid]["pref_label"] and name not in terms[tid]["alt_labels"]:
                terms[tid]["alt_labels"].append(name)
                counts["s4_surface_variant_aliases"] += 1

    # ---- S5 model-asserted aliases, guarded.
    pref_keys = {vocab.normalize(t["pref_label"]) for t in terms.values()}
    for r in rows:
        k = vocab.normalize(r["name"]) or ""
        tid = by_key.get(k) or by_label_key.get((r["label"], k))
        if not tid:
            continue
        for a in (r.get("aliases") or []):
            ka = vocab.normalize(a)
            if not ka or ka == vocab.normalize(terms[tid]["pref_label"]):
                continue
            if ka in pref_keys:
                # The term that OWNS a name is not overridden by another term's guess about
                # it. `AI-ready data -> high-quality data` is the case this exists for.
                counts["s5_refused_would_steal_a_preferred_label"] += 1
                continue
            if a not in terms[tid]["alt_labels"]:
                terms[tid]["alt_labels"].append(a)
                counts["s5_aliases"] += 1

    counts["terms_total"] = len(terms)
    counts["aliases_total"] = sum(len(t["alt_labels"]) for t in terms.values())
    return {"terms": terms, "counts": dict(counts)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--emit", action="store_true")
    ap.add_argument("--extend", action="store_true",
                    help="append only what the log does not already carry, and re-declare the "
                         "epoch with a corrected note (append-only correction, never an edit)")
    a = ap.parse_args(argv)
    built = build()
    terms, counts = built["terms"], built["counts"]
    print(json.dumps(counts, indent=1, sort_keys=True))
    STATE.write_text(json.dumps({"task": TASK, "epoch": 1, "counts": counts,
                                 "terms": terms}, indent=1) + "\n", encoding="utf-8")
    print(f"-> {STATE.relative_to(REPO)}", file=sys.stderr)
    if not (a.emit or a.extend):
        return 0
    have = vocab.project()
    if have and a.emit:
        raise SystemExit("FATAL: terms already on the log; use --extend (the log is "
                         "append-only and the seed never re-runs over itself)")
    added_t = added_a = 0
    for t in terms.values():
        cur = have.get(t["term_id"])
        if cur is None:
            vocab.add_term(t["term_id"], t["pref_label"], t["scope_note"], t["source"],
                           node_labels=t.get("node_labels") or [])
            added_t += 1
            existing = set()
        else:
            existing = set(cur["alt_labels"])
        for i, alias in enumerate(t["alt_labels"]):
            if alias in existing:
                continue
            vocab.add_alias(t["term_id"], alias,
                            (t["alias_sources"][i] if i < len(t["alias_sources"]) else t["source"]))
            added_a += 1
    total = vocab.project()
    vocab.declare_epoch(1, f"seed from five sources ({TASK} §1.2): {len(total)} terms, "
                           f"{sum(len(x['alt_labels']) for x in total.values())} aliases "
                           f"(this run appended {added_t} terms and {added_a} aliases)")
    print(f"epoch {vocab.epoch()}: +{added_t} terms, +{added_a} aliases; "
          f"log now holds {len(total)} terms")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
