#!/usr/bin/env python3
"""The model choke point: every model call in this repository goes through ``invoke``.

``invoke`` runs ``claude -p`` under Claude Max OAuth, never ``ANTHROPIC_API_KEY`` (DD-007), and
carries (a) the provenance stamp every extracted item must have (§4: model_id, schema_version,
extraction_event_id, timestamp), (b) the API-key guard, (c) the reserve-before-dispatch spend
guard (DD-022) and (d) the model-identity gate (invariant 5).

**Which model, and how it is launched (seldon AD-035, task MODEL-001, 2026-10-09).** A config
names a ROLE from seldon's ``models/registry.yaml`` (``model_config.yaml`` ``role:``; the G1
consumer config ``role =``), never a model id or an alias (R4). ``seldon.models`` resolves the
role to the id the lock holds for its family (R1), and ``invoke`` launches the LOCK's CLI with
``--model <id>``, ``--settings {"switchModelsOnFlag": false}``, ``--effort`` when the role has
one, and the four ``ANTHROPIC_DEFAULT_*_MODEL`` lock ids laid over the child's environment (R3).
Every call's served-model receipt goes into the spend ledger's settle record, and a served
model other than the requested one stops the unit as ``model_substituted`` (R6).
"""
from __future__ import annotations

import datetime
import json
import os
import re
import subprocess
import tempfile
import time
from pathlib import Path

# Extraction runs from a neutral empty directory so `claude -p` loads NO project context
# (CLAUDE.md / .claude settings). With the repo cwd, the model reads the project context and
# turns conversational — narrating and wrapping the JSON in prose ("I'll perform the
# extraction…" + a trailing "Note:…"), which broke parsing (root cause found 2026-07-09). A
# hermetic cwd makes it emit clean JSON. Created once, reused across calls.
_HERMETIC_CWD: str | None = None


def _hermetic_cwd() -> str:
    global _HERMETIC_CWD
    if _HERMETIC_CWD is None or not os.path.isdir(_HERMETIC_CWD):
        _HERMETIC_CWD = tempfile.mkdtemp(prefix="airkg-extract-hermetic-")
    return _HERMETIC_CWD

try:
    import yaml
except ImportError:  # fail loud (standard 4)
    raise SystemExit("FATAL: 'pyyaml' is required to load model_config.yaml (pip install pyyaml)")

try:
    from seldon import models  # the model registry, lock and receipt (seldon AD-035)
except ImportError as _exc:  # fail loud (standard 4): there is no model id without it
    raise SystemExit("FATAL: `seldon.models` is required to resolve a model role (seldon AD-035); "
                     "install the seldon checkout editable into this interpreter") from _exc

from kg import eventlog
from kg import spend  # preemptive shared spend guard (DD-022) — lives beside the DD-007 gate

_CONFIG_PATH = Path(__file__).resolve().parent / "model_config.yaml"
_PROMPT_PATH = Path(__file__).resolve().parent / "prompt_template.md"
# Credentials that must NOT be present: subscription OAuth only (DD-007). ANTHROPIC_API_KEY
# and ANTHROPIC_AUTH_TOKEN would both take precedence over the OAuth login.
_FORBIDDEN_ENV = ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN")
# claude -p protocol invariants (not operator-tunable): JSON envelope, no tools (pure
# completion). "NoTool" is a non-existent tool name — an allowlist that grants nothing real.
_OUTPUT_FORMAT = "json"
_EMPTY_ALLOWLIST = "NoTool"


class ModelConfigError(RuntimeError):
    """Config or credential misconfiguration — fail loud, never fall through (standard 4)."""


#: model_config.yaml names ROLES (seldon AD-035 R4). Each role key derives the id key the
#: callers have always read (`cfg["primary_judge_model_id"]` etc.): the id is an OUTPUT of
#: the lock, resolved at load, and never an input a config can set.
ROLE_KEYS = {"role": "model_id",
             "primary_judge_role": "primary_judge_model_id",
             "secondary_judge_role": "secondary_judge_model_id",
             "cleanup_role": "cleanup_model_id"}
#: Keys a model config may no longer carry. The ids are derived (above); the CLI is the lock's
#: (R3); the effort is the registry role's (R1). A config that still names one is refused at
#: load rather than silently ignored, because an ignored pin reads as an obeyed one.
_REFUSED_KEYS = (*ROLE_KEYS.values(), "cli", "effort")


