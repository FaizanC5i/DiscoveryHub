import type { InputHTMLAttributes } from "react";
import { cn } from "@/lib/cn";

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  invalid?: boolean;
}

/** Text input styled with the Input/* component tokens. */
export function Input({ invalid = false, className, ...props }: InputProps) {
  return (
    <input
      aria-invalid={invalid || undefined}
      className={cn(
        "h-11 w-full rounded-control border bg-surface px-3 text-body-large text-fg outline-none transition-colors",
        "placeholder:text-fg-muted",
        "disabled:bg-page disabled:text-fg-disabled",
        invalid
          ? "border-error"
          : "border-border hover:border-border-brand focus:border-border-brand-strong",
        className,
      )}
      {...props}
    />
  );
}
