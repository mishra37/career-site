"""
Job data access layer — reads from SQLite via database.py.

Provides Job model instances and helper functions for the API layer.
"""

from __future__ import annotations

from database import get_all_jobs_raw, get_facets, get_job_by_id as _db_get_job
from models import Job, Salary


def _dict_to_job(d: dict) -> Job:
    """Convert a database row dict into a Job Pydantic model."""
    return Job(
        id=d["id"],
        title=d["title"],
        company=d["company"],
        department=d["department"],
        industry=d.get("industry", ""),
        location=d["location"],
        type=d["type"],
        level=d["level"],
        remote_type=d.get("remote_type", "On-site"),
        salary=Salary(
            min=d.get("salary_min") or 0,
            max=d.get("salary_max") or 0,
            currency=d.get("salary_currency", "USD"),
        ),
        description=d["description"],
        requirements=d.get("requirements", []),
        responsibilities=d.get("responsibilities", []),
        skills=d.get("skills", []),
        posted_date=d["posted_date"],
        visa_sponsorship=d.get("visa_sponsorship", False),
        years_experience_min=d.get("years_experience_min"),
        years_experience_max=d.get("years_experience_max"),
        recruiter_name=d.get("recruiter_name"),
        recruiter_role=d.get("recruiter_role"),
        recruiter_email=d.get("recruiter_email"),
        company_size=d.get("company_size"),
    )


def load_jobs() -> list[Job]:
    """Load all jobs from SQLite as Job model instances."""
    rows = get_all_jobs_raw()
    return [_dict_to_job(r) for r in rows]


def get_job_by_id(job_id: str) -> Job | None:
    """Return a single Job by ID, or None."""
    row = _db_get_job(job_id)
    if row is None:
        return None
    return _dict_to_job(row)


def get_departments() -> list[str]:
    return get_facets().get("departments", [])


def get_levels() -> list[str]:
    return get_facets().get("levels", [])


def get_locations() -> list[str]:
    return get_facets().get("locations", [])


def get_types() -> list[str]:
    return get_facets().get("types", [])
