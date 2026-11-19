import Link from "next/link";
import { ArrowRightIcon } from "@/components/icons";
import { buttonStyles } from "@/components/ui/Button";

interface ReviewLinkProps {
  href: string;
}

export function ReviewLink({ href }: ReviewLinkProps) {
  return (
    <Link href={href} className={buttonStyles({ variant: "link" })}>
      Review
      <ArrowRightIcon className="size-4" />
    </Link>
  );
}