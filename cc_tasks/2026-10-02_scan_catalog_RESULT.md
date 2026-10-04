# RESULT: the scan catalog (task `aaffd0db`, with ADDENDUM-01)

**Status:** complete. Every gate in §7 ran to its EXIT line before this file was written. The full suite is **red on 5 tests that are red on a clean checkout of the launch base `856a1167`**. Those 5 are the corpus-manifest view guards, unchanged since the Commerce admission (§7). Layer: DN-005 §2.4 exposure. Shipped: `docs/catalog/` (README, `scan_catalog`, `actions`, `enablers`, `front_door`, `catalog_inputs.yaml`, `rollups/`), `scripts/build_scan_catalog.py` (`--check` is byte-for-byte), `scripts/check_protected_scan_catalog.sh` and `tests/test_scan_catalog.py` (33 tests, 2 of them negative controls).

## 1. Rows
**71 scan rows over all 49 indicators.** By who can run them: `public_outside_in` 41, `agency_enabled` 9, `agency_records` 8, `needs_standard` 13. By method kind: `built_rule` 26, `tool_open_source` 8, `tool_commercial` 10, `roll_your_own` 23, `none_known` 4. By row source: `record` 62, `catalog_search` 2, `proposed_link` 7. **64 action rows**: all 63 record Actions plus `named:llms-txt`. Of the 32 unmeasured framework indicators, the easiest route on any row is: public 10, needs a standard 9, agency records 7, agency-enabled 0. For the other 6 (B1, B2, B4, D2, E5, G4), no row offers anything to obtain. Each has a built rule; its unmeasured half is either `none_known`, or held up only by the definition of measured.

## 2. Greedy set cover (Chvátal), in order
Each step adds the unlocker that covers the most indicators not yet covered. Ties break on who can act alone, then on name. The order: `tool:wayback-cdx-server` (A7, F3), `pre:vintage-disambiguation-set` (C3, G2). Then one indicator each: `method:B6:wcag_reading_level`, `method:D3:prov_walk`, `method:G3:sdmx_structure_map`, `method:G5:sdmx_conf_status`, `pre:second-scan-cycle` (B5), `pre:second-scan-cycle+tool:oasdiff` (F2), `tool:aidrin` (C5), `tool:slsa-verifier` (F6), then 6 benchmark and probe sets (C1, C2, C4 by the engine-query route, E6, E8, E9, G6), then 7 agency-records sets (E1 to E4, E7, F1, F5). **24 steps cover 26 of 32**, and the remaining 6 are the ones listed in §1. The full order is in `rollups/set_cover.csv`.

## 3. Enabler candidates (decision 4)
**The operator's hypothesis, that one agency action unlocks many scans, is not supported.** No enabler unlocks more than **1** unmeasured framework indicator. The others deepen indicators that are already measured.
- Bing Webmaster Tools: **supported**. Existing node for C4 (the AI Performance report), proposed link for A11.
- Google Search Console: **supported**, proposed links for A5, A6 and A11 (all three already measured). The C4 link is **unsupported**: AI Overviews are "included in the overall search traffic", so the report cannot separate them.
- Web analytics (DAP): **supported**, proposed link for C4 through AI-referral visits (Watanabe 2026). Nothing on file says DAP sees crawlers.
- Cloudflare AI Crawl Control: **supported**. Existing node for A11, proposed link for A12.
- Akamai DataStream 2: **supported**, proposed link for A11.
- Raw server logs (GoAccess): **supported**, existing node for A11.
- robots.txt and sitemap submission: **unsupported** as an instrument. It is a discovery action, and those files are already public.

## 4. Value, effort and the grids (ADDENDUM-01)
Rubric v1 was written into the README first. Its prior art is Karlsson and Ryan 1997 (the cost-value approach), Seldon's Eisenhower grid, and OECD/JRC on weights (CL-083). The record's notional bands were mapped order-preservingly onto 1 to 5. `procurement` maps to `TBD`, and a tool's staffing is `TBD`. **The actions quick-win cell holds 10 actions, all `established`, 9 with `cheap_pass: yes`**: four robots.txt and crawler-access edits (A4, A11 ×2, A12), the sitemap listing (A5), three Dataset-markup edits (A6) and two catalog edits (D4). **`llms.txt`: value 1, `unevidenced`.** Ahrefs (2026-06-15) measured 137,210 domains: "97% of those files received zero traffic in May." That does not meet the operator's expectation of high value. **robots.txt:** serving one where none exists rates 2, because RFC 9309 §2.3.1.3 lets crawlers fetch anything when there is no file. Removing a disallow on data paths rates 5. The operator documentation for 7 of the 8 user agents the harness probes is cited. Claude-Web is named in none.

## 5. Cheap-pass prior art (decision 8)
The corpus holds none of it: `Goodhart`, `Campbell`, `gaming` and `composite indicator` returned 0 hits. Read on the web: Goodhart, via Manheim and Garrabrant 2018 (arXiv:1803.04585), whose four variants include *adversarial*; and Campbell 1979 (*Evaluation and Program Planning* 2(1)). In the corpus: Kumar and Lakkaraju 2024 (strategic text sequences), applied to C4. Each judgement is filled by a described case taken from the rule module or spec.

