/** Footer note explaining how artifacts turn into answers. */
export function WorkflowNote() {
  return (
    <section aria-labelledby="workflow-note-title" className="flex flex-col gap-2 rounded-card bg-surface-muted p-6">
      <h2 id="workflow-note-title" className="text-title-medium font-medium text-fg">
        Create or upload → Extract evidence → Review answer → Close the gap
      </h2>
      <p className="text-body-medium text-fg-muted">
        Artifacts are saved in the Context Library and linked to their phase and questions. Only a reviewed answer
        changes checklist coverage. You can create drafts in any phase before discovery is complete.
      </p>
    </section>
  );
}