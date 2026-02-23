# CareerMatch — AI-Powered Personalized Career Site

> Browse 9,900+ jobs, upload your resume, and get AI-powered personalized recommendations instantly. These jobs aren't real as they are synthetically generated using AI tools.

![Next.js](https://img.shields.io/badge/Next.js-16-black?logo=next.js)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi)
![TypeScript](https://img.shields.io/badge/TypeScript-5-blue?logo=typescript)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python)
![Tests](https://img.shields.io/badge/Tests-73_passing-brightgreen)

---

## Features

- **Browse & Search** — 9,900 synthetic jobs across 16 industries with keyword search, location search, filters (type, remote, visa, experience, salary, recency), sorting, and pagination
- **Resume Upload** — Drag-and-drop PDF/TXT upload via header modal or sidebar widget
- **AI Matching** — 6-signal scoring: TF-IDF similarity, skill match, title relevance, domain alignment, level proximity, role category match (100 pts max)
- **Smart Extraction** — Parses work history (titles, companies, durations), detects role categories (SWE, ML, Data Science, etc.), infers experience level from education status and years
- **Job Detail & Apply** — Full descriptions, requirements, skills, recruiter info, salary ranges, and application flow

---

## Architecture

```
┌────────────────────────────────────────────────┐
│  Vercel — Next.js 16, React 19, Tailwind v4   │
│  /  /jobs  /jobs/[id]  /jobs/[id]/apply        │
│  next.config.ts rewrites /api/* → backend      │
├────────────────────────────────────────────────┤
│  Render — FastAPI + Python                     │
│  GET /api/jobs · GET /api/jobs/{id}            │
│  POST /api/match · POST /api/admin/jobs        │
├────────────────────────────────────────────────┤
│  SQLite (WAL mode) — 9,900 jobs · 44 locations │
│  In-memory TF-IDF index (scikit-learn)         │
└────────────────────────────────────────────────┘
```

---

## Resume Matching

```
Upload PDF/TXT → Extract text (pdfplumber)
  ├─ KeywordExtractor: skills, work history, role categories,
  │  education status, experience level, domains
  ├─ TF-IDF cosine similarity (resume vs 9,900 job documents)
  └─ KeywordMatcher: 6-signal scoring → top 100 ranked matches
```

| Signal | Points | Description |
|--------|--------|-------------|
| TF-IDF similarity | 25 | Cosine similarity (title x4, dept x3, skills x2, desc x1) |
| Skill match | 35 | % of job skills found in resume |
| Title relevance | 5 | Resume skills appearing in job title |
| Domain alignment | 15 | Resume domain matches job department |
| Level proximity | 10 | Distance between inferred and job level |
| Role category | 10 | Work history roles match job type |

Cross-domain penalties: healthcare job + non-healthcare resume (x0.3), incompatible domains (x0.5). Level inference: student → intern/entry based on graduation proximity; work history years → mid/senior/lead; keyword fallback.

---

## Getting Started

```bash
# Clone & install
git clone https://github.com/mishra37/career-site.git
cd career-site && npm install
cd backend && pip install -r requirements.txt

# Seed database (9,900 jobs)
python3 seed_data.py --reset

# Run (two terminals)
uvicorn main:app --host 0.0.0.0 --port 8000   # Terminal 1: backend
cd .. && npm run dev                             # Terminal 2: frontend
```

Open **http://localhost:3000**. Backend auto-seeds if database is empty.

```bash
# Run tests (73 tests)
cd backend && python3 -m pytest tests/ -v
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 16, React 19, TypeScript, Tailwind CSS v4, Lucide React |
| Backend | FastAPI, Pydantic 2, scikit-learn TF-IDF, pdfplumber |
| Database | SQLite (WAL mode) |
| Testing | pytest, httpx (73 tests across 5 files) |
| Hosting | Vercel (frontend) + Render (backend) |

---

## Scaling Strategy

Phase 2 plan is still in progress!

| Scale | Tentative Strategy |
|-------|----------|
| **500** | Current approach works perfectly |
| **5,000** | Add SQLite FTS5, facet caching, background TF-IDF rebuild |
| **500,000** | PostgreSQL + Redis + retrieve-rerank pipeline + async matching |
| **5,000,000** | Elasticsearch cluster + vector embeddings + microservices |

---

## Credits

Claude Code has been used for coding part of this project.

---

## License

MIT
