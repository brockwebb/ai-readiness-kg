# RESULT: every seed verified by one GET, `scan_2026-10-07_seeded` measured, and `scan_2026-10-07_composite_d` frozen as the composite the concise report cites

**Task:** `cc_tasks/2026-10-07_seed_known_locations_verify.md` with `_ADDENDUM_01.md`, which was read before any step and committed with the first commit (`d39a6fb1`). The task was launched by the operator, not dispatched. **Layer:** DN-005 §2.2, measurement. **Spend:** no harness model call. The session ran on `claude-opus-5-5` and used about 0.7M tokens of context; no tool meters this, so it is an estimate. The addendum's estimate was 3M. **Network:** manners layer only (identified UA, robots-first, 1 req/s per host). catalog.data.gov's `Crawl-Delay: 10` was also honoured by the verifier, but the cycle's Fetcher (`manners.py`, protected) does not read it (§5 item 12).

**Gate: green, on `86b34d06`.** `make gate-task`: fast tier 3284 passed, 4 skipped, 41 xfailed, 30 deselected, 186.09 s; re-derivation 25 passed, 0 skipped, 0 xfailed, 25 deselected, 4.21 s; wall clock 3 m 12 s; `EXIT=0` (`logs/svl_gate_task_2.log`; the deselected counts come from `--collect-only`, `svl_gate_task_collect.log`, because xdist prints none). The 4 skips are two live-model tests (`test_dispatch_config.py:305`, `:373`), `test_scan_harness.py:290` and `test_g1_preservation.py:337`. **`test_kg_questions.py:115` now runs and passes; it does not skip.** The first gate run (`svl_gate_task.log`) failed 8 tests, in 6 test functions; §5 items 9–10 give the causes. `make guards` (a guard test changed): 80 passed, 0 skipped, 0 xfailed, 0 deselected, 63 s, `EXIT=0` (`svl_guards.log`). `seldon verify`: all checks passed, `EXIT=0` (`svl_seldon_verify.log`). **Protected paths:** `scripts/check_protected_seed_known_locations_verify.sh` against `512c1315` gives PASS, `EXIT=0` (`svl_protected.log`). It holds byte-identical every rule and collector, `manners.py` and `score.py`. It also holds every prior payload, matrix and task file. It names the two admitted files, whose diffs are quoted whole in the appendix. It checks shape too: `params.yaml` moves only in `cycle.name` and `d1_sources.terms_text_max_bytes`; `targets.yaml` moves only in `declared_locations`, with every `read_from` kept; the part 1 seed table moves only in `status` and `verified_at`; the event shards and the Seldon store only grow.

## 1. Hosts, data.gov, verification (decisions 1–2)
- **Host list:** 45 hosts (every seed host plus catalog.data.gov, api.data.gov and the 16 roster hosts), printed and recorded at 2026-10-11T04:01:04Z, before the first request (`state/seed_verification_hosts_2026-10-11.json`). It was amended once, before any request to the two hosts added: `gis.ers.usda.gov` and `nassgeodata.gmu.edu`, both named by catalog.data.gov seeds.
- **Requests:** the verifier made 286 requests over 47 hosts (`state/seed_verification_runs_2026-10-11.jsonl`): catalog.data.gov 131, www.census.gov 9, and 7 or fewer on each other host. The cycle made 1,078 requests over 37 hosts (payload `requests_per_host`): www.census.gov 89, www.bea.gov, www.cdc.gov and www.ers.usda.gov 81 each, and catalog.data.gov 47.
- **data.gov:** the seed table's queries returned 404 (CKAN's action API is gone since the catalog was rebuilt). I ran the same question through the site's own `/search` instead, by organization and publisher. That found 30 seeds, 13 of them API bases: BEA, Census (under `commerce` as "U.S. Census Bureau"), EIA, ERS and NASS. `/harvest_source/<id>` returns 404. api.data.gov's `/docs/` returns 404 and the site lists no API, so it is recorded as searched, with no seeds.
- **Seeds:** 178 seed entries over 130 distinct URLs, each fetched once. Entries by source (an entry can have several): repo 119, model knowledge 53, developer page 44, catalog.data.gov 30, api.data.gov 0. By status: verified 66, not_the_object 47, http_403 31, refused_robots 21, http_404 11, http_500 2. The tests are in `seeds/verification.yaml`. A changelog must carry ≥2 distinct dates *and* be titled as a log of changes. A seeded API base must be on one of the body's hosts. The per-seed report is `state/seed_verification_2026-10-11.json`.
- **`targets.yaml` scheme 2:** every location the recollection read keeps its `read_from`. Every location still standing (verified, refused or unverified) carries `seeded_from`, `status` and `verified_at`. `searched` records, per object, which sources were searched. A seed that came back 404/410 or `not_the_object` stays in the seed tables, with its status.

