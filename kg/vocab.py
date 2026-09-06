"""The controlled vocabulary: preferred terms, aliases, and alias-first resolution.

Task `cc_tasks/2026-09-05_vocabulary_and_entity_linking.md` §1.1–§1.3. **Zero model spend** —
this module is a log, a normaliser and a dictionary lookup.

**Prior art, because none of this is new.** A controlled vocabulary is a curated list of
preferred terms with aliases, broader/narrower links and scope notes, against which every
incoming mention is indexed: Cutter (1876) *Rules for a Dictionary Catalog*; Library of
Congress Subject Headings; ISO 25964-1:2011; W3C SKOS Reference (2009). The export in
`scripts/export_vocabulary_skos.py` is SKOS for that reason — the data model is a thesaurus's
and pretending otherwise would only cost interoperability. What the old versions could not
afford was the *cataloguer*; that bottleneck is what §2 spends money on.

**Where it lives, and why here rather than in Seldon's ontology module (§1.1).** Two blockers,
both read out of `seldon/commands/ontology.py` rather than assumed:

1. `ONTOLOGY_MASTER_DB = "seldon-ontology"` is a module-level constant in `seldon/config.py`
   with no override. Every write path (`_ensure_master_db`, `_increment_epoch`,
   `_read_master_state`) names it directly, so a second master database — the task's
   `ai-readiness-vocabulary` option — cannot exist without editing Seldon.
2. `_do_sync` pulls `MATCH (a:Artifact:OntologyTerm) RETURN a` with **no namespace filter**.
   Every term in master lands in every project's replica. Putting a domain thesaurus of this
   size into the shared master would push it into every other project — precisely what §1.1
   forbids ("without adding terms to Seldon's own master").

So the vocabulary is project-owned `:Term` nodes carrying the same event shapes AD-017 uses,
and `af389420` is the seldon ResearchTask registered to fold it into the ontology module once
that module can host a second, namespaced vocabulary. Nothing here writes to `seldon-ontology`.

**Events** (append-only, shard `batch-026`, untagged — the vocabulary is part of the graph's
history, not an experiment arm):

    term_added         term_id, pref_label, scope_note, source, broader, alt_labels
    term_alias_added   term_id, alias, source
    term_deprecated    term_id, reason, replaced_by
    vocabulary_epoch   epoch, note

A term is never edited and never deleted. A `RESOLVES_TO` edge written under epoch 1 still
resolves after epoch 2 changes something, which is the whole reason AD-017 works this way.
"""
from __future__ import annotations

import datetime
import re
import unicodedata

from . import eventlog

#: The graph shard these events live on. Untagged: `eventlog.replay()` skips tagged shards,
#: so a tagged vocabulary would never reach the projection.
VOCAB_BATCH = 26

TERM_ADDED = "term_added"
TERM_ALIAS_ADDED = "term_alias_added"
TERM_DEPRECATED = "term_deprecated"
VOCABULARY_EPOCH = "vocabulary_epoch"

#: Namespace prefix for this project's term ids, so a term id never collides with a Seldon
#: OntologyTerm id if the two vocabularies are ever merged (the §1.1 follow-up task).
NS = "air"


class VocabRefusal(RuntimeError):
    """A vocabulary write that must not become an event."""


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


# ---------------------------------------------------------------- normalisation
_PUNCT = re.compile(r"[^\w\s]", re.UNICODE)
_WS = re.compile(r"\s+")

#: Singular nouns of this domain that end in `s`. A closed, stated list beats a suffix
#: heuristic here: `alias` and `bias` are live vocabulary terms, and folding either to `alia`
#: / `bia` would make the alias table unable to name itself. Add to this list, do not widen
#: the rule below — a wider rule silently merges terms nobody inspected.
_SINGULAR_IN_S = frozenset({
    "alias", "bias", "analysis", "basis", "hypothesis", "thesis", "axis", "status",
    "census", "corpus", "consensus", "focus", "apparatus", "atlas", "canvas", "gas",
    "lens", "series", "species", "means", "news", "process", "access", "address",
    "class", "mass", "pass", "loss", "cross", "business", "readiness", "completeness",
    "usefulness", "openness", "fitness", "richness", "awareness", "robustness",
    "timeliness", "trustworthiness", "https", "dns", "cms", "gis", "os",
})

