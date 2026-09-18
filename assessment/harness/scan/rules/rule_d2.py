"""D2 v1 — the host's robots.txt declares, as a `Content-Signal`, its terms for AI training and
AI input.

`cc_tasks/2026-09-18_schema_field_rules.md` decision 6. Pre-registered before cycle 5
(2026-10-05), which is the first cycle that judges it.

**The field.** `corpus/kernel/cloudflare-content-signals-policy.md` (doc_id
`cloudflare-content-signals-policy`): "The Content-Signal directive works by signaling your
preference of either allowing (yes) or disallowing (no) certain categories of AI actions", with
`ai-train` "Training or fine-tuning AI models" and `ai-input` "Inputting content into one or more
AI models (e.g., retrieval augmented generation, grounding, or other real-time taking of content
for generative AI search answers)". The indicator — "Terms address model training/retrieval use
explicitly" — names exactly those two uses, so the rule requires BOTH to be declared, yes or no.
The policy's own clause (c) is why one is not enough: "If the website operator does not include
a content signal for a corresponding use, the website operator neither grants nor restricts
permission via content signal with respect to the corresponding use" — an undeclared use is not
addressed.

**A directive, not a policy** (decision 6). Declared `yes` and declared `no` both pass: the rule
reads that the terms ADDRESS the use, not what they say about it. Whether a crawler honours
them is A12's declared-versus-enforced question and is not re-measured here.

**The verdict**, over the directives that apply to the product's path (unscoped, or scoped to a
path it lies under):

* no robots.txt served, or none applies, or one of the two uses is undeclared → `fail`;
* an applying directive names a category or a value the policy does not define → `fail`;
* both uses declared → `pass`, quoting the declarations.

**What is NOT measured**, and every verdict says so: the prose terms of use, which stay a judged
reading (the node's `tier_note`), and whether the declaration is enforced.

**The subject is the product's path** (`MEASURES = "product"`), following A4, which reads the
same file for the same path; the file is A4's observation (`CONSUMES`), enriched at collection
with `v2clauses.content_signals`. `fail` is an absence claim.
"""
from __future__ import annotations

from . import _common as c

RULE_ID, LEG = "RULE-D2-v1", "D2"
CONSUMES = ("A4",)
CLAIM = "absence"
MEASURES = "product"

#: The `content_signal` scheme this rule understands (`v2clauses.CONTENT_SIGNAL_SCHEME`).
SCHEME = 1

UNMEASURED = ("not measured: the prose terms of use, which stay a judged reading, and whether "
              "the declaration is enforced, which is A12's")


def judge(observations: list, params: dict):
    obs = [o for o in observations if o.leg == "A4"]
    if not obs:
        return c.empty(RULE_ID, LEG, params)
    if c.only_errors(obs, params):
        return c.make(RULE_ID, LEG, obs, "error",
                      f"robots.txt could not be observed: {obs[0].error_class}", params)
    probe = obs[0]
    blind = c.unobserved_error(RULE_ID, LEG, obs, probe, params, "robots.txt")
    if blind:
        return blind
    spec = params["content_signal"]
    required = list(spec["required"])
    parsed = probe.parsed or {}
    if not parsed.get("present"):
        return c.make(RULE_ID, LEG, obs, "fail",
                      f"no robots.txt served, so the host "
                      f"declares no Content-Signal for {' or '.join(f'`{r}`' for r in required)}"
                      f"; {UNMEASURED}", params)
    block = parsed.get("content_signal")
    if not isinstance(block, dict) or block.get("scheme") != SCHEME:
        return c.make(RULE_ID, LEG, obs, "error",
                      f"robots.txt at {probe.target_url} was served and carries no "
                      f"Content-Signal extraction: it was collected before `content_signal` "
                      f"existed, so the declaration cannot be read from it", params)
    applying = [x for x in block.get("directives") or [] if x.get("applies")]
    known, values = set(spec["categories"]), set(spec["values"])
    odd = sorted({f"{k}={v}" for x in applying for k, v in (x.get("signals") or {}).items()
                  if k not in known or v not in values}
                 | {m for x in applying for m in x.get("malformed") or []})
    if odd:
        return c.make(RULE_ID, LEG, obs, "fail",
                      f"robots.txt at {probe.target_url} carries a Content-Signal that names "
                      f"a category or value the Content Signals Policy does not define: "
                      f"{', '.join(odd)}; {UNMEASURED}", params)
    declared = {k: v for x in applying for k, v in (x.get("signals") or {}).items()
                if k in required}
    missing = [r for r in required if r not in declared]
    if missing:
        others = len(block.get("directives") or []) - len(applying)
        scoped = (f" ({others} directive(s) scoped to other paths)" if others else "")
        return c.make(RULE_ID, LEG, obs, "fail",
                      f"robots.txt at {probe.target_url} "
                      f"declares no Content-Signal for {' or '.join(f'`{m}`' for m in missing)} "
                      f"on the product path{scoped}; under the policy an undeclared use is "
                      f"neither granted nor restricted; {UNMEASURED}", params)
    said = ", ".join(f"{k}={declared[k]}" for k in required)
    return c.make(RULE_ID, LEG, obs, "pass",
                  f"robots.txt at {probe.target_url} declares a Content-Signal for both uses on "
                  f"the product path ({said}); {UNMEASURED}", params)
