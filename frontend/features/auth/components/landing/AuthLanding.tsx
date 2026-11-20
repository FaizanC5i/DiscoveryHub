"use client";

import "@fontsource-variable/manrope";
import "@fontsource-variable/dm-sans";
import "../../styles/auth-landing.css";
import { useEffect, useRef, useState } from "react";
import { LandingHero } from "./LandingHero";
import { LandingSignInPanel } from "./LandingSignInPanel";
import { WorkspaceIllustration } from "./WorkspaceIllustration";

/**
 * Landing page + sign-in (the /login route). The hero shows first; "Enter Discovery Hub"
 * slides in the sign-in panel and the illustration moves left. Close (or the logo, or
 * Escape) goes back to the hero. The hidden scene is made inert so keyboard and screen
 * readers only reach the visible one.
 */
export function AuthLanding() {
  const [isSignIn, setIsSignIn] = useState(false);
  const enterButtonRef = useRef<HTMLButtonElement>(null);
  const emailInputRef = useRef<HTMLInputElement>(null);
  const hasMoved = useRef(false);

  // Move keyboard focus with the scene change (not on first load).
  useEffect(() => {
    if (!hasMoved.current) {
      hasMoved.current = true;
      return;
    }
    const target = isSignIn ? emailInputRef.current : enterButtonRef.current;
    const timer = setTimeout(() => target?.focus(), 250);
    return () => clearTimeout(timer);
  }, [isSignIn]);

  // Escape closes the sign-in panel.
  useEffect(() => {
    if (!isSignIn) return;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") setIsSignIn(false);
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [isSignIn]);

  return (
    <main className={`dhl-app-shell ${isSignIn ? "dhl-app-shell--signin" : ""}`}>
      <div className="dhl-background-shape dhl-background-shape--top" aria-hidden="true" />
      <div className="dhl-background-shape dhl-background-shape--bottom" aria-hidden="true" />
      <div className="dhl-background-glow" aria-hidden="true" />
      <div className="dhl-background-grid" aria-hidden="true" />

      <div className={`dhl-scene dhl-scene--hero ${isSignIn ? "dhl-scene--hidden" : ""}`} inert={isSignIn}>
        <LandingHero onEnter={() => setIsSignIn(true)} enterButtonRef={enterButtonRef} />
      </div>

      <WorkspaceIllustration signIn={isSignIn} />

      <div className={`dhl-scene dhl-scene--signin ${isSignIn ? "dhl-scene--visible" : ""}`} inert={!isSignIn}>
        <LandingSignInPanel onBack={() => setIsSignIn(false)} emailInputRef={emailInputRef} />
      </div>
    </main>
  );
}
