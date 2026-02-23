import Link from "next/link";
import { Briefcase, Search, Upload, Sparkles, MapPin, Building2, ArrowRight, Globe } from "lucide-react";
import FeaturedJobs from "@/components/FeaturedJobs";
import UploadResumeButton from "@/components/UploadResumeButton";

export default function LandingPage() {
  return (
    <div>
      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-accent/5" />
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-16 pb-12 sm:pt-24 sm:pb-16">
          <div className="max-w-3xl">
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-foreground tracking-tight leading-tight">
              Find Your Perfect{" "}
              <span className="text-primary">Career Match</span>
            </h1>
            <p className="mt-4 text-lg text-muted max-w-xl">
              Browse thousands of open positions across every industry, or upload
              your resume and let us find the best matches for you.
            </p>
            <div className="flex flex-wrap gap-3 mt-8">
              <Link
                href="/jobs"
                className="inline-flex items-center gap-2 px-6 py-3 bg-primary text-white rounded-xl font-medium hover:bg-primary-hover transition-all shadow-lg shadow-primary/20 hover:shadow-primary/30"
              >
                <Search className="w-4 h-4" />
                Browse All Jobs
              </Link>
              <UploadResumeButton />
            </div>
          </div>
        </div>
      </section>

      {/* Stats */}
      <section className="border-y border-border bg-card-bg/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            {[
              { icon: Briefcase, value: "10,000+", label: "Open Positions" },
              { icon: Building2, value: "50+", label: "Companies" },
              { icon: MapPin, value: "30+", label: "Locations" },
              { icon: Globe, value: "14", label: "Industries" },
            ].map(({ icon: Icon, value, label }) => (
              <div key={label} className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center shrink-0">
                  <Icon className="w-5 h-5 text-primary" />
                </div>
                <div>
                  <p className="text-lg font-bold text-foreground">{value}</p>
                  <p className="text-xs text-muted">{label}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="text-center mb-10">
          <h2 className="text-2xl sm:text-3xl font-bold text-foreground">
            How It Works
          </h2>
          <p className="mt-2 text-muted">
            Three simple steps to your next career opportunity
          </p>
        </div>
        <div className="grid md:grid-cols-3 gap-6">
          {[
            {
              icon: Search,
              title: "Browse & Search",
              desc: "Explore jobs by keyword, location, salary, and more. Filter across 14 industries to find the right fit.",
              step: "1",
            },
            {
              icon: Upload,
              title: "Upload Resume",
              desc: "Upload your resume and we'll identify your skills, experience level, and areas of expertise automatically.",
              step: "2",
            },
            {
              icon: Sparkles,
              title: "Get Matched",
              desc: "We rank every job by how well it fits your background. See your personalized match score for each position.",
              step: "3",
            },
          ].map(({ icon: Icon, title, desc, step }) => (
            <div
              key={step}
              className="relative bg-card-bg border border-border rounded-2xl p-6 hover:shadow-lg hover:border-primary/30 transition-all"
            >
              <div className="absolute -top-3 -left-3 w-8 h-8 rounded-full bg-primary text-white text-sm font-bold flex items-center justify-center shadow-lg">
                {step}
              </div>
              <div className="w-12 h-12 rounded-2xl bg-primary/10 flex items-center justify-center mb-4">
                <Icon className="w-6 h-6 text-primary" />
              </div>
              <h3 className="text-lg font-semibold text-foreground mb-2">{title}</h3>
              <p className="text-sm text-muted leading-relaxed">{desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Featured Jobs */}
      <FeaturedJobs />

      {/* CTA */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="bg-gradient-to-br from-primary to-accent rounded-2xl p-8 sm:p-12 text-center text-white">
          <h2 className="text-2xl sm:text-3xl font-bold mb-3">
            Ready to find your match?
          </h2>
          <p className="text-white/80 max-w-lg mx-auto mb-6">
            Upload your resume to get personalized job recommendations powered by
            AI, or browse all open positions.
          </p>
          <Link
            href="/jobs"
            className="inline-flex items-center gap-2 px-8 py-3 bg-white text-primary rounded-xl font-medium hover:bg-white/90 transition-all shadow-lg"
          >
            Get Started
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </section>
    </div>
  );
}
