# C5i Design System: Tokens Reference

Source: Figma file "C5i - Design System" (key `OTvxyJS6b7qLpai3hurziJ`), local variable collections: **Primitives**, **Semantic** (modes: Light, Dark), **Component**.

Use this file as the single source of truth for colors, typography, spacing, and radii. Always reference tokens by their semantic name (for example `--color-text-default-primary`) rather than hard-coding hex values in components. Primitives are the raw palette; Semantic tokens are what UI should use; Component tokens are aliases for specific controls.

---

## 1. Primitive tokens

### 1.1 Color: Brand (purple)

| Token | Hex |
|---|---|
| Color/Brand/50 | `#ede8ff` |
| Color/Brand/75 | `#e5deff` |
| Color/Brand/100 | `#ddd5ff` |
| Color/Brand/200 | `#bdaaff` |
| Color/Brand/300 | `#a07dff` |
| Color/Brand/400 | `#8647ff` |
| Color/Brand/500 | `#5500ba` |
| Color/Brand/600 | `#6800e0` |
| Color/Brand/700 | `#420093` |
| Color/Brand/800 | `#2f006e` |
| Color/Brand/900 | `#1e004a` |
| Color/Brand/950 | `#110030` |

### 1.2 Color: Neutral (grey)

| Token | Hex |
|---|---|
| Color/Neutral/50 | `#f6f6f6` |
| Color/Neutral/75 | `#ebebeb` |
| Color/Neutral/100 | `#e2e2e2` |
| Color/Neutral/200 | `#c6c6c6` |
| Color/Neutral/300 | `#a8a8a8` |
| Color/Neutral/400 | `#8e8e8e` |
| Color/Neutral/500 | `#747474` |
| Color/Neutral/600 | `#5c5c5c` |
| Color/Neutral/700 | `#444444` |
| Color/Neutral/800 | `#2e2e2e` |
| Color/Neutral/900 | `#181818` |
| Color/Neutral/950 | `#0c0c0c` |

### 1.3 Color: Base and Tertiary

| Token | Hex |
|---|---|
| Color/Base/White | `#ffffff` |
| Color/Base/Black | `#000000` |
| Color/Tertiary/Green/100 | `#d7f5dc` |
| Color/Tertiary/Green/500 | `#0aa50e` |
| Color/Tertiary/Green/700 | `#09590b` |
| Color/Tertiary/Yellow/100 | `#fffad8` |
| Color/Tertiary/Yellow/500 | `#ffce00` |
| Color/Tertiary/Yellow/700 | `#624f03` |
| Color/Tertiary/Orange/100 | `#fce6d5` |
| Color/Tertiary/Orange/500 | `#ea792d` |
| Color/Tertiary/Orange/700 | `#b85a17` |
| Color/Tertiary/Red/100 | `#fadada` |
| Color/Tertiary/Red/500 | `#e84646` |
| Color/Tertiary/Red/700 | `#8f0b0b` |

### 1.4 Typography

| Token | Value |
|---|---|
| Type/Font family/Primary | `Degular` |
| Type/Font family/Secondary | `Segoe UI` |
| Type/Font weight/Regular | `400` |
| Type/Font weight/Medium | `500` |
| Type/Font weight/Semi Bold | `600` |
| Type/Font weight/Bold | `700` |

**Type scale (font size / line height, px)**

| Style | Font size | Line height |
|---|---|---|
| Caption | 12 | 16 |
| Body-small | 13 | 20 |
| Body-medium | 14 | 20 |
| Body-large | 16 | 24 |
| Title-small | 18 | 24 |
| Title-medium | 20 | 28 |
| Title-large | 23 | 32 |
| Heading-6 | 26 | 32 |
| Heading-5 | 29 | 36 |
| Heading-4 | 32 | 40 |
| Heading-3 | 36 | 44 |
| Heading-2 | 41 | 52 |
| Heading-1 | 46 | 56 |

### 1.5 Spacing (4px base grid)

