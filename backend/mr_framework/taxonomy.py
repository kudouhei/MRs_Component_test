"""MR type taxonomy (Phase 1) — stable relation_type → type_category mapping."""

from __future__ import annotations

TAXONOMY_VERSION = "1.0.0"

RELATION_TYPE_CATEGORIES: dict[str, dict[str, str]] = {
    "input_property_relations": {
        "type_equivalence": "Type equivalence — same-type inputs behave consistently",
        "null_handling": "Null/undefined inputs have deterministic behavior",
        "enum_consistency": "Enum options are mutually exclusive with stable behavior",
        "boundary_preservation": "Boundary values behave consistently",
        "monotonicity": "Monotonic input changes produce monotonic outputs",
        "step_consistency": "Step changes are uniform and predictable",
        "prop_dependency": "Dependent props stay consistent",
        "mutually_exclusive_props": "Mutually exclusive props cannot both apply",
        "conditional_props": "Conditional props apply only when conditions hold",
    },
    "state_behavior_relations": {
        "state_equivalence": "Equivalent states produce equivalent UI",
        "operation_reversibility": "Operations are reversible where expected",
        "state_synchronization": "Related state stays synchronized",
        "event_order": "Event order is deterministic",
        "event_idempotence": "Repeated events yield the same result",
        "event_propagation": "Bubble/capture behavior is consistent",
        "loading_consistency": "Loading states are visually consistent",
        "async_data_consistency": "Async updates keep data self-consistent",
        "race_condition_handling": "Concurrent updates resolve deterministically",
    },
    "visual_representation_relations": {
        "responsive_sizing": "Size changes scale responsively",
        "breakpoint_consistency": "Behavior is consistent across breakpoints",
        "overflow_handling": "Overflow is handled uniformly",
        "state_visual_mapping": "States map to consistent visuals",
        "interaction_feedback": "Interactions provide consistent feedback",
        "animation_consistency": "Animations are consistent for same actions",
        "focus_management": "Focus behavior is consistent",
        "aria_mapping": "ARIA reflects true state",
        "keyboard_interaction": "Keyboard interaction is deterministic",
    },
    "composition_relations": {
        "prop_passing": "Props pass correctly to children",
        "child_event_bubbling": "Child events bubble correctly",
        "parent_child_state_sync": "Parent/child state stays in sync",
        "mutually_exclusive_selection": "Exclusive selection behaves predictably",
        "cooperative_components": "Cooperating parts stay consistent",
        "visual_alignment": "Related parts align visually",
        "theme_consistency": "Theme tokens apply consistently",
        "i18n_consistency": "i18n handling is consistent",
        "environment_adaptation": "Behavior adapts sensibly to environment",
    },
    "data_flow_relations": {
        "two_way_binding": "UI and data stay synchronized",
        "data_validation": "Validation rules apply consistently",
        "data_formatting": "Formatting is consistent",
        "filtering_consistency": "Filters yield consistent results",
        "sorting_determinism": "Sorting order is deterministic",
        "pagination_consistency": "Pagination behaves consistently",
        "render_optimization": "Identical data does not over-render",
        "memory_management": "Resources are released/reused correctly",
        "batched_updates": "Batched updates are handled efficiently",
    },
}

RELATION_TYPE_TO_CATEGORY: dict[str, str] = {}
for _cat, _types in RELATION_TYPE_CATEGORIES.items():
    for _rt in _types:
        RELATION_TYPE_TO_CATEGORY[_rt] = _cat

ALL_RELATION_TYPES: list[str] = list(RELATION_TYPE_TO_CATEGORY.keys())

CODE_PATTERN_HINTS: list[tuple[tuple[str, ...], list[str]]] = [
    (("disabled", "readonly"), ["prop_dependency", "interaction_feedback"]),
    (("aria-", "role", "labelledby"), ["aria_mapping", "keyboard_interaction"]),
    (("focus", "blur", "tabindex"), ["focus_management", "keyboard_interaction"]),
    (("keydown", "keyup", "onkey"), ["keyboard_interaction", "event_order"]),
    (("onchange", "oninput", "value", "defaultvalue"), ["two_way_binding", "state_synchronization"]),
    (("loading", "pending", "spinning"), ["loading_consistency", "async_data_consistency"]),
    (("pagination", "page", "pagesize"), ["pagination_consistency", "data_validation"]),
    (("filter", "search", "options"), ["filtering_consistency", "enum_consistency"]),
    (("null", "undefined", "empty"), ["null_handling", "boundary_preservation"]),
    (("min", "max", "step", "range"), ["boundary_preservation", "monotonicity", "step_consistency"]),
    (("children", "slot", "renderprops"), ["prop_passing", "child_event_bubbling"]),
    (("theme", "sx", "classnames", "classname"), ["theme_consistency", "state_visual_mapping"]),
    (("open", "expanded", "collapsed"), ["state_equivalence", "state_visual_mapping"]),
    (("error", "invalid", "validate"), ["data_validation", "null_handling"]),
]
