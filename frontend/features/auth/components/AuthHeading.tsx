interface AuthHeadingProps {
  eyebrow: string;
  title: string;
  description: string;
}

export function AuthHeading({ eyebrow, title, description }: AuthHeadingProps) {
  return (
    <header className="flex flex-col gap-3">
      <p className="text-caption font-semibold uppercase tracking-wider text-fg-muted">{eyebrow}</p>
      <h1 className="text-heading-5 font-medium text-fg">{title}</h1>
      <p className="text-body-large text-fg-muted">{description}</p>
    </header>
  );
}
