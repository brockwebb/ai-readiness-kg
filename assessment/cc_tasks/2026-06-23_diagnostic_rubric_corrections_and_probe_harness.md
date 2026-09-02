# CC Task — FSS AI Data Readiness Diagnostic: rubric corrections + probe harness

**Date:** 2026-06-23
**Type:** Build (correct existing design docs, then implement probe harness)
**Author:** Brock (via Desktop design session)
**Status:** ready, BUT Stage 3 (probe impl) BLOCKS on the definition task (51fe4574) landing — see Dependencies
**Project dir:** `/Users/brock/GitHub/brock_projects/ai-readiness-fss`

---

## Dependencies (read before starting)

- **Definition task 51fe4574** targets a DIFFERENT repo: `/Users/brock/Documents/GitHub/icsp_notebook`. It produces the adopted AI-data-readiness definition: **Part A** (content-side, adoptable core) and **Part B** (dated access-axis addendum — WebMCP/MCP/llms.txt as forward interpretation). The core/frontier split in this task IS that Part A / Part B boundary. Do NOT re-derive it. At Stage 3, READ the committed definition output from icsp_notebook and make the probe's core-vs-frontier classification trace to it explicitly. If 51fe4574 has not landed, STOP at end of Stage 2 and report — do not guess the boundary.
- Stages 1–2 (doc corrections) have NO dependency and run now.

## Why this task exists

Three design docs live in repo root: `benchmark_rubric.md`, `covariate_clustering_schema.md`, and `notes/` (three memos). A Desktop session settled decisions that make parts of those docs stale or contradictory. This task (a) corrects them, (b) reconciles a framing collision between the rubric and the covariate schema, then (c) implements the probe harness. Do them IN ORDER; later stages depend on earlier ones being correct.

Standing principles (do not violate, do not re-litigate):
- **No PMT (performative metric theater).** No self-attested fields anywhere in the scored instrument. If a human types it, it is not a benchmark input.
- **Diagnostic in purpose, measurement in mechanism.** Scores aggregate into a system picture, read within peer cohort. Anti-gaming comes from reality-based probing, not surveillance.
- **Evidence-emitting.** Every probe emits the actual HTTP response / artifact retrieved. A score is auditable, never asserted.
- **Pass/partial/fail only** (2/1/0). No maturity tiers, no 1–5 stars. Goodhart bait.

---

## STAGE 1 — Rubric corrections (`benchmark_rubric.md`)

### 1A. Replace the can't-vs-hasn't gate with a clean SCOPE BOUNDARY

Current rubric treats legally-restricted data via a \"can't-vs-hasn't gate\" that flags LAWFULLY NON-EXPOSED targets. **Wrong register.** Replace with a scope statement:

> **The measurement universe is public and public-mandated data assets ONLY.** Protected data (Title 13 microdata, Title 26, CIPSEA-restricted, PII) is OUT OF SCOPE — not flagged, not stratified, not scored. The instrument measures one thing: is data that is *already public or mandated-public* exposed in AI-ready ways? It has NOTHING to do with access to protected data. Nobody is being asked to expose protected data; the question is whether the data an agency *already publishes* is published so a machine can actually use it.

Preserve the rationale in-doc: this preempts the \"you're penalizing us for protecting data\" attack entirely — protected data never enters the frame, so there is nothing to argue about. Cleaner and more defensible than stratifying legal constraint.

Keep restriction-discoverability ONLY in this narrow form: if a public catalog *points at* a dataset that is access-restricted, a machine should be able to learn *that it is restricted and why* (machine-readable access-tier metadata). That is an interpretability property of the public catalog — fold into D3, do NOT keep as a top-level gate.

### 1B. Split the frontier track into maturity tiers (llms.txt is NOT WebMCP)

Current \"core vs frontier\" edit lumps `llms.txt` and `MCP/WebMCP` together. Too coarse:
- **llms.txt** — low-effort, already-circulating convention, achievable TODAY. Failing it is \"hasn't bothered,\" not \"ahead of the standard.\" Tier: **frontier_near** (readily-achievable forward-lean).
- **WebMCP** — standardized ~2026-Q1, ~3 months before this assessment. Failing it is \"the standard barely existed.\" Tier: **frontier_deep** (presence visionary; absence explicitly NOT core unreadiness).

