import type { HTMLAttributes } from "react";
import { cn } from "@/lib/cn";

export type BadgeTone = "brand" | "neutral" | "success" | "warning" | "error";

const toneClasses: Record<BadgeTone, string> = {
  brand: "bg-badge-brand-bg text-badge-brand-fg",
  neutral: "bg-badge-neutral-bg text-badge-neutral-fg",
  success: "bg-badge-success-bg text-badge-success-fg",
  warning: "bg-badge-warning-bg text-badge-warning-fg",
  error: "bg-badge-error-bg text-badge-error-fg",
};

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  tone?: BadgeTone;
}

export function Badge({ tone = "neutral", className, ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-chip px-2 py-0.5 text-caption font-medium whitespace-nowrap",
        toneClasses[tone],
        className,
      )}
      {...props}
    />
  );
}
