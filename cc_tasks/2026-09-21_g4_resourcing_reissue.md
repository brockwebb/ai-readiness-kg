# CC Task: G4 re-sourcing, release date from the record, grounding punctuation count (re-issue with a Network header that parses), plus the checkpoint rule in this repo's docs

**Date:** 2026-09-21
**Project:** ai-readiness-kg
**Authored by:** Desktop session. Re-issues `cc_tasks/2026-09-20_g4_resourcing_release_date_grounding_fold.md` (`cd1e5b2d`, superseded by this task), which the dispatcher correctly refused for 5 hours as `network_undeclared: c5`: Desktop wrote its Network header as prose, not in the grammar. `dispatch_stuck` fired at 21:51:36Z on the third pass, as built the day before.
**Implements:** as the superseded file states, plus `~/GitHub/CLAUDE.md` §15 (2026-09-20).
**Framework layer served (DN-005 §5 rule 1):** §2.1, the validity layer, and the published views.
**Fulfils:** its own ResearchTask (`seldon cc register`). Launched by the dispatcher.
**After:** none
**Spend:** zero model calls.
**Network:** allowlist: api.github.com, github.com, semiceu.github.io

**HEADLESS NOTICE.** Under `claude -p` there is no next turn. Every command longer than two minutes is detached with its `EXIT=` line inside the `bash -c` string, logged, and polled in this turn.

---

## 0. The specification

**The specification is `cc_tasks/2026-09-20_g4_resourcing_release_date_grounding_fold.md`, §0 through §5, decisions 1 to 8, write set and SEQUENCING, read in full and executed unchanged, with these four differences:**

1. **Network** is the header above. `api.github.com` is decision 4's one Pages read. `semiceu.github.io` is touched only if decision 2 admits DCAT-AP (`https://semiceu.github.io/DCAT-AP/r5r/releases/3.0.0/`), through the corpus admission path. `github.com` is `git push`. No federal host.
2. **Filenames follow this task's slug:** RESULT `cc_tasks/2026-09-21_g4_resourcing_reissue_RESULT.md`, guard `scripts/check_protected_g4_resourcing_reissue.sh`, addenda glob `2026-09-21_g4_resourcing_reissue_ADDENDUM*.md` (and the superseded file's glob, which should return nothing).
3. **Decision 9 (new): the checkpoint rule lands in this repo's docs.** `~/GitHub/CLAUDE.md` §15 now requires every loop of model calls, network calls, or more than about two minutes of compute to persist per unit, resume by skipping completed keys, print progress on an interval, pilot before the full run, abort cleanly on ceilings, report partial results, and carry a SIGKILL-and-resume test. Here: (a) one paragraph in this repo's `CLAUDE.md` under the dispatch protocol, citing §15 and naming what already complies and what does not; (b) a short design note `docs/design/2026-09-21_DN-008_checkpoint_conformance.md` that audits each standing loop against §15's eight points, one table row each: the scan fetch loop, the judgement engine, the KG extraction batches, `claude -p` extraction calls, `score.py`, the report builders. Read the code; do not assume. Each cell is `yes` with the file and line, or `no`. **This task fixes nothing the audit finds**: each `no` on a loop that spends money or touches a federal host becomes one ResearchTask, named in the RESULT. A `no` on a pure local loop under two minutes is recorded and left.
4. **Part C's script conforms to §15 itself** if its population makes it run longer than two minutes: per-item JSONL, resume by key, progress line. If it runs in seconds, say so with the measured time and skip the machinery.

**Write set additions:** `CLAUDE.md` (decision 9a's paragraph), `docs/design/2026-09-21_DN-008_checkpoint_conformance.md`.

**Immutable once written.**

## 1. Report
As the superseded file's §5, plus §7: the DN-008 table and the ResearchTask ids it produced. `seldon cc complete`, commit, push.

**SEQUENCING:** glob addenda → superseded file's §1 (part B) → §2 (part A) → §3 (part C) → decision 9 → glob addenda → gate → report → push.
