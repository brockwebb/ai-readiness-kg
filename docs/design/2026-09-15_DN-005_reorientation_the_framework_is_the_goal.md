# DN-005 — Design note: reorientation. The goal is the framework; L0 is one level of it

**Date:** 2026-09-15. Desktop design note, written at the operator's direction at thread close, after the operator corrected two direction errors in one session: the L0 report being run as a publication (DOI, licence polish, self-row, page budget) and, when that was called out, the Desktop's swing to "the deliverable is the January brief". Both were the same error: naming the most recent artifact as the goal. This note is the standing map every later task cites, and it supersedes the "deliverable" sentence in `handoffs/2026-09-15_thread_close_l0_shipped_rejudgements_on_log.md`.

Under DD-001 (every assertion citable by a stranger), DD-003, DD-054, DN-001 to DN-004.

---

## 1. The goal, unchanged since the project began

**An AI-readiness framework for federal statistical publishers: a way to rate and score, quantitatively and qualitatively, whether the public and the tools the public now uses can reach, understand and use the data they paid for.** Everything else in this repository is a level of it, a measurement of it, a view of it, or a demonstration of it.

- **L0** is the most basic level (host-level: crawler policy present, discovery files, deep links, declared versus enforced access). It is one step, and the one with cold, re-derivable data behind it today.
- **The L0 report** (`docs/reports/2026-09_fss_ai_readiness_L0.pdf`) is evidence under the framework. It is not the product and it is not a publication in the release sense; nobody has been told it exists.
- **The site** (`brockwebb.github.io/ai-readiness-kg`) is a demonstration of what an AI-ready site looks like, data-first, with its own scorecard visible. That is the whole of its purpose.
- **The January ICSP briefing** is a view of the framework at whatever state it is in then: professionally, FSS sites are not AI ready, the public who paid for the data is underserved, here is who, here is what to do. Slides with visuals from matrices that already exist.
- **Open source** exists to protect the work from being hidden or gatekept, not to publish it. Provenance is git, the append-only log with timestamps and hashes, and CC BY 4.0. No DOI is needed for that and none is being minted.

## 2. The framework's layers, and where each stands

### 2.1 The framework object: constructs, indicators, levels, a rating

**Exists.** The framework record (`framework/ai_readiness_framework.json`, one writer, event-logged) is projected into Neo4j: `AssessmentIndicator`, `Construct`, `Definition`, `MeasurementSpec`, `Rule`, `Document` nodes, `EVIDENCED_BY`, `MEASURED_BY`, `MEASURES`, `SUPERSEDES` edges. 12 indicators carry a construct, a spec, a rule and cited sources with locators read from the documents (DN-001). The appendix, the traceability test and the tool map are queries over it. The framework as its own graph object is therefore not future work; it is the substrate.

**Does not exist.** (a) Levels above L0 defined as levels. (b) A scoring model: today the instrument reports pass rates per check with Wilson intervals and nothing composite; there is no quantitative score and no qualitative rubric. (c) A10 is a stub against an operator-held internal draft; A12 is a CANDIDATE rule (DD-054) and enters no numerator. (d) The extended skeleton's candidate indicators beyond the 12 have no spec, rule or source.

### 2.2 Measurement capability, tiered three ways

Every indicator in the framework is to be tagged with how it can be measured. This tagging does not exist yet and is the first bounded piece of work under this note.

- **Tier M (measured by our harness).** The six L0 host checks and the product checks A1, A3, A8, B3, D4, G1-D, across 16 bodies plus three reference hosts, four measured cycles and one self cycle, every payload re-derivable byte for byte, every judgement on the append-only log (DN-003). Cold data. This is the tier the January position rests on.
- **Tier O (measurable with open tools).** The Screaming Frog investigation and `docs/design/scan_tool_map.md` (a generated table of which tool feeds which check) exist. What does not exist: the coverage answer (which framework indicators open tools reach that our harness does not), and a harness path that runs them under the same manners, evidence retention and re-derivation discipline.
- **Tier D (declared: paid tools, agency-side configuration, or things only the agency can say).** The honest scope of a survey. Nothing tiers indicators this way yet.

### 2.3 Prescription: action mapped to indicator, with effort, cost and value

