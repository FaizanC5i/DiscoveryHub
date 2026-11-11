---
name: ui-design-system
description: Use whenever creating or changing any UI in this project (components, pages, styles, layouts, buttons, inputs, forms, cards, navigation, modals, tables, colors, typography, spacing, radius, dark mode). Builds the UI from the C5i design system tokens in frontend/docs/design-system.md and follows a highly modular, reusable, clean, and industry-standard component architecture.
---

# C5i UI Design System & Frontend Architecture

Any UI work in this repository must follow both:

1. The **C5i Design System**
2. A **clean, modular, reusable, industry-standard frontend architecture**

The goal is not just to make the UI look correct. The implementation must also be clean, maintainable, scalable, reusable, and easy for other developers to understand and modify.

---

## 1. Single Source of Truth for UI Design

The C5i design system is the single source of truth:

`frontend/docs/design-system.md`

Local path:

`d:\DiscoveryHub\frontend\docs\design-system.md`

Read that file before writing or changing UI code.

Do not guess token names, colors, typography values, spacing, radius, or component states.

---

# 2. Mandatory Code Architecture and Modularity Rules

## 2.1 Build Small, Focused Components

Do not place large amounts of UI, styling logic, state logic, and repeated markup inside a single page or component.

Break the implementation into small, focused, reusable components wherever appropriate.

For example, instead of:

```text
ProjectPage.tsx
  └── Hundreds of lines containing:
      - Header
      - Navigation
      - Filters
      - Search
      - Cards
      - Forms
      - Modals
      - Tables
      - Empty states
```

Prefer:

```text
ProjectPage/
├── ProjectPage.tsx
├── ProjectHeader.tsx
├── ProjectFilters.tsx
├── ProjectSearch.tsx
├── ProjectCard.tsx
├── ProjectList.tsx
├── ProjectEmptyState.tsx
└── ProjectModal.tsx
```

Each component should have one clear responsibility.

---

## 2.2 Reuse Components Instead of Duplicating Code

Before creating new UI code, check whether an existing component can be reused.

Do not duplicate:

- Buttons
- Inputs
- Dropdowns
- Cards
- Modals
- Tabs
- Tables
- Navigation items
- Empty states
- Loading states
- Status badges
- Form layouts

If the same UI pattern appears in multiple places, create or reuse a shared component.

Prefer:

```text
components/
├── ui/
│   ├── Button.tsx
│   ├── Input.tsx
│   ├── Select.tsx
│   ├── Modal.tsx
│   ├── Card.tsx
│   ├── Badge.tsx
│   └── EmptyState.tsx
```

over creating slightly different copies of the same component on every page.

---

## 2.3 Keep Pages and Components Clean

Page-level files should primarily be responsible for:

- Page composition
- Layout
- Coordinating page-level state
- Connecting reusable components

They should not become large files containing every UI detail.

Move complex sections into separate components.

Avoid unnecessarily large files.

If a component starts handling multiple unrelated responsibilities, split it into smaller logical components.

---

## 2.4 Separate UI, Logic, and Reusable Utilities

Keep different responsibilities separated.

Prefer a structure similar to:

```text
components/
hooks/
lib/
utils/
types/
features/
```

Use:

- **Components** for reusable UI
- **Hooks** for reusable stateful logic
- **Utilities** for reusable helper functions
- **Types** for shared TypeScript types
- **Feature folders** for feature-specific components and logic

Do not place unrelated helper functions, types, constants, and large amounts of business logic directly inside UI components.

---

## 2.5 Avoid Over-Engineering

Modularity should improve clarity, not create unnecessary complexity.

Do not create a separate component for every tiny element if it makes the code harder to understand.

Create a new component when it:

- Is reused
- Has a distinct responsibility
- Makes the parent component significantly cleaner
- Contains meaningful logic or markup
- Represents a clear UI section or pattern

Keep closely related, simple markup together when splitting it would reduce readability.

The goal is **clean architecture**, not unnecessary fragmentation.

---

## 2.6 Create Reusable and Configurable Components

Shared components should be designed to support reasonable reuse.

For example:

```text
<Button
  variant="primary"
  size="medium"
  loading={false}
  disabled={false}
/>
```

instead of creating separate duplicated components such as:

```text
PrimaryButton.tsx
SecondaryButton.tsx
LargePrimaryButton.tsx
SmallPrimaryButton.tsx
```

