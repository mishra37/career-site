"use client";

import { createContext, useContext, useState, useCallback, ReactNode } from "react";
import { MatchResult, ExtractedKeywords } from "@/lib/types";

interface ResumeModalContextType {
  isOpen: boolean;
  openModal: () => void;
  closeModal: () => void;
  matchResults: MatchResult[] | null;
  extractedKeywords: ExtractedKeywords | null;
  setResults: (results: MatchResult[] | null, keywords: ExtractedKeywords | null) => void;
  clearResults: () => void;
}

const ResumeModalContext = createContext<ResumeModalContextType | null>(null);

export function ResumeModalProvider({ children }: { children: ReactNode }) {
  const [isOpen, setIsOpen] = useState(false);
  const [matchResults, setMatchResults] = useState<MatchResult[] | null>(null);
  const [extractedKeywords, setExtractedKeywords] = useState<ExtractedKeywords | null>(null);

  const openModal = useCallback(() => setIsOpen(true), []);
  const closeModal = useCallback(() => setIsOpen(false), []);

  const setResults = useCallback((results: MatchResult[] | null, keywords: ExtractedKeywords | null) => {
    setMatchResults(results);
    setExtractedKeywords(keywords);
  }, []);

  const clearResults = useCallback(() => {
    setMatchResults(null);
    setExtractedKeywords(null);
  }, []);

  return (
    <ResumeModalContext.Provider
      value={{ isOpen, openModal, closeModal, matchResults, extractedKeywords, setResults, clearResults }}
    >
      {children}
    </ResumeModalContext.Provider>
  );
}

export function useResumeModal() {
  const context = useContext(ResumeModalContext);
  if (!context) {
    throw new Error("useResumeModal must be used within ResumeModalProvider");
  }
  return context;
}
