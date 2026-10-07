"""Hosts in parallel, politeness per host: the two guards DN-013-R2 is held to.

`cc_tasks/2026-10-07_parallel_hosts_and_fast_gate.md` decisions 1 to 3.

Prior art, adopted not invented: Heritrix's per-host frontier queues with a politeness delay,
and Scrapy's `CONCURRENT_REQUESTS_PER_DOMAIN` with `DOWNLOAD_DELAY`. Every polite crawler keeps
the delay per host and the parallelism across hosts; the harness now does the same, with one
request in flight per host (the stricter Heritrix setting).

The guards, both in `make guards`:

* **Equivalence.** Loopback fixtures scanned as a cycle, serially (`max_parallel_hosts: 1`) and
  in parallel, against the SAME servers so every URL and therefore every derived id is the
  same: the two payloads are equal once the timing fields are removed, and every rule's verdict
  is identical. The order of first contact (`robots_log`) is timing too and is compared as a
  set keyed on the netloc.
* **Politeness under concurrency.** From the parallel run's own fetch log, consecutive requests
  to one netloc are never closer than `1 / requests_per_second_per_host`, including a host two
  bodies declare, which two workers reach at once.

Each guard carries the positive control that shows it can fail: a perturbed verdict makes the
equivalence comparison unequal, and a Fetcher with its per-netloc lock removed (the code before
this task) breaks the gap when two threads reach one netloc together.
"""
from __future__ import annotations

import contextlib
import copy
import re
import sys
import threading
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "assessment" / "harness"))

from scan import declarations, load_params, run                    # noqa: E402
from scan.clock import RealClock, VirtualClock                      # noqa: E402
from scan.fixtures.server import FixtureServer                      # noqa: E402
from scan.manners import Fetcher                                    # noqa: E402
from scan.model import params_hash                                  # noqa: E402

#: Requests per second per host for the REAL-clock legs below. A test interval, stated here so a
#: reader can see the standing rate is not what they are about; the same value
#: `tests/test_virtual_time.py` uses for its real-clock agreement check.
TEST_INTERVAL_RPS = 20

#: Keys that record WHEN or HOW LONG, never WHAT. `captured_at` and `read_at` are wall and
#: monotonic stamps; `elapsed_ms` is a duration; `earliest_surface_captured_at` is E5's copy of
#: the first stamp; `fetched_at` is named by the task file and absent today. Nothing else is
#: removed, so anything else that differs is a difference in what was measured.
TIMING_KEYS = frozenset({"captured_at", "read_at", "elapsed_ms",
                         "earliest_surface_captured_at", "fetched_at"})

#: E5's reason QUOTES the first real host's `captured_at` ("every control observation precedes
#: the first real host (2026-...)"), so the stamp is masked inside reasons, and only there.
_REASON_KEYS = frozenset({"reason", "control_reason"})
_ISO_STAMP = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?([+-]\d{2}:\d{2}|Z)?")

#: The bodies of the scratch frame: (agency, fixture). Three netlocs, so three workers, and a
#: fourth server, `SHARED`, that ALPHA and BETA both declare as their API host, so two workers
#: reach one off-roster netloc: the `www.usda.gov` case.
BODIES = (("ALPHA", "passes_all"), ("BETA", "fails_all"), ("GAMMA", "resets_links_only"))


def _params(max_parallel_hosts, rps=None) -> dict:
    p = copy.deepcopy(load_params())
    p["manners"]["max_parallel_hosts"] = max_parallel_hosts
    if rps is not None:
        p["manners"]["requests_per_second_per_host"] = rps
    return p


def _targets(bases: dict, shared: str, params: dict) -> list:
    """`run.targets`' row shape over loopback servers: per body a well-known row (A12, probed
    at the home page), a home page and a flagship, every leg the frame gives each kind."""
    out = []
    for agency, base in bases.items():
        netloc = base.split("//", 1)[1]
        declared = (declarations.control_fixture(shared, params)
                    if agency in ("ALPHA", "BETA") else declarations.control_fixture(base, params))
        common = {"agency": agency, "tier": "A", "admitted": False, "host": netloc,
                  "declared": declared}
        out.append(dict(common, doc_id=f"host:{netloc}", url=f"{base}/robots.txt",
                        surface_kind="well_known", legs=list(run.HOST_LEGS),
                        probe_url=f"{base}/index.html"))
        out.append(dict(common, doc_id=f"home:{netloc}", url=f"{base}/index.html",
                        surface_kind="home", legs=list(run.CONTROL_LEGS)))
        out.append(dict(common, doc_id=f"flagship:{netloc}/index.html",
                        url=f"{base}/index.html", surface_kind="flagship",
                        legs=list(run.CONTROL_LEGS)))
    return out


