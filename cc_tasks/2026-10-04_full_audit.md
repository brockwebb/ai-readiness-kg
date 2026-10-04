# CC Task: full-project audit before anything is shown: holes, weaknesses, and what it takes to operationalize

**Date:** 2026-10-04
**Project:** ai-readiness-kg
**Authored by:** Desktop session, on the operator's instruction of 2026-10-04: before the summary or anything else is shown to anyone, audit the whole project at full power for holes and weaknesses, and for what stands between it and a system other people can run and trust. The audit is of this project's own evidence, methods and code. It compares against nothing outside this repository and names no other group's work.
**Implements:** DN-009 decisions 2, 3 and 7; DN-010; the adversarial-review rubric v1.3.0.
**Framework layer served (DN-005 §5 rule 1):** all layers; the audit is cross-cutting and says so.
**Fulfils:** its own ResearchTask. Launched by the dispatcher.
**After:** `2026-10-04_views_regenerate_v2.md`
**Spend:** est. 12M tokens. **Model:** `claude-fable-5-1` at maximum reasoning effort if the dispatcher's launch profile can select it; if it cannot, the session records the model it ran under as premise wrong number 1 and the operator reruns the task by hand under Fable. The audit reads RESULTs and code; it builds nothing and fixes nothing.
**Network:** none beyond `git push` from the shell. WebSearch and WebFetch harness tool calls are permitted for decision 1 only.

**HEADLESS NOTICE.** No next turn. Poll every detached command to its EXIT line.

## Decisions

1. **Method first, named, before any file is opened.** Write the audit protocol into the README before reading anything else. Base it on: this repository's adversarial-review rubric v1.3.0 and `seldon audit` (run it first; its output is the audit's starting inventory); threats-to-validity taxonomy for empirical work (Wohlin et al., *Experimentation in Software Engineering*, the four validity classes: construct, internal, external, conclusion); the ACM Artifact Review and Badging reproducibility criteria (available, functional, reusable, results reproduced); and the SFV construct this project's own author is writing up (state fidelity validity: does the stored state match what the pipeline claims it did). Retrieve each with a locator; one that cannot be retrieved is labelled recalled. Every finding below is tagged with the validity class or badge criterion it threatens.

2. **Inventory, read in this order.** Every RESULT under `cc_tasks/` dated 2026-10-02 to 2026-10-04 and their "premises wrong" sections; `docs/evidence/claims.yaml`, `definition_pairs.md`, `kg_questions.yaml`; `docs/catalog/`; `docs/figures/`; `docs/design/` from DN-005 on and `design_decisions.md`; `framework/ai_readiness_framework.json`; `assessment/harness/scan/rules/`, `score.py`, `targets.yaml`; `kg/schema.yaml`, `build_projection.py`, `eventlog.py`, `grounding.py`; `docs/research/2026-10-04_node_key_fusion_audit.md`; `tests/`. Record what was read and what was not.

3. **The known list, verified, not re-found.** Each of these is confirmed open, closed or changed, with the locator, and a confirmation is not a finding: 16 indicators with no `EVIDENCED_BY` edge (`CL-054`); 26 Definitions with no asserting event (NOAA among them); no construct layer, so comparative questions are `partial` or `cannot_answer`; A12 as candidate versus the counts; 3 of 16 agencies unranked on denial, and whether the manners boundary is stated so a hostile reader cannot call it a blocked scan; any citation still "recalled, not retrieved"; node-key fusion and its effect on cited counts; the single-leg fragility of every rank; anything in `docs/` that reads as ROI, impact or value entering the score; the deck still carrying 24 and 264; the `declared_tokens` and header-parse defects in the dispatcher (`fa40072e`, `1267b87d`).

4. **Findings beyond the list.** Every new finding carries: the file and line or node id; the validity class; what a skeptical reader would say in one sentence; severity on a declared 3-point scale (blocks showing, must fix before a second cycle, note); what closes it, in one sentence, and whether that is a task, a ruling, or a wording change. No finding without a locator. No finding that is an opinion about style. "Vibe" claims (a thing that looks built but has no test, no control, no locator, or no event) are the audit's priority class.

5. **Operationalization, separately.** A second list: what a stranger would need to run this on one site, from `docs/adopt/run_on_your_site.md` to a finished scan, where it breaks, and what is undocumented, hard-coded or local to this machine. Each item locates the dependency. The modular-roster record (`712755f8`) is read, not duplicated.

6. **Controls on the auditor.** Three planted defects, placed by script in a scratch copy before the audit reads (a claim with a wrong locator, a test with no assertion, a number in a figure caption that is off by one), and the audit reports whether it caught each. Planted defects are removed before the RESULT and never committed.

7. **Reader gate (DN-009 d7).** A fresh subagent given only the ranked findings table writes five sentences on what would stop it trusting this project, and the one thing to fix first.

**Write set:** `docs/audit/2026-10-04_full_audit.md` (protocol, inventory, findings table, operationalization list, controls, limits), `docs/audit/2026-10-04_full_audit_findings.csv`, `scripts/plant_audit_controls.py`, the RESULT. Byte-identical: everything else. No fix of any kind.

**Immutable once written.**

## Gate and report
`make gate-fast`, `seldon verify`, the protected-paths diff. RESULT `cc_tasks/2026-10-04_full_audit_RESULT.md`, under 80 lines: the method and what was retrieved versus recalled; counts of findings by severity and by validity class; the top ten findings in full; the controls caught; the operationalization list's length and its top three; the reader gate's five sentences; premises wrong, with the model actually used first; tokens and model. `seldon cc complete`, commit, push.

**SEQUENCING:** protocol and retrieval → `seldon audit` → plant controls → read inventory → verify known list → new findings → operationalization → remove controls → reader gate → gate → RESULT → push.
