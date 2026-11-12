"use client";

import { useCallback, useEffect, useState } from "react";
import { noteService } from "../services/noteService";
import type { NoteInput, ProjectNote } from "../types/note";

export type NotesStatus = "loading" | "ready" | "error";

/** Loads a project's notes and provides add and remove actions. */
export function useProjectNotes(projectId: number) {
  const [notes, setNotes] = useState<ProjectNote[]>([]);
  const [status, setStatus] = useState<NotesStatus>("loading");

  useEffect(() => {
    let active = true;
    noteService
      .list(projectId)
      .then((items) => {
        if (active) {
          setNotes(items);
          setStatus("ready");
        }
      })
      .catch(() => {
        if (active) setStatus("error");
      });
    return () => {
      active = false;
    };
  }, [projectId]);

  const addNote = useCallback(
    async (input: NoteInput): Promise<void> => {
      const created = await noteService.create(projectId, input);
      setNotes((previous) => [created, ...previous]);
    },
    [projectId],
  );

  const removeNote = useCallback(
    async (noteId: string): Promise<void> => {
      await noteService.remove(projectId, noteId);
      setNotes((previous) => previous.filter((note) => note.id !== noteId));
    },
    [projectId],
  );

  return { notes, status, addNote, removeNote };
}