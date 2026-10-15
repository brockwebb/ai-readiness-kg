#!/usr/bin/env python3
"""The planted-sentence and unsupported-sentence checks on the diagnostic preface. **Model spend.**

`cc_tasks/2026-10-15_readiness_diagnostic_package.md` Part C: the planted-sentence and
unsupported-sentence checks (role `critic`) run on the preface as they ran on the summary
(`scripts/summary_verify.py --check`). One call to the checker (role `critic`, a third family
from the author and the hostile reader): it sees every factual sentence of the preface with a
set of planted false controls interleaved, and the CLAIMS (what the preface is entitled to say,
from the computed result-token values and the published method), and labels each sentence
`supported`, `unsupported` or `no_factual_content`. The run FAILS, and no verdict is trusted,
unless every planted control is caught as `unsupported`. A real sentence the checker does not
support is reported for the author to fix, never reworded by a model.

**Checkpoint** (`~/GitHub/CLAUDE.md` §15), reusing `scripts/dcat_faq_run.py`: unit = one call;
key = sha1(kind | input sha | model | template sha). Re-running is the resume.

    /opt/anaconda3/bin/python3 scripts/preface_critic_check.py --dry-run
    /opt/anaconda3/bin/python3 scripts/preface_critic_check.py --check
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
for _p in ("", "scripts"):
    if str(REPO / _p) not in sys.path:
        sys.path.insert(0, str(REPO / _p))

import dcat_faq_run as FR  # noqa: E402
import diagnostic_package_build as B  # noqa: E402
import instrument as INS  # noqa: E402
import instrument_read as IR  # noqa: E402

GENERATOR = "scripts/preface_critic_check.py"
TASK = INS.TASK
RUN_DIR = REPO / "reports" / "diagnostic" / "critic_run"

TEMPLATE = """You are an adversarial fact checker for the preface of a public document. Your job is
to find every sentence below that says something the CLAIMS do not support. Do not pass a sentence
to be agreeable and do not fail one to look diligent. A sentence may read as confident or well
written; that is evidence about its writer, not about the claims.

Label each numbered sentence exactly one of:
- "supported": every factual part of the sentence (each number, each "one"/"every"/"no"/"only",
  each statement of what the client does or never does) is stated by one or more CLAIMS below, or
  follows from them directly with no new fact. Give the ids of the claims that support it.
- "unsupported": any factual part is not stated by the claims, contradicts them, or changes a
  number or a quantifier. Say which part, in the reason.
- "no_factual_content": the sentence states no checkable fact (it frames, defines a term, or is
  a heading).

Return ONLY a JSON array, one object per sentence in order, no prose and no code fence:
[{{"n": 1, "label": "supported"|"unsupported"|"no_factual_content", "claims": ["..."], "reason": "..."}}, ...]

CLAIMS (what the preface is entitled to say)
{claims}

