import { SectionCard } from "@/components/ui/SectionCard";
import { ReviewLink } from "./ReviewLink";

interface ProblemStatementCardProps {
  statement: string;
  reviewHref: string;
}

export function ProblemStatementCard({ statement, reviewHref }: ProblemStatementCardProps) {
  return (
    <SectionCard title="Problem statement" action={<ReviewLink href={reviewHref} />}>
      <p className="text-body-large text-fg-secondary">{statement}</p>
    </SectionCard>
  );
}