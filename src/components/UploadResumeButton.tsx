"use client";

import { Upload } from "lucide-react";
import { useResumeModal } from "@/contexts/ResumeModalContext";

export default function UploadResumeButton() {
  const { openModal } = useResumeModal();

  return (
    <button
      onClick={openModal}
      className="inline-flex items-center gap-2 px-6 py-3 border border-border rounded-xl font-medium text-foreground hover:bg-foreground/5 transition-all"
    >
      <Upload className="w-4 h-4" />
      Upload Resume
    </button>
  );
}