def role_key(id_key: str) -> str:
    """The role key behind an id key: `model_id` -> `role`, `primary_judge_model_id` ->
    `primary_judge_role`. Report configs (`answer_model_key: model_id`) name id keys."""
    for rk, ik in ROLE_KEYS.items():
        if ik == id_key:
            return rk
    raise ModelConfigError(f"{id_key!r} is not a model_config id key; known: {sorted(ROLE_KEYS.values())}")


def check_role_name(role, where: str) -> str:
    """A role name, or a loud refusal naming why it is not one (AD-035 R1, R4)."""
    if not isinstance(role, str) or not role:
        raise ModelConfigError(f"{where}: no role named (AD-035 R4: configs name registry roles)")
    if role in models.ALIASES or models.MODEL_ID_RE.search(role):
        raise ModelConfigError(f"{where}: {role!r} is a model alias or id, not a role; name a role "
                               f"from seldon models/registry.yaml (AD-035 R4)")
    try:
        models.resolve(role)
    except models.ModelsError as exc:
        raise ModelConfigError(f"{where}: {exc} (AD-035 R1)") from exc
    return role


def resolve(role: str) -> str:
    """The lock id for a registry role, validated: the one call a script's `--role` argument
    makes (seldon AD-035 R1). An alias, an id or an unknown role is refused loudly."""
    return models.resolve(check_role_name(role, "role"))


def load_model_config(path: Path | None = None) -> dict:
    """Load model_config.yaml and resolve its roles through the seldon lock.

    Fails loud on a missing key, a non-OAuth provider, a key that names a model id, a CLI or
    an effort (AD-035 R4), or a role the registry does not hold (R1)."""
    path = path or _CONFIG_PATH
    if not path.is_file():
        raise ModelConfigError(f"model config not found: {path}")
    with path.open(encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh) or {}
    named = [k for k in _REFUSED_KEYS if k in cfg]
    if named:
        raise ModelConfigError(
            f"{path}: {named} name a model, a CLI or an effort; a model config names registry "
            f"roles only ({sorted(ROLE_KEYS)}), and the lock supplies the id, the CLI and the "
            f"effort (seldon AD-035 R3, R4)")
    for key in ("role", "provider"):
        if not cfg.get(key):
            raise ModelConfigError(f"model_config.yaml missing '{key}'")
    if cfg["provider"] != "claude_max_oauth":
        raise ModelConfigError(
            f"provider must be 'claude_max_oauth' (OAuth only, DD-007); got {cfg['provider']!r}"
        )
    for rk, ik in ROLE_KEYS.items():
        if rk in cfg:
            cfg[ik] = models.resolve(check_role_name(cfg[rk], f"{path.name} `{rk}`"))
    return cfg


def config_for_role(role: str, base: dict | None = None) -> dict:
    """A stub config that launches `role`: the base config (default model_config.yaml) with
    its `role` and `model_id` replaced. The ONLY way a caller retargets a call to another
    model; setting `model_id` by hand is refused at `invoke` (AD-035 R3)."""
    base = dict(base if base is not None else load_model_config())
    role = check_role_name(role, "config_for_role")
    return {**base, "role": role, "model_id": models.resolve(role)}


def role_for_model(model_id: str, config: dict | None = None) -> str:
    """The role, among those `config` names, whose lock id is `model_id`.

    For the `--model` arguments kept for compatibility (AD-035 R3 allows a `--model` that is
    validated to be a lock id): an id that is not the lock's id for one of this config's roles
    is refused, and so is an id two roles of different effort share, because the launch would
    have to guess the effort."""
    config = config if config is not None else load_model_config()
    roles = sorted({config[rk] for rk in ROLE_KEYS if config.get(rk)})
    hits = [r for r in roles if models.resolve(r) == model_id]
    if not hits:
        raise ModelConfigError(
            f"{model_id!r} is not the lock id of any role this config names ({roles}); the "
            f"lock: {models.lock_quote()} (AD-035 R3: launch from the lock, never a free id)")
    efforts = {models.resolve_role(r).effort for r in hits}
    if len(efforts) > 1:
        raise ModelConfigError(f"{model_id!r} is the lock id of roles {hits} with different "
                               f"efforts; name the role (`--role`), not the id")
    return hits[0]


