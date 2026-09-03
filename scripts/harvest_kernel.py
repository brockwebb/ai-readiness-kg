#!/usr/bin/env python3
"""Bounded, idempotent kernel harvest -> corpus/staging/inbox/kernel/.

Task: cc_tasks/2026-08-21_v03_visibility_kernel.md, Phase 2. Fetches the named list in
scripts/kernel_list.yaml (never hardcoded here), writes PDFs as .pdf and web pages as
markdown .md, and registers EVERY entry (fetched / fetch_failed / excluded_by_rule /
oversize_needs_clearance) in corpus/staging/candidate_register.jsonl plus a machine-readable
_fetch_register.json for Phase 3. Zero LLM spend: this script never calls a model and refuses
to run if ANTHROPIC_API_KEY is set (DD-007 posture).

Acquisition path mirrors docs/research/bulk_acquisition_report.md: PDFs direct via httpx;
web pages -> markdown via crawl4ai `crwl` (its pruning filter does the boilerplate stripping;
nothing is hand-edited); a min-content guard rejects blank captures. Two additions, both
forced by what the hosts actually do: (1) hosts that serve an anti-bot challenge to the
headless browser (www.w3.org) fall back to httpx + a DOM->markdown converter; (2) AUTH-4
extent trims (drop whole h2 sections by regex) are applied on the DOM for oversize specs.

Idempotent: a doc_id whose fetch already succeeded (present in _fetch_register.json with
status `fetched` and the file's sha256 still matching) is skipped; register lines are never
duplicated for the same doc_id + discovered_via. Nothing here manifest-adds (Phase 3 does that).

Usage:
    /opt/anaconda3/bin/python3 scripts/harvest_kernel.py [--only DOC_ID ...] [--dry-run] [--force]
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import httpx
import yaml
from bs4 import BeautifulSoup, NavigableString, Tag

REPO = Path(__file__).resolve().parents[1]
KERNEL_LIST = REPO / "scripts" / "kernel_list.yaml"
INBOX = REPO / "corpus" / "staging" / "inbox" / "kernel"
FETCH_REGISTER = INBOX / "_fetch_register.json"
CANDIDATE_REGISTER = REPO / "corpus" / "staging" / "candidate_register.jsonl"
REFETCH_CANDIDATES = REPO / "corpus" / "staging" / "refetch_candidates.jsonl"
MANIFEST = REPO / "corpus" / "manifest.json"
TASK_REF = "cc_tasks/2026-08-21_v03_visibility_kernel.md Phase 2"

STATUSES = ("fetched", "fetch_failed", "excluded_by_rule", "oversize_needs_clearance")


# ----------------------------------------------------------------------------- helpers
def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def log(msg: str) -> None:
    print(f"[{utc_now()}] {msg}", flush=True)


def http_date_to_iso(value: str | None) -> str | None:
    if not value:
        return None
    from email.utils import parsedate_to_datetime
    try:
        return parsedate_to_datetime(value).astimezone(dt.timezone.utc).strftime("%Y-%m-%d")
    except (TypeError, ValueError):
        return None


def pdf_date_to_iso(value: str | None) -> str | None:
    # PDF dates look like D:20230922143000-04'00'
    if not value:
        return None
    m = re.search(r"(\d{4})(\d{2})(\d{2})", str(value))
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else None


def pdf_text_and_meta(data: bytes) -> tuple[str, dict]:
    from pypdf import PdfReader
    reader = PdfReader(io.BytesIO(data))
    text = "\n".join((page.extract_text() or "") for page in reader.pages)
    meta = {}
    try:
        md = reader.metadata or {}
        meta = {k: str(v) for k, v in md.items()}
    except Exception as exc:  # pypdf raises assorted exceptions on odd metadata; record, don't hide
        meta = {"_metadata_error": f"{type(exc).__name__}: {exc}"}
    return text, meta


# ----------------------------------------------------------------------------- DOM -> markdown
BLOCK_SKIP = {"script", "style", "noscript", "svg", "canvas", "iframe", "template"}


class DomMarkdown:
    """Small, faithful HTML->markdown for spec pages (headings, paragraphs, lists, tables, code,
    definition lists). Does not paraphrase or drop body text; `nav` elements are dropped as
    boilerplate. Keeps heading levels so AUTH-4 extents are auditable by section."""

    def __init__(self) -> None:
        self.out: list[str] = []

    def render(self, root: Tag) -> str:
        self._walk(root)
        text = "\n".join(self.out)
        text = re.sub(r"[ \t]+\n", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip() + "\n"

    def _inline(self, node) -> str:
        if isinstance(node, NavigableString):
            return re.sub(r"\s+", " ", str(node))
        if not isinstance(node, Tag) or node.name in BLOCK_SKIP:
            return ""
        if node.name == "br":
            return "\n"
        if node.name == "code":
            inner = "".join(self._inline(c) for c in node.children)
            return f"`{inner}`" if inner.strip() else inner
        if node.name in ("strong", "b"):
            return f"**{''.join(self._inline(c) for c in node.children)}**"
        if node.name in ("em", "i"):
            return f"*{''.join(self._inline(c) for c in node.children)}*"
        return "".join(self._inline(c) for c in node.children)

    def _walk(self, node) -> None:
        if isinstance(node, NavigableString):
            s = re.sub(r"\s+", " ", str(node))
            if s.strip():
                self.out.append(s.strip())
            return
        if not isinstance(node, Tag) or node.name in BLOCK_SKIP or node.name == "nav":
            return
        n = node.name
        if n in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.out.append("")
            self.out.append("#" * int(n[1]) + " " + self._inline(node).strip())
            self.out.append("")
        elif n == "p":
            self.out.append(self._inline(node).strip())
            self.out.append("")
        elif n == "pre":
            self.out.append("```")
            self.out.append(node.get_text().rstrip("\n"))
            self.out.append("```")
            self.out.append("")
        elif n in ("ul", "ol"):
            self._list(node, 0)
            self.out.append("")
        elif n == "table":
            self._table(node)
        elif n == "dl":
            for child in node.children:
                if isinstance(child, Tag) and child.name == "dt":
                    self.out.append("**" + self._inline(child).strip() + "**")
                elif isinstance(child, Tag) and child.name == "dd":
                    self.out.append(": " + self._inline(child).strip())
            self.out.append("")
        elif n == "blockquote":
            sub = DomMarkdown()
            for c in node.children:
                sub._walk(c)
            self.out.extend("> " + line for line in "\n".join(sub.out).splitlines())
            self.out.append("")
        else:
            for c in node.children:
                self._walk(c)

    def _list(self, node: Tag, depth: int) -> None:
        ordered = node.name == "ol"
        i = 0
        for li in node.children:
            if not isinstance(li, Tag) or li.name != "li":
                continue
            i += 1
            marker = f"{i}." if ordered else "-"
            inline_parts, nested = [], []
            for c in li.children:
                if isinstance(c, Tag) and c.name in ("ul", "ol"):
                    nested.append(c)
                elif isinstance(c, Tag) and c.name in ("p", "div"):
                    inline_parts.append(self._inline(c))
                else:
                    inline_parts.append(self._inline(c))
            text = re.sub(r"\s+", " ", "".join(inline_parts)).strip()
            self.out.append("  " * depth + f"{marker} {text}")
            for sub in nested:
                self._list(sub, depth + 1)

    def _table(self, node: Tag) -> None:
        rows = []
        for tr in node.find_all("tr"):
            cells = [re.sub(r"\s+", " ", self._inline(td)).strip().replace("|", "\\|")
                     for td in tr.find_all(["th", "td"], recursive=False)]
            if cells:
                rows.append(cells)
        if not rows:
            return
        width = max(len(r) for r in rows)
        rows = [r + [""] * (width - len(r)) for r in rows]
        self.out.append("| " + " | ".join(rows[0]) + " |")
        self.out.append("|" + "---|" * width)
        for r in rows[1:]:
            self.out.append("| " + " | ".join(r) + " |")
        self.out.append("")


def apply_extent(soup: BeautifulSoup, drop_h2: list[str]) -> list[str]:
    """Drop whole h2 sections whose heading matches any regex. Returns the headings dropped.
    Handles both nested markup (ReSpec: <section><h2/>...</section>) and flat markup (Bikeshed:
    <h2/> then sibling <h3>/<section> blocks): starting from the h2's container, every following
    sibling up to the next element that is, or contains, an h2 belongs to the section."""
    dropped: list[str] = []
    pats = [re.compile(p) for p in drop_h2]
    for h2 in list(soup.find_all("h2")):
        if h2.decomposed if hasattr(h2, "decomposed") else False:
            continue
        title = h2.get_text(" ", strip=True)
        if not any(p.search(title) for p in pats):
            continue
        dropped.append(title)
        # climb to the outermost wrapper whose first h2 is this heading (ReSpec <section>, the
        # OpenAPI site's <section><div class="header-wrapper"><h2/></div>..., etc.)
        container = h2
        parent = h2.parent
        while isinstance(parent, Tag) and parent.name in ("section", "div") and parent.find("h2") is h2:
            container = parent
            parent = parent.parent
        sib = container.next_sibling
        while sib is not None:
            nxt = sib.next_sibling
            if isinstance(sib, Tag) and (sib.name == "h2" or sib.find("h2") is not None):
                break
            if isinstance(sib, Tag):
                sib.decompose()
            else:
                sib.extract()
            sib = nxt
        container.decompose()
    return dropped


def html_declared_dates(soup: BeautifulSoup) -> tuple[str | None, str | None]:
    """Page-declared date: meta tags first, then <time datetime>, then ReSpec/W3C 'dt-published'."""
    keys = ("article:modified_time", "article:published_time", "last-modified", "dcterms.modified",
            "dcterms.date", "dcterms.issued", "dc.date", "date", "og:updated_time", "datePublished",
            "dateModified", "last_updated", "revised")
    for m in soup.find_all("meta"):
        k = (m.get("property") or m.get("name") or m.get("itemprop") or "").strip()
        if k.lower() in [x.lower() for x in keys] and m.get("content"):
            return _norm_date(m["content"]), f"meta:{k}"
    t = soup.find("time", attrs={"datetime": True})
    if t is not None:
        return _norm_date(t["datetime"]), "time[datetime]"
    for cls in ("dt-published", "dt-updated"):
        el = soup.find(class_=cls)
        if el is not None and el.get("datetime"):
            return _norm_date(el["datetime"]), f".{cls}"
    return None, None


def _norm_date(v: str) -> str | None:
    v = v.strip()
    m = re.match(r"(\d{4}-\d{2}-\d{2})", v)
    if m:
        return m.group(1)
    for fmt in ("%d %B %Y", "%B %d, %Y", "%b %d, %Y", "%Y%m%d"):
        try:
            return dt.datetime.strptime(v, fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass
    return None


# ----------------------------------------------------------------------------- fetchers
class Fetcher:
    def __init__(self, settings: dict, crwl_path: str | None) -> None:
        self.s = settings
        self.crwl_path = crwl_path
        self.client = httpx.Client(headers={"User-Agent": settings["user_agent"]},
                                   timeout=settings["timeout_seconds"], follow_redirects=True)
        self._filter_file = None
        if crwl_path:
            fd, path = tempfile.mkstemp(prefix="crwl_filter_", suffix=".yaml")
            with os.fdopen(fd, "w") as fh:
                yaml.safe_dump(settings["crwl_filter"], fh)
            self._filter_file = path

    def close(self) -> None:
        self.client.close()
        if self._filter_file and os.path.exists(self._filter_file):
            os.unlink(self._filter_file)

    # -- httpx with one retry (settings.retries)
    def get(self, url: str) -> httpx.Response:
        last: Exception | None = None
        for attempt in range(1 + int(self.s["retries"])):
            try:
                return self.client.get(url)
            except httpx.HTTPError as exc:
                last = exc
                log(f"    httpx {type(exc).__name__} on attempt {attempt + 1}: {url}")
                time.sleep(self.s["spacing_seconds"])
        assert last is not None
        raise last

    # -- crawl4ai: one call, JSON 'all' output -> raw + fit markdown + headers + metadata
    def crwl(self, url: str, crwl_params: str | None = None) -> dict:
        assert self.crwl_path
        with tempfile.TemporaryDirectory(prefix="crwl_out_") as td:
            out = Path(td) / "out.json"
            cmd = [self.crwl_path, "crawl", url, "-o", "all", "-f", self._filter_file, "-bc", "-O", str(out)]
            if crwl_params:  # per-entry crawler params from kernel_list.yaml (e.g. render waits for JS-only pages)
                cmd += ["-c", crwl_params]
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=self.s["crwl_timeout_seconds"])
            if not out.exists():
                raise RuntimeError(f"crwl produced no output (rc={proc.returncode}): {proc.stderr[-400:]}")
            return json.loads(out.read_text())


# ----------------------------------------------------------------------------- one entry
_SECRET_ENV_FALLBACK = Path.home() / ".wintermute" / ".env"


def secret_values(entry: dict) -> dict:
    """`secret_env: [NAME, ...]` on an entry -> {NAME: value} from the environment, falling
    back to ~/.wintermute/.env (the same fallback the Neo4j credentials use). Raises when a
    named secret is absent: an unauthenticated request in place of an authenticated one
    would silently fetch a different surface (api.census.gov redirects to a 'Missing Key'
    page). ANTHROPIC_API_KEY is refused by name (DD-007: never a model key)."""
    out = {}
    for name in entry.get("secret_env") or []:
        if name == "ANTHROPIC_API_KEY":
            raise RuntimeError("secret_env may not name ANTHROPIC_API_KEY (DD-007)")
        val = os.environ.get(name)
        if not val and _SECRET_ENV_FALLBACK.is_file():
            for line in _SECRET_ENV_FALLBACK.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line.startswith(f"{name}="):
                    val = line.split("=", 1)[1].strip().strip("'\"")
                    break
        if not val:
            raise RuntimeError(f"secret_env {name} is not set (environment or {_SECRET_ENV_FALLBACK})")
        out[name] = val
    return out


def expand_secrets(url: str, secrets: dict) -> str:
    for name, val in secrets.items():
        url = url.replace("{" + name + "}", val)
    return url


def redact_secrets(text: str, secrets: dict) -> str:
    for name, val in secrets.items():
        text = text.replace(val, "{" + name + "}")
    return text


def _redact_record(rec: dict, secrets: dict) -> None:
    if not secrets:
        return
    for k in ("final_url", "reason"):
        if isinstance(rec.get(k), str):
            rec[k] = redact_secrets(rec[k], secrets)
    rec["urls_tried"] = [redact_secrets(u, secrets) for u in rec.get("urls_tried") or []]
    if isinstance(rec.get("_text"), str):
        rec["_text"] = redact_secrets(rec["_text"], secrets)
    if isinstance(rec.get("_bytes"), (bytes, bytearray)):
        rec["_bytes"] = redact_secrets(rec["_bytes"].decode("utf-8", errors="surrogateescape"), secrets).encode("utf-8", errors="surrogateescape")


def fetch_entry(entry: dict, fx: Fetcher, settings: dict, dry_run: bool) -> dict:
    """Returns a record dict with candidate_status and evidence fields. Never raises on a fetch
    failure: every failure mode becomes candidate_status=fetch_failed with `reason` and `urls_tried`."""
    rec = {
        "doc_id": entry["doc_id"], "title": entry["title"], "primary_url": entry.get("primary_url"),
        "source_type": entry["source_type"], "clause": entry["clause"],
        "authors_or_org": entry.get("authors_or_org", []), "task_item": entry.get("task_item"),
        "task_note": entry.get("task_note"), "extent_note": entry.get("extent_note"),
        "retrieved_at_utc": utc_now(), "urls_tried": [], "fetch_method": None,
        "local_path": None, "sha256": None, "bytes": None, "chars": None, "as_of": None,
        "as_of_source": None, "final_url": None, "http_status": None, "content_type": None,
        "candidate_status": None, "reason": None, "extent_dropped_sections": None,
    }
    if dry_run:
        rec["candidate_status"] = "dry_run"
        return rec

    INBOX.mkdir(parents=True, exist_ok=True)
    # Request-time secrets (task 2026-09-03_g1_eval_v2 step 2): an entry may name env vars
    # in `secret_env`; `{NAME}` placeholders in its URLs are expanded only for the request
    # and every recorded string (urls_tried, final_url, reason, the capture header) carries
    # the placeholder back, so no key value reaches a register, an event or a corpus file.
    # A missing secret fails here, before any request (never a silent unauthenticated fetch).
    secrets = secret_values(entry)
    # Primary URL first, then the entry's documented alternates (each attempt is recorded in urls_tried).
    urls = [entry.get("pdf_url") or entry.get("raw_url") or entry["primary_url"]] + list(entry.get("alt_urls", []))
    for i, url in enumerate(urls):
        url = expand_secrets(url, secrets)
        if i:
            time.sleep(settings["spacing_seconds"])
            log(f"    trying alternate URL: {redact_secrets(url, secrets)}")
        for k in ("_text", "_bytes", "_ext"):
            rec.pop(k, None)
        rec["candidate_status"], rec["reason"] = None, None
        try:
            if entry.get("pdf_url"):
                _fetch_pdf(entry, fx, rec, url)
            elif entry.get("fetcher") == "raw":
                _fetch_raw(entry, fx, rec, url)
            elif entry.get("fetcher") == "httpx_dom":
                _fetch_dom(entry, fx, rec, url)
            else:
                _fetch_crwl_with_fallback(entry, fx, rec, settings, url)
        except httpx.HTTPError as exc:
            rec["candidate_status"], rec["reason"] = "fetch_failed", f"httpx {type(exc).__name__}: {exc}"
            _redact_record(rec, secrets)
            continue
        except (subprocess.TimeoutExpired, RuntimeError, json.JSONDecodeError) as exc:
            rec["candidate_status"], rec["reason"] = "fetch_failed", f"{type(exc).__name__}: {str(exc)[:300]}"
            _redact_record(rec, secrets)
            continue
        _redact_record(rec, secrets)
        if rec["candidate_status"] == "fetch_failed":
            continue
        if len(rec["_text"].strip()) < settings["min_content_chars"]:
            rec["candidate_status"] = "fetch_failed"
            rec["reason"] = (f"min-content guard: {len(rec['_text'].strip())} chars of text (< {settings['min_content_chars']}); "
                             f"capture not kept [status={rec.get('http_status')}, final_url={str(rec.get('final_url'))[:100]}]")
            continue
        break
    if rec["candidate_status"] == "fetch_failed":
        for k in ("_text", "_bytes", "_ext"):
            rec.pop(k, None)
        return rec

    # AUTH-4 extent rule
    text = rec.pop("_text")
    data = rec.pop("_bytes")
    ext = rec.pop("_ext")
    rec["chars"] = len(text)
    rec["sha256"] = sha256_bytes(data)
    rec["bytes"] = len(data)
    if rec["chars"] > settings["max_doc_chars"]:
        rec["candidate_status"] = "oversize_needs_clearance"
        rec["reason"] = (f"{rec['chars']} chars > MAX_DOC_CHARS {settings['max_doc_chars']}"
                         + (" after the configured extent trim" if entry.get("extent") else "; no stated-extent version configured"))
        target = INBOX / "oversize" / f"{entry['doc_id']}{ext}"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        rec["local_path"] = str(target.relative_to(REPO))
        return rec
    target = INBOX / f"{entry['doc_id']}{ext}"
    target.write_bytes(data)
    rec["local_path"] = str(target.relative_to(REPO))
    rec["candidate_status"] = "fetched"
    return rec


def _fetch_pdf(entry: dict, fx: Fetcher, rec: dict, url: str) -> None:
    rec["urls_tried"].append(url)
    r = fx.get(url)
    rec["http_status"], rec["final_url"] = r.status_code, str(r.url)
    rec["content_type"] = r.headers.get("content-type")
    rec["fetch_method"] = "httpx-pdf"
    if r.status_code != 200 or b"%PDF" not in r.content[:1024]:
        rec["candidate_status"] = "fetch_failed"
        rec["reason"] = f"HTTP {r.status_code} / not a PDF ({rec['content_type']}) [final_url={str(r.url)[:100]}]"
        return
    text, meta = pdf_text_and_meta(r.content)
    rec["pdf_metadata"] = meta
    rec["as_of"], rec["as_of_source"] = None, None
    for key in ("/ModDate", "/CreationDate"):
        if meta.get(key):
            rec["as_of"], rec["as_of_source"] = pdf_date_to_iso(meta[key]), f"pdf:{key}"
            break
    if not rec["as_of"]:
        rec["as_of"], rec["as_of_source"] = http_date_to_iso(r.headers.get("last-modified")), "http:Last-Modified"
    if not rec["as_of"]:
        rec["as_of_source"] = "none (no PDF date, no Last-Modified)"
    rec["_text"], rec["_bytes"], rec["_ext"] = text, r.content, ".pdf"


def _fetch_raw(entry: dict, fx: Fetcher, rec: dict, url: str) -> None:
    rec["urls_tried"].append(url)
    r = fx.get(url)
    rec["http_status"], rec["final_url"] = r.status_code, str(r.url)
    rec["content_type"] = r.headers.get("content-type")
    rec["fetch_method"] = "httpx-raw"
    if r.status_code != 200:
        rec["candidate_status"] = "fetch_failed"
        rec["reason"] = f"HTTP {r.status_code} [final_url={str(r.url)[:100]}]"
        return
    text = r.text
    rec["as_of"] = http_date_to_iso(r.headers.get("last-modified"))
    rec["as_of_source"] = "http:Last-Modified" if rec["as_of"] else "none (raw file; no Last-Modified header)"
    # The header carries no timestamp on purpose: identical content must hash identically across re-runs
    # (retrieved_at_utc lives in the registers).
    header = (f"<!-- kernel harvest: {TASK_REF}; primary_url={entry['primary_url']}; raw_url={url} -->\n\n")
    body = (header + text).encode("utf-8")
    rec["_text"], rec["_bytes"], rec["_ext"] = text, body, ".md"


def _fetch_dom(entry: dict, fx: Fetcher, rec: dict, url: str) -> None:
    rec["urls_tried"].append(url)
    r = fx.get(url)
    rec["http_status"], rec["final_url"] = r.status_code, str(r.url)
    rec["content_type"] = r.headers.get("content-type")
    rec["fetch_method"] = "httpx-dom"
    if r.status_code != 200:
        rec["candidate_status"] = "fetch_failed"
        rec["reason"] = f"HTTP {r.status_code} [final_url={str(r.url)[:100]}]"
        return
    soup = BeautifulSoup(r.text, "lxml")
    rec["as_of"], rec["as_of_source"] = html_declared_dates(soup)
    if not rec["as_of"]:
        rec["as_of"] = http_date_to_iso(r.headers.get("last-modified"))
        rec["as_of_source"] = "http:Last-Modified" if rec["as_of"] else "none (no page date, no Last-Modified)"
    dropped = apply_extent(soup, entry["extent"]["drop_h2"]) if entry.get("extent") else []
    rec["extent_dropped_sections"] = dropped
    page_title = soup.title.get_text(strip=True) if soup.title else entry["title"]
    body = soup.body or soup
    md = DomMarkdown().render(body)
    header = (f"<!-- kernel harvest: {TASK_REF}; primary_url={entry['primary_url']}; final_url={r.url}; "
              f"fetch_method=httpx-dom; page_title={page_title!r}"
              + (f"; extent_dropped_sections={dropped!r}" if dropped else "") + " -->\n\n")
    rec["_text"], rec["_bytes"], rec["_ext"] = md, (header + md).encode("utf-8"), ".md"


def _fetch_crwl_with_fallback(entry: dict, fx: Fetcher, rec: dict, settings: dict, url: str) -> None:
    if not fx.crwl_path:
        log("    crwl unavailable; using httpx-dom fallback")
        _fetch_dom(entry, fx, rec, url)
        return
    rec["urls_tried"].append(url)
    try:
        res = fx.crwl(url, entry.get("crwl_params"))
    except (subprocess.TimeoutExpired, RuntimeError, json.JSONDecodeError) as exc:
        log(f"    crwl failed ({type(exc).__name__}); falling back to httpx-dom")
        rec["crwl_error"] = f"{type(exc).__name__}: {str(exc)[:200]}"
        _fetch_dom(entry, fx, rec, url)
        return
    md = res.get("markdown") or {}
    raw = (md.get("raw_markdown") if isinstance(md, dict) else md) or ""
    fit = (md.get("fit_markdown") if isinstance(md, dict) else "") or ""
    headers = {k.lower(): v for k, v in (res.get("response_headers") or {}).items()}
    rec["http_status"] = res.get("status_code")
    rec["final_url"] = res.get("redirected_url") or res.get("url") or url
    rec["content_type"] = headers.get("content-type")
    rec["fetch_method"] = "crwl"
    challenged = any(m in raw[:4000] for m in settings["challenge_markers"]) and len(raw) < 8000
    if not res.get("success") or challenged or (rec["http_status"] or 0) >= 400:
        why = "anti-bot challenge page" if challenged else f"success={res.get('success')} status={rec['http_status']} {str(res.get('error_message'))[:160]}"
        log(f"    crwl returned no usable page ({why}); falling back to httpx-dom")
        rec["crwl_error"] = why
        _fetch_dom(entry, fx, rec, url)
        return
    # markdown variant: crwl's pruned fit_markdown unless pruning removed most of the page
    use_fit = bool(fit.strip()) and len(fit) >= settings["fit_min_fraction_of_raw"] * len(raw)
    text = fit if use_fit else raw
    rec["markdown_variant"] = "fit_markdown" if use_fit else "raw_markdown"
    rec["raw_markdown_chars"], rec["fit_markdown_chars"] = len(raw), len(fit)
    meta = res.get("metadata") or {}
    rec["page_title"] = meta.get("title")
    rec["as_of"], rec["as_of_source"] = None, None
    for k in ("article:modified_time", "article:published_time", "last-modified", "dcterms.modified",
              "dcterms.date", "date", "og:updated_time", "dateModified", "datePublished"):
        if meta.get(k):
            rec["as_of"], rec["as_of_source"] = _norm_date(str(meta[k])), f"meta:{k}"
            if rec["as_of"]:
                break
    if not rec["as_of"]:
        rec["as_of"] = http_date_to_iso(headers.get("last-modified"))
        rec["as_of_source"] = "http:Last-Modified" if rec["as_of"] else "none (no page date, no Last-Modified)"
    header = (f"<!-- kernel harvest: {TASK_REF}; primary_url={url}; final_url={rec['final_url']}; "
              f"fetch_method=crwl/{rec['markdown_variant']}; "
              f"page_title={rec['page_title']!r} -->\n\n")
    rec["_text"], rec["_bytes"], rec["_ext"] = text, (header + text).encode("utf-8"), ".md"


# ----------------------------------------------------------------------------- registers
def load_fetch_register() -> dict:
    if FETCH_REGISTER.exists():
        return json.loads(FETCH_REGISTER.read_text())
    return {"task": TASK_REF, "kernel_list": str(KERNEL_LIST.relative_to(REPO)), "records": {}}


def save_fetch_register(reg: dict) -> None:
    reg["updated_at_utc"] = utc_now()
    FETCH_REGISTER.write_text(json.dumps(reg, indent=1, ensure_ascii=False) + "\n")


def existing_register_keys(path: Path, discovered_via: str) -> dict[str, tuple]:
    """doc_id -> (candidate_status, sha256) of the latest line registered under this discovered_via.
    The register is append-only: a re-run appends a new line only when status or content hash changed."""
    keys: dict[str, tuple] = {}
    if not path.exists():
        return keys
    with path.open() as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            if discovered_via in (obj.get("discovered_via") or []) and obj.get("doc_id"):
                keys[obj["doc_id"]] = (obj.get("candidate_status"), obj.get("sha256"))
    return keys


def candidate_line(entry: dict, rec: dict, settings: dict) -> dict:
    status_map = {"fetched": "staged", "fetch_failed": "needs_source",
                  "excluded_by_rule": "excluded", "oversize_needs_clearance": "needs_clearance"}
    year = entry.get("year") or (rec.get("as_of") or "")[:4] or None
    url = entry.get("primary_url") or ""
    dedup = ("arxiv:" + re.search(r"(\d{4}\.\d{5})", url).group(1)) if "arxiv.org" in url and re.search(r"(\d{4}\.\d{5})", url) \
        else ("url:" + re.sub(r"^https?://(www\.)?", "", url).rstrip("/") if url else f"docid:{entry['doc_id']}")
    return {
        "title": entry["title"], "primary_url": entry.get("primary_url"),
        "authors": entry.get("authors_or_org", []), "year": year, "source_type": entry["source_type"],
        "discovered_via": [settings["discovered_via"]],
        "notes": "; ".join(x for x in (entry.get("task_item"), entry.get("task_note")) if x),
        "dedup_key": dedup, "status": status_map[rec["candidate_status"]],
        "decision_reason": rec.get("reason") or f"kernel list clause ({rec['clause']}); {rec['candidate_status']}",
        "decided_at": rec["retrieved_at_utc"][:10], "decided_by": "cc",
        "candidate_status": rec["candidate_status"], "clause": rec["clause"], "doc_id": entry["doc_id"],
        "local_path": rec.get("local_path"), "sha256": rec.get("sha256"), "chars": rec.get("chars"),
        "as_of": rec.get("as_of"), "retrieved_at_utc": rec["retrieved_at_utc"], "final_url": rec.get("final_url"),
        "extent_note": rec.get("extent_note"),
        "urls_tried": rec.get("urls_tried", []), "http_status": rec.get("http_status"),
    }


def refetch_line(entry: dict, rec: dict) -> dict:
    # same shape family as the 721 pre-existing lines (candidate_id / status / note / surfaced_by) + reason
    return {"candidate_id": entry["doc_id"], "reason": "oversize_needs_clearance", "status": "oversize_needs_clearance",
            "primary_url": entry.get("primary_url"), "chars": rec.get("chars"), "local_path": rec.get("local_path"),
            "extent_note": rec.get("extent_note"), "note": rec.get("reason"),
            "surfaced_by": f"{TASK_REF} (AUTH-4)", "surfaced_at_utc": rec["retrieved_at_utc"]}


def manifest_index() -> tuple[set[str], set[str]]:
    m = json.loads(MANIFEST.read_text())
    ids, urls = set(), set()
    for doc_id, e in m["entries"].items():
        ids.add(doc_id)
        u = (e.get("identity") or {}).get("source_url")
        if u:
            urls.add(re.sub(r"^https?://(www\.)?", "", u).rstrip("/"))
    return ids, urls


# ----------------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", nargs="*", default=None, help="restrict to these doc_ids")
    ap.add_argument("--dry-run", action="store_true", help="list what would be fetched; no network, no writes")
    ap.add_argument("--force", action="store_true", help="re-fetch even if already fetched")
    args = ap.parse_args()

    if os.environ.get("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY is set; this task runs with zero model spend and refuses to start (DD-007).", file=sys.stderr)
        return 2
    cfg = yaml.safe_load(KERNEL_LIST.read_text())
    settings, entries = cfg["settings"], cfg["entries"]
    for key in ("user_agent", "discovered_via", "max_doc_chars", "min_content_chars", "timeout_seconds",
                "retries", "spacing_seconds", "crwl_timeout_seconds", "crwl_filter", "fit_min_fraction_of_raw",
                "challenge_markers"):
        if key not in settings:
            print(f"kernel_list.yaml settings missing required key: {key}", file=sys.stderr)
            return 2
    ids = [e["doc_id"] for e in entries]
    if len(ids) != len(set(ids)):
        print("duplicate doc_id in kernel_list.yaml", file=sys.stderr)
        return 2
    if args.only:
        entries = [e for e in entries if e["doc_id"] in set(args.only)]

    crwl_path = shutil.which("crwl") or next((p for p in ("/opt/anaconda3/bin/crwl", os.path.expanduser("~/.bun/bin/crwl")) if os.path.exists(p)), None)
    log(f"crwl: {crwl_path or 'NOT FOUND (httpx-dom fallback for all HTML)'}")
    manifest_ids, manifest_urls = manifest_index()

    reg = load_fetch_register()
    done_keys = existing_register_keys(CANDIDATE_REGISTER, settings["discovered_via"])
    fx = Fetcher(settings, crwl_path)
    counts = {s: 0 for s in STATUSES}
    counts["skipped_already_fetched"] = 0
    try:
        for entry in entries:
            did = entry["doc_id"]
            prev = reg["records"].get(did)
            if prev and prev.get("candidate_status") == "fetched" and not args.force:
                p = REPO / prev["local_path"]
                if p.exists() and sha256_bytes(p.read_bytes()) == prev["sha256"]:
                    counts["skipped_already_fetched"] += 1
                    log(f"skip (already fetched, sha ok): {did}")
                    continue
            log(f"{did}")
            # exclusions decided without fetching
            url_key = re.sub(r"^https?://(www\.)?", "", entry.get("primary_url") or "").rstrip("/")
            if entry.get("already_manifested") or did in manifest_ids or (url_key and url_key in manifest_urls):
                rec = {"doc_id": did, "title": entry["title"], "primary_url": entry.get("primary_url"), "clause": entry["clause"],
                       "source_type": entry["source_type"], "retrieved_at_utc": utc_now(), "candidate_status": "excluded_by_rule",
                       "reason": "already_manifested", "urls_tried": [], "extent_note": None, "task_item": entry.get("task_item")}
            elif entry.get("inbox_glob"):
                hits = sorted(REPO.glob(entry["inbox_glob"]))
                if hits:
                    src = hits[0]
                    data = src.read_bytes()
                    text = pdf_text_and_meta(data)[0] if src.suffix.lower() == ".pdf" else data.decode("utf-8", "replace")
                    target = INBOX / f"{did}{src.suffix.lower()}"
                    target.write_bytes(data)
                    rec = {"doc_id": did, "title": entry["title"], "primary_url": None, "clause": entry["clause"], "source_type": entry["source_type"],
                           "retrieved_at_utc": utc_now(), "candidate_status": "fetched", "reason": f"copied from inbox: {src.name}",
                           "local_path": str(target.relative_to(REPO)), "sha256": sha256_bytes(data), "bytes": len(data), "chars": len(text),
                           "as_of": None, "as_of_source": "none (inbox file)", "urls_tried": [], "extent_note": None, "task_item": entry.get("task_item")}
                else:
                    # Rule text: "Exclude ... anything without a stable URL or a fetchable primary text."
                    rec = {"doc_id": did, "title": entry["title"], "primary_url": None, "clause": entry["clause"], "source_type": entry["source_type"],
                           "retrieved_at_utc": utc_now(), "candidate_status": "excluded_by_rule",
                           "reason": f"no_fetchable_primary_text: no file matching {entry['inbox_glob']} in inbox (Phase 0 also found none) and no URL",
                           "urls_tried": [], "extent_note": None, "task_item": entry.get("task_item"), "task_note": entry.get("task_note")}
            else:
                rec = fetch_entry(entry, fx, settings, args.dry_run)
                time.sleep(settings["spacing_seconds"])
            if args.dry_run:
                print(f"  would fetch: {entry.get('pdf_url') or entry.get('raw_url') or entry.get('primary_url')} via {entry.get('fetcher') or ('pdf' if entry.get('pdf_url') else 'crwl')}")
                continue
            st = rec["candidate_status"]
            counts[st] += 1
            log(f"  -> {st}" + (f" ({rec.get('reason')})" if rec.get("reason") else "") + (f" chars={rec.get('chars')}" if rec.get("chars") else ""))
            reg["records"][did] = rec
            save_fetch_register(reg)
            key = (st, rec.get("sha256"))
            if done_keys.get(did) != key:
                with CANDIDATE_REGISTER.open("a") as fh:
                    fh.write(json.dumps(candidate_line(entry, rec, settings), ensure_ascii=False) + "\n")
                done_keys[did] = key
            else:
                log(f"  (register line for {did} with status {st} and same sha256 already present; not duplicated)")
            if st == "oversize_needs_clearance":
                with REFETCH_CANDIDATES.open("a") as fh:
                    fh.write(json.dumps(refetch_line(entry, rec), ensure_ascii=False) + "\n")
    finally:
        fx.close()
    if not args.dry_run:
        reg["counts"] = counts
        save_fetch_register(reg)
    log("counts: " + json.dumps(counts))
    return 0


if __name__ == "__main__":
    sys.exit(main())
