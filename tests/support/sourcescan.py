"""Scan Python source for a needle, reading CODE and not prose.

`cc_tasks/2026-09-10_harness_small.md` decision 4, prescribed for the class by
`cc_tasks/2026-09-10_virtual_time_RESULT.md` §5 item 6.

**Four times a source-scanning check in this repo has matched the text that talks about the
thing rather than the thing**, and each fix addressed the specific match:

* the AST gate detector read `Fetcher.allowed()` inside `robots.py`'s comment explaining why a
  rule does not call it, and reported that collector as gated;
* the self-licensing lint matched its own test file's string literal planting the bait;
* the suffix-list retirement check matched a comment mentioning "the tldextract retirement
  check", twice, in two different files.

The class is: **a scanner that treats source as text will match the text that talks about the
thing.** The fix is to look at code. `strip_prose` removes comments, docstrings and string
literals via the tokeniser, so a needle survives only where it is an identifier, an attribute or
a call — somewhere it does something.

`literals=False` is for the one check whose needle IS data rather than a name: the self-licensing
lint looks for `os.environ["AIRKG_SCAN_CYCLE"] = ...`, where the offence is the subscript KEY, so
blanking literals blinds it instead of sharpening it. Comments and docstrings still go — those
are prose under any reading. The line to hold is prose vs. code, not quoted vs. unquoted; for
most checks the two coincide, and for that one they do not.

Callers still assemble their needles from parts. That is a separate defence, against a file
matching its own scanner definition, and it is still needed: `strip_prose` cannot help a module
whose live code names the needle.
"""
from __future__ import annotations

import io
import tokenize
from pathlib import Path


#: A STRING token that opens a logical line is a docstring (module, class, function) or a
#: statement-position string — prose either way. Anything after these has an expression before
#: it, so the string is a value the code uses.
_LINE_START = (tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT, tokenize.ENCODING)


def strip_prose(source: str, literals: bool = True) -> str:
    """`source` with every comment and docstring blanked out; string literals too by default.

    Pass `literals=False` when the check's needle is itself quoted data — a dict key, an env
    var name — and blanking literals would hide the offence rather than the prose.

    Whitespace and line structure are preserved so a caller can still report a line number
    that means something. A file that does not tokenise (a syntax error, a partial fragment)
    comes back unchanged rather than silently empty: returning nothing would make every check
    pass on a file nobody could parse, which is the wrong direction for a guard.
    """
    try:
        toks = list(tokenize.generate_tokens(io.StringIO(source).readline))
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return source

    lines = source.splitlines(keepends=True)
    out = [list(line) for line in lines]
    at_line_start = True
    for tok in toks:
        if tok.type == tokenize.STRING and not literals and not at_line_start:
            continue                                   # a value, not prose
        if tok.type not in (tokenize.COMMENT, tokenize.NL):
            at_line_start = tok.type in _LINE_START
        if tok.type not in (tokenize.COMMENT, tokenize.STRING):
            continue
        (r1, c1), (r2, c2) = tok.start, tok.end
        for row in range(r1, r2 + 1):
            if row - 1 >= len(out):
                continue
            line = out[row - 1]
            start = c1 if row == r1 else 0
            end = c2 if row == r2 else len(line)
            for i in range(start, min(end, len(line))):
                if line[i] not in "\r\n":
                    line[i] = " "
    return "".join("".join(line) for line in out)


def scan(roots, needles, skip=(), literals: bool = True) -> list:
    """`[(relpath, lineno, line)]` where a needle appears in CODE under any of `roots`.

    `skip` is a set of path suffixes to leave out — a scanner's own test file, where the needle
    legitimately lives as a planted example. `literals` is passed through to `strip_prose`.
    """
    hits = []
    for root in roots:
        root = Path(root)
        for py in sorted(root.rglob("*.py")):
            if "__pycache__" in py.parts or any(str(py).endswith(s) for s in skip):
                continue
            src = py.read_text(encoding="utf-8")
            code = strip_prose(src, literals=literals)
            for i, line in enumerate(code.splitlines(), 1):
                if any(n in line for n in needles):
                    original = src.splitlines()[i - 1] if i - 1 < len(src.splitlines()) else ""
                    hits.append((str(py), i, original.strip()))
    return hits
