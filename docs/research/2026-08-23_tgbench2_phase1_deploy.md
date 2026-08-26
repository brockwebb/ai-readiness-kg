# TrustGraph benchmark v2 — Phase 1: deploy + claude-cli backend (task `2026-08-23_trustgraph_benchmark_v2`, Seldon 36a5c0e1)

**Executed:** 2026-08-25 22:12–22:31 EDT. **Outcome: COMPLETE.** Stack deployed, custom
`claude-cli-completion` backend implemented against TrustGraph's text-completion component
contract, unit-tested with a stub CLI (no model calls), and smoke-tested end-to-end with
exactly ONE real model call. `ANTHROPIC_API_KEY` was never set anywhere (verified empty in
the session env; the backend refuses to start if present). Stack left RUNNING.

Supersedes the v1 Phase-1 blocker record (`2026-08-23_tgbench_phase1_blocker.md`): v1
stopped at 0 min deploy for want of a Google credential; v2's design (same pinned Claude
model both sides via the Claude Code CLI) removes that dependency entirely.

## Headline numbers

| metric | value |
|---|---|
| deploy wall-clock (task start → first successful API query) | **16.8 min** (22:12:16 → 22:29:04) of a 2 h box |
| backend implementation (interleaved; contract study → tests green) | **≈ 17 min** (22:14 → 22:31) of a 3 h box |
| image pull + `up -d` wall-clock (first attempt, cold images) | 115 s (epoch 1787710736 → 1787710851) |
| `up -d` → bootstrap complete (final clean run) | 72 s |
| `up -d` → first successful authenticated API query (final clean run) | 78 s (1787711266 → 1787711344) |
| containers | 17 long-running + 2 one-shot init (of 20 defined; 1 disabled by design) |
| total RAM footprint (`docker stats`, post-smoke) | **4,357 MiB** |
| smoke test wall-clock (CLI client, gateway round trip) | 7 s (1787711373 → 1787711380); model call itself 3,374 ms |
| smoke test model calls | exactly 1; 0 retries |
| smoke envelope usage (`claude-opus-4-8`) | input=2, cache_read=16,012, cache_creation=18,241 (Σ input ctx 34,255), output=124; envelope cost_usd 0.193526 (informational — subscription OAuth, no API billing) |
| unit tests | 14/14 new backend tests pass (stub CLI, zero model calls); 168/168 in the whole text-completion unit suite |

## What was deployed

- **Fork:** `github.com/trustgraph-ai/trustgraph` cloned to `/Users/brock/GitHub/trustgraph-fork`.
  Clone head was `9a5ffc9c82d1d84edf2ff12d0022994400b799dd` (2026-08-24, 2.9-dev); the working
  branch **`claude-cli-backend` is based at tag `v2.8.15`** (`3cb64396`) so host-side code
  matches the deployed container images exactly (schema dir diff v2.8.15→master: empty, but
  the pin removes the risk class). Backend commit: `7395f6b2`. Committed to the fork only;
  no remote push (no GitHub fork exists under the operator's name; creating one is his call).
- **Deployment generation:** the repo's README points at `npx @trustgraph/config`, which is an
  interactive wizard calling a REMOTE config service. The actual generator lives in a separate
  repo, `trustgraph-ai/trustgraph-templates` (jsonnet templates + `tg-build-deployment` CLI) —
  run locally, fully offline, non-interactive:
  `tg-build-deployment --template 2.8 --latest --input config.json --platform docker-compose -o deploy.zip`
  (resolved to template version **2.8.15**). Artifacts under
  `benchmarks/trustgraph/deploy/` (`config.json`, `deploy.zip`, `unpacked/`).
- **Component selection** (`config.json`): trustgraph-base, pulsar, cassandra,
  triple-store-cassandra, row-store-cassandra, vector-store-qdrant, garage,
  embeddings-fastembed, ollama (max-output-tokens 4096). No vLLM, no OCR components, no
  grafana/loki. The `ollama` entry exists only because the templates require *some* LLM
  component to shape the flow config; its container is **never started** (below). No vendor
  LLM container runs; no API key exists anywhere in the deployment.
- **Override** (`unpacked/claude-cli-override.yaml`, their compose-profiles mechanism):
  1. `text-completion` service moved to a never-activated profile — the host claude-cli
     process replaces it (running both would split the shared Pulsar subscription);
  2. Pulsar `6650:6650` published for the host process — the generated broker config already
     advertises a `localhost` listener (`advertisedListeners: external:pulsar://pulsar:6650,localhost:pulsar://localhost:6650`),
     and `trustgraph-base` supports `--pulsar-listener localhost`, so host-side processors are
     an intended TrustGraph pattern, not a hack;
  3. api-gateway `8088:8088` published for CLI/API access.
- **Model pinning:** the seeded runtime config (`unpacked/trustgraph/config.json`) had
  `llm-model` default `gemma3:12b` (from the ollama component). Edited pre-bootstrap:
  `parameter-type/llm-model` and (missing upstream) `parameter-type/llm-rag-model` now default
  to **`claude-opus-4-8`**. Verified live: `tg-show-flows` reports the default flow
  (blueprint `everything`) with "LLM model: Claude Opus 4.8 (pinned, via host claude-cli
  backend)". The backend additionally enforces the pin via its model-substitution gate.

