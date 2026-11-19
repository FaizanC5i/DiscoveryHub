import Link from "next/link";
import { ChevronLeftIcon } from "@/components/icons";
import { buttonStyles } from "@/components/ui/Button";
import { ROUTES } from "@/lib/constants";

interface PillarSubNavProps {
  projectId: string;
  title: string;
}

/** Bar under the header: back to the Discovery Hub and the page title. */
export function PillarSubNav({ projectId, title }: PillarSubNavProps) {
  return (
    <div className="border-b border-border-subtle bg-surface">
      <div className="grid h-14 grid-cols-[1fr_auto_1fr] items-center gap-4 px-4 sm:px-6 lg:px-8">
        <div className="flex">
          <Link
            href={ROUTES.projectSection(projectId, "discovery")}
            className={buttonStyles({ variant: "outline", size: "sm" })}
          >
            <ChevronLeftIcon className="size-4" />
            Discovery Hub
          </Link>
        </div>

        <h1 className="text-title-small font-semibold text-fg-brand">{title}</h1>

        <div />
      </div>
    </div>
  );
}
