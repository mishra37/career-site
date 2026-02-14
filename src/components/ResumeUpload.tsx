"use client";

import { useState, useCallback, useRef } from "react";
import { Upload, FileText, X, Loader2, Sparkles } from "lucide-react";
import { MatchResult } from "@/lib/types";

interface ResumeUploadProps {
  onMatchResults: (results: MatchResult[] | null) => void;
  isMatched: boolean;
}

export default function ResumeUpload({ onMatchResults, isMatched }: ResumeUploadProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [fileName, setFileName] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback(
    async (file: File) => {
      setError(null);
      setFileName(file.name);
      setIsUploading(true);

      try {
        const formData = new FormData();
        formData.append("resume", file);

        const response = await fetch("/api/match", {
          method: "POST",
          body: formData,
        });

        const data = await response.json();

        if (!response.ok) {
          throw new Error(data.error || "Failed to process resume");
        }

        onMatchResults(data.matches);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Something went wrong");
        setFileName(null);
        onMatchResults(null);
      } finally {
        setIsUploading(false);
      }
    },
    [onMatchResults]
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

  const handleClear = () => {
    setFileName(null);
    setError(null);
    onMatchResults(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  if (isMatched && fileName) {
    return (
      <div className="bg-primary-light border border-primary/20 rounded-2xl p-4 flex items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center">
            <Sparkles className="w-5 h-5 text-primary" />
          </div>
          <div>
            <p className="text-sm font-semibold text-foreground">
              Jobs personalized for you
            </p>
            <p className="text-xs text-muted">{fileName}</p>
          </div>
        </div>
        <button
          onClick={handleClear}
          className="text-muted hover:text-foreground transition-colors p-1.5 rounded-lg hover:bg-foreground/5"
          title="Clear and show all jobs"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-3">
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
              ? "border-primary bg-primary-light scale-[1.02]"
              : "border-border hover:border-primary/50 hover:bg-primary-light/50"
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
                Matching your profile against open positions
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
                {fileName || "Upload your resume"}
              </p>
              <p className="text-xs text-muted mt-1">
                Drop a PDF or TXT file here, or click to browse
              </p>
            </div>
          </div>
        )}
      </div>

      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-3 text-sm text-red-600 dark:text-red-400">
          {error}
        </div>
      )}
    </div>
  );
}