**Does not exist in any form, and it is the largest gap.** The instrument measures; it does not yet say what to do. This layer is what makes "you need this, here is what you do, here is the effort, here is the cost, here is the value" a query rather than a slide.

Prior art for the shape (to be read before designing, per DD-003): WCAG's success criterion → sufficient techniques → common failures; CIS Benchmarks and OpenSSF Scorecard, each check with a remediation. None carries cost or value; that part is this project's contribution and must be sourced where a source exists and marked as estimate where none does. In graph terms: an `Action` node type, `REMEDIATES` edges to indicators, effort/cost/benefit fields with provenance, and a source or an explicit estimate marker on each.

### 2.4 Exposure: the graph through an MCP with a natural-language front

**Does not exist for this graph.** The pattern exists in fss-policy-kg and the Census MCP. Once 2.2 and 2.3 are in the graph, this is the same server shape over the `ai-readiness-kg` Neo4j database (the database name is the graph name, per the operator's convention). It exposes the research, the documentation, the framework, the evidence and the prescriptions through one interface.

### 2.5 The survey, and what the working group expects

The ICSP working group expects a self-report survey in January by which agencies declare themselves AI ready. This project's position: probe the sites for hard data, and treat the survey as at most the **declared layer** against **measured behaviour**, which is exactly the A11 triad already in the instrument (declared, enforced, and the gap between them). Where nothing can be probed (Tier D), the survey is all there is and says so. The survey is not fought; it is placed.

## 3. What stops

The publication-process track is closed: no DOI, no host repository unless the operator asks for it, no further licence or citation polish beyond what standing tests already enforce, no page budgets. `2026-09-14_standing_guards.md` (`0af9b050`) runs because it is the last of that track and it stops the evidence moving under everything else; after it, no task is authored under DN-002 decisions 5 or 6.

## 4. Order of work, all of it under §1

1. **The standing cadence** (`6ee71737`, the standing dispatcher; then cycle 5 from a schedule). January's numbers must be January's, and a cycle's own gate now publishes its measurement and any commissioned re-judgement to the log (DN-003).
2. **Capability tiering of every indicator** (§2.2), with the open-tool investigation as its evidence and the tool map as its starting table. Output: a `measurement_tier` on every indicator node, sourced.
3. **The prescription layer's schema and its first sourced actions for the Tier M checks** (§2.3), since those are the checks with cold data behind them.
4. **The MCP over the graph** (§2.4).
5. **The scoring model** (§2.1 b), which needs 2 and 3 to have anything to score, and the level definitions with it.
6. **The January view** falls out of 1 to 3 without being aimed at: matrices already exist; visuals already exist; the prescriptions are what make the third slide.

Research threads that continue alongside and are not displaced: the G1 January pilot (instrument frozen at v2, `73f0aa5d`, fixture source `0128144c`); the third-party-observed layer (`43108db6`); the little-guy ladder (`ae58c74e`); ER debt 1 to 5 (`43edd2cc`, `26214693`, `f9c5d054`, `d9c26f0c`, `4e132d0e`) gated by `37476f34`; the write-ups (`f1da94c6`, `3b89a2f6`); cycle-4 instrument maintenance (`520ec74b`) and the hygiene queue (`34ccb843`, `3e8c6661`, `44ba0fd0`, `f6b24c9d`, `885c5d81`, `2b11ba3a`, `0caa13f7`).

## 5. Anti-drift rules for the Desktop, binding on every task authored from here

1. **Every task file names the framework layer it advances** (§2.1 to §2.5) in its header. A task that advances none is a hygiene task and says so; a task that cannot say which layer it serves is not authored.
2. **No artifact is the goal.** A report, a site, a brief, a survey, a paper: each is a view or a demonstration. When a RESULT's "next task" list points at polishing a view, the Desktop asks which layer the polish advances before authoring anything.
3. **The operator is brought in for value inputs and public releases only.** Not for process decisions, not for cosmetic fixes, not for identifiers.
4. **When the Desktop notices it has named the most recent thing as the target, that is the signal to stop and re-read this note**, not to name a different recent thing.

## 6. Where this note is cited

The handoff of 2026-09-15 (addendum), `CLAUDE.md` (to be updated by the next session to point here from its statement of purpose), and every task file from `0af9b050` onward.