#: Suffixes that are never a plural `-s` inflection.
_NOT_PLURAL_SUFFIX = ("ss", "us", "is")


def _fold_plural(word: str) -> str:
    """Conservative inflectional fold — deliberately NOT a stemmer.

    A Porter stemmer (1980) would take `readiness` to `readi` and `provenance` to `proven`,
    collapsing terms this vocabulary must keep apart: `AI readiness` and `AI ready` name
    different things, and §3a of the previous task established that the phrase is a homonym
    carrying at least three senses. ISO 25964 puts the burden on the *indexing* side rather
    than on a stemmer for exactly this reason. So: an explicit exception list, then `-ies` →
    `-y`, `-es` after a sibilant, plain `-s`, and nothing else.

    The asymmetry is deliberate. An over-fold is a silently wrong merge that nothing
    downstream can detect, because the merged node stops being counted as unresolved. An
    under-fold is a candidate pair that §1.3's embedding band still catches and §2's judge
    still sees. When in doubt, under-fold.
    """
    if len(word) <= 3 or word in _SINGULAR_IN_S:
        return word
    if word.endswith("ies") and len(word) > 4:
        return word[:-3] + "y"
    if word.endswith(_NOT_PLURAL_SUFFIX):
        return word
    if word.endswith("es") and len(word) > 4 and (
            word[-3] in "sxz" or word.endswith(("ches", "shes"))):
        return word[:-2]
    if word.endswith("s"):
        return word[:-1]
    return word


def normalize(name) -> str | None:
    """NFKC → casefold → punctuation-to-space → whitespace collapse → per-word plural fold.

    Stronger than `assessment/cq/collapse.canonical_key`, on purpose and in one direction
    only. `canonical_key` is the *measurement instrument* bound to the CQ before/after series
    — it merges only what nobody could dispute is the same string, so the collapsed view is a
    floor on redundancy. This is the *indexing* key for a curated vocabulary, where a
    cataloguer has already decided the term and its aliases, so folding case, punctuation and
    number is recording their decision rather than guessing at identity. The two must not be
    unified: changing `canonical_key` would silently move a registered `flip`.

    Punctuation becomes a SPACE rather than being deleted, so `AI-readiness` and `AI
    readiness` meet while `dcatus` and `DCAT-US` do not.
    """
    if name is None:
        return None
    s = unicodedata.normalize("NFKC", str(name))
    s = _PUNCT.sub(" ", s).casefold()
    s = _WS.sub(" ", s).strip()
    if not s:
        return None
    return " ".join(_fold_plural(w) for w in s.split())


# ---------------------------------------------------------------- writes
def add_term(term_id: str, pref_label: str, scope_note: str, source: str,
             broader: str | None = None, alt_labels=(), node_labels=()) -> str:
    """Emit one `term_added`. Every term carries a `dcterms:source` (§1.2) — a term whose
    provenance is 'someone typed it' is the drift vector the whole vocabulary exists against."""
    if not term_id or not pref_label:
        raise VocabRefusal("a term needs an id and a preferred label")
    if not source:
        raise VocabRefusal(f"{term_id!r} carries no source; §1.2 requires a dcterms:source")
    return eventlog.append({
        "event_type": TERM_ADDED, "term_id": term_id, "pref_label": pref_label,
        "scope_note": scope_note or "", "source": source, "broader": broader,
        "alt_labels": list(alt_labels),
        # Which KG node label(s) this term's members carried. §1.3 blocks on it: an
        # `Instrument` named "Coverage" and a `Concept` named "Coverage" are two terms, and a
        # vocabulary that cannot tell them apart is a worse answer than no vocabulary.
        "node_labels": sorted(node_labels), "ts": _now()}, batch=VOCAB_BATCH)


def add_alias(term_id: str, alias: str, source: str,
              derivation: str | None = None, evidence: str | None = None) -> str:
    """Emit one `term_alias_added`.

    `derivation` names the GENERATOR that produced the alias and `evidence` the node it was
    read off (task 2026-09-06_aliases_homograph_judge_epoch2 §1.1). Both are optional so the
    epoch-1 events replay unchanged; both are required by the generators, because an alias
    nobody can trace back to a surface form in the corpus is a guess, and the whole point of
    the label-theft guard is that guesses are refused rather than absorbed."""
    if not normalize(alias):
        raise VocabRefusal(f"alias {alias!r} normalises to nothing")
    ev = {"event_type": TERM_ALIAS_ADDED, "term_id": term_id, "alias": alias,
          "source": source, "ts": _now()}
    if derivation:
        ev["derivation"] = derivation
    if evidence:
        ev["evidence"] = evidence
    return eventlog.append(ev, batch=VOCAB_BATCH)