class _TracingFetcher(Fetcher):
    """Records which worker thread issued each request to which netloc. Observation only: every
    request still goes through the real gate, limiter and client."""

    def __init__(self, *a, **k) -> None:
        super().__init__(*a, **k)
        self.threads_by_netloc: dict = {}
        self._trace = threading.Lock()

    def _wait(self, host: str) -> None:
        super()._wait(host)
        with self._trace:
            self.threads_by_netloc.setdefault(host, set()).add(threading.current_thread().name)


def _cycle(params, tgts, controls, clock) -> tuple:
    fetcher = _TracingFetcher(params, clock=clock)
    payload = run.run_cycle(params, tgts, controls, fetcher, task="test",
                            evidence_root="test")
    return payload, fetcher


def normalize(payload):
    """The payload less its timing: `TIMING_KEYS` anywhere, a timestamp quoted in a reason, the
    HTTP `Date` header the fixture server stamps on each response, and `robots_log` as a set
    (its ORDER is first contact)."""
    def walk(x, parent=None):
        if parent in _REASON_KEYS and isinstance(x, str):
            return _ISO_STAMP.sub("<captured_at>", x)
        if isinstance(x, dict):
            return {k: walk(v, k) for k, v in x.items()
                    if k not in TIMING_KEYS and not (parent == "headers" and k.lower() == "date")}
        if isinstance(x, list):
            return [walk(v, parent) for v in x]
        return x
    out = walk(payload)
    out["robots_log"] = sorted(out["robots_log"], key=lambda r: (r["netloc"], r["url"]))
    return out


@pytest.fixture(scope="module")
def serial_and_parallel(tmp_path_factory):
    """One scratch frame on four live loopback servers, scanned serially and then in parallel
    under one control gate, both on virtual clocks."""
    from scan import model
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(model, "EVIDENCE_ROOT", tmp_path_factory.mktemp("parallel_hosts_evidence"))
        with contextlib.ExitStack() as stack:
            bases = {a: stack.enter_context(FixtureServer(fx)) for a, fx in BODIES}
            shared = stack.enter_context(FixtureServer("passes_all"))
            serial_p, parallel_p = _params(1), _params(None)
            tgts = _targets(bases, shared, serial_p)
            cf, e5, control_obs, ok = run.run_controls(serial_p, clock=VirtualClock())
            assert ok, e5.reason
            controls = (cf, e5, control_obs)
            serial, serial_f = _cycle(serial_p, tgts, controls, VirtualClock())
            parallel, parallel_f = _cycle(parallel_p, tgts, controls, VirtualClock())
    return {"serial": serial, "parallel": parallel, "serial_f": serial_f,
            "parallel_f": parallel_f, "shared": shared.split("//", 1)[1], "tgts": tgts,
            "params": parallel_p}


# ================================================================ decision 3: equivalence

def test_a_parallel_cycle_is_the_serial_cycle_but_for_timing(serial_and_parallel):
    s, p = serial_and_parallel["serial"], serial_and_parallel["parallel"]
    assert s["findings"] > 0 and s["observations"] > 0, "nothing was measured"
    ns, np_ = normalize(s), normalize(p)
    diff = sorted(k for k in set(ns) | set(np_) if ns.get(k) != np_.get(k))
    assert not diff, f"serial and parallel payloads differ beyond timing on: {diff}"


def test_every_rule_gives_the_same_verdict_serial_and_parallel(serial_and_parallel):
    def verdicts(payload):
        return [(f["finding_id"], f["rule_id"], f["target_doc_id"], f["verdict"])
                for f in payload["findings_detail"]]
    s, p = serial_and_parallel["serial"], serial_and_parallel["parallel"]
    assert verdicts(s) == verdicts(p)
    # The verdicts span more than one value, so an instrument that returned one verdict for
    # everything could not pass this by accident.
    assert len({v for *_, v in verdicts(s)}) >= 2, verdicts(s)


