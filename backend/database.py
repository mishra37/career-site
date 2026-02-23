"""
SQLite database layer for CareerMatch.

Provides connection management, schema initialization, and CRUD helpers.
Uses Python's built-in sqlite3 module — no external ORM needed for ~1000 jobs.
"""

from __future__ import annotations

import json
import os
import sqlite3
import uuid
from datetime import date, timedelta
from pathlib import Path
from typing import Any

# Default database path — next to this file in data/
DB_PATH = os.environ.get(
    "DATABASE_PATH",
    str(Path(__file__).resolve().parent.parent / "data" / "career_site.db"),
)

# ── Connection ────────────────────────────────────────────

_connection: sqlite3.Connection | None = None


def get_db(db_path: str | None = None) -> sqlite3.Connection:
    """Return the singleton database connection (creates it if needed)."""
    global _connection
    if _connection is None:
        path = db_path or DB_PATH
        os.makedirs(os.path.dirname(path), exist_ok=True)
        _connection = sqlite3.connect(path, check_same_thread=False)
        _connection.row_factory = sqlite3.Row
        _connection.execute("PRAGMA journal_mode=WAL")
        _connection.execute("PRAGMA foreign_keys=ON")
    return _connection


def set_db(conn: sqlite3.Connection) -> None:
    """Override the global connection (used by tests)."""
    global _connection
    _connection = conn


def close_db() -> None:
    """Close the database connection."""
    global _connection
    if _connection is not None:
        _connection.close()
        _connection = None


