# Handoff — 2026-07-02 — ai-readiness-kg bootstrap session

**Session type:** Desktop (design/gate)
**Graph state is authoritative; this is compression. Verify via `seldon go` at /Users/brock/GitHub/ai-readiness-kg.**

## What happened

1. Repo designed and scaffolded. Public at github.com/brockwebb/ai-readiness-kg.
2. Design docs on disk: `docs/schema_v0.1.md` (claims-and-constructs schema, whole-doc Fable extraction protocol, pilot gate) and `docs/design_decisions.md` (DD-001..DD-008: self-containment, discovery≠extraction, manifest gate, controls.yaml/Wintermute hook, autonomy ramp L2→L4 with SQC promotion gates, sharded event log).
3. CC tasks executed: scaffold (703825e3, done), manifest module (c49109b1, done — event-sourced projection, five rejection paths, hash verify).
4. CC task written, pending execution: discovery scan (ab28a2f8) — builds `corpus/staging/candidate_register.jsonl` from (A) the DeepResearch synthesis doc in docs/research/, (B) wintermute-intake keyword scan, (C) fss-policy-kg manifest cross-scan.

## Standing rulings made this session

- Synthesis/DeepResearch docs are discovery input only, never corpus Documents. Their citations become candidates, verified at manifest-add.
- Extraction is always native to this graph against primary sources. No imported extractions from Wintermute or fss-policy-kg, ever (DD-002).
- Budget: Max OAuth, personal project. USAi = possible later Census-internal fork.
- `.env` exists at repo root (gitignored). Operator to confirm `git ls-files .env` empty and audit for ANTHROPIC_API_KEY.

## Next session (in order)

1. Run discovery scan CC task if not yet run.
2. Triage candidate register → first manifest adds (Desktop judgment). Target the 5 pilot docs first (schema doc §9): FCSM 25-03, MLMU-25, Lawrence DRL, one industry (Cisco index or IBM), one academic instrument paper (AIDRIN or DRAI 360).
3. Write CC task: extraction module (model client on Max OAuth + whole-doc protocol from schema §5 + grounding validator + build metrics). Pilot gate before any bulk.

## Open items

- .env audit (above).
- Autonomy level: currently L2 (manual). Promotion criteria not yet quantified — define control limits after pilot metrics exist.
- Log rotation implemented via sharded eventlog (DD-008); no action needed.
