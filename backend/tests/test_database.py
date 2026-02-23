"""Tests for the SQLite database layer."""

from __future__ import annotations

from datetime import date, timedelta

from database import get_job_by_id, get_jobs, get_all_jobs_raw, insert_job, get_job_count
from tests.conftest import SAMPLE_JOBS


class TestSchema:
    def test_init_db_creates_tables(self, test_db):
        tables = test_db.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        table_names = [t[0] for t in tables]
        assert "jobs" in table_names

    def test_job_count(self, test_db):
        assert get_job_count(conn=test_db) == len(SAMPLE_JOBS)


class TestInsertAndRetrieve:
    def test_insert_job(self, fresh_db):
        data = {
            "title": "Test Role",
            "company": "TestCo",
            "department": "Eng",
            "location": "Remote",
            "type": "Full-time",
            "level": "Mid",
            "salary_min": 100000,
            "salary_max": 150000,
            "salary_currency": "USD",
            "description": "A test job",
            "requirements": ["Req 1"],
            "responsibilities": ["Resp 1"],
            "skills": ["Python"],
            "posted_date": date.today().isoformat(),
        }
        result = insert_job(data, conn=fresh_db)
        assert result is not None
        assert result["title"] == "Test Role"
        assert result["id"]  # auto-generated

    def test_get_job_by_id(self, test_db):
        job = get_job_by_id("job-1", conn=test_db)
        assert job is not None
        assert job["title"] == "Senior Software Engineer"
        assert job["skills"] == ["Python", "React", "AWS", "Docker", "PostgreSQL"]

    def test_get_job_not_found(self, test_db):
        assert get_job_by_id("nonexistent", conn=test_db) is None


class TestFilters:
    def test_get_all_jobs_no_filters(self, test_db):
        result = get_jobs(page_size=100, conn=test_db)
        assert result["total"] == len(SAMPLE_JOBS)
        assert len(result["jobs"]) == len(SAMPLE_JOBS)

    def test_filter_by_type(self, test_db):
        result = get_jobs(job_type="Part-time", conn=test_db)
        assert result["total"] == 1
        assert result["jobs"][0]["title"] == "Financial Analyst"

    def test_filter_by_remote_type(self, test_db):
        result = get_jobs(remote_type="Remote", page_size=100, conn=test_db)
        assert result["total"] == 3  # job-1, job-4, job-6

    def test_filter_by_visa_sponsorship(self, test_db):
        result = get_jobs(visa_sponsorship=True, page_size=100, conn=test_db)
        assert result["total"] == 3  # job-1, job-4, job-8

    def test_filter_by_salary_range(self, test_db):
        result = get_jobs(salary_min=100000, page_size=100, conn=test_db)
        # Jobs where salary_max >= 100000
        assert all(j["salary_max"] >= 100000 for j in result["jobs"])

    def test_filter_by_level(self, test_db):
        result = get_jobs(level="Senior", page_size=100, conn=test_db)
        assert result["total"] == 2  # job-1, job-6

    def test_filter_by_department(self, test_db):
        result = get_jobs(department="Engineering", page_size=100, conn=test_db)
        assert result["total"] == 3  # job-1, job-2, job-6

    def test_filter_by_posted_within_7d(self, test_db):
        result = get_jobs(posted_within="7d", page_size=100, conn=test_db)
        cutoff = date.today() - timedelta(days=7)
        for j in result["jobs"]:
            assert date.fromisoformat(j["posted_date"]) >= cutoff

    def test_filter_multiple_combined(self, test_db):
        result = get_jobs(
            remote_type="Remote",
            visa_sponsorship=True,
            conn=test_db,
        )
        # job-1 (Senior SWE, remote, visa) and job-4 (Data Scientist, remote, visa)
        assert result["total"] == 2

    def test_text_search(self, test_db):
        result = get_jobs(q="python", conn=test_db)
        assert result["total"] > 0
        # Should find jobs with Python in skills or description

    def test_location_search(self, test_db):
        result = get_jobs(location="New York", conn=test_db)
        assert result["total"] == 1
        assert "New York" in result["jobs"][0]["location"]


class TestPagination:
    def test_pagination_defaults(self, test_db):
        result = get_jobs(page_size=3, conn=test_db)
        assert len(result["jobs"]) == 3
        assert result["total"] == len(SAMPLE_JOBS)
        assert result["page"] == 1
        assert result["totalPages"] == 3  # ceil(8/3)

    def test_pagination_page_2(self, test_db):
        result = get_jobs(page=2, page_size=3, conn=test_db)
        assert result["page"] == 2
        assert len(result["jobs"]) == 3


class TestFacets:
    def test_facets_included(self, test_db):
        result = get_jobs(conn=test_db)
        assert "departments" in result
        assert "levels" in result
        assert "locations" in result
        assert "types" in result
        assert "remoteTypes" in result

    def test_facets_values(self, test_db):
        result = get_jobs(conn=test_db)
        assert "Engineering" in result["departments"]
        assert "Senior" in result["levels"]
        assert "Remote" in result["remoteTypes"]
