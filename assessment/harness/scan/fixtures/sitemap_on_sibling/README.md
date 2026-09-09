# `sitemap_on_sibling`

A host whose `robots.txt` declares its sitemap on a **second netloc of the same site**.

This directory holds one file, `robots.txt`. Everything else is served from `passes_all`, so
"a well-formed surface" keeps exactly one definition on disk; the overlay exists because this
fixture differs from `passes_all` in precisely one byte-range, the `Sitemap:` line.

## What it reproduces

`cc_tasks/2026-09-09_report_draft_RESULT.md` §3. Cycle 3 issued

```
GET https://samhsa.gov/sitemap.xml
GET https://data.gov/sitemap.xml
```

after reading `www.samhsa.gov/robots.txt` and `www.data.gov/robots.txt` and following the
`Sitemap:` line each declared. Neither apex netloc's own `robots.txt` was fetched first, which
this scanner's manners require of every request it makes. `scan_2026-09-07b`'s RESULT §2 said
the opposite, and the request log falsified it.

## The two-netloc mechanism, and why it is the right one

The primary and the sibling are **two ports on `127.0.0.1`**. That gives the two properties the
defect needs and nothing else:

* **Different netloc.** `127.0.0.1:A` and `127.0.0.1:B` are distinct authorities, so the
  sibling has its own `robots.txt` that a compliant client must fetch before touching it. A
  single server could not express "the declared URL is somewhere this cycle has not read
  robots for".
* **Same site.** The WHATWG URL and Fetch standards define a site as the scheme plus the
  registrable domain, and the **port is not part of it**. An IP-literal host has no registrable
  domain, so the host itself is the site key and both ports resolve to one site. That is the
  same relation `www.samhsa.gov` has to `samhsa.gov` (one registrable domain, two netlocs), so
  the fixture reproduces the real shape rather than a neighbouring one.

Two hostnames would have needed an `/etc/hosts` entry, which is machine state a test may not
depend on. Two schemes would have changed the site. Two ports is the only mechanism that moves
the netloc without moving the site, using nothing but the loopback interface.

## Expected behaviour

Before the fix, and this is the defect: the sitemap collector dereferences the declared URL
with `fetcher.raw_get` and the sibling receives `GET /sitemap.xml` with **no prior
`GET /robots.txt`**.

After the fix the sibling receives its own `robots.txt` first, and only then the sitemap. The
verdict on A5 does not change, because a same-site sibling is in scope under the contact bound;
what changes is that the request is made politely. An **off-site** declaration is a different
case and is not this fixture: that one is observed and never fetched.