## 2. Collection changes (ADDENDUM A), each red before and green after (`tests/test_seeded_cycle_collection.py`: 10 failed on `HEAD` `runner.py`/`run.py`, 10 passed after; `svl_tests_pre_change.log`, `svl_tests_post_change.log`)
- **A13:** A13 is now a leg of every Tier A product row (`run.targets`). `--pages-from` builds each surface's page Observation from the 10-06 page, with no fetch: collector `stored_page`, with this cycle's `declared` block, kept off E5's clock. A2 fetches RFC 9727 `/.well-known/api-catalog` on the product host and on a verified API host, plus `/data.json` on the API host. **A13 fetches: 72** (`api_catalog` 59: www.census.gov, www.bea.gov, www.cdc.gov, www.ers.usda.gov, www.nass.usda.gov, api.census.gov and data.cdc.gov 4 each, the rest 2–3; API-host `/data.json` 13: api.census.gov 4, data.cdc.gov 4, api.ojp.gov 3, data.bts.gov 2). No host serves `application/linkset+json`, and no page sends `rel="api-catalog"`. **A13 per body (pass/fail/error):** DRSMSU 2/0/0; BEA, CENSUS, ERS, NASS, NCHS 0/4/0; BJS, NCSES, SOI 0/3/0; NAHMSAPHIS, NCES, SAMHSACBHS 0/2/0; EIA 0/2/1; BLS, BTS, ORES 0/0/2.
- **D1:** the terms page is now kept whole, up to `d1_sources.terms_text_max_bytes` = **4,194,304**. I chose it from the largest terms page the seed tables name: BEA's API user guide, 1,376,062 bytes, a PDF (the largest HTML page is census.gov popest's, 364,944 bytes). That gives about 3× headroom, under the 15 MB Googlebot reads per file. **Census 4 error → 4 fail and EIA 3 error → 3 fail.** Both terms pages are read whole, and each states its licence in free text, not as an identifier.

