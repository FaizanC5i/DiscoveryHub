import Link from "next/link";

interface AuthFooterPromptProps {
  prompt: string;
  linkLabel: string;
  href: string;
}

export function AuthFooterPrompt({ prompt, linkLabel, href }: AuthFooterPromptProps) {
  return (
    <p className="text-center text-body-medium text-fg-muted">
      {prompt}{" "}
      <Link href={href} className="font-semibold text-fg-brand hover:text-fg-brand-strong">
        {linkLabel}
      </Link>
    </p>
  );
}
