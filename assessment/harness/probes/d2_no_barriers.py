"""D2 Retrieval — no anti-machine barriers (no CAPTCHA / login wall / refusal).

Scored over n fetches of the same target, not one. An edge that refuses automated
clients intermittently is the case a single fetch cannot see: one fetch returns
either a refusal or a page, and cannot distinguish "always refuses" from
"refuses most of the time". Measured on census.gov/quickfacts on 2026-09-01,
2,874 of 4,374 Common Crawl index records for the sitemap URL form are HTTP 403,
and a home-machine probe of one QuickFacts page on 2026-09-02 was refused on 4 of
5 attempts. A single-fetch verdict on that surface is a coin flip.

An intermittent refusal is still a barrier to a machine: a consuming system that
must retry an unknown number of times to reach public data is being gated, and a
pipeline that fetches once gets nothing. So ANY refusal across the attempts fails
the probe, and the evidence carries the refusal fraction so a reviewer sees
whether it was one in five or five in five.

PASS    every attempt reachable (2xx) with no CAPTCHA / login / refusal markers.
FAIL    any attempt returns 401/403, carries barrier markers, or does not resolve.

There is no PARTIAL. A barrier that appears on some attempts is not half a
barrier; it is a barrier plus uncertainty about when. (A prior version of this
probe scored a JS-render dependency PARTIAL, but "enable javascript" is itself in
BARRIER_MARKERS, so that branch could never be reached. It was removed rather
than left as a score the probe cannot produce.)
"""
from __future__ import annotations

from typing import List

from ..fetch import Fetched
from ..records import SOURCE_CATALOG, SOURCE_SITEMAP, Score, Track
from .base import DistributionProbe
from ._formats import has_barrier_markers

# Statuses that are a refusal of the client rather than a missing resource.
REFUSAL_STATUSES = (401, 403)


class NoBarriersProbe(DistributionProbe):
    probe_id = "d2_no_barriers"
    dimension = "D2"
    track = Track.CORE
    # A barrier is a barrier on a catalog distribution and on a product page.
    sources = (SOURCE_CATALOG, SOURCE_SITEMAP)
    multi_attempt = True

    def evaluate(self, fetched: Fetched, distribution: dict):
        """Single-fetch entry point, kept so one attempt scores the same way."""
        return self.evaluate_attempts([fetched], distribution)

    def evaluate_attempts(self, attempts: List[Fetched], distribution: dict):
        if not attempts:
            return Score.FAIL, "no fetch attempts were made", {"attempts": 0}

        n = len(attempts)
        statuses = [a.status for a in attempts]
        refused = [
            a for a in attempts
            if a.status in REFUSAL_STATUSES or has_barrier_markers(a.body)
        ]
        # Identity, not equality: two attempts can be byte-identical, and a
        # dataclass compares by value, which would silently merge them.
        refused_ids = {id(a) for a in refused}
        unreachable = [a for a in attempts if not a.ok and id(a) not in refused_ids]
        refusal_fraction = len(refused) / n
        trace = f"attempts={n}, statuses={statuses}"
        # Observed facts, kept apart from the verdict. The runner adds the
        # crawler-access triad (`effective_crawler_access`,
        # `crawler_policy_mismatch_warning`) beside these, because that needs
        # robots.txt and the configured token list, which this probe does not
        # hold.
        obs = {
            "attempts": n,
            "statuses": statuses,
            "refusal_fraction": round(refusal_fraction, 4),
        }

        if refused:
            kinds = sorted({
                f"HTTP {a.status}" if a.status in REFUSAL_STATUSES
                else "barrier markers in body"
                for a in refused
            })
            return Score.FAIL, (
                f"refused on {len(refused)}/{n} attempts "
                f"(refusal_fraction={refusal_fraction:.2f}; {', '.join(kinds)}); "
                f"{trace}"
            ), obs
        if unreachable:
            return Score.FAIL, (
                f"not retrievable on {len(unreachable)}/{n} attempts "
                f"(refusal_fraction={refusal_fraction:.2f}); {trace}; "
                f"first error={unreachable[0].error}"
            ), obs
        return Score.PASS, (
            f"no anti-machine barriers detected on any of {n} attempts "
            f"(refusal_fraction={refusal_fraction:.2f}); {trace}"
        ), obs
