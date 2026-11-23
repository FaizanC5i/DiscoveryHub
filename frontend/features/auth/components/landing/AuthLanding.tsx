"use client";

import "@fontsource-variable/manrope";
import "@fontsource-variable/dm-sans";
import "../../styles/auth-landing.css";
import { useEffect, useRef, useState } from "react";
import { LandingHero } from "./LandingHero";
import { LandingSignInPanel } from "./LandingSignInPanel";
import { LandingSignUpPanel } from "./LandingSignUpPanel";
import { WorkspaceIllustration } from "./WorkspaceIllustration";

export type LandingMode = "hero" | "signin" | "signup";

interface AuthLandingProps {
  /** Which view opens first: the hero (/welcome), sign in (/login) or sign up (/signup). */
  initialMode?: LandingMode;
  /** Pre-fills the sign-up email, for example after "no account" on the sign-in panel. */
  initialEmail?: string;
}

/**
 * Landing page with sign in and sign up. The hero shows first; "Enter Discovery Hub" slides in
 * the panel and the illustration moves left. Sign in and sign up switch in the same panel.
 * Close (or the logo, or Escape) goes back to the hero. The hidden scene is made inert so keyboard
 * and screen readers only reach the visible one.
 */
export function AuthLanding({ initialMode = "hero", initialEmail = "" }: AuthLandingProps) {
  const [mode, setMode] = useState<LandingMode>(initialMode);
  const [signUpEmail, setSignUpEmail] = useState(initialEmail);
  const enterButtonRef = useRef<HTMLButtonElement>(null);
  const emailInputRef = useRef<HTMLInputElement>(null);
  const nameInputRef = useRef<HTMLInputElement>(null);
  const hasMoved = useRef(false);
  const isPanel = mode !== "hero";

  // Move keyboard focus with the scene change (not on first load).
  useEffect(() => {
    if (!hasMoved.current) {
      hasMoved.current = true;
      return;
    }
    const target =
      mode === "signin" ? emailInputRef.current : mode === "signup" ? nameInputRef.current : enterButtonRef.current;
    const timer = setTimeout(() => target?.focus(), 250);
    return () => clearTimeout(timer);
  }, [mode]);

  // Escape closes the panel.
  useEffect(() => {
    if (!isPanel) return;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") setMode("hero");
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [isPanel]);

  function openSignUp(email: string) {
    setSignUpEmail(email);
    setMode("signup");
  }

  return (
    <main className={`dhl-app-shell ${isPanel ? "dhl-app-shell--signin" : ""}`}>
      <div className="dhl-background-shape dhl-background-shape--top" aria-hidden="true" />
      <div className="dhl-background-shape dhl-background-shape--bottom" aria-hidden="true" />
      <div className="dhl-background-glow" aria-hidden="true" />
      <div className="dhl-background-grid" aria-hidden="true" />

      <div className={`dhl-scene dhl-scene--hero ${isPanel ? "dhl-scene--hidden" : ""}`} inert={isPanel}>
        <LandingHero onEnter={() => setMode("signin")} enterButtonRef={enterButtonRef} />
      </div>

      <WorkspaceIllustration signIn={isPanel} />

      <div className={`dhl-scene dhl-scene--signin ${isPanel ? "dhl-scene--visible" : ""}`} inert={!isPanel}>
        {mode === "signup" ? (
          <LandingSignUpPanel
            key={signUpEmail}
            onBack={() => setMode("hero")}
            onSwitchToSignIn={() => setMode("signin")}
            initialEmail={signUpEmail}
            nameInputRef={nameInputRef}
          />
        ) : (
          <LandingSignInPanel
            onBack={() => setMode("hero")}
            onSwitchToSignUp={openSignUp}
            emailInputRef={emailInputRef}
          />
        )}
      </div>
    </main>
  );
}
