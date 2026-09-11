# Suite tiers. `cc_tasks/2026-09-09_guards_earn_their_keep.md` decision 4.
#
# No test is removed or weakened by the split. A marker decides which tier waits for what:
#
#   gate-fast  the per-task gate. Everything except `slow`, which is the loopback control
#              cycles at the standing 1 req/s and the re-derivation of payloads older than the
#              two most recent cycles.
#   gate-task  what a task's gate actually is: the fast tier PLUS the re-derivation of every
#              payload the task could have touched. If a rule or the engine changed, that is
#              all of them, and `RECENT=` is how you say so.
#   gate-full  the pre-push check, under the long-running protocol (CLAUDE.md): detached,
#              logged to logs/, polled to EXIT.
#
# The point of the split is that a two-minute gate exists at all. The full suite still runs
# before every push, and a green fast tier is never reported as a green suite.

PY := /opt/anaconda3/bin/python3
LOGS := logs

.PHONY: gate-fast gate-task gate-full guards report-pdf

gate-fast:
	$(PY) -m pytest tests/ assessment/ -q -m "not slow"

## Re-derivation of every stored payload, whatever its age. Run this whenever a rule module,
## the rule registry, or the re-derivation engine changed.
gate-task: gate-fast
	$(PY) -m pytest tests/test_scan_harness_v4.py -q -k re_derives

## Every guard against the incident it was built for, and every control fixture that replays
## one. `cc_tasks/2026-09-11_absence_claims_under_scope_limitation.md` decision 5 adds the
## eighth fixture: it is the first control to catch a live instance of the blind-probe family
## rather than a payload being read after the fact, and its replay belongs beside the others.
guards:
	$(PY) -m pytest tests/test_guards_replay_their_incidents.py \
		tests/test_control_fixture_robots_forbids_product.py -q

gate-full:
	@mkdir -p $(LOGS)
	nohup sh -c '$(PY) -m pytest tests/ assessment/ -q; echo EXIT=$$? >> $(LOGS)/suite.log' \
		> $(LOGS)/suite.log 2>&1 & \
	echo "started; poll with: tail -5 $(LOGS)/suite.log"

# ---------------------------------------------------------------- the L0 report as a PDF
#
# `cc_tasks/2026-09-10_report_pdf.md` decision 1: the PDF is a BUILD PRODUCT, so the next
# revision is one command. `scripts/build_report_pdf.py` rebuilds the markdown first, so every
# {{result:...}} resolves from the graph and no number can be typed into the PDF.
#
# Toolchain, pinned to what is already installed (decision 1 forbids installing one):
#   pandoc 3.8.3   converter
#   typst  0.14.2  PDF engine. No LaTeX exists here; typst also renders SVG natively, which
#                  matters because F5 is an SVG the graph page already builds and decision 3
#                  says not to redraw it.
report-pdf:
	$(PY) scripts/build_report_pdf.py
	$(PY) -m pytest tests/test_report_pdf.py -q