| Token | px | Token | px |
|---|---|---|---|
| Spacing/1 | 4 | Spacing/16 | 64 |
| Spacing/2 | 8 | Spacing/20 | 80 |
| Spacing/3 | 12 | Spacing/24 | 96 |
| Spacing/4 | 16 | Spacing/32 | 128 |
| Spacing/5 | 20 | Spacing/40 | 160 |
| Spacing/6 | 24 | Spacing/48 | 192 |
| Spacing/7 | 32 | Spacing/56 | 224 |
| Spacing/10 | 40 | Spacing/64 | 256 |
| Spacing/12 | 48 | | |

### 1.6 Radius

| Token | px |
|---|---|
| Radius/xs | 2 |
| Radius/sm | 4 |
| Radius/md | 8 |
| Radius/lg | 12 |
| Radius/xl | 16 |

No full/pill radius token exists. Use a large value such as `9999px` only for pills, and note it is outside the system.

---

## 2. Semantic tokens (Light / Dark)

Each row lists the Light value, then the Dark value. Use these in components. The Dark column is applied when the theme is dark.

### 2.1 Background

| Token | Light | Dark |
|---|---|---|
| Background/Default/Primary | `#ffffff` | `#0c0c0c` |
| Background/Default/Secondary | `#f6f6f6` | `#181818` |
| Background/Default/Subtle | `#ebebeb` | `#2e2e2e` |
| Background/Default/Disabled | `#e2e2e2` | `#444444` |
| Background/Default/Inverse | `#ffffff` | `#ffffff` |
| Background/Brand/Primary | `#5500ba` | `#5500ba` |
| Background/Brand/Secondary | `#6800e0` | `#6800e0` |
| Background/Brand/Strong | `#420093` | `#420093` |
| Background/Brand/Subtle | `#ede8ff` | `#ede8ff` |

### 2.2 Text

| Token | Light | Dark |
|---|---|---|
| Text/Default/Primary | `#000000` | `#ffffff` |
| Text/Default/Secondary | `#2e2e2e` | `#e2e2e2` |
| Text/Default/Subtle | `#5c5c5c` | `#a8a8a8` |
| Text/Default/Disabled | `#c6c6c6` | `#747474` |
| Text/Default/Inverse | `#ffffff` | `#000000` |
| Text/Brand/Primary | `#5500ba` | `#5500ba` |
| Text/Brand/Secondary | `#6800e0` | `#6800e0` |
| Text/Brand/Strong | `#420093` | `#420093` |
| Text/Brand/Subtle | `#bdaaff` | `#bdaaff` |

### 2.3 Border

| Token | Light | Dark |
|---|---|---|
| Border/Default/Primary | `#8e8e8e` | `#444444` |
| Border/Default/Strong | `#181818` | `#c6c6c6` |
| Border/Default/Subtle | `#f6f6f6` | `#f6f6f6` |
| Border/Default/Disabled | `#e2e2e2` | `#181818` |
| Border/Brand/Primary | `#5500ba` | `#5500ba` |
| Border/Brand/Strong | `#420093` | `#420093` |
| Border/Brand/Subtle | `#bdaaff` | `#bdaaff` |

### 2.4 Icon

| Token | Light | Dark |
|---|---|---|
| Icon/Primary | `#000000` | `#ffffff` |
| Icon/Secondary | `#444444` | `#c6c6c6` |
| Icon/Disabled | `#e2e2e2` | `#747474` |
| Icon/Inverse | `#ffffff` | `#000000` |

### 2.5 Primary (interactive brand accent)

| Token | Light | Dark |
|---|---|---|
| Color/Primary/Default | `#5500ba` | `#8647ff` |
| Color/Primary/Hover | `#6800e0` | `#a07dff` |
| Color/Primary/Selected | `#420093` | `#bdaaff` |
| Color/Primary/Light | `#a07dff` | `#5500ba` |
| Color/Primary/Subtle | `#bdaaff` | `#1e004a` |

### 2.6 Status

