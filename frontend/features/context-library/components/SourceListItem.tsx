import { Badge } from "@/components/ui/Badge";
import { SOURCE_ORIGINS } from "../constants";
import type { ContextSource } from "../types/contextLibrary";

export function SourceListItem({ source }: { source: ContextSource }) {
  const origin = SOURCE_ORIGINS[source.origin];

  return (
    <li className="flex flex-col items-start gap-1">
      <span className="text-body-small font-semibold break-all text-fg">{source.name}</span>
      <Badge tone={origin.tone}>{origin.label}</Badge>
    </li>
  );
}