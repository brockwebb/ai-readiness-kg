# CC Task: Reconcile the ai-readiness-fss probe harness into the crosswalk as reference implementation

**Date:** 2026-09-01
**Authored by:** Desktop session
**Immutable once written. Before starting: glob and read all sibling `2026-09-01_harness_reconciliation_ADDENDUM*.md` files.**
**SEQUENCING: run only AFTER `cc_tasks/2026-09-01_machine_diagnostic_stub.md` has completed (both edit the skeleton; the stub adds A10/A11 and §6b.5 that this task references).**

## Context

Operator prior art at `/Users/brock/GitHub/brock_projects/ai-readiness-fss`: a working, tested, evidence-emitting probe harness ("test the machine by being the machine") implementing a benchmark rubric with dimensions D1 Discovery / D2 Retrieval / D3 Interpretability / D4 Trust-freshness plus a dated frontier track. Zero runtime dependencies, fetch/evaluate separation, per-probe evidence artifacts, config-not-constants. First external consumer: `census-web-concept-inventory` (D0/D0-r2), which ran it against the QuickFacts stratum and fed probe-design findings back; two-source enumeration and barrier intermittency landed in the harness 2026-09-01.

**Desktop decision (recorded, not re-litigated):** the harness is ADOPTED as the reference implementation of the crosswalk's `public`/AUTO tier. Adopt-before-create; it is the operator's own prior art, its invariants match the crosswalk's stance, and it has survived a consuming project. The crosswalk framework remains the superset (EVAL tier, C group, G group, TEVV loop are not in the harness and are the build target).

## Steps

All edits target `docs/crosswalk/usafacts_operationalization_skeleton.md` unless stated. Small, surgical.

### 1. §6b — add three numbered instrument design decisions (continue numbering after the stub's item 5)

> 6. **Reference implementation (adopted 2026-09-01).** The `public`/AUTO tier's reference implementation is the FSS AI Data Readiness probe harness (`brock_projects/ai-readiness-fss`): evidence-emitting probes, pass/partial/fail (2/1/0), fetch/evaluate separation, per-probe raw-artifact capture. New AUTO indicators are specified as probes against that harness's conventions rather than as free-text test descriptions. The harness covers discovery, retrieval, interpretability, and trust/freshness; EVAL-tier indicators (group C, E, G1) are outside it and remain this framework's build target.
> 7. **Core/frontier firewall with as_of dating (adopted from the harness rubric).** Indicators that test mechanisms postdating the policy corpus (llms.txt, as_of 2024-09; MCP/WebMCP-class agent endpoints, as_of 2026-01) score on a dated frontier track reported separately and never folded into any core aggregate. Machine-first remains the design norm; the scoring discipline dates every indicator and never reads absence of a post-corpus standard as core unreadiness. Presence is signal; absence is not a deficiency.
> 8. **Enumeration and scope (adopted from the harness rubric).** (a) Two measurement universes per agency — the machine-readable catalog (data.json/DCAT distributions) and the web surface (sitemap-declared product pages) — probed and reported as separate vectors, never summed; their divergence is itself a finding. (b) Scope boundary: the measurement universe is public and public-mandated assets only; protected data (Title 13/26, CIPSEA, PII) never enters the frame. The sole surviving restriction concern is restriction-discoverability: where a public catalog points at a restricted dataset, the restriction and its reason must be machine-readable — an interpretability property of the catalog.

### 2. §2 table annotations (three existing rows; do not restructure)

- Row A5 (or wherever llms.txt is the indicator): append to its Status/notes: `frontier_near track, as_of 2024-09 (§6b.7)`.
- The MCP/agent-endpoint indicator row (A-group): append: `frontier_deep track, as_of 2026-01 (§6b.7)`.
- If any row's evidence column can carry it without breaking the table, note `ref impl: ai-readiness-fss harness` on the crawler-access (A4/A11) and metadata-standard rows. If the table gets unwieldy, skip this sub-step and note the skip in the RESULT — §6b.6 already records the adoption.

### 3. §9 — add three entries

- `ai-readiness-fss probe harness adopted as public-tier reference implementation (§6b.6). Not manifest-admitted: internal repo, admission gated on publication. On publication: admit rubric + spec, crosswalk its probes item-level against A/B/D indicators.`
- `Empirical evidence pointers (internal, reproducible-by-design, admission gated): census-web-concept-inventory D0/D0-r2 findings — disconnected catalog layers (1,798/1,798 data.json distributions on api.census.gov, none on www; catalog omits 21.8% of the site's own sitemap universe); QuickFacts = 86.4% of census.gov 403s to Common Crawl (live declared/enforced/observed mismatch, instantiates A11); robots-declared vs fixed-path sitemap divergence; meta-robots nofollow on 77/98 sampled pages. Candidate self-implicating findings for the FCSM writeup.`
- `Harness gap registered: no EVAL-tier probes (group C restatement/faithfulness, G1 uncertainty preservation). The harness is hops 1–3 of the operational model; hop 4 is unimplemented anywhere. Build target, not deferral.`

### 4. Version note

Append to the file's Status line: `; v0.2.2 2026-09-01: harness reconciliation (§6b.6–8, A-row frontier dating, three §9 entries) — task cc_tasks/2026-09-01_harness_reconciliation.md`.

### 5. Cross-repo pointer (one new file, small)

Write `docs/crosswalk/reference_implementation.md` (~half page): what the harness is, path, the adoption decision and date, the firewall/dating/two-source/scope-boundary patterns adopted, the EVAL gap, and the rule that new AUTO indicators are specified as probes. Link §6b.6. Do NOT copy harness code or rubric text into ai-readiness-kg — pointer and summary only (symlinks-not-copies discipline applies in spirit; cross-repo, so a pointer doc).

## Constraints

- Zero model calls, zero spend. Do not touch the running burn, ledger, or manifest.
- Do not edit anything in `brock_projects/ai-readiness-fss` or `census-web-concept-inventory` — read-only inputs to this task.
- Verify the stub task's edits are present before starting (A10/A11 rows, §6b.5). If absent, STOP and write the RESULT stating the sequencing violation.
- Discrepancies between this task's premises and live file state go in the RESULT, never silently reconciled.

## Completion

- Run `seldon verify` after edits.
- Write `cc_tasks/2026-09-01_harness_reconciliation_RESULT.md`.
- Run `seldon cc complete cc_tasks/2026-09-01_harness_reconciliation.md`.
- Commit and push.
