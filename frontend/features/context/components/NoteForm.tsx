"use client";

import { Alert } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";
import { FormField } from "@/components/ui/FormField";
import { Input } from "@/components/ui/Input";
import { Textarea } from "@/components/ui/Textarea";
import { useForm } from "@/hooks/useForm";
import type { NoteFormValues, NoteInput } from "../types/note";
import { NOTE_BODY_MAX_LENGTH, validateNoteForm } from "../utils/noteValidation";

interface NoteFormProps {
  initialValues: NoteFormValues;
  submitLabel: string;
  onSubmit: (input: NoteInput) => Promise<void>;
  onCancel: () => void;
}

/** Title and text fields shared by Add Note and note editing. Both fields are required. */
export function NoteForm({ initialValues, submitLabel, onSubmit, onCancel }: NoteFormProps) {
  const { values, errors, handleChange, handleBlur, handleSubmit, isSubmitting, submitError } =
    useForm<NoteFormValues>({
      initialValues,
      validate: validateNoteForm,
      onSubmit: async (submitted) => {
        await onSubmit({ title: submitted.title.trim(), body: submitted.body.trim() });
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
        <Button variant="outline" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit" loading={isSubmitting}>
          {submitLabel}
        </Button>
      </div>
    </form>
  );
}