when a single reusable component can handle these variations cleanly.

However, do not add excessive props or variants that are not genuinely needed.

---

## 2.7 Use Clear Naming Conventions

Use clear, descriptive, and consistent names.

Examples:

- `ProjectHeader`
- `DiscoveryProgressCard`
- `ContextLibrary`
- `ArtifactList`
- `CreateProjectModal`

Avoid vague names such as:

- `Component1`
- `Box`
- `Data`
- `Helper`
- `Stuff`
- `NewComponent`

Functions, variables, props, hooks, and files should clearly communicate their purpose.

---

## 2.8 Keep Props Clean and Typed

Component props should be:

- Clearly named
- Minimal
- Purposeful
- Strongly typed where TypeScript is used

Avoid passing unnecessary large objects when only a few values are needed.

Avoid deeply nested prop drilling when a cleaner architecture or appropriate shared state approach exists.

---

## 2.9 Avoid Hard-Coded Repeated Values

Do not repeatedly hard-code the same:

- Labels
- Configuration values
- UI states
- Option lists
- Repeated strings
- Component variations

Move repeated values into appropriate constants or configuration structures when this improves maintainability.

The same principle applies to design values: always use the C5i design system tokens instead of hard-coded visual values.

---

## 2.10 Maintain Consistent File Organization

Organize code logically.

A recommended approach:

```text
frontend/
├── app/
│   └── ...
│
├── components/
│   ├── ui/
│   │   ├── Button.tsx
│   │   ├── Input.tsx
│   │   ├── Card.tsx
│   │   └── Modal.tsx
│   │
│   └── shared/
│       └── ...
│
├── features/
│   ├── projects/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── types/
│   │   └── utils/
│   │
│   └── discovery/
│       └── ...
│
├── hooks/
├── lib/
├── utils/
├── types/
└── docs/
```

Follow the existing repository architecture where it already exists. Do not restructure the entire project unnecessarily.

---

# 3. Design System Implementation

## 3.1 Read the Design System Documentation First

Read at least the sections relevant to the UI work:

- **Colors and themes:** Sections 2 and 4
- **Control states:** Section 3
- **Text:** Section 1.4 and Section 5, Rule 5
- **Spacing:** Section 1.5
- **Corners:** Section 1.6
- **Implementation rules:** Section 5
- **Known issues:** Section 6

---

## 3.2 Reference Tokens by Semantic Name

Never use raw hex values directly in UI code.

Use CSS variables from Section 4.

Examples:

```css
var(--color-text-default-primary)
var(--color-bg-default-primary)
var(--space-4)
var(--radius-md)
var(--font-size-body-medium)
```

Use **Semantic Tokens** in UI code.

Use **Primitive Tokens** such as:

```css
--color-brand-500
```

only when defining new semantic tokens.

Use **Component Tokens** from Section 3 when building controls so that:

- Default states
- Hover states
- Focus states
- Selected states
- Disabled states

remain consistent with the design system.

---

# 4. Design System Rules

## 4.1 Spacing

Use the 4px spacing grid.

Padding, margins, and gaps should follow the spacing tokens defined in the design system.

Do not introduce arbitrary spacing values unless explicitly supported by the design system.

---

## 4.2 Typography

Every font size must be paired with the appropriate line height from the design system type scale.

Use:

- **Degular** for headings and primary text
- **Segoe UI** with the required system fallback stack for secondary text

Example fallback:

```css
"Segoe UI", system-ui, sans-serif
```

---

## 4.3 Border Radius

Use Radius tokens only.

Example:

```css
var(--radius-sm)
var(--radius-md)
var(--radius-lg)
```

For pill-shaped UI, a large value such as:

```css
9999px
```

is allowed, but this should be explicitly identified as an exception outside the standard radius token system.

---

## 4.4 Dark Mode

Follow the design system's existing approach:

```css
:root[data-theme="dark"]
```

and the relevant:

```css
prefers-color-scheme
```

implementation.

Do not automatically invert colors.

Always ensure new UI works correctly in both light and dark themes.

---

# 5. Existing Component Reuse

Before building a new component:

1. Check whether a similar component already exists.
2. Reuse it if it meets the requirement.
3. Extend it carefully if a small additional capability is needed.
4. Create a new component only when the existing component is not appropriate.

Do not modify a shared component in a way that unintentionally breaks other parts of the application.