| Token | Light | Dark |
|---|---|---|
| Color/Status/Success | `#0aa50e` | `#0aa50e` |
| Color/Status/Warning | `#ffce00` | `#ffce00` |
| Color/Status/Error | `#e84646` | `#e84646` |
| Color/Status/Info | `#5500ba` | `#8647ff` |
| Color/Status/Status-light/Success | `#d7f5dc` | `#d7f5dc` |
| Color/Status/Status-light/Warning | `#fffad8` | `#fffad8` |
| Color/Status/Status-light/Error | `#fadada` | `#fadada` |
| Color/Status/Status-light/Info | `#ede8ff` | `#ede8ff` |

---

## 3. Component tokens

Component tokens are aliases to Semantic tokens. Apply them directly to the matching control. Resolve through Semantic (and then Primitives) when implementing.

### 3.1 Button

| Token | Maps to |
|---|---|
| Button/Primary/Default/Background | Background/Brand/Primary |
| Button/Primary/Default/Text | Text/Default/Inverse |
| Button/Primary/Hover/Background | Background/Brand/Secondary |
| Button/Primary/Hover/Text | Text/Default/Inverse |
| Button/Primary/Selected/Background | Background/Brand/Strong |
| Button/Primary/Selected/Text | Text/Default/Inverse |
| Button/Primary/Disabled/Background | Background/Default/Disabled |
| Button/Primary/Disabled/Text | Text/Default/Disabled |
| Button/Secondary/Default/Background | Background/Default/Primary |
| Button/Secondary/Default/Text | Text/Brand/Primary |
| Button/Secondary/Default/Border | Border/Brand/Primary |
| Button/Secondary/Hover/Background | Background/Default/Primary |
| Button/Secondary/Hover/Text | Text/Brand/Strong |
| Button/Secondary/Hover/Border | Border/Brand/Strong |
| Button/Secondary/Selected/Background | Background/Brand/Subtle |
| Button/Secondary/Selected/Text | Text/Brand/Strong |
| Button/Secondary/Selected/Border | Border/Brand/Primary |
| Button/Secondary/Disabled/Background | Background/Default/Primary |
| Button/Secondary/Disabled/Text | Text/Brand/Subtle |
| Button/Secondary/Disabled/Border | Border/Brand/Subtle |
| Button/Subtle/Default/Background | Background/Default/Primary |
| Button/Subtle/Default/Text | Text/Default/Primary |
| Button/Subtle/Hover/Background | Background/Default/Secondary |
| Button/Subtle/Hover/Text | Text/Default/Primary |
| Button/Subtle/Selected/Background | Background/Default/Subtle |
| Button/Subtle/Selected/Text | Text/Default/Primary |
| Button/Subtle/Disabled/Background | Background/Default/Disabled |
| Button/Subtle/Disabled/Text | Text/Default/Disabled |
| Button/Link/Default | Text/Default/Primary |
| Button/Link/Hover | Text/Default/Subtle |
| Button/Link/Selected | Text/Default/Primary |
| Button/Link/Disabled | Text/Default/Disabled |

### 3.2 Input

| Token | Maps to |
|---|---|
| Input/Background/Default | Background/Default/Primary |
| Input/Background/Disabled | Background/Default/Secondary |
| Input/Border/Default | Border/Default/Primary |
| Input/Border/Hover | Border/Brand/Primary |
| Input/Border/Selected | Border/Brand/Strong |
| Input/Border/Disabled | Border/Default/Disabled |
| Input/Border/Error | Color/Status/Error |
| Input/Text/Value | Text/Default/Primary |
| Input/Text/Placeholder | Text/Default/Subtle |
| Input/Text/Disabled | Text/Default/Disabled |
| Input/Text/Help-default | Text/Default/Subtle |
| Input/Text/Help-error | Color/Status/Error |
| Input/Label | Text/Default/Secondary |
| Input/Icon/Default | Icon/Secondary |
| Input/Icon/Focus | Color/Primary/Default |
| Input/Icon/Disabled | Icon/Disabled |
| Input/Divider | Border/Default/Subtle |

