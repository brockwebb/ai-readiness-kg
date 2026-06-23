"""FSS AI Data Readiness probe harness.

Test the machine by being the machine: point probes at what an agency publicly
exposes and score what comes back. No self-report; every score is backed by the
raw artifact it was derived from.

Core-vs-frontier firewall traces to icsp_notebook task 51fe4574 (flagship term
"AI-ready data"): Part A (content-side, data a system can already reach) = core;
Part B (the dated access axis — llms.txt / MCP / WebMCP) = frontier tracks, never
folded into the core composite.
"""
