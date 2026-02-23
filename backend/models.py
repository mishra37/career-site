"""
Pydantic models for the CareerMatch API.

All models use camelCase aliases for JSON serialization so the API response
format stays identical to what the Next.js frontend expects.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    """Base model that serializes field names to camelCase."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        serialize_by_alias=True,      # JSON output uses camelCase
    )


# ── Job Models ──────────────────────────────────────────────


class Salary(CamelModel):
    min: int
    max: int
    currency: str = "USD"


class Job(CamelModel):
    id: str
    title: str
    company: str
    department: str
    industry: str = ""
    location: str
    type: str
    level: str
    remote_type: str = "On-site"                    # "On-site" | "Remote" | "Hybrid"
    salary: Salary
    description: str
    requirements: list[str]
    responsibilities: list[str]
    skills: list[str]
    posted_date: str
    visa_sponsorship: bool = False
    years_experience_min: int | None = None
    years_experience_max: int | None = None
    recruiter_name: str | None = None
    recruiter_role: str | None = None
    recruiter_email: str | None = None
    company_size: str | None = None


class CreateJobRequest(CamelModel):
    """Request body for POST /api/admin/jobs."""
    title: str
    company: str
    department: str
    industry: str = ""
    location: str
    type: str
    level: str
    remote_type: str = "On-site"
    salary: Salary
    description: str
    requirements: list[str] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    posted_date: str | None = None                  # defaults to today
    visa_sponsorship: bool = False
    years_experience_min: int | None = None
    years_experience_max: int | None = None
    recruiter_name: str | None = None
    recruiter_role: str | None = None
    recruiter_email: str | None = None
    company_size: str | None = None


# ── Keyword Extraction Models ───────────────────────────────


class WorkEntry(CamelModel):
    """A single parsed work history entry."""

    title: str
    company: str | None = None
    duration_years: float | None = None


class ExtractedKeywords(CamelModel):
    """Structured keywords extracted from a resume."""

    skills: list[str]
    experience_level: str | None = None
    years_of_experience: int | None = None
    education: list[str] = []
    domains: list[str] = []
    # Enhanced fields
    work_history: list[WorkEntry] = []
    calculated_years: float | None = None
    role_categories: list[str] = []
    education_status: str | None = None
    graduation_proximity: str | None = None


# ── API Response Models ─────────────────────────────────────


class JobsResponse(CamelModel):
    jobs: list[Job]
    total: int
    page: int
    total_pages: int
    departments: list[str]
    levels: list[str]
    locations: list[str]
    types: list[str]
    remote_types: list[str] = []
    industries: list[str] = []


class MatchResult(CamelModel):
    job: Job
    score: int
    reason: str


class MatchResponse(CamelModel):
    matches: list[MatchResult]
    resume_summary: str
    total_matched: int
    extracted_keywords: ExtractedKeywords