Restructure so \"has llms.txt but not WebMCP\" is distinguishable from \"has neither\" — partial forward-lean is informative signal. Add an explicit `as_of_date` (standardization date) field per frontier probe so the dating convention lives in the data, not just prose.

Update rubric Open Items: mark 1A, 1B resolved; leave probe-impl + target-list open (closed in Stage 3).

---

## STAGE 2 — Covariate schema reconciliation (`covariate_clustering_schema.md`)

The 1A scope reframe collides with this doc. Reconcile, do not ignore.

Current: **C1 (legal constraint regime)** is the *\"dominant variable\"* that *\"drives the can't-vs-hasn't gate\"* and *\"explains a low benchmark score entirely.\"* After 1A that framing is dead — there are no low scores on out-of-scope protected data because protected data is not measured. Reconcile:
- C1 no longer \"explains low scores\" (those scores don't exist).
- C1 still matters for **cohorting only**: an agency with a large restricted portfolio has a *smaller public surface to measure* — relevant to WHO ITS PEERS ARE, not to excusing a score. Demote C1 to \"a cohorting axis: public-surface size / mandate breadth.\"
- Remove all can't-vs-hasn't references; point to the scope boundary instead.
- Keep C2/C3/C4 as-is (C4 still flagged collinear-verify).
- Do NOT silently delete C1 — rewrite its role with a design-history note explaining the change.

---

## STAGE 3 — Probe harness (BLOCKS on 51fe4574; see Dependencies)

Start only if the definition task has landed AND you have read its Part A/Part B output. Else STOP, report.

Python probe harness. Constraints:
- One module per probe. Each returns `{score: 2|1|0, evidence: <raw artifact>, probe_id, target, timestamp, track: \"core\"|\"frontier_near\"|\"frontier_deep\", as_of_date}`.
- Reproducible by anyone with a browser + Python — public endpoints only, no privileged access, no API keys beyond public. This reproducibility IS the design's source of authority (anyone could run it; we surface what is already publicly observable). Do not add any dependency that breaks \"anyone can re-run this.\"
- Probes implement D1 Discovery, D2 Retrieval, D3 Interpretability, D4 Trust/freshness. Core probes → core score. Access-axis probes (llms.txt → frontier_near; MCP/WebMCP → frontier_deep) → frontier tracks, NEVER the core composite.
- Evidence capture writes the raw response to disk beside the score. A reviewer verifies any score from emitted evidence without re-running.
- Output: per-target JSON record + per-agency rollup (dimension vectors, core composite, frontier tracks separate). Rollup feeds the covariate/clustering layer — do NOT implement clustering here (later task, post-data, per covariate doc sequencing).

### Target enumeration (sub-task)
Build a first-pass enumerator: from each FSS agency's public catalog (data.json / DCAT where present, else the open-data landing page), extract candidate public data-asset endpoints. Mechanical. Flag any agency with no machine-readable catalog (itself a D1 finding — record, don't error out).

