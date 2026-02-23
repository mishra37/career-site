"use client";

import { ReactNode } from "react";
import { ResumeModalProvider } from "@/contexts/ResumeModalContext";
import ResumeMatchModal from "@/components/ResumeMatchModal";

export default function Providers({ children }: { children: ReactNode }) {
  return (
    <ResumeModalProvider>
      {children}
      <ResumeMatchModal />
    </ResumeModalProvider>
  );
}
