# Phase 2: Scaling Architecture — From 500 to 5M Jobs

## Overview

This document presents a progressive scaling strategy for CareerMatch, evolving from the current single-server architecture (10K jobs) to a distributed system capable of serving 5 million jobs to millions of users. Each tier introduces only the complexity necessary for the next order of magnitude — no premature optimization.

**Philosophy:** Do not add infrastructure until you need it.

---

## Current Architecture (Phase 1 Baseline)

```
┌──────────────────────────────────────────────────────┐
│  Vercel (Next.js 16, React 19)                       │
│                                                      │
│  /              Landing page + featured jobs          │
│  /jobs           Browse/search (client-side state)    │
│  /jobs/[id]      Job detail                          │
│  /jobs/[id]/apply  Application flow                  │
│                                                      │
│  next.config.ts rewrites /api/* ─────────────────┐   │
└──────────────────────────────────────────────────┼───┘
                                                   │
                                                   ▼
┌──────────────────────────────────────────────────────┐
│  Render (FastAPI, single instance, 512MB RAM)        │
│                                                      │
│  GET  /api/jobs       SQL filters + TF-IDF re-rank   │
│  GET  /api/jobs/{id}  Direct SELECT by primary key   │
│  POST /api/match      Resume upload → AI matching    │
│    1. Parse PDF (pdfplumber)                         │
│    2. Extract keywords (keyword_extractor.py)        │
│    3. TF-IDF score ALL 9,900 jobs (tfidf_index.py)   │
│    4. load_jobs() → ALL rows into RAM                │
│    5. KeywordMatcher scores all → returns top 100    │
│  POST /api/admin/jobs  Create job + rebuild TF-IDF   │
│                                                      │
│  In-Memory: TF-IDF matrix (~2MB sparse CSR)          │
│  Singleton: SQLite connection (WAL mode)             │
├──────────────────────────────────────────────────────┤
│  SQLite (data/career_site.db, ~150MB)                │
│  9,900 rows · 24 columns · 6 B-tree indexes         │
│  Text search: LIKE '%word%' (full table scan)        │
│  Facets: SELECT DISTINCT per column × 6              │
└──────────────────────────────────────────────────────┘
```

### Current Performance (10K jobs)

| Operation | Latency | Memory |
|-----------|---------|--------|
| TF-IDF index build (startup) | ~150ms | ~2MB |
| Keyword search (TF-IDF) | <5ms | negligible |
| SQL text search (LIKE) | ~50ms | negligible |
| Resume match (full pipeline) | ~1.5s | ~100MB peak |
| Facet computation (6 queries) | ~10ms | negligible |
| Job detail by ID | <1ms | negligible |

### Bottleneck Inventory

| # | Bottleneck | Where | Impact at Scale |
|---|-----------|-------|-----------------|
| 1 | **LIKE '%word%' text search** | `database.py` — each search word adds 6 LIKE clauses across title, description, skills, company, location, department. Leading wildcards prevent index usage. | Full table scan. At 500K: 2-5s per query. At 5M: 20-50s. |
| 2 | **In-memory TF-IDF matrix** | `tfidf_index.py` — `fit_transform()` builds entire matrix in RAM. 8,000 features × N jobs. | 10K = 2MB. 500K = 500MB-1GB. 5M = 5-10GB (exceeds RAM). |
| 3 | **Load ALL jobs for matching** | `main.py` — `load_jobs()` fetches every row, deserializes 3 JSON columns per row, creates Pydantic models. | 10K = 100MB/200ms. 500K = 5GB/20s. 5M = OOM crash. |
| 4 | **O(N) resume scoring** | `keyword_matcher.py` — loops through every job to compute 6-signal score. | Linear with job count. 5M = 30-60s per resume. |
| 5 | **Synchronous TF-IDF rebuild** | `main.py` — `_rebuild_tfidf()` blocks all requests during rebuild. Called on every admin job creation. | 10K = 150ms. 500K = 30s (server unresponsive). |
| 6 | **Facets on every request** | `database.py` — 6 `SELECT DISTINCT` queries, no caching. | 500K = 500ms+ cold. Multiplied by every API call. |
| 7 | **SQLite single-writer** | `database.py` — WAL mode allows concurrent reads but only one writer. No connection pooling. | Write contention under concurrent ingestion. |

