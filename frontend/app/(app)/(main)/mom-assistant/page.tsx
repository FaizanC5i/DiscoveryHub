import type { Metadata } from "next";
import { MomAssistantView } from "@/features/mom-assistant/components/MomAssistantView";

export const metadata: Metadata = {
  title: "MOM Assistant",
};

export default function MomAssistantPage() {
  return <MomAssistantView />;
}
