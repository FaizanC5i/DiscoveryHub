---
name: ui-design-system
description: Use whenever creating or changing any UI in this project (components, pages, styles, layouts, buttons, inputs, forms, cards, navigation, modals, tables, colors, typography, spacing, radius, dark mode). Builds the UI from the C5i design system tokens in frontend/docs/design-system.md instead of hard-coded values.
---

# C5i UI design system

Any UI work in this repo follows the C5i design system. The single source of truth is:

**`frontend/docs/design-system.md`** (`d:\DiscoveryHub\frontend\docs\design-system.md`)

Read that file before writing or changing UI code. Do not guess token names, colors, or sizes.

## Steps

1. **Read the design system doc** first, at least the sections that match the work:
   - Colors and themes: sections 2 (Semantic) and 4 (CSS custom properties)
   - Control states (buttons, inputs, dropdowns, toggles, sliders, badges, navigation, tables, etc.): section 3 (Component tokens)
   - Text: section 1.4 (Type scale) and section 5, rule 5
   - Spacing: section 1.5 (4px grid)
   - Corners: section 1.6 (Radius)
   - Rules for implementation: section 5
   - Known issues to be aware of: section 6

2. **Reference tokens by semantic name, never raw hex values.**
   - Use the CSS variables from section 4, for example `var(--color-text-default-primary)`, `var(--color-bg-default-primary)`, `var(--space-4)`, `var(--radius-md)`, `var(--font-size-body-medium)`.
   - Use **Semantic** tokens in UI code. Use **Primitives** (`--color-brand-500` etc.) only when defining new semantic tokens.
   - Use **Component** tokens (section 3) when building a control, so default, hover, selected, and disabled states match the design.

3. **Follow the rules in section 5 of the doc:**
   - Spacing (padding, margin, gap) only on the 4px grid.
   - Every font size is paired with its line height from the type scale.
   - Headings and primary text use Degular; secondary text uses Segoe UI with the system fallback stack.
   - Corners use Radius tokens only. For pills, a large value such as `9999px` is allowed, and call it out as outside the system.
   - Dark theme uses the dark values from the doc. Do not invert colors automatically.

4. **If a value you need is not in the doc**, do not invent one. Pick the nearest existing token, and tell the user which token you used and why. If the design truly needs a new token, say so and suggest it for the design team rather than adding a hex value inline.

5. **Dark mode**: follow the doc's approach (`:root[data-theme="dark"]` and the `prefers-color-scheme` block). Check that new UI looks correct in both themes.

6. **Known issues** (section 6) affect real code. Notably:
   - `Color/Base/Transparent` has no defined value. Use the CSS keyword `transparent` and mention it.
   - Use the correct spelling `Disabled`, not the typo `Diasabled` from the source file.
   - Segoe UI is not available on macOS, Linux, or most web browsers. Always keep the fallback stack (`"Segoe UI", system-ui, sans-serif`).

## When this skill applies

Use it for any of these, even when the user does not say "design system":
- Creating or editing components, pages, layouts, or styles in `frontend/`
- Choosing colors, fonts, font sizes, spacing, border radius, shadows, or themes
- Building buttons, inputs, dropdowns, checkboxes, radios, toggles, sliders, badges, cards, modals, tooltips, tables, toasts, tabs, breadcrumbs, or other controls

It does not apply to backend-only work with no UI output.

## Output expectations

- Styles use CSS variables or Tailwind classes that resolve to these tokens. No new hard-coded hex, rgb, or arbitrary pixel values for colors, text, spacing, or radius.
- When you finish UI work, briefly state which tokens and component mappings you used, and flag any gap you had to work around.