## 3. Cycle, composite, freeze (decisions 3–5)
- **`scan_2026-10-07_seeded`:** control gate PASS. 460 Findings: 12 pass, 203 fail, 245 error. Re-derivation is identical, 762/762 (`svl_rederive.log`). Published: 478 bodies promoted, 1,784 Observation events and 762 Finding events, 0 Findings with unretained evidence (`svl_publish.log`). `pages_read_from` is on the payload.
- **Per leg on the 46 surfaces, `_composite_c` → `_composite_d` (pass/fail/error):** A2 0/7/39 → 0/25/21 · D1 0/0/46 → 0/31/15 · F4 0/15/31 → 0/36/10 · A9 4/3/39 → 10/5/31 · D4, B4, D3, G4 0/14/32 and B1 0/13/33, unchanged · A13 — → 2/37/7.
- **`scan_2026-10-07_composite_d`:** the ten legs above, over `_composite_c`. That keeps A1, A3 and B3 from `recollect_rj1` and every other leg from `rj5`: 1,055 Findings in all (`svl_composite_d.log`). Published as the cycle of record: matrices; Results registered 120 for the seeded cycle and 174 + 168 + 3 + 86 for the composite; 6 figures; framework write-backs (D1 is now `measured`); a projection of 5,366 s, with the round-trip gate green. Every view was rebuilt and all 14 `--check` runs pass (`svl_views_check_3.log`). Tagged Results: 68 of 68 reproduce. 53 Results are published at `24df342e`/`3431bbd6`, and 49 `_composite_c` Results are `stale` with `superseded_by`.
- **Evidence map and freeze:** `docs/evidence/claims.yaml` cites `_composite_d` (0 references to `_composite_c`). `docs/evidence/FROZEN.md` reads: `scan_2026-10-07_composite_d`, commit `cd0ccae6de99`, 2026-10-11T06:37:54Z, "the concise report cites this composite and no other".
- **KG answers (ADDENDUM B):** `scripts/run_kg_questions.py` re-ran against the projection. The only change of substance: A13 enters the crosswalk as a candidate item. It now reads 50 items to 49 constructs (was 49 to 48), 2 candidate items, and 49 constructs with no definition. No question was edited.

## 4. Delta (decision 6, `docs/research/2026-10-11_seeded_delta.md`, `scripts/seeded_delta.py`)
**Headline: 15 body × object pairs, in 11 bodies, where the object exists and no product page of the body reaches it, out of 29 pairs where it exists.** Per surface, the count is 54 of 88. Existence and discoverability are `RULE-A13-v1`'s own `_exists` and `per_object` over the stored Observations.

## 5. Premises wrong (the task's, then mine)
1. **catalog.data.gov's CKAN API and api.data.gov's `/docs/` are gone** (§1). The `census` organization holds the TIGER records; Census's API records are under `commerce`. ORES's records are published by its parent, SSA, as DRSMSU's are by the Board (an alias in config).
2. **Scheme 2 holds one `api_base` and one `terms_url` per body.** The rule for the slot: the recollection's entry if it still stands; else a verified machine-readable base; else an unverified base; else a verified landing page. Every other candidate stays in the seed tables with its status.
3. **The addendum says "stored whole as visible text"; I stored it whole as served.** The frozen `RULE-D1-v6` decides truncation by comparing the bytes kept with the bytes served, and it reads `rel="license"` links out of the HTML. Pre-stripped text would read as truncated on every page. Over the ceiling, the reason names the bytes kept (the ceiling), not the parameter's key, because the rule is frozen.
4. **A13 reads only the legs it consumes,** so the convention fetches ride on A2. A 403 at `/.well-known/api-catalog` is worded by the rule as "was not fetched" (4 surfaces).
5. **The stored 10-06 page carries the recollection's scheme-1 `declared` block.** `_existence.declared` merges blocks first-wins, so that block would have shadowed the seeded API base. The page Observation is therefore rebuilt from the stored fields: new `obs_id`, same `captured_at`, bytes and links.
6. **A composite over a composite was unsupported.** `composite.py` scheme 2: `parts`, `collections` and recursive `evidence`; a flat composite is unchanged (`tests/test_composite_nested.py`). Five readers that opened `composed_of` directly were updated.
7. **The seeded shard carries U+0085 in raw form** (a decoded PDF). `str.splitlines()` splits there, and JSON Lines does not. Six readers now split on `"\n"`, guarded by `tests/test_shard_line_separator.py`. The events are valid JSON Lines and were not touched.
8. **The evidence map needed the new rule wordings:** Q2 classifies D1's free-text branch as nonconformant and A13's as an absence; Q4 reads generation 16's inventory remainder.
9. **`ind:A2` and `ind:D1` reach no admitted source,** so a report that quotes them by number breaks DN-001's floor (5 of the 8 first-gate failures). Both are stated in words, untagged, as part 1 did for A2. `scan_l0_product_a2_applicable_n_2026-10-07_composite_d` was published while it was still tagged, and stays published.
10. **Test pins moved, each with its reason:** scheme 1 → 2, BEA's recorded API, the snapshot payload, the cycle of record, the F5 blanks, measurement status 23/1/26, payload kinds 8 measured / 3 composite, and locator reads.
11. **Writes outside the stated set, each needed:** `composite.py` and its readers; the shard readers; `build_evidence_map.py`; `publication.yaml`; `figures.yaml`; the report sections; the test pins. The data.gov search responses (526 MB) are kept local under `state/evidence_staging/` with their digests on the log, not committed. The promoted cycle evidence (107 MB) is committed under the scan store's own rule.
12. **Pre-existing, unchanged:** the scan runner is not checkpointed (§15). The Fetcher ignores `Crawl-Delay` (the cycle hit catalog.data.gov 47 times at 1 req/s). D1 reads a PDF terms page as text.

