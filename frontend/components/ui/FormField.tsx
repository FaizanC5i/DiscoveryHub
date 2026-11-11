import { useId, type ReactNode } from "react";

export interface FormControlProps {
  id: string;
  "aria-describedby"?: string;
  invalid: boolean;
}

interface FormFieldProps {
  label: string;
  error?: string;
  hint?: string;
  labelAction?: ReactNode;
  children: (controlProps: FormControlProps) => ReactNode;
}

/**
 * Label, control and message wrapper. The control is supplied through a render
 * function so the field can pass its id and aria attributes to it.
 */
export function FormField({ label, error, hint, labelAction, children }: FormFieldProps) {
  const id = useId();
  const messageId = `${id}-message`;
  const message = error ?? hint;

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center justify-between gap-4">
        <label htmlFor={id} className="text-body-medium font-semibold text-fg-secondary">
          {label}
        </label>
        {labelAction}
      </div>
      {children({
        id,
        "aria-describedby": message ? messageId : undefined,
        invalid: Boolean(error),
      })}
      {message ? (
        <p
          id={messageId}
          className={error ? "text-caption text-error" : "text-caption text-fg-muted"}
        >
          {message}
        </p>
      ) : null}
    </div>
  );
}