### Inventory-as-pointer constraint (HARD)
M-25-21 AI use-case inventories are SELF-REPORTED, inflation-prone. If internal-readiness signals enter anywhere, the inventory is a **pointer (where to look), NEVER a scored metric.** Compute NO score from inventory contents. A thin inventory is a lead, not a measure (under-use OR under-reporting OR conservative definition — the probe can't distinguish). Out of scope for the scored harness; note as future internal-assessment input only.

---

## Done criteria
- Stages 1–2: docs corrected, internally consistent, design-history notes preserved, zero surviving can't-vs-hasn't references.
- Stage 3 (if unblocked): harness runs against ≥1 real FSS agency public catalog end-to-end, emits scored records + evidence files + rollup, core and frontier tracks separated, traceable to the 51fe4574 definition boundary.
- Append a `## DONE` block to THIS file on completion (do not create a separate result file). Use `_RESULT`/`_BLOCKED` suffix sections if Stage 3 blocks.

---

## DONE — 2026-06-23

All three stages complete. Dependency **51fe4574 had landed** (icsp_notebook commit `eb425a9`), so Stage 3 was unblocked and executed.

### Stage 1 — `benchmark_rubric.md` corrected
- **1A scope boundary:** replaced the can't-vs-hasn't gate with the public/public-mandated-only scope statement. Protected data is out of scope — never flagged/stratified/scored. Design-history note preserved (gate retired, not silently deleted). Restriction-discoverability narrowed and folded into D3 as a machine-readable **access-tier metadata** probe.
- **1B frontier tiers:** split frontier into `frontier_near` (llms.txt, as_of 2024-09) vs `frontier_deep` (MCP/WebMCP, as_of 2026-01); per-probe `as_of_date`; "llms.txt but not WebMCP" is a distinct, informative state. Firewall restated as *established mechanism = core* vs *emerging-standard access mechanism = frontier* (NOT "D1/D2 = frontier"), traced explicitly to 51fe4574 Part A/Part B. Moved `llms.txt` out of D1 and `MCP/WebMCP` out of D2 into a dedicated Frontier access track section. Disambiguated the anti-PMT "no tiers" exclusion (dating buckets ≠ maturity grades). Open Items updated (1A/1B resolved; probe-impl + target-list now point to this task).

### Stage 2 — `covariate_clustering_schema.md` reconciled
- C1 demoted from *"dominant variable / drives the can't-vs-hasn't gate / explains a low score entirely"* to a **pure cohorting axis: public-surface size / mandate breadth**. Rewritten with a design-history note (not deleted). C2/C3/C4 kept as-is (C4 still flagged collinear-verify). Zero surviving can't-vs-hasn't references except the two intentional design-history notes explaining the retirement.

### Stage 3 — probe harness (unblocked; runs end-to-end)
- Zero-runtime-dependency Python harness (stdlib `urllib`/`json`/`xml`/`tomllib`); pytest dev-only. Reproducibility preserved per constraint.
- **18 probe modules, one per probe** (`harness/probes/`): D1×4, D2×4, D3×4, D4×4, frontier×2. Each separates `fetch` (I/O) from `evaluate` (pure) → testable from fixtures.
- Each record emits `{probe_id, target, dimension, track, score(2|1|0), as_of_date, evidence, timestamp, evidence_path}`. Raw artifact written to disk beside each score (auditable, not asserted).
- **Core-vs-frontier firewall traced to 51fe4574** and enforced structurally in `rollup.py` (frontier partitioned out before the composite is summed — verified by `test_frontier_pass_does_not_change_core_composite`). Per-agency rollup = core dimension vectors `[D1,D2,D3,D4]` + core composite + the two frontier tracks reported **separately**.
- Target enumerator parses Project Open Data / DCAT `data.json`; no machine-readable catalog = recorded D1 finding, not an error.
- **Inventory-as-pointer HARD constraint** honored: no inventory probe/module/field/score anywhere. Documented in `notes/inventory_as_pointer_constraint.md` as future internal-assessment input only.
- All tunables in `config/*.toml` (no hardcoding). Config fails loud on missing keys (§4).

### Verification (evidence, not assertion)
- `python -m pytest tests/` → **86 passed**.
- Real end-to-end run: `python -m harness.run --agency census --agency bea --max-datasets 3 --max-dists-per-dataset 1`
  - **census**: catalog yes (1789 datasets enumerated, 3 probed), core composite **63/84**, frontier_near 0/2, frontier_deep 0/2; 44 records + 44 evidence files.
  - **bea**: catalog yes (26 datasets, 3 probed), core composite **51/84**, frontier 0/0.
  - **bls**: catalog endpoint returns 403 to our UA → that *is* the recorded D1 finding (the harness keeps going).
- Bug found + fixed via the live run (TDD regression test added): a 2 MB body cap truncated Census's ~2 MB `data.json` mid-JSON, producing a **false** "no machine-readable catalog" D1 finding. Body cap is now configurable (default 50 MB) and separated from a per-file evidence-write cap.

### Notes / follow-ons (not blockers)
- `results/` and `evidence/` are gitignored (regenerable).
- Probe `evaluate` heuristics are first-pass and intentionally conservative (e.g., `d4_integrity` PASS requires a real checksum; most federal catalogs will score PARTIAL/FAIL — honest signal). A deeper D3 pass could fetch and lint the `describedBy` schema contents (currently scores schema *presence/machine-readability*).
- Agency list seeded with census/bls/bea; expand `config/agencies.toml` as the target list is validated.
