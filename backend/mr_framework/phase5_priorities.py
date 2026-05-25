"""Phase 5: priorities and improvement suggestions."""

from __future__ import annotations

from typing import Any

from .models import SampleMeta
from .taxonomy import normalize_type_category

SUGGESTION_TEMPLATES: dict[str, dict[str, str]] = {
    "aria_mapping": {
        "transformation": "Change the component state through user interaction or prop updates.",
        "oracle": "Assert that ARIA attributes/roles reflect the changed observable state.",
        "test_sketch": "Render the component, trigger the state change, then assert role and aria-* attributes.",
    },
    "keyboard_interaction": {
        "transformation": "Apply equivalent mouse and keyboard interactions, or a sequence of keyboard events.",
        "oracle": "Assert that focus, selected/active item, callbacks, and visible state change consistently.",
        "test_sketch": "Use userEvent.keyboard for Arrow/Enter/Escape/Tab and assert the same behavioral relation as pointer interaction.",
    },
    "focus_management": {
        "transformation": "Move focus into, through, and out of the component.",
        "oracle": "Assert that activeElement, focus restoration, and focus trap/release behavior follow the expected relation.",
        "test_sketch": "Trigger open/focus/blur/close transitions and assert document.activeElement after each transition.",
    },
    "state_synchronization": {
        "transformation": "Switch between controlled/default state or update state through an event and a prop rerender.",
        "oracle": "Assert that DOM state, callback payloads, and externally controlled value remain synchronized.",
        "test_sketch": "Render with a value, trigger change, rerender with the new value, and assert UI/callback consistency.",
    },
    "two_way_binding": {
        "transformation": "Mutate the UI value and then rerender from the data value.",
        "oracle": "Assert that UI-to-data and data-to-UI transitions produce the same final observable value.",
        "test_sketch": "Type/select a value, assert callback data, rerender with that data, then assert displayed value.",
    },
    "null_handling": {
        "transformation": "Replace normal props/data with null, undefined, empty string, or empty collection.",
        "oracle": "Assert deterministic fallback rendering and absence of crashes or invalid callbacks.",
        "test_sketch": "Render with empty inputs, rerender with populated inputs, and assert stable fallback/transition behavior.",
    },
    "pagination_consistency": {
        "transformation": "Move between pages or change page size/total item count.",
        "oracle": "Assert that visible items, active page, disabled navigation controls, and callbacks stay consistent.",
        "test_sketch": "Click next/previous or change pageSize and assert item range plus pagination state.",
    },
    "data_validation": {
        "transformation": "Move from valid to invalid input and back to valid input.",
        "oracle": "Assert that error state, helper text, ARIA invalid state, and callbacks remain consistent.",
        "test_sketch": "Submit invalid input, assert validation feedback, then correct it and assert feedback clears.",
    },
    "data_formatting": {
        "transformation": "Provide equivalent raw/formatted values or switch locale/formatter props.",
        "oracle": "Assert that displayed text and emitted values preserve the intended formatting relation.",
        "test_sketch": "Render equivalent values under different format settings and assert display/callback consistency.",
    },
    "sorting_determinism": {
        "transformation": "Apply the same sort action repeatedly or sort equivalent data in different original orders.",
        "oracle": "Assert deterministic row/item order and stable tie handling.",
        "test_sketch": "Sort twice and assert item order, then rerender equivalent data and assert the same sorted order.",
    },
    "filtering_consistency": {
        "transformation": "Change filter/search input while holding the data set constant.",
        "oracle": "Assert that visible items equal the expected filtered subset and reset restores the original set.",
        "test_sketch": "Type a query, assert visible subset, clear query, and assert original items return.",
    },
    "prop_dependency": {
        "transformation": "Toggle dependent props such as disabled/readOnly/required/value/defaultValue.",
        "oracle": "Assert that the dependent behavior changes consistently and incompatible prop combinations are handled.",
        "test_sketch": "Rerender with dependent props changed and assert interaction/callback/visual state relation.",
    },
    "interaction_feedback": {
        "transformation": "Apply hover/press/click/disabled interactions across equivalent variants.",
        "oracle": "Assert visible feedback, callback firing/suppression, and state changes consistently.",
        "test_sketch": "Trigger interaction events and assert both visual feedback and callback behavior.",
    },
    "responsive_sizing": {
        "transformation": "Change container or viewport size.",
        "oracle": "Assert that layout, visible items, or measured dimensions follow the expected responsive relation.",
        "test_sketch": "Mock viewport/container size, rerender, and assert layout classes/styles or visible structure.",
    },
    "placement_consistency": {
        "transformation": "Change anchor position, placement prop, or viewport boundary conditions.",
        "oracle": "Assert overlay placement and collision handling remain consistent with the anchor relation.",
        "test_sketch": "Render anchored content, change placement/bounds, and assert computed placement or DOM position marker.",
    },
}