---

## Tier 1: 500 Jobs — "Works Out of the Box"

### Changes Required

**None.** The current architecture handles this perfectly.

### Performance at 500 Jobs

| Operation | Latency | Notes |
|-----------|---------|-------|
| TF-IDF build | <20ms | Matrix fits in L2 cache |
| Text search | <5ms | SQLite page cache holds entire DB |
| Resume match | <200ms | 500 rows loaded and scored instantly |
| Total DB size | ~8MB | Trivial |

### Trade-off Rationale

Adding Redis, PostgreSQL, or Elasticsearch for 500 jobs increases operational complexity (deployment, monitoring, debugging, cost) with zero user-visible benefit. The entire dataset fits in CPU cache. Keep it simple.

**Infrastructure cost: $0/month** (Render free + Vercel hobby)

---

## Tier 2: 5,000 Jobs — "Optimize What We Have"

### Changes Required

Targeted optimizations within the existing stack. No new services.

| Change | What | Why |
|--------|------|-----|
| **SQLite FTS5** | Add full-text search virtual table | Replace LIKE queries (O(N) scan → O(log N) inverted index lookup) |
| **Facet caching** | In-process TTL cache (5-minute expiry) | Eliminate 6 redundant SELECT DISTINCT queries per request |
| **Background TF-IDF rebuild** | Move `_rebuild_tfidf()` to a daemon thread | Prevent blocking all requests when admin adds a job |
| **Selective column loading** | Load only scoring-relevant columns for matching | Reduce memory from ~100MB to ~40MB for full match pipeline |

### SQLite FTS5 Implementation

```sql
-- Virtual table mirroring searchable text columns
CREATE VIRTUAL TABLE jobs_fts USING fts5(
    title, description, skills, company, location, department,
    content='jobs', content_rowid='rowid'
);

-- Triggers to keep FTS5 in sync with the jobs table
CREATE TRIGGER jobs_ai AFTER INSERT ON jobs BEGIN
    INSERT INTO jobs_fts(rowid, title, description, skills, ...)
    VALUES (new.rowid, new.title, new.description, new.skills, ...);
END;
```

**Query change:**
```sql
-- Before (full table scan):
WHERE LOWER(title) LIKE '%software%' OR LOWER(description) LIKE '%software%' ...

-- After (inverted index lookup):
SELECT * FROM jobs WHERE rowid IN (
    SELECT rowid FROM jobs_fts WHERE jobs_fts MATCH 'software'
)
```

### What Stays

SQLite, single Render instance, in-memory TF-IDF, Vercel frontend. The core architecture is unchanged.

### Trade-offs

| Decision | Pro | Con |
|----------|-----|-----|
| FTS5 over Elasticsearch | Zero new infrastructure, built into SQLite | No fuzzy matching, no aggregation-based facets |
| In-process cache over Redis | No new service to manage | Cache lost on restart, not shared across instances |
| Background thread over task queue | Simple threading, no new dependency | No retry logic, no monitoring |

**Infrastructure cost: $0/month** (still within free tier limits)

---

## Tier 3: 500,000 Jobs — "New Infrastructure"

This is the critical inflection point where the architecture fundamentally changes.

### Why Current Approach Breaks

| Component | At 5K | At 500K | Failure Mode |
|-----------|-------|---------|-------------|
| TF-IDF matrix | 0.5MB | 500MB-1GB | Exceeds Render RAM (512MB) |
| `load_jobs()` | 50MB, 200ms | 5-10GB, 20-40s | Out of memory crash |
| SQLite writes | Fast | WAL contention | Concurrent ingestion fails |
| FTS5 | Fast | Large index rebuilds | Slow sync, no replication |
| Facets (cached) | OK | Cold start: 500ms+ | First request after restart is slow |

