"use client";

import { useState, useEffect, useCallback, useMemo } from "react";
import { Job, MatchResult, FilterState, ExtractedKeywords, SortOption } from "@/lib/types";
import JobCard from "@/components/JobCard";
import JobCardSkeleton from "@/components/JobCardSkeleton";
import FilterSidebar from "@/components/FilterSidebar";
import ResumeUpload from "@/components/ResumeUpload";
import { Search, MapPin, X, Sparkles, ChevronDown } from "lucide-react";
import { useResumeModal } from "@/contexts/ResumeModalContext";

const DEFAULT_FILTERS: FilterState = {
  search: "",
  location: "",
  type: "",
  remoteType: "",
  visaSponsorship: null,
  postedWithin: "",
  yearsMin: "",
  yearsMax: "",
  salaryMin: "",
  salaryMax: "",
  sort: "date",
};

export default function BrowsePage() {
  const resumeModal = useResumeModal();
  const [jobs, setJobs] = useState<Job[]>([]);
  const [matchResults, setMatchResults] = useState<MatchResult[] | null>(null);
  const [extractedKeywords, setExtractedKeywords] = useState<ExtractedKeywords | null>(null);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState<FilterState>(DEFAULT_FILTERS);
  const [filterOptions, setFilterOptions] = useState({
    types: [] as string[],
    remoteTypes: [] as string[],
  });
  const [page, setPage] = useState(1);
  const [totalJobs, setTotalJobs] = useState(0);
  const [totalPages, setTotalPages] = useState(1);

  // Search inputs are separate from filters — only applied on submit
  const [searchInput, setSearchInput] = useState("");
  const [locationInput, setLocationInput] = useState("");

  // Sync results from resume modal context (triggered by header/landing modal)
  useEffect(() => {
    if (resumeModal.matchResults) {
      setMatchResults(resumeModal.matchResults);
      setExtractedKeywords(resumeModal.extractedKeywords);
      setFilters({ ...DEFAULT_FILTERS, sort: "relevance" });
      setSearchInput("");
      setLocationInput("");
      setPage(1);
      resumeModal.clearResults();
    }
  }, [resumeModal.matchResults]); // eslint-disable-line react-hooks/exhaustive-deps

  // Fetch jobs from API
  const fetchJobs = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.set("page", page.toString());
      params.set("pageSize", "12");
      if (filters.search) params.set("q", filters.search);
      if (filters.location) params.set("location", filters.location);
      if (filters.type) params.set("type", filters.type);
      if (filters.remoteType) params.set("remoteType", filters.remoteType);
      if (filters.visaSponsorship !== null) params.set("visaSponsorship", filters.visaSponsorship.toString());
      if (filters.postedWithin) params.set("postedWithin", filters.postedWithin);
      if (filters.yearsMin) params.set("yearsMin", filters.yearsMin);
      if (filters.yearsMax) params.set("yearsMax", filters.yearsMax);
      if (filters.salaryMin) params.set("salaryMin", filters.salaryMin);
      if (filters.salaryMax) params.set("salaryMax", filters.salaryMax);
      if (filters.sort) params.set("sort", filters.sort);

      const res = await fetch(`/api/jobs?${params.toString()}`);
      if (!res.ok) throw new Error(`API error: ${res.status}`);
      const data = await res.json();

      setJobs(data.jobs || []);
      setTotalJobs(data.total || 0);
      setTotalPages(data.totalPages || 1);
      setFilterOptions({
        types: data.types || [],
        remoteTypes: data.remoteTypes || [],
      });
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
  }, [
    filters.search,
    filters.location,
    filters.type,
    filters.remoteType,
    filters.visaSponsorship,
    filters.postedWithin,
    filters.yearsMin,
    filters.yearsMax,
    filters.salaryMin,
    filters.salaryMax,
    filters.sort,
  ]);

  // Handle search submit (Enter or button click)
  const handleSearchSubmit = () => {
    setFilters((prev) => ({
      ...prev,
      search: searchInput,
      location: locationInput,
    }));
  };

  const handleSearchKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      handleSearchSubmit();
    }
  };

  const clearSearch = () => {
    setSearchInput("");
    setLocationInput("");
    setFilters((prev) => ({ ...prev, search: "", location: "" }));
  };

  // Client-side filtering for personalized results
  const filteredMatches = useMemo(() => {
    if (!matchResults) return null;

    let results = [...matchResults];

    results = results.filter((m) => {
      const job = m.job;
      if (filters.search) {
        const s = filters.search.toLowerCase();
        const matches =
          job.title.toLowerCase().includes(s) ||
          job.description.toLowerCase().includes(s) ||
          job.skills.some((sk) => sk.toLowerCase().includes(s)) ||
          job.department.toLowerCase().includes(s) ||
          job.company.toLowerCase().includes(s);
        if (!matches) return false;
      }
      if (filters.location) {
        if (!job.location.toLowerCase().includes(filters.location.toLowerCase())) return false;
      }
      if (filters.type && job.type !== filters.type) return false;
      if (filters.remoteType && job.remoteType !== filters.remoteType) return false;
      if (filters.visaSponsorship !== null && job.visaSponsorship !== filters.visaSponsorship)
        return false;
      if (filters.postedWithin) {
        const cutoff = new Date();
        const days = filters.postedWithin === "24h" ? 1 : filters.postedWithin === "7d" ? 7 : 30;
        cutoff.setDate(cutoff.getDate() - days);
        if (new Date(job.postedDate) < cutoff) return false;
      }
      if (filters.yearsMin && job.yearsExperienceMin !== null) {
        if (job.yearsExperienceMin < parseInt(filters.yearsMin)) return false;
      }
      if (filters.yearsMax && job.yearsExperienceMax !== null) {
        if (job.yearsExperienceMax > parseInt(filters.yearsMax)) return false;
      }
      if (filters.salaryMin && job.salary.max < parseInt(filters.salaryMin)) return false;
      if (filters.salaryMax && job.salary.min > parseInt(filters.salaryMax)) return false;
      return true;
    });

    // Sort
    if (filters.sort === "date") {
      results.sort((a, b) => new Date(b.job.postedDate).getTime() - new Date(a.job.postedDate).getTime());
    } else if (filters.sort === "salary-high") {
      results.sort((a, b) => b.job.salary.max - a.job.salary.max);
    } else if (filters.sort === "salary-low") {
      results.sort((a, b) => a.job.salary.min - b.job.salary.min);
    }

    return results;
  }, [matchResults, filters]);

  // Paginate personalized results client-side
  const PAGE_SIZE = 12;
  const personalizedPage = filteredMatches
    ? filteredMatches.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE)
    : null;
  const personalizedTotalPages = filteredMatches
    ? Math.max(1, Math.ceil(filteredMatches.length / PAGE_SIZE))
    : 1;

  const displayJobs = matchResults
    ? (personalizedPage || []).map(({ job, score, reason }) => ({ job, score, reason }))
    : jobs.map((j) => ({ job: j, score: 0, reason: "" }));

  const displayTotal = matchResults ? (filteredMatches?.length || 0) : totalJobs;
  const displayTotalPages = matchResults ? personalizedTotalPages : totalPages;

  const handleMatchResults = (
    results: MatchResult[] | null,
    keywords?: ExtractedKeywords | null
  ) => {
    setMatchResults(results);
    setExtractedKeywords(keywords ?? null);
    setPage(1);
    if (results) {
      setFilters({ ...DEFAULT_FILTERS, sort: "relevance" });
      setSearchInput("");
      setLocationInput("");
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      {/* Search bar + sort */}
      <div className="flex flex-col sm:flex-row gap-3 mb-6">
        {/* Keyword search */}
        <div className="relative flex-1">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-light" />
          <input
            type="text"
            placeholder="Search by title, skill, or keyword..."
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            onKeyDown={handleSearchKeyDown}
            className="w-full pl-10 pr-10 py-2.5 rounded-xl border border-border bg-card-bg text-sm text-foreground placeholder:text-muted-light focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
          />
          {searchInput && (
            <button
              onClick={() => {
                setSearchInput("");
                if (filters.search) setFilters((prev) => ({ ...prev, search: "" }));
              }}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-light hover:text-foreground"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>

        {/* Location search */}
        <div className="relative sm:w-48">
          <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-light" />
          <input
            type="text"
            placeholder="Location..."
            value={locationInput}
            onChange={(e) => setLocationInput(e.target.value)}
            onKeyDown={handleSearchKeyDown}
            className="w-full pl-9 pr-3 py-2.5 rounded-xl border border-border bg-card-bg text-sm text-foreground placeholder:text-muted-light focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
          />
        </div>

        {/* Search button */}
        <button
          onClick={handleSearchSubmit}
          className="px-5 py-2.5 bg-primary text-white rounded-xl text-sm font-medium hover:bg-primary-hover transition-all shadow-sm hover:shadow-md flex items-center gap-2 justify-center"
        >
          <Search className="w-4 h-4" />
          Search
        </button>

        {/* Sort */}
        <div className="relative sm:w-44">
          <select
            value={filters.sort}
            onChange={(e) =>
              setFilters({ ...filters, sort: e.target.value as SortOption })
            }
            className="w-full px-3 py-2.5 rounded-xl border border-border bg-card-bg text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20 appearance-none pr-8"
          >
            {matchResults && <option value="relevance">Sort: Relevance</option>}
            <option value="date">Sort: Newest</option>
            <option value="salary-high">Sort: Salary High</option>
            <option value="salary-low">Sort: Salary Low</option>
          </select>
          <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-light pointer-events-none" />
        </div>
      </div>

      {/* Active search chips */}
      {(filters.search || filters.location) && (
        <div className="flex flex-wrap gap-2 mb-4">
          {filters.search && (
            <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-primary/10 text-primary text-sm rounded-full font-medium">
              <Search className="w-3 h-3" />
              {filters.search}
              <button onClick={() => { setSearchInput(""); setFilters((prev) => ({ ...prev, search: "" })); }}>
                <X className="w-3 h-3" />
              </button>
            </span>
          )}
          {filters.location && (
            <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-primary/10 text-primary text-sm rounded-full font-medium">
              <MapPin className="w-3 h-3" />
              {filters.location}
              <button onClick={() => { setLocationInput(""); setFilters((prev) => ({ ...prev, location: "" })); }}>
                <X className="w-3 h-3" />
              </button>
            </span>
          )}
          <button
            onClick={clearSearch}
            className="text-xs text-muted hover:text-foreground px-2 py-1"
          >
            Clear search
          </button>
        </div>
      )}

      <div className="grid lg:grid-cols-[280px_1fr] gap-8">
        {/* Sidebar */}
        <div className="space-y-6">
          {/* Resume Upload */}
          <div id="upload">
            <h2 className="text-sm font-semibold text-foreground mb-3 flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-primary" />
              AI Resume Matching
            </h2>
            <ResumeUpload
              onMatchResults={handleMatchResults}
              isMatched={matchResults !== null}
              extractedKeywords={extractedKeywords}
            />
          </div>

          {/* Match Summary */}
          {matchResults && (
            <div className="bg-card-bg border border-border rounded-2xl p-4 animate-fade-in-up">
              <h3 className="text-sm font-semibold text-foreground mb-3">Match Summary</h3>
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-muted">Total matches</span>
                  <span className="font-semibold text-foreground">{matchResults.length}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted">Strong (70%+)</span>
                  <span className="font-semibold text-success">
                    {matchResults.filter((m) => m.score >= 70).length}
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted">Good (40-69%)</span>
                  <span className="font-semibold text-warning">
                    {matchResults.filter((m) => m.score >= 40 && m.score < 70).length}
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted">Top score</span>
                  <span className="font-semibold text-primary">
                    {matchResults.length > 0 ? `${matchResults[0].score}%` : "\u2014"}
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Extracted Keywords */}
          {extractedKeywords && extractedKeywords.skills.length > 0 && (
            <div className="bg-card-bg border border-border rounded-2xl p-4 animate-fade-in-up">
              <h3 className="text-sm font-semibold text-foreground mb-3">Extracted Keywords</h3>
              <div className="flex flex-wrap gap-1.5">
                {extractedKeywords.skills.slice(0, 15).map((skill) => (
                  <span
                    key={skill}
                    className="px-2 py-0.5 bg-primary/10 text-primary text-xs rounded-full font-medium"
                  >
                    {skill}
                  </span>
                ))}
                {extractedKeywords.skills.length > 15 && (
                  <span className="px-2 py-0.5 text-muted text-xs">
                    +{extractedKeywords.skills.length - 15} more
                  </span>
                )}
              </div>
              {(extractedKeywords.experienceLevel || extractedKeywords.domains.length > 0) && (
                <div className="mt-3 pt-3 border-t border-border space-y-1.5">
                  {extractedKeywords.experienceLevel && (
                    <p className="text-xs text-muted">
                      Level:{" "}
                      <span className="text-foreground font-medium capitalize">
                        {extractedKeywords.experienceLevel}
                      </span>
                      {extractedKeywords.yearsOfExperience &&
                        ` (${extractedKeywords.yearsOfExperience}+ years)`}
                    </p>
                  )}
                  {extractedKeywords.domains.length > 0 && (
                    <p className="text-xs text-muted">
                      Domains:{" "}
                      <span className="text-foreground font-medium capitalize">
                        {extractedKeywords.domains.join(", ")}
                      </span>
                    </p>
                  )}
                  {extractedKeywords.education.length > 0 && (
                    <p className="text-xs text-muted">
                      Education:{" "}
                      <span className="text-foreground font-medium">
                        {extractedKeywords.education.join(", ")}
                      </span>
                    </p>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Filters */}
          <FilterSidebar
            filters={filters}
            onFilterChange={setFilters}
            filterOptions={filterOptions}
            totalJobs={displayTotal}
            isPersonalized={matchResults !== null}
          />
        </div>

        {/* Job Grid */}
        <div className="space-y-4">
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

              {/* Pagination */}
              {displayTotalPages > 1 && (
                <div className="flex items-center justify-center gap-2 mt-8">
                  <button
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page === 1}
                    className="px-4 py-2 rounded-xl border border-border text-sm font-medium disabled:opacity-40 hover:bg-foreground/5 transition-all"
                  >
                    Previous
                  </button>
                  <span className="text-sm text-muted px-3">
                    Page {page} of {displayTotalPages}
                  </span>
                  <button
                    onClick={() => setPage((p) => Math.min(displayTotalPages, p + 1))}
                    disabled={page === displayTotalPages}
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
                onClick={() => {
                  setFilters(DEFAULT_FILTERS);
                  setSearchInput("");
                  setLocationInput("");
                }}
                className="mt-3 text-sm text-primary hover:text-primary-hover font-medium"
              >
                Clear filters
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
