"use client";

import { Alert } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";
import { FormField } from "@/components/ui/FormField";
import { Input } from "@/components/ui/Input";
import { Modal } from "@/components/ui/Modal";
import { Textarea } from "@/components/ui/Textarea";
import { useForm } from "@/hooks/useForm";
import type { NoteFormValues, NoteInput } from "../types/note";
import { NOTE_BODY_MAX_LENGTH, validateNoteForm } from "../utils/noteValidation";

interface AddNoteDialogProps {
  open: boolean;
  onClose: () => void;
  onSave: (input: NoteInput) => Promise<void>;
}

export function AddNoteDialog({ open, onClose, onSave }: AddNoteDialogProps) {
  return (
    <Modal open={open} onClose={onClose} title="Add a note">
      <AddNoteForm onSave={onSave} onDone={onClose} />
    </Modal>
  );
}

const EMPTY_NOTE: NoteFormValues = { title: "", body: "" };

interface AddNoteFormProps {
  onSave: (input: NoteInput) => Promise<void>;
  onDone: () => void;
}

/** Mounts fresh each time the dialog opens, so no text is left over from the last note. */
function AddNoteForm({ onSave, onDone }: AddNoteFormProps) {
  const { values, errors, handleChange, handleBlur, handleSubmit, isSubmitting, submitError } =
    useForm<NoteFormValues>({
      initialValues: EMPTY_NOTE,
      validate: validateNoteForm,
      onSubmit: async (submitted) => {
        await onSave({ title: submitted.title.trim(), body: submitted.body.trim() });
        onDone();
      },
    });

  return (
    <form method="post" noValidate onSubmit={handleSubmit} className="flex flex-col gap-6">
      {submitError ? <Alert>{submitError}</Alert> : null}

      <FormField label="Title" required error={errors.title}>
        {(controlProps) => (
          <Input
            {...controlProps}
            type="text"
            name="title"
            autoComplete="off"
            placeholder="For example, Kick-off call notes"
            value={values.title}
            onChange={handleChange}
            onBlur={handleBlur}
          />
        )}
      </FormField>

      <FormField
        label="Note"
        required
        error={errors.body}
        hint={`${values.body.length.toLocaleString("en-US")} / ${NOTE_BODY_MAX_LENGTH.toLocaleString("en-US")}`}
      >
        {(controlProps) => (
          <Textarea
            {...controlProps}
            name="body"
            placeholder="What do you want to remember about this project?"
            value={values.body}
            onChange={handleChange}
            onBlur={handleBlur}
          />
        )}
      </FormField>

      <div className="flex flex-col-reverse gap-3 border-t border-border-subtle pt-6 sm:flex-row sm:justify-end">
        <Button variant="outline" onClick={onDone}>
          Cancel
        </Button>
        <Button type="submit" loading={isSubmitting}>
          Save note
        </Button>
      </div>
    </form>
  );
}