def test_the_control_gate_judges_the_same_serial_and_parallel():
    """`run_controls` scans its fixtures in parallel too: each is its own server on its own
    port, so its own netloc. Every control Finding and E5's verdict are the serial gate's. Each
    run binds fresh ephemeral ports, which enter every URL and every derived id, so the
    comparison is on the judgement (rule, leg, surface, verdict, reason) with the port masked."""
    port = re.compile(r"127\.0\.0\.1:\d+")

    def judged(params):
        cf, e5, _obs, ok = run.run_controls(params, clock=VirtualClock())
        return ok, [tuple(port.sub("<port>", x) for x in
                          (f.rule_id, f.leg, f.target_doc_id, f.verdict, f.reason))
                    for f in cf + [e5]]

    ok_s, serial = judged(_params(1))
    ok_p, parallel = judged(_params(None))
    assert ok_s and ok_p
    assert serial == parallel


def test_the_equivalence_comparison_can_fail(serial_and_parallel):
    """Positive control: one changed verdict, and the normalized payloads are unequal."""
    p = copy.deepcopy(serial_and_parallel["parallel"])
    f = p["findings_detail"][0]
    f["verdict"] = "fail" if f["verdict"] != "fail" else "pass"
    assert normalize(p) != normalize(serial_and_parallel["serial"])


def test_the_parallel_run_was_parallel_and_the_shared_host_was_shared(serial_and_parallel):
    """Without this the equivalence above could be two serial runs. The parallel cycle used
    one worker per body, and the declared off-roster host was reached from two of them."""
    pf, sf = serial_and_parallel["parallel_f"], serial_and_parallel["serial_f"]
    workers = set().union(*pf.threads_by_netloc.values())
    assert len([w for w in workers if w.startswith("scan-host")]) == len(BODIES), workers
    shared = serial_and_parallel["shared"]
    assert len(pf.threads_by_netloc.get(shared, ())) >= 2, pf.threads_by_netloc
    # The serial run is the old loop: the calling thread, nobody else.
    assert set().union(*sf.threads_by_netloc.values()) == {threading.current_thread().name}
    # And the two runs asked the same number of things of every host.
    assert sf.requests == pf.requests


def test_max_parallel_hosts_shapes_no_hash():
    """`manners.max_parallel_hosts` is outside `params_hash` (`model.UNHASHED_NESTED_KEYS`):
    with it, without it and at any value, one hash. The rate is inside and still moves it."""
    params = load_params()
    assert "max_parallel_hosts" in params["manners"]
    without = copy.deepcopy(params)
    del without["manners"]["max_parallel_hosts"]
    assert params_hash(params) == params_hash(without) == params_hash(_params(4))
    assert params_hash(_params(None, rps=2.0)) != params_hash(params)


def test_the_worker_count_is_the_config_or_refused():
    assert run.parallel_hosts(_params(None), 3) == 3
    assert run.parallel_hosts(_params(None), 42) == run.MAX_PARALLEL_HOSTS == 16
    assert run.parallel_hosts(_params(1), 42) == 1
    assert run.parallel_hosts(_params(8), 3) == 3
    for bad in (0, 17, -1, 2.5, "4", True):
        with pytest.raises(SystemExit, match="max_parallel_hosts"):
            run.parallel_hosts(_params(bad), 3)


def test_map_by_host_keeps_order_within_a_host_and_returns_input_order():
    seen: dict = {}
    lock = threading.Lock()
    items = [("a", 0), ("b", 0), ("a", 1), ("c", 0), ("b", 1), ("a", 2)]

    def fn(it):
        with lock:
            seen.setdefault(it[0], []).append((it[1], threading.current_thread().name))
        return it

    out = run.map_by_host(items, lambda it: it[0], fn, _params(None))
    assert out == items
    for key, calls in seen.items():
        assert [n for n, _ in calls] == sorted(n for n, _ in calls), (key, calls)
        assert len({t for _, t in calls}) == 1, f"{key} ran on more than one worker"


def test_a_worker_failure_is_raised_not_swallowed():
    def fn(it):
        if it == "boom":
            raise RuntimeError("collector defect outside the recorded path")
        return it
    with pytest.raises(RuntimeError, match="collector defect"):
        run.map_by_host(["x", "boom", "y"], lambda it: it, fn, _params(None))


# ================================================================ decision 3: politeness

def _gaps(times: list) -> list:
    return [b - a for a, b in zip(times, times[1:])]


