import type { ReactNode } from "react";
import { cn } from "@/lib/cn";

interface AlertProps {
  children: ReactNode;
  className?: string;
}

/** Inline error message for form-level and page-level failures. */
export function Alert({ children, className }: AlertProps) {
  return (
    <div
      role="alert"
      className={cn(
        "rounded-control border border-error bg-error-subtle px-4 py-3 text-body-medium text-fg",
        className,
      )}
    >
      {children}
    </div>
  );
}
