export interface Job {
  id: string;
  title: string;
  company: string;
  department: string;
  location: string;
  type: "Full-time" | "Part-time" | "Contract" | "Internship";
  level: "Intern" | "Entry" | "Mid" | "Senior" | "Lead" | "Manager" | "Director" | "VP" | "C-Suite";
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
  remote: boolean;
}

export interface MatchResult {
  job: Job;
  score: number;
  reason: string;
}

export interface ResumeData {
  text: string;
  fileName: string;
}

export type SortOption = "relevance" | "date" | "salary-high" | "salary-low";

export interface FilterState {
  search: string;
  department: string;
  level: string;
  type: string;
  location: string;
  remote: boolean | null;
}
