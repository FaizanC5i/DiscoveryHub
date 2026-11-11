import { SectionCard } from "@/components/ui/SectionCard";
import type { Stakeholder } from "../types/projectOverview";
import { ReviewLink } from "./ReviewLink";

interface StakeholdersCardProps {
  internal: Stakeholder[];
  external: Stakeholder[];
  reviewHref: string;
}

export function StakeholdersCard({ internal, external, reviewHref }: StakeholdersCardProps) {
  return (
    <SectionCard title="Stakeholders" action={<ReviewLink href={reviewHref} />}>
      <div className="grid gap-6 sm:grid-cols-2">
        <StakeholderGroup heading="Internal" stakeholders={internal} />
        <StakeholderGroup heading="External" stakeholders={external} />
      </div>
    </SectionCard>
  );
}

function StakeholderGroup({
  heading,
  stakeholders,
}: {
  heading: string;
  stakeholders: Stakeholder[];
}) {
  return (
    <div className="flex flex-col gap-4">
      <h3 className="text-body-small text-fg-muted">{heading}</h3>
      <ul className="flex flex-col gap-4">
        {stakeholders.map(({ role, note }) => (
          <li key={role} className="flex flex-col">
            <span className="text-body-medium font-semibold text-fg">{role}</span>
            <span className="text-body-small text-fg-muted">{note}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}