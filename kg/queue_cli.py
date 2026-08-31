#!/usr/bin/env python3
"""`python -m kg queue …` — the status surface.

`kg queue status` is the answer to "what are we doing"; it has to fit a terminal, so the table
is width-bounded and the totals line carries the reconciliation against the manifest ledger.
"""
from __future__ import annotations

import json

from . import queue as q


def _short(s: str, n: int) -> str:
    s = str(s or "")
    return s if len(s) <= n else s[: n - 1] + "…"


def cmd_status(a) -> int:
    rows = q.project()
    sel = [r for r in rows.values()
           if (not a.state or r["extraction_state"] == a.state)
           and (not a.arm or (r.get("requested_profile") or r.get("pinned_profile")) == a.arm)]
    sel.sort(key=lambda r: (q.STATES.index(r["extraction_state"]),
                            r["priority"] if r["priority"] is not None else 10**6,
                            r["doc_id"]))
    tot = q.status_totals()
    print(f"pinned profile: {tot['pinned_profile']}   included: {tot['included']}   "
          f"manifest_add events: {tot['manifest_add_events']}   "
          f"reconciles: {'YES' if tot['reconciles'] else 'NO'}")
    print(f"{'document':<34}{'type':<11}{'state':<17}{'under':<14}{'prio':>5}")
    print("-" * 81)
    for r in sel[: a.limit]:
        latest = r["latest_extraction"] or {}
        under = latest.get("profile") or (latest.get("corpus_epoch") or "—")
        print(f"{_short(r['doc_id'], 33):<34}{_short(r['doc_type'], 10):<11}"
              f"{r['extraction_state']:<17}{_short(under, 13):<14}"
              f"{(r['priority'] if r['priority'] is not None else '—'):>5}")
    if len(sel) > a.limit:
        print(f"… {len(sel) - a.limit} more (use --limit)")
    print("-" * 81)
    print("  ".join(f"{s}={n}" for s, n in tot["by_state"].items()) + f"   total={tot['total']}")
    if not tot["reconciles"]:
        print(f"WARNING: {tot['included']} included documents but "
              f"{tot['manifest_add_events']} manifest_add events — the projection and the "
              f"admission ledger disagree; investigate before trusting this table.")
    return 0


def cmd_add(a) -> int:
    n = 0
    for doc in a.doc_ids:
        try:
            q.request(doc, a.priority, a.requested_by, a.reason,
                      profile=a.profile, superseding=a.superseding)
            n += 1
            print(f"  queued {doc} (priority {a.priority})")
        except q.QueueRefusal as exc:
            print(f"  REFUSED {doc}: {exc}")
    print(f"{n} of {len(a.doc_ids)} requested")
    return 0 if n == len(a.doc_ids) else 1


def cmd_add_epoch(a) -> int:
    rows = q.included_documents()
    docs = [d for d, e in rows.items()
            if (e.get("acquisition") or {}).get("corpus_epoch") == a.epoch
            or (e.get("extra") or {}).get("corpus_epoch") == a.epoch]
    if not docs:
        print(f"no included documents carry manifest epoch {a.epoch!r}")
        return 1
    a.doc_ids = sorted(docs)
    return cmd_add(a)


def cmd_withdraw(a) -> int:
    q.withdraw(a.doc_id, a.reason)
    print(f"withdrawn {a.doc_id}: {a.reason}")
    return 0


def cmd_defer(a) -> int:
    q.defer(a.doc_id, a.reason)
    print(f"deferred {a.doc_id}: {a.reason}")
    return 0


def cmd_next(a) -> int:
    wl = q.worklist(a.arm)[: a.n]
    rows = q.project()
    est = _per_doc_estimate()
    print(f"{'#':>3}  {'document':<40}{'prio':>5}{'state':>12}")
    for i, doc in enumerate(wl, 1):
        r = rows[doc]
        print(f"{i:>3}  {_short(doc, 39):<40}"
              f"{(r['priority'] if r['priority'] is not None else '—'):>5}"
              f"{r['extraction_state']:>12}")
    if est:
        print(f"\nestimated {len(wl)} x {est:,} = {len(wl) * est:,} tokens "
              f"(ledger running mean, informational — each run declares its own ceiling)")
    else:
        print("\nno measured settles for an estimate yet")
    return 0


