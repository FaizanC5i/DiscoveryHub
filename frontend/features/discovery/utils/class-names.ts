/**
 * Shared Tailwind class strings for the Discovery Hub page.
 * Every value points at a variable in app/styles/tokens.css.
 */

const buttonBase =
  "inline-flex items-center justify-center gap-(--space-2) whitespace-nowrap rounded-(--radius-md) border " +
  "px-(--space-4) py-(--space-2) text-(length:--font-size-body-medium) leading-(--line-height-body-medium) " +
  "font-semibold no-underline cursor-pointer focus-visible:outline-2 focus-visible:outline-offset-2 " +
  "focus-visible:outline-(--color-primary-default)";

export const buttonClass = {
  primary: `${buttonBase} border-transparent bg-(--color-bg-brand-primary) text-(--color-text-default-inverse) hover:bg-(--color-bg-brand-secondary) active:bg-(--color-bg-brand-strong)`,
  secondary: `${buttonBase} border-(--color-border-brand-primary) bg-(--color-bg-default-primary) text-(--color-text-brand-primary) hover:border-(--color-border-brand-strong) hover:text-(--color-text-brand-strong)`,
  subtle: `${buttonBase} border-(--color-border-default-disabled) bg-(--color-bg-default-primary) text-(--color-text-default-primary) hover:bg-(--color-bg-default-secondary)`,
  icon: "inline-flex items-center justify-center rounded-(--radius-md) p-(--space-1) text-(--color-icon-secondary) hover:bg-(--color-bg-default-subtle) cursor-pointer",
};

const badgeBase =
  "inline-flex items-center gap-(--space-1) whitespace-nowrap rounded-full px-(--space-2) " +
  "text-(length:--font-size-caption) leading-(--line-height-caption) font-medium";

export const badgeClass = {
  brand: `${badgeBase} bg-(--color-bg-brand-subtle) text-(--color-text-brand-primary)`,
  grey: `${badgeBase} bg-(--color-neutral-75) text-(--color-neutral-950)`,
  success: `${badgeBase} bg-(--color-status-success-light) text-(--color-green-700)`,
  warning: `${badgeBase} bg-(--color-status-warning-light) text-(--color-yellow-700)`,
  error: `${badgeBase} bg-(--color-status-error-light) text-(--color-red-700)`,
};

/** Larger badge used in the summary card. */
export const badgeMedium =
  "px-(--space-3) py-(--space-1) text-(length:--font-size-body-small) leading-(--line-height-body-small)";

/** White card with the light grey border shown in the PDF. */
export const cardClass =
  "rounded-(--radius-xl) border border-(--color-border-default-disabled) bg-(--color-bg-default-primary)";