## The component contract implemented against

- `trustgraph-base/trustgraph/base/llm_service.py` — `LlmService` (subclass of
  `FlowProcessor`): registers a `ConsumerSpec` on the `request` topic
  (`TextCompletionRequest`) and a `ProducerSpec` on `response`
  (`TextCompletionResponse`); subclasses implement
  `async generate_content(system, prompt, model, temperature, response_format, schema) -> LlmResult(text, in_token, out_token, model)`.
  Pulsar plumbing, flow-config subscription, error envelopes, and `TooManyRequests`
  backoff live in the base.
- Reference implementations mirrored: `trustgraph-flow/trustgraph/model/text_completion/claude/llm.py`
  (their Anthropic-SDK backend) and `.../ollama/llm.py` (system+prompt concatenation policy).
- Launch mechanism: `processor-group` (`trustgraph-base/trustgraph/base/processor_group.py`)
  with a `launch.yaml` — the same mechanism their containers use.

## The backend (fork branch `claude-cli-backend`, commit `7395f6b2`)

New files:
- `trustgraph-flow/trustgraph/model/text_completion/claude_cli/llm.py` (+ `__init__.py`, `__main__.py`)
- entry point `text-completion-claude-cli` in `trustgraph-flow/pyproject.toml`
- `deploy/claude-cli-host/launch.yaml` — two processors (`text-completion`,
  `text-completion-rag`), concurrency 1 each, `pulsar://localhost:6650` +
  `pulsar_listener: localhost`
- `tests/unit/test_text_completion/test_claude_cli_processor.py`

Behaviour (mirrors `kg/extraction/model_stub.py` conventions):
`claude -p --model claude-opus-4-8 --output-format json --allowed-tools NoTool`, prompt on
stdin (system + "\n\n" + prompt; prompt text unmodified), hermetic empty temp cwd, JSON
envelope parsed; refuses `ANTHROPIC_API_KEY`/`ANTHROPIC_AUTH_TOKEN` at startup;
model-substitution gate (envelope `modelUsage` must list exactly the requested model,
else discard + raise); retry-once with 5 s pause on OSError (CLI auto-update window) and
nonzero exit; `TooManyRequests` on rate-limit envelopes (base handler backs off); response
text returned **verbatim** (`PromptManager.parse_json` downstream already strips fences);
`in_token` = inputTokens + cacheRead + cacheCreation, breakdown logged per call.
Streaming: not supported (declared honestly; base falls back to non-streaming).
Temperature and forced-schema args are accepted for contract compatibility and ignored —
the CLI exposes neither (recorded as a fidelity limitation).

**Unit test:** a stub `claude` shell script on PATH emits a canned JSON envelope; covers the
happy path, exact CLI argv contract, stdin pass-through, model-substitution rejection (wrong
and extra model), retry-once semantics (exactly 2 invocations then error), missing CLI,
error/rate-limit/unparseable envelopes, API-key refusal, optional system prompt.
14/14 pass with zero model calls; full text-completion suite 168/168
(4 files excluded as pre-existing collection errors — they import optional provider
packages `trustgraph-bedrock`/`-vertexai`/googleaistudio not installed here; unrelated to this change).

## Smoke test (ONE real call)

Gate honoured: `pgrep -f probe_judge.py` empty before and after. Command:
`tg-invoke-llm -u http://localhost:8088/ -t $IAM_BOOTSTRAP_TOKEN --no-streaming --show-usage "<system>" "<one paragraph>"`
→ gateway REST → Pulsar `request:tg:text-completion:default:default` → host claude-cli
backend → `claude -p` → response back through the same path. 7 s round trip; sane
one-sentence summary returned; usage above. This exercises TrustGraph's full transport +
flow-config machinery with the backend; document ingestion (chunker → kg-extraction) is
deliberately NOT run — that is Phase 2's extraction work and would have made 4+ model calls
per chunk.

