#!/usr/bin/env python3
"""`python -m kg <command>` — the operator's entry point.

Currently one command group: `queue` (task 2026-08-27_extraction_queue). The CLI is the whole
interface per AD-003 — internal tools are CLI, not MCP.
"""
from __future__ import annotations

import argparse
import sys


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m kg")
    sub = ap.add_subparsers(dest="group", required=True)
    from .queue_cli import add_parser as add_queue
    add_queue(sub)
    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
