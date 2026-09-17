# RESULT: 12 of the 20 unassigned indicators got a tier; the other 8 got a source-shaped reason they cannot have one

**Task:** `cc_tasks/2026-09-17_unassigned_indicators.md`. I globbed `2026-09-17_unassigned_indicators_ADDENDUM*.md` before starting and again before §3. Neither glob found an addendum.
**Session:** launched headless by the standing dispatcher from HEAD `11f2222`.
**Framework layer served:** DN-005 §2.2 (measurement capability tiered three ways).
**Spend:** zero model calls. **Network:** none beyond `git push`.
**Gate:** green, with every command run to its `EXIT=` line before this file was written.
- `make gate-full` (the full tier, `-rs`): **2347 passed, 3 skipped, 12 xfailed, 0 deselected**, `EXIT=0`, wall-clock 1426.96 s.
- `seldon verify`: all checks passed, `EXIT=0`.
- `scripts/check_protected_unassigned_tiers.sh`: `PROTECTED PATHS OK`, `EXIT=0`.
The log paths are in §4.

**In one paragraph.** The 20 rows the predecessor left unassigned were put to decisions 1 to 5. **12 took a tier**: 4 D (the definition names an act before publication or a tracked internal metric), 7 M (a corpus document names the structured field and a collector already fetches the surface carrying it), 1 O (AIDRIN's documentation is on disk after all). **8 stayed unassigned**, each with the test that failed and what would settle it; 3 of those carry `open_tool_candidate`, the shopping list for a later ingest task. Record totals moved from 27 M / 1 O / 1 D / 20 unassigned to **34 M / 2 O / 5 D / 8 unassigned**. The one substantive departure from the task file: decision 2 asked for basis `harness_leg`, three gates outside the tiering layer caught that the value means "a rule in `rules.CURRENT` serves it", and the seven rows carry the sixth basis `structured_field` instead (DN-005 ADDENDUM_02). No gate was moved.

## 0. The 20 rows

`—` in the tier column is a row still unassigned; its reason is the cell beside it, abridged here and carried in full on the node.

| code | tier | basis | source, or the reason it has none | `open_tool_candidate` |
|---|---|---|---|---|
| **E2** | D | declaration | decision 1: "pre-registered before results" — a threshold is pre-registered only if it existed before the results it judges, and the agency's timestamps are the only record of that order | — |
| **E7** | D | declaration | decision 1: "mean-time-to-closure tracked" — measured over the agency's own ticket history, which no served surface carries | — |
| **F1** | D | declaration | decision 1: "before going live" — whether a release passed the suite happened on the agency's side and leaves nothing on the surface | — |
| **F5** | D | declaration | decision 1: "AI-consumer regression run before promotion" — only the agency can say that it ran | — |
| **B1** | M | structured_field | decision 2: schema.org `variableMeasured` (`corpus/kernel/schema-org-dataset.md`) and DCAT-US `describedBy` (`corpus/kernel/dcat-us-1-1-schema.md`), read by `structured_data.fetch` / `dcat.fetch_catalog` | — |
| **B2** | M | structured_field | decision 2: schema.org `DefinedTerm` with `termCode`, `inDefinedTermSet`, `description` (`corpus/kernel/schema-org-definedterm.md`), read by `structured_data.fetch` | — |
| **B4** | M | structured_field | decision 2: DCAT-US 3 `hasQualityMeasurement` and `versionNotes` / `previousVersion` (`corpus/kernel/dcat-us-3-dataset-schema.md`), read by `dcat.fetch_catalog` | — |
| **B5** | M | structured_field | decision 2: schema.org `DefinedTerm.termCode` within `inDefinedTermSet` (`corpus/kernel/schema-org-definedterm.md`), read by `structured_data.fetch` | — |
| **D2** | M | structured_field | decision 2: the `Content-Signal` directive in robots.txt, categories `ai-train` and `ai-input` (`corpus/kernel/cloudflare-content-signals-policy.md`), read by `robots.fetch` | — |
| **D3** | M | structured_field | decision 2: DCAT-US 3 `wasGeneratedBy` / `qualifiedAttribution` and DCAT-3 `prov:wasGeneratedBy` / `prov:wasDerivedFrom`, read by `dcat.fetch_catalog` and `structured_data.fetch` | — |
| **G4** | M | structured_field | decision 2: DCAT-US 1.1 `bureauCode` and `programCode` (`corpus/kernel/dcat-us-1-1-schema.md`), read by `dcat.fetch_catalog` | — |
| **C5** | O | open_tool | decision 3: AIDRIN's documentation IS on disk — `aidrin-hiniduma-2024` reference [1], "AIDRIn: AI Data Readiness Inspector. test.pypi.org/project/aidrin/0.5.4" | — |
| A7 | — | — | decision 3: the Wayback CDX API's documentation is not in the corpus. Reason kept verbatim from the predecessor | Wayback CDX API (ResearchTask 43108db6) — documentation not in corpus |
| F2 | — | — | decision 3: `oasdiff`'s documentation is not in the corpus. Reason kept verbatim | oasdiff — documentation not in corpus |
| F3 | — | — | decision 3: the Wayback CDX API's documentation is not in the corpus. Reason kept verbatim | Wayback CDX API (ResearchTask 43108db6) — documentation not in corpus |
| B6 | — | — | decision 4: the G1 precedent does NOT carry it. G1's act is a preservation score of a restatement; B6 asks whether the summary is plain language (readability of the text) and current (freshness against the product's `modified`). Different instrument | — |
| E1 | — | — | decision 1 fails: the act the definition names is "reported separately from", a publication act, and the ordering constraint is checkable from the two reports the first clause requires. What is missing is an instrument that reads a published report | — |
| E3 | — | — | decision 1 fails: both clauses are properties of published artifacts. Its observability is **one-sided** — a results table citing no instrument version fails visibly, a pass cannot be confirmed without the agency's records — and one-sided observability is not one of the three tiers | — |
| G3 | — | — | decision 5: a corpus document names the artifact (SDMX 3.0 §1 Structure Map and representation maps) and **no collector reads SDMX**, so decision 2's second half fails. Candidate: M once an SDMX collector exists | — |
| G5 | — | — | decision 2: **no admitted document names a machine-readable suppression or disclosure field.** The failed search is in §2. Its own source asks for "plain language with unique identifiers", which is the prose the indicator says it strengthens | — |