def guard_no_api_key(env: dict | None = None) -> None:
    """Refuse to proceed if an Anthropic API key or auth token is present (DD-007).
    Subscription OAuth (via `claude -p`) is the only sanctioned path; either variable would
    take precedence over the OAuth login, so we fail loud rather than let it through."""
    env = os.environ if env is None else env
    for name in _FORBIDDEN_ENV:
        if env.get(name):
            raise ModelConfigError(
                f"{name} is set; extraction uses subscription OAuth only (DD-007). "
                f"Unset it; `claude -p` authenticates via the existing Claude login."
            )


def prompt_version() -> str:
    """The extraction prompt template version (from its `prompt_version:` header line),
    stamped in extraction events per §4 so a re-run under a hardened prompt is traceable."""
    for line in _PROMPT_PATH.read_text(encoding="utf-8").splitlines():
        m = re.match(r"\s*prompt_version:\s*(\S+)", line)
        if m:
            return m.group(1)
    raise ModelConfigError(f"no prompt_version header in {_PROMPT_PATH}")


def provenance_stamp(extraction_event_id: str, config: dict | None = None,
                     model_id: str | None = None) -> dict:
    """The universal provenance every extracted node/edge carries (§4). ``model_id`` overrides
    the config value with the model actually reported by the response envelope."""
    config = config or load_model_config()
    return {
        "model_id": model_id or config["model_id"],
        "schema_version": eventlog.schema_version(),
        "prompt_version": prompt_version(),
        "extraction_event_id": extraction_event_id,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }


def build_prompt(doc_id: str, source_text: str, config: dict | None = None) -> str:
    """Render prompt_template.md with the document. The rendered {{document_text}} IS the
    grounding source — validate spans against this same text (§5)."""
    template = _PROMPT_PATH.read_text(encoding="utf-8")
    return (template
            .replace("{{schema_version}}", eventlog.schema_version())
            .replace("{{document_id}}", doc_id)
            .replace("{{document_text}}", source_text))


def _balanced_object(text: str) -> str | None:
    """Return the first complete brace-balanced ``{...}`` object in ``text``, honoring JSON
    string literals so a ``}`` inside a quoted value doesn't close the object early. Robust to
    prose before AND after the object (the model frequently narrates around the extraction)."""
    depth = 0
    start = None
    in_str = esc = False
    for i, ch in enumerate(text):
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}" and depth > 0:
            depth -= 1
            if depth == 0 and start is not None:
                return text[start:i + 1]
    return None


def _extract_json(result_text: str) -> dict:
    """Parse the extraction JSON object from the model's response, tolerant of the model
    wrapping it in conversational prose and/or a ```json code fence (observed 2026-07-09:
    ``I'll perform the extraction…`` + fenced JSON + a trailing ``Note:…`` paragraph).

    Tries, in order: (1) a fenced ```json {…}``` block anywhere in the text, (2) the whole
    stripped text, (3) the first brace-balanced object. Only if ALL fail is it a per-document
    invocation failure (ModelInvocationError → driver retries/skips) — NOT a ModelConfigError,
    which is reserved for config/credential faults fatal to every document."""
    text = result_text.strip()
    candidates: list[str] = []
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fence:
        candidates.append(fence.group(1))
    candidates.append(re.sub(r"\s*```$", "", re.sub(r"^```(?:json)?\s*", "", text)).strip())
    balanced = _balanced_object(text)
    if balanced:
        candidates.append(balanced)
    # Top-level JSON ARRAY responses (batched contracts, 2026-08-23): a balanced-object scan
    # would return only the first row; recover the whole array. The array candidate outranks
    # the balanced object only when the array opens before any object does (a bare-array
    # reply with prose around it); an array nested inside an object never wins.
    arr_start = text.find("[")
    obj_start = text.find("{")
    if arr_start >= 0:
        depth = 0
        for i in range(arr_start, len(text)):
            if text[i] == "[": depth += 1
            elif text[i] == "]":
                depth -= 1
                if depth == 0:
                    cand = text[arr_start:i + 1]
                    if obj_start < 0 or arr_start < obj_start:
                        candidates.insert(max(0, len(candidates) - 1) if balanced else len(candidates), cand)
                    else:
                        candidates.append(cand)
                    break
    for cand in candidates:
        try:
            return json.loads(cand)
        except json.JSONDecodeError:
            continue
    raise ModelInvocationError("model response contains no parseable JSON object")


