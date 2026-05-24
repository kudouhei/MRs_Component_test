"""Model-agnostic test↔MR alignment (Phase 2 evidence_* / hybrid_*)."""

from __future__ import annotations

import re
from typing import Any, List, Sequence

__all__ = ["apply_local_evidence_mr_coverage"]

_COVER_ASSERTION_MARKERS_LOWER: tuple[str, ...] = (
    "expect(",
    "assert",
    ".should(",
    "should(",
    "cy.should(",
)


def _tests_lower_has_assert_reference(tests_lower: str) -> bool:
    tl = tests_lower or ""
    if not tl.strip():
        return False
    if "expect(" in tl or ".expect(" in tl:
        return True
    if re.search(r"\bexpect\s*\(", tl):
        return True
    if re.search(r"\bassert\w*\s*\(", tl):
        return True
    if re.search(r"\bassert\s+", tl):
        return True
    if ".should(" in tl or "cy.should(" in tl:
        return True
    if re.search(r"\bshould\s*\(", tl):
        return True
    if re.search(r"\bcy\s*\.\s*should\s*\(", tl):
        return True
    return False


def apply_local_evidence_mr_coverage(
    *,
    mrs: Sequence[Any],
    mr_coverage: List[dict[str, Any]],
    tests: str | None,
    scenario: str | None,
    code_alignment_fallback: str | None = None,
) -> None:
    if not mr_coverage:
        return
    tests_only = str(tests or "").strip()
    code_fb = str(code_alignment_fallback or "").strip()
    if not tests_only and not code_fb:
        return
    tests_text = tests_only or code_fb
    tl = tests_text.lower()
    tl_assert = tests_only.lower()

    def _rel(obj: Any, name: str) -> Any:
        if isinstance(obj, dict):
            return obj.get(name)
        return getattr(obj, name, None)

    def _tokens(text: str) -> set[str]:
        toks = set(re.findall(r"[a-zA-Z_][a-zA-Z0-9_]{2,}", text or ""))
        return {t.lower() for t in toks if t}

    def _extract_test_features(*, unit_text: str, unit_label: str) -> dict[str, set[str]]:
        t = unit_text or ""
        tlc = t.lower()
        lbl_l = (unit_label or "").lower()
        title_words: set[str] = set()
        try:
            m = re.search(r"\b(?:it|test)\(\s*(['\"])([^'\"]{1,220})\1", t)
            if m:
                title_words |= _tokens(m.group(2))
            for dm in re.finditer(r"\bdescribe\(\s*(['\"])([^'\"]{1,220})\1", t):
                title_words |= _tokens(dm.group(2))
        except Exception:
            pass
        props = set(m.group(1) for m in re.finditer(r"\bprops\.([A-Za-z0-9_]+)\b", t))
        events = set(m.group(0) for m in re.finditer(r"\bon[A-Z][A-Za-z0-9_]*\b", t))
        interactions = {
            k for k in ("click", "focus", "blur", "keydown", "keyup", "tab", "enter") if k in tlc
        }
        aria = set(m.group(0).lower() for m in re.finditer(r"aria-[a-z0-9_-]+", tlc))
        if "role" in tlc:
            aria.add("role")
        assertions = {k for k in ("expect(", "assert", "should") if k in tlc}
        if _tests_lower_has_assert_reference(tlc):
            assertions.add("assert_ref")
        activity = {k for k in ("render(", "fireevent", "screen.") if k in tlc}
        if "describeconformance" in tlc or "createrenderer" in tlc:
            activity.add("conformance")
        return {
            "props": {p.lower() for p in props if 3 <= len(p) <= 40},
            "events": {e.lower() for e in events},
            "interactions": interactions,
            "aria": aria,
            "assertions": assertions,
            "meta": {w.lower() for w in title_words | _tokens(lbl_l)},
            "activity": activity,
        }

    def _kw_for_relation_type(rt: str | None) -> list[str]:
        if not rt:
            return []
        r = str(rt).lower().strip()
        kws = [r]
        kws.extend(
            {
                "null_handling": ["null", "undefined", "empty"],
                "keyboard_interaction": ["keydown", "key", "tab", "enter"],
                "focus_management": ["focus", "blur"],
                "aria_mapping": ["aria", "role"],
                "state_synchronization": ["controlled", "value", "onchange"],
                "pagination_consistency": ["page", "pagination"],
            }.get(r, [])
        )
        return kws

    def _collect_mr_keywords(mr: Any) -> list[str]:
        kws: list[str] = []
        kws.extend(_kw_for_relation_type(_rel(mr, "relation_type")))
        for field in ("description", "expected_relation"):
            for w in str(_rel(mr, field) or "")[:220].lower().split():
                w = w.strip(".,;:()[]{}\"'`")
                if len(w) >= 4 and w.isascii() and w not in kws:
                    kws.append(w)
                if len(kws) >= 32:
                    return kws
        return kws

    def _expand_mr_tokens_for_row(mr_obj: Any, row: dict[str, Any]) -> set[str]:
        feat = _tokens(" ".join(_collect_mr_keywords(mr_obj)))
        rt = row.get("relation_type")
        if rt:
            rs = str(rt).lower()
            feat |= _tokens(rs)
            for seg in re.split(r"[_\-\s]+", rs):
                if len(seg) >= 3:
                    feat.add(seg)
        return {t for t in feat if 3 <= len(t) <= 40}

    def _split_test_units(text: str) -> list[dict[str, str]]:
        lines = (text or "").splitlines()
        anchors: list[int] = []
        for idx, ln in enumerate(lines):
            st = ln.strip()
            if st.startswith(("it(", "test(", "describe(")):
                anchors.append(idx)
            elif re.match(r"^(?:async\s+)?def\s+test_[A-Za-z0-9_]+\s*\(", st):
                anchors.append(idx)
        if not anchors:
            return [{"label": "whole_file", "text": text or ""}]
        units = []
        for i, start in enumerate(anchors):
            end = anchors[i + 1] if i + 1 < len(anchors) else len(lines)
            chunk = "\n".join(lines[start:end]).strip()
            if chunk:
                units.append({"label": lines[start].strip()[:80], "text": chunk})
        return units

    file_activity = set(
        _extract_test_features(unit_text=tests_text, unit_label="__file__").get("activity") or set()
    )
    unit_features = []
    for u in _split_test_units(tests_text):
        feats = _extract_test_features(unit_text=u["text"], unit_label=u["label"])
        feats["activity"] = set(feats.get("activity") or set()) | file_activity
        tokens = set().union(
            feats.get("props", set()),
            feats.get("events", set()),
            feats.get("interactions", set()),
            feats.get("aria", set()),
            feats.get("assertions", set()),
            feats.get("meta", set()),
        )
        unit_features.append({"label": u["label"], "text": u["text"], "features": feats, "tokens": tokens})

    def _soft_sim(mr_tokens: set[str], test_tokens: set[str]) -> tuple[float, list[str]]:
        if not mr_tokens:
            return 0.0, []
        inter = sorted(mr_tokens.intersection(test_tokens))
        return len(inter) / float(len(mr_tokens)), inter[:5]

    has_test_activity = bool(tests_only.strip()) and (
        re.search(r"\b(describe|it|test|render)\s*\(", tests_text)
        or _tests_lower_has_assert_reference(tl)
        or "screen." in tl
    )
    mr_by_id = {_rel(m, "id"): m for m in (mrs or []) if _rel(m, "id")}

    def _best_alignment(row: dict[str, Any]) -> tuple[float, list[str], str, bool]:
        mr = mr_by_id.get(row.get("mr_id"))
        mr_tokens = _expand_mr_tokens_for_row(mr, row)
        best_sc, best_hs, best_lab, best_act = 0.0, [], "", False
        for u in unit_features:
            sc, hs = _soft_sim(mr_tokens, u["tokens"])
            if sc > best_sc:
                best_sc, best_hs, best_lab, best_act = sc, hs, u["label"], bool(
                    (u.get("features") or {}).get("activity")
                )
        if mr_tokens and best_sc <= 0:
            raw_hits = sorted({t for t in mr_tokens if t in tl})
            if raw_hits:
                best_sc = min(1.0, len(raw_hits) / max(len(mr_tokens), 1))
                best_hs = raw_hits[:8]
        return best_sc, best_hs, best_lab, best_act

    def _evidence_covered(hits: list[str]) -> bool:
        if not hits or not _tests_lower_has_assert_reference(tl_assert):
            return False
        for h in hits[:5]:
            if not h:
                continue
            for marker in _COVER_ASSERTION_MARKERS_LOWER:
                idx = 0
                while True:
                    pos = tl_assert.find(marker, idx)
                    if pos < 0:
                        break
                    if h in tl_assert[pos : pos + len(marker) + 220]:
                        return True
                    idx = pos + len(marker)
        return False

    def _apply_touch(row: dict[str, Any], score: float, hits: list[str], label: str) -> None:
        row["evidence_touch"] = True
        row["evidence_touch_score"] = round(score, 4)
        row["evidence_touch_hits"] = list(hits)
        row["evidence_touch_unit"] = label
        row["evidence_covered"] = _evidence_covered(hits)
        row["confidence"] = max(float(row.get("confidence") or 0), 0.61)
        s_code = max(0.0, min(1.0, score))
        row["hybrid_score"] = round(0.6 * s_code + 0.4 * (1.0 if row["evidence_covered"] else 0.0), 4)
        row["hybrid_touched"] = bool(row["evidence_covered"]) or s_code >= 0.5
        row["touched"] = bool(row.get("evidence_touch") or row.get("hybrid_touched") or row.get("covered"))

    for it in mr_coverage:
        if not isinstance(it, dict) or it.get("evidence_touch"):
            continue
        score, hits, label, has_act = _best_alignment(it)
        if (score >= 0.25 and hits) or (has_act and hits and score >= 0.12):
            _apply_touch(it, score, hits, label)

    if has_test_activity:
        rows = [x for x in mr_coverage if isinstance(x, dict)]
        if rows and not any(x.get("evidence_touch") for x in rows):
            best_it, best_sc, best_hs, best_lab = None, -1.0, [], ""
            for it in rows:
                sc, hs, lab, _ = _best_alignment(it)
                if sc > best_sc:
                    best_it, best_sc, best_hs, best_lab = it, sc, hs, lab
            if best_it is not None:
                _apply_touch(best_it, max(0.12, best_sc), list(best_hs) or ["tests_nonempty"], best_lab or "floor")

    for it in mr_coverage:
        if isinstance(it, dict):
            it.setdefault("evidence_touch", False)
            it.setdefault("evidence_covered", False)
            it.setdefault("hybrid_touched", False)
            it["touched"] = bool(it.get("evidence_touch") or it.get("hybrid_touched") or it.get("covered"))
