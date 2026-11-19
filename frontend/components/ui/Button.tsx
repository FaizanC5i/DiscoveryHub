import type { ButtonHTMLAttributes } from "react";
import { cn } from "@/lib/cn";
import { Spinner } from "./Spinner";

type ButtonVariant = "primary" | "secondary" | "outline" | "subtle" | "link";
type ButtonSize = "sm" | "md";

/*
 * Variants map to the design system component tokens:
 * - primary:   Button/Primary/*
 * - secondary: Button/Secondary/* (brand border, active = Selected state)
 * - outline:   Button/Subtle hover with Border/Default/Primary (neutral outline)
 * - subtle:    Button/Subtle/*
 * - link:      Button/Link/* (text only, ignores size)
 */
const variantClasses: Record<ButtonVariant, string> = {
  primary:
    "bg-surface-brand text-fg-inverse hover:bg-surface-brand-hover active:bg-surface-brand-pressed disabled:bg-surface-disabled disabled:text-fg-disabled",
  secondary:
    "border border-border-brand bg-surface text-fg-brand hover:border-border-brand-strong hover:text-fg-brand-strong active:bg-surface-brand-subtle active:text-fg-brand-strong disabled:border-border-brand-subtle disabled:text-fg-brand-subtle",
  outline:
    "border border-border bg-surface text-fg hover:bg-surface-muted disabled:text-fg-disabled disabled:border-border-disabled",
  subtle:
    "bg-surface text-fg hover:bg-surface-muted active:bg-surface-muted disabled:bg-surface-disabled disabled:text-fg-disabled",
  link: "gap-1 text-body-medium text-fg hover:text-fg-muted disabled:text-fg-disabled",
};

const sizeClasses: Record<ButtonSize, string> = {
  sm: "h-9 gap-2 px-3 text-body-medium",
  md: "h-11 gap-2 px-5 text-body-large",
};

interface ButtonStyleOptions {
  variant?: ButtonVariant;
  size?: ButtonSize;
  fullWidth?: boolean;
  className?: string;
}

/** Shared button styling, used by Button and by link-based buttons. */
export function buttonStyles({
  variant = "primary",
  size = "md",
  fullWidth = false,
  className,
}: ButtonStyleOptions = {}) {
  return cn(
    "inline-flex items-center justify-center rounded-control font-semibold whitespace-nowrap transition-colors",
    "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-border-brand-strong",
    "disabled:cursor-not-allowed",
    variantClasses[variant],
    variant !== "link" && sizeClasses[size],
    fullWidth && "w-full",
    className,
  );
}

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
  fullWidth?: boolean;
}

export function Button({
  variant = "primary",
  size = "md",
  loading = false,
  fullWidth = false,
  disabled,
  className,
  children,
  type = "button",
  ...props
}: ButtonProps) {
  return (
    <button
      type={type}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      className={buttonStyles({ variant, size, fullWidth, className })}
      {...props}
    >
      {loading ? <Spinner /> : null}
      {children}
    </button>
  );
}