### Architecture

```
┌──────────────────────────────────────────────────────┐
│  Vercel (Next.js 16)                                 │
│  NEW: Polling for async match results                │
│  NEW: ISR for job detail pages (1hr revalidation)    │
└───────────────────┬──────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────────┐
│  Render (FastAPI, 2+ instances, load balanced)       │
│                                                      │
│  /api/jobs         → PostgreSQL full-text search     │
│  /api/jobs/{id}    → PostgreSQL primary key lookup   │
│  /api/match        → Enqueue to job queue (HTTP 202) │
│  /api/match/{id}   → Poll status / get results       │
│                                                      │
│  NEW: No more in-memory TF-IDF (search via Postgres) │
│  NEW: SQLAlchemy 2.0 + asyncpg connection pool       │
│  NEW: Redis for caching + rate limiting              │
├──────────┬───────────────────────┬───────────────────┤
│          │                       │                    │
│  ┌───────▼─────────┐  ┌─────────▼──────────┐        │
│  │  Redis (Upstash) │  │  Background Workers │        │
│  │  - Facet cache   │  │  - Parse PDF        │        │
│  │  - Query cache   │  │  - Retrieve (FTS)   │        │
│  │  - Match results │  │  - Rerank (500 cand) │       │
│  │  - Rate limits   │  │  - Store results     │       │
│  │  - Job queue     │  │                      │       │
│  └─────────────────┘  └──────────────────────┘       │
│                                                      │
├──────────────────────────────────────────────────────┤
│  PostgreSQL 16 (Neon / Supabase)                     │
│  ├── tsvector + GIN index for full-text search       │
│  ├── B-tree indexes on all filter columns            │
│  ├── JSONB for skills, requirements                  │
│  ├── Connection pooling via PgBouncer                │
│  └── Optional: read replica for search queries       │
└──────────────────────────────────────────────────────┘
```

### Key Changes

#### 3a. Database: SQLite → PostgreSQL

**Why PostgreSQL:**
- Built-in `tsvector` + GIN indexes for full-text search (replaces LIKE and FTS5)
- `websearch_to_tsquery('english', ...)` supports natural language queries
- Connection pooling (PgBouncer) handles concurrent requests
- Read replicas for horizontal read scaling
- `pg_trgm` extension for fuzzy/typo-tolerant matching
- JSONB type with GIN indexing for skills array queries

**Schema evolution:**
```sql
-- Weighted full-text search column (auto-maintained)
ALTER TABLE jobs ADD COLUMN search_vector tsvector
  GENERATED ALWAYS AS (
    setweight(to_tsvector('english', title), 'A') ||
    setweight(to_tsvector('english', coalesce(skills_text, '')), 'A') ||
    setweight(to_tsvector('english', description), 'B') ||
    setweight(to_tsvector('english', coalesce(requirements_text, '')), 'C')
  ) STORED;

CREATE INDEX idx_jobs_search ON jobs USING GIN(search_vector);
```

**Query change:**
```sql
-- Replaces both LIKE queries and TF-IDF for keyword search
SELECT *, ts_rank_cd(search_vector, query) AS rank
FROM jobs, websearch_to_tsquery('english', 'machine learning python') AS query
WHERE search_vector @@ query
ORDER BY rank DESC
LIMIT 12 OFFSET 0;
```

#### 3b. Resume Matching: Retrieve-Rerank Pipeline

Replace the O(N) brute-force matching with a two-stage pipeline:

```
Resume Text
    │
    ├──► Extract Keywords (same as Phase 1)
    │    → skills, level, domains, role categories
    │
    ├──► Stage 1: RETRIEVE (narrow the candidate set)
    │    Build a search query from resume profile:
    │      "software engineer python react senior"
    │    Run PostgreSQL FTS → retrieve top 500 candidates
    │    Complexity: O(log N) instead of O(N)
    │
    └──► Stage 2: RERANK (detailed scoring on 500 candidates)
         Apply the 6-signal scoring (skill match, domain,
         level proximity, role category, title, text similarity)
         on just 500 jobs instead of 500,000
         Complexity: O(K) where K=500 (constant)
```

