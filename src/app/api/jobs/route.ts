import { NextRequest, NextResponse } from "next/server";
import { jobs, getDepartments, getLevels, getLocations, getTypes } from "@/lib/jobs-data";
import { Job, FilterState } from "@/lib/types";

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;

  const filters: FilterState = {
    search: searchParams.get("search") || "",
    department: searchParams.get("department") || "",
    level: searchParams.get("level") || "",
    type: searchParams.get("type") || "",
    location: searchParams.get("location") || "",
    remote: searchParams.get("remote") === "true" ? true : searchParams.get("remote") === "false" ? false : null,
  };

  const page = parseInt(searchParams.get("page") || "1");
  const pageSize = parseInt(searchParams.get("pageSize") || "12");
  const sort = searchParams.get("sort") || "date";

  let filtered = filterJobs(jobs, filters);
  filtered = sortJobs(filtered, sort);

  const total = filtered.length;
  const totalPages = Math.ceil(total / pageSize);
  const paginated = filtered.slice((page - 1) * pageSize, page * pageSize);

  return NextResponse.json({
    jobs: paginated,
    total,
    page,
    pageSize,
    totalPages,
    filters: {
      departments: getDepartments(),
      levels: getLevels(),
      locations: getLocations(),
      types: getTypes(),
    },
  });
}

function filterJobs(jobsList: Job[], filters: FilterState): Job[] {
  return jobsList.filter((job) => {
    if (filters.search) {
      const search = filters.search.toLowerCase();
      const matchesSearch =
        job.title.toLowerCase().includes(search) ||
        job.description.toLowerCase().includes(search) ||
        job.department.toLowerCase().includes(search) ||
        job.skills.some((s) => s.toLowerCase().includes(search)) ||
        job.location.toLowerCase().includes(search) ||
        job.company.toLowerCase().includes(search);
      if (!matchesSearch) return false;
    }

    if (filters.department && job.department !== filters.department) return false;
    if (filters.level && job.level !== filters.level) return false;
    if (filters.type && job.type !== filters.type) return false;
    if (filters.location && job.location !== filters.location) return false;
    if (filters.remote !== null && job.remote !== filters.remote) return false;

    return true;
  });
}

function sortJobs(jobsList: Job[], sort: string): Job[] {
  const sorted = [...jobsList];
  switch (sort) {
    case "date":
      return sorted.sort((a, b) => new Date(b.postedDate).getTime() - new Date(a.postedDate).getTime());
    case "salary-high":
      return sorted.sort((a, b) => b.salary.max - a.salary.max);
    case "salary-low":
      return sorted.sort((a, b) => a.salary.min - b.salary.min);
    default:
      return sorted;
  }
}
