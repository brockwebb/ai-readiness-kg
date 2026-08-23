#!/usr/bin/env python3
"""Probe Phase 4.3 — cross-family judging via operator chat export
(task 2026-08-22_faithfulness_probe). Writes numbered markdown batches of 10 facts (fact,
span, window, answer template) to corpus/staging/metrics/probe_crossfamily_batches/. The
operator pastes a batch into another vendor's model and drops the response (JSONL, one line
per fact, header line with the model name+version) into corpus/staging/inbox/probe_crossfamily/.
This task does not wait for responses; a follow-on ingests them (agent id = the model the
operator records; absent -> `unknown_crossfamily`, flagged).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
import probe_judge as pj  # noqa: E402

OUT = REPO / "corpus/staging/metrics/probe_crossfamily_batches"
INBOX = REPO / "corpus/staging/inbox/probe_crossfamily"
SIZE = 10

HEADER = """# Cross-family faithfulness batch {n:03d} — paste this whole file into a non-Claude model

Task: for EACH fact, say whether the GROUNDING SPAN ALONE entails the fact. The WINDOW is
document context; use it ONLY to decide between `subject_dropped`/`span_truncated` (document
supports the fact, span omits it) and `fabrication` (document does not support it).
Classes when not entailed: doc_level_attribute | span_truncated | subject_dropped |
filled_attribute | fabrication | grade_misassigned.

Reply with JSONL, one line per fact, FIRST line a header naming the model you used:
{{"agent": "<vendor model name and version>", "agent_type": "prov:SoftwareAgent"}}
{{"fact_id": "...", "label": "entailed|not_entailed", "class": "<class>|null", "confidence": 0.0, "reason": "..."}}

Save the reply as `corpus/staging/inbox/probe_crossfamily/batch_{n:03d}.jsonl`.

"""


def main() -> int:
    facts = pj.load_facts()
    OUT.mkdir(parents=True, exist_ok=True); INBOX.mkdir(parents=True, exist_ok=True)
    for i in range(0, len(facts), SIZE):
        n = i // SIZE + 1
        blocks = []
        for f in facts[i:i + SIZE]:
            blocks.append(f"""## fact_id: {f['fact_id']}
- item type: {f['type']} · attribute: {f['attribute']}
- **FACT:** {f['fact_text']}
- **GROUNDING SPAN:** "{f['grounding_span']}"
- WINDOW:
    {(f.get('window') or '(span not located in document text)').replace(chr(10), ' ')}
""")
        (OUT / f"batch_{n:03d}.md").write_text(HEADER.format(n=n) + "\n".join(blocks), encoding="utf-8")
    (INBOX / "README.md").write_text("Drop cross-family responses here as batch_NNN.jsonl (see ../../metrics/probe_crossfamily_batches/). Ingested by a follow-on task.\n", encoding="utf-8")
    print(f"{(len(facts) + SIZE - 1) // SIZE} batches of {SIZE} -> {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
