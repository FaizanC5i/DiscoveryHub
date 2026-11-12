"use client";

import { ArrowRightIcon } from "@/components/icons";
import { Alert } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";
import { FormField } from "@/components/ui/FormField";
import { Input } from "@/components/ui/Input";
import { Textarea } from "@/components/ui/Textarea";
import { useForm } from "@/hooks/useForm";
import type { ProjectInput } from "@/types/project";
import type { ProjectFormValues } from "../types/projectForm";
import { toProjectInput } from "../utils/projectInput";
import { PROJECT_DESCRIPTION_MAX_LENGTH, validateProjectForm } from "../utils/validation";

interface ProjectFormProps {
  initialValues: ProjectFormValues;
  submitLabel: string;
  /** Receives the API-ready values. Throw an error to show it in the form's alert. */
  onSubmit: (input: ProjectInput) => Promise<void>;
  onCancel: () => void;
}

/**
 * The fields for creating or editing a project. It knows nothing about where the
 * data goes: the parent passes onSubmit, so create and edit share this one form.
 *
 * Analogy: a paper intake form. The form does not decide where the file is filed.
 * It only checks that each box is filled in correctly before handing it over.
 */
export function ProjectForm({ initialValues, submitLabel, onSubmit, onCancel }: ProjectFormProps) {
  const { values, errors, handleChange, handleBlur, handleSubmit, isSubmitting, submitError } =
    useForm<ProjectFormValues>({
      initialValues,
      validate: validateProjectForm,
      onSubmit: (submitted) => onSubmit(toProjectInput(submitted)),
    });

  const descriptionCount = values.description.length.toLocaleString("en-US");
  const descriptionMax = PROJECT_DESCRIPTION_MAX_LENGTH.toLocaleString("en-US");

  return (
    <form method="post" noValidate onSubmit={handleSubmit} className="flex flex-col gap-6">
      {submitError ? <Alert>{submitError}</Alert> : null}

      <FormField label="Project name" required error={errors.name}>
        {(controlProps) => (
          <Input
            {...controlProps}
            type="text"
            name="name"
            autoComplete="off"
            placeholder="For example, Atlas Service Hub"
            value={values.name}
            onChange={handleChange}
            onBlur={handleBlur}
          />
        )}
      </FormField>

      <FormField
        label="Project description"
        required
        error={errors.description}
        hint={`Only what you write here is used as the description. ${descriptionCount} / ${descriptionMax}`}
      >
        {(controlProps) => (
          <Textarea
            {...controlProps}
            name="description"
            placeholder="What are you building, for whom, and why?"
            value={values.description}
            onChange={handleChange}
            onBlur={handleBlur}
          />
        )}
      </FormField>

      <div className="grid gap-6 sm:grid-cols-2">
        <FormField label="Start date" error={errors.startDate}>
          {(controlProps) => (
            <Input
              {...controlProps}
              type="date"
              name="startDate"
              value={values.startDate}
              onChange={handleChange}
              onBlur={handleBlur}
            />
          )}
        </FormField>

        <FormField label="End date" error={errors.endDate}>
          {(controlProps) => (
            <Input
              {...controlProps}
              type="date"
              name="endDate"
              value={values.endDate}
              onChange={handleChange}
              onBlur={handleBlur}
            />
          )}
        </FormField>
      </div>

      <div className="flex flex-col-reverse gap-3 border-t border-border-subtle pt-6 sm:flex-row sm:justify-end">
        <Button variant="outline" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit" loading={isSubmitting}>
          {submitLabel}
          <ArrowRightIcon className="size-5" />
        </Button>
      </div>
    </form>
  );
}
