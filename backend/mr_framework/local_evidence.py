"""Auditable local test↔MR alignment.

This module is intentionally conservative: local evidence can identify likely
touches and strict coverage, but strict coverage requires assertions in the
same test block as relation-specific behavioral cues.
"""

from __future__ import annotations

import re
from typing import Any, List, Sequence

_COVER_MARKERS = ("expect(", "assert", ".should(", "should(")
_STOPWORDS = {
    "and",
    "are",
    "can",
    "for",
    "from",
    "has",
    "have",
    "same",
    "should",
    "state",
    "stay",
    "the",
    "true",
    "with",
    "yield",
    "yields",
}
_TEST_BLOCK_RE = re.compile(
    r"\b(?:it|test)\s*\(\s*([`'\"])(?P<title>.*?)(?<!\\)\1\s*,(?P<body>.*?)(?=\n\s*\}\s*\)|\n\s*\)\s*;|\n\s*\)\s*$)",
    re.DOTALL,
)
_RELATION_KEYWORDS: dict[str, tuple[str, ...]] = {
    "aria_mapping": ("aria-", "role", "accessibility", "a11y", "tohaveattribute"),
    "async_data_consistency": ("async", "await", "promise", "waitfor", "loading"),
    "boundary_preservation": ("min", "max", "boundary", "limit", "clamp"),
    "breakpoint_consistency": ("breakpoint", "responsive", "viewport", "media"),
    "data_formatting": ("format", "formatter", "parse", "locale"),
    "data_validation": ("valid", "invalid", "error", "required", "rule"),
    "enum_consistency": ("variant", "size", "color", "type", "status"),
    "event_idempotence": ("twice", "again", "rerender", "repeat", "idempot"),
    "event_order": ("before", "after", "order", "sequence"),
    "event_propagation": ("stoppropagation", "preventdefault", "bubble"),
    "filtering_consistency": ("filter", "search", "query"),
    "focus_management": ("focus", "blur", "tab", "activeelement"),
    "interaction_feedback": ("click", "hover", "press", "mouse", "keyboard", "disabled"),
    "keyboard_interaction": ("keydown", "keyboard", "tab", "arrow", "enter", "escape", "space"),
    "loading_consistency": ("loading", "spinner", "skeleton", "pending"),
    "monotonicity": ("increase", "decrease", "greater", "less", "next"),
    "null_handling": ("null", "undefined", "empty", "none", "without"),
    "operation_reversibility": ("open", "close", "toggle", "undo", "restore"),
    "overflow_handling": ("overflow", "scroll", "truncate", "ellipsis"),
    "pagination_consistency": ("page", "pagination", "next", "prev", "total"),
    "parent_child_state_sync": ("parent", "child", "controlled", "value"),
    "prop_dependency": ("disabled", "readonly", "required", "controlled", "default"),
    "prop_passing": ("prop", "class", "style", "slot", "ref"),
    "responsive_sizing": ("width", "height", "size", "resize", "viewport"),
    "sorting_determinism": ("sort", "order", "asc", "desc"),
    "state_synchronization": ("state", "controlled", "uncontrolled", "value", "checked"),
    "state_visual_mapping": ("selected", "active", "checked", "expanded", "visible"),
    "step_consistency": ("step", "increment", "decrement"),
    "theme_consistency": ("theme", "token", "css", "class", "style"),
    "two_way_binding": ("value", "onchange", "change", "input", "controlled"),
    "type_equivalence": ("string", "number", "boolean", "object", "array"),
}
_TRANSFORMATION_CUES = (
    "rerender",
    "setprops",
    "fireevent",
    "userevent",
    "user.",
    "click",
    "type",
    "keyboard",
    "hover",
    "focus",
    "blur",
    "change",
    "toggle",
    "open",
    "close",
    "next",
    "prev",
)


def _has_assert(tl: str) -> bool:
    return any(m in tl for m in _COVER_MARKERS) or bool(re.search(r"\bexpect\s*\(", tl))


def _tokens(text: str) -> set[str]:
    return {
        t.lower()
        for t in re.findall(r"[a-zA-Z_][a-zA-Z0-9_]{2,}", text or "")
        if t.lower() not in _STOPWORDS
    }


def _split_test_blocks(tests: str) -> list[dict[str, str]]:
    blocks = []
    for m in _TEST_BLOCK_RE.finditer(tests or ""):
        title = m.group("title").strip()
        body = m.group("body")
        blocks.append({"title": title, "body": body, "text": f"{title}\n{body}"})
    if not blocks and (tests or "").strip():
        blocks.append({"title": "<whole-test-file>", "body": tests, "text": tests})
    return blocks


