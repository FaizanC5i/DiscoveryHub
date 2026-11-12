import type { TextareaHTMLAttributes } from "react";
import { cn } from "@/lib/cn";

export interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  invalid?: boolean;
}

/** Multi-line text input styled with the same Input/* component tokens as Input. */
export function Textarea({ invalid = false, className, ...props }: TextareaProps) {
  return (
    <textarea
      aria-invalid={invalid || undefined}
      className={cn(
        "min-h-32 w-full resize-y rounded-control border bg-surface px-3 py-2.5 text-body-large text-fg outline-none transition-colors",
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