class ModelInvocationError(RuntimeError):
    """A transport/CLI failure or an unusable envelope — the run driver may retry once."""


class ModelParseError(ModelInvocationError):
    """The envelope arrived but its result yielded no parseable JSON. Carries the call's
    usage and session id so the truncation fallback (ADDENDUM-01 §3) can decide and resume,
    and the call's served-model receipt (seldon AD-035 R6), which the gate had already passed."""

    def __init__(self, msg: str, usage: dict | None = None, session_id: str | None = None,
                 receipt: dict | None = None):
        self.usage = usage or {}
        self.session_id = session_id
        self.receipt = receipt
        super().__init__(msg)


class ModelRateLimitError(ModelInvocationError):
    """The CLI reported a rate-limit / overload / usage-cap rejection (task 2026-08-26
    overnight-burn rule): the reservation was RELEASED, the driver should sleep and retry;
    after 6 consecutive occurrences a lane STOPs with `rate_limited`, not `failed`."""


# Markers observed in CLI rate-limit / overload / subscription-cap rejections. Matched
# case-insensitively against stderr+stdout of a non-zero exit only.
_RATE_LIMIT_MARKERS = ("rate limit", "rate_limit", "rate-limit", "overloaded", "529",
                       "usage limit", "hit your limit", "out of extended usage",
                       "too many requests")


def _looks_rate_limited(text: str) -> bool:
    low = (text or "").lower()
    return any(m in low for m in _RATE_LIMIT_MARKERS)


# CLI outcome classes (task 2026-09-02_spend_guard_exit1_and_state_merge, defect 1). A
# `claude -p` result is classified into exactly one of these BEFORE its reservation is
# settled or released, so the ledger can say what each booked token was booked for.
CLI_SUCCESS = "success"                      # exit 0
CLI_RATE_LIMITED = "rate_limited"            # exit != 0, a rate-limit/overload/cap marker
CLI_EMPTY_FAILURE = "empty_failure"          # exit != 0, NOTHING on stdout or stderr
CLI_ERROR_WITH_OUTPUT = "error_with_output"  # exit != 0, something on either stream


def classify_cli_outcome(returncode: int, stdout: str | None, stderr: str | None) -> str:
    """Pure classifier of a `claude -p` completion. Rate-limit markers win over the
    empty/with-output split because a marker IS output. `empty_failure` requires both
    streams blank (None or whitespace-only): observed 2026-09-02 03:01Z, five consecutive
    exit-1s with empty stderr and empty stdout as the Max usage window closed, ~3 s each —
    no envelope, no error text, nothing that could have been billed. Anything else on a
    non-zero exit is `error_with_output` and keeps the conservative settle-at-estimate rule
    (a failed CLI that printed something may have consumed tokens server-side)."""
    if returncode == 0:
        return CLI_SUCCESS
    if _looks_rate_limited((stderr or "") + (stdout or "")[:2000]):
        return CLI_RATE_LIMITED
    if not (stdout or "").strip() and not (stderr or "").strip():
        return CLI_EMPTY_FAILURE
    return CLI_ERROR_WITH_OUTPUT


# Module attribute so tests record the back-off instead of serving it.
_sleep = time.sleep


#: Outcome classes a parsed envelope can still fail on (seldon AD-035 R6, task MODEL-001). They
#: extend the CLI classes above at the same point in the flow: the envelope is classified
#: BEFORE its reservation is settled, so the ledger says what each booked token was booked for.
#: Both are measured spends (the call ran), so both settle at the envelope's tokens.
CLI_MODEL_SUBSTITUTED = models.SUBSTITUTED       # "model_substituted": served != requested
CLI_MODEL_SIDE_CALL = "model_side_call"          # served == requested, but other models too


