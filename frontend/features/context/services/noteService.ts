/**
 * Note storage behind one interface. Components call noteService and never know
 * whether notes come from memory or from the API.
 */
import { apiRequest } from "@/lib/api/client";
import { API_PATHS } from "@/lib/api/endpoints";
import type { NoteInput, ProjectNote } from "../types/note";

export interface NoteService {
  list(projectId: number): Promise<ProjectNote[]>;
  create(projectId: number, input: NoteInput): Promise<ProjectNote>;
  remove(projectId: number, noteId: string): Promise<void>;
}

/** In-memory store for local development. Notes are lost on a full page reload. */
const mockStore = new Map<number, ProjectNote[]>();

const mockNoteService: NoteService = {
  async list(projectId) {
    return [...(mockStore.get(projectId) ?? [])];
  },
  async create(projectId, input) {
    const note: ProjectNote = {
      id: crypto.randomUUID(),
      title: input.title,
      body: input.body,
      created_at: new Date().toISOString(),
    };
    mockStore.set(projectId, [note, ...(mockStore.get(projectId) ?? [])]);
    return note;
  },
  async remove(projectId, noteId) {
    mockStore.set(
      projectId,
      (mockStore.get(projectId) ?? []).filter((note) => note.id !== noteId),
    );
  },
};

/** Calls the backend. Used once the notes routes exist. */
const apiNoteService: NoteService = {
  list: (projectId) => apiRequest<ProjectNote[]>(API_PATHS.notes.list(projectId)),
  create: (projectId, input) =>
    apiRequest<ProjectNote>(API_PATHS.notes.list(projectId), {
      method: "POST",
      body: JSON.stringify(input),
    }),
  remove: (projectId, noteId) =>
    apiRequest<void>(API_PATHS.notes.detail(projectId, noteId), { method: "DELETE" }),
};

const USE_MOCK_NOTES = process.env.NEXT_PUBLIC_USE_MOCK_NOTES !== "false";

export const noteService: NoteService = USE_MOCK_NOTES ? mockNoteService : apiNoteService;