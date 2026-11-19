"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { ArrowRightIcon } from "@/features/discovery/components/icons";
import { badgeClass, buttonClass, cardClass } from "@/features/discovery/utils/class-names";
import { generateArtifactDraft } from "../services/artifact-studio.service";
import type { ArtifactReadiness, ArtifactType } from "../types/artifact-studio.types";
import { GenerateConfirmDialog } from "./GenerateConfirmDialog";

const labelClass =
  "mb-(--space-2) flex items-center gap-(--space-2) text-(length:--font-size-body-medium) leading-(--line-height-body-medium) font-semibold text-(--color-text-default-secondary)";

const fieldClass =
  "w-full rounded-(--radius-md) border border-(--color-border-default-primary) bg-(--color-bg-default-primary) " +
  "px-(--space-3) py-(--space-2) font-(family-name:--font-family-secondary) text-(length:--font-size-body-medium) " +
  "leading-(--line-height-body-medium) text-(--color-text-default-primary) placeholder:text-(--color-text-default-subtle) " +
  "hover:border-(--color-border-brand-primary) focus-visible:outline-none focus-visible:border-(--color-border-brand-strong)";

interface DraftConfigFormProps {
  projectId: string;
  projectName: string;
  artifact: ArtifactType;
  audiences: string[];
  readiness: ArtifactReadiness;
}

/**
 * Step 3: title, audience and scope for the draft.
 * The parent gives this a `key` per artifact, so the title resets when the type changes.
 */
export function DraftConfigForm({ projectId, projectName, artifact, audiences, readiness }: DraftConfigFormProps) {
  const router = useRouter();
  const [title, setTitle] = useState(`${projectName}: ${artifact.name}`);
  const [audience, setAudience] = useState(audiences[0] ?? "");
  const [scope, setScope] = useState("");
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isFinalReady = readiness.verified === readiness.total;

  async function generate() {
    setIsGenerating(true);
    setError(null);
    try {
      await generateArtifactDraft(projectId, artifact.code, { title, audience, scope });
      setIsDialogOpen(false);
      setIsGenerating(false);
      router.push(`/projects/${projectId}/studio/${artifact.code.toLowerCase()}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not generate the draft.");
      setIsGenerating(false);
      setIsDialogOpen(false);
    }
  }

  // Discovery not complete: ask first. Complete: generate straight away.
  function handleGenerateClick() {
    if (isFinalReady) void generate();
    else setIsDialogOpen(true);
  }

  return (
    <section aria-labelledby="configure-title" className={`${cardClass} flex flex-col gap-(--space-4) p-(--space-5)`}>
      <h2
        id="configure-title"
        className="m-0 text-(length:--font-size-title-small) leading-(--line-height-title-small) font-semibold"
      >
        3. Configure the draft
      </h2>

      <div>
        <label htmlFor="draft-title" className={labelClass}>Document title</label>
        <input id="draft-title" value={title} onChange={(e) => setTitle(e.target.value)} className={fieldClass} />
      </div>

      <div>
        <label htmlFor="draft-audience" className={labelClass}>Audience</label>
        <select
          id="draft-audience"
          value={audience}
          onChange={(e) => setAudience(e.target.value)}
          className={fieldClass}
        >
          {audiences.map((a) => (
            <option key={a} value={a}>{a}</option>
          ))}
        </select>
      </div>

      <div>
        <label htmlFor="draft-scope" className={labelClass}>
          Scope
          <span className={`${badgeClass.grey} uppercase`}>Optional</span>
        </label>
        <input
          id="draft-scope"
          value={scope}
          onChange={(e) => setScope(e.target.value)}
          placeholder="For example, request intake and triage"
          className={fieldClass}
        />
        <p className="m-0 mt-(--space-2) text-(length:--font-size-caption) leading-(--line-height-caption) text-(--color-text-default-subtle)">
          Source selection does not raise the coverage score.
        </p>
      </div>

      <div>
        <button
          type="button"
          onClick={handleGenerateClick}
          disabled={isGenerating}
          className={`${buttonClass.primary} px-(--space-5) py-(--space-3) disabled:cursor-wait disabled:opacity-70`}
        >
          Generate {artifact.name}
          <ArrowRightIcon />
        </button>
        {error && (
          <p role="alert" className="m-0 mt-(--space-2) text-(length:--font-size-body-small) leading-(--line-height-body-small) text-(--color-red-700)">
            {error}
          </p>
        )}
      </div>

      <GenerateConfirmDialog
        open={isDialogOpen}
        projectId={projectId}
        artifactName={artifact.name}
        readiness={readiness}
        isGenerating={isGenerating}
        onConfirm={() => void generate()}
        onClose={() => setIsDialogOpen(false)}
      />
    </section>
  );
}