### 3.3 Dropdown

| Token | Maps to |
|---|---|
| Dropdown/Background/Default | Background/Default/Primary |
| Dropdown/Background/Disabled | Background/Default/Disabled |
| Dropdown/Border/Default | Border/Default/Primary |
| Dropdown/Border/Hover | Border/Brand/Primary |
| Dropdown/Border/Selected | Border/Brand/Strong |
| Dropdown/Border/Disabled | Border/Default/Disabled |
| Dropdown/Placeholder | Text/Default/Subtle |
| Dropdown/Option/Background/Default | Background/Default/Primary |
| Dropdown/Option/Background/Hover | Background/Default/Secondary |
| Dropdown/Option/Background/Selected | Background/Brand/Subtle |
| Dropdown/Option/Background/Disabled | Background/Default/Disabled |
| Dropdown/Option/Text/Default | Text/Default/Primary |
| Dropdown/Option/Text/Secondary | Text/Default/Subtle |
| Dropdown/Option/Text/Hover | Text/Default/Primary |
| Dropdown/Option/Text/Selected | Text/Brand/Primary |
| Dropdown/Option/Text/Disabled | Text/Default/Disabled |
| Dropdown/Option/Icon/Default | Icon/Secondary |
| Dropdown/Option/Icon/Hover | Icon/Secondary |
| Dropdown/Option/Icon/Selected | Color/Primary/Hover |
| Dropdown/Option/Icon/Disabled | Icon/Disabled |

### 3.4 Control (checkbox, radio, toggle)

| Token | Maps to |
|---|---|
| Control/Border/Unselected | Border/Default/Primary |
| Control/Border/Selected | Color/Primary/Default |
| Control/Background/Unselected | Background/Default/Primary |
| Control/Background/Selected | Color/Primary/Default |
| Control/Icon/Checked | Icon/Inverse |
| Control/Toggle/Handle | Background/Default/Primary |
| Control/Toggle/Track-off | Background/Default/Disabled |
| Control/Toggle/Track-on | Color/Primary/Default |

### 3.5 Slider

| Token | Maps to |
|---|---|
| Slider/Handle/Background/Default | Background/Default/Primary |
| Slider/Handle/Background/Disabled | Background/Default/Secondary |
| Slider/Handle/Border/Default | Border/Default/Subtle |
| Slider/Handle/Border/Disabled | Border/Default/Disabled |
| Slider/Track/Inactive | Background/Default/Disabled |
| Slider/Track/Active | Color/Primary/Default |
| Slider/Track/Disabled | Background/Default/Disabled |
| Slider/Popup/Background | Background/Default/Primary |
| Slider/Popup/Border | Border/Default/Subtle |
| Slider/Popup/Text | Text/Default/Primary |

### 3.6 Badges

| Token | Maps to |
|---|---|
| Badges/Brand/Background | Background/Brand/Subtle |
| Badges/Brand/Text | Text/Brand/Primary |
| Badges/Grey/Background | Color/Neutral/75 |
| Badges/Grey/Text | Color/Neutral/950 |
| Badges/Success/Background | Color/Status/Status-light/Success |
| Badges/Success/Text | Color/Tertiary/Green/700 |
| Badges/Warning/Background | Color/Status/Status-light/Warning |
| Badges/Warning/Text | Color/Tertiary/Yellow/700 |
| Badges/Error/Background | Color/Status/Status-light/Error |
| Badges/Error/Text | Color/Tertiary/Red/700 |

### 3.7 Surfaces (tooltip, card, modal)

| Token | Maps to |
|---|---|
| Surface/Tooltip/Bg | Background/Default/Inverse |
| Surface/Tooltip/Text | Text/Default/Inverse |
| Surface/Card/Bg | Background/Default/Primary |
| Surface/Card/Border | Border/Default/Subtle |
| Surface/Card/Value | Text/Default/Primary |
| Surface/Card/Description | Text/Default/Disabled |
| Surface/Card/Label | Text/Default/Disabled |
| Surface/Modal/Bg | Background/Default/Primary |
| Surface/Modal/Overlay | Color/Neutral/950 |

