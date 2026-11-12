"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { DiscoveryHeader } from "@/features/discovery/components/DiscoveryHeader";
import { PageError, PageLoading } from "@/features/discovery/components/PageStatus";
import { getDiscoveryOverview } from "@/features/discovery/services/discovery.service";
import type { DiscoveryOverview } from "@/features/discovery/types/discovery.types";
import { badgeClass, cardClass } from "@/features/discovery/utils/class-names";
import {
  exportArtifactDraft,
  getArtifactDraft,
  saveDraftSection,
  saveDraftVersion,
} from "../services/artifact-studio.service";
import type { ArtifactCode, ArtifactDraft, ExportOptions } from "../types/artifact-studio.types";
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

  const [overview, setOverview] = useState<DiscoveryOverview | null>(null);
  const [draft, setDraft] = useState<ArtifactDraft | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);
  const [activeSectionId, setActiveSectionId] = useState<string | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [isSavingVersion, setIsSavingVersion] = useState(false);

  useEffect(() => {
    let cancelled = false;
    Promise.all([getDiscoveryOverview(projectId), getArtifactDraft(projectId, code)])
      .then(([overviewResult, draftResult]) => {
        if (cancelled) return;
        setOverview(overviewResult);
        setDraft(draftResult);
      })
      .catch((e: unknown) => {
        if (!cancelled) setError(e instanceof Error ? e.message : "Could not load the draft.");
      });
    return () => {
      cancelled = true;
    };
  }, [projectId, code, reloadKey]);

  function retry() {
    setError(null);
    setOverview(null);
    setDraft(null);
    setReloadKey((k) => k + 1);
  }

  async function handleSaveSection(sectionId: string, bullets: string[]) {
    const updated = await saveDraftSection(projectId, code, sectionId, bullets);
    setDraft((current) =>
      current ? { ...current, sections: current.sections.map((s) => (s.id === sectionId ? updated : s)) } : current,
    );
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
  if (!overview || !draft) return <PageLoading label="Loading draft…" />;

  const activeSection = draft.sections.find((s) => s.id === activeSectionId) ?? draft.sections[0]!;

  return (
    <div className="flex min-h-dvh flex-col bg-(--color-bg-default-secondary) text-(--color-text-default-primary)">
      <DiscoveryHeader projectName={overview.project.name} userName={overview.user.name} />

      <main className="flex flex-1 flex-col gap-(--space-6) p-(--space-4) lg:p-(--space-7)">
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
          <DraftSectionNav sections={draft.sections} activeId={activeSection.id} onSelect={setActiveSectionId} />

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

              <DraftSectionContent
                key={activeSection.id}
                section={activeSection}
                onSave={(bullets) => handleSaveSection(activeSection.id, bullets)}
                onEditingChange={setIsEditing}
              />
            </article>
          </div>
        </div>
      </main>

      <DraftExportBar isClientReady={draft.isClientReady} onExport={handleExport} />
    </div>
  );
}