# ── Schema ────────────────────────────────────────────────

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS jobs (
    id                    TEXT PRIMARY KEY,
    title                 TEXT NOT NULL,
    company               TEXT NOT NULL,
    department            TEXT NOT NULL,
    industry              TEXT NOT NULL DEFAULT '',
    location              TEXT NOT NULL,
    type                  TEXT NOT NULL,
    level                 TEXT NOT NULL,
    remote_type           TEXT NOT NULL DEFAULT 'On-site',
    salary_min            INTEGER,
    salary_max            INTEGER,
    salary_currency       TEXT NOT NULL DEFAULT 'USD',
    description           TEXT NOT NULL,
    requirements          TEXT NOT NULL,
    responsibilities      TEXT NOT NULL,
    skills                TEXT NOT NULL,
    posted_date           TEXT NOT NULL,
    visa_sponsorship      INTEGER NOT NULL DEFAULT 0,
    years_experience_min  INTEGER,
    years_experience_max  INTEGER,
    recruiter_name        TEXT,
    recruiter_role        TEXT,
    recruiter_email       TEXT,
    company_size          TEXT,
    created_at            TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_jobs_department ON jobs(department);
CREATE INDEX IF NOT EXISTS idx_jobs_level ON jobs(level);
CREATE INDEX IF NOT EXISTS idx_jobs_type ON jobs(type);
CREATE INDEX IF NOT EXISTS idx_jobs_remote_type ON jobs(remote_type);
CREATE INDEX IF NOT EXISTS idx_jobs_posted_date ON jobs(posted_date);
CREATE INDEX IF NOT EXISTS idx_jobs_visa ON jobs(visa_sponsorship);
"""


def init_db(conn: sqlite3.Connection | None = None) -> None:
    """Create tables and indexes if they don't exist."""
    db = conn or get_db()
    db.executescript(SCHEMA_SQL)
    db.commit()


# ── Insert ────────────────────────────────────────────────


def insert_job(data: dict[str, Any], conn: sqlite3.Connection | None = None) -> dict:
    """Insert a job into the database. Returns the inserted row as a dict."""
    db = conn or get_db()
    job_id = data.get("id") or str(uuid.uuid4())

    db.execute(
        """
        INSERT INTO jobs (
            id, title, company, department, industry, location, type, level,
            remote_type, salary_min, salary_max, salary_currency,
            description, requirements, responsibilities, skills,
            posted_date, visa_sponsorship,
            years_experience_min, years_experience_max,
            recruiter_name, recruiter_role, recruiter_email,
            company_size
        ) VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?,
            ?, ?, ?, ?,
            ?, ?,
            ?, ?,
            ?, ?, ?,
            ?
        )
        """,
        (
            job_id,
            data["title"],
            data["company"],
            data["department"],
            data.get("industry", ""),
            data["location"],
            data["type"],
            data["level"],
            data.get("remote_type", "On-site"),
            data.get("salary_min"),
            data.get("salary_max"),
            data.get("salary_currency", "USD"),
            data["description"],
            json.dumps(data.get("requirements", [])),
            json.dumps(data.get("responsibilities", [])),
            json.dumps(data.get("skills", [])),
            data["posted_date"],
            1 if data.get("visa_sponsorship") else 0,
            data.get("years_experience_min"),
            data.get("years_experience_max"),
            data.get("recruiter_name"),
            data.get("recruiter_role"),
            data.get("recruiter_email"),
            data.get("company_size"),
        ),
    )
    db.commit()
    return get_job_by_id(job_id, conn=db)  # type: ignore[return-value]


# ── Read ──────────────────────────────────────────────────


def _row_to_dict(row: sqlite3.Row) -> dict:
    """Convert a sqlite3.Row to a plain dict with parsed JSON arrays."""
    d = dict(row)
    for field in ("requirements", "responsibilities", "skills"):
        if isinstance(d.get(field), str):
            d[field] = json.loads(d[field])
    d["visa_sponsorship"] = bool(d.get("visa_sponsorship"))
    return d


def get_job_by_id(
    job_id: str, conn: sqlite3.Connection | None = None
) -> dict | None:
    """Return a single job by ID, or None."""
    db = conn or get_db()
    row = db.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    if row is None:
        return None
    return _row_to_dict(row)


def get_jobs(
    *,
    q: str | None = None,
    location: str | None = None,
    department: str | None = None,
    level: str | None = None,
    job_type: str | None = None,
    remote_type: str | None = None,
    visa_sponsorship: bool | None = None,
    years_min: int | None = None,
    years_max: int | None = None,
    salary_min: int | None = None,
    salary_max: int | None = None,
    posted_within: str | None = None,
    sort: str | None = None,
    page: int = 1,
    page_size: int = 12,
    conn: sqlite3.Connection | None = None,
) -> dict:
    """
    Query jobs with filters, search, sort, and pagination.

    Returns: {jobs, total, page, totalPages, departments, levels, locations,
              types, remoteTypes, industries}
    """
    db = conn or get_db()

    conditions: list[str] = []
    params: list[Any] = []

    # ── Filters ───────────────────────────────────────────
    if department:
        conditions.append("department = ?")
        params.append(department)
    if level:
        conditions.append("level = ?")
        params.append(level)
    if job_type:
        conditions.append("type = ?")
        params.append(job_type)
    if remote_type:
        conditions.append("remote_type = ?")
        params.append(remote_type)
    if visa_sponsorship is not None:
        conditions.append("visa_sponsorship = ?")
        params.append(1 if visa_sponsorship else 0)
    if location:
        conditions.append("location LIKE ?")
        params.append(f"%{location}%")
    if salary_min is not None:
        conditions.append("salary_max >= ?")
        params.append(salary_min)
    if salary_max is not None:
        conditions.append("salary_min <= ?")
        params.append(salary_max)
    if years_min is not None:
        conditions.append("(years_experience_min IS NULL OR years_experience_min <= ?)")
        params.append(years_min)
    if years_max is not None:
        conditions.append("(years_experience_max IS NULL OR years_experience_max >= ?)")
        params.append(years_max)
    if posted_within:
        today = date.today()
        delta_map = {
            "24h": timedelta(days=1),
            "7d": timedelta(days=7),
            "30d": timedelta(days=30),
        }
        delta = delta_map.get(posted_within)
        if delta:
            cutoff = (today - delta).isoformat()
            conditions.append("posted_date >= ?")
            params.append(cutoff)

    # ── Text search (match each word independently) ──────
    if q:
        words = q.lower().split()
        for word in words:
            word_like = f"%{word}%"
            conditions.append(
                "(LOWER(title) LIKE ? OR LOWER(description) LIKE ? "
                "OR LOWER(skills) LIKE ? OR LOWER(company) LIKE ? "
                "OR LOWER(location) LIKE ? OR LOWER(department) LIKE ?)"
            )
            params.extend([word_like] * 6)

    where = " WHERE " + " AND ".join(conditions) if conditions else ""

    # ── Count total ───────────────────────────────────────
    total = db.execute(f"SELECT COUNT(*) FROM jobs{where}", params).fetchone()[0]

    # ── Sort ──────────────────────────────────────────────
    order_clause = "ORDER BY posted_date DESC"  # default
    if sort == "date":
        order_clause = "ORDER BY posted_date DESC"
    elif sort == "salary-high":
        order_clause = "ORDER BY salary_max DESC"
    elif sort == "salary-low":
        order_clause = "ORDER BY salary_min ASC"
    # "relevance" is handled by TF-IDF reranking in main.py

    # ── Paginate ──────────────────────────────────────────
    total_pages = max(1, -(-total // page_size))
    offset = (page - 1) * page_size

    rows = db.execute(
        f"SELECT * FROM jobs{where} {order_clause} LIMIT ? OFFSET ?",
        params + [page_size, offset],
    ).fetchall()

    jobs = [_row_to_dict(r) for r in rows]

    # ── Facets (distinct values for filter dropdowns) ─────
    facets = get_facets(conn=db)

    return {
        "jobs": jobs,
        "total": total,
        "page": page,
        "totalPages": total_pages,
        **facets,
    }


def get_all_jobs_raw(conn: sqlite3.Connection | None = None) -> list[dict]:
    """Return all jobs as dicts (used for building TF-IDF index)."""
    db = conn or get_db()
    rows = db.execute("SELECT * FROM jobs ORDER BY posted_date DESC").fetchall()
    return [_row_to_dict(r) for r in rows]


def get_facets(conn: sqlite3.Connection | None = None) -> dict:
    """Return distinct values for each filter dimension."""
    db = conn or get_db()
    return {
        "departments": _distinct(db, "department"),
        "levels": _distinct(db, "level"),
        "locations": _distinct(db, "location"),
        "types": _distinct(db, "type"),
        "remoteTypes": _distinct(db, "remote_type"),
        "industries": _distinct(db, "industry"),
    }


def _distinct(db: sqlite3.Connection, column: str) -> list[str]:
    """Return sorted distinct non-empty values for a column."""
    rows = db.execute(
        f"SELECT DISTINCT {column} FROM jobs WHERE {column} != '' ORDER BY {column}"
    ).fetchall()
    return [r[0] for r in rows]


def get_job_count(conn: sqlite3.Connection | None = None) -> int:
    """Return total number of jobs."""
    db = conn or get_db()
    return db.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
