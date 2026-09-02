"""Probe modules — one module per probe (CC task 2026-06-23, Stage 3 constraint).

Each probe is self-contained and independently reproducible. A probe separates
`fetch` (network I/O) from `evaluate` (pure scoring of a fetched artifact) so the
scoring logic is testable from fixtures without hitting the network.
"""
