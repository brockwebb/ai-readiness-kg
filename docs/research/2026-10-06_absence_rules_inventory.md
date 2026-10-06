# Absence rules inventory: which `fail` verdicts are reached over a partial search

**Date:** 2026-10-06. **Task:** `cc_tasks/2026-10-06_absence_verdicts_rules.md` decision 1, written before any rule or collector changed. **Implements:** DN-012 d1 to d3. **Source of the counts:** `state/scan_2026-09-10_rj4.json` (the cycle of record) and `state/scan_2026-09-10.json` (its Observations), read by script on 2026-10-06.

## 1. The test applied

DN-012 d1 names three ways an absence verdict is reached over a partial search:

1. **Truncated.** The candidate set was cut by a bound, such as `link_probe.max_links_probed` or `d1_sources.max_terms_probed`, or by the collector stopping at the first match.
2. **Never reached the place the indicator names.** The signal says where the object lives, and the collector looked somewhere else.
3. **Declared and not followed.** A documented location exists, and the collector guessed paths instead.

Decision 5 restates these as "bounded, guessed, or undeclared".

**Scope versus predicate.** The test is about scope: where the collector looked. It is not about the predicate that recognises a candidate once the candidate is in hand. Take B3's methodology token. B3 runs it over *every* link on the page, so its "no link" branch is a complete search with an imperfect recogniser. That is a validity question, and this task does not answer it.

**Applied to.** Every rule in `rules.CURRENT` whose `fail` branch asserts that something is not there. Each one is listed below with the collector it reads and the bound or guess that limits its candidate set.

## 2. The rules that ARE absence over a partial search (12 legs)

| leg | current rule (rj4) | rj4 fail | collector, and the bound or guess | trigger | new version |
|---|---|---|---|---|---|
| A1 | `RULE-A1-v4` | 38 | `links.probe` HEADs the first 25 on-host links in document order and `break`s (`params.link_probe.max_links_probed: 25`). The links after the 25th leave no record. On 38 of the 46 product surfaces whose page was served, the page carried 38 to 871 on-host links (`home:www.samhsa.gov` 871, `scan-census-flagship-2-american-community-survey-acs` 115). | 1 | `RULE-A1-v5` |
| A3 | `RULE-A3-v6` | 21 | The same probe and the same cap. | 1 | `RULE-A3-v7` |
| A2 | `RULE-A2-v3` | 40 | `runner.collect_leg` GETs three guessed paths on the surface host (`/openapi.json`, `/swagger.json`, `/api/openapi.json`, from `params.a9_m2m.probes`). spec:A2 says "the documented API base". | 2, 3 | `RULE-A2-v4` |
| D4 | `RULE-D4-v3` | 37 | `dcat.fetch_catalog` reads `<surface host>/data.json` only. ind:D4 says "data.gov/agency inventory". `params.yaml` `dept_domains` records that data.gov reads each department's data.json. | 2 | `RULE-D4-v4` |
| B1 | `RULE-B1-v2` | 37 | The DCAT half reads D4's catalog observation (`CONSUMES = ("D4", "A6")`). Its "no catalog record" branches inherit D4's scope. | 2 | `RULE-B1-v3` |
| B4 | `RULE-B4-v1` | 38 | `CONSUMES = ("D4",)`, the same. | 2 | `RULE-B4-v2` |
| D3 | `RULE-D3-v1` | 38 | `CONSUMES = ("D4",)`, the same. | 2 | `RULE-D3-v2` |
| G4 | `RULE-G4-v1` | 37 | `CONSUMES = ("D4",)`, the same. | 2 | `RULE-G4-v2` |
| A9 | `RULE-A9-v1` | 40 | The same guessed paths, plus `/llms.txt` and `/.well-known/mcp.json`. spec:A9 says "OpenAPI at the documented base". A9 is frontier, so this changes no score. | 2, 3 | `RULE-A9-v2` |
| B3 | `RULE-B3-v3` | 34 | `runner.collect_leg` follows the **first** page link whose href or text carries `methodolog` and `return`s. The "PDF-only", "not retrievable without JS" and "no structured-text methodology reachable" branches judge one document when several matching links can exist. The "no link to a methodology document" branch is a complete search of the page's links and is kept. | 1 | `RULE-B3-v4` |
| D1 | `RULE-D1-v3` | 40 | `runner.collect_leg` probes `d1_sources.terms_paths[:max_terms_probed]`, which is 3 of 7 guessed paths, and stops at the first one served. spec:D1 names "the API's terms endpoint", and the harness never locates it. | 1, 2 | `RULE-D1-v4` |
| F4 | `RULE-F4-v3` | 40 | Five guessed paths (`params.f4_changelog.paths`). spec:F4 says "any changelog or release-notes endpoint". No location is declared or discovered. | 2 | `RULE-F4-v4` |

