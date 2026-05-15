# Workshop Mode WCAG 2.2 AA Checklist

## Purpose
This checklist defines implementation and QA requirements for GLOW Workshop Mode pages, forms, galleries, and facilitator tools.

## Semantic Structure
- One H1 per page.
- Ordered heading hierarchy (H2 after H1, H3 under H2).
- Landmark usage: header, nav, main, footer.
- Skip link to main content appears first and is keyboard focusable.

## Keyboard Access
- All controls operable via keyboard.
- No positive tabindex values.
- Visible focus indicator present and high contrast.
- No keyboard trap in overlays or dialogs.
- Focus returns to trigger after dialog close.

## Forms and Errors
- Every input has a persistent label.
- Required fields are programmatically exposed.
- Error messaging is linked to fields.
- Submit errors provide clear remediation guidance.
- Entered values are preserved after validation failures.

## Tables
- Tables are only used for tabular data.
- Every table has a caption.
- Header cells use proper scope values.
- Reading order remains logical for screen readers.

## Links and Controls
- Link text is descriptive out of context.
- Icon-only controls include accessible names.
- New-tab behavior is announced in link text where applicable.
- Status is never conveyed by color only.

## Visual and Contrast
- Text contrast minimum 4.5:1.
- Large text and UI boundaries minimum 3:1.
- Focus ring contrast minimum 3:1.
- Reflow support at 320px-equivalent width.
- Zoom support to 200 percent without loss of function.

## Dynamic Updates
- Live region used only when content updates asynchronously.
- Polite announcements for non-critical changes.
- No repeated or noisy announcements.
- Focus is not stolen during background updates.

## Cognitive and Readability
- Plain language instructions.
- Task steps are short and explicit.
- Avoid ambiguous jargon where possible.
- Keep action labels consistent across workflow steps.

## Verification Gates
Automated gate:
- axe-core scan with WCAG 2.2 AA tags must have zero critical and serious issues.

Manual gate:
- Keyboard-only walkthrough
- Screen reader smoke test
- Contrast spot checks
- Form error and recovery path validation

## Workshop-Specific Human Review Safeguard
Every AI-assisted workflow output must include:
- what AI drafted,
- what human must verify,
- final reviewer owner,
- final acceptance note.
