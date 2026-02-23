"""Shared fixtures for the CareerMatch backend test suite."""

from __future__ import annotations

import json
import sqlite3
from datetime import date, timedelta

import pytest

from database import init_db, set_db, insert_job


# ── Sample job data ───────────────────────────────────────

def _make_job(
    *,
    id: str,
    title: str,
    department: str = "Engineering",
    industry: str = "Technology",
    level: str = "Mid",
    skills: list[str] | None = None,
    remote_type: str = "On-site",
    visa_sponsorship: bool = False,
    salary_min: int = 80000,
    salary_max: int = 120000,
    posted_date: str | None = None,
    years_min: int | None = None,
    years_max: int | None = None,
    location: str = "San Francisco, CA",
    job_type: str = "Full-time",
    company: str = "TestCo",
) -> dict:
    return {
        "id": id,
        "title": title,
        "company": company,
        "department": department,
        "industry": industry,
        "location": location,
        "type": job_type,
        "level": level,
        "remote_type": remote_type,
        "salary_min": salary_min,
        "salary_max": salary_max,
        "salary_currency": "USD",
        "description": f"We are looking for a {title} to join our team.",
        "requirements": [f"Experience with {s}" for s in (skills or ["Python"])],
        "responsibilities": [f"Work on {department.lower()} projects"],
        "skills": skills or ["Python"],
        "posted_date": posted_date or date.today().isoformat(),
        "visa_sponsorship": visa_sponsorship,
        "years_experience_min": years_min,
        "years_experience_max": years_max,
        "recruiter_name": "Jane Doe",
        "recruiter_role": "Technical Recruiter",
        "recruiter_email": "jane@testco.com",
        "company_size": "201-1000",
    }


SAMPLE_JOBS = [
    _make_job(
        id="job-1",
        title="Senior Software Engineer",
        department="Engineering",
        industry="Technology",
        level="Senior",
        skills=["Python", "React", "AWS", "Docker", "PostgreSQL"],
        remote_type="Remote",
        visa_sponsorship=True,
        salary_min=150000,
        salary_max=220000,
        posted_date=date.today().isoformat(),
        years_min=5,
        years_max=10,
    ),
    _make_job(
        id="job-2",
        title="Junior Frontend Developer",
        department="Engineering",
        industry="Technology",
        level="Entry",
        skills=["JavaScript", "React", "CSS", "HTML", "TypeScript"],
        remote_type="Hybrid",
        salary_min=60000,
        salary_max=85000,
        posted_date=(date.today() - timedelta(days=3)).isoformat(),
    ),
    _make_job(
        id="job-3",
        title="Registered Nurse",
        department="Healthcare",
        industry="Healthcare",
        level="Mid",
        skills=["Patient Care", "Clinical Assessment", "Electronic Health Records"],
        location="New York, NY",
        salary_min=70000,
        salary_max=95000,
        posted_date=(date.today() - timedelta(days=10)).isoformat(),
    ),
    _make_job(
        id="job-4",
        title="Data Scientist",
        department="AI & Data Science",
        industry="Technology",
        level="Mid",
        skills=["Python", "Machine Learning", "TensorFlow", "SQL", "Statistics"],
        remote_type="Remote",
        visa_sponsorship=True,
        salary_min=120000,
        salary_max=180000,
        posted_date=(date.today() - timedelta(days=1)).isoformat(),
        years_min=3,
        years_max=6,
    ),
    _make_job(
        id="job-5",
        title="Marketing Manager",
        department="Marketing",
        industry="Marketing",
        level="Manager",
        skills=["SEO", "Content Strategy", "Google Analytics", "Social Media"],
        location="Austin, TX",
        salary_min=90000,
        salary_max=130000,
        posted_date=(date.today() - timedelta(days=45)).isoformat(),
    ),
    _make_job(
        id="job-6",
        title="DevOps Engineer",
        department="Engineering",
        industry="Technology",
        level="Senior",
        skills=["Docker", "Kubernetes", "AWS", "Terraform", "CI/CD", "Linux"],
        remote_type="Remote",
        salary_min=140000,
        salary_max=200000,
        posted_date=(date.today() - timedelta(days=5)).isoformat(),
        years_min=5,
    ),
    _make_job(
        id="job-7",
        title="Financial Analyst",
        department="Finance",
        industry="Finance",
        level="Entry",
        skills=["Excel", "Financial Modeling", "SQL", "Bloomberg Terminal"],
        location="Chicago, IL",
        job_type="Part-time",
        salary_min=55000,
        salary_max=75000,
        posted_date=(date.today() - timedelta(days=20)).isoformat(),
    ),
    _make_job(
        id="job-8",
        title="ML Engineer Intern",
        department="AI & Data Science",
        industry="Technology",
        level="Intern",
        skills=["Python", "PyTorch", "Machine Learning"],
        remote_type="Hybrid",
        visa_sponsorship=True,
        salary_min=40000,
        salary_max=60000,
        job_type="Internship",
        posted_date=date.today().isoformat(),
    ),
]


@pytest.fixture(scope="session")
def test_db():
    """Create an in-memory SQLite database with test jobs."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    set_db(conn)
    init_db(conn)
    for job in SAMPLE_JOBS:
        insert_job(job, conn=conn)
    yield conn
    conn.close()


@pytest.fixture()
def fresh_db():
    """Per-test in-memory database (clean slate)."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    set_db(conn)
    init_db(conn)
    yield conn
    conn.close()


SAMPLE_RESUME_TEXT = """
John Smith
Senior Software Engineer

Summary:
Experienced software engineer with 6+ years of professional experience
building scalable web applications. Expertise in Python, React, and cloud
infrastructure. Master's degree in Computer Science from MIT.

Experience:
- Senior Software Engineer at TechCorp (2020-present)
  Built microservices with Python and FastAPI, deployed on AWS using Docker
  and Kubernetes. Led a team of 5 engineers.
- Software Engineer at StartupXYZ (2018-2020)
  Developed React frontends, Node.js backends, and PostgreSQL databases.

Skills: Python, JavaScript, React, Node.js, AWS, Docker, Kubernetes,
PostgreSQL, FastAPI, CI/CD, Git, Agile, Machine Learning, TensorFlow

Education: M.S. Computer Science, MIT
"""
