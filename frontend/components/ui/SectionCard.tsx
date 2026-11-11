import type { ReactNode } from "react";
import { cn } from "@/lib/cn";
import { Card } from "./Card";

interface SectionCardProps {
  title: string;
  badge?: ReactNode;
  action?: ReactNode;
  className?: string;
  children: ReactNode;
}

/** Card with a standard header: title, optional badge, optional right-aligned action. */
export function SectionCard({ title, badge, action, className, children }: SectionCardProps) {
  return (
    <Card className={cn("flex flex-col gap-4 p-6", className)}>
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <h2 className="text-title-small font-semibold text-fg">{title}</h2>
          {badge}
        </div>
        {action}
      </div>
      {children}
    </Card>
  );
}