**The audit named the first four legs** (C-01: A1 and A3; C-04: D4 and its consumers; C-14: A2). **The inventory adds A9, B3, D1 and F4.** Each is treated under decision 5, with a new version and its prior version kept unedited.

**"The five consuming legs" is four.** `CONSUMES = ("D4",)` or `("D4", "A6")` is declared by `RULE-B1-v1`, `RULE-B1-v2`, `RULE-B4-v1`, `RULE-D3-v1` and `RULE-G4-v1`. That is five *modules* but four *legs*, because B1 has two versions. The audit's "5 of 21 scored legs" counts D4 itself with its four consumers. No fifth consuming leg exists.

## 3. Absence rules whose search is complete, kept unchanged

| leg | rule | why the search is complete |
|---|---|---|
| A4 | `RULE-A4-v1` | robots.txt has one location (RFC 9309 §2.3), and it is read. |
| A5 | `RULE-A5-v2` | spec:A5 names `/sitemap.xml`, the path robots.txt declares, `/llms.txt` and `/.well-known/`. Every one is fetched, and a blind candidate already gives `error`. |
| A6 | `RULE-A6-v2` | The markup on the product page. The page is the whole candidate set. |
| A8 | `RULE-A8-v4` | `follow_latest_pointer` tries every pointer found on the page, in order, until one resolves (`v2clauses.py:200`). There is no cap. A blind pointer already gives `error`. |
| A10 | `RULE-A10-v3` | Not an absence claim. It is the server's behaviour on two probes. |
| A11-declared | `RULE-A11-declared-v2` | robots.txt and the page's meta-robots, both read. |
| B2, B5 | `RULE-B2-v1`, `RULE-B5-v1` | The product page's markup, read whole. |
| D2 | `RULE-D2-v1` | The Content-Signal lines in the robots.txt A4 reads. |
| G1-D | `RULE-G1-D-v1` | The structured fields of the surface, read whole. |
| E5 | `RULE-E5-v2` | It judges the cycle's controls, not a product. |
| A12 | `RULE-A12-v3` | Candidate. Host behaviour, not absence. |

## 4. What changes, in one paragraph per decision

- **Collector (DN-012 d2).** Candidates are ranked before the cap. Every on-host candidate past the cap is written as an Observation with `fetched: false` and `error_class: unprobed_over_cap`, which is a new BLIND, unrequested class. The page Observation carries a `link_candidates` block that counts on-host candidates, probed and unprobed. A stored cycle gets the same block from `scan/reread.py`, computed from the page Observation's own `parsed.links`.
- **Declarations (DN-012 d3).** `targets.yaml` gains a `declared_locations` map: per body, `api_base` and `inventory_urls`, each with the page it was read from. Anything not resolvable from this repository is listed under `unresolved`, and the rules name it.
- **Rules (DN-012 d1).** Each `fail` above that asserts absence first checks the candidate set: unprobed links, blind members, declared locations not observed, guessed paths, and capped terms paths. If any of those remain, it returns `error` naming the remainder. Existence verdicts stand unchanged.

## 5. Open after this task

- **F4 and D1 cannot reach `fail` until a location is declared.** F4 needs a changelog URL. D1 needs the API's terms endpoint, and all seven terms paths must be probed. Neither field is in DN-012 d3, and this task does not invent one: their `error` names what would unlock a verdict.
- **A1/A3 `fail` needs the cap to cover the candidates, or a rescan that probes them.** Raising `max_links_probed` is DN-012 §2's open question, owned by the manners layer.
