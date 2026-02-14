"use client";

import { useState, useEffect, useCallback, useMemo } from "react";
import { Job, MatchResult, FilterState } from "@/lib/types";
import JobCard from "@/components/JobCard";
import JobCardSkeleton from "@/components/JobCardSkeleton";
import FilterBar from "@/components/FilterBar";
import ResumeUpload from "@/components/ResumeUpload";
import { Sparkles, TrendingUp, Users, Zap } from "lucide-react";

export default function HomePage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [matchResults, setMatchResults] = useState<MatchResult[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState<FilterState>({
    search: "",
    department: "",
    level: "",
    type: "",
    location: "",
    remote: null,
  });
  const [filterOptions, setFilterOptions] = useState({
    departments: [] as string[],
    levels: [] as string[],
    locations: [] as string[],
    types: [] as string[],
  });
  const [page, setPage] = useState(1);
  const [totalJobs, setTotalJobs] = useState(0);
  const [totalPages, setTotalPages] = useState(1);

  // Fetch jobs from API
  const fetchJobs = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.set("page", page.toString());
      params.set("pageSize", "12");
      if (filters.search) params.set("search", filters.search);
      if (filters.department) params.set("department", filters.department);
      if (filters.level) params.set("level", filters.level);
      if (filters.type) params.set("type", filters.type);
      if (filters.location) params.set("location", filters.location);
      if (filters.remote !== null) params.set("remote", filters.remote.toString());

      const res = await fetch(`/api/jobs?${params.toString()}`);
      const data = await res.json();

      setJobs(data.jobs);
      setTotalJobs(data.total);
      setTotalPages(data.totalPages);
      setFilterOptions(data.filters);
    } catch (error) {
      console.error("Failed to fetch jobs:", error);
    } finally {
      setLoading(false);
    }
  }, [page, filters]);

  useEffect(() => {
    if (!matchResults) {
      fetchJobs();
    }
  }, [fetchJobs, matchResults]);

  // Reset page when filters change
  useEffect(() => {
    setPage(1);
  }, [filters]);

  // Apply client-side filtering to match results
  const filteredMatches = useMemo(() => {
    if (!matchResults) return null;

    return matchResults.filter((m) => {
      const job = m.job;
      if (filters.search) {
        const s = filters.search.toLowerCase();
        const matches =
          job.title.toLowerCase().includes(s) ||
          job.description.toLowerCase().includes(s) ||
          job.skills.some((sk) => sk.toLowerCase().includes(s)) ||
          job.department.toLowerCase().includes(s);
        if (!matches) return false;
      }
      if (filters.department && job.department !== filters.department) return false;
      if (filters.level && job.level !== filters.level) return false;
      if (filters.type && job.type !== filters.type) return false;
      if (filters.location && job.location !== filters.location) return false;
      if (filters.remote !== null && job.remote !== filters.remote) return false;
      return true;
    });
  }, [matchResults, filters]);

  const displayJobs = matchResults
    ? filteredMatches || []
    : jobs.map((j) => ({ job: j, score: 0, reason: "" }));

  const handleMatchResults = (results: MatchResult[] | null) => {
    setMatchResults(results);
    if (results) {
      setFilters({ search: "", department: "", level: "", type: "", location: "", remote: null });
    }
  };

  return (
    <div>
      {/* Hero Section */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-accent/5" />
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-12 pb-8">
          <div className="max-w-2xl">
            <h1 className="text-3xl sm:text-4xl font-bold text-foreground tracking-tight">
              Find your next role,{" "}
              <span className="text-primary">powered by AI</span>
            </h1>
            <p className="mt-3 text-base text-muted max-w-lg">
              Upload your resume and our AI will match you with the most relevant
              positions. Or browse all open jobs below.
            </p>
          </div>

          {/* Stats */}
          <div className="flex flex-wrap gap-6 mt-6">
            {[
              { icon: Zap, label: "Open Positions", value: "50+" },
              { icon: TrendingUp, label: "AI-Matched", value: "Real-time" },
              { icon: Users, label: "Companies", value: "10+" },
              { icon: Sparkles, label: "Avg Match Time", value: "<3s" },
            ].map(({ icon: Icon, label, value }) => (
              <div key={label} className="flex items-center gap-2">
                <Icon className="w-4 h-4 text-primary" />
                <span className="text-sm font-semibold text-foreground">{value}</span>
                <span className="text-xs text-muted">{label}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Main Content */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-16">
        <div className="grid lg:grid-cols-[320px_1fr] gap-8">
          {/* Sidebar */}
          <div className="space-y-6" id="upload">
            <div>
              <h2 className="text-sm font-semibold text-foreground mb-3 flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-primary" />
                AI Resume Matching
              </h2>
              <ResumeUpload
                onMatchResults={handleMatchResults}
                isMatched={matchResults !== null}
              />
            </div>

            {/* Quick stats when personalized */}
            {matchResults && (
              <div className="bg-card-bg border border-border rounded-2xl p-4 animate-fade-in-up">
                <h3 className="text-sm font-semibold text-foreground mb-3">Match Summary</h3>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-muted">Total matches</span>
                    <span className="font-semibold text-foreground">{matchResults.length}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-muted">Strong matches (70%+)</span>
                    <span className="font-semibold text-success">
                      {matchResults.filter((m) => m.score >= 70).length}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-muted">Good matches (40-69%)</span>
                    <span className="font-semibold text-warning">
                      {matchResults.filter((m) => m.score >= 40 && m.score < 70).length}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-muted">Top match score</span>
                    <span className="font-semibold text-primary">
                      {matchResults.length > 0 ? `${matchResults[0].score}%` : "—"}
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Job listings */}
          <div className="space-y-4">
            <FilterBar
              filters={filters}
              onFilterChange={setFilters}
              filterOptions={filterOptions}
              totalJobs={matchResults ? (filteredMatches?.length || 0) : totalJobs}
              isPersonalized={matchResults !== null}
            />

            {loading && !matchResults ? (
              <div className="grid sm:grid-cols-2 gap-4">
                {Array.from({ length: 6 }).map((_, i) => (
                  <JobCardSkeleton key={i} />
                ))}
              </div>
            ) : displayJobs.length > 0 ? (
              <>
                <div className="grid sm:grid-cols-2 gap-4 stagger-children">
                  {displayJobs.map(({ job, score, reason }) => (
                    <JobCard
                      key={job.id}
                      job={job}
                      matchScore={matchResults ? score : undefined}
                      matchReason={matchResults ? reason : undefined}
                    />
                  ))}
                </div>

                {/* Pagination (only for browse mode) */}
                {!matchResults && totalPages > 1 && (
                  <div className="flex items-center justify-center gap-2 mt-8">
                    <button
                      onClick={() => setPage((p) => Math.max(1, p - 1))}
                      disabled={page === 1}
                      className="px-4 py-2 rounded-xl border border-border text-sm font-medium disabled:opacity-40 hover:bg-foreground/5 transition-all"
                    >
                      Previous
                    </button>
                    <span className="text-sm text-muted px-3">
                      Page {page} of {totalPages}
                    </span>
                    <button
                      onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                      disabled={page === totalPages}
                      className="px-4 py-2 rounded-xl border border-border text-sm font-medium disabled:opacity-40 hover:bg-foreground/5 transition-all"
                    >
                      Next
                    </button>
                  </div>
                )}
              </>
            ) : (
              <div className="text-center py-16">
                <p className="text-muted text-sm">No jobs found matching your criteria.</p>
                <button
                  onClick={() =>
                    setFilters({ search: "", department: "", level: "", type: "", location: "", remote: null })
                  }
                  className="mt-3 text-sm text-primary hover:text-primary-hover font-medium"
                >
                  Clear filters
                </button>
              </div>
            )}
          </div>
        </div>
      </section>
    </div>
  );
}
