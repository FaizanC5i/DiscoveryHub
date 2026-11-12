"use client";

import { useState, type ChangeEvent, type FocusEvent, type FormEvent } from "react";

/** Controls that feed the form: single-line inputs and multi-line textareas. */
type FormControl = HTMLInputElement | HTMLTextAreaElement;

export type FormErrors<T> = Partial<Record<keyof T, string>>;

interface UseFormOptions<T extends Record<string, string>> {
  initialValues: T;
  validate: (values: T) => FormErrors<T>;
  onSubmit: (values: T) => Promise<void>;
}

/**
 * Generic form state for text inputs.
 * Errors appear for a field once it has been blurred or the form was submitted.
 */
export function useForm<T extends Record<string, string>>({
  initialValues,
  validate,
  onSubmit,
}: UseFormOptions<T>) {
  const [values, setValues] = useState<T>(initialValues);
  const [errors, setErrors] = useState<FormErrors<T>>({});
  const [touched, setTouched] = useState<Partial<Record<keyof T, boolean>>>({});
  const [submitAttempted, setSubmitAttempted] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  function handleChange(event: ChangeEvent<FormControl>) {
    const key = event.target.name as keyof T;
    const nextValues = { ...values, [key]: event.target.value };
    setValues(nextValues);
    setSubmitError(null);
    if (touched[key] || submitAttempted) {
      setErrors(validate(nextValues));
    }
  }

  function handleBlur(event: FocusEvent<FormControl>) {
    const key = event.target.name as keyof T;
    setTouched((previous) => ({ ...previous, [key]: true }));
    setErrors(validate(values));
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitAttempted(true);

    const validationErrors = validate(values);
    setErrors(validationErrors);
    if (Object.keys(validationErrors).length > 0) {
      return;
    }

    setIsSubmitting(true);
    setSubmitError(null);
    try {
      await onSubmit(values);
    } catch (error) {
      setSubmitError(error instanceof Error ? error.message : "Something went wrong. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  }

  const visibleErrors: FormErrors<T> = {};
  for (const key of Object.keys(errors) as Array<keyof T>) {
    if (touched[key] || submitAttempted) {
      visibleErrors[key] = errors[key];
    }
  }

  return {
    values,
    errors: visibleErrors,
    handleChange,
    handleBlur,
    handleSubmit,
    isSubmitting,
    submitError,
  };
}
