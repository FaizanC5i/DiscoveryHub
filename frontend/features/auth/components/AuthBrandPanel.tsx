import { Logo } from "@/components/brand/Logo";
import { COPYRIGHT_TEXT, ROUTES } from "@/lib/constants";
import { AUTH_PANEL_COPY } from "../constants";
import { WorkflowDiagram } from "./WorkflowDiagram";

/** Dark marketing panel shown beside the auth forms on large screens. */
export function AuthBrandPanel() {
  return (
    <section className="relative flex min-h-[600px] flex-col justify-between overflow-hidden rounded-card bg-panel p-10 text-panel-fg">
      <div aria-hidden="true" className="pointer-events-none absolute -right-48 top-24 size-[520px] rounded-full border-[56px] border-panel-raised/60" />

      <Logo tone="panel" href={ROUTES.login} />

      <div className="relative flex flex-1 items-center justify-center py-12">
        <WorkflowDiagram />
      </div>

      <div className="relative flex flex-col gap-4">
        <p className="text-caption font-semibold uppercase tracking-wider text-panel-accent">
          {AUTH_PANEL_COPY.eyebrow}
        </p>
        <h2 className="text-heading-2 font-medium text-panel-fg">{AUTH_PANEL_COPY.headline}</h2>
        <p className="text-body-large text-panel-fg-muted">{AUTH_PANEL_COPY.description}</p>
        <p className="pt-2 text-caption text-panel-fg-muted">{COPYRIGHT_TEXT}</p>
      </div>
    </section>
  );
}
