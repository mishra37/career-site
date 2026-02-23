# CareerMatch — AI-Powered Personalized Career Site

> Browse 9,900+ jobs, upload your resume, and get AI-powered personalized recommendations instantly. These jobs aren't real as they are synthetically generated using AI tools.

![Next.js](https://img.shields.io/badge/Next.js-16-black?logo=next.js)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi)
![TypeScript](https://img.shields.io/badge/TypeScript-5-blue?logo=typescript)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python)
![Tailwind CSS](https://img.shields.io/badge/Tailwind-v4-38bdf8?logo=tailwindcss)
![Tests](https://img.shields.io/badge/Tests-73_passing-brightgreen)

---

## Features

| Feature | Description |
|---------|-------------|
| **Browse Jobs** | 9,900 synthetic jobs across 16 industries with search, filters (type, remote, visa, experience, salary, recency), sorting, and pagination |
| **Resume Upload** | Drag-and-drop PDF/TXT upload via header modal or sidebar widget |
| **AI Matching** | 6-signal scoring engine: TF-IDF similarity, skill match, title relevance, domain alignment, level proximity, role category match |
| **Work History Parsing** | Extracts job titles, companies, and durations from resume experience sections |
| **Role Detection** | Maps work history to categories (SWE, ML, Data Science, Product, Design, Management) to prioritize relevant jobs |
| **Education Status** | Detects if candidate is pursuing a degree and infers intern/entry level based on graduation proximity |
| **Job Detail Pages** | Full descriptions, requirements, responsibilities, skills, recruiter info, and salary ranges |
| **Apply Flow** | Application form with name, email, phone, resume upload, and cover letter |
| **Dark Mode** | Automatic via `prefers-color-scheme` with consistent theming |
| **Responsive Design** | Mobile to desktop layout with loading skeletons |

---

## Architecture

```
┌──────────────────────────────────────────────────────┐
│  Vercel (Next.js 16, React 19, Tailwind CSS v4)     │
│                                                      │
│  /              Landing page + featured jobs          │
│  /jobs           Browse/search with filters           │
│  /jobs/[id]      Job detail                          │
│  /jobs/[id]/apply  Application flow                  │
│                                                      │
│  next.config.ts rewrites /api/* → backend            │
├──────────────────────────────────────────────────────┤
│  Render (FastAPI + Python)                           │
│                                                      │
│  GET  /api/health       Health check                 │
│  GET  /api/jobs         Paginated listing + search   │
│  GET  /api/jobs/{id}    Job detail                   │
│  POST /api/match        Resume upload → AI match     │
│  POST /api/admin/jobs   Create job (admin)           │
│                                                      │
│  Modules: database.py, models.py, jobs_data.py,      │
│  keyword_extractor.py, keyword_matcher.py,           │
│  tfidf_index.py, seed_data.py                        │
├──────────────────────────────────────────────────────┤
│  SQLite Database (data/career_site.db, WAL mode)     │
│  9,900 jobs · 16 industries · 44 locations           │
└──────────────────────────────────────────────────────┘
```

---

## Resume Matching — How It Works

### Pipeline

```
Upload PDF/TXT
      │
      ▼
Extract text (pdfplumber / UTF-8)
      │
      ├──► KeywordExtractor.extract(text)
      │     • Skills (200+ multi-word, 130+ single-word dictionary)
      │     • Work history (titles, companies, durations from Experience section)
      │     • Role categories (SWE, ML, Data Science, Product, Design, Management)
      │     • Education status (pursuing vs completed, graduation proximity)
      │     • Experience level (student → intern/entry, years → mid/senior/lead)
      │     • Domains (14 categories: engineering, healthcare, legal, etc.)
      │
      ├──► TF-IDF cosine similarity (resume vs all 9,900 job documents)
      │
      └──► KeywordMatcher.match() → scored + ranked top 100
```

### Scoring (100 points max)

| Signal | Points | How |
|--------|--------|-----|
| TF-IDF text similarity | 25 | Cosine similarity of resume vs job document (title x4, dept x3, skills x2, desc x1) |
| Skill match | 35 | % of job skills found in resume (exact match) |
| Title relevance | 5 | Resume skills appearing in job title |
| Domain alignment | 15 | Resume domain matches job department |
| Level proximity | 10 | Distance between inferred level and job level |
| Role category match | 10 | Work history roles match job type (SWE resume → SWE jobs) |

### Penalties (multiplicative)
- Healthcare job + non-healthcare resume → x0.3
- Cross-domain incompatibility (e.g., engineering resume vs design job) → x0.5

### Level Inference Priority
1. Student pursuing degree + no work experience → far from graduation = intern, near = entry
2. Calculated years from work history → `<1yr=intern, 1-2=entry, 2-4=mid, 5-7=senior, 8-10=lead, 11+=director`
3. Keyword-based detection fallback

### Example

Given a resume: "Software Engineer at Google (4 years), previously at Meta (1 year). Skills: Python, React, TypeScript, AWS, Kubernetes."

**Extracted:**
```json
{
  "skills": ["python", "react", "typescript", "aws", "kubernetes"],
  "workHistory": [
    {"title": "Software Engineer", "company": "Google", "durationYears": 4.0},
    {"title": "Software Engineer", "company": "Meta", "durationYears": 1.0}
  ],
  "roleCategories": ["swe"],
  "experienceLevel": "senior",
  "calculatedYears": 5.0,
  "domains": ["engineering"]
}
```

**Result:** Senior SWE/engineering jobs ranked highest. Non-tech jobs penalized. Intern/entry roles deprioritized due to level proximity scoring.

---

## Data

### Job Generation (seed_data.py)

- **16 industries**: Technology (2,500), Data Science & AI (1,000), Healthcare (800), Finance (600), Legal (600), Marketing (500), Sales (500), Operations (500), Education (400), Design (400), Manufacturing (400), Product (400), Hospitality (400), Real Estate (300), Media (300), HR (300)
- **9 experience levels**: Intern through C-Suite with weighted distribution
- **44 locations**: 20 US cities, 3 UK, 3 Canada, 4 India, 2 Australia, 3 Europe, 3 Asia-Pacific
- **Date distribution**: Shuffled across all industries for even recency distribution
- **9,900 total** jobs

### TF-IDF Index (tfidf_index.py)

- scikit-learn `TfidfVectorizer` with unigrams + bigrams, 8,000 max features
- Weighted documents: title x4, department x3, skills x2, description x1, requirements x1
- Built on server startup (~150ms for 10K jobs), queries in <5ms
- Supports keyword search (browse page) and resume scoring (match pipeline)

---

## Project Structure

```
career-site/
├── src/                          # Next.js frontend
│   ├── app/
│   │   ├── page.tsx              # Landing page
│   │   ├── layout.tsx            # Root layout + header/footer
│   │   ├── globals.css           # Tailwind + custom CSS vars
│   │   └── jobs/
│   │       ├── page.tsx          # Browse/search page
│   │       └── [id]/
│   │           ├── page.tsx      # Job detail
│   │           └── apply/page.tsx # Apply flow
│   ├── components/
│   │   ├── Header.tsx            # Sticky nav + "Match My Resume" button
│   │   ├── FilterSidebar.tsx     # All filter controls + years validation
│   │   ├── JobCard.tsx           # Job listing card with match score
│   │   ├── JobCardSkeleton.tsx   # Loading skeleton
│   │   ├── FeaturedJobs.tsx      # Landing page featured jobs
│   │   ├── ResumeUpload.tsx      # Drag-and-drop upload widget
│   │   ├── ResumeMatchModal.tsx  # Full-screen resume match overlay
│   │   ├── UploadResumeButton.tsx # CTA button for landing page
│   │   └── Providers.tsx         # React context providers
│   ├── contexts/
│   │   └── ResumeModalContext.tsx # Global resume modal state
│   └── lib/
│       └── types.ts              # TypeScript interfaces
│
├── backend/                      # FastAPI backend
│   ├── main.py                   # API routes + startup (auto-seeds if DB empty)
│   ├── database.py               # SQLite access layer (WAL mode, indexes)
│   ├── models.py                 # Pydantic models (Job, MatchResult, WorkEntry, etc.)
│   ├── jobs_data.py              # Job data access helpers
│   ├── keyword_extractor.py      # Resume → structured keywords + work history
│   ├── keyword_matcher.py        # Keywords + TF-IDF → scored matches
│   ├── tfidf_index.py            # TF-IDF vectorizer + search
│   ├── seed_data.py              # Generate 9,900 jobs
│   ├── requirements.txt          # Python dependencies
│   ├── runtime.txt               # Python version for Render (3.11.7)
│   └── tests/                    # 73 pytest tests
│       ├── conftest.py
│       ├── test_api.py           # 16 tests — all API endpoints
│       ├── test_database.py      # 18 tests — schema, CRUD, filtering
│       ├── test_keyword_extractor.py  # 22 tests — extraction logic
│       ├── test_keyword_matcher.py    # 12 tests — scoring engine
│       └── test_tfidf.py         # 5 tests — index + search
│
├── data/
│   ├── jobs.json                 # Original 50 seed jobs
│   └── career_site.db            # SQLite database (gitignored, auto-generated)
│
├── next.config.ts                # API proxy → backend (uses API_URL env var)
├── package.json
├── tsconfig.json
├── PHASE1_PLAN.md                # Phase 1 implementation details
├── PHASE2_PLAN.md                # Scaling architecture (500 → 5M jobs)
└── .gitignore
```

---

## Getting Started

### Prerequisites

- **Node.js** >= 18
- **Python** >= 3.10

### Installation

```bash
# Clone the repo
git clone https://github.com/mishra37/career-site.git
cd career-site

# Frontend dependencies
npm install

# Backend dependencies
cd backend
pip install -r requirements.txt
```

### Seed the Database

```bash
# Generate 9,900 jobs (run from backend/)
cd backend
python3 seed_data.py --reset
```

### Run the App

You need **two terminals**:

```bash
# Terminal 1: Start FastAPI backend (port 8000)
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000

# Terminal 2: Start Next.js frontend (port 3000)
npm run dev
```

Open **http://localhost:3000** to use the app.

> **Note:** If the database is empty on startup, the backend auto-seeds 9,900 jobs (useful for deployment).

### Run Tests

```bash
cd backend
python3 -m pytest tests/ -v
```

All 73 tests should pass.

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `API_URL` | No | `http://localhost:8000` | Backend URL (used by Next.js proxy in `next.config.ts`) |
| `DATABASE_PATH` | No | `data/career_site.db` | SQLite database file path |
| `ADMIN_API_KEY` | No | `dev-admin-key` | Admin API authentication key |

---

## Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Frontend | Next.js 16, React 19, TypeScript | App router, modern React |
| Styling | Tailwind CSS v4 | Utility-first, fast iteration |
| Icons | Lucide React | Lightweight, consistent icon set |
| Backend | FastAPI, Pydantic 2 | Fast async Python, auto-validation, OpenAPI docs |
| Database | SQLite (WAL mode) | Zero-config, single-file, great read concurrency |
| Search | scikit-learn TF-IDF | In-memory vectorized search, no external service |
| PDF Parsing | pdfplumber | Reliable server-side PDF text extraction |
| Testing | pytest, httpx | 73 backend tests across 5 test files |
| Hosting | Vercel (frontend) + Render (backend) | Decoupled deployment, free tier |

---

## Key Design Decisions

1. **Decoupled Frontend/Backend** — Next.js proxies `/api/*` to FastAPI via `rewrites()`. Frontend code uses relative paths (`/api/jobs`), backend runs as a standalone Python service. Either can be deployed independently.

2. **SQLite for Phase 1** — WAL mode provides excellent read concurrency with zero configuration. For a read-heavy job board with ~10K jobs, it outperforms PostgreSQL on single-machine latency (no network hop). The trade-off (single-writer) only matters at 50K+ jobs.

3. **TF-IDF over Embeddings** — For ~10K jobs, TF-IDF cosine similarity captures 80%+ of what embeddings would provide. No model serving, no embedding pipeline, no vector store needed. Semantic matching (e.g., "Data Scientist" matching "ML Engineer") is handled by role category detection instead.

4. **Multi-Signal Scoring** — Rather than relying on a single similarity metric, the matcher combines 6 weighted signals (TF-IDF, skills, title, domain, level, role category) with domain-specific penalties. This produces more intuitive results than any single signal alone.

5. **Client-Side Filtering for Match Results** — After matching, the top 100 results are sent to the client. Users can filter/sort these instantly without API round-trips. Server-side filtering is used for the full 9,900-job browse mode.

6. **Auto-Seed on Empty Database** — The backend detects an empty database on startup and runs `seed_data.py` automatically. This eliminates manual setup for deployments (Render, etc.).

---

## Scaling Strategy

Phase 2 plan is still in progress!

**Summary:**

| Scale | Tentative Strategy
|-------|----------
| **500 jobs** | Current approach works perfectly 
| **5,000 jobs** | Add SQLite FTS5, facet caching, background TF-IDF rebuild
| **500,000 jobs** | PostgreSQL + Redis + retrieve-rerank pipeline + async matching 
| **5,000,000 jobs** | Elasticsearch cluster + vector embeddings + microservices

**Current trade-offs:**
- SQLite WAL mode: great read concurrency, single-writer (fine for read-heavy job site)
- In-memory TF-IDF: fast queries (<5ms) but rebuilds on every restart (~150ms)
- Client-side filtering for match results (max 100): instant filter changes, no API round-trips
- Server-side filtering for browse: handles full 9,900 jobs efficiently with SQL indexes

---

## Test Coverage

**73 tests across 5 test files:**

| File | Tests | What |
|------|-------|------|
| `test_api.py` | 16 | All API endpoints, auth, error handling |
| `test_database.py` | 18 | Schema, CRUD, filtering, pagination, sorting |
| `test_keyword_extractor.py` | 22 | Skill extraction, work history, level detection, domains, education |
| `test_keyword_matcher.py` | 12 | Scoring, domain penalties, level proximity, role categories |
| `test_tfidf.py` | 5 | Index build, search ranking, resume scoring |

---

## License

MIT