**Impact:**
| Metric | Before (brute-force) | After (retrieve-rerank) |
|--------|---------------------|------------------------|
| Jobs scored per request | 500,000 | 500 |
| Memory per request | ~5GB | ~5MB |
| Latency | ~30s | ~100ms |
| Speedup | — | **300x** |

**Trade-off:** The retrieval stage may miss some relevant jobs that brute-force would have found. Mitigate by:
- Expanding K (retrieve top 1,000 instead of 500)
- Using multiple query strategies (skills query, title query, domain query, then merge)
- Boosting recall with a broad initial query

#### 3c. Async Resume Processing

Move resume matching to a background job queue:

1. `POST /api/match` immediately returns HTTP 202 with a `match_id`
2. Background worker processes: parse PDF → extract keywords → retrieve → rerank
3. Frontend polls `GET /api/match/{match_id}/status` until complete
4. Results cached in Redis for subsequent page loads

**Why:** Even the optimized pipeline takes 1-3s. Users get a better experience with a "Processing your resume..." indicator than a hanging spinner. Also enables retries on failure.

#### 3d. Caching Layer: Redis

| What to Cache | TTL | Why |
|---------------|-----|-----|
| Facet values (departments, locations, etc.) | 5 min | Same 6 queries return identical results for minutes |
| Popular search results ("software engineer SF") | 2 min | High-hit-rate queries cached at the edge |
| Resume match results (keyed by profile hash) | 30 min | Same resume doesn't need re-scoring |
| Rate limit counters (per IP) | 1 min sliding window | Prevent abuse of match endpoint |

**Why Redis over in-process cache:** When running 2+ API instances, each has its own cache → inconsistent results and wasted computation. Redis is shared.

### Trade-offs Summary (Tier 3)

| Decision | Chosen | Alternative | Why |
|----------|--------|-------------|-----|
| PostgreSQL FTS over Elasticsearch | PostgreSQL | Elasticsearch | One fewer service. Postgres FTS handles 500K with GIN indexes. ES only needed for aggregation facets at millions scale. |
| Neon/Supabase over self-hosted Postgres | Managed | Self-hosted on Render | Zero ops burden, auto-backups, connection pooling included. Free tier covers 500K rows. |
| Redis Queue over Celery | RQ | Celery | Simpler, fewer dependencies. Celery's distributed task features not needed at this scale. |
| Polling over WebSockets | Polling | WebSocket/SSE | Simpler to implement. Match results take 1-3s — polling every 500ms is fine. WebSockets add connection management complexity. |

### Infrastructure Cost

| Service | Provider | Monthly Cost |
|---------|----------|-------------|
| Frontend | Vercel Hobby | $0 |
| Backend (2 instances) | Render Starter | $14 |
| Database | Neon Free/Pro | $0-19 |
| Redis | Upstash Free/Pro | $0-10 |
| Worker | Render Background Worker | $7 |
| **Total** | | **$21-50/month** |

---

## Tier 4: 5,000,000 Jobs — "Distributed Systems"

### Why Tier 3 Breaks

| Component | At 500K | At 5M | Failure Mode |
|-----------|---------|-------|-------------|
| PostgreSQL FTS | GIN index fast | 10x larger index, slow update lag | Index maintenance delays writes |
| FTS retrieve top-500 | ~50ms | 200-500ms | Ranking 5M docs is slow even with GIN |
| Single PostgreSQL | Handles reads | Read replica lag, write bottleneck | Need dedicated search infrastructure |
| Redis cache | Effective | Lower hit rate (more unique queries) | Need smarter caching + eviction |
| Job detail pages | On-demand render | 5M pages can't be pre-rendered | Need edge caching / ISR |

### Architecture