When extending shared components, preserve backward compatibility whenever possible.

---

# 6. Code Quality Standards

All UI code should aim to meet professional, industry-level standards.

The implementation should be:

- Clean
- Modular
- Readable
- Reusable
- Maintainable
- Consistent
- Scalable
- Easy to review

Avoid:

- Massive monolithic components
- Duplicate markup
- Duplicate styling logic
- Hard-coded design values
- Unclear naming
- Unnecessary inline logic
- Unused code
- Dead components
- Excessive prop drilling
- Overly complex conditional rendering
- Unnecessary abstraction

Prefer:

- Small focused components
- Reusable hooks
- Shared utilities
- Clear types
- Consistent naming
- Logical folder structure
- Reusable configuration
- Simple, readable code

---

# 7. Component Design Principles

When creating a component, consider:

### Reusability
Can this component be used elsewhere?

### Single Responsibility
Does this component have one clear purpose?

### Maintainability
Can another developer easily understand and modify it?

### Scalability
Can the component handle reasonable future variations without being rewritten?

### Consistency
Does it use the C5i design system and existing component patterns?

### Simplicity
Is the implementation as simple as possible while remaining clean and maintainable?

---

# 8. If a Design Value Is Missing

If a value you need is not available in the design system:

1. Do not invent a new value.
2. Use the nearest existing token where appropriate.
3. Explain which token was selected and why.
4. If the design genuinely requires a new token, recommend it to the design team.
5. Do not add raw hex, RGB, or arbitrary visual values inline.

---

# 9. Known Issues

Section 6 of the design system document affects real implementation.

Notably:

- `Color/Base/Transparent` has no defined value. Use:

```css
transparent
```

and mention it as an exception.

- Use the correct spelling:

```text
Disabled
```

not the typo:

```text
Diasabled
```

from the source file.

- Segoe UI is not available on macOS, Linux, or many web environments. Always include:

```css
"Segoe UI", system-ui, sans-serif
```

---

# 10. When This Skill Applies

Use this skill for any of the following, even when the user does not explicitly mention the design system:

- Creating or editing components
- Creating or editing pages
- Building layouts
- Styling UI
- Building buttons
- Building forms
- Building inputs
- Building cards
- Building navigation
- Building modals
- Building tables
- Choosing colors
- Choosing typography
- Choosing font sizes
- Choosing spacing
- Choosing border radius
- Choosing shadows
- Implementing dark mode
- Refactoring existing UI code
- Breaking large UI components into reusable components
- Improving frontend code quality or maintainability

This skill applies to UI work within:

```text
frontend/
```

It does not apply to backend-only work with no UI output.

---

# 11. Required Workflow for UI Changes

When working on UI:

### Step 1: Inspect Before Changing

Read the relevant design system documentation.

Inspect existing related components before creating new ones.

### Step 2: Plan the Component Structure

Before writing a large amount of code, identify:

- What should remain at the page level
- What should become reusable components
- What can reuse existing components
- What logic belongs in hooks or utilities

### Step 3: Implement Cleanly

Build the UI using:

- C5i semantic tokens
- Reusable components
- Clear component boundaries
- Clean naming
- Minimal duplication

### Step 4: Check for Duplication

Before finishing, check whether:

- Similar UI already exists
- Code has been duplicated
- A repeated pattern should become reusable
- A large component should be split

### Step 5: Validate

Ensure:

- The UI follows the design system
- Light mode works
- Dark mode works
- Component states are handled correctly
- The implementation is clean and modular
- No unnecessary hard-coded design values were introduced

---

# 12. Output Expectations

All UI work must meet the following expectations:

- Styles use CSS variables or Tailwind classes that resolve to C5i design system tokens.
- No new hard-coded hex, RGB, or arbitrary visual values for colors, text, spacing, or radius.
- Large UI implementations are broken into logical, reusable components.
- Existing reusable components are used wherever appropriate.
- Duplicate UI code is avoided.
- Page files remain clean and focused on composition.
- Complex reusable logic is moved into hooks or utilities where appropriate.
- Components have clear, descriptive names.
- Code is organized logically and consistently.
- The implementation should look and feel like professional, production-quality frontend code.

When finishing UI work, briefly state:

1. Which design system tokens and component mappings were used.
2. Which components were created, reused, or refactored.
3. Any significant modularization decisions.
4. Any design-system gap or exception that had to be worked around.
