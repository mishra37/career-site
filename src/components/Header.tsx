"use client";

import { Briefcase } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useResumeModal } from "@/contexts/ResumeModalContext";

export default function Header() {
  const pathname = usePathname();
  const { openModal } = useResumeModal();

  return (
    <header className="sticky top-0 z-50 bg-background/80 backdrop-blur-xl border-b border-border">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <Link href="/" className="flex items-center gap-2.5 group">
            <div className="w-9 h-9 rounded-xl bg-primary flex items-center justify-center shadow-lg shadow-primary/25 group-hover:shadow-primary/40 transition-shadow">
              <Briefcase className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-foreground tracking-tight leading-none">
                CareerMatch
              </h1>
              <p className="text-[10px] text-muted font-medium tracking-wider uppercase leading-none mt-0.5">
                by Decimal AI
              </p>
            </div>
          </Link>

          <nav className="flex items-center gap-1">
            <Link
              href="/"
              className={`text-sm px-3 py-2 rounded-lg transition-all font-medium ${
                pathname === "/"
                  ? "text-foreground bg-foreground/5"
                  : "text-muted hover:text-foreground hover:bg-foreground/5"
              }`}
            >
              Home
            </Link>
            <Link
              href="/jobs"
              className={`text-sm px-3 py-2 rounded-lg transition-all font-medium ${
                pathname?.startsWith("/jobs")
                  ? "text-foreground bg-foreground/5"
                  : "text-muted hover:text-foreground hover:bg-foreground/5"
              }`}
            >
              Browse Jobs
            </Link>
            <button
              onClick={openModal}
              className="text-sm bg-primary text-white px-4 py-2 rounded-xl hover:bg-primary-hover transition-all font-medium shadow-sm hover:shadow-md"
            >
              Match My Resume
            </button>
          </nav>
        </div>
      </div>
    </header>
  );
}