**Next:** admit sources for `ind:A2` (OpenAPI) and `ind:D1` (SPDX / Creative Commons), so both can be quoted. Teach `adopt.py` to declare locations.
**STOP file:** `.seldon/DISPATCH_STOP` has been present since 2026-10-11T03:51:00Z (its mtime; the operator's, for this launch). Per the task's SEQUENCING, this session removes it last, after the push; the removal time is given in the session's closing message.
**Logs:** `logs/svl_hosts.log`, `svl_datagov{,_2,_3}.log`, `svl_verify.log`, `svl_classify_2.log`, `svl_declare.log`, `svl_relocate.log`, `svl_tests_pre_change.log`, `svl_tests_post_change.log`, `svl_cycle.log`, `svl_rederive.log`, `svl_publish.log`, `svl_composite_d.log`, `svl_reg_seeded_matrices.log`, `svl_registrations_2.log`, `svl_writebacks.log`, `svl_projection.log`, `svl_rederive_tagged_3.log`, `svl_verify_states{,_2}.log`, `svl_publish_states{,_2}.log`, `svl_supersede_3.log`, `svl_views_{8,9}.log`, `svl_views_check_3.log`, `svl_gate_task{,_2}.log`, `svl_gate_task_collect.log`, `svl_guards.log`, `svl_seldon_verify.log`, `svl_protected.log`, `svl_collector_diffs.diff`.

## Appendix: the two collector diffs (ADDENDUM_01 A, quoted whole, `git diff 512c1315 -- runner.py run.py`)

```diff
diff --git a/assessment/harness/scan/run.py b/assessment/harness/scan/run.py
index e2b38720..73212b15 100755
--- a/assessment/harness/scan/run.py
+++ b/assessment/harness/scan/run.py
@@ -30,7 +30,7 @@ from scan.model import (Observation, SYNTHETIC_PREFIXES,       # noqa: E402
                         params_hash)
 from scan.rules import (BODY_LEGS, CANDIDATE_LEGS, CURRENT,       # noqa: E402
                         FRAMEWORK_LEGS, body_groups, consumes, judge as judge_rule)
-from scan.runner import collect_leg                            # noqa: E402
+from scan.runner import STORED_PAGE_COLLECTOR, collect_leg     # noqa: E402
 
 FRAMEWORK = REPO / "framework" / "ai_readiness_framework.json"
 #: Where a cycle STAGES the bodies it captures, before anything is published.
@@ -529,6 +529,14 @@ def targets(params: dict, bodies=None) -> list:
             # the same rule passes on product surfaces; what is withdrawn is the LEVEL, not the
             # leg.
             legs = [l for l in CONTROL_LEGS if l not in withdrawn_on(params, kind)]
+            # A candidate that judges a PRODUCT surface reaches it here
+            # (`cc_tasks/2026-10-07_seed_known_locations_verify_ADDENDUM_01.md` A): A13 asks
+            # whether a machine starting from this page reaches the body's API, terms, changelog
+            # and inventory, so it is a leg of every Tier A surface that is not a host's
+            # well-known set. A candidate in `HOST_LEGS` (A12) stays on `well_known` rows only.
+            # Candidate Findings sit on the matrix and enter no level and no score (DD-054).
+            legs += [l for l in sorted(CANDIDATE_LEGS)
+                     if l not in HOST_LEGS and l not in withdrawn_on(params, kind)]
         url = r["url"]
         if not synthetic:
             url = ((entries[doc_id].get("identity") or {}).get("source_url") or url)
@@ -637,9 +645,36 @@ def merge_controls(payload_path: Path, params: dict, clock=None) -> int:
     return 0
 
 
+def stored_pages(cycle: str, tgts: list) -> dict:
+    """`{doc_id: page Observation row}`: the link probe's product-page Observation of each
+    target in a stored cycle, for `--pages-from` (`ADDENDUM_01` A, base decision 4: "the
+    product-page link observations are read from scan_2026-10-06_recollect, not re-fetched").
+
+    Refuses rather than guesses: a target with no stored page, or with more than one, would be
+    judged on a page another surface recorded or on none."""
+    path = STATE_DIR / f"{cycle}.json"
+    if not path.is_file():
+        raise SystemExit(f"REFUSING: --pages-from {cycle}: {path} does not exist")
+    rows = json.loads(path.read_text(encoding="utf-8")).get("observations_detail") or []
+    pages: dict = {}
+    for o in rows:
+        if o.get("leg") != "link_probe" or (o.get("parsed") or {}).get("probe") == "link" \
+                or str(o.get("target_doc_id", "")).startswith("control:"):
+            continue
+        if o["target_doc_id"] in pages:
+            raise SystemExit(f"REFUSING: {cycle} holds two page Observations for "
+                             f"{o['target_doc_id']}")
+        pages[o["target_doc_id"]] = o
+    missing = [t["doc_id"] for t in tgts if t["doc_id"] not in pages]
+    if missing:
+        raise SystemExit(f"REFUSING: {cycle} recorded no product page for {len(missing)} "
+                         f"target(s), first {missing[:3]}")
+    return {t["doc_id"]: pages[t["doc_id"]] for t in tgts}
+
+
 def run_cycle(params: dict, tgts: list, controls: tuple, fetcher, *, task: str,
               evidence_root: str, cycle: str | None = None, spot_targets=None,
-              legs_collected=None, surfaces_dropped=None) -> dict:
+              legs_collected=None, surfaces_dropped=None, pages_from=None) -> dict:
     """Measure `tgts` after a control gate that PASSED, and return the cycle's payload.
 
     Factored out of `main` (`cc_tasks/2026-09-19_spot_scan.md` decision 5) so the spot path can
@@ -704,7 +739,11 @@ def run_cycle(params: dict, tgts: list, controls: tuple, fetcher, *, task: str,
     # cycle if a control misfired; this re-judges E5 with the ordering evidence now that there
     # IS a first real host, so the cycle's recorded E5 Finding carries the whole signal rather
     # than the half a pure rule could see beforehand.
-    earliest = min((o.captured_at for o in all_obs), default=None)
+    # A product page READ from a stored cycle (`--pages-from`) carries the time its bytes were
+    # captured, in that cycle; no host was asked for it in this one, so it is not this cycle's
+    # first contact with a real host and is left off the ordering clock.
+    earliest = min((o.captured_at for o in all_obs if o.collector != STORED_PAGE_COLLECTOR),
+                   default=None)
     if earliest:
         for o in control_obs:
             if o.leg == "E5":
@@ -725,6 +764,10 @@ def run_cycle(params: dict, tgts: list, controls: tuple, fetcher, *, task: str,
         **({"legs_collected": list(legs_collected),
             "surfaces_dropped": list(surfaces_dropped or [])}
            if legs_collected is not None else {}),
+        # Where this cycle's product pages came from when they were read rather than fetched
+        # (`--pages-from`): the stored cycle, how many, and the rule, on the payload so the
+        # cycle's manifest says it (base decision 4).
+        **({"pages_read_from": pages_from} if pages_from else {}),
         **({"spot_targets": list(spot_targets),
             # The frame cycle `params.yaml` names on the day the spot ran. Recorded, not
             # implied: the spot measured under that cycle's parameters and is not that cycle.
@@ -948,6 +991,10 @@ def main(argv=None) -> int:
                          "the frame gives them; a surface left with none is not contacted. The "
                          "payload records `scope: legs`. "
                          "cc_tasks/2026-10-06_absence_verdicts_recollection_v2.md decision 2")
+    ap.add_argument("--pages-from", default=None, metavar="CYCLE",
+                    help="with --legs: read each surface's product page from this stored "
+                         "cycle's link-probe Observation instead of fetching it, and probe no "
+                         "link. cc_tasks/2026-10-07_seed_known_locations_verify_ADDENDUM_01.md A")
     a = ap.parse_args(argv)
     params = load_params()
     if a.frame:
@@ -979,6 +1026,21 @@ def main(argv=None) -> int:
         print(f"TARGETED cycle: {len(tgts)} surface(s) on {', '.join(legs_collected)}; "
               f"{len(surfaces_dropped)} surface(s) carry none of them and are not contacted",
               file=sys.stderr)
+    pages_from = None
+    if a.pages_from:
+        if legs_collected is None:
+            raise SystemExit("REFUSING: --pages-from reads stored pages for a TARGETED cycle; "
+                             "give --legs")
+        pages = stored_pages(a.pages_from, tgts)
+        tgts = [dict(t, stored_page={"cycle": a.pages_from, "row": pages[t["doc_id"]]})
+                for t in tgts]
+        pages_from = {"cycle": a.pages_from, "surfaces": len(tgts),
+                      "collector": STORED_PAGE_COLLECTOR,
+                      "rule": ("each surface's product page is the link probe's page "
+                               "Observation in this cycle, read from the stored cycle and never "
+                               "re-fetched; no link is probed (ADDENDUM_01 A, base decision 4)")}
+        print(f"PAGES read from {a.pages_from} for {len(tgts)} surface(s); none re-fetched",
+              file=sys.stderr)
     # Redirect the module-path global rather than threading a root through seven collectors:
     # `store_evidence` reads `EVIDENCE_ROOT` at CALL time, which is the repo convention
     # (CLAUDE.md "Conventions specific to this repo") and the same seam `tests/conftest.py`
@@ -1041,7 +1103,8 @@ def main(argv=None) -> int:
     from scan.manners import Fetcher
     summary = run_cycle(params, tgts, (cf, e5, control_obs), Fetcher(params), task=a.task,
                         evidence_root=_staging_rel, cycle=cycle, spot_targets=spot_targets,
-                        legs_collected=legs_collected, surfaces_dropped=surfaces_dropped)
+                        legs_collected=legs_collected, surfaces_dropped=surfaces_dropped,
+                        pages_from=pages_from)
     cycle_out, _ = out_paths(params, cycle)
     write_payload(cycle_out, summary, params)
     print(json.dumps({k: v for k, v in summary.items()
diff --git a/assessment/harness/scan/runner.py b/assessment/harness/scan/runner.py
index d9f7b007..7455b89a 100644
--- a/assessment/harness/scan/runner.py
+++ b/assessment/harness/scan/runner.py
@@ -48,6 +48,87 @@ def _with_declared(obs: list, block) -> list:
     return obs
 
 
+#: The collector of a product-page Observation READ from a stored cycle, never fetched
+#: (`cc_tasks/2026-10-07_seed_known_locations_verify_ADDENDUM_01.md` A, base decision 4). Its
+#: `obs_id` differs from the stored one because the collector and the params are this cycle's;
+#: its `captured_at`, `request` and `response` are the stored Observation's, and
+#: `parsed.read_from_cycle` names that Observation. `run.run_cycle` excludes it from E5's "every
+#: control precedes the first real host" clock, because no host was asked for it in this cycle.
+STORED_PAGE_COLLECTOR = "stored_page"
+STORED_PAGE_VERSION = "0.1.0"
+#: The page facts carried over. `link_candidates` is not: it counts the stored cycle's link
+#: PROBES, and this cycle probed none, so carrying it would put another cycle's requests on a
+#: page Observation of this one. `declared` is not: this cycle's block is attached instead.
+STORED_PAGE_KEYS = ("content_type", "final_url", "extension", "links", "links_error")
+
+
+def stored_page(stored: dict, leg: str, doc_id: str, url: str, params: dict):
+    """The link probe's product-page Observation for this surface, made from the Observation
+    a stored cycle recorded for it (`target["stored_page"]`, set by `run.py --pages-from`). No
+    request is made. Refuses a stored row of another surface or another URL."""
+    from .model import Observation
+    row = stored["row"]
+    if row.get("target_doc_id") != doc_id or row.get("target_url") != url \
+            or row.get("leg") != leg or (row.get("parsed") or {}).get("probe") == "link":
+        raise ValueError(f"stored page {row.get('obs_id')} is not the {leg} page of "
+                         f"{doc_id} at {url}")
+    parsed = {k: row["parsed"][k] for k in STORED_PAGE_KEYS if k in (row.get("parsed") or {})}
+    parsed["read_from_cycle"] = {"cycle": stored["cycle"], "obs_id": row["obs_id"],
+                                 "captured_at": row["captured_at"]}
+    return Observation.make(leg, leg, doc_id, url, STORED_PAGE_COLLECTOR, STORED_PAGE_VERSION,
+                            params, dict(row.get("request") or {}),
+                            dict(row.get("response") or {}), parsed=parsed,
+                            error_class=row.get("error_class"),
+                            captured_at=row["captured_at"])
+
+
+def _convention_fetches(f, leg: str, doc_id: str, url: str, decl, params: dict,
+                        admitted) -> list:
+    """The discoverability candidate's convention locations (`RULE-A13-v1`), collected on A2
+    because A13 reads only the legs it consumes and A2 is the API leg among them.
+
+    For the product page's host and, where the body's recorded API base is `verified`, the API's
+    host: RFC 9727's `/.well-known/api-catalog` (§2), and `/data.json` at the API host's root
+    (OMB M-13-13; the product host's own `/data.json` is D4's fetch already, `d4_catalog.paths`,
+    and is not asked for twice). Through the same gate every collector uses, robots-first.
+    `ADDENDUM_01` A: "for each roster host and each verified API host"."""
+    from .manners import on_roster_host
+    conv = params["discoverability"]["convention"]
+    roots = ["{0.scheme}://{0.netloc}".format(urllib.parse.urlsplit(url))]
+    api = (decl or {}).get("api_base") or {}
+    if api.get("url") and api.get("status") == "verified":
+        api_root = "{0.scheme}://{0.netloc}".format(urllib.parse.urlsplit(api["url"]))
+        if api_root.lower() != roots[0].lower():
+            roots.append(api_root)
+    out = []
+    for i, root in enumerate(roots):
+        of = "product_host" if i == 0 else "api_host"
+        wanted = [(root + conv["api_catalog_path"], "api_catalog")]
+        if of == "api_host":
+            wanted.append((root + conv["inventory_path"], "convention_inventory"))
+        for u, probe in wanted:
+            if not on_roster_host(u, url, params, admitted):
+                continue
+            for o in http.fetch(f, leg, doc_id, u, params):
+                o.parsed = dict(o.parsed or {}, probe=probe, convention_of=of)
+                out.append(o)
+    return out
+
+
+def _terms_text(body: bytes, params: dict) -> dict:
+    """The terms page as D1 stores it: the WHOLE body, decoded, up to the declared ceiling
+    (`d1_sources.terms_text_max_bytes`; `ADDENDUM_01` A, "a truncated read is never judged").
+    A page over the ceiling keeps its first `ceiling` bytes and says so, and `RULE-D1-v6`'s
+    truncated-read branch makes that `error` ("read to N of its M bytes", N the ceiling). The
+    body is stored as served, not as visible text: the rule reads visible text and the
+    `license` links from it itself, and decides truncation by comparing what is kept with the
+    bytes served, so a pre-stripped text would read as truncated on every page."""
+    cap = int(params["d1_sources"]["terms_text_max_bytes"])
+    over = len(body) > cap
+    return {"terms_text": (body[:cap] if over else body).decode("utf-8", "replace"),
+            "terms_text_ceiling": cap, "terms_text_truncated": over}
+
+
 def _declared_api_urls(decl, already: list) -> list:
     """The declared API base and its description, where declared and not already probed."""
     api = (decl or {}).get("api_base") or {}
@@ -71,6 +152,13 @@ def collect_leg(spec: dict, target: dict, params: dict, fetcher=None) -> list:
     declared = declarations.record(decl, body, leg, params)
 
     lp = params["link_probe"]
+    if leg == lp["shared_leg"] and target.get("stored_page") is not None:
+        # Read, never re-fetched (`ADDENDUM_01` A; base decision 4): the product page this
+        # surface's link probe recorded in a stored cycle, as THIS cycle's page Observation with
+        # THIS cycle's `declared` block. No link is probed: only `RULE-A13-v1` reads this leg in
+        # such a cycle, and it reads the page alone (`CONSUMES_PAGE_ONLY`).
+        return _with_declared([stored_page(target["stored_page"], leg, doc_id, url, params)],
+                              declared)
     if leg == lp["shared_leg"]:
         # The product page and every download link on it, observed ONCE per surface. A1 and A3
         # ask different questions of the same 25 objects; before this leg existed each HEADed
@@ -109,6 +197,7 @@ def collect_leg(spec: dict, target: dict, params: dict, fetcher=None) -> list:
                 o.parsed = dict(o.parsed or {}, api=v2clauses.api_declarations(
                     _body(o), (o.response or {}).get("headers") or {}, params))
             out += obs
+        out += _convention_fetches(f, leg, doc_id, url, decl, params, admitted)
         return _with_declared(out, declared)
     if leg == "A12":
         # The two layers, observed against the SAME path so the comparison is real. A12 judges
@@ -213,8 +302,7 @@ def collect_leg(spec: dict, target: dict, params: dict, fetcher=None) -> list:
                     :int(params["d1_sources"]["max_terms_probed"])]:
                 t = http.fetch(f, leg, doc_id, join(p), params)
                 for o in t:
-                    o.parsed = dict(o.parsed or {}, probe="terms",
-                                    terms_text=_body(o).decode("utf-8", "replace")[:20000])
+                    o.parsed = dict(o.parsed or {}, probe="terms", **_terms_text(_body(o), params))
                 obs += t
                 # `.get("status", 999)` here is the same bug the four v3 rules exist for, and
                 # it survived the rule fix because it lives in the COLLECTOR layer: it crashed
@@ -232,8 +320,7 @@ def collect_leg(spec: dict, target: dict, params: dict, fetcher=None) -> list:
                     and on_roster_host(terms, url, params, admitted):
                 t = http.fetch(f, leg, doc_id, terms, params)
                 for o in t:
-                    o.parsed = dict(o.parsed or {}, probe="terms",
-                                    terms_text=_body(o).decode("utf-8", "replace")[:20000])
+                    o.parsed = dict(o.parsed or {}, probe="terms", **_terms_text(_body(o), params))
                 obs += t
         return _with_declared(obs, declared)
     if leg == "D4":
```
