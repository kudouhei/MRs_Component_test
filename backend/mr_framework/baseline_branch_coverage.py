"""Branch coverage baseline (static proxy).

Like the statement-coverage proxy, this module does NOT require a runnable
test harness.  It extracts logical branch points from source (if/else,
switch/case, ternary, short-circuit &&/||) and measures how many of those
branch conditions share identifying tokens with the test file.

Limitations (documented for paper):
  - Static only: no control-flow graph, no runtime instrumentation.
  - Branch "coverage" here means the branch *condition* was referenced in
    tests, not that both outcomes were exercised.
  - Short-circuit operators counted only when they appear in conditional
    position (guarding a statement), not inside expressions.
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Any

# ── tokenisation (shared with baseline_coverage) ────────────────────────────

_COMMENT_RE = re.compile(r"/\*.*?\*/|//.*?$", re.DOTALL | re.MULTILINE)
_STRING_RE = re.compile(r"(['\"`])(?:\\.|(?!\1).)*\1", re.DOTALL)
_TOKEN_RE = re.compile(r"[A-Za-z_$][A-Za-z0-9_$]*")
_STOPWORDS = {
    "and", "args", "array", "async", "await", "boolean", "case", "catch",
    "class", "const", "default", "else", "false", "for", "from", "function",
    "if", "import", "let", "new", "null", "object", "props", "react",
    "return", "string", "switch", "this", "throw", "true", "try",
    "undefined", "var", "while",
}


def _strip_comments(text: str) -> str:
    return _COMMENT_RE.sub("", text or "")


def _tokens(text: str) -> set[str]:
    clean = _STRING_RE.sub(" ", text or "")
    return {
        t.lower()
        for t in _TOKEN_RE.findall(clean)
        if len(t) >= 3 and t.lower() not in _STOPWORDS
    }


# ── branch extraction ────────────────────────────────────────────────────────

# Patterns that mark a branch point and capture the condition text.
_IF_RE = re.compile(r"\bif\s*\((.{1,200}?)\)\s*[{;]?", re.DOTALL)
_ELSE_IF_RE = re.compile(r"\belse\s+if\s*\((.{1,200}?)\)\s*[{;]?", re.DOTALL)
_TERNARY_RE = re.compile(r"([A-Za-z_$][A-Za-z0-9_$.]*\s*(?:===?|!==?|>=?|<=?)\s*[^\n?:]{1,80})\?", re.DOTALL)
_SWITCH_RE = re.compile(r"\bswitch\s*\((.{1,200}?)\)\s*\{", re.DOTALL)
_CASE_RE = re.compile(r"\bcase\s+([^\n:]{1,80}):", re.DOTALL)
_SHORT_CIRCUIT_RE = re.compile(r"\)\s*(&&|\|\|)\s*[({A-Za-z_$]")

# Attribute/prop patterns typical in JSX components (e.g. disabled={condition})
_JSX_ATTR_RE = re.compile(r'\b(disabled|readOnly|required|checked|open|visible|loading|error)\s*=\s*\{([^}]{1,120})\}')


def _extract_branches(code: str) -> list[dict[str, Any]]:
    """Return a list of branch descriptors from source code."""
    clean = _strip_comments(code)
    branches: list[dict[str, Any]] = []

    def add(kind: str, condition: str, line: int) -> None:
        condition = re.sub(r"\s+", " ", condition).strip()
        if len(condition) < 2:
            return
        branches.append({"kind": kind, "condition": condition, "line": line})

    def line_of(m: re.Match) -> int:  # type: ignore[type-arg]
        return clean[: m.start()].count("\n") + 1

    for m in _IF_RE.finditer(clean):
        if not _ELSE_IF_RE.match(clean[m.start():]):
            add("if", m.group(1), line_of(m))

    for m in _ELSE_IF_RE.finditer(clean):
        add("else_if", m.group(1), line_of(m))

    for m in _TERNARY_RE.finditer(clean):
        add("ternary", m.group(1), line_of(m))

    for m in _SWITCH_RE.finditer(clean):
        add("switch", m.group(1), line_of(m))

    for m in _CASE_RE.finditer(clean):
        add("case", m.group(1), line_of(m))

    for m in _JSX_ATTR_RE.finditer(clean):
        add("jsx_prop", f"{m.group(1)}={m.group(2)}", line_of(m))

    return branches


# ── coverage decision ────────────────────────────────────────────────────────

def _is_branch_covered(condition: str, test_tokens: set[str]) -> tuple[bool, list[str]]:
    """A branch is covered if ≥2 identifying tokens appear in the test file,
    or a single strong token (prop name, component identifier) appears."""
    cond_tokens = _tokens(condition)
    strong = {
        t for t in cond_tokens
        if len(t) >= 5  # longer tokens are more identifying
    }
    hits = sorted(cond_tokens & test_tokens)
    strong_hits = sorted(strong & test_tokens)
    covered = len(strong_hits) >= 1 or len(hits) >= 2
    return covered, hits[:8]


# ── public API ───────────────────────────────────────────────────────────────

def compute_branch_coverage_baseline(code: str, tests: str) -> dict[str, Any]:
    """Compute a static branch-coverage proxy for a source/test pair."""
    branches = _extract_branches(code)
    test_tok = _tokens(tests)

    covered_items: list[dict[str, Any]] = []
    uncovered_items: list[dict[str, Any]] = []

    kind_counts: Counter[str] = Counter()
    kind_covered: Counter[str] = Counter()

    for b in branches:
        is_cov, hits = _is_branch_covered(b["condition"], test_tok)
        kind_counts[b["kind"]] += 1
        item = {
            "kind": b["kind"],
            "condition": b["condition"][:120],
            "line": b["line"],
            "hits": hits,
        }
        if is_cov:
            kind_covered[b["kind"]] += 1
            covered_items.append(item)
        else:
            uncovered_items.append(item)

    total = len(branches)
    covered_n = len(covered_items)

    return {
        "kind": "branch_coverage_static_proxy",
        "method": (
            "Static token-overlap proxy over extracted branch conditions "
            "(if/else-if/ternary/switch-case/jsx-prop); "
            "not runtime branch coverage."
        ),
        "total_branches": total,
        "covered_branches": covered_n,
        "uncovered_branches": total - covered_n,
        "branch_coverage_rate": round(covered_n / total, 6) if total else 0.0,
        "by_kind": {
            k: {
                "total": kind_counts[k],
                "covered": kind_covered[k],
                "rate": round(kind_covered[k] / kind_counts[k], 6) if kind_counts[k] else 0.0,
            }
            for k in sorted(kind_counts)
        },
        "covered_branch_examples": covered_items[:6],
        "uncovered_branch_examples": uncovered_items[:6],
    }
