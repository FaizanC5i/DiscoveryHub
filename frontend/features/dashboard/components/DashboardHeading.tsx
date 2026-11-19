import type { ReactNode } from "react";

interface DashboardHeadingProps {
  firstName: string;
  action?: ReactNode;
}

export function DashboardHeading({ firstName, action }: DashboardHeadingProps) {
  return (
    <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
      <header className="flex flex-col gap-1">
        <h1 className="text-heading-6 font-medium text-fg">Welcome back, {firstName}.</h1>
        <p className="text-body-large text-fg-muted">
          Pick up a project, or start a new one from your documents.
        </p>
      </header>
      {action}
    </div>
  );
}
