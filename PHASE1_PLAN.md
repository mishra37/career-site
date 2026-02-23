# Phase 1: Personalized Career Site — Implementation Plan

## Assignment

Build a **Personalized Career Site** (inspired by the AmEx/Eightfold career site) that allows candidates to browse jobs, upload a resume, and receive AI-powered personalized recommendations. Must scale from 500 to 5M jobs.

**Deliverables:** Hosted app + GitHub repo.

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│  Next.js 16 Frontend  (port 3000)                   │
│  React 19 + Tailwind CSS v4 + TypeScript             │
│                                                     │
│  /              Landing page + featured jobs         │
│  /jobs           Browse/search with filters          │
│  /jobs/[id]      Job detail                         │
│  /jobs/[id]/apply  Apply flow                       │
│                                                     │
│  Components: Header, FilterSidebar, JobCard,         │
│  ResumeUpload, ResumeMatchModal, FeaturedJobs        │
│                                                     │
│  next.config.ts rewrites /api/* → backend            │
├─────────────────────────────────────────────────────┤
│  FastAPI Backend  (port 8000)                        │
│  Python 3.14 + SQLite (WAL mode)                     │
│                                                     │
│  GET  /api/jobs          Paginated listing + search  │
│  GET  /api/jobs/{id}     Job detail                  │
│  POST /api/match         Resume upload → AI match    │
│  POST /api/admin/jobs    Create job (admin)          │
│                                                     │
│  Modules: database.py, models.py, jobs_data.py,      │
│  keyword_extractor.py, keyword_matcher.py,           │
│  tfidf_index.py, seed_data.py                        │
├─────────────────────────────────────────────────────┤
│  SQLite Database  (data/career_site.db)              │
│  9,900 jobs · 18 departments · 16 industries         │
│  44 locations (US, UK, India, Canada, Australia, etc)│
└─────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Frontend | Next.js 16, React 19, TypeScript | SSR, app router, modern React |
| Styling | Tailwind CSS v4 | Utility-first, fast iteration |
| Icons | Lucide React | Lightweight, consistent icon set |
| Backend | FastAPI, Pydantic 2 | Fast async Python, auto-validation |
| Database | SQLite (WAL mode) | Zero-config, single-file, good for ~100K jobs |
| Search | scikit-learn TF-IDF | No external service, vectorizes in-memory |
| PDF parsing | pdfplumber | Reliable PDF text extraction |
| Testing | pytest, httpx | 73 backend tests |

---

## Core Features

### 1. Browse Jobs (`/jobs`)

- **Paginated listing** of 9,900 jobs with server-side filtering
- **Search bar**: Keyword search powered by TF-IDF (triggers on button click / Enter)
- **Location search**: Separate location input
- **Filters**:
  - Job Type (Full-time, Part-time, Contract, Internship)
  - Work Setting (On-site, Remote, Hybrid)
  - Visa Sponsorship (Any / Yes / No)
  - Posted Within (24h, 7d, 30d)
  - Years of Experience (min/max with Apply button + validation)
  - Salary Range (min/max dropdowns)
- **Sort**: Newest, Salary High→Low, Salary Low→High, Relevance (when searching)
- Active search/filter chips with clear buttons

### 2. Job Detail (`/jobs/[id]`)

- Full job description, requirements, responsibilities
- Skills tags, salary range, location, remote type
- Recruiter info (when available)
- Company size, visa sponsorship status
- "Apply Now" button → apply flow

### 3. Resume Upload & AI Matching

Two entry points:
- **"Match My Resume"** button in header → modal overlay
- **Upload widget** in sidebar on browse page

**Resume matching pipeline:**

```
Upload PDF/TXT
      │
      ▼
Extract text (pdfplumber / UTF-8)
      │
      ├──► KeywordExtractor.extract(text)
      │     • Skills (200+ multi-word, 130+ single-word dictionary)
      │     • Work history (parses Experience section → titles, companies, durations)
      │     • Role categories (SWE, ML, Data Science, Product, Design, Management)
      │     • Education status (pursuing vs completed, graduation proximity)
      │     • Experience level (student → intern/entry, years → mid/senior/lead)
      │     • Domains (14 domains: engineering, healthcare, legal, etc.)
      │
      ├──► TF-IDF cosine similarity (resume vs all 9,900 job documents)
      │
      └──► KeywordMatcher.match() → scored + ranked results
```

**Scoring (100 points max):**

| Signal | Points | How |
|--------|--------|-----|
| TF-IDF text similarity | 25 | Cosine similarity of resume vs job document |
| Skill match | 35 | % of job skills found in resume (exact match) |
| Title relevance | 5 | Resume skills appearing in job title |
| Domain alignment | 15 | Resume domain matches job department |
| Level proximity | 10 | Distance between inferred level and job level |
| Role category match | 10 | Work history roles match job type (SWE→SWE jobs) |

**Penalties (multiplicative):**
- Healthcare job + non-healthcare resume → ×0.3
- Cross-domain incompatibility (e.g., engineering resume vs design job) → ×0.5

**Level inference priority:**
1. Student pursuing degree + no work exp → far from graduation = intern, near = entry
2. Calculated years from work history → `<1=intern, 1-2=entry, 2-4=mid, 5-7=senior, 8-10=lead, 11+=director`
3. Keyword-based detection fallback

**Result:** Top 100 matches returned, filtered client-side with the same filter controls as browse mode.

### 4. Apply Flow (`/jobs/[id]/apply`)

- Application form with name, email, phone, resume upload
- Cover letter textarea
- Confirmation on submit

---

## Data

### Job Generation (`seed_data.py`)

- **16 industries**: Technology (2,500), Data Science & AI (1,000), Healthcare (800), Finance (600), Legal (600), Marketing (500), Sales (500), Operations (500), Education (400), Design (400), Manufacturing (400), Product (400), Hospitality (400), Real Estate (300), Media (300), HR (300)
- **9 experience levels**: Intern through C-Suite with weighted distribution
- **44 locations**: 20 US cities, 3 UK, 3 Canada, 4 India, 2 Australia, 3 Europe, 3 Asia-Pacific
- **Date distribution**: Shuffled across all industries for even recency distribution
- **9,900 total** jobs

### TF-IDF Index (`tfidf_index.py`)

- scikit-learn `TfidfVectorizer` with unigrams + bigrams
- Weighted documents: title ×4, department ×3, skills ×2, description ×1, requirements ×1
- Built on server startup (~150ms for 10K jobs)
- Supports keyword search (browse) and resume scoring (match)

---

## Scalability Considerations

| Scale | Strategy |
|-------|----------|
| **500 jobs** | Current approach works perfectly. In-memory TF-IDF, SQLite, client-side filtering for match results. |
| **5,000 jobs** | Current approach handles this well. SQLite with indexes, paginated API, TF-IDF builds in ~200ms. |
| **50,000 jobs** | SQLite still works. Add FTS5 full-text search extension for keyword search instead of TF-IDF search. Keep TF-IDF for resume matching (batched scoring). Add result caching. |
| **500,000 jobs** | Move to PostgreSQL with pg_trgm + full-text search. Replace in-memory TF-IDF with Elasticsearch or pgvector for ANN search. Pre-compute embeddings. Add Redis caching layer. |
| **5,000,000 jobs** | Distributed search (Elasticsearch cluster). Embedding-based matching with vector DB (Pinecone/Qdrant). Async job processing for resume matching. CDN for static job pages. Database sharding by region. |

**Current trade-offs:**
- SQLite WAL mode: great read concurrency, single-writer (fine for read-heavy job site)
- In-memory TF-IDF: fast queries (<5ms) but rebuilds on every restart (~150ms)
- Client-side filtering for match results (max 100): instant filter changes, no API round-trips
- Server-side filtering for browse: handles full 9,900 jobs efficiently with SQL indexes

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
│   ├── components/               # React components
│   │   ├── Header.tsx
│   │   ├── FilterSidebar.tsx
│   │   ├── JobCard.tsx
│   │   ├── JobCardSkeleton.tsx
│   │   ├── FeaturedJobs.tsx
│   │   ├── ResumeUpload.tsx
│   │   ├── ResumeMatchModal.tsx
│   │   ├── UploadResumeButton.tsx
│   │   └── Providers.tsx
│   ├── contexts/
│   │   └── ResumeModalContext.tsx # Global resume modal state
│   └── lib/
│       └── types.ts              # TypeScript interfaces
│
├── backend/                      # FastAPI backend
│   ├── main.py                   # API routes + startup
│   ├── database.py               # SQLite access layer
│   ├── models.py                 # Pydantic models (Job, MatchResult, etc.)
│   ├── jobs_data.py              # Job data access helpers
│   ├── keyword_extractor.py      # Resume → structured keywords
│   ├── keyword_matcher.py        # Keywords + TF-IDF → scored matches
│   ├── tfidf_index.py            # TF-IDF vectorizer + search
│   ├── seed_data.py              # Generate 9,900 jobs
│   ├── requirements.txt
│   └── tests/                    # 73 pytest tests
│       ├── conftest.py
│       ├── test_api.py
│       ├── test_database.py
│       ├── test_keyword_extractor.py
│       ├── test_keyword_matcher.py
│       └── test_tfidf.py
│
├── data/
│   ├── jobs.json                 # Original 50 seed jobs
│   └── career_site.db            # SQLite database (gitignored, re-generated)
│
├── next.config.ts                # API proxy → backend
├── package.json
├── tsconfig.json
├── tailwind / postcss configs
└── .gitignore
```

---

## Running Locally

```bash
# 1. Install frontend dependencies
cd career-site
npm install

# 2. Install backend dependencies
cd backend
pip install -r requirements.txt

# 3. Seed the database (9,900 jobs)
python3 seed_data.py --reset

# 4. Start backend (port 8000)
uvicorn main:app --host 0.0.0.0 --port 8000

# 5. Start frontend (port 3000) — in another terminal
cd ..
npm run dev

# 6. Run tests
cd backend
python3 -m pytest tests/ -v
```

Open [http://localhost:3000](https://career-match-app.vercel.app/jobs) to use the app.

---

## Test Coverage

**73 tests across 5 test files:**

| File | Tests | What |
|------|-------|------|
| `test_api.py` | 16 | All API endpoints, auth, error handling |
| `test_database.py` | 18 | Schema, CRUD, filtering, pagination, sorting |
| `test_keyword_extractor.py` | 22 | Skill extraction, level detection, domains, education |
| `test_keyword_matcher.py` | 12 | Scoring, domain penalties, level proximity, bounds |
| `test_tfidf.py` | 5 | Index build, search ranking, resume scoring |
