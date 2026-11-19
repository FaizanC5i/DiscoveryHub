interface AuthDividerProps {
  label: string;
}

export function AuthDivider({ label }: AuthDividerProps) {
  return (
    <div className="flex items-center gap-4" role="separator">
      <span className="h-px flex-1 bg-border-subtle" />
      <span className="text-caption font-medium uppercase tracking-wider text-fg-muted">{label}</span>
      <span className="h-px flex-1 bg-border-subtle" />
    </div>
  );
}
