"""
CareerMatch API — FastAPI backend.

Endpoints
---------
GET  /api/jobs          Paginated job listing with search + filters + TF-IDF ranking.
GET  /api/jobs/{id}     Single job by ID.
POST /api/match         Upload a resume → extract keywords → TF-IDF + keyword match.
POST /api/admin/jobs    Admin: create a new job posting (requires X-Admin-Key header).

Run with:
    cd backend && uvicorn main:app --reload --port 8000
"""

from __future__ import annotations

import io
import os
from contextlib import asynccontextmanager
from typing import Optional

import pdfplumber
from fastapi import FastAPI, File, Header, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from database import get_all_jobs_raw, get_job_by_id as db_get_job, get_job_count, get_jobs, init_db, insert_job
from jobs_data import _dict_to_job
from keyword_extractor import KeywordExtractor
from keyword_matcher import KeywordMatcher
from models import CreateJobRequest, JobsResponse, MatchResponse
from tfidf_index import tfidf_index

# ── Admin API key (set via environment variable) ──────────
ADMIN_API_KEY = os.environ.get("ADMIN_API_KEY", "dev-admin-key")


# ── Lifespan: init DB + build TF-IDF on startup ──────────
@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Startup
    init_db()
    # Auto-seed if database is empty (e.g., first deploy on Render)
    if get_job_count() == 0:
        from seed_data import seed_database
        seed_database(reset=False)
    _rebuild_tfidf()
    yield
    # Shutdown (nothing to clean up)


