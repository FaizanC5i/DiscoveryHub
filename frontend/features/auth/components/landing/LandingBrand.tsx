const LOGO = (name: string) => `/landing/${name}`;

interface LandingBrandProps {
  /** Smaller version used inside the sign-in panel. */
  compact?: boolean;
}

/** C5i logo + "Discovery Hub powered by Agent5i", as in the design. */
export function LandingBrand({ compact = false }: LandingBrandProps) {
  return (
    <span className={`dhl-brand ${compact ? "dhl-brand--compact" : ""}`}>
      <span className="dhl-brand__logo" aria-hidden="true">
        {/* eslint-disable-next-line @next/next/no-img-element -- small decorative SVGs from the design */}
        <img className="dhl-brand__mark" src={LOGO(compact ? "logo-mark-small.svg" : "logo-mark.svg")} alt="" />
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img className="dhl-brand__word" src={LOGO(compact ? "logo-word-small.svg" : "logo-word.svg")} alt="" />
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img className="dhl-brand__tag" src={LOGO(compact ? "logo-tag-small.svg" : "logo-tag.svg")} alt="" />
      </span>
      <span className="dhl-brand__rule" />
      <span className="dhl-brand__name">
        Discovery Hub <span>powered by Agent5i</span>
      </span>
    </span>
  );
}
