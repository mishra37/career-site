"use client";

import { Job, formatSalary } from "@/lib/types";
import {
  MapPin,
  Clock,
  DollarSign,
  Briefcase,
  Wifi,
  Building2,
  Globe,
  Shield,
} from "lucide-react";
import Link from "next/link";

interface JobCardProps {
  job: Job;
  matchScore?: number;
  matchReason?: string;
}

export default function JobCard({ job, matchScore, matchReason }: JobCardProps) {
  const daysAgo = Math.floor(
    (Date.now() - new Date(job.postedDate).getTime()) / (1000 * 60 * 60 * 24)
  );
  const postedLabel =
    daysAgo === 0 ? "Today" : daysAgo === 1 ? "Yesterday" : `${daysAgo}d ago`;

  const remoteColor =
    job.remoteType === "Remote"
      ? "bg-success/10 text-success"
      : job.remoteType === "Hybrid"
        ? "bg-warning/10 text-warning"
        : "bg-foreground/5 text-muted";

  const remoteIcon =
    job.remoteType === "Remote" ? Wifi : job.remoteType === "Hybrid" ? Globe : Building2;
  const RemoteIcon = remoteIcon;

  return (
    <Link href={`/jobs/${job.id}`}>
      <div className="group bg-card-bg border border-border rounded-2xl p-5 hover:shadow-lg hover:shadow-primary/5 hover:border-primary/30 transition-all duration-200 cursor-pointer relative overflow-hidden h-full">
        {/* Match Score Badge */}
        {matchScore !== undefined && (
          <div className="absolute top-4 right-4">
            <div className="score-badge text-xs font-bold px-2.5 py-1 rounded-full">
              {matchScore}% match
            </div>
          </div>
        )}

        {/* Header */}
        <div className="mb-3">
          <h3 className="text-base font-semibold text-foreground group-hover:text-primary transition-colors pr-20 line-clamp-1">
            {job.title}
          </h3>
          <div className="flex items-center gap-1.5 mt-1">
            <Building2 className="w-3.5 h-3.5 text-muted-light" />
            <span className="text-sm text-muted">{job.company}</span>
          </div>
        </div>

        {/* Tags */}
        <div className="flex flex-wrap gap-1.5 mb-3">
          <span className="inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-lg bg-primary/5 text-primary font-medium">
            <Briefcase className="w-3 h-3" />
            {job.department}
          </span>
          <span className="inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-lg bg-foreground/5 text-muted font-medium">
            {job.level}
          </span>
          <span className={`inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-lg font-medium ${remoteColor}`}>
            <RemoteIcon className="w-3 h-3" />
            {job.remoteType}
          </span>
          {job.visaSponsorship && (
            <span className="inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-lg bg-success/10 text-success font-medium">
              <Shield className="w-3 h-3" />
              Visa
            </span>
          )}
        </div>

        {/* Info row */}
        <div className="flex flex-wrap items-center gap-3 text-xs text-muted">
          <span className="inline-flex items-center gap-1">
            <MapPin className="w-3.5 h-3.5" />
            {job.location}
          </span>
          <span className="inline-flex items-center gap-1">
            <DollarSign className="w-3.5 h-3.5" />
            {formatSalary(job.salary.min, job.salary.max)}
          </span>
          <span className="inline-flex items-center gap-1">
            <Clock className="w-3.5 h-3.5" />
            {postedLabel}
          </span>
        </div>

        {/* Match reason */}
        {matchReason && (
          <div className="mt-3 pt-3 border-t border-border">
            <p className="text-xs text-muted italic line-clamp-2">{matchReason}</p>
          </div>
        )}

        {/* Skills preview */}
        {!matchReason && (
          <div className="mt-3 pt-3 border-t border-border">
            <div className="flex flex-wrap gap-1">
              {job.skills.slice(0, 4).map((skill) => (
                <span
                  key={skill}
                  className="text-[11px] px-2 py-0.5 rounded-md bg-foreground/5 text-muted-light"
                >
                  {skill}
                </span>
              ))}
              {job.skills.length > 4 && (
                <span className="text-[11px] px-2 py-0.5 rounded-md text-muted-light">
                  +{job.skills.length - 4}
                </span>
              )}
            </div>
          </div>
        )}
      </div>
    </Link>
  );
}
