import type { ReactNode } from "react";
import { cn } from "@/lib/cn";

interface ProgressRingProps {
  value: number;
  label: string;
  className?: string;
  children?: ReactNode;
}

const CENTER = 60;
const RADIUS = 52;
const STROKE_WIDTH = 10; // No stroke-width token exists in the design system.
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;

/** Circular progress. Progress/Track and Progress/Indicator component tokens. */
export function ProgressRing({ value, label, className, children }: ProgressRingProps) {
  const clamped = Math.min(100, Math.max(0, value));

  return (
    <div
      role="progressbar"
      aria-label={label}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={clamped}
      className={cn("relative size-28 shrink-0", className)}
    >
      <svg viewBox="0 0 120 120" aria-hidden="true" className="size-full -rotate-90">
        <circle
          cx={CENTER}
          cy={CENTER}
          r={RADIUS}
          fill="none"
          strokeWidth={STROKE_WIDTH}
          className="stroke-surface-disabled"
        />
        <circle
          cx={CENTER}
          cy={CENTER}
          r={RADIUS}
          fill="none"
          strokeWidth={STROKE_WIDTH}
          strokeLinecap="round"
          strokeDasharray={CIRCUMFERENCE}
          strokeDashoffset={CIRCUMFERENCE * (1 - clamped / 100)}
          className="stroke-accent transition-[stroke-dashoffset]"
        />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">{children}</div>
    </div>
  );
}