import Image from "next/image";
import Link from "next/link";
import { APP_NAME, ROUTES } from "@/lib/constants";
import { cn } from "@/lib/cn";

interface LogoProps {
  /** "default" for light surfaces, "panel" for the dark brand panel. */
  tone?: "default" | "panel";
  href?: string;
}

/*
 * The C5i logo files live in public/brand/:
 *   c5i-logo.png        dark purple strokes, for light surfaces
 *   c5i-logo-light.png  white strokes, for dark surfaces (the purple squares are unchanged)
 * Both are transparent PNGs, cropped to the artwork (962 x 500).
 */
const LOGO_SOURCES = {
  default: "/brand/c5i-logo.png",
  panel: "/brand/c5i-logo-light.png",
} as const;

const LOGO_WIDTH = 962;
const LOGO_HEIGHT = 500;

/** C5i logo followed by the app name. Links to the given href (dashboard by default). */
export function Logo({ tone = "default", href = ROUTES.dashboard }: LogoProps) {
  const isPanel = tone === "panel";

  return (
    <Link href={href} className="inline-flex items-center gap-3 rounded-control">
      <Image
        src={isPanel ? LOGO_SOURCES.panel : LOGO_SOURCES.default}
        alt="C5i"
        width={LOGO_WIDTH}
        height={LOGO_HEIGHT}
        className="h-10 w-auto"
        priority
      />
      <span aria-hidden className={cn("h-6 w-px", isPanel ? "bg-panel-border" : "bg-border")} />
      <span className={cn("text-title-small font-bold", isPanel ? "text-panel-fg" : "text-fg")}>
        {APP_NAME}
      </span>
    </Link>
  );
}
