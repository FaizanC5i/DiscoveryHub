import type { Ref } from "react";
import { LandingArrow } from "./LandingArrow";
import { LandingBrand } from "./LandingBrand";

interface LandingHeroProps {
  onEnter: () => void;
  enterButtonRef?: Ref<HTMLButtonElement>;
}

/** Left side of the landing page: headline, description and "Enter Discovery Hub". */
export function LandingHero({ onEnter, enterButtonRef }: LandingHeroProps) {
  return (
    <section className="dhl-hero" aria-label="Discovery Hub introduction">
      <header className="dhl-hero__header">
        <LandingBrand />
      </header>

      <div className="dhl-hero__copy">
        <h1>
          Know what to build
          <br />
          <strong>Before you build it</strong>
        </h1>
        <p>
          An AI-assisted workspace that guides you from first meeting to signed-off BRD. Turn client
          conversations, documents, and research into clear requirements with no gaps.
        </p>
        <button ref={enterButtonRef} className="dhl-primary-cta" type="button" onClick={onEnter}>
          <span>Enter Discovery Hub</span>
          <span className="dhl-primary-cta__arrow">
            <LandingArrow />
          </span>
        </button>
      </div>
    </section>
  );
}
