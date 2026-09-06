"""LINT: no Cypher write may bind a node by property alone (task §1.2).

This repo has now shipped the same defect twice, and both times it cost a rebuild:

* 2026-09-04, the g1eval extraction — `MERGE (a {key: ...})` created an unlabelled twin of a
  Document, so 17 documents read `run_ok_no_edges` after a clean extraction;
* 2026-09-05, the vocabulary loader — `MATCH (n {key: $key})` bound BOTH nodes of the 82 keys
  that DD-020's `<doc_id>::<item_id>` does not make unique across types, writing 32 spurious
  `RESOLVES_TO` edges and 50 spurious `unresolved` flags.

A comment is not a guard. This test reads every Cypher string in the write paths and fails on
any node pattern that binds on properties with no label and no `labels(...)` predicate in the
same query. It is a grep, deliberately: a lint that understood Cypher would be a dependency
and a second thing to be wrong.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

#: Every file that runs Cypher writes against the KG.
WRITE_PATHS = sorted(list((REPO / "kg").rglob("*.py")) + [REPO / "scripts" / "build_projection.py"])

#: A node pattern binding on a property map with no label: `(n {`, `(a {`, `(n{`.
_UNLABELLED = re.compile(r"\(\s*([a-z][a-z0-9_]*)\s*\{")

#: Allowed, each with the reason it cannot carry a label. Keep this list SHORT and specific;
#: an entry here is a standing risk, not a dismissal.
ALLOW = {
    # An edge endpoint may be a Document, any KG node, or a cited document never manifested.
    # Its type is not knowable at write time — that is why `build()` deletes unlabelled nodes
    # at reset rather than trying to type them.
    "MERGE (a {key: $from_id}) MERGE (b {key: $to_id})",
}


def _cypher_strings(text: str) -> list:
    """Every string literal that looks like Cypher, joined per `session.run(...)` call so an
    f-string split across lines is checked as one query."""
    out = []
    for call in re.split(r"session\.run\(", text)[1:]:
        depth, buf = 1, []
        for ch in call:
            depth += (ch == "(") - (ch == ")")
            if depth <= 0:
                break
            buf.append(ch)
        chunk = "".join(buf)
        parts = re.findall(r'f?"((?:[^"\\]|\\.)*)"|f?\'((?:[^\'\\]|\\.)*)\'', chunk)
        joined = " ".join(a or b for a, b in parts)
        # An f-string doubles its literal braces in the source; normalise so a pattern reads
        # the same whether or not the query happened to need interpolation.
        joined = joined.replace("{{", "{").replace("}}", "}")
        if joined.strip():
            out.append(" ".join(joined.split()))
    return out


def test_no_write_path_binds_a_node_by_property_without_a_label():
    offenders = []
    for path in WRITE_PATHS:
        text = path.read_text(encoding="utf-8")
        for query in _cypher_strings(text):
            if not _UNLABELLED.search(query):
                continue
            # A `labels(...)` predicate in the same query is an explicit guard and passes.
            if "labels(" in query:
                continue
            if any(a in query for a in ALLOW):
                continue
            offenders.append(f"{path.relative_to(REPO)}: {query[:120]}")
    assert not offenders, (
        "unlabelled node pattern in a Cypher write — this is the defect that cost two "
        "rebuilds:\n  " + "\n  ".join(offenders))


def test_the_lint_would_catch_the_defect_it_was_written_for():
    """Mutation guard: the lint has to fail on the exact string that shipped twice, or it is
    decoration."""
    bad = 'MATCH (n {key: $key}) MERGE (t:Term {term_id: $term}) MERGE (n)-[:RESOLVES_TO]->(t)'
    assert _UNLABELLED.search(bad)
    assert "labels(" not in bad and not any(a in bad for a in ALLOW)


def test_the_lint_accepts_the_labelled_form_that_fixed_it():
    good = 'MATCH (n:Concept {key: $key}) MERGE (t:Term {term_id: $term})'
    assert not _UNLABELLED.search(good)
    guarded = 'MATCH (n {key: $key}) WHERE any(l IN labels(n) WHERE l IN $kg) SET n.x = 1'
    assert _UNLABELLED.search(guarded) and "labels(" in guarded
