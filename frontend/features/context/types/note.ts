/** A note as the API will return it. Field names are snake_case to match the other API types. */
export interface ProjectNote {
  id: string;
  title: string;
  body: string;
  created_at: string;
}

export interface NoteInput {
  title: string;
  body: string;
}

export type NoteFormValues = {
  title: string;
  body: string;
};