### 3.8 Navigation

| Token | Maps to |
|---|---|
| Nav/Sidebar-bg | Color/Primary/Default |
| Nav/Item/Text | Text/Default/Inverse |
| Nav/Item/Active-bg | Background/Default/Primary |
| Nav/Item/Active-text | Color/Primary/Default |
| Nav/Item/Hover-bg | Color/Primary/Hover |
| Nav Aids/Breadcrumb/link | Text/Default/Secondary |
| Nav Aids/Breadcrumb/current | Text/Default/Primary |
| Nav Aids/Breadcrumb/separator | Icon/Disabled |
| Nav Aids/Tab/Text-active | Color/Primary/Default |
| Nav Aids/Tab/Text-inactive | Text/Default/Secondary |
| Nav Aids/Tab/Border-active | Color/Primary/Default |
| Nav Aids/Tab/Border-inactive | Color/Base/Transparent |
| Nav Aids/Tab/Bg-hover | Background/Default/Subtle |

### 3.9 Feedback and data display

| Token | Maps to |
|---|---|
| Toast/Bg | Background/Default/Primary |
| Toast/Border | Border/Default/Subtle |
| Toast/Icon-success | Color/Status/Success |
| Toast/Icon-error | Color/Status/Error |
| Toast/Icon-warning | Color/Status/Warning |
| Toast/Icon-info | Color/Status/Info |
| Toast/Text-title | Text/Default/Primary |
| Toast/Text-body | Text/Default/Secondary |
| Table/Header-bg | Background/Default/Secondary |
| Table/Row-border | Border/Default/Subtle |
| Table/Row-bg-hover | Background/Default/Subtle |
| Table/Text-header | Text/Default/Secondary |
| Table/Text-cell | Text/Default/Primary |
| Progress/Track | Background/Default/Disabled |
| Progress/Indicator | Color/Primary/Default |
| Loader/Spinner | Color/Primary/Default |
| Stepper/Completed-bg | Color/Primary/Default |
| Stepper/Active-border | Color/Primary/Default |
| Stepper/Inactive-border | Background/Default/Disabled |
| Stepper/Line | Border/Default/Subtle |
| Accordion/Bg-default | Background/Default/Primary |
| Accordion/Bg-expanded | Background/Default/Subtle |
| Accordion/Border | Border/Default/Subtle |
| Accordion/Icon | Color/Primary/Default |

### 3.10 Calendar

| Token | Maps to |
|---|---|
| Calendar/Bg | Background/Default/Primary |
| Calendar/Date-default-text | Text/Default/Primary |
| Calendar/Date-selected-bg | Color/Primary/Default |
| Calendar/Date-selected-text | Icon/Inverse |
| Calendar/Date-hover-bg | Background/Default/Subtle |
| Calendar/Date-disabled-text | Text/Default/Disabled |

---

## 4. CSS custom properties (copy-ready)

Paste this into a global stylesheet. Light values are the default. Dark values apply under `[data-theme="dark"]` or `prefers-color-scheme: dark`.

