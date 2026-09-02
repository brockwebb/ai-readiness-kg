# Covariate Schema & Peer-Cohort Clustering — FSS AI Data Readiness
*The fairness layer. Stratify to be fair, not lenient.*

## Why this exists
A flat FSS-wide score is itself theater — it pretends a 50-person agency under Title 13 and a large multi-program agency with a public mandate are playing the same game. Covariates contextualize the benchmark score and define **peer cohorts** so agencies are compared within-group. They do **not** adjust or excuse scores. Bottom of your own cohort = excuses spent.

## Covariates

### C1 — Public-surface size / mandate breadth *(a cohorting axis)*
How much *publicly measurable* data an agency has, given the authorities it operates under. An agency with a large restricted portfolio has a **smaller public surface to measure** — which is relevant to *who its peers are*, not to excusing any score.
- Fields: governing statutes (Title 13, Title 26, CIPSEA, HIPAA, privacy/PII regimes) *as descriptors of public-surface size*, share of holdings that are public/mandated-public vs. restricted, presence of public-release mandate.
- Use: a clustering axis only — group agencies with comparable public surfaces so a small-public-surface agency is benchmarked against peers, not against a large open-data publisher.

**Design-history note:** C1 was originally the *"dominant variable"* that *"drives the can't-vs-hasn't gate"* and *"explains a low benchmark score entirely."* The benchmark's 1A scope reframe killed that role: the measurement universe is now public/public-mandated assets only, so **protected data is never scored** — there are no low scores on out-of-scope data for C1 to explain. C1 is therefore demoted from score-explainer to a pure cohorting axis (public-surface size / mandate breadth). It is rewritten, not deleted: the legal regime still tells you how big an agency's measurable public surface is, which still legitimately shapes peer grouping. See `benchmark_rubric.md` → Scope boundary.

### C2 — Data complexity (the 4 V's)
- **Volume** — scale of holdings.
- **Variety** — structured / semi / unstructured mix; number of distinct product types.
- **Veracity** — known quality/uncertainty burden.
- **Velocity** — update frequency / streaming vs. static.
- Use: high-variety/unstructured estates are genuinely harder to make machine-consumable; sets expectation, not excuse.

### C3 — Capacity (size)
- Fields: staff (total / technical / data-specific), budget proxy, in-house vs. contracted IT.
- Use: capacity proxy; small shops are resource-bound, not necessarily negligent.

### C4 — Institutional age / history *(candidate — verify independence)*
- Fields: founding era, legacy-system footprint, count of legacy data formats.
- **Hypothesis: collinear with C2-variety + C3-size** (old + big = legacy debt). Test before treating as an independent axis. Drop if it doesn't earn a column.

## Method — keep the two jobs separate

### Step 1: Clustering (unsupervised) → peer cohorts
- Input: covariates C1–C4 (NOT the benchmark score).
- Method: hierarchical or k-means; small N (FSS principal agencies ~13, broader ~100+) favors hierarchical for interpretability.
- Output: agency cohorts of genuinely comparable peers.
- Purpose: score the benchmark **within cohort**.

### Step 2: Explanatory model (supervised) → what drives readiness *(optional, AFTER benchmark)*
- Input: covariates as features, **benchmark score as target**.
- Method: decision tree (interpretable) or random forest (importance ranking).
- Output: which covariates actually predict readiness — separates structural constraint from fixable neglect across the system.
- **Sequencing: impossible before the benchmark exists.** Forest comes after, never before. Do not invert.

## Discipline
- Covariates set **expectations within a peer group**; they never adjust the raw benchmark score.
- A lawfully-constrained, small, old agency is benchmarked against *other* lawfully-constrained small old agencies — and still has a floor.
- Stratification is the escape hatch for theater if abused ("we're small/old/Title-13, so our zero is fine"). Resist it.

## Open items
- [ ] Finalize covariate field list + sources (most are public: budget tables, agency org data, statute mapping).
- [ ] Decide cohort granularity (principal statistical agencies vs. full FSS membership).
- [ ] Test C4 collinearity; keep or drop.
- [ ] Clustering scaffold (sklearn) once covariate table is populated.