def _per_doc_estimate() -> int:
    """Running mean of measured settles, informational only. DD-022 keeps the binding number
    on the run's own declaration, so this must never be mistaken for a ceiling."""
    from . import spend
    path = spend.default_ledger().path if hasattr(spend.default_ledger(), "path") else None
    try:
        lines = (path or q._LEDGER_PATH).read_text(encoding="utf-8").splitlines()
    except OSError:
        return 0
    vals = []
    for line in lines:
        try:
            r = json.loads(line)
        except Exception:
            continue
        if r.get("record") == "settle" and not r.get("settled_as_estimate"):
            vals.append(int(r["actual_tokens"]))
    return int(sum(vals[-10:]) / len(vals[-10:])) if vals else 0


def cmd_explain(a) -> int:
    from . import eventlog
    doc = a.doc_id
    print(f"=== {doc} ===")
    for ev in eventlog.replay():
        if (ev.get("doc_id") or ev.get("document_id")) != doc:
            continue
        t = ev.get("event_type")
        if t in ("node_asserted", "edge_asserted"):
            continue                       # thousands per document; summarised below
        detail = ev.get("reason") or ev.get("stage") or ev.get("to_state") or ""
        print(f"  {str(ev.get('timestamp') or ev.get('ts'))[:19]}  {t:<28} {_short(detail, 60)}")
    row = q.project().get(doc)
    if not row:
        print("  (not manifest-included)")
        return 1
    print(f"\n  state: {row['extraction_state']}   pinned profile: {row['pinned_profile']}")
    for e in row["extracted_under"]:
        flag = "  AMBIGUOUS PROFILE" if e.get("profile_ambiguous") else ""
        print(f"  extracted_under: profile={e['profile']} epoch={e['corpus_epoch']} "
              f"model={e['model_id']} ts={str(e['ts'])[:19]}{flag}")
    if row["failure"]:
        print(f"  failure: {row['failure']}")
    return 0


def cmd_backfill(a) -> int:
    """Emit the base task's §6 backfill as events, so the queue's starting state is auditable
    rather than assumed. Dry-run by default (the repo's release-orphans idiom)."""
    plan = q.backfill_plan()
    by_epoch = {}
    for row in plan:
        by_epoch.setdefault(row["epoch"], []).append(row)
    for epoch, rows in by_epoch.items():
        print(f"  {epoch:<28} {len(rows):>4} requests  "
              f"profile={rows[0]['profile']} priority={rows[0]['priority']}")
    print(f"  {'TOTAL':<28} {len(plan):>4}")
    if not a.commit:
        print("\ndry run — pass --commit to emit")
        return 0
    n = 0
    for row in plan:
        try:
            q.request(row["document_id"], row["priority"], "backfill", row["reason"],
                      profile=row["profile"])
            n += 1
        except q.QueueRefusal as exc:
            print(f"  REFUSED {row['document_id']}: {exc}")
    print(f"\nemitted {n} extraction_request events")
    return 0


def add_parser(sub) -> None:
    p = sub.add_parser("queue", help="extraction queue: admitted -> prioritized -> extracted")
    s = p.add_subparsers(dest="cmd", required=True)

    st = s.add_parser("status"); st.set_defaults(func=cmd_status)
    st.add_argument("--arm"); st.add_argument("--state")
    st.add_argument("--limit", type=int, default=40)

    ad = s.add_parser("add"); ad.set_defaults(func=cmd_add)
    ad.add_argument("doc_ids", nargs="+")
    ad.add_argument("--priority", type=int, required=True)
    ad.add_argument("--reason", required=True)
    ad.add_argument("--profile", default=None)
    ad.add_argument("--requested-by", dest="requested_by", default="operator")
    ad.add_argument("--superseding", action="store_true")

    ae = s.add_parser("add-epoch"); ae.set_defaults(func=cmd_add_epoch)
    ae.add_argument("epoch")
    ae.add_argument("--priority", type=int, required=True)
    ae.add_argument("--reason", required=True)
    ae.add_argument("--profile", default=None)
    ae.add_argument("--requested-by", dest="requested_by", default="operator")
    ae.add_argument("--superseding", action="store_true")

    wd = s.add_parser("withdraw"); wd.set_defaults(func=cmd_withdraw)
    wd.add_argument("doc_id"); wd.add_argument("--reason", required=True)

    df = s.add_parser("defer"); df.set_defaults(func=cmd_defer)
    df.add_argument("doc_id"); df.add_argument("--reason", required=True)

    nx = s.add_parser("next"); nx.set_defaults(func=cmd_next)
    nx.add_argument("--n", type=int, default=5); nx.add_argument("--arm", default=None)

    ex = s.add_parser("explain"); ex.set_defaults(func=cmd_explain)
    ex.add_argument("doc_id")

    bf = s.add_parser("backfill"); bf.set_defaults(func=cmd_backfill)
    bf.add_argument("--commit", action="store_true")
