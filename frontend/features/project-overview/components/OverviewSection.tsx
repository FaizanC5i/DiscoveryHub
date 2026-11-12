import type { ReactNode } from "react";
import { Card } from "@/components/ui/Card";
import { cn } from "@/lib/cn";

interface OverviewSectionProps {
  title: string;
  badge?: ReactNode;
  action?: ReactNode;
  className?: string;
  children: ReactNode;
}

export function OverviewSection({ title, badge, action, className, children }: OverviewSectionProps) {
  return (
    <Card className={cn("flex flex-col gap-4 p-6", className)}>
      <header className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <h2 className="text-title-small font-semibold text-fg">{title}</h2>
          {badge}
        </div>
        {action}
      </header>
      {children}
    </Card>
  );
}