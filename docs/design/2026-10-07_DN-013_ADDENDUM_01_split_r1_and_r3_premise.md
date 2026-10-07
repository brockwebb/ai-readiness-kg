# DN-013 ADDENDUM 01: R1 runs in two parts, R3's independence is declared by resource, and R6's banned list is created

**Date:** 2026-10-07. Desktop session, from the recollection RESULT (`cc_tasks/2026-10-06_absence_verdicts_recollection_RESULT.md`) and the dispatcher's stuck record. Amends DN-013; supersedes nothing in it.

## A1. R1 is two tasks
R1 needs fetches against agency hosts, and the operator reserves rescans to himself (DN-012 d6, the recollection's launch rule). Part 1, `2026-10-07_seed_known_locations_and_split_discoverability.md` (6f6d03c5), fetches nothing and runs under the dispatcher: the three false passes the recollection exposed (A2 counting a `dcat:Catalog` as an API description; D1 matching licence tokens inside HTML; A3 passing HTML as a file), the existence and discoverability rules, the discoverability candidate indicator, and the seed table. Part 2, `2026-10-07_seed_known_locations_verify.md` (c966dfd5), verifies every seed by one fetch, judges, and freezes the composite the report cites in `docs/evidence/FROZEN.md`; it is operator-launched.

**Discoverability's convention locations** are named prior art, not invention: RFC 9727 (`/.well-known/api-catalog`, June 2025) for APIs, and `/data.json` at the host root (OMB M-13-13, Project Open Data) for inventories.

**Existence `fail`** is a complete search over named seed sources (model knowledge, the repository's citations, catalog.data.gov, api.data.gov, the agency's developer page): no source records a location. That keeps DN-012 d1.

## A2. R3's premise is wrong
R3 says the precedes graph says which tasks are independent. It records orderings a Desktop wrote, not disjoint resources. Tasks with no edge between them share the Neo4j database, the append-only JSONL in git, the spend ledger, `.seldon/`, and the regenerated views. Independence is declared per task (`Exclusive`, `Touches`, default exclusive) and the scheduler never infers it: GitHub Actions concurrency groups and Make/Bazel declared outputs are the model. Registered in the seldon repo as SEL-004 (aa428cde). Evidence that a shared checkout is already unsafe: the recollection's first full-suite run died at 35% at 02:17:51Z when a Desktop session committed DN-013 in the same checkout.

## A3. R6's banned list did not exist
No file in this repository holds it. The concise report task creates `docs/style/operator_banned_words.yaml` from the operator's stated preferences (`load-bearing`, `hallucinate` with `confabulate` as his term, `delve`, `testament`; Gartner flagged as a source) and wires `scripts/dcat_faq_lint.py` to it.

## A4. Two task headers the dispatcher could never parse
DCAT-004 (d2f8166a) led its Network header with "the model CLI"; install_closure (b79134fa) led with a backticked `pip` and its layer header lacked `none`. The dispatcher refused DCAT-004 81 times from 2026-10-06T16:45Z. Both are superseded by v2 files with exact-host allowlists (a591e8b3, 283ae518). DCAT-004 v2 launched 2026-10-07T11:55:57Z. A Desktop session should run its header lines through `seldon.core.dispatch.parse_headers` before registering; that check belongs in `seldon_cc_register` (sibling of fa40072e).

## A5. Order
DCAT-004 v2 → install_closure v2 → parallel hosts and fast gate; seed part 1 after DCAT-004 v2; seed part 2 (operator) after part 1; the concise report after part 2. SEL-004 in the seldon repo, launched by the operator.
