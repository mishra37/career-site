"""Integration tests for the CareerMatch API endpoints."""

from __future__ import annotations

import sqlite3
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from database import init_db, set_db, insert_job
from tests.conftest import SAMPLE_JOBS


@pytest.fixture(scope="module")
def client():
    """Create a test client with an in-memory database.

    We patch the lifespan's init_db and _rebuild_tfidf since the DB is already
    set up before the TestClient starts (avoids cross-thread SQLite errors).
    """
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    set_db(conn)
    init_db(conn)
    for job in SAMPLE_JOBS:
        insert_job(job, conn=conn)

    from main import app, _rebuild_tfidf
    _rebuild_tfidf()

    # Patch lifespan's init_db so it doesn't re-init on a different thread
    with patch("main.init_db"), patch("main._rebuild_tfidf"):
        with TestClient(app) as c:
            yield c
    conn.close()


class TestListJobs:
    def test_get_jobs_default(self, client):
        resp = client.get("/api/jobs")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == len(SAMPLE_JOBS)
        assert len(data["jobs"]) <= 12
        assert "departments" in data
        assert "levels" in data

    def test_get_jobs_pagination(self, client):
        resp = client.get("/api/jobs?pageSize=3&page=2")
        assert resp.status_code == 200
        data = resp.json()
        assert data["page"] == 2
        assert len(data["jobs"]) == 3

    def test_get_jobs_with_search(self, client):
        resp = client.get("/api/jobs?q=python")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] > 0

    def test_get_jobs_filter_remote(self, client):
        resp = client.get("/api/jobs?remoteType=Remote")
        assert resp.status_code == 200
        data = resp.json()
        for job in data["jobs"]:
            assert job["remoteType"] == "Remote"

    def test_get_jobs_filter_visa(self, client):
        resp = client.get("/api/jobs?visaSponsorship=true")
        assert resp.status_code == 200
        data = resp.json()
        for job in data["jobs"]:
            assert job["visaSponsorship"] is True

    def test_get_jobs_filter_type(self, client):
        resp = client.get("/api/jobs?type=Part-time")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["jobs"][0]["type"] == "Part-time"

    def test_get_jobs_sort_salary_high(self, client):
        resp = client.get("/api/jobs?sort=salary-high&pageSize=100")
        assert resp.status_code == 200
        data = resp.json()
        salaries = [j["salary"]["max"] for j in data["jobs"]]
        assert salaries == sorted(salaries, reverse=True)

    def test_get_jobs_sort_salary_low(self, client):
        resp = client.get("/api/jobs?sort=salary-low&pageSize=100")
        assert resp.status_code == 200
        data = resp.json()
        salaries = [j["salary"]["min"] for j in data["jobs"]]
        assert salaries == sorted(salaries)


class TestJobDetail:
    def test_get_job_by_id(self, client):
        resp = client.get("/api/jobs/job-1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "Senior Software Engineer"
        assert data["visaSponsorship"] is True
        assert data["remoteType"] == "Remote"
        assert data["recruiterName"] == "Jane Doe"

    def test_get_job_not_found(self, client):
        resp = client.get("/api/jobs/nonexistent-id")
        assert resp.status_code == 404


class TestAdminCreateJob:
    def test_create_job_success(self, client):
        resp = client.post(
            "/api/admin/jobs",
            json={
                "title": "New Engineer",
                "company": "NewCo",
                "department": "Engineering",
                "location": "Remote",
                "type": "Full-time",
                "level": "Mid",
                "salary": {"min": 100000, "max": 150000},
                "description": "A new engineering role",
                "skills": ["Go", "Rust"],
            },
            headers={"X-Admin-Key": "dev-admin-key"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "New Engineer"
        assert data["id"]

    def test_create_job_unauthorized(self, client):
        resp = client.post(
            "/api/admin/jobs",
            json={
                "title": "Hacker",
                "company": "X",
                "department": "Y",
                "location": "Z",
                "type": "Full-time",
                "level": "Mid",
                "salary": {"min": 1, "max": 2},
                "description": "test",
            },
        )
        assert resp.status_code == 401

    def test_create_job_wrong_key(self, client):
        resp = client.post(
            "/api/admin/jobs",
            json={
                "title": "Hacker",
                "company": "X",
                "department": "Y",
                "location": "Z",
                "type": "Full-time",
                "level": "Mid",
                "salary": {"min": 1, "max": 2},
                "description": "test",
            },
            headers={"X-Admin-Key": "wrong-key"},
        )
        assert resp.status_code == 401


class TestResumeMatch:
    def test_match_txt_resume(self, client):
        resume_content = (
            "Senior Python developer with 6 years experience in React, AWS, "
            "Docker, and machine learning. Master's in Computer Science."
        )
        resp = client.post(
            "/api/match",
            files={"resume": ("resume.txt", resume_content.encode(), "text/plain")},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["totalMatched"] > 0
        assert len(data["matches"]) > 0
        assert "extractedKeywords" in data
        # Top match should be an engineering role
        top_dept = data["matches"][0]["job"]["department"]
        assert top_dept in ("Engineering", "AI & Data Science")

    def test_match_unsupported_file(self, client):
        resp = client.post(
            "/api/match",
            files={"resume": ("photo.jpg", b"fake image data", "image/jpeg")},
        )
        assert resp.status_code == 400

    def test_match_empty_resume(self, client):
        resp = client.post(
            "/api/match",
            files={"resume": ("empty.txt", b"", "text/plain")},
        )
        assert resp.status_code == 400
