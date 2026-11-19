"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Alert } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import { formatProjectTimestamp } from "@/features/project-overview/utils/formatProjectDate";
import { deleteSource, getNote, updateNote } from "../services/contextService";
import type { NoteDetail, NoteInput } from "../types/note";
import { NoteForm } from "./NoteForm";
import { SourceStatusBadge } from "./SourceStatusBadge";

interface NoteDetailDialogProps {
  projectId: number;
  sourceId: number;
  onClose: () => void;
}

/** The result of loading one note. It records which id it is for, so a stale result is ignored. */
type Loaded = { id: number; note: NoteDetail } | { id: number; failed: true };

type LoadState =
  | { status: "loading" }
  | { status: "error" }
  | { status: "ready"; note: NoteDetail };

/** Opens one manual note: its full text, its details, and edit and remove actions. */
export function NoteDetailDialog({ projectId, sourceId, onClose }: NoteDetailDialogProps) {
  const router = useRouter();
  const [currentId, setCurrentId] = useState(sourceId);
  const [loaded, setLoaded] = useState<Loaded | null>(null);
  const [mode, setMode] = useState<"view" | "edit" | "confirm-remove">("view");
  const [actionError, setActionError] = useState<string | null>(null);
  const [isRemoving, setIsRemoving] = useState(false);

  useEffect(() => {
    let active = true;
    getNote(projectId, currentId)
      .then((note) => {
        if (active) setLoaded({ id: currentId, note });
      })
      .catch(() => {
        if (active) setLoaded({ id: currentId, failed: true });
      });
    return () => {
      active = false;
    };
  }, [projectId, currentId]);

  const current = loaded?.id === currentId ? loaded : null;
  const load: LoadState = !current
    ? { status: "loading" }
    : "failed" in current
      ? { status: "error" }
      : { status: "ready", note: current.note };

  const title = load.status === "ready" ? load.note.title : "Manual note";

  async function handleSave(input: NoteInput) {
    const saved = await updateNote(projectId, currentId, input);
    // A text change replaces the note with a new source row, so the dialog follows the new id.
    setCurrentId(saved.id);
    setMode("view");
    router.refresh();
  }

  async function handleRemove() {
    setIsRemoving(true);
    setActionError(null);
    try {
      await deleteSource(projectId, currentId);
      router.refresh();
      onClose();
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Could not remove this note.");
      setIsRemoving(false);
    }
  }

  return (
    <Modal open onClose={onClose} title={title} dismissible={!isRemoving}>
      {load.status === "loading" ? <p className="text-body-small text-fg-muted">Loading note...</p> : null}
      {load.status === "error" ? (
        <Alert>This note could not be loaded. It may have been removed.</Alert>
      ) : null}

      {load.status === "ready" && mode === "edit" ? (
        <NoteForm
          initialValues={{ title: load.note.title, body: load.note.body }}
          submitLabel="Save changes"
          onSubmit={handleSave}
          onCancel={() => setMode("view")}
        />
      ) : null}

      {load.status === "ready" && mode !== "edit" ? (
        <NoteView note={load.note} />
      ) : null}

      {load.status === "ready" && mode === "view" ? (
        <div className="mt-6 flex flex-col-reverse gap-3 border-t border-border-subtle pt-6 sm:flex-row sm:justify-end">
          <Button variant="outline" onClick={() => setMode("confirm-remove")}>
            Remove
          </Button>
          <Button onClick={() => setMode("edit")}>Edit note</Button>
        </div>
      ) : null}

      {load.status === "ready" && mode === "confirm-remove" ? (
        <div className="mt-6 flex flex-col gap-4 border-t border-border-subtle pt-6">
          <p className="text-body-small text-fg">
            Remove this note? It will no longer be used as project context.
          </p>
          {actionError ? (
            <p role="alert" className="text-caption text-error">
              {actionError}
            </p>
          ) : null}
          <div className="flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
            <Button variant="outline" disabled={isRemoving} onClick={() => setMode("view")}>
              Cancel
            </Button>
            <Button loading={isRemoving} disabled={isRemoving} onClick={handleRemove}>
              Remove note
            </Button>
          </div>
        </div>
      ) : null}
    </Modal>
  );
}

function NoteView({ note }: { note: NoteDetail }) {
  return (
    <div className="flex flex-col gap-6">
      <dl className="grid grid-cols-2 gap-x-6 gap-y-3 text-body-small">
        <Field label="Created by" value={note.created_by_name} />
        <Field label="Created" value={formatProjectTimestamp(note.created_at)} />
        <Field
          label="Last updated"
          value={formatProjectTimestamp(note.updated_at ?? note.created_at)}
        />
        <div className="flex flex-col gap-1">
          <dt className="text-caption text-fg-muted">Processing</dt>
          <dd>
            <SourceStatusBadge status={note.processing_status} sourceType="MANUAL_NOTE" />
          </dd>
        </div>
        <Field label="Chunks" value={String(note.chunk_count)} />
      </dl>

      {note.failure_reason ? (
        <p role="alert" className="text-caption text-error">
          {note.failure_reason}
        </p>
      ) : null}

      <div className="max-h-[50vh] overflow-y-auto rounded-card bg-page p-4">
        <p className="whitespace-pre-wrap break-words text-body-small text-fg">{note.body}</p>
      </div>
    </div>
  );
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col gap-1">
      <dt className="text-caption text-fg-muted">{label}</dt>
      <dd className="text-fg">{value}</dd>
    </div>
  );
}
