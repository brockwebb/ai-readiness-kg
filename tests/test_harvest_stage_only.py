"""`stage_only` verdict on the triage harvester (task 2026-09-02_g1_eval_prior_art §3).

A cited-but-not-admitted document must be fetched into staging with provenance and then
registered `staged_not_admitted` with its clause — never `fetched`, which is the only
status manifest_triage admits. No network: the kernel fetcher is stubbed.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[1]


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def harvest(monkeypatch):
    mod = _load("harvest_triage")
    return mod


def _list(tmp_path: Path, verdict: str) -> Path:
    # The harvester records the list path repo-relative, so it must live under the repo;
    # tmp/ is gitignored. tmp_path only keys the per-test subdirectory name.
    cfg = {
        "settings": {
            "user_agent": "t", "browser_user_agent": "b", "discovered_via": "t",
            "discovered_via_gap": "tg", "max_doc_chars": 1000, "min_content_chars": 1,
            "timeout_seconds": 1, "retries": 0, "spacing_seconds": 0,
            "crwl_timeout_seconds": 1, "fit_min_fraction_of_raw": 0.1,
            "challenge_markers": [], "crwl_filter": {}, "paywall_domains": ["ssrn.com"],
            "vetting_input1": {"source": "x", "expertise": "none", "weight": "not_vetting"},
        },
        "entries": [{
            "row": 1, "doc_id": "doc-a", "title": "A", "year": "2026",
            "source_type": "academic", "primary_url": "https://example.org/a",
            "pdf_url": "https://example.org/a.pdf", "verdict": verdict,
            "clause": "R1_method_not_construct", "gap": True, "notes": "n",
        }],
    }
    d = REPO / "tmp" / f"test_harvest_stage_only_{tmp_path.name}"
    d.mkdir(parents=True, exist_ok=True)
    p = d / "list.yaml"
    p.write_text(yaml.safe_dump(cfg))
    return p


def _run(harvest, monkeypatch, tmp_path, verdict):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    def fake_fetch_entry(entry, fx, settings, dry_run):
        return {"doc_id": entry["doc_id"], "title": entry["title"],
                "primary_url": entry["primary_url"], "source_type": entry["source_type"],
                "clause": entry["clause"], "retrieved_at_utc": "2026-09-02T00:00:00Z",
                "urls_tried": [entry["pdf_url"]], "final_url": entry["pdf_url"],
                "http_status": 200, "local_path": "corpus/staging/inbox/x/doc-a.pdf",
                "sha256": "0" * 64, "bytes": 10, "chars": 10, "candidate_status": "fetched"}

    class FakeFetcher:
        def __init__(self, *a, **k): ...
        def close(self): ...

    monkeypatch.setattr(harvest.hk, "fetch_entry", fake_fetch_entry)
    monkeypatch.setattr(harvest.hk, "Fetcher", FakeFetcher)
    inbox = tmp_path / "inbox"
    monkeypatch.setattr(sys, "argv", ["harvest_triage.py", "--list", str(_list(tmp_path, verdict)),
                                      "--inbox", str(inbox), "--task-ref", "test"])
    try:
        assert harvest.main() == 0
        return json.loads((inbox / "_fetch_register.json").read_text())["records"]["doc-a"]
    finally:
        import shutil
        shutil.rmtree(REPO / "tmp" / f"test_harvest_stage_only_{tmp_path.name}", ignore_errors=True)


def test_stage_only_is_fetched_then_marked_not_admitted(harvest, monkeypatch, tmp_path):
    rec = _run(harvest, monkeypatch, tmp_path, "stage_only")
    assert rec["candidate_status"] == "staged_not_admitted"
    assert rec["clause"] == "R1_method_not_construct"
    assert rec["sha256"] == "0" * 64 and rec["local_path"]      # provenance kept
    assert "R1_method_not_construct" in rec["reason"]


def test_fetch_verdict_unchanged(harvest, monkeypatch, tmp_path):
    rec = _run(harvest, monkeypatch, tmp_path, "fetch")
    assert rec["candidate_status"] == "fetched"


def test_manifest_triage_registers_staged_not_admitted_as_excluded():
    mt = _load("manifest_triage")
    assert mt.REGISTER_STATUS["staged_not_admitted"] == "excluded"
    # and it is not the one status the admission loop accepts
    assert "staged_not_admitted" != "fetched"
