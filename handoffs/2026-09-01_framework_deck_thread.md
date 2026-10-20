# Handoff — 2026-09-01: framework deck thread (+ standing state)

Session protocol applies: verify against live state before trusting any prose below. `seldon go` with explicit project_dir; graph outranks this file.

## MISSION for the new thread: the hybrid/combined AI-readiness framework deck

Produce a plain-text PowerPoint (no template, no theme, text-first slides) presenting the hybrid/combined AI Data Readiness framework — the USAFacts-ACCURATE-crossed operationalization with Brock's extensions. Desktop drafts the content and structure (judgment work); the mechanical pptx build can go either way (Desktop pptx skill, or a CC task with python-pptx). Target: a working deck Brock can edit, not a polished deliverable.

### Source documents, in reading order
1. `docs/crosswalk/usafacts_operationalization_skeleton.md` — the framework itself: indicator groups A–G, ~40 indicators, machine-first/machine-testable stance (self-report replaced throughout).
2. `docs/crosswalk/meeting_brief_2026-09-01.md` — current evidence coverage per group; the honest group D empty row (corpus holds zero licensing/openness evidence — a finding, not a bug); group F thin pending b014/b015.
3. Brock's TEVV critique of the USAFacts framework (missing TEVV loops) — already delivered as formal feedback; referenced in memory and crosswalk docs.
4. `docs/research/writeup_draft_v1.md` — the methods story if the deck wants a quality-measurement slide (gates, SPRT, acceptance sampling; one slide max).
5. `docs/research/writeup_foils.md` — corrected foil characterizations (Karpathy wiki, OKF) if positioning-vs-adjacent-work appears.
6. The discovery/access-control reference cluster (AEM tagging/query, Google canonicalization, Bing robots directives, OAI-SearchBot publisher controls, Cloudflare AI Crawl Control + WAF/bots precedence + managed robots.txt, FedRAMP marketplace entries) — pasted into the 2026-09-01 thread, held as potential source material. Maps to the SEO/AI-O/GEO under-representation gap; ADJACENT to but distinct from group D (access-control = can the machine reach it; group D = may the machine reuse it). Fork to resolve if used: corpus material for the KG vs reference material for instrumenting a discovery/access indicator — different admission paths.

### Framing points already settled (do not re-litigate)
- G1 (uncertainty legibility: MOEs/CVs as structured fields + EVAL for whether AI restatements preserve uncertainty) is the flagship — absent from all adjacent frameworks.
- Machine-first: AI is the primary consumer; human views are downstream projections.
- The KG grounds citations and detail; ~76% of crosswalk demand extracted now, ~85% at b015 close. Deferred content is low-demand by measurement and revivable by one event; do not block deck content on corpus completeness.
- The quality line, usable verbatim: every claim in the graph passed a pre-registered faithfulness gate (F_upper < 0.10) and every batch passed acceptance sampling before entering; the graph practices G1's own discipline (numbers carry intervals).
- Group D empty row is a talking point (the measurement layer finds its own corpus gaps), and the acquisition round it triggers is pending a value call after the meeting.

## Standing state (verify live; accurate as of ~08:00 EDT 2026-09-01)

- **v038 burn:** b001–b013 scoped set complete — 9 accepts + b010 `sampling_inconclusive` (accept-with-flag; true cause: 33 admitted items < 55-fact SPRT floor — unsatisfiable, not ambiguous; distinction recorded for the writeup). ADDENDUM-03 executed: substrate wiring verified no-behavior-change (92 byte-identical / 100 fall-through / 2 intended changes), b014 (odcs) verdict pending confirmation, b015 (slsa) was mid-flight at a seam-STOP (`events/bulk_v038_STOP.json`, operator pause). NEXT SESSION FIRST CHECK: ledger quiet? b014/b015 verdicts on disk? §19 reconciliation appended? `seldon cc complete` fired on the base task? Zero quarantines and 132 refusals/22 docs already gathered for the reconciliation.
- **Open tasks (graph):** f1da94c6 (writeup — draft v1 on disk awaiting Brock's review; task closes only on his acceptance), 6ee71737 (dispatcher design — the real L4 gap is dispatch latency; Desktop design session; swarm notes are a hard input), 3b89a2f6 (boundaries essay — accepted; notes at `docs/research/swarm_stigmergy_notes.md`), 95f286e4 (duplicate manifest_add — zero spend, any idle slot), 82c281ff (bulk base task — closes at reconciliation).
- **Stale relics safe to delete in housekeeping:** `state/overnight_burn_STOP`, `state/overnight_burn_status.json` (08-27/28 lane system, not this burn).
- **Evening budget note:** b015 completion is the END of scoped+revived work — nothing left to burn on v038 afterward except the deferred tomes (593 chunks, 6 demand, standing call: demand-pull only). A night budget has no v038 target; candidates are the group D acquisition round (post-meeting value call) or nothing.

## Bus protocol (agreed 2026-09-01)
Brock does not paste CC narration. CC finishes → Brock sends a one-liner ("X done") → Desktop reads RESULT/ledger/graph and reports what the record shows. Claims are checked against files, not relayed.