class ModelSubstitutionError(ModelConfigError, models.ModelSubstituted):
    """The envelope reports a model other than the pinned one (e.g. a classifier reroute).
    The driver records the substitution and STOPs; the unit's output is discarded unparsed,
    never substituted.

    It is also seldon's ``ModelSubstituted`` (AD-035 R6), so a caller written against the
    accessor catches it too. ``reason`` is ``model_substituted`` when the served model is not
    the requested one, and ``model_side_call`` when the requested model answered but the
    envelope lists other models beside it: this repo's invariant 5 ("exactly the pinned
    model") is stricter than R6's minimum, and R6 does not repeal it. ``receipt`` is R6's
    ``{requested, served, side_models, ok}``."""

    def __init__(self, expected: str, observed: list, receipt: dict | None = None,
                 reason: str = CLI_MODEL_SUBSTITUTED):
        self.expected = expected
        self.observed = observed
        self.reason = reason
        self.receipt = dict(receipt) if receipt is not None else {
            "requested": expected, "served": None, "side_models": list(observed), "ok": False}
        RuntimeError.__init__(self, f"{reason}: expected {expected} but envelope reports "
                                    f"models {observed} (seldon AD-035 R6)")


def launch_spec(config: dict) -> dict:
    """The seldon launch spec for a stub config's role, refusing a config that has no role or
    whose `model_id` is not that role's lock id (a caller still setting ids by hand)."""
    role = config.get("role")
    if not role:
        raise ModelConfigError(
            "stub config names no `role`; build it with load_model_config() or "
            "config_for_role(role) (seldon AD-035 R1, R4)")
    try:
        spec = models.launch_spec(role)
    except models.ModelsError as exc:
        raise ModelConfigError(f"{exc} (seldon AD-035 R1)") from exc
    configured = config.get("model_id")
    if configured is not None and configured != spec["model"]:
        raise ModelConfigError(
            f"config model_id {configured!r} is not role {role!r}'s lock id {spec['model']!r}: "
            f"retarget with config_for_role(role), never by setting a model id (seldon AD-035 "
            f"R3, R4); the lock: {models.lock_quote()}")
    return spec


