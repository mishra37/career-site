"use client";

import { FilterState } from "@/lib/types";
import { Search, SlidersHorizontal, X } from "lucide-react";
import { useState } from "react";

interface FilterBarProps {
  filters: FilterState;
  onFilterChange: (filters: FilterState) => void;
  filterOptions: {
    departments: string[];
    levels: string[];
    locations: string[];
    types: string[];
  };
  totalJobs: number;
  isPersonalized: boolean;
}

export default function FilterBar({
  filters,
  onFilterChange,
  filterOptions,
  totalJobs,
  isPersonalized,
}: FilterBarProps) {
  const [showFilters, setShowFilters] = useState(false);

  const updateFilter = (key: keyof FilterState, value: string | boolean | null) => {
    onFilterChange({ ...filters, [key]: value });
  };

  const clearFilters = () => {
    onFilterChange({
      search: "",
      department: "",
      level: "",
      type: "",
      location: "",
      remote: null,
    });
  };

  const hasActiveFilters =
    filters.department || filters.level || filters.type || filters.location || filters.remote !== null;

  return (
    <div className="space-y-3">
      {/* Search + filter toggle */}
      <div className="flex gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-light" />
          <input
            type="text"
            placeholder="Search by title, skill, or keyword..."
            value={filters.search}
            onChange={(e) => updateFilter("search", e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-border bg-card-bg text-sm text-foreground placeholder:text-muted-light focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
          />
          {filters.search && (
            <button
              onClick={() => updateFilter("search", "")}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-light hover:text-foreground"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
        <button
          onClick={() => setShowFilters(!showFilters)}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-xl border text-sm font-medium transition-all ${
            showFilters || hasActiveFilters
              ? "bg-primary text-white border-primary"
              : "bg-card-bg border-border text-muted hover:border-primary/50"
          }`}
        >
          <SlidersHorizontal className="w-4 h-4" />
          <span className="hidden sm:inline">Filters</span>
          {hasActiveFilters && (
            <span className="w-5 h-5 rounded-full bg-white/20 text-xs flex items-center justify-center">
              {[filters.department, filters.level, filters.type, filters.location, filters.remote !== null ? "r" : ""].filter(Boolean).length}
            </span>
          )}
        </button>
      </div>

      {/* Filter panel */}
      {showFilters && (
        <div className="bg-card-bg border border-border rounded-2xl p-4 animate-fade-in-up">
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-3">
            <div>
              <label className="text-xs font-medium text-muted mb-1 block">Department</label>
              <select
                value={filters.department}
                onChange={(e) => updateFilter("department", e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20"
              >
                <option value="">All</option>
                {filterOptions.departments.map((d) => (
                  <option key={d} value={d}>{d}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-xs font-medium text-muted mb-1 block">Level</label>
              <select
                value={filters.level}
                onChange={(e) => updateFilter("level", e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20"
              >
                <option value="">All</option>
                {filterOptions.levels.map((l) => (
                  <option key={l} value={l}>{l}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-xs font-medium text-muted mb-1 block">Type</label>
              <select
                value={filters.type}
                onChange={(e) => updateFilter("type", e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20"
              >
                <option value="">All</option>
                {filterOptions.types.map((t) => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-xs font-medium text-muted mb-1 block">Location</label>
              <select
                value={filters.location}
                onChange={(e) => updateFilter("location", e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20"
              >
                <option value="">All</option>
                {filterOptions.locations.map((l) => (
                  <option key={l} value={l}>{l}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-xs font-medium text-muted mb-1 block">Remote</label>
              <select
                value={filters.remote === null ? "" : filters.remote ? "true" : "false"}
                onChange={(e) =>
                  updateFilter(
                    "remote",
                    e.target.value === "" ? null : e.target.value === "true"
                  )
                }
                className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20"
              >
                <option value="">All</option>
                <option value="true">Remote Only</option>
                <option value="false">On-site</option>
              </select>
            </div>
          </div>
          {hasActiveFilters && (
            <button
              onClick={clearFilters}
              className="mt-3 text-xs text-primary hover:text-primary-hover font-medium flex items-center gap-1"
            >
              <X className="w-3 h-3" /> Clear all filters
            </button>
          )}
        </div>
      )}

      {/* Result count */}
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted">
          {isPersonalized ? (
            <>
              <span className="font-semibold text-primary">{totalJobs}</span> personalized matches
            </>
          ) : (
            <>
              <span className="font-semibold text-foreground">{totalJobs}</span> open positions
            </>
          )}
        </p>
      </div>
    </div>
  );
}