## 6. Front door (decision 13; no new request)
Vendor named by stored headers or refusal pages on `scan_2026-09-10`:
- Cloudflare: CENSUS (`server`, 230 of 235 observations), BJS, DRSMSU, NIST.
- Akamai: BLS (also named in its HTTP 403 page body), BTS, EIA, NAHMSAPHIS, SOI.
- `x-azure-ref`: BEA, NASS, NCHS.
- CloudFront: data.gov, GSA.
- `not_observed_in_record`: ERS, NCES, NCSES, ORES, SAMHSACBHS.

## 7. Gates (logs under `logs/`, not shipped)
- `make gate-fast`: **5 failed, 2885 passed, 3 skipped, 27 deselected, 12 xfailed**, 694.08 s, EXIT=2 (`logs/scan_catalog_gate_fast.log`).
- Full suite: **5 failed, 2912 passed, 3 skipped, 0 deselected, 12 xfailed**, 2373.63 s, EXIT=1 (`logs/scan_catalog_gate_full.log`).
- The 5 failing tests: `test_brief_deck`, `test_brief_pack` ×2, `test_g4_resourcing_reissue` and `test_publication`. Each failed identically in a clean worktree of `856a1167` (`logs/scan_catalog_head_baseline.log`, `logs/scan_catalog_head_baseline_pack.log`); the Commerce and definition-pass RESULTs report the same 5. They are not fixed here, because `docs/brief/`, `docs/deck/` and `docs/data/` are protected.
- `tests/test_scan_catalog.py`: 33 passed, 0 skipped (`logs/scan_catalog_tests.log`).
- `seldon verify`: all checks passed, EXIT=0 (`logs/scan_catalog_seldon_verify.log`).
- Protected paths: PASS, EXIT=0, `--check` no drift (`logs/scan_catalog_protected.log`).

## 8. Reader gate (DN-009 d7)
The fresh subagent read only the README, `rollups.md` and `actions.md`. Its first run misread the label "nothing to acquire" as "needs nothing", so the label was renamed and indicator texts were added. The second run, verbatim:
> 1. From outside, with no help from the agency, the public can run 41 of the catalog's 71 scans, and for 10 of the 32 indicators not yet measured, the easiest route is one of these outside scans: persistent URLs (A7), consistent identifiers (B5), plain-language summaries (B6), scoring against published AI-data-readiness metrics (C5), published lineage (D3), versioned API changes (F2), identifiers that survive a new vintage (F3), signed releases (F6), stable series IDs (G3) and machine-readable suppression documentation (G5).
> 2. Seven unmeasured indicators need records only the agency holds: E1 to E4, E7, F1 and F5, which cover its evaluation reports, thresholds, eval-set versions, held-out rotation, failure-closure records, release-validation records and staging regression records. No unmeasured indicator has an easiest route that needs the agency to turn something on, such as an account, a console or analytics; that category has 0 indicators.
> 3. Nine unmeasured indicators need a standard or reference set that does not exist yet: C1 to C4, E6, E8, E9, G2 and G6, mostly question benchmarks, probe sets and adversarial test banks for how AI tools answer about the data. For 6 more (B1, B2, B4, D2, E5, G4), no row offers anything to obtain at all.
> 4. No single agency-side enabler unlocks more than 1 unmeasured indicator: Bing Webmaster Tools and web analytics each reach only C4, whether AI engines cite the authoritative page. The widest reach is Google Search Console at 3 indicators (A5, A6, A11), but all 3 are already measured, so it deepens existing measurements rather than adding new ones.
> 5. The actions "quick win" cell holds 10 actions, all with `established` evidence and 9 marked `cheap_pass: yes`: permit in robots.txt the AI crawlers you intend to serve; allow your data paths for those crawlers; resolve a meta-robots tag that contradicts robots.txt; publish a robots.txt group an identified machine client matches; list the product URL in the sitemap; embed JSON-LD on the product page; type that markup as a Dataset; make it conform to its declared profile; add the product to the public data inventory; and make the catalog conform to DCAT-US.
>
> ONE ACTION: I would first allow the product's data paths in robots.txt for the AI crawlers we intend to serve, because the files rate it at the top value (5, "data unreachable or unusable by a machine reader"), its notional effort is hours at no cost, and the evidence that crawlers obey robots.txt is `established`.

## 9. Premises wrong
1. The OECD/JRC Handbook is not in the corpus, as CL-083 had already recorded.
2. The corpus holds 265 admitted documents, not 264.
3. The record has no indicator rationale, so `why` is `TBD` on 48 of 49 indicators. A12's `candidate_rationale` fills the 49th.
4. The record misses methods: CL_CONF_STATUS (SDMX) for G5, which the record says has no field, and WCAG SC 3.1.5 for B6. Both are web sources; writing them back is a follow-on.
5. No bib entries were added: `docs/evidence/` is byte-identical by this task's terms.
6. The write set grew by `catalog_inputs.yaml`, `enablers.*`, four extra rollup CSVs, `rollups.md` and the check script.

**Network:** shell egress was `git push` only. The harness made 9 WebSearch and 16 WebFetch calls; 2 fetches failed (Bing help returned a 404 and one page came back empty). **Model and tokens:** `claude-opus-5-5`, measured from the transcript (124 turns): 248 input, 140,117 output, 372,338 cache-write and 27,839,370 cache-read tokens. The reader-gate subagents used 74,235 and 76,945 tokens. There were no other model calls.