```css
:root {
  /* Primitives: Brand */
  --color-brand-50: #ede8ff;
  --color-brand-75: #e5deff;
  --color-brand-100: #ddd5ff;
  --color-brand-200: #bdaaff;
  --color-brand-300: #a07dff;
  --color-brand-400: #8647ff;
  --color-brand-500: #5500ba;
  --color-brand-600: #6800e0;
  --color-brand-700: #420093;
  --color-brand-800: #2f006e;
  --color-brand-900: #1e004a;
  --color-brand-950: #110030;

  /* Primitives: Neutral */
  --color-neutral-50: #f6f6f6;
  --color-neutral-75: #ebebeb;
  --color-neutral-100: #e2e2e2;
  --color-neutral-200: #c6c6c6;
  --color-neutral-300: #a8a8a8;
  --color-neutral-400: #8e8e8e;
  --color-neutral-500: #747474;
  --color-neutral-600: #5c5c5c;
  --color-neutral-700: #444444;
  --color-neutral-800: #2e2e2e;
  --color-neutral-900: #181818;
  --color-neutral-950: #0c0c0c;

  /* Primitives: Base and Tertiary */
  --color-white: #ffffff;
  --color-black: #000000;
  --color-green-100: #d7f5dc;
  --color-green-500: #0aa50e;
  --color-green-700: #09590b;
  --color-yellow-100: #fffad8;
  --color-yellow-500: #ffce00;
  --color-yellow-700: #624f03;
  --color-orange-100: #fce6d5;
  --color-orange-500: #ea792d;
  --color-orange-700: #b85a17;
  --color-red-100: #fadada;
  --color-red-500: #e84646;
  --color-red-700: #8f0b0b;

  /* Typography */
  --font-family-primary: "Degular", "Segoe UI", system-ui, sans-serif;
  --font-family-secondary: "Segoe UI", system-ui, sans-serif;
  --font-weight-regular: 400;
  --font-weight-medium: 500;
  --font-weight-semibold: 600;
  --font-weight-bold: 700;

  --font-size-caption: 12px;        --line-height-caption: 16px;
  --font-size-body-small: 13px;     --line-height-body-small: 20px;
  --font-size-body-medium: 14px;    --line-height-body-medium: 20px;
  --font-size-body-large: 16px;     --line-height-body-large: 24px;
  --font-size-title-small: 18px;    --line-height-title-small: 24px;
  --font-size-title-medium: 20px;   --line-height-title-medium: 28px;
  --font-size-title-large: 23px;    --line-height-title-large: 32px;
  --font-size-heading-6: 26px;      --line-height-heading-6: 32px;
  --font-size-heading-5: 29px;      --line-height-heading-5: 36px;
  --font-size-heading-4: 32px;      --line-height-heading-4: 40px;
  --font-size-heading-3: 36px;      --line-height-heading-3: 44px;
  --font-size-heading-2: 41px;      --line-height-heading-2: 52px;
  --font-size-heading-1: 46px;      --line-height-heading-1: 56px;

  /* Spacing */
  --space-1: 4px;    --space-2: 8px;    --space-3: 12px;   --space-4: 16px;
  --space-5: 20px;   --space-6: 24px;   --space-7: 32px;   --space-10: 40px;
  --space-12: 48px;  --space-16: 64px;  --space-20: 80px;  --space-24: 96px;
  --space-32: 128px; --space-40: 160px; --space-48: 192px; --space-56: 224px;
  --space-64: 256px;

  /* Radius */
  --radius-xs: 2px;
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-xl: 16px;

  /* Semantic: Background */
  --color-bg-default-primary: #ffffff;
  --color-bg-default-secondary: #f6f6f6;
  --color-bg-default-subtle: #ebebeb;
  --color-bg-default-disabled: #e2e2e2;
  --color-bg-default-inverse: #ffffff;
  --color-bg-brand-primary: #5500ba;
  --color-bg-brand-secondary: #6800e0;
  --color-bg-brand-strong: #420093;
  --color-bg-brand-subtle: #ede8ff;

  /* Semantic: Text */
  --color-text-default-primary: #000000;
  --color-text-default-secondary: #2e2e2e;
  --color-text-default-subtle: #5c5c5c;
  --color-text-default-disabled: #c6c6c6;
  --color-text-default-inverse: #ffffff;
  --color-text-brand-primary: #5500ba;
  --color-text-brand-secondary: #6800e0;
  --color-text-brand-strong: #420093;
  --color-text-brand-subtle: #bdaaff;

  /* Semantic: Border */
  --color-border-default-primary: #8e8e8e;
  --color-border-default-strong: #181818;
  --color-border-default-subtle: #f6f6f6;
  --color-border-default-disabled: #e2e2e2;
  --color-border-brand-primary: #5500ba;
  --color-border-brand-strong: #420093;
  --color-border-brand-subtle: #bdaaff;

  /* Semantic: Icon */
  --color-icon-primary: #000000;
  --color-icon-secondary: #444444;
  --color-icon-disabled: #e2e2e2;
  --color-icon-inverse: #ffffff;

  /* Semantic: Primary (interactive accent) */
  --color-primary-default: #5500ba;
  --color-primary-hover: #6800e0;
  --color-primary-selected: #420093;
  --color-primary-light: #a07dff;
  --color-primary-subtle: #bdaaff;

  /* Semantic: Status */
  --color-status-success: #0aa50e;
  --color-status-warning: #ffce00;
  --color-status-error: #e84646;
  --color-status-info: #5500ba;
  --color-status-success-light: #d7f5dc;
  --color-status-warning-light: #fffad8;
  --color-status-error-light: #fadada;
  --color-status-info-light: #ede8ff;
}

:root[data-theme="dark"] {
    --color-bg-default-primary: #0c0c0c;
    --color-bg-default-secondary: #181818;
    --color-bg-default-subtle: #2e2e2e;
    --color-bg-default-disabled: #444444;
    --color-bg-default-inverse: #ffffff;

    --color-text-default-primary: #ffffff;
    --color-text-default-secondary: #e2e2e2;
    --color-text-default-subtle: #a8a8a8;
    --color-text-default-disabled: #747474;
    --color-text-default-inverse: #000000;
    --color-text-brand-subtle: #bdaaff;

    --color-border-default-primary: #444444;
    --color-border-default-strong: #c6c6c6;
    --color-border-default-subtle: #f6f6f6;
    --color-border-default-disabled: #181818;

    --color-icon-primary: #ffffff;
    --color-icon-secondary: #c6c6c6;
    --color-icon-disabled: #747474;
    --color-icon-inverse: #000000;

    --color-primary-default: #8647ff;
    --color-primary-hover: #a07dff;
    --color-primary-selected: #bdaaff;
    --color-primary-light: #5500ba;
    --color-primary-subtle: #1e004a;

    --color-status-info: #8647ff;
}

/* To follow the OS setting instead of a manual toggle, wrap the same dark block like this: */
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    /* same declarations as the dark block above */
  }
}
```

