"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Upload, FileText, X, Loader2, Sparkles, CheckCircle2 } from "lucide-react";
import { useResumeModal } from "@/contexts/ResumeModalContext";

export default function ResumeMatchModal() {
  const { isOpen, closeModal, setResults } = useResumeModal();
  const router = useRouter();
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [fileName, setFileName] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [matchCount, setMatchCount] = useState<number | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const overlayRef = useRef<HTMLDivElement>(null);

  // Reset state when modal opens
  useEffect(() => {
    if (isOpen) {
      setFileName(null);
      setError(null);
      setMatchCount(null);
      setIsUploading(false);
    }
  }, [isOpen]);

  // Prevent body scroll when modal is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [isOpen]);

  const handleFile = useCallback(
    async (file: File) => {
      setError(null);
      setFileName(file.name);
      setIsUploading(true);
      setMatchCount(null);

      try {
        const formData = new FormData();
        formData.append("resume", file);

        const response = await fetch("/api/match", {
          method: "POST",
          body: formData,
        });

        if (!response.ok) {
          let message = "Failed to process resume";
          try {
            const errData = await response.json();
            message = errData.detail || errData.error || message;
          } catch {}
          throw new Error(message);
        }

        const data = await response.json();

        setResults(data.matches, data.extractedKeywords);
        setMatchCount(data.matches?.length || 0);

        // Brief delay to show success, then navigate
        setTimeout(() => {
          closeModal();
          router.push("/jobs");
        }, 1500);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Something went wrong");
        setFileName(null);
      } finally {
        setIsUploading(false);
      }
    },
    [setResults, closeModal, router]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        ref={overlayRef}
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={() => {
          if (!isUploading) closeModal();
        }}
      />

      {/* Modal */}
      <div className="relative bg-background border border-border rounded-2xl shadow-2xl w-full max-w-md animate-fade-in-up">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-border">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-primary/10 flex items-center justify-center">
              <Sparkles className="w-4 h-4 text-primary" />
            </div>
            <h2 className="text-lg font-semibold text-foreground">Match My Resume</h2>
          </div>
          {!isUploading && (
            <button
              onClick={closeModal}
              className="text-muted hover:text-foreground p-1.5 rounded-lg hover:bg-foreground/5 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          )}
        </div>

        {/* Body */}
        <div className="p-5">
          {matchCount !== null ? (
            /* Success state */
            <div className="text-center py-6">
              <div className="w-14 h-14 rounded-full bg-success/10 flex items-center justify-center mx-auto mb-4">
                <CheckCircle2 className="w-7 h-7 text-success" />
              </div>
              <h3 className="text-lg font-semibold text-foreground mb-1">
                {matchCount} Jobs Matched!
              </h3>
              <p className="text-sm text-muted">
                Redirecting to your personalized results...
              </p>
            </div>
          ) : (
            <>
              <p className="text-sm text-muted mb-4">
                Upload your resume and we&apos;ll match you with the best open positions based on your skills and experience.
              </p>

              {/* Drop zone */}
              <div
                onDragOver={(e) => {
                  e.preventDefault();
                  setIsDragging(true);
                }}
                onDragLeave={() => setIsDragging(false)}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                className={`
                  relative border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer
                  transition-all duration-200 ease-out
                  ${
                    isDragging
                      ? "border-primary bg-primary/5 scale-[1.02]"
                      : "border-border hover:border-primary/50 hover:bg-primary/5"
                  }
                  ${isUploading ? "pointer-events-none opacity-70" : ""}
                `}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,.txt"
                  className="hidden"
                  onChange={(e) => {
                    const file = e.target.files?.[0];
                    if (file) handleFile(file);
                  }}
                />

                {isUploading ? (
                  <div className="flex flex-col items-center gap-3">
                    <Loader2 className="w-8 h-8 text-primary animate-spin" />
                    <div>
                      <p className="text-sm font-medium text-foreground">
                        Analyzing your resume...
                      </p>
                      <p className="text-xs text-muted mt-1">
                        Matching against open positions
                      </p>
                    </div>
                  </div>
                ) : (
                  <div className="flex flex-col items-center gap-3">
                    <div className="w-12 h-12 rounded-2xl bg-primary/10 flex items-center justify-center">
                      {fileName ? (
                        <FileText className="w-6 h-6 text-primary" />
                      ) : (
                        <Upload className="w-6 h-6 text-primary" />
                      )}
                    </div>
                    <div>
                      <p className="text-sm font-medium text-foreground">
                        {fileName || "Drop your resume here"}
                      </p>
                      <p className="text-xs text-muted mt-1">
                        PDF or TXT file, up to 10MB
                      </p>
                    </div>
                  </div>
                )}
              </div>

              {error && (
                <div className="mt-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-3 text-sm text-red-600 dark:text-red-400">
                  {error}
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