def invoke(doc_id: str, source_text: str, prompt: str | None = None,
           timeout: int = 1800, config: dict | None = None,
           resume_session_id: str | None = None, parse_json: bool = True) -> dict:
    """Extract one document via ``claude -p`` on the subscription OAuth (no API key).

    Returns ``{output, model_id, usage, cost_usd, duration_ms, raw_result}`` where ``output``
    is the parsed extraction envelope. Raises ModelConfigError on a forbidden credential or a
    fallback model; ModelInvocationError on transport/CLI failure or an unparseable envelope.
    Never passes ``--bare`` (that path demands an API key).

    ``parse_json=False`` (task 2026-09-02_g1_eval_probe_family_v0 step 1) returns the
    envelope's result text as ``output`` unparsed: the G1 observed leg elicits prose
    restatements through this same choke point — same DD-007 gate, same DD-022
    reservation, same model-identity gate — and scores the prose deterministically
    downstream. Nothing before this line changes with the flag.
    """
    config = config or load_model_config()
    guard_no_api_key()
    # The empty-failure back-off policy is read BEFORE the first reservation so a missing
    # or malformed policy is a config error at the first call, not mid-burn at the first
    # failure (task 2026-09-02_spend_guard_exit1_and_state_merge).
    backoff, max_retries = spend.empty_failure_policy()

    # Seldon AD-035 R3: the role's lock id, the lock's CLI (never `claude` on PATH, whose
    # auto-updated alias table is what pinned a model generation unrecorded), the
    # switchModelsOnFlag settings, the role's effort, and all four family ids in the child's
    # environment so the CLI's own background work follows the lock too. Resolved before the
    # first reservation: a config fault refuses without booking anything.
    spec = launch_spec(config)
    model_id = spec["model"]
    child_env = {**os.environ, **spec["env"]}
    prompt = prompt if prompt is not None else build_prompt(doc_id, source_text, config)

    cmd = [spec["cli_path"], "-p", *spec["args"],
           "--output-format", _OUTPUT_FORMAT, "--allowed-tools", _EMPTY_ALLOWLIST]
    if resume_session_id:
        # Continue an existing headless session (task 2026-08-23_batched_repair_resume,
        # DD-019): prior turns — e.g. a document sent once per doc — become cached prefix,
        # which separate -p invocations cannot share (measured: 3 calls, 0 prefix reuse).
        cmd += ["--resume", resume_session_id]

    ledger = spend.default_ledger()
    attempt = 0
    while True:
        # Preemptive shared spend guard (DD-022) — the second gate at this choke point,
        # beside the DD-007 API-key gate above. Reserve BEFORE dispatch against the
        # flock-guarded ledger; no reservation, no subprocess. An undeclared run refuses too
        # — there is no unmetered path. Callers treat SpendRefusalStop as a clean stop
        # (exit 0), the same contract as the STOP file and cap exhaustion. A retry after an
        # `empty_failure` reserves afresh, so it is bounded by the same ceilings.
        granted = ledger.reserve(spend.current_run_id(), doc_id=doc_id)
        if isinstance(granted, spend.Refusal):
            raise spend.SpendRefusalStop(granted)
        try:
            proc = subprocess.run(cmd, input=prompt, capture_output=True, text=True,
                                  timeout=timeout, cwd=_hermetic_cwd(), env=child_env)
        except subprocess.TimeoutExpired as exc:
            # The CLI DID dispatch; tokens may have been consumed server-side with no
            # envelope to measure them. Settle at the estimate (conservative: capacity stays
            # consumed; never a content-derived guess) rather than release.
            ledger.settle(granted, granted.estimate_tokens, settled_as_estimate=True,
                          outcome_class="timeout")
            raise ModelInvocationError(
                f"claude -p timed out after {timeout}s for {doc_id}") from exc
        except OSError as exc:
            # The Claude Code CLI auto-updates in place; for a few seconds the `claude`
            # symlink does not resolve (observed 2026-08-22 twice, killing two judging
            # streams). That is a transient per-call failure the driver should retry, not a
            # crash. The CLI never ran, so the reservation is released — capacity restored.
            ledger.release(granted, reason=f"cli_unavailable: {exc}",
                           outcome_class="cli_unavailable")
            raise ModelInvocationError(f"claude CLI unavailable for {doc_id}: {exc}") from exc
        outcome = classify_cli_outcome(proc.returncode, proc.stdout, proc.stderr)
        if outcome == CLI_EMPTY_FAILURE and attempt < max_retries:
            # Nothing on either stream: nothing that could have been billed. RELEASE the
            # reservation, back off on the configured schedule, and retry under a fresh
            # reservation. The 2026-09-02 relaunch measured normal per-chunk usage right
            # after such failures, and a Haiku liveness call succeeded with no change to
            # the machine — the failure is the session/usage window, not the call.
            ledger.release(granted, reason="empty_failure", outcome_class=CLI_EMPTY_FAILURE)
            delay = backoff[min(attempt, len(backoff) - 1)]
            print(f"  {doc_id}: claude -p exit {proc.returncode} with empty stdout+stderr "
                  f"(empty_failure {attempt + 1}/{max_retries}); released, sleeping {delay}s",
                  flush=True)
            _sleep(delay)
            attempt += 1
            continue
        break

    if outcome == CLI_RATE_LIMITED:
        # Overnight-burn rule (task 2026-08-26): a rate-limit/overload rejection consumed
        # no meaningful tokens — RELEASE the reservation (capacity restored) and raise a
        # typed error so drivers back off instead of counting a failure.
        ledger.release(granted, reason="rate_limited", outcome_class=CLI_RATE_LIMITED)
        raise ModelRateLimitError(
            f"claude -p rate-limited/overloaded for {doc_id}: {proc.stderr.strip()[:200]}")
    if outcome == CLI_EMPTY_FAILURE:
        # Retry cap reached: the conservative rule returns. Settle at the estimate, and raise
        # the plain invocation error so the driver's systemic-failure streak counts it.
        ledger.settle(granted, granted.estimate_tokens, settled_as_estimate=True,
                      outcome_class=CLI_EMPTY_FAILURE)
        raise ModelInvocationError(
            f"claude -p exited {proc.returncode} for {doc_id} with empty stdout+stderr "
            f"(empty_failure) {max_retries + 1} times; settled at the estimate")
    if outcome == CLI_ERROR_WITH_OUTPUT:
        # A failed CLI that printed something may have consumed tokens server-side: settle
        # at the estimate (never a content-derived guess). Unchanged by the reclassification.
        ledger.settle(granted, granted.estimate_tokens, settled_as_estimate=True,
                      outcome_class=CLI_ERROR_WITH_OUTPUT)
        raise ModelInvocationError(
            f"claude -p exited {proc.returncode} for {doc_id}: {proc.stderr.strip()[:300]}")

    try:
        envelope = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        ledger.settle(granted, granted.estimate_tokens, settled_as_estimate=True,
                      outcome_class="unparseable_envelope")
        raise ModelInvocationError(f"unparseable claude -p envelope for {doc_id}: {exc}") from exc

    # The served-model receipt (seldon AD-035 R6), taken from the envelope before anything
    # else reads it, and classified with the CLI outcome classes: an error envelope keeps its
    # old class (the receipt is still recorded), a served model other than the requested one
    # is `model_substituted`, and a side model beside the requested one is `model_side_call`.
    receipt = models.receipt(model_id, envelope)
    model_usage = envelope.get("modelUsage") or {}
    if envelope.get("is_error"):
        envelope_class = CLI_SUCCESS
    elif not receipt["ok"]:
        envelope_class = CLI_MODEL_SUBSTITUTED
    elif receipt["side_models"] or len(model_usage) != 1:
        envelope_class = CLI_MODEL_SIDE_CALL
    else:
        envelope_class = CLI_SUCCESS

    # Settle at the envelope's measured token count the moment it is parseable, before any
    # content gate can raise — a substituted or error envelope still spent real tokens. The
    # settle record is the call's durable record, so the receipt goes into it.
    usage = (model_usage.get(model_id) or next(iter(model_usage.values()), {}))
    actual = sum(int(usage.get(k, 0) or 0) for k in
                 ("inputTokens", "outputTokens", "cacheCreationInputTokens",
                  "cacheReadInputTokens"))
    if actual:
        ledger.settle(granted, actual, outcome_class=envelope_class, model_receipt=receipt)
    else:
        # Envelope lacks the fields the stub records as tokens: settle at the estimate and
        # flag it — never estimate from content (task rule), never book zero for a real call.
        ledger.settle(granted, granted.estimate_tokens,
                      settled_as_estimate=True, usage_fields_missing=True,
                      outcome_class=("usage_fields_missing" if envelope_class == CLI_SUCCESS
                                     else envelope_class),
                      model_receipt=receipt)

    if envelope.get("is_error"):
        raise ModelInvocationError(f"claude -p reported error for {doc_id}: {envelope}")

    if envelope_class != CLI_SUCCESS:
        # A different or extra model served the call (classifier reroute / fallback / side
        # call). Raise the substitution gate so the driver records it and STOPs: the output is
        # never parsed and never used.
        raise ModelSubstitutionError(expected=model_id, observed=list(model_usage),
                                     receipt=receipt, reason=envelope_class)

    if parse_json:
        try:
            output = _extract_json(envelope.get("result", ""))
        except ModelInvocationError as exc:
            # carry usage + session so the truncation fallback can decide and resume (§3)
            raise ModelParseError(str(exc), usage=model_usage.get(model_id, {}),
                                  session_id=envelope.get("session_id"),
                                  receipt=receipt) from exc
    else:
        output = envelope.get("result", "")
    return {
        "output": output,
        "model_id": model_id,
        "role": spec["role"],
        "model_receipt": receipt,
        "usage": model_usage.get(model_id, {}),
        "cost_usd": envelope.get("total_cost_usd"),
        "duration_ms": envelope.get("duration_ms"),
        "session_id": envelope.get("session_id"),
        "raw_result": envelope.get("result", ""),
        "spend_run_id": granted.run_id,
        "spend_reservation_id": granted.reservation_id,
    }


