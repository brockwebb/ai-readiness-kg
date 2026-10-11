# CC Task: the manners layer honours a host's Crawl-delay

**Date:** 2026-10-11
**Project:** ai-readiness-kg
**Authored by:** Desktop session, from part 2's RESULT §5.12 (`cc_tasks/2026-10-07_seed_known_locations_verify_RESULT.md`).
**Implements:** no design note; a defect fix to the manners layer (`assessment/harness/scan/manners.py`), found by part 2's RESULT §5.12.
**Framework layer served (DN-005 §5 rule 1):** none directly: the scanner's conduct toward the hosts it measures. No verdict, record or score may change.
**Fulfils:** its own ResearchTask. Launched by the dispatcher.
**After:** none
**Spend:** est. 0.5M tokens (Opus). Read it as 2 to 4x low. One change to `manners.py`, fixture tests. No harness model call. Nothing is fetched from a real host.
**Network:** none beyond git push

**HEADLESS NOTICE.** No next turn. Poll every detached command to its EXIT line.

## Measured premises (verify before acting; report any that is wrong)

- Part 2's cycle made 47 requests to catalog.data.gov at the standing 1 request per second, while that host's robots.txt asks `Crawl-Delay: 10`. The seed verifier honoured it; the cycle's Fetcher (`assessment/harness/scan/manners.py`) does not read the field.
- The scanner describes itself as robots-first under an identified user agent. A rate ten times what the host asked for contradicts that in the record of every cycle that touches such a host.

## Prior art

### Internal
- internal receipt: query "crawl delay robots" | repo ai-readiness-kg@6c0be70736064cdb5f49fd8ffab6604a13103f33 | hits none (run 2026-10-11 from the seldon project; the same query hit nothing in seldon, squiddy, arnold, icsp_notebook, wintermute or the audit workbench)

### External
- RFC 9309, Robots Exclusion Protocol (2022), §2.2.4 "Other Records".

## Decisions

1. **Honour it.** RFC 9309 (Robots Exclusion Protocol) does not define `Crawl-delay`, and its §2.2.4 lets parsers read records it does not define; Bing's webmaster documentation honours it and Google Search Central documents ignoring it (Yandex dropped it in 2018). Those three are Desktop's statements from memory, not fetched here; the decision does not rest on them, because it rests on this scanner's own posture. This scanner's stated posture is to be the most polite client on the host, so the per-host interval is `max(standing interval, Crawl-delay)` for the user agent group that applies to it (the same group-matching rule the Fetcher already uses for Allow and Disallow). Parse it as a non-negative number of seconds; an unparseable value is logged and ignored, not guessed.
2. **A ceiling, stated, never silent.** A `Crawl-delay` above `manners.crawl_delay_max_s` in `params.yaml` (set it to 60 and say why that number) means the host is not fetched in that cycle, and every leg that needed it is `error` with a reason naming the host's delay and the ceiling. The cycle does not quietly run at the ceiling instead.
3. **On the record.** Each cycle's payload records, per host, the interval it actually used and its source (`standing` or `crawl_delay`). Prior payloads are untouched.
4. **Protected-file change, narrowly.** `manners.py` changes for this alone; the protected-paths script names it and the RESULT quotes the diff whole. `params.yaml` gains only `manners.crawl_delay_max_s`.

## Gate

Fixture tests, red on the current Fetcher and green after: a robots.txt with `Crawl-delay: 10` spaces requests 10 s apart under a fake clock; a group-specific delay applies only to its group; an unparseable value is ignored and logged; a delay over the ceiling yields the `error` path. Then `make gate-task`, quoting passed, skipped, xfailed, deselected and wall clock; `seldon verify`; the protected-paths diff.

## RESULT

Under 40 lines: premises checked, the diff, the tests red then green, the gate. `seldon cc complete`, commit, push.
