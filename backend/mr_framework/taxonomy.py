"""MR type taxonomy — stable relation_type → type_category encoding framework.

The top-level categories follow a UI component behavior model:
props/inputs, state/events, interaction/accessibility, visual/layout,
composition/context, and data flow. This keeps the codebook explainable for
paper methodology while preserving stable snake_case relation types.
"""

from __future__ import annotations

TAXONOMY_VERSION = "2.0.0"

RELATION_TYPE_CATEGORIES: dict[str, dict[str, str]] = {
    "input_prop_relations": {
        "type_equivalence": "Same-type inputs yield consistent behavior",
        "null_handling": "Null/undefined/empty inputs are handled deterministically",
        "enum_consistency": "Enum/option sets behave consistently",
        "boundary_preservation": "Boundary values behave consistently",
        "monotonicity": "Monotonic input changes yield monotonic outputs",
        "step_consistency": "Step changes are uniform",
        "prop_dependency": "Dependent props stay consistent",
        "mutually_exclusive_props": "Mutually exclusive props cannot both apply",
        "conditional_props": "Conditional props apply only when conditions hold",
    },
    "state_event_relations": {
        "state_equivalence": "Equivalent states yield equivalent UI",
        "operation_reversibility": "Operations are reversible where expected",
        "state_synchronization": "Related state stays synchronized",
        "event_order": "Event order is deterministic",
        "event_idempotence": "Repeated events yield the same result",
        "event_propagation": "Bubble/capture behavior is consistent",
        "race_condition_handling": "Concurrent updates resolve deterministically",
    },
    "interaction_accessibility_relations": {
        "interaction_feedback": "Interactions provide consistent feedback",
        "focus_management": "Focus behavior is consistent",
        "aria_mapping": "ARIA reflects true state",
        "keyboard_interaction": "Keyboard interaction is deterministic",
        "disabled_interaction": "Disabled/readOnly states suppress or alter interaction consistently",
        "screen_reader_state": "Assistive-technology observable state matches component state",
    },
    "visual_layout_relations": {
        "responsive_sizing": "Size changes scale responsively",
        "breakpoint_consistency": "Behavior is consistent across breakpoints",
        "overflow_handling": "Overflow is handled uniformly",
        "state_visual_mapping": "States map to consistent visuals",
        "animation_consistency": "Animations are consistent for same actions",
        "placement_consistency": "Overlay or positioned content keeps consistent placement under equivalent anchors",
        "theme_consistency": "Theme tokens apply consistently",
        "visual_alignment": "Related parts align visually",
    },
    "composition_context_relations": {
        "prop_passing": "Props pass correctly to children",
        "child_event_bubbling": "Child events bubble correctly",
        "parent_child_state_sync": "Parent/child state stays in sync",
        "mutually_exclusive_selection": "Exclusive selection behaves predictably",
        "slot_composition": "Slots and render props preserve expected component behavior",
        "context_propagation": "Context/provider changes propagate consistently",
        "i18n_consistency": "i18n handling is consistent",
        "environment_adaptation": "Environment changes are handled sensibly",
    },
    "data_flow_relations": {
        "two_way_binding": "UI and data stay synchronized",
        "data_validation": "Validation rules apply consistently",
        "data_formatting": "Formatting is consistent",
        "filtering_consistency": "Filters yield consistent results",
        "sorting_determinism": "Sorting order is deterministic",
        "pagination_consistency": "Pagination behaves consistently",
        "loading_consistency": "Loading states are consistent",
        "async_data_consistency": "Async updates keep data self-consistent",
        "batched_updates": "Batched updates are handled consistently",
    },
}

RELATION_TYPE_TO_CATEGORY: dict[str, str] = {}
for _cat, _types in RELATION_TYPE_CATEGORIES.items():
    for _rt in _types:
        RELATION_TYPE_TO_CATEGORY[_rt] = _cat

TYPE_CATEGORY_ALIASES: dict[str, str] = {
    "input_property_relations": "input_prop_relations",
    "state_behavior_relations": "state_event_relations",
    "visual_representation_relations": "visual_layout_relations",
    "composition_relations": "composition_context_relations",
}


def normalize_type_category(type_category: str | None, relation_type: str | None = None) -> str:
    """Return the canonical v2 top-level category for a relation."""
    if relation_type and relation_type in RELATION_TYPE_TO_CATEGORY:
        return RELATION_TYPE_TO_CATEGORY[relation_type]
    key = (type_category or "").strip()
    return TYPE_CATEGORY_ALIASES.get(key, key if key in RELATION_TYPE_CATEGORIES else "input_prop_relations")
