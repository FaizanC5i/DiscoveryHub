/** Arrow icon from the design ("large" is the one inside the Sign In button). */
export function LandingArrow({ large = false }: { large?: boolean }) {
  return (
    // eslint-disable-next-line @next/next/no-img-element -- decorative SVG from the design
    <img
      className={large ? "dhl-arrow dhl-arrow--large" : "dhl-arrow"}
      src={`/landing/${large ? "arrow-19.svg" : "arrow-18.svg"}`}
      alt=""
      aria-hidden="true"
    />
  );
}
