"use client";

import { useEffect, useState } from "react";
import { Job } from "@/lib/types";
import JobCard from "./JobCard";
import JobCardSkeleton from "./JobCardSkeleton";
import Link from "next/link";
import { ArrowRight } from "lucide-react";

export default function FeaturedJobs() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/jobs?pageSize=6&sort=date")
      .then((res) => {
        if (!res.ok) throw new Error(`API error: ${res.status}`);
        return res.json();
      })
      .then((data) => setJobs(data.jobs || []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return (
    <section className="bg-card-bg/30 border-y border-border">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h2 className="text-2xl sm:text-3xl font-bold text-foreground">
              Latest Openings
            </h2>
            <p className="mt-1 text-muted text-sm">
              Recently posted positions across all industries
            </p>
          </div>
          <Link
            href="/jobs"
            className="hidden sm:inline-flex items-center gap-1.5 text-sm text-primary hover:text-primary-hover font-medium transition-colors"
          >
            View all jobs
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>

        {loading ? (
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {Array.from({ length: 6 }).map((_, i) => (
              <JobCardSkeleton key={i} />
            ))}
          </div>
        ) : (
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4 stagger-children">
            {jobs.map((job) => (
              <JobCard key={job.id} job={job} />
            ))}
          </div>
        )}

        <div className="mt-6 text-center sm:hidden">
          <Link
            href="/jobs"
            className="inline-flex items-center gap-1.5 text-sm text-primary font-medium"
          >
            View all jobs
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </div>
    </section>
  );
}
