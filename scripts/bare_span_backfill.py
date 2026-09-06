#!/usr/bin/env python3
"""Backfill bare grounding spans from the manifested corpus. **Zero model spend.**

Task `cc_tasks/2026-09-06_bare_span_backfill.md` §2-§3. Issue `e21b9ab3`.

**Prior art.** Luhn (1960), "Key word-in-context index for technical literature", *American
Documentation* 11(4): the useful unit is the mention **plus its bounded context**. Block
segmentation follows CommonMark §4-§5 (heading, list item, table row, paragraph), which is
deterministic — nothing here asks a model anything. Provenance follows PROV-O
`prov:wasRevisionOf`: the widened span is a **revision** of the bare one and the bare one is
retained on the log, which is exactly what the existing `grounding_relocated` overlay already
implements. **Extraction events are never rewritten** — `prov_extraction_event_id` is
untouched on every node.

**What `location` turned out to be, read from the code and the graph rather than assumed:** a
MODEL-AUTHORED HEADING PATH in free text. `prompt_template_v0_3_8.md` requires a `location` on
every node and never defines its format, so the model writes `Stages of the journey >
Readiness`, `Introduction`, `title/intro`, `DIME PROJECT banner`. It is not an offset and not
a stable section id, so it is used **only to disambiguate** between candidate matches and can
never lose a match that a plain phrase search would have found.

    /opt/anaconda3/bin/python3 scripts/bare_span_backfill.py --phase plan
    /opt/anaconda3/bin/python3 scripts/bare_span_backfill.py --phase write
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, "/Users/brock/GitHub/seldon")

TASK = "cc_tasks/2026-09-06_bare_span_backfill.md"
OUT = REPO / "state" / "bare_span_backfill_2026-09-06.json"
DERIVATION = "kwic_backfill_v1"
#: Shard 27. Chosen as "the next free one" and it was NOT free — it already held 4
#: `manifest_add` events, so the 1,695 relocations sit beside them. Harmless (mixed event
#: types per shard are normal here — batch-004 holds assertions, model_call, STOP and skip
#: events) and unfixable in the right direction: the log is append-only, so moving them would
#: mean deleting them. Recorded rather than tidied. Relocation overlays are applied in a
#: second pass after the main replay, so shard order does not affect them either way.
BACKFILL_BATCH = 27

#: §2.3 bounds. A span under `MIN_TOKENS` is not context, and one over `MAX_CHARS` is a
#: passage rather than a span; both are the task's pre-registered numbers.
MIN_TOKENS = 8
MAX_CHARS = 400
#: A block whose non-name token count is at or below this is treated as contextless and
#: extended into the following block (§2.3).
THIN_NON_NAME_TOKENS = 6

_WS = re.compile(r"\s+")
_SENT = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9(\"'])")
_WORD = re.compile(r"[a-z0-9]+")


def norm(s) -> str:
    return _WS.sub(" ", (s or "").strip())


def _tokens(s: str) -> list:
    return _WORD.findall((s or "").lower())


def _stem(t: str) -> str:
    """The same conservative inflectional fold the vocabulary uses, inlined for one token."""
    if len(t) > 3 and t.endswith("ies"):
        return t[:-3] + "y"
    if len(t) > 3 and t.endswith("es") and t[-3] in "sxz":
        return t[:-2]
    if len(t) > 3 and t.endswith("s") and not t.endswith("ss"):
        return t[:-1]
    return t


# ---------------------------------------------------------------- segmentation
_HEADING = re.compile(r"^\s{0,3}(#{1,6})\s+(.*)$")
_LIST = re.compile(r"^\s*([-*+]|\d+[.)])\s+")
_TABLE = re.compile(r"^\s*\|.*\|\s*$")


def strip_marker(raw: str) -> str:
    """Drop the block's MARKUP, keep its content: `## `, `- `, `1. `, and the outer table
    pipes. The marker is not something the source says; a grounding span reading `- Accuracy`
    quotes the bullet, not the corpus."""
    out = []
    for line in (raw or "").splitlines():
        line = _HEADING.sub(lambda m: m.group(2), line)
        line = _LIST.sub("", line)
        if _TABLE.match(line):
            line = " ".join(c.strip() for c in line.strip().strip("|").split("|") if c.strip())
        out.append(line)
    return norm("\n".join(out))


def blocks(text: str) -> list:
    """CommonMark-ish blocks with their kind, nearest heading, and char range.

    Deliberately simple: a heading is its own block, a list item is its own block, a table row
    is its own block, and consecutive non-blank other lines form a paragraph. A full parser
    would be a dependency and a second thing to be wrong; what matters here is that the unit
    is smaller than the document and larger than the word.
    """
    out, buf, start, heading = [], [], 0, ""
    pos = 0

    def flush(end: int) -> None:
        nonlocal buf, start
        if buf and "".join(buf).strip():
            out.append({"kind": "paragraph", "text": strip_marker("".join(buf)),
                        "heading": heading, "start": start, "end": end})
        buf = []

    for line in text.splitlines(keepends=True):
        line_start, pos = pos, pos + len(line)
        stripped = line.strip()
        m = _HEADING.match(line)
        if m:
            flush(line_start)
            heading = m.group(2).strip()
            out.append({"kind": "heading", "text": strip_marker(line), "heading": heading,
                        "start": line_start, "end": pos})
            start = pos
            continue
        if _TABLE.match(line):
            flush(line_start)
            if not re.fullmatch(r"[\s|:-]+", stripped):
                out.append({"kind": "table_row", "text": strip_marker(line), "heading": heading,
                            "start": line_start, "end": pos})
            start = pos
            continue
        if _LIST.match(line):
            flush(line_start)
            out.append({"kind": "list_item", "text": strip_marker(line), "heading": heading,
                        "start": line_start, "end": pos})
            start = pos
            continue
        if not stripped:
            flush(line_start)
            start = pos
            continue
        if not buf:
            start = line_start
        buf.append(line)
    flush(pos)
    return out


# ---------------------------------------------------------------- locating
def contains_name(span: str, name: str) -> bool:
    """§2.5: the widened span must still contain its own name, tolerating inflection."""
    want = [_stem(t) for t in _tokens(name)]
    have = [_stem(t) for t in _tokens(span)]
    if not want:
        return False
    n = len(want)
    return any(have[i:i + n] == want for i in range(len(have) - n + 1))


def locate(text: str, name: str, location: str | None) -> dict | None:
    """The smallest block containing `name`, preferring one under a heading that matches
    `location`. `location` may only DISAMBIGUATE — a value matching nothing falls back."""
    bl = blocks(text)
    hits = [b for b in bl if contains_name(b["text"], name)]
    if not hits:
        return None
    if location:
        loc_tokens = {_stem(t) for t in _tokens(location)}
        scoped = [b for b in hits
                  if loc_tokens and loc_tokens & {_stem(t) for t in _tokens(b["heading"])}]
        if scoped:
            hits = scoped
    # prefer the block with the most context, so a bare heading loses to the paragraph that
    # explains it when both match.
    non_name = lambda b: len(set(_tokens(b["text"])) - set(_tokens(name)))  # noqa: E731
    return sorted(hits, key=lambda b: (-non_name(b), b["start"]))[0]


def span_for(text: str, block: dict, name: str) -> tuple:
    """(span, block_kind). Extends a contextless block into the one that follows it."""
    if block is None:
        return "", ""
    bl = blocks(text)
    idx = next((i for i, b in enumerate(bl) if b["start"] == block["start"]), None)
    span = block["text"]
    non_name = len(set(_tokens(span)) - set(_tokens(name)))
    if block["kind"] == "heading" or non_name <= THIN_NON_NAME_TOKENS:
        for nxt in bl[(idx or 0) + 1:]:
            if nxt["kind"] == "heading":
                break
            first = _SENT.split(nxt["text"])[0] if nxt["text"] else ""
            if first:
                span = f"{span} — {first}" if span else first
                break
    span = norm(span)
    if len(span) > MAX_CHARS:
        span = window_on(span, name)
    return span, block["kind"]


def window_on(span: str, name: str) -> str:
    """A `MAX_CHARS` window CENTRED on the mention, snapped to sentence boundaries.

    This is the actual Luhn (1960) construction and the first pass did not implement it: it
    truncated from the block's start, which drops the mention whenever it sits past
    `MAX_CHARS` — 1,190 of 1,773 nodes failed the §2.5 name check that way, and the failure
    was concentrated in PDF-derived text where a "paragraph" can be a whole page.
    """
    sentences = _SENT.split(span) or [span]
    hit = next((i for i, s in enumerate(sentences) if contains_name(s, name)), None)
    if hit is None:
        return span[:MAX_CHARS].rstrip()
    out, lo, hi = sentences[hit], hit, hit
    # grow outward, nearest sentence first, while the budget holds
    while True:
        nxt = sentences[hi + 1] if hi + 1 < len(sentences) else None
        prv = sentences[lo - 1] if lo > 0 else None
        grew = False
        if nxt is not None and len(out) + 1 + len(nxt) <= MAX_CHARS:
            out, hi, grew = f"{out} {nxt}", hi + 1, True
        if prv is not None and len(prv) + 1 + len(out) <= MAX_CHARS:
            out, lo, grew = f"{prv} {out}", lo - 1, True
        if not grew:
            break
    if len(out) > MAX_CHARS:                      # one sentence longer than the budget
        i = out.lower().find(_tokens(name)[0]) if _tokens(name) else 0
        start = max(0, min(i - MAX_CHARS // 3, len(out) - MAX_CHARS))
        out = out[start:start + MAX_CHARS]
    return norm(out)


# ---------------------------------------------------------------- the §3 floor
def is_thin(span: str, name: str) -> bool:
    """Invariant 3's new floor: >= 8 tokens OR >= 3 tokens outside the name.

    `RDF 1.1` against the name `RDF` is flagged, and that is the floor's KNOWN COST, kept
    deliberately: thinness is exactly what this measures, and an exception for short standard
    names would make the floor unfalsifiable. A flagged span is annotated `grounding_thin`,
    never deleted — the extraction event stands.
    """
    toks = _tokens(span)
    outside = len(set(toks) - set(_tokens(name)))
    return not (len(toks) >= MIN_TOKENS or outside >= 3)


# ---------------------------------------------------------------- the pass
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--phase", choices=("plan", "write"), default="plan")
    a = ap.parse_args(argv)

    import run_bulk_extraction as rbe
    import run_chunked_bulk as rcb
    from kg import eventlog
    from bare_span_measure import NAMED_LABELS, is_bare
    from seldon.config import get_neo4j_driver, load_project_config

    cfg = load_project_config(REPO)
    driver = get_neo4j_driver(cfg)
    try:
        with driver.session(database=cfg["neo4j"]["database"]) as s:
            rows = []
            for label in NAMED_LABELS:
                rows += [dict(r, label=label) for r in s.run(
                    f"MATCH (n:{label}) RETURN n.key AS key, n.name AS name, "
                    f"n.grounding_span AS span, n.doc_id AS doc_id, n.location AS location,"
                    f"n.id AS item_id").data()]
    finally:
        driver.close()

    bare = [r for r in rows if is_bare(r["span"], r["name"])]
    paths = rcb.document_paths()
    texts: dict = {}

    def text_for(doc_id: str) -> str:
        if doc_id not in texts:
            p = paths.get(doc_id)
            texts[doc_id] = rbe.doc_text(Path(p), doc_id) if p else ""
        return texts[doc_id]

    counts = collections.Counter()
    plan = []
    for r in sorted(bare, key=lambda x: (x["doc_id"] or "", x["key"])):
        text = text_for(r["doc_id"])
        if not text.strip():
            counts["unlocatable_no_text"] += 1
            continue
        block = locate(text, r["name"], r.get("location"))
        if block is None:
            counts["unlocatable"] += 1
            continue
        span, kind = span_for(text, block, r["name"])
        if not contains_name(span, r["name"]):
            counts["name_absent"] += 1
            continue
        if is_bare(span, r["name"]) or is_thin(span, r["name"]):
            counts["still_thin"] += 1
            continue
        counts["backfilled"] += 1
        counts[f"block_kind_{kind}"] += 1
        plan.append({"key": r["key"], "label": r["label"], "doc_id": r["doc_id"],
                     "item_id": r["item_id"], "name": r["name"],
                     "old_span": r["span"], "new_span": span, "block_kind": kind,
                     "locator": ("location+phrase" if r.get("location") else "phrase"),
                     "char_range": [block["start"], block["end"]]})

    summary = {"task": TASK, "bare_total": len(bare), "counts": dict(counts),
               "backfilled": counts["backfilled"],
               "unlocatable": counts["unlocatable"] + counts["unlocatable_no_text"],
               "name_absent": counts["name_absent"], "still_thin": counts["still_thin"],
               "remaining_bare": len(bare) - counts["backfilled"],
               "share_after": round((len(bare) - counts["backfilled"]) / len(rows), 6),
               "nodes_examined": len(rows)}
    OUT.write_text(json.dumps({**summary, "plan": plan}, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=1))
    for p in plan[:5]:
        print(f"\n  {p['key']}\n    old: {p['old_span']!r}\n    new: {p['new_span'][:200]!r} [{p['block_kind']}]")

    if a.phase == "plan":
        return 0
    now = datetime.now(timezone.utc).isoformat()
    for p in plan:
        eventlog.append({
            "event_type": "grounding_relocated", "doc_id": p["doc_id"], "item_id": p["item_id"],
            "node_key": p["key"], "label": p["label"],
            "old_span": p["old_span"], "new_span": p["new_span"],
            "method": DERIVATION, "derivation": DERIVATION, "locator": p["locator"],
            "block_kind": p["block_kind"], "char_range": p["char_range"],
            "task": TASK, "ts": now}, batch=BACKFILL_BATCH)
    print(f"\nwrote {len(plan)} grounding_relocated overlay events")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
