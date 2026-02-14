import { getJobById, formatSalary, jobs } from "@/lib/jobs-data";
import {
  MapPin,
  Clock,
  DollarSign,
  Briefcase,
  Wifi,
  Building2,
  ArrowLeft,
  ExternalLink,
  CheckCircle2,
} from "lucide-react";
import Link from "next/link";
import { notFound } from "next/navigation";
import { Metadata } from "next";

interface PageProps {
  params: Promise<{ id: string }>;
}

export async function generateStaticParams() {
  return jobs.map((job) => ({ id: job.id }));
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { id } = await params;
  const job = getJobById(id);
  if (!job) return { title: "Job Not Found" };

  return {
    title: `${job.title} at ${job.company} | CareerMatch`,
    description: job.description,
  };
}

export default async function JobDetailPage({ params }: PageProps) {
  const { id } = await params;
  const job = getJobById(id);

  if (!job) {
    notFound();
  }

  const daysAgo = Math.floor(
    (Date.now() - new Date(job.postedDate).getTime()) / (1000 * 60 * 60 * 24)
  );
  const postedLabel =
    daysAgo === 0 ? "Today" : daysAgo === 1 ? "Yesterday" : `${daysAgo} days ago`;

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Back button */}
      <Link
        href="/"
        className="inline-flex items-center gap-2 text-sm text-muted hover:text-foreground transition-colors mb-6"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to all jobs
      </Link>

      {/* Job header */}
      <div className="bg-card-bg border border-border rounded-2xl p-6 sm:p-8 mb-6 animate-fade-in-up">
        <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold text-foreground">
              {job.title}
            </h1>
            <div className="flex items-center gap-2 mt-2">
              <Building2 className="w-4 h-4 text-muted-light" />
              <span className="text-base text-muted">{job.company}</span>
            </div>
          </div>
          <button className="inline-flex items-center gap-2 px-6 py-3 bg-primary text-white rounded-xl font-medium hover:bg-primary-hover transition-all shadow-lg shadow-primary/20 hover:shadow-primary/30 whitespace-nowrap">
            Apply Now
            <ExternalLink className="w-4 h-4" />
          </button>
        </div>

        {/* Tags */}
        <div className="flex flex-wrap gap-2 mt-4">
          <span className="inline-flex items-center gap-1.5 text-sm px-3 py-1.5 rounded-lg bg-primary/5 text-primary font-medium">
            <Briefcase className="w-3.5 h-3.5" />
            {job.department}
          </span>
          <span className="inline-flex items-center gap-1.5 text-sm px-3 py-1.5 rounded-lg bg-foreground/5 text-muted font-medium">
            {job.level} · {job.type}
          </span>
          {job.remote && (
            <span className="inline-flex items-center gap-1.5 text-sm px-3 py-1.5 rounded-lg bg-success/10 text-success font-medium">
              <Wifi className="w-3.5 h-3.5" />
              Remote
            </span>
          )}
        </div>

        {/* Info bar */}
        <div className="flex flex-wrap gap-4 mt-4 pt-4 border-t border-border text-sm text-muted">
          <span className="inline-flex items-center gap-1.5">
            <MapPin className="w-4 h-4" />
            {job.location}
          </span>
          <span className="inline-flex items-center gap-1.5">
            <DollarSign className="w-4 h-4" />
            {formatSalary(job.salary.min, job.salary.max)} / year
          </span>
          <span className="inline-flex items-center gap-1.5">
            <Clock className="w-4 h-4" />
            Posted {postedLabel}
          </span>
        </div>
      </div>

      <div className="grid lg:grid-cols-[1fr_280px] gap-6">
        {/* Main content */}
        <div className="space-y-6">
          {/* Description */}
          <section className="bg-card-bg border border-border rounded-2xl p-6 animate-fade-in-up">
            <h2 className="text-lg font-semibold text-foreground mb-3">
              About this role
            </h2>
            <p className="text-sm text-muted leading-relaxed">{job.description}</p>
          </section>

          {/* Responsibilities */}
          <section className="bg-card-bg border border-border rounded-2xl p-6 animate-fade-in-up">
            <h2 className="text-lg font-semibold text-foreground mb-3">
              What you&apos;ll do
            </h2>
            <ul className="space-y-2">
              {job.responsibilities.map((resp, i) => (
                <li key={i} className="flex gap-2.5 text-sm text-muted">
                  <CheckCircle2 className="w-4 h-4 text-success mt-0.5 shrink-0" />
                  <span>{resp}</span>
                </li>
              ))}
            </ul>
          </section>

          {/* Requirements */}
          <section className="bg-card-bg border border-border rounded-2xl p-6 animate-fade-in-up">
            <h2 className="text-lg font-semibold text-foreground mb-3">
              What we&apos;re looking for
            </h2>
            <ul className="space-y-2">
              {job.requirements.map((req, i) => (
                <li key={i} className="flex gap-2.5 text-sm text-muted">
                  <div className="w-1.5 h-1.5 rounded-full bg-primary mt-2 shrink-0" />
                  <span>{req}</span>
                </li>
              ))}
            </ul>
          </section>
        </div>

        {/* Sidebar */}
        <div className="space-y-4">
          {/* Skills */}
          <div className="bg-card-bg border border-border rounded-2xl p-5 animate-fade-in-up">
            <h3 className="text-sm font-semibold text-foreground mb-3">
              Skills & Technologies
            </h3>
            <div className="flex flex-wrap gap-1.5">
              {job.skills.map((skill) => (
                <span
                  key={skill}
                  className="text-xs px-2.5 py-1 rounded-lg bg-primary/5 text-primary font-medium"
                >
                  {skill}
                </span>
              ))}
            </div>
          </div>

          {/* Apply card */}
          <div className="bg-gradient-to-br from-primary to-accent rounded-2xl p-5 text-white animate-fade-in-up">
            <h3 className="font-semibold mb-2">Interested in this role?</h3>
            <p className="text-sm text-white/80 mb-4">
              Apply now or upload your resume on our homepage to see how well you
              match.
            </p>
            <div className="space-y-2">
              <button className="w-full py-2.5 bg-white text-primary rounded-xl font-medium text-sm hover:bg-white/90 transition-all">
                Apply Now
              </button>
              <Link
                href="/#upload"
                className="w-full py-2.5 bg-white/10 text-white rounded-xl font-medium text-sm hover:bg-white/20 transition-all text-center block"
              >
                Check My Match Score
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
