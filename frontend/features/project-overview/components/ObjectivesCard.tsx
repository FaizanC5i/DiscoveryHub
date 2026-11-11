import { Badge } from "@/components/ui/Badge";
import { SectionCard } from "@/components/ui/SectionCard";
import { ReviewLink } from "./ReviewLink";

interface ObjectivesCardProps {
  items: string[];
  isAiDraft: boolean;
  reviewHref: string;
}

export function ObjectivesCard({ items, isAiDraft, reviewHref }: ObjectivesCardProps) {
  return (
    <SectionCard
      title="Objectives"
      badge={isAiDraft ? <Badge tone="brand">AI draft</Badge> : null}
      action={<ReviewLink href={reviewHref} />}
    >
      <ul className="flex flex-col gap-3">
        {items.map((item) => (
          <li key={item} className="flex gap-3 text-body-medium text-fg-secondary">
            <span aria-hidden="true" className="mt-2 size-1.5 shrink-0 rounded-full bg-accent" />
            {item}
          </li>
        ))}
      </ul>
    </SectionCard>
  );
}