```
┌──────────────────────────────────────────────────────────┐
│  Vercel Edge Network (CDN)                               │
│  ├── ISR for /jobs/[id] pages (1hr stale-while-revald.)  │
│  ├── Edge-cached API responses (5min TTL)                │
│  └── Next.js 16 frontend (React 19)                     │
└───────────────────────┬──────────────────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────────────┐
│  API Gateway (rate limiting, auth, routing)               │
├─────────────┬───────────────────┬────────────────────────┤
│             │                   │                         │
│  ┌──────────▼────────┐  ┌──────▼──────────┐  ┌──────────▼───────┐
│  │  Search Service   │  │ Resume Service  │  │ Recommend Service │
│  │  (2+ instances)   │  │ (2+ instances)  │  │ (2+ instances)    │
│  │                   │  │                 │  │                   │
│  │  ES queries       │  │ PDF parse       │  │ Vector retrieval  │
│  │  Aggregation      │  │ Keyword extract │  │ Rerank (500 cand) │
│  │  facets           │  │ Embedding gen   │  │ Cache results     │
│  └────────┬──────────┘  └────────┬────────┘  └─────────┬────────┘
│           │                      │                      │
└───────────┼──────────────────────┼──────────────────────┼────────┘
            │                      │                      │
   ┌────────▼────────┐    ┌───────▼───────┐    ┌─────────▼───────┐
   │  Elasticsearch  │    │  Vector DB    │    │  Redis Cluster  │
   │  3-node cluster │    │  (pgvector or │    │  - Cache        │
   │  BM25 + aggs    │    │   Pinecone)   │    │  - Queue        │
   │  5M documents   │    │  5M vectors   │    │  - Rate limits  │
   └─────────────────┘    └───────────────┘    └─────────────────┘

   ┌──────────────────────────────────────────────────────────┐
   │  PostgreSQL (source of truth)                            │
   │  Job metadata, users, applications, recommendation logs  │
   │  NOT used for search queries (delegated to ES)           │
   │  Read replica for analytics / reporting                  │
   └──────────────────────────────────────────────────────────┘
```

### Key Changes

#### 4a. Search: Elasticsearch Cluster

At 5M jobs, Elasticsearch becomes the primary search engine:

- **3-node cluster** (2 data + 1 coordinator) for query parallelism and redundancy
- **BM25 scoring** with field boosting: `title^4`, `skills^3`, `description^1`, `requirements^1`
- **Aggregation-based facets** computed as a side-effect of every query — eliminates separate facet queries entirely
- **`search_after` cursor pagination** instead of offset-based (offset pagination degrades at depth)
- **Near-real-time indexing**: new jobs available in search within 1 second via CDC from PostgreSQL

**Why Elasticsearch at this tier (not Tier 3):**
PostgreSQL FTS with GIN indexes handles 500K well. At 5M, Elasticsearch's distributed architecture (shards across nodes) and purpose-built BM25 scoring outperform single-node Postgres FTS. The aggregation framework also eliminates the facet computation bottleneck.

#### 4b. Resume Matching: Vector Embeddings

Replace TF-IDF entirely with embedding-based semantic search:

```
Job Created/Updated
    │
    └──► Async Worker → Generate embedding (sentence-transformers)
                      → Store in vector DB (384-dim vector)

Resume Uploaded
    │
    ├──► Generate resume embedding (same model)
    │
    ├──► ANN Search: find top 500 nearest job vectors (~20ms)
    │    (Approximate Nearest Neighbor via HNSW index)
    │
    └──► Rerank: apply multi-signal scoring on 500 candidates
```

**Why embeddings over TF-IDF at this scale:**
- **Semantic understanding**: "Data Scientist" resume matches "ML Engineer" jobs even without keyword overlap. TF-IDF is purely lexical and misses this.
- **Constant query time**: HNSW index gives O(log N) ANN search regardless of dataset size. TF-IDF cosine similarity is O(N).
- **Memory efficient**: 5M × 384-dim float32 vectors = ~7.2GB, stored in a dedicated vector DB (not in application RAM).

**Implementation options:**