**How decision 1 was read, since four rows passed it and two did not.** The test applied: the definition must carry a clause naming an act that is *temporally before publication* (pre-registration, before going live, before promotion) or *locationally inside the agency's records* (a tracked internal metric). Those are the three forms decision 1's own parenthesis names. E1 and E3 have neither; their acts are publication acts and their artifacts are published artifacts, so they stay unassigned rather than take D by resemblance. The operator can overturn this reading; it is a naming decision, not a value one.

**How B5 came to be tiered when decision 5 left it undetermined.** Decision 5 says B5 stays undetermined "unless a definition clause or corpus document settles it". `corpus/kernel/schema-org-definedterm.md` names `termCode` ("A code that identifies this DefinedTerm within a DefinedTermSet") and `inDefinedTermSet` — the identifier and the concept the definition compares — and `structured_data` already fetches and retains the JSON-LD that carries them. That is decision 2's test, passed. What B5 would still be the first rule to do is compare two collected surfaces rather than judge one; the cross-product half is decidable inside a single cycle and the cross-vintage half across two cycles on the log. The node's `tier_note` says so.

**Why B1 and B2 are M and not O, though the task file grouped them under decision 3.** `extruct`'s documentation is on disk (`corpus/kernel/extruct-readme.md`), so decision 3's on-disk test passes. But DN-005 §2.2 defines tier O by what does *not* exist for it: "a harness path that runs them under the same manners, evidence retention and re-derivation discipline". `extruct` has one — it is the `structured_data` collector's own library, and A6 and A8 are M through it. Tiering B1 and B2 O would have put the same tool on two tiers in one record. C5 stays O because AIDRIN has no harness path at all, which is the distinction doing its work rather than a rule about library ownership.

## 1. Counts, before and after

