# Kernel inclusion rule — 2026-08-21 — task cc_tasks/2026-08-21_v03_visibility_kernel.md (Phase 2; applied by Phase 3 under AUTH-2)

Quoted verbatim from the task file, "Phase 2 — Kernel harvest to staging", *Inclusion rule*:

> Include if the document is one of: (a) a normative specification or its steward-published primer; (b) platform-official documentation from the operator of a search engine, crawler, CDN, or AI retrieval system; (c) peer-reviewed or preprint research on web/dataset discoverability, retrieval, or generative-engine behavior; (d) US federal digital-service guidance or statute bearing on public web data exposure; (e) SME/practitioner guidance already in the inbox. Exclude: vendor product marketing pages, SEO-agency blog posts, listicles, anything without a stable URL or a fetchable primary text. Exclusions are registered, not silently dropped.

Every entry in `scripts/kernel_list.yaml` carries a `clause` (a–e) naming which limb it is claimed under; Phase 3 records that clause as the per-document rationale in the manifest event.
