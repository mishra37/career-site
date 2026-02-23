"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Job } from "@/lib/types";
import {
  ArrowLeft,
  CheckCircle2,
  Upload,
  User,
  Mail,
  Phone,
  FileText,
  Briefcase,
  MapPin,
} from "lucide-react";
import Link from "next/link";

export default function ApplyPage() {
  const params = useParams();
  const [job, setJob] = useState<Job | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitted, setSubmitted] = useState(false);
  const [fileName, setFileName] = useState("");

  const [form, setForm] = useState({
    fullName: "",
    email: "",
    phone: "",
    coverLetter: "",
  });

  useEffect(() => {
    const id = params?.id;
    if (!id) return;

    fetch(`/api/jobs/${id}`)
      .then((res) => {
        if (!res.ok) throw new Error("Not found");
        return res.json();
      })
      .then((data) => setJob(data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [params?.id]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setFileName(file.name);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitted(true);
  };

  if (loading) {
    return (
      <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="animate-shimmer h-6 w-32 rounded-lg mb-6" />
        <div className="bg-card-bg border border-border rounded-2xl p-8">
          <div className="animate-shimmer h-8 w-2/3 rounded-lg mb-4" />
          <div className="animate-shimmer h-5 w-1/3 rounded-lg mb-8" />
          <div className="space-y-4">
            <div className="animate-shimmer h-10 w-full rounded-lg" />
            <div className="animate-shimmer h-10 w-full rounded-lg" />
            <div className="animate-shimmer h-10 w-full rounded-lg" />
          </div>
        </div>
      </div>
    );
  }

  if (!job) {
    return (
      <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-16 text-center">
        <h1 className="text-2xl font-bold text-foreground mb-2">Job Not Found</h1>
        <p className="text-muted mb-4">The job you&apos;re looking for doesn&apos;t exist or has been removed.</p>
        <Link href="/jobs" className="text-primary hover:text-primary-hover font-medium">
          Browse all jobs
        </Link>
      </div>
    );
  }

  if (submitted) {
    return (
      <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="bg-card-bg border border-border rounded-2xl p-8 sm:p-12 text-center animate-fade-in-up">
          <div className="w-16 h-16 rounded-full bg-success/10 flex items-center justify-center mx-auto mb-6">
            <CheckCircle2 className="w-8 h-8 text-success" />
          </div>
          <h1 className="text-2xl font-bold text-foreground mb-2">
            Application Submitted!
          </h1>
          <p className="text-muted mb-2">
            Your application for <span className="font-semibold text-foreground">{job.title}</span> at{" "}
            <span className="font-semibold text-foreground">{job.company}</span> has been received.
          </p>
          <p className="text-sm text-muted-light mb-8">
            The hiring team will review your application and get back to you shortly.
          </p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <Link
              href={`/jobs/${job.id}`}
              className="inline-flex items-center justify-center gap-2 px-6 py-2.5 border border-border rounded-xl text-sm font-medium text-foreground hover:bg-foreground/5 transition-all"
            >
              <ArrowLeft className="w-4 h-4" />
              Back to Job
            </Link>
            <Link
              href="/jobs"
              className="inline-flex items-center justify-center gap-2 px-6 py-2.5 bg-primary text-white rounded-xl text-sm font-medium hover:bg-primary-hover transition-all"
            >
              Browse More Jobs
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Back button */}
      <Link
        href={`/jobs/${job.id}`}
        className="inline-flex items-center gap-2 text-sm text-muted hover:text-foreground transition-colors mb-6"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to job details
      </Link>

      {/* Job summary */}
      <div className="bg-card-bg border border-border rounded-2xl p-5 mb-6 animate-fade-in-up">
        <p className="text-xs font-semibold text-primary uppercase tracking-wide mb-1.5">
          Applying for
        </p>
        <h1 className="text-xl font-bold text-foreground">{job.title}</h1>
        <div className="flex flex-wrap items-center gap-3 mt-2 text-sm text-muted">
          <span className="inline-flex items-center gap-1.5">
            <Briefcase className="w-3.5 h-3.5" />
            {job.company}
          </span>
          <span className="inline-flex items-center gap-1.5">
            <MapPin className="w-3.5 h-3.5" />
            {job.location}
          </span>
        </div>
      </div>

      {/* Application form */}
      <form onSubmit={handleSubmit} className="bg-card-bg border border-border rounded-2xl p-6 sm:p-8 animate-fade-in-up">
        <h2 className="text-lg font-semibold text-foreground mb-6">Your Information</h2>

        <div className="space-y-5">
          {/* Full Name */}
          <div>
            <label htmlFor="fullName" className="text-sm font-medium text-foreground mb-1.5 block">
              Full Name <span className="text-red-400">*</span>
            </label>
            <div className="relative">
              <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-light" />
              <input
                id="fullName"
                type="text"
                required
                value={form.fullName}
                onChange={(e) => setForm({ ...form, fullName: e.target.value })}
                placeholder="John Doe"
                className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-border bg-background text-sm text-foreground placeholder:text-muted-light focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
              />
            </div>
          </div>

          {/* Email */}
          <div>
            <label htmlFor="email" className="text-sm font-medium text-foreground mb-1.5 block">
              Email Address <span className="text-red-400">*</span>
            </label>
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-light" />
              <input
                id="email"
                type="email"
                required
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                placeholder="john@example.com"
                className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-border bg-background text-sm text-foreground placeholder:text-muted-light focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
              />
            </div>
          </div>

          {/* Phone */}
          <div>
            <label htmlFor="phone" className="text-sm font-medium text-foreground mb-1.5 block">
              Phone Number
            </label>
            <div className="relative">
              <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-light" />
              <input
                id="phone"
                type="tel"
                value={form.phone}
                onChange={(e) => setForm({ ...form, phone: e.target.value })}
                placeholder="+1 (555) 123-4567"
                className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-border bg-background text-sm text-foreground placeholder:text-muted-light focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
              />
            </div>
          </div>

          {/* Resume Upload */}
          <div>
            <label className="text-sm font-medium text-foreground mb-1.5 block">
              Resume <span className="text-red-400">*</span>
            </label>
            <label
              htmlFor="resume"
              className="flex flex-col items-center justify-center w-full py-6 border-2 border-dashed border-border rounded-xl cursor-pointer hover:border-primary/50 hover:bg-primary/5 transition-all"
            >
              {fileName ? (
                <div className="flex items-center gap-2 text-sm text-foreground">
                  <FileText className="w-5 h-5 text-primary" />
                  <span className="font-medium">{fileName}</span>
                </div>
              ) : (
                <>
                  <Upload className="w-6 h-6 text-muted-light mb-2" />
                  <p className="text-sm text-muted">
                    <span className="text-primary font-medium">Click to upload</span> or drag and drop
                  </p>
                  <p className="text-xs text-muted-light mt-1">PDF, DOC, or DOCX (max 10MB)</p>
                </>
              )}
              <input
                id="resume"
                type="file"
                accept=".pdf,.doc,.docx,.txt"
                required
                onChange={handleFileChange}
                className="hidden"
              />
            </label>
          </div>

          {/* Cover Letter */}
          <div>
            <label htmlFor="coverLetter" className="text-sm font-medium text-foreground mb-1.5 block">
              Cover Letter <span className="text-muted-light text-xs">(Optional)</span>
            </label>
            <textarea
              id="coverLetter"
              value={form.coverLetter}
              onChange={(e) => setForm({ ...form, coverLetter: e.target.value })}
              placeholder="Tell us why you're interested in this role..."
              rows={4}
              className="w-full px-4 py-2.5 rounded-xl border border-border bg-background text-sm text-foreground placeholder:text-muted-light focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all resize-none"
            />
          </div>
        </div>

        <button
          type="submit"
          className="w-full mt-6 py-3 bg-primary text-white rounded-xl font-medium hover:bg-primary-hover transition-all shadow-lg shadow-primary/20 hover:shadow-primary/30"
        >
          Submit Application
        </button>

        <p className="text-xs text-muted-light text-center mt-4">
          By submitting, you agree to share your information with the hiring team.
        </p>
      </form>
    </div>
  );
}