TYPE_CATEGORY_TEMPLATES: dict[str, dict[str, str]] = {
    "input_prop_relations": {
        "transformation": "Change one input/prop dimension while keeping unrelated props constant.",
        "oracle": "Assert that only the behavior governed by that prop changes and unrelated behavior is preserved.",
        "test_sketch": "Render baseline props, rerender transformed props, then assert the expected relation between outputs.",
    },
    "state_event_relations": {
        "transformation": "Apply a state transition or event sequence and compare against an equivalent sequence.",
        "oracle": "Assert deterministic state, callback trace, and rendered output after the transition.",
        "test_sketch": "Trigger the event sequence, capture callbacks/output, and compare with the equivalent transition.",
    },
    "interaction_accessibility_relations": {
        "transformation": "Exercise the same behavior through pointer, keyboard, focus, and accessibility-observable state.",
        "oracle": "Assert that visible state and accessibility state remain aligned.",
        "test_sketch": "Combine userEvent interaction with role/aria/focus assertions.",
    },
    "visual_layout_relations": {
        "transformation": "Change visual state, theme, placement, size, or viewport constraints.",
        "oracle": "Assert stable visual/layout relation using DOM structure, classes, styles, or measured layout proxies.",
        "test_sketch": "Rerender under the visual/layout transformation and assert the expected output relation.",
    },
    "composition_context_relations": {
        "transformation": "Change children, slots, provider/context, or parent-controlled state.",
        "oracle": "Assert that composed parts receive props/state/events consistently.",
        "test_sketch": "Render composed children/slots, trigger parent-child transitions, and assert synchronized behavior.",
    },
    "data_flow_relations": {
        "transformation": "Change data, derived view state, async loading, or data operation parameters.",
        "oracle": "Assert that rendered data, callbacks, and derived state remain mutually consistent.",
        "test_sketch": "Transform data or operation parameters and assert the relation between input data and visible output.",
    },
}


def build_test_priorities(
    meta: SampleMeta,
    mr_coverage: list[dict[str, Any]],
    *,
    issue_pressure: int = 0,
) -> list[dict[str, Any]]:
    items = []
    for r in mr_coverage:
        touched = bool(r.get("touched"))
        covered = bool(r.get("covered"))
        if covered:
            continue
        reason = "touched_not_covered" if touched else "miss_at_uncov"
        score = (0.7 if touched else 1.0) + min(issue_pressure, 20) * 0.03
        tmpl = _suggestion_template(r)
        type_category = normalize_type_category(r.get("type_category"), r.get("relation_type"))
        items.append(
            {
                "library": meta.library,
                "category": meta.category,
                "component_name": meta.component_name,
                "relation_type": r.get("relation_type"),
                "type_category": type_category,
                "reason": reason,
                "test_transformation": tmpl["transformation"],
                "expected_oracle": tmpl["oracle"],
                "priority_score": round(score, 4),
            }
        )
    items.sort(key=lambda x: -x["priority_score"])
    return items[:25]


