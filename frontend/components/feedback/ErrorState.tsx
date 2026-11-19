import { Button } from "@/components/ui/Button";
import { cardStyles } from "@/components/ui/Card";
import { cn } from "@/lib/cn";

interface ErrorStateProps {
  title: string;
  message: string;
  onRetry?: () => void;
  className?: string;
}

/** Route or section error with an optional retry action. */
export function ErrorState({ title, message, onRetry, className }: ErrorStateProps) {
  return (
    <div role="alert" className={cn(cardStyles, "flex flex-col items-start gap-3 p-6", className)}>
      <h2 className="text-title-small font-semibold text-fg">{title}</h2>
      <p className="text-body-medium text-fg-muted">{message}</p>
      {onRetry ? (
        <Button variant="outline" size="sm" onClick={onRetry}>
          Try again
        </Button>
      ) : null}
    </div>
  );
}