| tier | before | after | | basis | before | after |
|---|---|---|---|---|---|---|
| M | 27 | **34** | | harness_leg | 17 | 17 |
| O | 1 | **2** | | structured_field | — | **7** |
| D | 1 | **5** | | judged_reading | 2 | 2 |
| unassigned | 20 | **8** | | evaluation | 8 | 8 |
| **total** | **49** | **49** | | open_tool | 1 | **2** |
| | | | | declaration | 1 | **5** |

- **Sources that are `estimate`: 0**, as before. Every assignment rests on a locator into a document admitted in `corpus/manifest.json`, or on a verbatim quote of the indicator's own definition. The tagger checks each quote as a substring of the definition before writing, and two new tests check each cited `doc_id` against the corpus ledger: it must be an `included` entry whose `canonical_path` is the path the source prints.
- **Live Cypher after projection** (`logs/unassigned_cypher.log`):
  - `D declaration 5 [E2 E4 E7 F1 F5]`
  - `M evaluation 8 [C1 C2 C3 C4 E6 E8 E9 G2]`
  - `M harness_leg 17 [A1 A10 A11 A12 A2 A3 A4 A5 A6 A8 A9 B3 D1 D4 E5 F4 G1-D]`
  - `M judged_reading 2 [G1-O G6]`
  - `M structured_field 7 [B1 B2 B4 B5 D2 D3 G4]`
  - `O open_tool 2 [C5 F6]`
  - `— — 8 [A7 B6 E1 E3 F2 F3 G3 G5]`
  - `harness_leg without an action: []` — the prescription layer's invariant, still true.
  `tests/test_measurement_tiers.py` asserts the same distribution as a literal against the record and against the graph.

## 2. The tools whose documentation is not on disk

Decision 3 asked for this as one list. Checked by grep over `corpus/` (`*.md`, `*.html`, `*.txt`) and against `corpus/manifest.json`:

| tool | indicator it would serve | on disk? |
|---|---|---|
| `extruct` | B1, B2 | **yes** — `corpus/kernel/extruct-readme.md`, `included`. Tiered M, not O; see §0 |
| AIDRIN | C5 | **yes** — `corpus/pilot/aidrin-hiniduma-2024.pdf` and `corpus/bulk/aidrin-2-0-...pdf`, both `included`. Reference [1] gives the locator |
| `oasdiff` | F2 | **no** — zero hits in `corpus/`; not in the manifest |
| Wayback CDX API | A7, F3 | **no** — the only `cdx` hit in `corpus/` is a scan evidence page, and the only `web.archive.org` hit is a citation link inside the SLSA specification |

Two further searches that failed, recorded because "no source names it" is a claim and not a default:

- **A machine-readable suppression or disclosure field (G5).** `suppress`, `confidential`, `disclosure` across `corpus/kernel`, `corpus/crosswalk` and `corpus/components`: one hit, `bing-webmaster-guidelines`, on search-result suppression. Nothing in the SDMX 3.0 §1 framework or the DDI codebook. `w3c-rdf-data-cube`'s `qb:AttributeProperty` carries observation status ("estimated, provisional") generically and names no suppression field.
- **A version field for a `DefinedTerm` or `DefinedTermSet` (B2's third clause), and a field for a statutory mandate or the statistical-versus-administrative distinction (G4's second and third clauses).** Searched `schema-org-definedterm`, `schema-org-dataset`, `w3c-dcat-3`, `dcat-us-3-dataset-schema`, `dcat-us-1-1-schema`, `ddi-codebook-specification`. None names one. Each node's `tier_note` says which clause a rule would have to record as unmeasured.

**A third finding, on the record rather than in the corpus.** `ind:D3`'s `gap` cell says "**gap** — no PROV-O/W3C-PROV document is admitted; the skeleton's 'PROV-aligned standards nodes' did not resolve". That is stale: `w3c-prov-o-ontology` and `w3c-prov-dm-data-model` are both `included` and `verified` in `corpus/manifest.json`, at `corpus/crosswalk/`. The cell belongs to the evidence layer and is not this task's to write, so it is left as it stands and reported here; D3's `tier_note` also carries it.

## 3. Premises this task file got wrong