def deprecate(term_id: str, reason: str, replaced_by: str | None = None) -> str:
    if not reason:
        raise VocabRefusal("a deprecation without a reason is an unexplained gap")
    return eventlog.append({
        "event_type": TERM_DEPRECATED, "term_id": term_id, "reason": reason,
        "replaced_by": replaced_by, "ts": _now()}, batch=VOCAB_BATCH)


def declare_epoch(epoch: int, note: str) -> str:
    return eventlog.append({"event_type": VOCABULARY_EPOCH, "epoch": int(epoch),
                            "note": note, "ts": _now()}, batch=VOCAB_BATCH)


# ---------------------------------------------------------------- reads
def project() -> dict:
    """{term_id: term} by ordinary replay. Deprecated terms stay in the projection with
    `state: deprecated` — they are history, and an edge that cited one must still explain
    itself."""
    terms: dict = {}
    for ev in eventlog.replay():
        t = ev.get("event_type")
        tid = ev.get("term_id")
        if not tid:
            continue
        if t == TERM_ADDED:
            terms[tid] = {
                "term_id": tid, "pref_label": ev.get("pref_label"),
                "scope_note": ev.get("scope_note") or "",
                "broader": ev.get("broader"),
                "alt_labels": list(ev.get("alt_labels") or []),
                "node_labels": list(ev.get("node_labels") or []),
                "sources": [ev.get("source")] if ev.get("source") else [],
                "state": "active", "replaced_by": None,
            }
        elif t == TERM_ALIAS_ADDED and tid in terms:
            a = ev.get("alias")
            if a and a not in terms[tid]["alt_labels"]:
                terms[tid]["alt_labels"].append(a)
            src = ev.get("source")
            if src and src not in terms[tid]["sources"]:
                terms[tid]["sources"].append(src)
        elif t == TERM_DEPRECATED and tid in terms:
            terms[tid]["state"] = "deprecated"
            terms[tid]["replaced_by"] = ev.get("replaced_by")
            terms[tid]["deprecation_reason"] = ev.get("reason")
    return terms


def epoch() -> int:
    """Highest declared vocabulary epoch, 0 if none."""
    n = 0
    for ev in eventlog.replay():
        if ev.get("event_type") == VOCABULARY_EPOCH:
            n = max(n, int(ev.get("epoch") or 0))
    return n


def alias_index(terms: dict | None = None, node_label: str | None = None) -> dict:
    """{normalized label: [term_id, …]} over ACTIVE terms only, preferred labels and aliases
    alike. A list rather than a single id because ambiguity has to survive to `resolve`,
    which is where it is refused.

    `node_label` applies §1.3's BLOCKING rule: only terms whose members carried that KG label
    are indexed. A term seeded from curated sources (the framework, the discovery stack, the
    search-optimisation lineage) carries no node label and is visible to every block, because
    it was authored to name a thing rather than derived from nodes of one type.
    """
    terms = project() if terms is None else terms
    idx: dict = {}
    for tid, t in terms.items():
        if t["state"] != "active":
            continue
        labels = t.get("node_labels") or []
        if node_label is not None and labels and node_label not in labels:
            continue
        for label in [t["pref_label"], *t["alt_labels"]]:
            k = normalize(label)
            if not k:
                continue
            if tid not in idx.setdefault(k, []):
                idx[k].append(tid)
    return {k: sorted(v) for k, v in idx.items()}


def resolve(name, index: dict | None = None, node_label: str | None = None) -> str | None:
    """The term this name denotes, or None.

    §1.3's upper threshold: a name resolves when it is identical (after `normalize`) to the
    preferred label or an alias of **exactly one** term. Two claimants resolve to NEITHER —
    a table that picks one is silently wrong, and the node it mislabels stops being counted as
    unresolved, so nothing ever finds the error. `index` is an argument because the loader
    resolves thousands of nodes and rebuilding it per node would replay the log per node.
    """
    k = normalize(name)
    if not k:
        return None
    hits = (alias_index(node_label=node_label) if index is None else index).get(k) or []
    return hits[0] if len(hits) == 1 else None
