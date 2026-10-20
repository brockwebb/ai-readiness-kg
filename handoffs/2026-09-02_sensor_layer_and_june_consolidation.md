# Handoff — 2026-09-01/02: sensor layer, June consolidation, orientation-first

Desktop thread. All tasks zero model spend; burn ran throughout.

## What happened

- SEO SME's Machine Diagnostic spec (internal draft, admission gated) assessed as a Tier-1 sensor instrument for the discovery/access slice. Stubbed conceptually: A10 (application/data-tool machine surface), A11 (declared/enforced/observed crawler access), §6b.5 (observed facts vs versioned warning rules), G1 measurement-template note. Item-level rule crosswalk deferred to spec finalization.
- Working deck built (18 slides, v3, plain pptx at `docs/crosswalk/framework_deck_2026-09-01.pptx`, content at `deck_content_2026-09-01.md`, builder `scripts/build_framework_deck.py`). Includes OV-1, SV-1 (capability language only), knowledge-architecture slide, and the audience-education slide for staff with no SEO/AIO background.
- June 2026 ai-readiness-fss work compared document-by-document against the crosswalk, then consolidated INTO this repo by git subtree (`assessment/`, history preserved, old location tombstoned, untracked cc_tasks/results/evidence moved afterwards). Two conflicts found and resolved: unit of analysis (two-level: product profiles → agency vectors → cohort reading) and frontier firewall vs machine-first rhetoric (firewall adopted; machine-first is a design norm, never core scoring). Merged live design at `docs/crosswalk/assessment_protocol.md`; DD-031.
- Orientation-first rule codified: discovery is the first-order construct; the established discovery stack (RFC 9309, sitemaps, RFC 8615, schema.org Dataset, DCAT, content negotiation, PIDs) is core-scored; any mechanism old or new is a hypothesis admitted or retired by observed machine behavior, never by vintage. MCP/llms.txt are dated frontier candidates. Deck de-MCP'd accordingly.
- CC dispatch protocol added to CLAUDE.md (operator order). Seldon verify crash root-caused and fixed (directory registered as DataFile); snapshot-artifact drift semantics escalated to the Seldon project.

## Queued (dispatch lines in the thread; sequencing noted in each file)

- `seldon/cc_tasks/2026-09-02_snapshot_artifacts_verify.md` — Seldon repo, first.
- `cc_tasks/2026-09-02_housekeeping.md` — A9 into §2, snapshot flags (after the Seldon task), verify clean.
- `cc_tasks/2026-09-02_probe_depth_d0r2.md` — four D0-r2 harness defects, verify-first, fixtures required.

## Next design session

Hop-4 / EVAL tier (group C, G1): no implementation exists anywhere. Prior-art search first (RAG faithfulness frameworks for restatement fidelity; uncertainty-preservation has no known named prior art, which is a claim requiring the failed search). Then a probe family under `assessment/harness/`.

## Waiting on the world

SEO spec finalization → item-level crosswalk + admission. Harness tagged release → admission. Burn completion → replace "floor" numbers in deck slide 15 with real counts.

## Superseded, keep on disk

`cc_tasks/2026-09-01_harness_reconciliation.md` (ADDENDUM-01 guards it). Never dispatch.