1. **Decision 2: "Assign M, basis `harness_leg`".** `harness_leg` is defined by DN-005 ADDENDUM_01 §2 as "a rule in `rules.CURRENT` serves the indicator", and three things outside the tiering layer depend on it meaning exactly that: `scripts/tag_prescriptions.py::validate` (which refuses to write unless `OUTCOMES` covers exactly the record's `harness_leg` set), `tests/test_prescriptions.py` (two tests, one on the record and one by Cypher), and `scripts/load_framework_graph.py`'s `harness_leg_indicators_without_an_action` count. The first write used `harness_leg` as asked and all three failed — correctly, because decision 2's own mandated `tier_note` ("no rule in rules.CURRENT yet") says in prose what the field would have said falsely in data. **No gate was moved.** The seven rows were re-based to a sixth value, `structured_field`, recorded in `docs/design/2026-09-15_DN-005_reorientation_the_framework_is_the_goal_ADDENDUM_02.md`, and `tests/test_measurement_tiers.py::test_the_basis_that_means_a_rule_is_only_ever_a_rule` now holds the boundary in both directions. The framework shard therefore carries **two** write-back events from this task, the second correcting the first, because a correction is a new event and never an edit.
2. **§0's grouping "O for B2, C5, F2, F3, and A7 or B1".** B1 and B2 are M, for the reason in §0: `extruct` is the `structured_data` collector's own library, so DN-005 §2.2's O ("what does not exist: a harness path") does not hold for it.
3. **§0's "M judged reading for B6".** Decision 4's own test refuses it: G1's act is a preservation score of a restatement, and B6's two clauses are properties of the surface. B6 is unassigned.
4. **§0's "D for E1, E2, E3, E7, F1, F5".** Four of the six pass decision 1. E1 and E3 do not; see §0.
5. **§0's "undetermined for B5 and G3".** B5 is settled by a corpus document (§0). G3 is not, and its reason now names the SDMX artifact and the collector that does not exist, which is more than "undetermined".
6. **Decision 3's premise that AIDRIN's papers do not say where the tool is obtained** (inherited from the predecessor's reason text). Reference [1] of `aidrin-hiniduma-2024` gives `test.pypi.org/project/aidrin/0.5.4`, and the body says "Users can install the AIDRIN PyPI package via the command line". The index named is TestPyPI and not the production index; the node's `tier_note` says so rather than smoothing it.
7. **The write set omits `scripts/scan_tool_map.py`.** Decision 2 puts the field and the collector on the node, and the generated §2 row then printed "no collector reaches this yet" beside a source naming one — two cells of one row in contradiction. `verdict_for` gained one branch: where the node carries `tier_collector`, the row says "no rule in rules.CURRENT yet; `<entry points>` would read `<field>`". Pure insertion, nine lines, no line removed; `scripts/check_protected_unassigned_tiers.sh` asserts both.
8. **Decision 6's "the site payloads the predecessor named".** The predecessor named three (`sources_per_check`, `framework_copy`, `data_manifest`) plus the citation files. Only two moved: `docs/data/ai_readiness_framework.json` and `docs/data/index.json`. `sources_per_check.json` did not, because its only tier-derived cell is G1-D's `measurement_level` and no decision here touches it; the citation files did not, because their date is already today's. The build was run with all three `--only` flags anyway, so the absence is a fact about the payloads and not about what was rebuilt.

## 4. Gate

**Tier:** `make gate-full` (the whole suite, `-rs`, detached and polled to its `EXIT=` line inside this turn). Not the fast tier. The task touched no rule module, the registry or the re-derivation engine, so `gate-task` adds nothing beyond the full run, which includes it.

| check | result | log |
|---|---|---|
| `make gate-full` | **2347 passed, 3 skipped, 12 xfailed, 0 deselected**, 248 warnings, 1426.96 s, `EXIT=0` | `logs/suite.log` |
| skips | `tests/test_dispatch_config.py:333` (interactive_only: this is a dispatched session, which holds its own claim and dirties the tree); `tests/test_scan_harness.py:281` (E5 judges the cycle's controls, not a surface); `assessment/tests/test_g1_preservation.py:337` (no dev proposition publishes SE and CI together) | `logs/suite.log` |
| `seldon verify` | all checks passed (34856+ events readable; replay skipped as expensive, per its own default), `EXIT=0` | `logs/unassigned_seldon_verify.log` |
| protected paths | `PROTECTED PATHS OK`, `EXIT=0` (`scripts/check_protected_unassigned_tiers.sh`) | `logs/unassigned_protected.log` |
| framework projection | `scripts/load_framework_graph.py`, `EXIT=0`, `harness_leg_indicators_without_an_action: []`; the round-trip gate is green inside the suite | `logs/unassigned_projection.log` |
| tier Cypher | §1 | `logs/unassigned_cypher.log` |
| site payloads | `build_l0_site.py --only sources_per_check --only framework_copy --only data_manifest`, `EXIT=0` | `logs/unassigned_site.log` |
| tagger | idempotent: a second run returns `unchanged: true`, `nodes_changed: 0`. `scripts/build_framework_graph.py --dry-run` over the new record is still a byte-for-byte no-op | `logs/unassigned_tagger.log` |

**An earlier `make gate-full` on the same working tree failed** (3 failed, 2343 passed, 1460.31 s) on the three prescription-layer gates in §3 premise 1. Nothing was shipped from it; the basis was corrected and the whole suite re-run from scratch. The failing run is reported here rather than overwritten, because a gate that failed and was then made to pass by changing the work is the only kind of pass this record can carry.

**The record**, written through `framework_writeback.save`, the single writer:

| event | time | nodes changed | framework sha256 |
|---|---|---|---|
| `ce28d528f05d439896508961e7a98c9a` | 2026-09-17T21:21:57Z | 20 | `745ea090…f05b35` |
| `e16f565299d5463b96df7af866616748` | 2026-09-17T21:50:41Z | 7 | `595d86e2…6bc83e` |

Both on `events/batch-033_framework.jsonl`. No node, edge or `counts` key was added or dropped by either.

**Write set as committed:**
- the record: `framework/ai_readiness_framework.json`, plus the two events above;
- code: `scripts/tag_measurement_tiers.py` (decisions 1 to 5 as `TABLE2`, `UNASSIGNED2`, `OPEN_TOOL_CANDIDATE`), `scripts/scan_tool_map.py` (§3 premise 7);
- checks: `scripts/check_protected_unassigned_tiers.sh` (new);
- tests: `tests/test_measurement_tiers.py` (new literals and five new gates);
- the DN-005 addendum: `docs/design/2026-09-15_DN-005_reorientation_the_framework_is_the_goal_ADDENDUM_02.md` (new);
- regenerated and published: `docs/design/scan_tool_map.md`, `docs/data/ai_readiness_framework.json`, `docs/data/index.json`;
- `seldon_events.jsonl`;
- this RESULT.

Nothing under `state/`, `corpus/`, `kg/`, `assessment/`, `docs/reports/` or `docs/research/` moved. No cycle ran, no Result was registered, no matrix, figure or report was rebuilt.

## 5. What the next task starts from

The 8 rows still unassigned split three ways, and each way is a different next task:

1. **An ingest task** — three tool documents the corpus does not hold: `oasdiff` (F2), the Wayback CDX API (A7, F3). That closes the `open_tool_candidate` list and would tier three rows O.
2. **A collector task** — SDMX. G3's crosswalk artifact is specified in an admitted document and nothing reads it. B6's "current" half and A7's declared-identifier half (schema.org `identifier` carrying a DOI, via `structured_data`) are the same shape of work and were deliberately not assigned here, because decision 3 governs A7 and decision 4 governs B6.
3. **Two rows that may have no tier at all.** E1 and E3 both turn on reading a *published report* rather than a served data surface, and E3's observability is one-sided. Whether the three tiers need a fourth kind — or whether report-reading is simply a `judged_reading` no instrument exists for — is the question those two rows pose, and it is a naming decision for the operator rather than a search result.

The seven `structured_field` rows are the other open thread: each names a field and a collector and lacks only a rule. They are the natural input to the next harness task, and the prescription layer will pick them up automatically once a rule moves one to `harness_leg`, because its join is on the basis and not on a hand-kept list.