# --- Truncation fallback: per-layer emission (overnight burn ADDENDUM-01 §3) -------------
# A dense document can blow the single-pass output budget: observed 2026-08-27, 67,057
# output tokens with no recoverable envelope layers (aidrin pilot). Truncation is a STATUS,
# never a silent zero: the wrapper below detects it (no extraction layers + outputTokens
# above model_config `truncation_suspect_tokens`) and retries ONCE in per-layer emission
# mode — same headless session (the document is already cached prefix, DD-019 §3), three
# resumed turns, each parsed independently, merged into one output with
# `emission_mode: per_layer`. Single-pass stays the default; per-layer is fallback only.

_EXTRACTION_LAYERS = ("concepts", "definitions", "claims", "instruments", "measures",
                      "standards", "frameworks", "practices", "tools", "platforms",
                      "edges", "cites", "proposed_relationships")
_LAYER_TURNS = (
    ("nodes_general", ("concepts", "definitions", "claims", "standards", "frameworks",
                       "practices", "tools", "platforms")),
    ("instruments_measures", ("instruments", "measures")),
    ("edges", ("edges", "cites", "proposed_relationships")),
)


def has_extraction_layers(output) -> bool:
    return isinstance(output, dict) and any(
        isinstance(output.get(k), list) and output.get(k) for k in _EXTRACTION_LAYERS)


