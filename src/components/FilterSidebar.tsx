"use client";

import { FilterState } from "@/lib/types";
import { X, SlidersHorizontal, Check } from "lucide-react";
import { useState, useEffect } from "react";

interface FilterSidebarProps {
  filters: FilterState;
  onFilterChange: (filters: FilterState) => void;
  filterOptions: {
    types: string[];
    remoteTypes: string[];
  };
  totalJobs: number;
  isPersonalized: boolean;
}

export default function FilterSidebar({
  filters,
  onFilterChange,
  filterOptions,
  totalJobs,
  isPersonalized,
}: FilterSidebarProps) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [yearsMinInput, setYearsMinInput] = useState(filters.yearsMin);
  const [yearsMaxInput, setYearsMaxInput] = useState(filters.yearsMax);

  // Sync local state when filters are cleared externally
  useEffect(() => {
    setYearsMinInput(filters.yearsMin);
    setYearsMaxInput(filters.yearsMax);
  }, [filters.yearsMin, filters.yearsMax]);

  const yearsRangeInvalid =
    yearsMinInput !== "" &&
    yearsMaxInput !== "" &&
    Number(yearsMaxInput) < Number(yearsMinInput);

  const yearsChanged =
    yearsMinInput !== filters.yearsMin || yearsMaxInput !== filters.yearsMax;

  const applyYearsFilter = () => {
    if (yearsRangeInvalid) return;
    onFilterChange({
      ...filters,
      yearsMin: yearsMinInput,
      yearsMax: yearsMaxInput,
    });
  };

  const update = (key: keyof FilterState, value: string | boolean | null) => {
    onFilterChange({ ...filters, [key]: value } as FilterState);
  };

  const clearFilters = () => {
    onFilterChange({
      search: filters.search,
      location: filters.location,
      type: "",
      remoteType: "",
      visaSponsorship: null,
      postedWithin: "",
      yearsMin: "",
      yearsMax: "",
      salaryMin: "",
      salaryMax: "",
      sort: filters.sort,
    });
  };

  const hasActiveFilters =
    filters.type ||
    filters.remoteType ||
    filters.visaSponsorship !== null ||
    filters.postedWithin ||
    filters.yearsMin ||
    filters.yearsMax ||
    filters.salaryMin ||
    filters.salaryMax;

  const activeCount = [
    filters.type,
    filters.remoteType,
    filters.visaSponsorship !== null ? "v" : "",
    filters.postedWithin,
    filters.yearsMin || filters.yearsMax ? "y" : "",
    filters.salaryMin || filters.salaryMax ? "s" : "",
  ].filter(Boolean).length;

  const filterContent = (
    <div className="space-y-4">
      {/* Result count */}
      <div className="pb-3 border-b border-border">
        <p className="text-sm text-muted">
          {isPersonalized ? (
            <>
              <span className="font-semibold text-primary">{totalJobs}</span>{" "}
              personalized matches
            </>
          ) : (
            <>
              <span className="font-semibold text-foreground">{totalJobs.toLocaleString()}</span>{" "}
              open positions
            </>
          )}
        </p>
      </div>

      {/* Job Type */}
      <FilterSelect
        label="Job Type"
        value={filters.type}
        onChange={(v) => update("type", v)}
        options={filterOptions.types}
        placeholder="All Types"
      />

      {/* Work Setting */}
      <FilterSelect
        label="Work Setting"
        value={filters.remoteType}
        onChange={(v) => update("remoteType", v)}
        options={filterOptions.remoteTypes}
        placeholder="All"
      />

      {/* Visa Sponsorship */}
      <div>
        <label className="text-xs font-semibold text-foreground/70 uppercase tracking-wide mb-1.5 block">
          Visa Sponsorship
        </label>
        <div className="flex gap-1.5">
          {[
            { label: "Any", value: "" },
            { label: "Yes", value: "true" },
            { label: "No", value: "false" },
          ].map((opt) => {
            const current =
              filters.visaSponsorship === null ? "" : filters.visaSponsorship ? "true" : "false";
            const isActive = current === opt.value;
            return (
              <button
                key={opt.value}
                onClick={() =>
                  update("visaSponsorship", opt.value === "" ? null : opt.value === "true")
                }
                className={`flex-1 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  isActive
                    ? "bg-primary text-white"
                    : "bg-foreground/5 text-muted hover:bg-foreground/10"
                }`}
              >
                {opt.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Posted Within */}
      <div>
        <label className="text-xs font-semibold text-foreground/70 uppercase tracking-wide mb-1.5 block">
          Posted Within
        </label>
        <div className="flex gap-1.5">
          {[
            { label: "All", value: "" },
            { label: "24h", value: "24h" },
            { label: "7d", value: "7d" },
            { label: "30d", value: "30d" },
          ].map((opt) => {
            const isActive = filters.postedWithin === opt.value;
            return (
              <button
                key={opt.value}
                onClick={() => update("postedWithin", opt.value)}
                className={`flex-1 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  isActive
                    ? "bg-primary text-white"
                    : "bg-foreground/5 text-muted hover:bg-foreground/10"
                }`}
              >
                {opt.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Years of Experience */}
      <div>
        <label className="text-xs font-semibold text-foreground/70 uppercase tracking-wide mb-1.5 block">
          Years of Experience
        </label>
        <div className="flex gap-2 items-center">
          <input
            type="number"
            min="0"
            max="30"
            placeholder="Min"
            value={yearsMinInput}
            onChange={(e) => setYearsMinInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && applyYearsFilter()}
            className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm text-foreground placeholder:text-muted-light focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
          />
          <span className="text-muted text-xs shrink-0">to</span>
          <input
            type="number"
            min="0"
            max="30"
            placeholder="Max"
            value={yearsMaxInput}
            onChange={(e) => setYearsMaxInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && applyYearsFilter()}
            className={`w-full px-3 py-2 rounded-lg border bg-background text-sm text-foreground placeholder:text-muted-light focus:outline-none focus:ring-2 transition-all ${
              yearsRangeInvalid
                ? "border-red-500 focus:ring-red-500/20 focus:border-red-500"
                : "border-border focus:ring-primary/20 focus:border-primary"
            }`}
          />
        </div>
        {yearsRangeInvalid && (
          <p className="text-red-500 text-xs mt-1">Max must be ≥ min</p>
        )}
        {yearsChanged && !yearsRangeInvalid && (yearsMinInput || yearsMaxInput) && (
          <button
            onClick={applyYearsFilter}
            className="mt-2 w-full py-1.5 rounded-lg text-xs font-medium bg-primary text-white hover:bg-primary/90 flex items-center justify-center gap-1 transition-all"
          >
            <Check className="w-3 h-3" /> Apply
          </button>
        )}
      </div>

      {/* Salary Range */}
      <FilterSelect
        label="Min Salary"
        value={filters.salaryMin}
        onChange={(v) => update("salaryMin", v)}
        options={["50000", "75000", "100000", "150000", "200000"]}
        labels={["$50k+", "$75k+", "$100k+", "$150k+", "$200k+"]}
        placeholder="No min"
      />
      <FilterSelect
        label="Max Salary"
        value={filters.salaryMax}
        onChange={(v) => update("salaryMax", v)}
        options={["75000", "100000", "150000", "200000", "300000", "500000"]}
        labels={["Up to $75k", "Up to $100k", "Up to $150k", "Up to $200k", "Up to $300k", "Up to $500k"]}
        placeholder="No max"
      />

      {hasActiveFilters && (
        <button
          onClick={clearFilters}
          className="w-full mt-1 py-2 rounded-lg text-xs text-primary hover:bg-primary/5 font-medium flex items-center justify-center gap-1 transition-all"
        >
          <X className="w-3 h-3" /> Clear all filters
        </button>
      )}
    </div>
  );

  return (
    <>
      {/* Mobile filter toggle */}
      <button
        onClick={() => setMobileOpen(true)}
        className="lg:hidden flex items-center gap-2 px-4 py-2.5 rounded-xl border border-border bg-card-bg text-sm font-medium text-muted hover:border-primary/50 transition-all"
      >
        <SlidersHorizontal className="w-4 h-4" />
        Filters
        {activeCount > 0 && (
          <span className="min-w-5 h-5 rounded-full bg-primary text-white text-xs flex items-center justify-center px-1">
            {activeCount}
          </span>
        )}
      </button>

      {/* Mobile overlay */}
      {mobileOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div
            className="absolute inset-0 bg-black/40 backdrop-blur-sm"
            onClick={() => setMobileOpen(false)}
          />
          <div className="absolute left-0 top-0 h-full w-80 bg-background border-r border-border overflow-y-auto">
            <div className="sticky top-0 bg-background border-b border-border p-4 flex items-center justify-between z-10">
              <h3 className="font-semibold text-foreground">Filters</h3>
              <button
                onClick={() => setMobileOpen(false)}
                className="text-muted hover:text-foreground p-1 rounded-lg hover:bg-foreground/5"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-4">{filterContent}</div>
          </div>
        </div>
      )}

      {/* Desktop sidebar */}
      <div className="hidden lg:block bg-card-bg border border-border rounded-2xl p-5">
        <h3 className="text-sm font-semibold text-foreground mb-4 flex items-center justify-between">
          <span className="flex items-center gap-2">
            <SlidersHorizontal className="w-4 h-4 text-primary" />
            Filters
          </span>
          {activeCount > 0 && (
            <span className="min-w-5 h-5 rounded-full bg-primary text-white text-xs flex items-center justify-center px-1">
              {activeCount}
            </span>
          )}
        </h3>
        {filterContent}
      </div>
    </>
  );
}

function FilterSelect({
  label,
  value,
  onChange,
  options,
  labels,
  placeholder,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  options: string[];
  labels?: string[];
  placeholder: string;
}) {
  return (
    <div>
      <label className="text-xs font-semibold text-foreground/70 uppercase tracking-wide mb-1.5 block">
        {label}
      </label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all appearance-none cursor-pointer"
        style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%239ca3af' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='m6 9 6 6 6-6'/%3E%3C/svg%3E")`,
          backgroundPosition: "right 8px center",
          backgroundRepeat: "no-repeat",
        }}
      >
        <option value="">{placeholder}</option>
        {options.map((opt, i) => (
          <option key={opt} value={opt}>
            {labels ? labels[i] : opt}
          </option>
        ))}
      </select>
    </div>
  );
}
