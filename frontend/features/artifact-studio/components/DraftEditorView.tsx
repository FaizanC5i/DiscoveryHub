"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { PageError, PageLoading } from "@/features/discovery/components/PageStatus";
import { badgeClass, cardClass } from "@/features/discovery/utils/class-names";
import {
  exportArtifactDraft,
  getArtifactDraft,
  regenerateDraftSection,
  requestSectionClarification,
  saveDraftSection,
  saveDraftVersion,
} from "../services/artifact-studio.service";
import type {
  ArtifactCode,
  ArtifactDraft,
  ClarificationAnswer,
  DraftSection,
  ExportOptions,
} from "../types/artifact-studio.types";
import { ClarifyDialog } from "./ClarifyDialog";
import { DraftExportBar } from "./DraftExportBar";
import { DraftSectionContent, type SectionActivity } from "./DraftSectionContent";
import { DraftSectionNav } from "./DraftSectionNav";
import { DraftStatusBanner } from "./DraftStatusBanner";
import { DraftVersionsCard } from "./DraftVersionsCard";

/** A Regenerate or Clarify run started from this page, followed until it finishes. */
interface PendingRun {
  runId: number;
  sectionId: string;
  kind: "regenerate" | "clarify";
}

/** How often to check a section run (seconds matter here) and a full generation. */
const SECTION_POLL_MS = 3_000;
const GENERATION_POLL_MS = 10_000;

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
  const [pending, setPending] = useState<PendingRun | null>(null);
  const [clarifySectionId, setClarifySectionId] = useState<string | null>(null);
  const [sectionMessages, setSectionMessages] = useState<Record<string, string>>({});
  // The load callback reads the pending run without re-subscribing the effect.
  const pendingRef = useRef<PendingRun | null>(null);

  function setPendingRun(run: PendingRun | null) {
    pendingRef.current = run;
    setPending(run);
  }

  function setSectionMessage(sectionId: string, message: string | null) {
    setSectionMessages((current) => {
      const next = { ...current };
      if (message) next[sectionId] = message;
      else delete next[sectionId];
      return next;
    });
  }

  useEffect(() => {
    let cancelled = false;
    getArtifactDraft(projectId, code)
      .then((result) => {
        if (cancelled) return;
        setDraft(result);

        // Did the run started from this page finish?
        const run = pendingRef.current;
        const latest = result.latestRun;
        if (!run || !latest || latest.id !== run.runId || latest.status === "running") return;
        pendingRef.current = null;
        setPending(null);

        if (latest.status === "failed") {
          setSectionMessage(run.sectionId, latest.error_message ?? "The agent could not finish. Please try again.");
          return;
        }
        if (run.kind === "clarify") {
          const section = result.sections.find((s) => s.id === run.sectionId);
          if (section?.clarificationQuestions?.length) setClarifySectionId(run.sectionId);
          else setSectionMessage(run.sectionId, "No questions came back for this section. Please try again.");
        }
      })
      .catch((e: unknown) => {
        if (!cancelled) setError(e instanceof Error ? e.message : "Could not load the draft.");
      });
    return () => {
      cancelled = true;
    };
  }, [projectId, code, reloadKey]);

  // While the agent is working, check again: every 3 s for a section run started here,
  // every 10 s for a full generation (paused while editing, so nothing moves under the cursor).
  useEffect(() => {
    if (!draft) return;
    const isRunning = pending !== null || draft.latestRun?.status === "running" || draft.status === "Generating";
    if (!isRunning || (isEditing && pending === null)) return;
    const timer = setTimeout(() => setReloadKey((k) => k + 1), pending ? SECTION_POLL_MS : GENERATION_POLL_MS);
    return () => clearTimeout(timer);
  }, [draft, isEditing, pending]);

  function retry() {
    setError(null);
    setDraft(null);
    setReloadKey((k) => k + 1);
  }

  async function handleSaveSection(sectionId: string, bullets: string[]) {
    const updated = await saveDraftSection(projectId, code, sectionId, bullets);
    setDraft((current) =>
      current ? { ...current, sections: current.sections.map((s) => (s.id === sectionId ? updated : s)) } : current,
    );
  }

  /** Regenerate: rewrite the section with the agent (answers come from Clarify). */
  async function startRegenerate(sectionId: string, answers: ClarificationAnswer[] = []) {
    const runId = await regenerateDraftSection(projectId, code, sectionId, answers);
    setPendingRun({ runId, sectionId, kind: "regenerate" });
    setReloadKey((k) => k + 1);
  }

  async function handleRegenerate(sectionId: string) {
    setSectionMessage(sectionId, null);
    try {
      await startRegenerate(sectionId);
    } catch (e) {
      setSectionMessage(sectionId, e instanceof Error ? e.message : "Could not start regenerating.");
    }
  }

  /** Clarify: open the questions if the section has them, otherwise ask the agent for them first. */
  async function handleClarify(section: DraftSection) {
    setSectionMessage(section.id, null);
    if (section.clarificationQuestions?.length) {
      setClarifySectionId(section.id);
      return;
    }
    try {
      const runId = await requestSectionClarification(projectId, code, section.id);
      setPendingRun({ runId, sectionId: section.id, kind: "clarify" });
      setReloadKey((k) => k + 1);
    } catch (e) {
      setSectionMessage(section.id, e instanceof Error ? e.message : "Could not prepare questions.");
    }
  }

  /** Submit & Regenerate in the Clarify dialog. Errors stay in the dialog. */
  async function handleClarifySubmit(answers: ClarificationAnswer[]) {
    if (!clarifySectionId) return;
    await startRegenerate(clarifySectionId, answers);
    setClarifySectionId(null);
  }

  /** What the agent is doing for a section: from this page's run, or a run found on load. */
  function activityFor(sectionId: string): SectionActivity {
    if (pending?.sectionId === sectionId) return pending.kind;
    const run = draft?.latestRun;
    if (run?.status === "running" && run.section_key === sectionId) {
      if (run.run_type === "brd_regenerate") return "regenerate";
      if (run.run_type === "brd_clarify") return "clarify";
    }
    return null;
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
  const clarifySection = draft.sections.find((s) => s.id === clarifySectionId) ?? null;
  const isAgentBusy = pending !== null || draft.latestRun?.status === "running" || draft.status === "Generating";

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
                onRegenerate={() => void handleRegenerate(activeSection.id)}
                onClarify={() => void handleClarify(activeSection)}
                activity={activityFor(activeSection.id)}
                isAgentBusy={isAgentBusy}
                message={sectionMessages[activeSection.id] ?? null}
              />
            </article>
          </div>
        </div>

      <DraftExportBar isClientReady={draft.isClientReady} onExport={handleExport} />

      <ClarifyDialog
        section={clarifySection}
        onClose={() => setClarifySectionId(null)}
        onSubmit={handleClarifySubmit}
      />
    </div>
  );
}