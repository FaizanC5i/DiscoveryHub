import { Spinner } from "@/components/ui/Spinner";

/** Centred spinner for a whole page while its data loads. Announced to screen readers. */
export function FullPageLoader({ label = "Loading" }: { label?: string }) {
  return (
    <div className="flex min-h-dvh items-center justify-center">
      <Spinner label={label} className="size-6 text-icon" />
    </div>
  );
}
