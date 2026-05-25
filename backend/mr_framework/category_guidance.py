"""Category-specific MR inference focus (Phase 1 context for LLM)."""

from __future__ import annotations

CATEGORY_MR_FOCUS: dict[str, str] = {
    "Inputs": (
        "Prioritize: controlled/uncontrolled value, validation, disabled/readOnly, "
        "keyboard interaction, focus, null/empty options, async options loading, "
        "formatting, two-way binding, prop dependencies between input props."
    ),
    "Navigation": (
        "Prioritize: selection state, expanded/collapsed, routing/link behavior, "
        "keyboard navigation (arrows/tab), active item, disabled items, "
        "hierarchical menus, pagination of nav items, URL/hash sync if applicable."
    ),
    "Feedback": (
        "Prioritize: open/close lifecycle, placement/portal, focus trap, escape dismiss, "
        "timing (auto-close), loading states, severity variants, aria-live regions, "
        "interaction with trigger elements."
    ),
    "Data display": (
        "Prioritize: empty/null data, sorting/filtering/pagination consistency, "
        "selection models, responsive layout, overflow, virtualization if implied, "
        "stable keys, rendering consistency when data reference changes."
    ),
    "Layout": (
        "Prioritize: responsive breakpoints, spacing alignment, scroll behavior, "
        "collapse/expand, child composition, theme/size tokens, overflow clipping."
    ),
}

DEFAULT_CATEGORY_FOCUS = (
    "Consider general UI metamorphic relations across props, state, events, "
    "accessibility, composition, and data flow."
)


def category_focus_text(category: str) -> str:
    return CATEGORY_MR_FOCUS.get(category.strip(), DEFAULT_CATEGORY_FOCUS)