def _out_tokens(usage: dict | None) -> int:
    return int((usage or {}).get("outputTokens", 0) or 0)


def _layer_turn_prompt(turn_name: str, layers: tuple, prior_note: str) -> str:
    keys = ", ".join(f'"{k}": [...]' for k in layers)
    return (
        "Your previous single-pass output could not be parsed (it appears truncated). "
        "Re-emit your extraction for the SAME document in parts, same rules and same "
        f"format as before. THIS turn, emit ONLY these layers as one strict JSON object "
        f"{{{keys}}} — no prose, no fences, nothing else.{prior_note}")


def invoke_with_layer_fallback(doc_id: str, source_text: str, timeout: int = 1800,
                               config: dict | None = None) -> dict:
    """``invoke`` plus the ADDENDUM-01 truncation fallback. Returns the usual meta dict;
    when the fallback ran, ``emission_mode`` is ``per_layer``, ``parse_failed_truncated``
    is True, ``usage`` sums all calls, and ``raw_result`` concatenates the turns."""
    config = config or load_model_config()
    suspect_floor = int(config.get("truncation_suspect_tokens", 40000))
    try:
        meta = invoke(doc_id, source_text, timeout=timeout, config=config)
        if has_extraction_layers(meta["output"]):
            return meta
        truncated = _out_tokens(meta.get("usage")) > suspect_floor
        session_id, base_usage = meta.get("session_id"), dict(meta.get("usage") or {})
        base_raw = meta.get("raw_result") or ""
        base_receipt = meta.get("model_receipt")
        if not truncated:
            return meta          # small-but-empty output is a real (bad) extraction, not truncation
    except ModelParseError as exc:
        if _out_tokens(exc.usage) <= suspect_floor or not exc.session_id:
            raise
        session_id, base_usage, base_raw = exc.session_id, dict(exc.usage), ""
        base_receipt = exc.receipt
    # per-layer retry: three resumed turns against the cached document prefix
    merged: dict = {}
    usages = [base_usage]
    raws = [base_raw]
    receipts = [r for r in (base_receipt,) if r]
    for turn_name, layers in _LAYER_TURNS:
        prior_note = ""
        if turn_name == "edges":
            prior_note = (" Edges may only reference node ids you emitted in the previous "
                          "two turns (plus the document id).")
        meta_t = invoke(f"{doc_id}#layer:{turn_name}", "",
                        prompt=_layer_turn_prompt(turn_name, layers, prior_note),
                        timeout=timeout, config=config, resume_session_id=session_id)
        session_id = meta_t.get("session_id") or session_id
        usages.append(meta_t.get("usage") or {})
        raws.append(meta_t.get("raw_result") or "")
        receipts.append(meta_t["model_receipt"])
        out_t = meta_t["output"] if isinstance(meta_t["output"], dict) else {}
        for k in layers:
            if isinstance(out_t.get(k), list):
                merged[k] = out_t[k]
    total_usage = {}
    for k in ("inputTokens", "outputTokens", "cacheCreationInputTokens", "cacheReadInputTokens"):
        total_usage[k] = sum(int((u or {}).get(k, 0) or 0) for u in usages)
    return {
        "output": merged,
        "model_id": receipts[-1]["requested"],
        "role": config.get("role"),
        # One receipt per call that made up this output (AD-035 R6); the last stands for all
        # in `model_receipt`, because a substituted turn raised before it could be appended.
        "model_receipt": receipts[-1],
        "model_receipts": receipts,
        "usage": total_usage,
        "cost_usd": None,
        "duration_ms": None,
        "session_id": session_id,
        "raw_result": "\n\n---PER_LAYER_TURN---\n\n".join(r for r in raws if r),
        "emission_mode": "per_layer",
        "parse_failed_truncated": True,
    }
