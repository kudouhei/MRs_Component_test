# MR Annotation Codebook

This codebook defines the human validation protocol for UI component metamorphic-relation (MR) completeness reports.

## Unit of Annotation

Each row is a `(component, MR, test suite)` item exported by:

```bash
python3 backend/scripts/export_annotation_sample.py --limit 300
```

Annotators inspect the component description/source when needed, the MR description, expected relation, and the test evidence fields.

## Labels

### `human_valid_mr`

Whether the inferred MR is a valid expected behavioral relation for the component.

- `1`: The MR is relevant to the component and describes a plausible behavioral relation.
- `0`: The MR is irrelevant, contradicted by the component API, too vague to test, or outside component behavior.

### `human_touched`

Whether the test suite touches the behavior involved in the MR.

- `1`: Tests render, configure, trigger, or reference behavior related to the MR.
- `0`: Tests do not exercise or reference the behavior.

Touch does not require a strong oracle. For example, firing a keyboard event touches `keyboard_interaction` even if the test does not assert the resulting focus/selection relation.

### `human_covered`

Whether the test suite strictly covers the MR.

Strict coverage requires all four elements:

1. A baseline input/state/event/configuration.
2. A transformed input/state/event/configuration.
3. Observable output, trace, callback, DOM state, accessibility state, or visual/layout proxy before/after transformation.
4. An assertion checking the expected relation between baseline and transformed observations.

Use `1` only when the assertion verifies the relation, not merely that the component renders or that an event fires.

## Examples

### Touched But Not Covered

MR: `keyboard_interaction`

Test fires `ArrowDown`, but only asserts that no error is thrown.

- `human_touched = 1`
- `human_covered = 0`

### Strictly Covered

MR: `aria_mapping`

Test opens a combobox, moves active option with keyboard, and asserts `aria-expanded` and `aria-activedescendant` match the active option.

- `human_touched = 1`
- `human_covered = 1`

### Untouched

MR: `pagination_consistency`

Component supports pagination, but tests never change page or page size.

- `human_touched = 0`
- `human_covered = 0`

## Adjudication

Two annotators should independently label a stratified sample across libraries and component categories. Disagreements are resolved through discussion, and agreement is reported with Cohen's kappa for `human_touched` and `human_covered`.