SENTENCES
{sentences}"""
TEMPLATE_SHA = FR.sha(TEMPLATE)


def claims(values: dict) -> list[dict]:
    """What the preface is entitled to say: the computed result-token values and the published
    method (DN-016; the harness configuration)."""
    v = values
    return [
        {"id": "C_checks", "text": f"The diagnostic runs {v['checks_total']} checks; each check is one "
         "published question about whether a machine client can reach, read and use the data, and the "
         "public client that runs them is the least privileged client a member of the public has."},
        {"id": "C_bodies", "text": f"It covers {v['bodies_total']} federal statistical bodies, with "
         f"{v['flagships_total']} reference hosts beside them, over {v['surfaces_total']} surfaces."},
        {"id": "C_rate", "text": f"The public client makes one request per check per surface and holds "
         f"to {v['rate_per_second_per_host']} request per second per host."},
        {"id": "C_crawl", "text": f"It waits longer when a host's robots.txt asks, up to a ceiling of "
         f"{v['crawl_delay_ceiling_s']} seconds, above which it records the surface as not measured."},
        {"id": "C_robots", "text": f"It honours robots.txt; on the cycle of record it did not fetch "
         f"{v['surfaces_robots_kept_out']} surfaces because robots.txt told it not to."},
        {"id": "C_ua", "text": f"It identifies itself in every request by one fixed user-agent string "
         f"({v['user_agent']}), so a security team can find every request it made in its own logs."},
        {"id": "C_rung1", "text": "At the first rung it presents no credentials of any kind."},
        {"id": "C_rung2", "text": "At the second rung it is the same client registered as any member of "
         "the public registers, presenting only a key obtained by open registration — a good-faith "
         "handshake, not a barrier. Rung two is specified now and measured in its own later cycle, and no "
         "rung-two result is shown before one exists. A refusal at rung one with a pass at rung two is "
         "reported as both, because both are true about the public experience."},
        {"id": "C_ladder", "text": "The public client runs on a ladder of two rungs: a first rung and a "
         "second rung, and no other."},
        {"id": "C_never", "text": "It submits no form, solves no CAPTCHA, signs in nowhere, runs none of "
         "a page's scripts, and fetches nothing beyond a page's own headers and body: no files a script "
         "would build, and no addresses reached only through a tool; it reads the page as first served."},
        {"id": "C_nocred", "text": "It takes no credential a citizen cannot obtain; a rung that needs an "
         "agency to grant what a citizen cannot get is reported as not measured, refused."},
        {"id": "C_states", "text": "A check comes back in one of four states. A pass means every one of "
         "the agency's data pages that was looked at met the check; a fail means every one did not; a "
         "partial means some met it and some did not; not measured means the client could not look at "
         "one or more pages, so that neither 'every page passes' nor 'every page fails' is established. "
         "Not measured has three reasons: the host refused the client; the client's own robots.txt "
         "compliance kept it out; or an absence could not be confirmed, or a server or network error "
         "occurred. Not measured is never a fail."},
        {"id": "C_notask", "text": "The diagnostic does not test whether an agent completed a task; that "
         "is a later level of the framework."},
        {"id": "C_notleague", "text": "It is not a public league table and not a campaign to open any "
         "site. The results go to the agency, not the public. A check resting on a rule the project chose "
         "rather than a published standard is shown for transparency and not scored as a finding. The "
         "method is published here in full so that a reader can see exactly what was and was not "
         "measured, and argue with it."},
    ]


#: Planted false controls (methodology 7.6): sentences the checker MUST catch as unsupported,
#: each contradicting a claim. If any is passed, the checker is not calibrated and no verdict holds.
CONTROLS = [
    "The public client signs in with an agency-issued username and password before it fetches a data page.",
    "When a page needs it, the client runs the page's scripts and fills in the site's search form to load the data.",
    "The diagnostic publishes a public ranking of the agencies from best to worst.",
]


def preface_sentences() -> list[str]:
    """The preface's factual sentences, from the resolved source (the rendered content)."""
    values = B.compute_values()
    pf = B.load_preface(values)
    blocks = [pf["what_it_is"], *pf["how_it_behaves"], *pf["what_it_never_does"],
              pf["four_states_note"], pf["two_rungs_note"], pf["what_it_is_not"],
              pf["not_a_league_table"]]
    sents = []
    for b in blocks:
        for s in re.split(r"(?<=[.;])\s+", str(b).strip()):
            s = s.strip()
            if len(s) > 12:
                sents.append(s)
    return sents


