import type { Metadata } from "next";
import { AuthLanding } from "@/features/auth/components/landing/AuthLanding";

export const metadata: Metadata = {
  title: "Sign in",
};

export default function LoginPage() {
  return <AuthLanding initialMode="signin" />;
}