def build_improvement_suggestions(
    meta: SampleMeta,
    mr_coverage: list[dict[str, Any]],
    completeness: dict[str, Any],
) -> list[dict[str, Any]]:
    suggestions = []
    cat_rates = _canonical_category_rates(completeness.get("by_type_category") or {})
    weak_cats = sorted(cat_rates.items(), key=lambda x: x[1].get("coverage_rate", 0))[:2]
    for cat, stats in weak_cats:
        suggestions.append(
            {
                "kind": "category_gap",
                "message": (
                    f"Category '{cat}' has low strict coverage "
                    f"({stats.get('coverage_rate', 0):.1%}) for {meta.component_name}; "
                    f"add tests targeting typical {meta.category} MRs (see taxonomy)."
                ),
            }
        )
    for r in mr_coverage:
        if r.get("covered"):
            continue
        tmpl = _suggestion_template(r)
        type_category = normalize_type_category(r.get("type_category"), r.get("relation_type"))
        suggestions.append(
            {
                "kind": "mr_gap",
                "relation_type": r.get("relation_type"),
                "type_category": type_category,
                "gap_type": "weak_oracle" if r.get("touched") else "untouched",
                "test_transformation": tmpl["transformation"],
                "expected_oracle": tmpl["oracle"],
                "test_sketch": tmpl["test_sketch"],
                "evidence": {
                    "touch_hits": r.get("evidence_touch_hits") or [],
                    "related_tests": r.get("related_tests") or [],
                    "reason": r.get("reason") or "no alignment evidence",
                },
                "message": (
                    f"Add test(s) for MR '{r.get('relation_type')}': "
                    f"{tmpl['transformation']} Oracle: {tmpl['oracle']}"
                ),
            }
        )
        if len(suggestions) >= 12:
            break
    return suggestions


def _suggestion_template(row: dict[str, Any]) -> dict[str, str]:
    rt = str(row.get("relation_type") or "")
    tc = normalize_type_category(row.get("type_category"), rt)
    return SUGGESTION_TEMPLATES.get(rt) or TYPE_CATEGORY_TEMPLATES.get(tc) or {
        "transformation": "Apply the MR transformation described by this relation.",
        "oracle": "Assert the expected relation between baseline and transformed observable outputs.",
        "test_sketch": "Create a baseline render, apply the transformation, and assert the expected relation.",
    }


def _canonical_category_rates(raw: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    buckets: dict[str, dict[str, float]] = {}
    for cat, stats in raw.items():
        canonical = normalize_type_category(cat)
        total = float(stats.get("total") or 0)
        covered = total * float(stats.get("coverage_rate") or 0)
        touched = total * float(stats.get("touch_rate") or 0)
        bucket = buckets.setdefault(canonical, {"total": 0.0, "covered": 0.0, "touched": 0.0})
        bucket["total"] += total
        bucket["covered"] += covered
        bucket["touched"] += touched
    return {
        cat: {
            "total": int(vals["total"]),
            "coverage_rate": vals["covered"] / vals["total"] if vals["total"] else 0.0,
            "touch_rate": vals["touched"] / vals["total"] if vals["total"] else 0.0,
        }
        for cat, vals in buckets.items()
    }


def insufficient_attention_evidence(
    completeness: dict[str, Any],
    blind: dict[str, Any],
    *,
    issue_pressure: int,
) -> dict[str, Any]:
    return {
        "touch_rate": completeness.get("touch_rate"),
        "coverage_rate": completeness.get("coverage_rate"),
        "miss_at_uncov": blind.get("miss_at_uncov"),
        "open_bug_pressure": issue_pressure,
        "summary": (
            "Tests show gaps in metamorphic relation space; "
            "strict coverage below full indicates insufficient behavioral-relation testing."
        ),
    }
