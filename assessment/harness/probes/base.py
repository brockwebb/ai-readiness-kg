"""Probe base classes.

Three families, each with a pure `evaluate` so scoring is testable from fixtures
without the network:

- SiteProbe          fetches a well-known path off the agency base_url
                     (robots.txt, sitemap.xml, data.json, llms.txt, mcp) and scores
                     the response. Run once per agency.
- MetadataProbe      pure: scores a single dataset record. On the catalog side that
                     record comes from data.json / DCAT; on a web surface it comes
                     from in-page JSON-LD, normalized to the same field names by
                     `harness/jsonld.py` and read via `evaluate_page`. No network.
- DistributionProbe  fetches one endpoint and scores the live response. Run per
                     distribution and, where the probe declares it, per web page.

Every probe declares `probe_id`, `dimension` (None for frontier), and `track`
(the core-vs-frontier firewall). `as_of_date` is derived from the track, so a
frontier probe's record always carries its dating.

`evaluate` returns `(score, evidence)`. A probe that emits structured
observations returns `(score, evidence, observations)` instead; the runner's
`unpack_verdict` accepts both, so adding observations to a probe never changes
its neighbours. Observations are facts kept apart from the score and from any
warning (skeleton §6b.5) and travel on `ProbeResult.observations`.

Every probe also declares `sources`: which enumeration sources it applies to. The
runner asks each probe rather than assuming, so a distribution-only probe is never
forced onto an HTML page. "Bulk availability" and "programmatic access" are
questions about a catalog distribution; asking them of a product page would
manufacture a score out of a category error. Widening a probe to a new surface is
a deliberate edit to its `sources`, visible in the diff.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from ..fetch import Fetched
from ..jsonld import dataset_nodes, dcat_record_from_nodes
from ..records import (
    SOURCE_CATALOG,
    SOURCE_EVAL,
    SOURCE_SITE,
    SOURCE_SITEMAP,
    Score,
    Track,
)


class _Probe:
    """Shared declaration surface: identity, dimension, track, and applicability."""

    probe_id: str = ""
    dimension: Optional[str] = None
    track: Track = Track.CORE
    # Enumeration sources this probe is meaningful for. Narrow by default.
    sources: Tuple[str, ...] = (SOURCE_CATALOG,)

    def applies_to(self, source: str) -> bool:
        return source in self.sources


class SiteProbe(_Probe):
    path: str = "/"
    sources: Tuple[str, ...] = (SOURCE_SITE,)

    def url_for(self, base_url: str) -> str:
        return base_url.rstrip("/") + self.path

    def evaluate(self, fetched: Fetched) -> Tuple[Score, str]:  # pragma: no cover
        raise NotImplementedError


class MetadataProbe(_Probe):
    def evaluate(self, dataset: dict) -> Tuple[Score, str]:  # pragma: no cover
        raise NotImplementedError

    def evaluate_page(self, fetched: Fetched, nodes: Optional[List[dict]] = None):
        """Score an HTML page by reading its in-page schema.org JSON-LD.

        The page's Dataset / DataCatalog markup is normalized to the DCAT field
        names the catalog side uses, then handed to the same `evaluate`, so one
        scoring rule covers both surfaces. `nodes` may be passed in when the
        caller has already extracted them, to avoid parsing the page twice.

        The evidence string names what the score was read from, so "FAIL" on a
        page with no markup is never mistaken for "FAIL" on a page whose markup
        was thin.
        """
        if nodes is None:
            nodes = dataset_nodes(fetched.body)
        record = dcat_record_from_nodes(nodes)
        score, evidence = self.evaluate(record)
        if nodes:
            types = record.get("_jsonld_types") or []
            read_from = (
                f"read from {len(nodes)} in-page JSON-LD schema.org node(s)"
                f"{', scored the node typed ' + ', '.join(types) if types else ''}"
            )
        else:
            read_from = (
                "no in-page JSON-LD schema.org Dataset/DataCatalog markup on the page"
            )
        return score, f"{evidence} [{read_from}]"


class DistributionProbe(_Probe):
    # True when the probe scores several fetches of the same target rather than
    # one. The runner fetches n times and calls `evaluate_attempts`.
    multi_attempt: bool = False

    def evaluate(self, fetched: Fetched, distribution: dict) -> Tuple[Score, str]:  # pragma: no cover
        raise NotImplementedError

    def evaluate_attempts(self, attempts: List[Fetched], distribution: dict):
        """Score a sequence of fetches of one target. Single-fetch by default."""
        return self.evaluate(attempts[0], distribution)


@dataclass(frozen=True)
class Elicited:
    """What a consumer returned for one proposition under one elicitation mode —
    the eval analogue of `Fetched`. Persisted to disk BEFORE scoring (the raw
    request and response are the evidence; a score is read from them, never
    asserted). `model_id` is the model the envelope REPORTED, checked against the
    pinned model at the choke point (invariant 5)."""

    proposition_id: str
    mode: str
    prompt: str
    response_text: str
    model_id: str
    prompt_epoch: str
    timestamp: str
    evidence_path: str
    usage: dict = field(default_factory=dict)
    duration_ms: Optional[int] = None
    cost_usd: Optional[float] = None
    spend_run_id: Optional[str] = None
    spend_reservation_id: Optional[str] = None


class EvalProbe(_Probe):
    """Fourth family: elicit a restatement from a model consumer, then score it
    with a pure `evaluate` (task 2026-09-02_g1_eval_probe_family_v0 step 1).

    Contract, mirroring the fetch/evaluate split of the other families:

    - `elicit(consumer, proposition, mode) -> Elicited` is the network/model half
      (the analogue of fetch). It renders the mode's prompt template with the
      proposition's source passage IN CONTEXT — retrieval is removed by
      construction (memo §4.8: separate "found the wrong table/vintage" from
      "found the right estimate and dropped its MOE"; a consumer that cannot see
      the source is the surfaced leg's problem, not this probe's). It persists the
      raw request and response before returning.
    - `evaluate(elicited, proposition) -> (Score | UNPARSEABLE, evidence,
      observations)` is pure and fixture-testable. Its unit is the proposition
      (memo §4.1: one estimate plus its qualifier set — FActScore's atomic fact,
      Du 2026's annotated proposition). Preservation is ordinal (memo §4.2: Du
      2026's level structure; van der Bles 2019's form-of-expression axis) and
      failures are named with the memo's vocabulary first (memo §4.3). Both modes
      (memo §4.4: indirect restatement and direct question) are scored by the
      same `evaluate`. The producer's published rule is the ground truth (memo
      §4.5), and no NLI/QA faithfulness score stands in for the metric (memo
      §4.6: those are number- and qualifier-blind).

    Records are `EvalResult`s with `source = SOURCE_EVAL`, which the rollup
    partitions out of every composite before summing.
    """

    sources: Tuple[str, ...] = (SOURCE_EVAL,)
    modes: Tuple[str, ...] = ("indirect", "direct")

    def elicit(self, consumer, proposition, mode: str) -> Elicited:  # pragma: no cover
        raise NotImplementedError

    def evaluate(self, elicited: Elicited, proposition):  # pragma: no cover
        raise NotImplementedError


def unpack_verdict(verdict):
    """`(score, evidence)` or `(score, evidence, observations)` -> three values."""
    if len(verdict) == 3:
        score, evidence, observations = verdict
        return score, evidence, dict(observations or {})
    score, evidence = verdict
    return score, evidence, {}


__all__ = [
    "unpack_verdict",
    "SiteProbe",
    "MetadataProbe",
    "DistributionProbe",
    "EvalProbe",
    "Elicited",
    "SOURCE_SITE",
    "SOURCE_CATALOG",
    "SOURCE_SITEMAP",
    "SOURCE_EVAL",
]