---

## 5. Implementation rules for AI builders

1. Never hard-code hex values in components. Use the semantic CSS variables.
2. Use Semantic tokens in UI code. Use Primitives only when defining new semantic tokens.
3. Use the Component token mapping in section 3 when building a control, so states (default, hover, selected, disabled) match the design.
4. Use the 4px spacing scale for padding, margin, and gap. Avoid values that are not on the grid.
5. Use the Type scale for all text. Pair each font size with its line height.
6. Use Degular for headings and primary text. Use Segoe UI as the secondary font, and keep the system fallback stack.
7. Use Radius tokens for all corners. The scale has no full radius token.
8. Apply the Dark values for dark theme. Do not invert colors automatically.

---

## 6. Known issues in the source file

These are noted in the Figma variables and should be reviewed by the design team:

- `Color/Base/Transparent` is referenced by `Nav Aids/Tab/Border-inactive` but its value was not found in the Primitives collection. Treat it as `transparent` until it is confirmed.
- Some component token names contain typos: `Button/Subtle/Diasabled/*` (should be `Disabled`) and `Input/Text/Help-default`.
- Several Semantic tokens use different values in Dark mode in ways that may be intentional but are worth a check, for example `Border/Default/Subtle` (`#f6f6f6` in both modes) and `Background/Default/Inverse` (white in both modes).
- `Type/Font family/Secondary` is set to Segoe UI, which is not available on macOS, Linux, or most web fonts. Provide a fallback or a web-safe alternative for non-Windows environments.
---

## 7. JSON version

This file does not include a separate JSON export. The CSS custom properties in section 4 carry the full token set with identical names. If a JSON format is needed (for example, for Style Dictionary or a token pipeline), generate it from those names.