| Option | Pros | Cons | Cost |
|--------|------|------|------|
| **pgvector** (Postgres extension) | No new infrastructure | Slower ANN at 5M+, single-node | $0 (included in Postgres) |
| **Pinecone** (managed) | Sub-20ms queries at any scale, fully managed | Vendor lock-in | $70-200/month |
| **Qdrant** (self-hosted) | Open-source, fast, rich filtering | Ops burden | $50-100/month (infra) |

**Recommendation:** Start with pgvector (already using Postgres). If p99 latency exceeds 200ms, migrate to Pinecone — the retrieval interface stays the same.

#### 4c. Microservice Boundaries

Split the monolith along natural domain boundaries:

| Service | Responsibility | Scales Independently Because |
|---------|---------------|---------------------------|
| **Search Service** | ES queries, facets, pagination | Read-heavy, scales with user traffic |
| **Resume Service** | PDF parsing, keyword extraction, embedding generation | CPU-heavy, scales with upload volume |
| **Recommendation Service** | Vector retrieval, reranking, result caching | Memory-heavy, scales with match requests |

**Why split now (not earlier):**
A monolith is faster to develop, easier to debug, and simpler to deploy. We split only when services need to scale independently — the resume processing service might need 10x more workers during peak hours while the search service stays steady.

#### 4d. Frontend: Edge Caching + ISR

| Strategy | What | Why |
|----------|------|-----|
| **ISR** | `/jobs/[id]` pages regenerate on-demand, cached at edge for 1hr | Can't pre-build 5M pages at deploy time |
| **Edge cache** | API responses cached at CDN edge (5min TTL) | "software engineer san francisco" is queried thousands of times |
| **Stale-while-revalidate** | Serve cached results instantly, refresh in background | Job listings aren't real-time — 5-min staleness is fine |

#### 4e. Data Ingestion Pipeline

At 5M jobs, new job data arrives via bulk feeds (not just the admin API):

```
Job Feed (CSV/API) → Ingest Worker → PostgreSQL (source of truth)
                                         │
                         ┌───────────────┼──────────────────┐
                         ▼               ▼                  ▼
                   Elasticsearch    Vector DB         Redis (invalidate
                   (index update)  (new embedding)    cached facets)
```

**Change Data Capture (CDC):** PostgreSQL NOTIFY/LISTEN or Debezium streams row changes to downstream systems, ensuring eventual consistency without tight coupling.

### Infrastructure Cost

| Service | Provider | Monthly Cost |
|---------|----------|-------------|
| Frontend | Vercel Pro | $20 |
| Backend (6 instances across 3 services) | Render / AWS | $100-200 |
| PostgreSQL (primary + replica) | Neon / RDS | $50-100 |
| Elasticsearch (3-node) | Elastic Cloud | $100-200 |
| Vector DB | pgvector ($0) / Pinecone ($70-200) | $0-200 |
| Redis cluster | Upstash / ElastiCache | $20-50 |
| Workers (3 instances) | Render / AWS | $40-60 |
| **Total** | | **$330-810/month** |

---

## Cross-Cutting Concerns

### Rate Limiting

| Tier | Strategy |
|------|----------|
| 1-2 | None needed (low traffic) |
| 3 | Redis sliding window — 100 req/min for search, 10/min for resume match |
| 4 | API gateway level (Kong / AWS API Gateway / Cloudflare) |

### Monitoring & Observability

| Tier | Strategy |
|------|----------|
| 1-2 | Render logs, Vercel analytics |
| 3 | Structured JSON logging, Sentry for errors, basic latency dashboards |
| 4 | Distributed tracing (OpenTelemetry), Grafana dashboards, p95/p99 latency alerts |

### Testing at Scale

Use the existing `seed_data.py` with configurable job counts to benchmark each tier boundary:
- At what N does LIKE search exceed 1s?
- At what N does TF-IDF build OOM?
- At what N does resume match exceed 5s?

Load test with k6 or Locust to find QPS limits before scaling up.

---

## Migration Playbook

