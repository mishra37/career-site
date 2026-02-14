# CareerMatch — Personalized Career Site

> **Decimal AI Take-Home Project** — A personalized career site that uses AI to match candidates with the most relevant job openings based on their resume.

![Next.js](https://img.shields.io/badge/Next.js-16-black?logo=next.js)
![TypeScript](https://img.shields.io/badge/TypeScript-5-blue?logo=typescript)
![Tailwind CSS](https://img.shields.io/badge/Tailwind-v4-38bdf8?logo=tailwindcss)

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| **Browse Jobs** | View 50+ open positions with search, filtering (department, level, type, location, remote), sorting, and pagination |
| **Resume Upload** | Drag-and-drop PDF/TXT resume upload with real-time processing feedback |
| **AI Matching** | Hybrid matching engine scores and ranks jobs based on resume content — skills, experience level, domain, and title relevance |
| **Job Detail Pages** | Statically generated detail pages for each role with full descriptions, requirements, responsibilities, and skills |
| **Dark Mode** | Automatic dark mode via `prefers-color-scheme` with consistent theming |
| **Responsive Design** | Fully responsive layout from mobile to desktop |
| **Animations** | Subtle stagger animations, fade-ins, and loading skeletons for a polished UX |

---

## 🏗️ Architecture

```
career-site/
├── src/
│   ├── app/
│   │   ├── api/
│   │   │   ├── jobs/           # GET /api/jobs — listing with filters + pagination
│   │   │   │   └── [id]/       # GET /api/jobs/:id — single job
│   │   │   └── match/          # POST /api/match — resume upload + AI matching
│   │   ├── jobs/[id]/          # Job detail page (SSG with generateStaticParams)
│   │   ├── layout.tsx          # Root layout with Header + Footer
│   │   ├── page.tsx            # Homepage — hero, resume upload, job grid
│   │   └── globals.css         # Theme variables, animations, custom styles
│   ├── components/
│   │   ├── Header.tsx          # Sticky navigation header
│   │   ├── JobCard.tsx         # Job listing card with optional match score
│   │   ├── JobCardSkeleton.tsx # Loading skeleton for job cards
│   │   ├── FilterBar.tsx       # Search + filter controls
│   │   └── ResumeUpload.tsx    # Drag-and-drop resume upload component
│   └── lib/
│       ├── types.ts            # TypeScript interfaces (Job, MatchResult, etc.)
│       ├── jobs-data.ts        # 50 synthetic jobs across diverse industries
│       └── ai-matching.ts      # Hybrid AI matching engine
├── .env.example                # Environment variable template
├── next.config.ts              # Next.js configuration
└── package.json
```

### Key Design Decisions

1. **Next.js App Router** — Leverages React Server Components for the job detail pages (SSG with `generateStaticParams`) while keeping the interactive homepage as a client component. API routes handle resume processing server-side.

2. **Hybrid Matching Engine** — Two modes:
   - **OpenAI Embeddings** (when `OPENAI_API_KEY` is set): Computes cosine similarity between resume and job description embeddings for semantic matching.
   - **Keyword-Based Fallback** (default): Multi-signal scoring algorithm that doesn't require any API key — perfect for local development and demos.

3. **In-Memory Data** — Job data lives in a TypeScript module for simplicity. This avoids the need for database setup while demonstrating the full data flow. See [Scalability](#-scaling-from-50-to-5-million-jobs) for how this would evolve.

4. **Diverse Job Data** — The 50 synthetic jobs intentionally span many industries (Engineering, Healthcare, Design, Marketing, Legal, Education, etc.) to test the matching engine's ability to discriminate between relevant and irrelevant roles.

5. **Server-Side PDF Parsing** — Resume PDFs are parsed on the server using `pdf-parse` to extract text, keeping the client lightweight and avoiding sending raw file bytes to external APIs.

---

## 🚀 Getting Started

### Prerequisites

- **Node.js** ≥ 18
- **npm** or **yarn**

### Installation

```bash
# Clone the repo
git clone <repo-url>
cd career-site

# Install dependencies
npm install

# Copy environment variables (optional — works without API key)
cp .env.example .env.local

# Start development server
npm run dev
```

The app will be available at **http://localhost:3000**.

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | No | OpenAI API key for embedding-based semantic matching. If not set, the app uses the keyword-based matching fallback which works great out of the box. |

---

## 🤖 AI Matching — How It Works

### Keyword-Based Matching (Default)

The fallback engine uses a **multi-signal scoring algorithm** with these weighted components:

| Signal | Weight | Description |
|--------|--------|-------------|
| **Skill Matching** | 40% | Percentage of the job's required skills found in the resume |
| **Title/Role Match** | 20% | Token overlap between job title and resume text |
| **Domain Alignment** | 15% | Whether the resume's detected domain (engineering, healthcare, etc.) matches the job's department |
| **Level Matching** | 15% | How well the candidate's inferred experience level matches the role (Intern → C-Suite) |
| **Description Overlap** | 10% | Keyword overlap between job description and resume |

Additionally, the engine applies a **domain penalty** (0.3x multiplier) for completely unrelated fields (e.g., a software engineer shouldn't highly match a nursing position).

### OpenAI Embeddings Mode

When `OPENAI_API_KEY` is provided, the engine:
1. Computes embeddings for the resume text using `text-embedding-3-small`
2. Computes embeddings for each job's combined description + requirements + skills
3. Ranks by cosine similarity
4. Returns top 20 matches with semantic relevance scores

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
# List jobs with filters
curl "http://localhost:3000/api/jobs?department=Engineering&level=Senior"

# Get a specific job
curl "http://localhost:3000/api/jobs/1"

# Match a resume (text file)
curl -X POST "http://localhost:3000/api/match" \
  -F "resume=@path/to/resume.txt;type=text/plain"

# Match a resume (PDF)
curl -X POST "http://localhost:3000/api/match" \
  -F "resume=@path/to/resume.pdf;type=application/pdf"
```

---

## 🛠️ Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| **Framework** | Next.js 16 (App Router) | Server components, API routes, SSG, excellent DX |
| **Language** | TypeScript | Type safety across the full stack |
| **Styling** | Tailwind CSS v4 | Utility-first, excellent for rapid UI development |
| **Icons** | Lucide React | Modern, consistent icon set |
| **PDF Parsing** | pdf-parse v2 | Server-side PDF text extraction |
| **AI** | OpenAI SDK (optional) | Embedding-based semantic matching |
| **Deployment** | Vercel | Zero-config Next.js deployment |

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
