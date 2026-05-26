"""Statement coverage baseline.

The extracted dataset contains component and test files without the original
package dependency graph/runtime harness, so this module computes a reproducible
static proxy for statement coverage rather than claiming Istanbul runtime
coverage. It estimates whether source statements are exercised or asserted by
tests through shared component/API/state tokens.
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Any

_COMMENT_RE = re.compile(r"/\*.*?\*/|//.*?$", re.DOTALL | re.MULTILINE)
_STRING_RE = re.compile(r"(['\"`])(?:\\.|(?!\1).)*\1", re.DOTALL)
_TOKEN_RE = re.compile(r"[A-Za-z_$][A-Za-z0-9_$]*")
_STATEMENT_END_RE = re.compile(r"[;{}]\s*$")
_SKIP_LINE_PREFIXES = (
    "import ",
    "export {",
    "export *",
    "type ",
)
_STATEMENT_STARTS = (
    "const ",
    "let ",
    "var ",
    "function ",
    "class ",
    "return ",
    "if ",
    "for ",
    "while ",
    "switch ",
    "case ",
    "throw ",
    "try",
    "catch ",
    "useEffect",
    "React.",
)
_STOPWORDS = {
    "and",
    "args",
    "array",
    "async",
    "await",
    "boolean",
    "case",
    "catch",
    "class",
    "const",
    "default",
    "else",
    "false",
    "for",
    "from",
    "function",
    "if",
    "import",
    "let",
    "new",
    "null",
    "object",
    "props",
    "react",
    "return",
    "string",
    "switch",
    "this",
    "throw",
    "true",
    "try",
    "undefined",
    "var",
    "while",
}


def compute_statement_coverage_baseline(code: str, tests: str) -> dict[str, Any]:
    """Compute a static statement-coverage proxy for a source/test pair."""
    statements = _extract_statements(code)
    test_tokens = _tokens(tests)
    covered: list[dict[str, Any]] = []
    uncovered: list[dict[str, Any]] = []

    for idx, statement in enumerate(statements, start=1):
        st_tokens = _tokens(statement["text"])
        strong = _strong_tokens(statement["text"], st_tokens)
        hits = sorted((strong or st_tokens) & test_tokens)
        broad_hits = sorted(st_tokens & test_tokens)
        score = len(broad_hits) / max(len(st_tokens), 1)
        is_covered = bool(hits) and (len(hits) >= 2 or score >= 0.25)
        item = {
            "statement_index": idx,
            "line": statement["line"],
            "statement": statement["text"][:220],
            "hits": hits[:10],
            "overlap_score": round(score, 6),
        }
        if is_covered:
            covered.append(item)
        else:
            uncovered.append(item)

    total = len(statements)
    covered_n = len(covered)
    return {
        "kind": "statement_coverage_static_proxy",
        "method": (
            "Static token-overlap proxy over extracted source statements; "
            "not runtime Istanbul coverage."
        ),
        "total_statements": total,
        "covered_statements": covered_n,
        "uncovered_statements": total - covered_n,
        "statement_coverage_rate": round(covered_n / total, 6) if total else 0.0,
        "covered_statement_examples": covered[:8],
        "uncovered_statement_examples": uncovered[:8],
    }


def _strip_comments(text: str) -> str:
    return _COMMENT_RE.sub("", text or "")


def _tokens(text: str) -> set[str]:
    clean = _STRING_RE.sub(" ", text or "")
    return {
        tok.lower()
        for tok in _TOKEN_RE.findall(clean)
        if len(tok) >= 3 and tok.lower() not in _STOPWORDS
    }


def _strong_tokens(text: str, tokens: set[str]) -> set[str]:
    names = set(tokens)
    for tok in _TOKEN_RE.findall(text or ""):
        if tok[:1].isupper() or tok.startswith("use") or tok.startswith("on"):
            low = tok.lower()
            if len(low) >= 3 and low not in _STOPWORDS:
                names.add(low)
    return names


def _extract_statements(code: str) -> list[dict[str, Any]]:
    lines = _strip_comments(code).splitlines()
    statements: list[dict[str, Any]] = []
    buf: list[str] = []
    start_line = 0

    def flush() -> None:
        nonlocal buf, start_line
        text = " ".join(part.strip() for part in buf if part.strip())
        buf = []
        if not text or not _is_executable_statement(text):
            return
        statements.append({"line": start_line, "text": re.sub(r"\s+", " ", text)})

    for lineno, raw in enumerate(lines, start=1):
        line = raw.strip()
        if not line:
            continue
        if any(line.startswith(prefix) for prefix in _SKIP_LINE_PREFIXES):
            continue
        if not buf:
            start_line = lineno
        buf.append(line)
        if _STATEMENT_END_RE.search(line) or line.endswith("),") or line.endswith("});"):
            flush()
    if buf:
        flush()
    return statements


def _is_executable_statement(text: str) -> bool:
    stripped = text.strip()
    if len(stripped) < 6:
        return False
    if stripped in {"{", "}", "};", "})"}:
        return False
    if stripped.startswith(("/*", "*", "//")):
        return False
    if stripped.startswith(_STATEMENT_STARTS):
        return True
    if "=>" in stripped or "=" in stripped or "(" in stripped and ")" in stripped:
        return True
    token_counts = Counter(_tokens(stripped))
    return len(token_counts) >= 3
