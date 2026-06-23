# FSS AI Data Readiness — Design Memo
*Sailor's Edition. Working synthesis, not a deliverable.*

## The problem as handed down
OMB wants a measure of "AI data readiness" across the federal statistical system. The term is undefined by the people requiring it, which is the root complaint: you cannot measure what no one will define, and a measure built on an undefined construct degrades into theater.

Two things have to get produced:
1. A **definition** of AI data readiness, scoped to the FSS.
2. A **mechanism** to ascertain it across agencies.

## Governing principle: no PMT
**No Performative Metric Theater.** Every measure must (a) mean something, (b) be cheap to collect, (c) be automated and human-free wherever possible. Anything that exists only to "show progress" is cut. This is the festina-lente / kill-pilot-theater stance pointed at measurement: break performative compliance, protect the things that make the measure credible.

Corollary — **Goodhart is a law, not a mood.** The moment a measure becomes a target it stops measuring. Maturity models self-reported up a chain converge on "everyone's a 3/5." The instrument must make cheating harder than complying. That's engineering, not cynicism.

## The central reframe: test, don't survey
For anything public-facing, **don't ask humans if their data is AI-ready — hit it with AI and find out.** The machine is the instrument. This operationalizes the real thesis: the test of whether the machine is a first-class consumer is whether a machine can actually consume the data. Self-report is the dirty-signal source; a live probe can't be gamed by optimism, only by actually fixing the thing.

## Three instruments, not one
Use the cheapest valid instrument for each layer. Refuse to survey what you can probe.

### 1. Machine benchmark — external / public layer
Point an agent at what each agency actually exposes.
- **Discover**: llms.txt, sitemap, content negotiation.
- **Retrieve**: API, MCP / WebMCP, downloadable structured formats.
- **Use correctly**: structure, metadata, provenance, machine-interpretability at inference time.
Pass/fail per probe, scored by rubric ("AI judge"). Reproducible by anyone with a browser and Python. Zero self-report. This is the part that is *yours* and absent from the current literature — the field still measures fitness-for-training, not machine-as-consumer.

### 2. Thin practitioner instrument — internal layer (the un-probeable residue)
Only for what a crawler physically cannot reach: governance, ownership, access friction, lineage, legal constraint.
- Aimed at **practitioners in the trenches**, collected **direct** — not laundered up the management chain (avoids the iceberg problem, where only safe surface problems survive aggregation).
- **Do not collect one sanitized response per agency.** Many practitioners, no pre-aggregation.
- Framed as **unreadiness / symptoms**, not readiness. People know their pain even when they can't define readiness. "Last time you needed to know what a field meant, how long did it take?" is answerable; "is your data documented?" is abstract.
- Symptom items double as **counter-verification** against the optimism in any positive self-report.
- **Statistical ranges** absorb the residual slop from people inclined to hide problems. That's what ranges are for.
- **Adaptive / role-based branching**, but only where role genuinely changes who can answer accurately (~2–3 tracks, not a decision tree). Executives get scoped to what they control (budget, mandate, prioritization); ground-truth/symptom items go to practitioners. Don't let exec optimism contaminate the diagnostic layer (anti-Gartner: doers hold ground truth, execs report hope).

### 3. Covariates — fairness layer (not scored)
Agencies aren't comparable in the raw. A flat FSS-wide score is itself theater.
- **Legal constraint regime** (Title 13, Title 26, CIPSEA, privacy law). The dominant variable. An agency can score "unready" precisely *because the law forbids exposure*. The benchmark MUST separate **can't** (legal) from **hasn't** (capability). Conflating them is the biggest fairness failure and the fastest way to get the instrument killed.
- **4 V's**: volume, variety, veracity, velocity — per-agency data complexity.
- **Size**: capacity proxy.
- **Age / institutional history**: legacy debt. Probably collinear with size + variety; a candidate, not a guaranteed independent axis.

Method sequence (keep these jobs separate):
1. Benchmark produces the score.
2. Covariates contextualize it.
3. **Clustering** (unsupervised: k-means / hierarchical) defines fair **peer cohorts** — score *within* group.
4. *Optional* **tree / random forest** (supervised) explains which covariates drive the score — only possible *after* the benchmark gives you a target. Forest comes after, not before.

Discipline: stratify to be **fair, not lenient.** Covariates set expectations within a peer group; they don't excuse the floor. Bottom of your own cohort = excuses spent.

## The definition deliverable
No binding government definition of "AI data readiness" exists.
- NAIRR implementation plan defers it to "community-driven principles and standards" — it punts.
- NIST is the wished-for owner (BPC recommends a CSF-style "nutrition label" standard) but **has not produced it.** A NIST-shaped hole, not a NIST answer.
- Every existing artifact (NOAA/ESIP AI-Ready Checklist, Virginia, NIH/EDRN) is a 2006-lens checklist: clean tables, labels, normalization, metadata. ML-training framing.
- **The machine-as-first-class-consumer framing is absent from the entire corpus.** You're ahead of it, not behind.

So you **author the interpretation** — the absence is your license. Two layers:
1. **Baseline** (conventional fitness-for-AI). Political cover, legibility, keeps you from being dismissed.
2. **FSS-specific machine-first extension** (MCP / llms.txt / WebMCP / MUI / machine-as-consumer). The substance that's actually yours.

Founding route: take NAIRR's "defer to community standards" + NIST RMF scaffolding, then write the FSS-specific interpretation with explicit provenance/etymology, since there's no canonical source to inherit from.

Note: definition and instrument need not share polarity. Define **readiness** (the deliverable demands it) but **measure unreadiness** (where clean signal lives).

## The through-line
Every structural choice that inserts a human filter between the data and the result is an opening for theater. Therefore:
- Remove the human entirely where a machine can measure the machine.
- Don't aggregate per-agency; collect from many practitioners direct.
- Weight practitioners over executives.
- Branch by role only where it changes who can answer truthfully.
- Measure symptoms/unreadiness where self-report is unavoidable.

## The one decision that gates everything (UNRESOLVED)
**Diagnostic or scorecard?**
A reproducible benchmark is objective — and therefore a public, agency-attributable ranking of who's broken. That's leverage or liability depending on who frames the report. It also determines survey honesty: if practitioners smell a scorecard, you get gamed data and you're back in the theater you're trying to burn down.

Decide intended use **before building**, because it changes what's safe to ask and whether you publish raw scores.

## Open items
- [ ] Diagnostic vs. scorecard decision.
- [ ] Draft the two-layer definition.
- [ ] Benchmark rubric: enumerate probes (llms.txt, MCP/WebMCP, content negotiation, metadata, provenance) + scoring.
- [ ] can't-vs-hasn't gate: how the benchmark detects/flags legal constraint so it doesn't penalize lawful non-exposure.
- [ ] Covariate schema + clustering scaffold for peer cohorts.
- [ ] Thin practitioner instrument: symptom item bank, role tracks, anti-laundering collection path.