def test_no_two_requests_to_one_netloc_are_closer_than_the_gap_virtual(serial_and_parallel):
    pf, params = serial_and_parallel["parallel_f"], serial_and_parallel["params"]
    gap = 1.0 / float(params["manners"]["requests_per_second_per_host"])
    shared = serial_and_parallel["shared"]
    assert len(pf.request_times.get(shared, [])) >= 2
    for netloc, times in pf.request_times.items():
        assert times == sorted(times), netloc
        short = [g for g in _gaps(times) if g < gap - 1e-9]
        assert not short, f"{netloc}: {len(short)} gap(s) under {gap}s: {short[:3]}"


def test_no_two_requests_to_one_netloc_are_closer_than_the_gap_real_clock(tmp_path,
                                                                         monkeypatch):
    """The same property on the REAL monotonic clock and real threads, at a test interval: a
    virtual clock adds parallel waits rather than overlapping them, so this is the run where
    the workers truly overlap in time."""
    from scan import model
    monkeypatch.setattr(model, "EVIDENCE_ROOT", tmp_path / "evidence")
    params = _params(None, rps=TEST_INTERVAL_RPS)
    gap = 1.0 / TEST_INTERVAL_RPS
    with contextlib.ExitStack() as stack:
        bases = {a: stack.enter_context(FixtureServer(fx)) for a, fx in BODIES}
        shared = stack.enter_context(FixtureServer("passes_all"))
        tgts = _targets(bases, shared, params)
        cf, e5, control_obs, ok = run.run_controls(params, clock=VirtualClock())
        assert ok, e5.reason
        _payload, fetcher = _cycle(params, tgts, (cf, e5, control_obs), RealClock())
    netloc = shared.split("//", 1)[1]
    assert len(fetcher.threads_by_netloc.get(netloc, ())) >= 2, fetcher.threads_by_netloc
    for host, times in fetcher.request_times.items():
        short = [g for g in _gaps(times) if g < gap - 1e-6]
        assert not short, f"{host}: {len(short)} gap(s) under {gap}s: {short[:3]}"


class _Resp:
    def __init__(self, url: str, status: int) -> None:
        self.status_code, self.url, self.headers, self.content = status, url, {}, b"ok"


class _FakeClient:
    """No network: `/robots.txt` is a 404 (RFC 9309 §2.3.1.3, allow all), anything else 200."""

    def get(self, url):
        return _Resp(url, 404 if url.endswith("/robots.txt") else 200)

    head = get


class _UnlockedFetcher(Fetcher):
    """The Fetcher with its per-netloc lock removed: the code before this task, which was safe
    only because one thread ever called it."""

    def host_lock(self, netloc):
        return contextlib.nullcontext()


def _race(fetcher_cls, rounds: int = 8) -> list:
    """Two threads, released together by a barrier each round, each asking one netloc for a
    page. Returns that netloc's request stamps."""
    params = _params(None, rps=TEST_INTERVAL_RPS)
    fetcher = fetcher_cls(params, client=_FakeClient(), clock=RealClock())
    fetcher.raw_get("http://shared.invalid/robots.txt")
    barrier = threading.Barrier(2)

    def worker(n: int) -> None:
        for i in range(rounds):
            barrier.wait()
            fetcher.raw_get(f"http://shared.invalid/page-{n}-{i}")

    threads = [threading.Thread(target=worker, args=(n,)) for n in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return fetcher.request_times["shared.invalid"]


def test_the_politeness_guard_catches_an_unlocked_fetcher():
    """Positive control. Without the lock, two threads read the same last stamp, sleep the same
    remainder and issue together: a gap far under the interval. With it, never."""
    gap = 1.0 / TEST_INTERVAL_RPS
    unlocked = _race(_UnlockedFetcher)
    assert any(g < gap / 2 for g in _gaps(unlocked)), (
        f"the unlocked fetcher kept every gap: {_gaps(unlocked)}; the guard has no teeth")
    locked = _race(Fetcher)
    assert all(g >= gap - 1e-6 for g in _gaps(locked)), _gaps(locked)


def test_a_body_stored_from_many_threads_is_whole(tmp_path):
    """`model.store_evidence` renames into place, so concurrent writers of one body leave the
    whole body and no temporary file behind (`runner._body` reads it back mid-cycle)."""
    from scan import model
    body = b"x" * (4 << 20)
    out: list = []
    threads = [threading.Thread(target=lambda: out.append(model.store_evidence(body, tmp_path)))
               for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert len({d for d, _ in out}) == 1
    stored = list(tmp_path.rglob("*"))
    files = [f for f in stored if f.is_file()]
    assert len(files) == 1 and files[0].read_bytes() == body, [f.name for f in files]