Two findings from the one call, relevant to Phases 2–3:
1. **Per-call context overhead:** the CLI injects its agent system prompt — 34,255 input
   tokens for a two-sentence task, of which 16,012 came from cache and 18,241 created cache
   (steady-state calls should read ~34k mostly from cache). TrustGraph-side call counts
   will multiply this; it is the same overhead class our own extractor pays via the same
   CLI, so the model-constant design holds, but token projections must budget ~34k
   input/call.
2. **Meta-commentary bleed:** the response opened with one sentence of the model reasoning
   about its CLI context ("This is ... not a task requiring skills...") before the answer.
   Verbatim return preserves this; downstream JSON extraction tolerates it (fence/balanced
   parsing), but judge-facing text metrics should expect occasional preamble.

## Friction log (minutes lost, deploy side)

| # | friction | cost |
|---|---|---|
| 1 | README's `npx @trustgraph/config` is an interactive wizard against a remote service; no GitHub releases carry `deploy.zip`; `templates/generate-all` referenced in DEVELOPER_GUIDE.md does not exist in the repo. Generator found in separate `trustgraph-templates` repo (local, non-interactive) | ~6 min discovery |
| 2 | `memory-profile-low` template is broken for minimal configs: patches component key `"qdrant"` where the component's visible key is `"vector-store"`, and patches components that are not deployed — jsonnet then materialises `create`-less fields → `RUNTIME ERROR: Field does not exist: create`. Deployed without it | ~7 min |
| 3 | **Docker VM disk 97.3% full** → BookKeeper marks ledger dirs non-writable → every persistent-topic subscribe times out → bootstrap/flow-svc crash-loop with opaque `PulsarException: 3 Timeout`. Root cause visible only in *bookie* logs. Fixed by `docker builder prune -af` (46 GB) + `docker image prune -f` (15.8 GB) | ~8 min |
| 4 | IAM bootstrap token must be **`tg_`-prefixed** (`API_KEY_PREFIX` in `iam/service/iam.py`; the gateway routes non-`tg_` bearers down the JWT path) — undocumented in the compose flow; every failure masked as `auth failure`. Required `down -v` + re-init with a compliant token | ~5 min |
| 5 | Loki log push is **enabled by default** with hardcoded `http://loki:3100` (`trustgraph-base/trustgraph/base/logging.py`); without the optional loki component every container's logs drown in `logging_loki` handler tracebacks, taxing all subsequent log forensics. Host process runs with `--no-loki-enabled` | ~3 min spread |
| 6 | `pip install -e` fails out of the box: `trustgraph/base_version.py` etc. are Makefile-generated and absent from a fresh clone. Created pinned at `2.8.15` | ~3 min |
| 7 | Master (2.9-dev) vs deployed containers (2.8.15): re-based the branch onto tag `v2.8.15` to eliminate wire-schema skew for the host processors | ~3 min |

None of these approached the 2 h stop. The disk-full incident (3) is environment, not
TrustGraph; 2, 4, 5 are TrustGraph defects/doc gaps worth an upstream note (operator's call).

## Exact commands — stack up / down

```bash
# up (from ai-readiness-kg)
cd benchmarks/trustgraph/deploy/unpacked
docker compose -f docker-compose.yaml -f claude-cli-override.yaml up -d
# host backend (after the flow bootstraps, ~90 s; from the fork)
cd /Users/brock/GitHub/trustgraph-fork
.venv/bin/processor-group --no-loki-enabled -P 8901 \
    -c deploy/claude-cli-host/launch.yaml > /tmp/claude-cli-backend.log 2>&1 &

# down (stop containers, keep data volumes)
cd benchmarks/trustgraph/deploy/unpacked
docker compose -f docker-compose.yaml -f claude-cli-override.yaml down
pkill -f 'processor-group.*claude-cli-host'
# full reset (wipes cassandra/pulsar/qdrant volumes; IAM re-seeds from .env token)
docker compose -f docker-compose.yaml -f claude-cli-override.yaml down -v
```

Auth: `benchmarks/trustgraph/deploy/unpacked/.env` holds the locally generated
`IAM_BOOTSTRAP_TOKEN` (`tg_`-prefixed; it IS the admin API key plaintext) — a
local-only secret; keep it out of git per standards even though `benchmarks/` is
otherwise committed. UI: http://localhost:8888 · gateway: http://localhost:8088 ·
Pulsar (host listener): pulsar://localhost:6650.

**State at close:** 17 containers running, host backend running (log
`/tmp/claude-cli-backend.log`, metrics :8901), default flow `default` (blueprint
`everything`) live and pinned to `claude-opus-4-8`. Ontology blueprint (`ontology`)
present in the seeded config for Phase 2.
