"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { PageError, PageLoading } from "@/features/discovery/components/PageStatus";
import { badgeClass, cardClass } from "@/features/discovery/utils/class-names";
import {
  exportArtifactDraft,
  getArtifactDraft,
  clarifyDraftSection,
  regenerateDraftSection,
  saveDraftSectionContent,
  saveDraftVersion,
} from "../services/artifact-studio.service";
import type { ArtifactCode, ArtifactDraft, ClarificationAnswer, ExportOptions } from "../types/artifact-studio.types";
import { DraftExportBar } from "./DraftExportBar";
import { DraftSectionContent } from "./DraftSectionContent";
import { DraftSectionNav } from "./DraftSectionNav";
import { DraftStatusBanner } from "./DraftStatusBanner";
import { DraftVersionsCard } from "./DraftVersionsCard";

interface DraftEditorViewProps {
  projectId: string;
  /** From the URL, e.g. "brd". */
  artifactSlug: string;
}

/** The draft editor page (last page of the PDF). All data comes from the service files. */
export function DraftEditorView({ projectId, artifactSlug }: DraftEditorViewProps) {
  const code = artifactSlug.toUpperCase() as ArtifactCode;

  const [draft, setDraft] = useState<ArtifactDraft | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);
  const [activeSectionId, setActiveSectionId] = useState<string | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [isSavingVersion, setIsSavingVersion] = useState(false);

  useEffect(() => {
    let cancelled = false;
    getArtifactDraft(projectId, code)
      .then((result) => {
        if (!cancelled) setDraft(result);
      })
      .catch((e: unknown) => {
        if (!cancelled) setError(e instanceof Error ? e.message : "Could not load the draft.");
      });
    return () => {
      cancelled = true;
    };
  }, [projectId, code, reloadKey]);

  // While the agent is still writing the draft, check again every 10 seconds (not while editing).
  useEffect(() => {
    if (draft?.status !== "Generating" || isEditing) return;
    const timer = setTimeout(() => setReloadKey((k) => k + 1), 10_000);
    return () => clearTimeout(timer);
  }, [draft, isEditing]);

  function retry() {
    setError(null);
    setDraft(null);
    setReloadKey((k) => k + 1);
  }

  async function handleSaveSection(sectionId: string, content: string) {
    const updated = await saveDraftSectionContent(projectId, code, sectionId, content);
    setDraft((current) =>
      current ? { ...current, sections: current.sections.map((s) => (s.id === sectionId ? updated : s)) } : current,
    );
  }

  // The agent works in the background: reload, so the page shows "Generating" and keeps checking.
  async function handleRegenerate(sectionId: string, answers: ClarificationAnswer[]) {
    await regenerateDraftSection(projectId, code, sectionId, answers);
    setReloadKey((k) => k + 1);
  }

  async function handleClarify(sectionId: string) {
    await clarifyDraftSection(projectId, code, sectionId);
    setReloadKey((k) => k + 1);
  }

  /** Left list: jump to the section on the scrolling page. */
  function goToSection(sectionId: string) {
    setActiveSectionId(sectionId);
    document.getElementById(`section-${sectionId}`)?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  async function handleSaveVersion() {
    if (!draft) return;
    setIsSavingVersion(true);
    const currentNumber = draft.versions.find((v) => v.isCurrent)?.number ?? 0;
    const newNumber = await saveDraftVersion(projectId, code, currentNumber);
    setDraft({
      ...draft,
      versions: [
        ...draft.versions.map((v) => ({ ...v, isCurrent: false })),
        { number: newNumber, label: "Just now", isCurrent: true },
      ],
    });
    setIsSavingVersion(false);
  }

  async function handleExport(options: ExportOptions) {
    if (!draft) return;
    const { fileName, blob } = await exportArtifactDraft(projectId, draft, options);
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = fileName;
    link.click();
    URL.revokeObjectURL(url);
  }

  if (error) return <PageError message={error} onRetry={retry} />;
  if (!draft) return <PageLoading label="Loading draft…" />;

  const activeSection = draft.sections.find((s) => s.id === activeSectionId) ?? draft.sections[0]!;

  return (
    <div className="flex flex-col gap-(--space-6)">
      {/* Breadcrumb */}
        <nav aria-label="Breadcrumb" className="text-(length:--font-size-body-small) leading-(--line-height-body-small)">
          <ol className="m-0 flex list-none items-center gap-(--space-1) p-0">
            <li>
              <Link
                href={`/projects/${projectId}/studio?artifact=${draft.artifactCode}`}
                className="text-(--color-text-default-subtle) no-underline hover:underline"
              >
                Artifact Studio
              </Link>
            </li>
            <li aria-hidden="true" className="text-(--color-text-default-subtle)">›</li>
            <li aria-current="page" className="font-semibold">{draft.artifactName}</li>
          </ol>
        </nav>

        {/* Status + versions */}
        <div className="grid grid-cols-1 gap-(--space-5) lg:grid-cols-[minmax(0,1fr)_var(--space-56)]">
          <DraftStatusBanner projectId={projectId} draft={draft} />
          <DraftVersionsCard versions={draft.versions} isSaving={isSavingVersion} onSaveVersion={() => void handleSaveVersion()} />
        </div>

        {/* Sections + document */}
        <div className={`${cardClass} grid grid-cols-1 overflow-hidden bg-(--color-bg-default-secondary) lg:grid-cols-[var(--space-56)_minmax(0,1fr)]`}>
          <DraftSectionNav sections={draft.sections} activeId={activeSection.id} onSelect={goToSection} />

          <div className="p-(--space-4) lg:p-(--space-7)">
            <article className={`${cardClass} p-(--space-5) lg:p-(--space-7)`}>
              <header className="mb-(--space-6) border-b-2 border-(--color-neutral-400) pb-(--space-6)">
                <h1 className="m-0 text-(length:--font-size-heading-5) leading-(--line-height-heading-5) font-medium">
                  {draft.title}
                </h1>
                <p className="m-0 mb-(--space-2) text-(length:--font-size-body-large) leading-(--line-height-body-large)">
                  {isEditing ? "Editing…" : "✓ Saved"}
                </p>
                <p className="m-0 mb-(--space-3) font-(family-name:--font-family-secondary) text-(length:--font-size-body-medium) leading-(--line-height-body-medium) text-(--color-text-default-subtle)">
                  {draft.description}
                </p>
                <span className={badgeClass.brand}>{draft.status}</span>
              </header>

              {/* All sections on one scrolling page, as in the original BRD tool. */}
              <div className="flex flex-col gap-(--space-12)">
                {draft.sections.map((section) => (
                  <DraftSectionContent
                    key={section.id}
                    section={section}
                    isBusy={draft.status === "Generating"}
                    onSave={(content) => handleSaveSection(section.id, content)}
                    onRegenerate={(answers) => handleRegenerate(section.id, answers)}
                    onClarify={() => handleClarify(section.id)}
                    onEditingChange={setIsEditing}
                  />
                ))}
              </div>
            </article>
          </div>
        </div>

      <DraftExportBar isClientReady={draft.isClientReady} onExport={handleExport} />
    </div>
  );
}