def _relation_terms(row: dict[str, Any], mr: Any) -> set[str]:
    rt = str(row.get("relation_type") or getattr(mr, "relation_type", "") or "")
    desc = str(row.get("mr_description") or getattr(mr, "description", "") or "")
    expected = str(row.get("expected_relation") or getattr(mr, "expected_relation", "") or "")
    terms = _tokens(f"{rt} {desc} {expected}")
    for seg in rt.split("_"):
        if len(seg) >= 3:
            terms.add(seg.lower())
    terms.update(_RELATION_KEYWORDS.get(rt, ()))
    return {t for t in terms if len(t) >= 3}


def _strong_terms(row: dict[str, Any]) -> set[str]:
    rt = str(row.get("relation_type") or "")
    terms = set(_RELATION_KEYWORDS.get(rt, ()))
    terms.update(seg for seg in rt.split("_") if len(seg) >= 4)
    return {t.lower() for t in terms if t.lower() not in _STOPWORDS}


def apply_local_evidence_mr_coverage(
    *,
    mrs: Sequence[Any],
    mr_coverage: List[dict[str, Any]],
    tests: str | None,
    code_alignment_fallback: str | None = None,
) -> None:
    if not mr_coverage:
        return
    tests_only = (tests or "").strip()
    text = tests_only or (code_alignment_fallback or "").strip()
    if not text:
        return
    tl_assert = tests_only.lower()
    test_tokens = _tokens(text)
    test_blocks = _split_test_blocks(tests_only)

    mr_map = {}
    for m in mrs:
        mid = getattr(m, "id", None) or (m.get("id") if isinstance(m, dict) else None)
        if mid:
            mr_map[mid] = m

    best_row, best_score, best_hits = None, -1.0, []
    for row in mr_coverage:
        mid = row.get("mr_id")
        mr = mr_map.get(mid)
        mr_tokens = _relation_terms(row, mr)
        inter = sorted(mr_tokens & test_tokens)
        score = len(inter) / max(len(mr_tokens), 1) if mr_tokens else 0.0
        strong_terms = _strong_terms(row)
        if inter and score > best_score:
            best_score, best_hits, best_row = score, inter, row
        keyword_hit = bool(strong_terms & test_tokens)
        if inter and (score >= 0.18 or keyword_hit):
            row["evidence_touch"] = True
            row["evidence_touch_score"] = round(score, 4)
            row["evidence_touch_hits"] = inter[:8]
            strict_blocks = []
            for block in test_blocks:
                block_l = block["text"].lower()
                block_hits = [h for h in inter if h in block_l]
                strong_block_hits = [h for h in block_hits if h in strong_terms]
                has_transform = any(cue in block_l for cue in _TRANSFORMATION_CUES)
                if strong_block_hits and has_transform and _has_assert(block_l):
                    strict_blocks.append(
                        {
                            "title": block["title"][:180],
                            "hits": strong_block_hits[:6],
                            "has_assertion": True,
                            "has_transformation": True,
                        }
                    )
            row["evidence_covered"] = bool(strict_blocks)
            if strict_blocks:
                row["evidence_strict_blocks"] = strict_blocks[:5]
                row["reason"] = (
                    row.get("reason")
                    or f"local strict evidence in test block(s): "
                    f"{', '.join(b['title'] for b in strict_blocks[:3])}"
                )
            elif row["evidence_touch"]:
                row["reason"] = row.get("reason") or "local evidence touched behavior but found no same-block assertion plus transformation cue"
            methods = list(row.get("alignment_method") or [])
            if "local_evidence" not in methods:
                methods.append("local_evidence")
            row["alignment_method"] = methods

    if tests_only and not any(r.get("evidence_touch") for r in mr_coverage if isinstance(r, dict)):
        if best_row is not None:
            best_row["evidence_touch"] = True
            best_row["evidence_touch_score"] = round(max(0.12, best_score), 4)
            best_row["evidence_touch_hits"] = best_hits[:8] or ["tests_nonempty"]
            methods = list(best_row.get("alignment_method") or [])
            if "local_evidence" not in methods:
                methods.append("local_evidence")
            best_row["alignment_method"] = methods

    for row in mr_coverage:
        row.setdefault("evidence_touch", False)
        row.setdefault("evidence_covered", False)
