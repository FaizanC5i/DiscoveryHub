import type { FormErrors } from "@/hooks/useForm";
import type { NoteFormValues } from "../types/note";

export const NOTE_TITLE_MAX_LENGTH = 255;
export const NOTE_BODY_MAX_LENGTH = 12000;

export function validateNoteForm(values: NoteFormValues): FormErrors<NoteFormValues> {
  const errors: FormErrors<NoteFormValues> = {};
  const title = values.title.trim();
  const body = values.body.trim();

  if (!title) {
    errors.title = "Give the note a title.";
  } else if (title.length > NOTE_TITLE_MAX_LENGTH) {
    errors.title = `Title must be ${NOTE_TITLE_MAX_LENGTH} characters or fewer.`;
  }

  if (!body) {
    errors.body = "Write something in the note.";
  } else if (body.length > NOTE_BODY_MAX_LENGTH) {
    errors.body = `Note must be ${NOTE_BODY_MAX_LENGTH.toLocaleString("en-US")} characters or fewer.`;
  }

  return errors;
}