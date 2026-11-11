import type { ButtonHTMLAttributes } from "react";
import { cn } from "@/lib/cn";
import { Spinner } from "./Spinner";

type ButtonVariant = "primary" | "outline" | "subtle";
type ButtonSize = "sm" | "md";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
  fullWidth?: boolean;
}

/*
 * Variants map to the design system component tokens:
 * - primary: Button/Primary/*
 * - outline: Button/Subtle hover with Border/Default/Primary (neutral outline)
 * - subtle:  Button/Subtle/*
 */
const variantClasses: Record<ButtonVariant, string> = {
  primary:
    "bg-surface-brand text-fg-inverse hover:bg-surface-brand-hover active:bg-surface-brand-pressed disabled:bg-surface-disabled disabled:text-fg-disabled",
  outline:
    "border border-border bg-surface text-fg hover:bg-surface-muted disabled:text-fg-disabled disabled:border-border-disabled",
  subtle:
    "bg-surface text-fg hover:bg-surface-muted active:bg-surface-muted disabled:bg-surface-disabled disabled:text-fg-disabled",
};

const sizeClasses: Record<ButtonSize, string> = {
  sm: "h-9 gap-2 px-3 text-body-medium",
  md: "h-11 gap-2 px-5 text-body-large",
};

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
      className={cn(
        "inline-flex items-center justify-center rounded-control font-semibold whitespace-nowrap transition-colors",
        "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-border-brand-strong",
        "disabled:cursor-not-allowed",
        variantClasses[variant],
        sizeClasses[size],
        fullWidth && "w-full",
        className,
      )}
      {...props}
    >
      {loading ? <Spinner /> : null}
      {children}
    </button>
  );
}
