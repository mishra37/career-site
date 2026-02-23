export interface Job {
  id: string;
  title: string;
  company: string;
  department: string;
  industry: string;
  location: string;
  type: "Full-time" | "Part-time" | "Contract" | "Internship";
  level: "Intern" | "Entry" | "Mid" | "Senior" | "Lead" | "Manager" | "Director" | "VP" | "C-Suite";
  remoteType: "On-site" | "Remote" | "Hybrid";
  salary: {
    min: number;
    max: number;
    currency: string;
  };
  description: string;
  requirements: string[];
  responsibilities: string[];
  skills: string[];
  postedDate: string;
  visaSponsorship: boolean;
  yearsExperienceMin: number | null;
  yearsExperienceMax: number | null;
  recruiterName: string | null;
  recruiterRole: string | null;
  recruiterEmail: string | null;
  companySize: string | null;
}

export interface MatchResult {
  job: Job;
  score: number;
  reason: string;
}

export interface ExtractedKeywords {
  skills: string[];
  experienceLevel: string | null;
  yearsOfExperience: number | null;
  education: string[];
  domains: string[];
}

export interface ResumeData {
  text: string;
  fileName: string;
}

export type SortOption = "relevance" | "date" | "salary-high" | "salary-low";

export interface FilterState {
  search: string;
  location: string;
  type: string;
  remoteType: string;
  visaSponsorship: boolean | null;
  postedWithin: string;
  yearsMin: string;
  yearsMax: string;
  salaryMin: string;
  salaryMax: string;
  sort: SortOption;
}

export function formatSalary(min: number, max: number): string {
  const fmt = (n: number) => {
    if (n >= 1000) return `$${(n / 1000).toFixed(0)}K`;
    return `$${n}`;
  };
  return `${fmt(min)} - ${fmt(max)}`;
}
