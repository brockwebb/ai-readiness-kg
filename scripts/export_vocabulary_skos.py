#!/usr/bin/env python3
"""Export the controlled vocabulary as SKOS Turtle. **Zero model spend.**

Task `cc_tasks/2026-09-05_vocabulary_and_entity_linking.md` §1.1: "the vocabulary exports as
SKOS Turtle … so it is a standard artifact and not a private one."

SKOS (W3C Recommendation, 2009) is the right target because the data model here IS a
thesaurus's — preferred label, alternative labels, broader/narrower, scope note, source — and
it is the model ISO 25964-1:2011 standardises. Exporting to it costs one script and buys the
property that anyone with a thesaurus tool can read this file. Inventing a private JSON shape
would have cost the same and bought nothing.

`skos:prefLabel` <- pref_label, `skos:altLabel` <- every alias, `skos:scopeNote` <- scope_note,
`skos:broader`/`skos:narrower` <- broader (both directions written, since a consumer may
traverse either), `dcterms:source` <- the seed source. A deprecated term is exported with
`owl:deprecated true` and, where one exists, `dcterms:isReplacedBy` — it is history and a
`RESOLVES_TO` edge that cited it must still explain itself.

    /opt/anaconda3/bin/python3 scripts/export_vocabulary_skos.py [--out ontology/ai_readiness_vocabulary.ttl]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from kg import vocab  # noqa: E402

TASK = "cc_tasks/2026-09-05_vocabulary_and_entity_linking.md"
OUT = REPO / "ontology" / "ai_readiness_vocabulary.ttl"
BASE = "https://brockwebb.github.io/ai-readiness-kg/vocabulary/"


def graph(terms: dict, epoch: int):
    from rdflib import Graph, Literal, Namespace, URIRef
    from rdflib.namespace import DCTERMS, OWL, RDF, SKOS, XSD

    g = Graph()
    AIR = Namespace(BASE)
    g.bind("skos", SKOS)
    g.bind("dcterms", DCTERMS)
    g.bind("owl", OWL)
    g.bind("air", AIR)

    scheme = URIRef(BASE)
    g.add((scheme, RDF.type, SKOS.ConceptScheme))
    g.add((scheme, SKOS.prefLabel, Literal("AI-readiness controlled vocabulary", lang="en")))
    g.add((scheme, DCTERMS.source, Literal(TASK)))
    g.add((scheme, OWL.versionInfo, Literal(f"vocabulary_epoch {epoch}")))

    def uri(term_id: str) -> "URIRef":
        return URIRef(BASE + term_id.split(":", 1)[-1])

    for tid, t in sorted(terms.items()):
        u = uri(tid)
        g.add((u, RDF.type, SKOS.Concept))
        g.add((u, SKOS.inScheme, scheme))
        g.add((u, SKOS.notation, Literal(tid)))
        g.add((u, SKOS.prefLabel, Literal(t["pref_label"], lang="en")))
        for a in t["alt_labels"]:
            g.add((u, SKOS.altLabel, Literal(a, lang="en")))
        if t.get("scope_note"):
            g.add((u, SKOS.scopeNote, Literal(t["scope_note"], lang="en")))
        for src in t.get("sources") or ():
            g.add((u, DCTERMS.source, Literal(src)))
        if t.get("broader") and t["broader"] in terms:
            g.add((u, SKOS.broader, uri(t["broader"])))
            g.add((uri(t["broader"]), SKOS.narrower, u))
        if t["state"] == "deprecated":
            g.add((u, OWL.deprecated, Literal(True, datatype=XSD.boolean)))
            if t.get("replaced_by"):
                g.add((u, DCTERMS.isReplacedBy, uri(t["replaced_by"])))
    return g


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=str(OUT))
    a = ap.parse_args(argv)
    terms, epoch = vocab.project(), vocab.epoch()
    if not terms:
        raise SystemExit("FATAL: no terms; run scripts/seed_vocabulary.py --emit first")
    g = graph(terms, epoch)
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    g.serialize(destination=str(out), format="turtle")
    print(f"{len(terms)} terms, {len(g)} triples, epoch {epoch} -> {out.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