### Tier 1 → Tier 2 (half-day)

1. Add FTS5 virtual table + sync triggers to `database.py`
2. Replace LIKE queries with FTS5 MATCH
3. Add `cachetools.TTLCache` for facets
4. Wrap `_rebuild_tfidf()` in a background thread
5. Optimize `load_jobs()` to select only scoring-relevant columns

### Tier 2 → Tier 3 (1-2 weeks)

1. Provision PostgreSQL (Neon) and Redis (Upstash)
2. Create SQLAlchemy models + Alembic migrations
3. Implement PostgreSQL FTS search (replace SQLite + TF-IDF for keyword search)
4. Implement retrieve-rerank pipeline for resume matching
5. Add Redis Queue worker for async resume processing
6. Update frontend for async match results (polling)
7. Data migration: export SQLite → PostgreSQL

### Tier 3 → Tier 4 (1-2 months)

1. Deploy Elasticsearch cluster, create index mappings, backfill from PostgreSQL
2. Implement embedding pipeline (sentence-transformers + pgvector/Pinecone)
3. Split monolith into 3 services (search, resume, recommendation)
4. Add API gateway with rate limiting and auth
5. Configure Vercel ISR for job pages
6. Set up CDC pipeline for real-time index sync
7. Implement monitoring, alerting, distributed tracing

---

## Cost vs. Scale Summary

```
Monthly    │
Cost ($)   │
           │                                          ┌──── Tier 4
 800 ─ ─ ─ │─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─┤  $330-810
           │                                       ╱
 300 ─ ─ ─ │─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ╱─ ─ ─
           │                                  ╱
  50 ─ ─ ─ │─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─┌────╱─ ─ ─ ─    Tier 3: $21-50
           │                          ╱ │
   0 ─ ─ ─ ├──────────────────────────┤──┤───────────
           │  Tier 1: $0  Tier 2: $0 │  │
           └──────────┬───────────┬───┼──┼──────┬────
                    500       5,000  │ 500K   5M    Jobs
                                     │
                              Inflection point:
                           Free tier → paid infra
```

---

## Decision Records

### DR-001: Why PostgreSQL over MySQL?
- Native `tsvector` + GIN full-text search with ranking (MySQL's FULLTEXT lacks ranking control)
- `pgvector` extension for vector search (MySQL has no equivalent)
- JSONB type with GIN indexing for skills array queries (MySQL's JSON has weaker indexing)
- Superior async driver ecosystem for Python (asyncpg)

### DR-002: Why Retrieve-Rerank over Brute-Force?
The current brute-force approach in `keyword_matcher.py` is O(N) in both memory and CPU. At 500K, this means loading 5GB of job data and scoring every single job for every resume — 30+ seconds per request. Retrieve-rerank reduces this to O(log N + K) where K=500. This is the standard pattern used by production recommendation systems at LinkedIn, Indeed, and Netflix.

### DR-003: Why Not Embeddings from Day 1?
Embeddings require: a model to serve, an embedding pipeline, a vector store — 3 new pieces of infrastructure. For 10K jobs, TF-IDF cosine similarity captures 80%+ of the signal that embeddings would provide. The additional semantic understanding (matching "Data Scientist" to "ML Engineer") only matters when the job corpus is large enough to have meaningful semantic diversity. Premature optimization.

### DR-004: Why Monolith-First?
A monolithic FastAPI app (`main.py`) is faster to develop, easier to debug, and simpler to deploy than microservices. Martin Fowler's "MonolithFirst" principle. Split only when services need to scale independently or when the codebase is too large for one team. For a 10K-job career site, a single 300-line Python file is the right level of complexity.

### DR-005: Why SQLite for Phase 1?
SQLite with WAL mode provides excellent read concurrency, zero configuration, and a single-file database that deploys anywhere. For a read-heavy job board with ~10K jobs, it outperforms PostgreSQL on single-machine latency (no network hop, no connection overhead). The trade-off (single-writer, no full-text search) only matters at 50K+ jobs.
