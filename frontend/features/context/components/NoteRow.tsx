"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { NotesIcon } from "@/components/icons";
import { Button } from "@/components/ui/Button";
import { reprocessSource } from "../services/contextService";
import type { Source } from "../types/source";
import { isWorking } from "../utils/sourceFilters";
import { ShimmerBar } from "./ProcessingIndicator";
import { SourceStatusBadge } from "./SourceStatusBadge";

interface NoteRowProps {
  projectId: number;
  source: Source;
  onOpen: (sourceId: number) => void;
}

/** A manual note in the Project sources list. Opening it shows the full text. */
export function NoteRow({ projectId, source, onOpen }: NoteRowProps) {
  const router = useRouter();
  const [isRetrying, setIsRetrying] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleRetry() {
    setIsRetrying(true);
    setError(null);
    try {
      await reprocessSource(projectId, source.id);
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong. Please try again.");
    } finally {
      setIsRetrying(false);
    }
  }

  return (
    <li className="flex flex-col gap-2 py-4">
      <div className="flex items-start justify-between gap-3">
        <button
          type="button"
          onClick={() => onOpen(source.id)}
          className="flex min-w-0 items-start gap-3 rounded-control text-left hover:opacity-80 focus-visible:outline-2 focus-visible:outline-border-brand-strong"
        >
          <NotesIcon className="mt-0.5 size-4 shrink-0 text-icon" />
          <span className="flex min-w-0 flex-col gap-1">
            <span className="truncate text-body-medium font-semibold text-fg">{source.title}</span>
            <span className="text-caption text-fg-muted">Manual note</span>
          </span>
        </button>
        <SourceStatusBadge
          status={source.processing_status}
          sourceType="MANUAL_NOTE"
          mappingPending={source.mapping_pending}
        />
      </div>

      {isWorking(source) ? <ShimmerBar /> : null}

      {source.failure_reason ? <p className="text-caption text-error">{source.failure_reason}</p> : null}
      {error ? (
        <p role="alert" className="text-caption text-error">
          {error}
        </p>
      ) : null}

      {source.processing_status === "failed" ? (
        <div>
          <Button size="sm" variant="outline" loading={isRetrying} disabled={isRetrying} onClick={handleRetry}>
            Retry
          </Button>
        </div>
      ) : null}
    </li>
  );
}
