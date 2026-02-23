# CareerMatch — Personalized Career Site

> **Decimal AI Take-Home Project** — A personalized career site that extracts keywords from uploaded resumes and matches candidates with the most relevant job openings.

![Next.js](https://img.shields.io/badge/Next.js-16-black?logo=next.js)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi)
![TypeScript](https://img.shields.io/badge/TypeScript-5-blue?logo=typescript)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python)
![Tailwind CSS](https://img.shields.io/badge/Tailwind-v4-38bdf8?logo=tailwindcss)

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| **Browse Jobs** | View 50+ open positions with search, filtering (department, level, type, location, remote), sorting, and pagination |
| **Resume Upload** | Drag-and-drop PDF/TXT resume upload with real-time processing feedback |
| **Keyword Extraction** | Extracts skills, experience level, years of experience, education, and domain keywords from resumes using curated dictionaries |
| **Keyword Matching** | Multi-signal scoring engine ranks jobs by skill overlap, title relevance, requirements match, and domain alignment |
| **Extracted Keywords Display** | Sidebar shows all extracted keywords (skills, level, years, domains, education) after resume upload |
| **Job Detail Pages** | Statically generated detail pages for each role with full descriptions, requirements, responsibilities, and skills |
| **Dark Mode** | Automatic dark mode via `prefers-color-scheme` with consistent theming |
| **Responsive Design** | Fully responsive layout from mobile to desktop |
| **Animations** | Subtle stagger animations, fade-ins, and loading skeletons for a polished UX |
| **API Docs** | Auto-generated Swagger/OpenAPI docs at `/docs` (FastAPI) |

---

## 🏗️ Architecture

```
career-site/
├── backend/                    # FastAPI Python backend
│   ├── main.py                 # FastAPI app — 3 endpoints (jobs, jobs/:id, match)
│   ├── models.py               # Pydantic models with camelCase serialization
│   ├── jobs_data.py            # Loads shared jobs from data/jobs.json
│   ├── keyword_extractor.py    # Resume keyword extraction engine
│   ├── keyword_matcher.py      # Job matching & scoring engine
│   └── requirements.txt        # Python dependencies
├── data/
│   └── jobs.json               # 50 jobs — shared data source for both services
├── src/
│   ├── app/
│   │   ├── jobs/[id]/          # Job detail page (SSG with generateStaticParams)
│   │   ├── layout.tsx          # Root layout with Header + Footer
│   │   ├── page.tsx            # Homepage — hero, resume upload, job grid, keyword sidebar
│   │   └── globals.css         # Theme variables, animations, custom styles
│   ├── components/
│   │   ├── Header.tsx          # Sticky navigation header
│   │   ├── JobCard.tsx         # Job listing card with optional match score
│   │   ├── JobCardSkeleton.tsx # Loading skeleton for job cards
│   │   ├── FilterBar.tsx       # Search + filter controls
│   │   └── ResumeUpload.tsx    # Drag-and-drop resume upload component
│   └── lib/
│       ├── types.ts            # TypeScript interfaces (Job, MatchResult, ExtractedKeywords)
│       └── jobs-data.ts        # Jobs data for SSG page generation
├── next.config.ts              # Proxies /api/* to FastAPI via rewrites
└── package.json
```

### Why FastAPI over Flask?

| Criteria | FastAPI | Flask |
|----------|---------|-------|
| **Async support** | Native `async/await` — non-blocking I/O out of the box | Requires extensions (quart, gevent) |
| **Data validation** | Built-in via Pydantic models — automatic request/response validation | Manual or via Flask-Marshmallow |
| **API documentation** | Auto-generated Swagger UI + ReDoc at `/docs` | Requires Flask-RESTx or flasgger |
| **File uploads** | Clean `UploadFile` API with streaming support | Werkzeug's `request.files` — more verbose |
| **Performance** | ASGI-based, significantly faster than WSGI | WSGI, synchronous by default |
| **Type hints** | First-class — powers validation, docs, and IDE support | Not integral to the framework |

**FastAPI was the clear choice** for this project because it provides automatic OpenAPI docs, Pydantic model validation (with camelCase serialization for seamless frontend integration), and native async support — all essential for a modern API that handles file uploads and keyword extraction.

### Key Design Decisions

1. **Decoupled Architecture** — The frontend (Next.js) and backend (FastAPI) are fully separated. Next.js proxies `/api/*` requests to FastAPI via `rewrites()`, keeping frontend code unchanged while the API runs as a standalone Python service.

2. **Shared Data Source** — Both services read from `data/jobs.json`, ensuring a single source of truth for all 50 jobs. The frontend uses it for SSG page generation, while the backend loads it for search and matching.

3. **Keyword-Based Matching** — Instead of semantic/embedding approaches, the engine uses explicit keyword extraction with curated skill dictionaries. This is transparent (users see exactly which keywords were extracted), fast (no API calls), and deterministic.

4. **Pydantic camelCase Models** — All API responses use `alias_generator=to_camel` so Python's `snake_case` fields serialize as `camelCase` JSON — matching JavaScript conventions without any frontend changes.

5. **Server-Side PDF Parsing** — Resume PDFs are parsed on the Python backend using `pdfplumber` (more reliable than pdf-parse for complex PDF layouts), keeping the client lightweight.

---

## 🚀 Getting Started

### Prerequisites

- **Node.js** ≥ 18
- **Python** ≥ 3.10
- **npm** or **yarn**

### Installation

```bash
# Clone the repo
git clone <repo-url>
cd career-site

# ─── Frontend ───
npm install

# ─── Backend ───
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd ..
```

### Running the App

You need **two terminals** — one for the FastAPI backend and one for the Next.js frontend:

```bash
# Terminal 1: Start FastAPI backend (port 8000)
cd backend
source venv/bin/activate
uvicorn main:app --reload --port 8000

# Terminal 2: Start Next.js frontend (port 3000)
npm run dev
```

The app will be available at **http://localhost:3000**.  
FastAPI Swagger docs are at **http://localhost:8000/docs**.

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `API_URL` | No | `http://localhost:8000` | FastAPI backend URL (used by Next.js proxy) |

---

## 🤖 Keyword Extraction & Matching — How It Works

### Step 1: Keyword Extraction (`keyword_extractor.py`)

When a user uploads a resume, the backend extracts structured keywords:

| Extracted Data | Method | Example |
|---------------|--------|---------|
| **Skills** | Curated dictionaries (~250 skills) — matches multi-word first (e.g., "machine learning"), then single-word (e.g., "python") | `["python", "react", "machine learning", "aws"]` |
| **Experience Level** | Pattern matching on keywords (e.g., "senior", "lead") + inferred from years | `"senior"` |
| **Years of Experience** | Regex patterns (e.g., "5+ years", "3 years of experience") | `5` |
| **Education** | Keyword matching (e.g., "bachelor", "phd", "computer science") | `["bachelor", "computer science"]` |
| **Domains** | Requires ≥2 keyword hits per domain from 13 domain categories | `["engineering", "data science"]` |

**Key implementation details:**
- Multi-word skills are matched first (sorted by length, longest first) to avoid partial matches
- Single-word skills are matched against word tokens only (not substrings) — prevents "scala" matching "scalable"
- Common false positives like "go" (the language vs. the word) are excluded — "golang" is used instead
- If level isn't detected by keywords but years are found, level is inferred (e.g., 5 years → senior)

### Step 2: Job Matching (`keyword_matcher.py`)

Extracted keywords are scored against each of the 50 jobs using weighted signals:

| Signal | Weight (pts) | Description |
|--------|-------------|-------------|
| **Skill Match** | 50 | Jaccard overlap between resume skills and job's requirements + skills |
| **Title Relevance** | 20 | Word overlap between resume text and job title |
| **Requirements Match** | 15 | How many of the job's specific requirements appear in the resume |
| **Domain Alignment** | 15 | Whether the candidate's detected domains match the job's department |
| **Level Bonus** | +5 | Added when experience level matches the job level |
| **Domain Penalty** | ×0.3 | Applied when domains are completely unrelated (e.g., healthcare vs engineering) |

Results are sorted by score and the top 20 matches (above a minimum threshold of 5) are returned.

### Example

Given a resume with "Senior Software Engineer, 5 years experience in Python, React, Node.js, PostgreSQL, AWS, microservices, REST APIs":

**Extracted Keywords:**
```json
{
  "skills": ["python", "react", "node.js", "postgresql", "aws", "microservices", "rest apis"],
  "experienceLevel": "senior",
  "yearsOfExperience": 5,
  "domains": ["engineering"],
  "education": []
}
```

**Top Matches:**
1. Senior Software Engineer — 46 pts
2. Full Stack Engineer — 46 pts
3. Junior Frontend Developer — 41 pts
4. Backend Engineer — 39 pts
5. Data Engineer — 35 pts

---

## 📊 Scaling from 50 to 5 Million Jobs

This section outlines how the architecture would evolve as the job catalog grows.

### Current State: 50 Jobs (In-Memory)
- Jobs stored in a TypeScript array
- Full-text search via string matching
- Matching runs against all jobs synchronously
- Response time: <100ms

### 500 → 5,000 Jobs: Add a Database
- **Migrate to PostgreSQL** with proper indexing (department, level, location, type)
- **Full-text search** using PostgreSQL's `tsvector` + `GIN` indexes
- **Connection pooling** via PgBouncer or Prisma's connection pool
- Cache filter aggregations (department counts, etc.)
- Response time target: <200ms

### 5,000 → 50,000 Jobs: Search Infrastructure
- **Introduce Elasticsearch/Meilisearch** for fast faceted search and typo-tolerant queries
- **Pre-compute embeddings** for all jobs and store in a vector database (Pinecone, pgvector, Qdrant)
- **Background job processing** — resume matching moves to a queue (Bull/BullMQ) with progress streaming via WebSockets/SSE
- **CDN caching** for job listing pages with ISR (Incremental Static Regeneration)
- **API pagination** with cursor-based pagination instead of offset

### 50,000 → 500,000 Jobs: Distributed Systems
- **Microservices split**: Separate services for job search, matching, and resume processing
- **Redis caching layer** for hot job data and pre-computed match results
- **Sharded vector database** — partition embeddings by industry/region
- **Rate limiting** and request throttling on the matching API
- **Horizontal scaling** with Kubernetes — auto-scale matching workers based on queue depth
- **Batch embedding computation** — nightly pipeline to update job embeddings for new/modified listings
- Response time target: <500ms for matching, <100ms for search

### 500,000 → 5 Million Jobs: Platform Scale
- **Event-driven architecture** with Kafka for job updates/matching events
- **Multi-region deployment** — job data replicated across regions for low-latency search
- **ML pipeline** (Airflow/Prefect) for:
  - Training custom matching models on user interaction data (clicks, applications)
  - A/B testing different ranking algorithms
  - Personalization signals beyond resume (browsing history, saved jobs)
- **Approximate Nearest Neighbor (ANN)** search via HNSW indexes for sub-second vector similarity across millions of embeddings
- **GraphQL federation** to compose data from multiple services
- **Data warehouse** (Snowflake/BigQuery) for analytics on matching quality, conversion rates
- Response time target: <1s for personalized matching (async with streaming results)

### Trade-offs at Each Stage

| Dimension | Small Scale | Platform Scale |
|-----------|-------------|----------------|
| **Complexity** | Single Next.js app, zero infra | Microservices, ML pipelines, message queues |
| **Cost** | $0/month (Vercel free tier) | $10K-100K+/month infra |
| **Matching Quality** | Keyword heuristics work well | Custom ML models with continuous learning |
| **Latency** | Synchronous, instant | Async with progressive loading |
| **Data Freshness** | Real-time (in-memory) | Eventually consistent (minutes) |
| **Team Size** | 1 developer | 5-15 engineers across platform/ML/infra |

The key principle: **start simple, measure, then optimize the bottleneck**. Don't build for 5M jobs when you have 50.

---

## 🧪 Testing the App

### Quick Test with Resume Upload

1. Visit `http://localhost:3000`
2. Upload any `.pdf` or `.txt` file containing resume text
3. Jobs will be re-ranked by relevance with match scores

### API Testing

```bash
# List jobs with filters (through Next.js proxy)
curl "http://localhost:3000/api/jobs?department=Engineering&level=Senior"

# Or hit FastAPI directly
curl "http://localhost:8000/api/jobs?department=Engineering&level=Senior"

# Get a specific job
curl "http://localhost:3000/api/jobs/1"

# Match a resume (text file)
curl -X POST "http://localhost:3000/api/match" \
  -F "resume=@path/to/resume.txt"

# Match a resume (PDF)
curl -X POST "http://localhost:3000/api/match" \
  -F "resume=@path/to/resume.pdf"

# Interactive API docs (FastAPI auto-generated)
open http://localhost:8000/docs
```

---

## 🛠️ Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| **Frontend** | Next.js 16 (App Router) | Server components, SSG for job pages, proxy rewrites |
| **Backend** | FastAPI 0.115 | Async, Pydantic validation, auto OpenAPI docs, native file upload |
| **Language (FE)** | TypeScript 5 | Type safety across the frontend |
| **Language (BE)** | Python 3.10+ | Rich NLP ecosystem, curated skill dictionaries |
| **Styling** | Tailwind CSS v4 | Utility-first, rapid UI development |
| **Icons** | Lucide React | Modern, consistent icon set |
| **PDF Parsing** | pdfplumber | Robust server-side PDF text extraction |
| **Data Validation** | Pydantic v2 | Request/response models with camelCase serialization |
| **ASGI Server** | Uvicorn | High-performance Python web server |
| **Deployment** | Vercel (FE) + any ASGI host (BE) | Decoupled deployment |

---

## 📝 Product Thinking

### What I'd Add Next (with more time)

1. **Saved Jobs** — Let users bookmark positions (localStorage → auth + database)
2. **Application Flow** — "Apply Now" with pre-filled fields from parsed resume
3. **Email Alerts** — Notify candidates when new matching jobs are posted
4. **Employer Dashboard** — Let recruiters see anonymized candidate match scores
5. **Resume Feedback** — Show which skills are missing for top-matched roles
6. **Multi-language Support** — i18n for global career sites
7. **Analytics** — Track search patterns, popular filters, conversion funnels
8. **Accessibility Audit** — Full WCAG 2.1 AA compliance with screen reader testing

### Design Rationale

- **Sidebar layout** for resume upload keeps it visible without interrupting browsing
- **Match scores** are shown as percentage badges — intuitive and scannable
- **Match reasons** explain *why* a job was recommended, building user trust
- **Diverse job data** demonstrates the engine can handle cross-industry matching
- **No auth required** — reduces friction for the primary use case (finding jobs)

---

## 📄 License

MIT
