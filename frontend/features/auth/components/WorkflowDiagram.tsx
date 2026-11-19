import { SparklesIcon } from "@/components/icons";
import { WORKFLOW_STEPS } from "../constants";

/** Decorative flow from idea to code, shown on the brand panel. */
export function WorkflowDiagram() {
  return (
    <div className="flex flex-col items-center gap-6" aria-hidden="true">
      <div className="flex size-16 items-center justify-center rounded-card border border-panel-border bg-panel-raised text-panel-accent">
        <SparklesIcon className="size-7" />
      </div>
      <div className="flex items-center">
        {WORKFLOW_STEPS.map((step, index) => (
          <div key={step} className="flex items-center">
            <span className="rounded-control border border-panel-border bg-panel-raised px-4 py-2 text-body-medium text-panel-fg">
              {step}
            </span>
            {index < WORKFLOW_STEPS.length - 1 ? (
              <span className="h-px w-6 bg-panel-border" />
            ) : null}
          </div>
        ))}
      </div>
    </div>
  );
}