app = FastAPI(
    title="CareerMatch API",
    description="Personalized career site backend — Decimal AI take-home",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

extractor = KeywordExtractor()
matcher = KeywordMatcher()


def _rebuild_tfidf() -> None:
    """Build (or rebuild) the TF-IDF index from all jobs in SQLite."""
    all_jobs = get_all_jobs_raw()
    tfidf_index.build(all_jobs)


# ── Health check (for Render) ─────────────────────────────


@app.get("/api/health")
async def health_check():
    return {"status": "ok"}


# ── GET /api/jobs ─────────────────────────────────────────


@app.get("/api/jobs", response_model=JobsResponse)
async def list_jobs(
    q: Optional[str] = Query(None),
    search: Optional[str] = Query(None),          # alias for q (backwards compat)
    department: Optional[str] = Query(None),
    level: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    remoteType: Optional[str] = Query(None),       # noqa: N803
    visaSponsorship: Optional[bool] = Query(None),  # noqa: N803
    yearsMin: Optional[int] = Query(None, ge=0),   # noqa: N803
    yearsMax: Optional[int] = Query(None, ge=0),   # noqa: N803
    postedWithin: Optional[str] = Query(None),     # noqa: N803 — "24h", "7d", "30d"
    salaryMin: Optional[int] = Query(None, ge=0),  # noqa: N803
    salaryMax: Optional[int] = Query(None, ge=0),  # noqa: N803
    page: int = Query(1, ge=1),
    pageSize: int = Query(12, ge=1, le=100),       # noqa: N803
    sort: Optional[str] = Query(None),
):
    query_text = q or search or None

    # TF-IDF relevance sorting: if user searches and wants relevance,
    # fetch IDs ranked by TF-IDF, then paginate from that order.
    if query_text and sort in (None, "relevance"):
        tfidf_results = tfidf_index.search(query_text, top_n=500)
        if tfidf_results:
            # Use TF-IDF ranked order — pass through SQL filters
            result = get_jobs(
                q=query_text,
                location=location,
                department=department,
                level=level,
                job_type=type,
                remote_type=remoteType,
                visa_sponsorship=visaSponsorship,
                years_min=yearsMin,
                years_max=yearsMax,
                salary_min=salaryMin,
                salary_max=salaryMax,
                posted_within=postedWithin,
                sort=sort,
                page=page,
                page_size=pageSize,
            )
            # Re-rank jobs on this page by TF-IDF score
            tfidf_map = {jid: score for jid, score in tfidf_results}
            result["jobs"] = sorted(
                result["jobs"],
                key=lambda j: tfidf_map.get(j["id"], 0),
                reverse=True,
            )
            return _build_jobs_response(result)

    # Default: SQL-based filtering + sorting
    result = get_jobs(
        q=query_text,
        location=location,
        department=department,
        level=level,
        job_type=type,
        remote_type=remoteType,
        visa_sponsorship=visaSponsorship,
        years_min=yearsMin,
        years_max=yearsMax,
        salary_min=salaryMin,
        salary_max=salaryMax,
        posted_within=postedWithin,
        sort=sort or "date",
        page=page,
        page_size=pageSize,
    )
    return _build_jobs_response(result)


def _build_jobs_response(result: dict) -> JobsResponse:
    """Convert database result dict into a JobsResponse model."""
    jobs = [_dict_to_job(j) for j in result["jobs"]]
    return JobsResponse(
        jobs=jobs,
        total=result["total"],
        page=result["page"],
        total_pages=result["totalPages"],
        departments=result.get("departments", []),
        levels=result.get("levels", []),
        locations=result.get("locations", []),
        types=result.get("types", []),
        remote_types=result.get("remoteTypes", []),
        industries=result.get("industries", []),
    )


# ── GET /api/jobs/{id} ───────────────────────────────────


@app.get("/api/jobs/{job_id}")
async def get_job(job_id: str):
    row = db_get_job(job_id)
    if not row:
        raise HTTPException(status_code=404, detail="Job not found")
    job = _dict_to_job(row)
    return job.model_dump(by_alias=True)


# ── POST /api/match ───────────────────────────────────────


@app.post("/api/match", response_model=MatchResponse)
async def match_resume(
    resume: UploadFile = File(...),
):
    # ── 1. Extract text from the uploaded file ─────────────
    content = await resume.read()
    filename = (resume.filename or "").lower()
    content_type = resume.content_type or ""

    resume_text = ""

    if "pdf" in content_type or filename.endswith(".pdf"):
        try:
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                pages = [p.extract_text() or "" for p in pdf.pages]
                resume_text = "\n".join(pages)
        except Exception:
            raise HTTPException(
                status_code=400,
                detail="Could not parse PDF. Please try a different file.",
            )
    elif (
        "text" in content_type
        or filename.endswith(".txt")
        or filename.endswith(".md")
    ):
        resume_text = content.decode("utf-8", errors="replace")
    else:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Please upload a PDF or TXT file.",
        )

    if not resume_text.strip():
        raise HTTPException(
            status_code=400,
            detail="Could not extract text from resume. Please try a different file.",
        )

    # ── 2. Extract keywords ────────────────────────────────
    keywords = extractor.extract(resume_text)

    # ── 3. TF-IDF scoring ─────────────────────────────────
    tfidf_scores = tfidf_index.score_resume(resume_text)

    # ── 4. Load all jobs and match ─────────────────────────
    from jobs_data import load_jobs
    jobs = load_jobs()
    matches = matcher.match(keywords, jobs, tfidf_scores)

    return MatchResponse(
        matches=matches,
        resume_summary=resume_text[:500],
        total_matched=len(matches),
        extracted_keywords=keywords,
    )


# ── POST /api/admin/jobs ─────────────────────────────────


@app.post("/api/admin/jobs")
async def create_job(
    body: CreateJobRequest,
    x_admin_key: Optional[str] = Header(None),
):
    if x_admin_key != ADMIN_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing admin API key")

    from datetime import date as dt_date

    data = {
        "title": body.title,
        "company": body.company,
        "department": body.department,
        "industry": body.industry,
        "location": body.location,
        "type": body.type,
        "level": body.level,
        "remote_type": body.remote_type,
        "salary_min": body.salary.min,
        "salary_max": body.salary.max,
        "salary_currency": body.salary.currency,
        "description": body.description,
        "requirements": body.requirements,
        "responsibilities": body.responsibilities,
        "skills": body.skills,
        "posted_date": body.posted_date or dt_date.today().isoformat(),
        "visa_sponsorship": body.visa_sponsorship,
        "years_experience_min": body.years_experience_min,
        "years_experience_max": body.years_experience_max,
        "recruiter_name": body.recruiter_name,
        "recruiter_role": body.recruiter_role,
        "recruiter_email": body.recruiter_email,
        "company_size": body.company_size,
    }

    inserted = insert_job(data)

    # Rebuild TF-IDF index to include the new job
    _rebuild_tfidf()

    job = _dict_to_job(inserted)
    return job.model_dump(by_alias=True)