def interleave(reals: list[str], controls: list[str]) -> tuple[list[str], list[int]]:
    """Controls spread evenly through the reals; returns the merged list and the control indices."""
    out, ctrl_idx = [], []
    step = max(1, len(reals) // (len(controls) + 1))
    ci = 0
    for i, r in enumerate(reals):
        out.append(r)
        if ci < len(controls) and (i + 1) % step == 0:
            out.append(controls[ci])          # control's 1-based position is now len(out)
            ctrl_idx.append(len(out))
            ci += 1
    while ci < len(controls):
        out.append(controls[ci])
        ctrl_idx.append(len(out))
        ci += 1
    return out, ctrl_idx


def parse_labels(text: str, n: int) -> list:
    obj = FR._json_payload(text)
    if not isinstance(obj, list) or len(obj) != n:
        raise ValueError(f"expected a JSON array of {n} labels, got {type(obj).__name__} len "
                         f"{len(obj) if isinstance(obj, list) else '?'}")
    out = []
    for i, o in enumerate(obj):
        lab = str((o or {}).get("label", "")).lower()
        if lab not in ("supported", "unsupported", "no_factual_content"):
            raise ValueError(f"sentence {i+1}: bad label {lab!r}")
        out.append({"n": i + 1, "label": lab, "claims": [str(x) for x in (o.get("claims") or [])],
                    "reason": str(o.get("reason") or "")})
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    cfg = INS.load_config()
    rc = cfg["critic"]
    values = B.compute_values()
    cl = claims(values)
    reals = preface_sentences()
    merged, ctrl_idx = interleave(reals, CONTROLS)
    claims_block = "\n".join(f"- [{c['id']}] {c['text']}" for c in cl)
    sent_block = "\n".join(f"{i+1}. {s}" for i, s in enumerate(merged))
    prompt = TEMPLATE.format(claims=claims_block, sentences=sent_block)

    if a.dry_run:
        print(f"critic role {rc['role']}; {len(reals)} real sentences, {len(CONTROLS)} controls at "
              f"{ctrl_idx}; {len(merged)} total")
        print("--- prompt ---")
        print(prompt)
        return 0

    RUN_DIR.mkdir(parents=True, exist_ok=True)
    cons, model = IR.consumer(rc, os.environ.get("INSTRUMENT_READ_SCRIPTED_CONSUMER"))
    ck = FR.Checkpoint(RUN_DIR / "checkpoint.jsonl")
    uid = FR.unit_id("critic", "preface", FR.sha(prompt), model, TEMPLATE_SHA)
    prior = [r for r in ck.read() if r["unit_id"] == uid]
    done = next((r for r in prior if r["status"] == "done"), None)
    if done:
        labels = done["parsed"]
    else:
        attempt = max((p["attempt"] for p in prior), default=0)
        labels = None
        while attempt < rc["max_attempts"]:
            attempt += 1
            comp, err = FR.call(cons, model, prompt, f"critic.preface.a{attempt}")
            if comp is None:
                ck.append({"unit_id": uid, "status": "error", "error": err, "attempt": attempt,
                           "ts": FR._now()})
                continue
            (RUN_DIR / "raw").mkdir(exist_ok=True)
            (RUN_DIR / "raw" / f"{uid}.a{attempt}.json").write_text(json.dumps(
                {"prompt": prompt, "response_text": comp.text, "usage": comp.usage,
                 "model_receipt": getattr(comp, "receipt", None)}, indent=1, ensure_ascii=False),
                encoding="utf-8")
            try:
                labels = parse_labels(comp.text, len(merged))
                ck.append({"unit_id": uid, "status": "done", "attempt": attempt, "model_id": model,
                           "parsed": labels, "usage": comp.usage, "tokens": FR._tokens(comp.usage),
                           "ts": FR._now()})
                break
            except (ValueError, KeyError, TypeError) as exc:
                ck.append({"unit_id": uid, "status": "unparsed", "attempt": attempt,
                           "error": str(exc)[:300], "ts": FR._now()})
        if labels is None:
            print(json.dumps({"stopped": "critic did not return parseable labels", "model": model}))
            return 3

    by_n = {x["n"]: x for x in labels}
    controls_caught = [i for i in ctrl_idx if by_n.get(i, {}).get("label") == "unsupported"]
    controls_missed = [i for i in ctrl_idx if i not in controls_caught]
    unsupported_reals = [{"n": x["n"], "sentence": merged[x["n"] - 1], "reason": x["reason"]}
                         for x in labels if x["label"] == "unsupported" and x["n"] not in ctrl_idx]
    result = {
        "generated_by": GENERATOR, "task": TASK, "model_id": model,
        "sentences": len(merged), "real": len(reals), "controls": len(CONTROLS),
        "control_indices": ctrl_idx, "controls_caught": controls_caught,
        "controls_missed": controls_missed, "unsupported_real_sentences": unsupported_reals,
        "calibrated": not controls_missed,
    }
    (RUN_DIR / "critic_result.json").write_text(json.dumps(result, indent=1, ensure_ascii=False) + "\n",
                                                encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("model_id", "real", "controls", "controls_caught",
                                              "controls_missed", "unsupported_real_sentences",
                                              "calibrated")}, indent=1, ensure_ascii=False))
    if controls_missed:
        print("CONTROL MISSED: the checker is not calibrated; no verdict is trusted.")
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
