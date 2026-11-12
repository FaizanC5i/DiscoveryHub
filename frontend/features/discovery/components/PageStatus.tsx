import { buttonClass } from "../utils/class-names";

const wrapperClass =
  "flex min-h-dvh flex-col items-center justify-center gap-(--space-4) bg-(--color-bg-default-secondary) p-(--space-7) text-center";

/** Full-page loading message while data is fetched. */
export function PageLoading({ label }: { label: string }) {
  return (
    <div role="status" aria-live="polite" className={wrapperClass}>
      <span
        aria-hidden="true"
        className="size-(--space-10) animate-spin rounded-full border-4 border-(--color-bg-default-disabled) border-t-(--color-primary-default)"
      />
      <p className="m-0 text-(length:--font-size-body-large) leading-(--line-height-body-large) text-(--color-text-default-subtle)">
        {label}
      </p>
    </div>
  );
}

/** Full-page error message with a retry button. */
export function PageError({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div role="alert" className={wrapperClass}>
      <p className="m-0 text-(length:--font-size-title-medium) leading-(--line-height-title-medium) font-semibold text-(--color-text-default-primary)">
        Something went wrong
      </p>
      <p className="m-0 max-w-[60ch] text-(length:--font-size-body-medium) leading-(--line-height-body-medium) text-(--color-text-default-subtle)">
        {message}
      </p>
      <button type="button" onClick={onRetry} className={buttonClass.primary}>
        Try again
      </button>
    </div>
  );
}