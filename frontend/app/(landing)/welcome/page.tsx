import type { Metadata } from "next";
import { AuthLanding } from "@/features/auth/components/landing/AuthLanding";

export const metadata: Metadata = {
  title: "Welcome",
};

/**
 * /welcome: new landing hero + sign-in panel design.
 * The existing /login page is unchanged. This lives in its own (landing) group so it does
 * not get the two-column (auth) layout.
 */
export default function WelcomePage() {
  return <AuthLanding />;
}
