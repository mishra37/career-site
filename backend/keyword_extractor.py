"""
Keyword Extractor — extracts structured keywords from resume text.

Strategy:
  1. Normalise text (lowercase, collapse whitespace)
  2. Match multi-word skills FIRST (e.g. "machine learning", "next.js")
     — these would be lost if we only checked single tokens.
  3. Match single-word skills from a curated dictionary.
  4. Detect experience level via keyword indicators.
  5. Detect years of experience via regex patterns.
  6. Detect education credentials.
  7. Detect primary domains (engineering, healthcare, etc.) by counting
     domain-indicator hits — needs ≥2 hits to register.

Why a curated dictionary instead of NLP/TF-IDF?
  • Deterministic and explainable — you can see exactly why a keyword matched.
  • Zero external model downloads (no NLTK data, no spaCy models).
  • Easily extended — just add terms to the sets below.
  • Fast — O(n) scan over the text for each skill.
"""

from __future__ import annotations

import re
from datetime import date
from models import ExtractedKeywords, WorkEntry

# =====================================================================
# Skills Dictionaries
# =====================================================================

MULTI_WORD_SKILLS: set[str] = {
    # Engineering & CS
    "machine learning", "deep learning", "natural language processing",
    "computer vision", "data science", "data engineering", "data analysis",
    "software engineering", "web development", "mobile development",
    "full stack", "front end", "back end", "cloud computing",
    "artificial intelligence", "neural networks", "distributed systems",
    "system design", "object oriented", "functional programming",
    "test driven", "continuous integration", "continuous deployment",
    "version control", "code review", "agile methodology",
    "project management", "product management", "program management",
    "user experience", "user interface", "user research",
    "graphic design", "visual design", "interaction design",
    "content strategy", "content marketing", "digital marketing",
    "search engine optimization", "social media marketing",
    "public relations", "brand management", "market research",
    "financial analysis", "financial modeling", "risk management",
    "supply chain", "operations management", "quality assurance",
    "human resources", "talent acquisition", "employee relations",
    "patient care", "clinical research", "electronic health records",
    "regulatory compliance", "contract negotiation", "intellectual property",
    "customer success", "account management", "business development",
    "sales operations", "revenue operations",
    "next.js", "node.js", "vue.js", "express.js", "nest.js",
    "react native", "ruby on rails",
    "amazon web services", "google cloud", "microsoft azure",
    "rest api", "rest apis", "graphql api",
    "ci/cd", "ci cd",
    "unit testing", "integration testing", "end to end testing",
    "data visualization", "business intelligence",
    "a/b testing", "ab testing",
    "cross functional",
    "adobe creative suite", "adobe photoshop", "adobe illustrator",
    "design systems", "design thinking",
    "curriculum development", "classroom management",
    "team leadership", "team management",
    "budget management", "vendor management",
    "dental hygiene", "pharmacy technician",
    "civil engineering", "structural engineering", "mechanical engineering",
    "legal research", "case management",
    "performance management", "compensation and benefits",
    "pivot tables",
    "event planning", "hotel management", "food service",
    "guest relations", "revenue management", "front desk operations",
    "banquet coordination", "menu planning", "food safety",
    "wedding planning", "conference planning",
}

SINGLE_WORD_SKILLS: set[str] = {
    # Programming Languages
    "python", "javascript", "typescript", "java", "kotlin", "swift",
    "rust", "golang", "ruby", "php", "scala", "haskell",
    "c++", "c#", "r", "matlab", "julia", "perl", "lua",
    "html", "css", "sass", "less",
    "sql", "nosql", "graphql",
    # Frameworks & Libraries
    "react", "angular", "vue", "svelte", "django", "flask", "fastapi",
    "spring", "express", "rails", "laravel", "nextjs",
    "tailwind", "bootstrap", "material",
    "tensorflow", "pytorch", "keras", "scikit",
    "pandas", "numpy", "matplotlib", "seaborn",
    "redux", "mobx", "zustand",
    # Databases
    "postgresql", "postgres", "mysql", "sqlite", "oracle",
    "mongodb", "dynamodb", "cassandra", "couchdb",
    "redis", "memcached", "elasticsearch",
    "neo4j",
    # Cloud & DevOps
    "aws", "azure", "gcp", "heroku", "vercel", "netlify",
    "docker", "kubernetes", "terraform", "ansible", "jenkins",
    "circleci", "github", "gitlab", "bitbucket",
    "nginx", "apache",
    "linux", "unix", "bash",
    # Tools & Platforms
    "git", "jira", "confluence", "slack", "notion",
    "figma", "sketch", "invision", "zeplin", "framer",
    "webpack", "vite", "rollup", "babel", "eslint",
    "jest", "mocha", "cypress", "playwright", "selenium",
    "postman", "swagger",
    "tableau", "powerbi", "looker",
    "salesforce", "hubspot", "zendesk",
    "quickbooks", "sap", "netsuite",
    # Concepts & Methodologies
    "agile", "scrum", "kanban", "lean",
    "devops", "mlops",
    "microservices", "serverless", "api",
    "oauth", "jwt", "authentication",
    "encryption", "security", "compliance",
    "accessibility", "wcag",
    "seo", "sem", "ppc",
    "crm", "erp", "saas",
    "etl", "pipeline",
    "hipaa", "gdpr", "sox",
    "autocad", "revit",
    # Soft Skills & Business
    "leadership", "communication", "collaboration",
    "mentoring", "coaching", "negotiation",
    "budgeting", "forecasting", "analytics",
    "copywriting",
    "excel", "powerpoint",
}

# =====================================================================
# Experience-level indicators
# =====================================================================

LEVEL_PATTERNS: dict[str, list[str]] = {
    "intern": ["intern", "internship", "co-op", "coop"],
    "entry": ["entry level", "entry-level", "junior", "associate",
              "new grad", "recent graduate", "0-2 years"],
    "mid": ["mid level", "mid-level", "2-4 years", "3-5 years",
            "intermediate"],
    "senior": ["senior", "sr.", "5+ years", "5-7 years", "6+ years",
               "7+ years", "8+ years", "experienced"],
    "lead": ["lead", "tech lead", "team lead", "principal", "staff"],
    "manager": ["manager", "management", "managing"],
    "director": ["director", "head of", "vp", "vice president"],
    "executive": ["executive", "chief", "c-level", "cto", "ceo",
                  "cfo", "coo", "cpo"],
}

# =====================================================================
# Domain indicators — need ≥2 hits to register
# =====================================================================

DOMAIN_KEYWORDS: dict[str, list[str]] = {
    "engineering": [
        "software", "engineer", "developer", "programming", "code",
        "coding", "technical", "backend", "frontend", "fullstack",
        "devops", "infrastructure", "platform", "systems",
    ],
    "data science": [
        "data science", "machine learning", "deep learning", "ai",
        "artificial intelligence", "nlp", "computer vision",
        "statistics", "analytics", "data analysis", "neural",
    ],
    "design": [
        "ui design", "ux design", "user experience", "user interface",
        "figma", "sketch", "prototyping", "wireframe", "visual design",
        "graphic design", "creative director", "branding",
        "interaction design", "design systems",
    ],
    "marketing": [
        "marketing", "seo", "sem", "social media", "content",
        "campaign", "brand", "advertising", "digital marketing",
        "growth", "acquisition",
    ],
    "sales": [
        "sales", "revenue", "quota", "pipeline", "prospecting",
        "account", "b2b", "b2c", "crm", "salesforce",
        "business development",
    ],
    "finance": [
        "finance", "accounting", "financial", "budget", "audit",
        "tax", "revenue", "bookkeeping", "quickbooks", "gaap",
        "forecasting",
    ],
    "healthcare": [
        "healthcare", "medical", "clinical", "patient", "nursing",
        "nurse", "pharmacy", "dental", "hipaa", "ehr", "diagnosis",
        "treatment", "hospital",
    ],
    "hr": [
        "human resources", "hr", "recruiting", "talent", "hiring",
        "onboarding", "payroll", "benefits", "compensation",
        "employee relations",
    ],
    "legal": [
        "legal", "law", "attorney", "lawyer", "contract",
        "compliance", "litigation", "regulatory",
        "intellectual property", "patent",
    ],
    "education": [
        "education", "teaching", "teacher", "curriculum",
        "classroom", "student", "academic", "instruction",
        "learning", "pedagogy",
    ],
    "operations": [
        "operations", "supply chain", "logistics", "procurement",
        "inventory", "warehouse", "manufacturing",
        "process improvement", "lean", "six sigma",
    ],
    "product": [
        "product management", "product manager", "roadmap",
        "backlog", "stakeholder", "product strategy",
        "user stories", "sprint planning",
    ],
    "customer success": [
        "customer success", "customer support", "customer service",
        "client relations", "retention", "churn", "nps",
    ],
    "hospitality": [
        "hospitality", "hotel", "restaurant", "guest", "tourism",
        "catering", "front desk", "concierge", "chef", "food service",
        "event planning", "banquet", "resort", "lodging",
    ],
}

# =====================================================================
# Stopwords (excluded from generic token extraction)
# =====================================================================

STOPWORDS: frozenset[str] = frozenset({
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to",
    "for", "of", "with", "by", "from", "is", "are", "was", "were",
    "be", "been", "being", "have", "has", "had", "do", "does", "did",
    "will", "would", "could", "should", "may", "might", "can", "shall",
    "must", "need", "it", "its", "this", "that", "these", "those",
    "i", "me", "my", "we", "our", "you", "your", "he", "she", "they",
    "them", "their", "who", "which", "what", "where", "when", "why",
    "how", "all", "each", "every", "both", "few", "more", "most",
    "other", "some", "such", "no", "not", "only", "same", "so",
    "than", "too", "very", "just", "about", "above", "after", "again",
    "also", "any", "as", "because", "before", "between", "during",
    "into", "over", "through", "under", "up", "out", "if", "then",
    "here", "there", "new", "work", "working", "worked", "experience",
    "experienced", "using", "used", "use", "including", "include",
    "well", "able", "ability", "strong", "excellent", "good", "great",
    "best", "etc", "required", "preferred", "minimum", "maximum",
    "years", "year", "responsible", "responsibilities",
})

# =====================================================================
# Role Category Mapping (job title → category)
# =====================================================================

ROLE_CATEGORY_MAP: dict[str, list[str]] = {
    "swe": [
        "software engineer", "software developer", "web developer",
        "frontend developer", "backend developer", "full-stack developer",
        "full stack developer", "mobile developer", "ios developer",
        "android developer", "platform engineer", "site reliability",
        "devops engineer", "infrastructure engineer", "embedded engineer",
        "qa engineer", "sdet", "automation engineer", "cloud engineer",
        "security engineer", "build engineer",
    ],
    "ml": [
        "machine learning engineer", "ml engineer", "deep learning",
        "ai engineer", "ai researcher", "research engineer",
        "nlp engineer", "computer vision engineer", "applied scientist",
        "mlops engineer",
    ],
    "data_science": [
        "data scientist", "data analyst", "analytics engineer",
        "data engineer", "business intelligence", "research scientist",
        "statistician",
    ],
    "product": [
        "product manager", "product owner", "program manager",
        "technical program manager", "product lead",
    ],
    "design": [
        "ux designer", "ui designer", "product designer",
        "graphic designer", "visual designer", "interaction designer",
        "design lead", "ux researcher",
    ],
    "management": [
        "engineering manager", "director of engineering", "vp of engineering",
        "cto", "tech lead", "team lead", "principal engineer",
        "staff engineer",
    ],
}

# =====================================================================
# Work Experience Section Patterns
# =====================================================================

_MONTH = (
    r"(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
    r"jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|"
    r"dec(?:ember)?)"
)

# Matches date ranges like "Jan 2020 - Present", "2018 - 2022"
_DATE_RANGE_RE = re.compile(
    rf"(?:{_MONTH}\s*\.?\s*)?(\d{{4}})\s*[-–—]+\s*"
    rf"(?:(present|current|now|ongoing)|(?:{_MONTH}\s*\.?\s*)?(\d{{4}}))",
    re.IGNORECASE,
)

# Section headers for work experience
_WORK_SECTION_RE = re.compile(
    r"^[ \t]*(?:work\s+)?(?:experience|employment|professional\s+experience|"
    r"work\s+history|career\s+history|relevant\s+experience)"
    r"[ \t]*:?[ \t]*$",
    re.MULTILINE | re.IGNORECASE,
)

# Section headers that end the work section
_SECTION_END_RE = re.compile(
    r"^[ \t]*(?:education|skills|certifications?|projects?|publications?|"
    r"awards?|volunteer|interests|references|summary|objective|"
    r"technical\s+skills|core\s+competencies|languages)"
    r"[ \t]*:?[ \t]*$",
    re.MULTILINE | re.IGNORECASE,
)

# Education status patterns
_PURSUING_RE = re.compile(
    r"(?:currently|presently)\s+(?:pursuing|studying|enrolled|completing)"
    r"|(?:pursuing|studying)\s+(?:a\s+)?(?:bachelor|master|ph\.?d|mba|degree)"
    r"|candidate\s+for\s+(?:a\s+)?(?:bachelor|master|ph\.?d|mba)"
    r"|(?:bachelor|master|ph\.?d|mba)\s+(?:candidate|student)",
    re.IGNORECASE,
)

_GRADUATION_YEAR_RE = re.compile(
    r"(?:expected|anticipated)\s+(?:graduation|completion)\s*:?\s*"
    r"(?:(?:spring|summer|fall|winter|jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|"
    r"apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|"
    r"oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\s+)?(\d{4})"
    r"|(?:graduating|graduation)\s*:?\s*"
    r"(?:(?:spring|summer|fall|winter|jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|"
    r"apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|"
    r"oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\s+)?(\d{4})"
    r"|class\s+of\s+(\d{4})",
    re.IGNORECASE,
)


# =====================================================================
# Extractor
# =====================================================================


class KeywordExtractor:
    """
    Extracts structured keywords from raw resume text.

    Usage:
        extractor = KeywordExtractor()
        result = extractor.extract("John Doe — 5 years React …")
    """

    # ── public API ──────────────────────────────────────────

    def extract(self, text: str) -> ExtractedKeywords:
        normalised = self._normalise(text)

        # Existing extractions
        skills = self._extract_skills(normalised)
        keyword_level = self._detect_level(normalised)
        years = self._detect_years(normalised)
        education = self._detect_education(normalised)
        domains = self._detect_domains(normalised)

        # New extractions (use original text for structure-aware parsing)
        work_history = self._extract_work_history(text)
        calculated_years = self._calculate_total_years(work_history)
        role_categories = self._detect_role_categories(work_history)
        education_status, graduation_proximity = self._detect_education_status(text)

        # Enhanced level inference
        level = self._infer_level(
            keyword_level, years, calculated_years,
            education_status, graduation_proximity, work_history,
        )

        # Use best years estimate
        best_years = self._best_years_estimate(years, calculated_years)

        return ExtractedKeywords(
            skills=skills,
            experience_level=level,
            years_of_experience=best_years,
            education=education,
            domains=domains,
            work_history=work_history,
            calculated_years=calculated_years,
            role_categories=role_categories,
            education_status=education_status,
            graduation_proximity=graduation_proximity,
        )

    # ── internal helpers ────────────────────────────────────

    @staticmethod
    def _normalise(text: str) -> str:
        text = text.lower()
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    @staticmethod
    def _extract_skills(text: str) -> list[str]:
        found: list[str] = []

        # Multi-word skills first (longer phrases before fragments)
        for skill in sorted(MULTI_WORD_SKILLS, key=len, reverse=True):
            # Build a pattern that respects word boundaries but allows
            # punctuation variants (e.g. "node.js" vs "nodejs").
            escaped = re.escape(skill)
            pattern = rf"(?<![a-z]){escaped}(?![a-z])"
            if re.search(pattern, text):
                found.append(skill)

        # Single-word skills
        words = set(re.findall(r"[a-z0-9+#/.]+", text))
        for skill in SINGLE_WORD_SKILLS:
            if skill in words:
                # Skip if already captured by a multi-word match
                if not any(skill in mw for mw in found):
                    found.append(skill)

        return sorted(set(found))

    @staticmethod
    def _detect_level(text: str) -> str | None:
        # Check from most-senior to most-junior so we pick the highest
        for level in reversed(list(LEVEL_PATTERNS)):
            for indicator in LEVEL_PATTERNS[level]:
                if indicator in text:
                    return level
        return None

    @staticmethod
    def _detect_years(text: str) -> int | None:
        patterns = [
            r"(\d+)\+?\s*years?\s*(?:of\s+)?(?:experience|expertise|professional)",
            r"(\d+)\+?\s*years?\s*(?:in|of|working)",
            r"over\s+(\d+)\s*years?",
        ]
        best: int | None = None
        for pat in patterns:
            for m in re.findall(pat, text):
                y = int(m)
                if best is None or y > best:
                    best = y
        return best

    @staticmethod
    def _detect_education(text: str) -> list[str]:
        found: list[str] = []
        checks = [
            ("PhD", r"\bph\.?d\b|\bdoctorate\b|\bdoctoral\b"),
            ("Master's", r"\bmaster'?s?\b|\bm\.?s\.?\b|\bm\.?b\.?a\.?\b"),
            ("Bachelor's", r"\bbachelor'?s?\b|\bb\.?s\.?\b|\bb\.?a\.?\b|\bundergraduate\b"),
        ]
        for label, pattern in checks:
            if re.search(pattern, text):
                found.append(label)
        return found

    @staticmethod
    def _detect_domains(text: str) -> list[str]:
        scores: dict[str, int] = {}
        for domain, keywords in DOMAIN_KEYWORDS.items():
            hits = sum(1 for kw in keywords if kw in text)
            if hits >= 2:
                scores[domain] = hits
        return sorted(scores, key=scores.get, reverse=True)  # type: ignore[arg-type]

    # ── work history extraction ────────────────────────────────

    @staticmethod
    def _extract_work_history(text: str) -> list[WorkEntry]:
        """Parse work experience entries from resume text."""
        current_year = date.today().year

        # Try to find a dedicated work experience section
        work_text = text
        section_match = _WORK_SECTION_RE.search(text)
        if section_match:
            start = section_match.end()
            end_match = _SECTION_END_RE.search(text, start)
            work_text = text[start:end_match.start()] if end_match else text[start:]

        entries: list[WorkEntry] = []
        lines = work_text.split("\n")

        for i, line in enumerate(lines):
            # Look for date ranges on this line
            date_match = _DATE_RANGE_RE.search(line)
            if not date_match:
                continue

            start_year = int(date_match.group(1))
            is_present = date_match.group(2) is not None
            end_year = current_year if is_present else (
                int(date_match.group(3)) if date_match.group(3) else current_year
            )

            # Sanity check years
            if start_year < 1980 or start_year > current_year + 1:
                continue
            if end_year < start_year:
                continue

            duration = max(end_year - start_year, 0.5)

            # Extract title and company from this line or adjacent lines
            title, company = _extract_title_and_company(lines, i, date_match)
            if title:
                entries.append(WorkEntry(
                    title=title,
                    company=company,
                    duration_years=round(duration, 1),
                ))

        return entries

    @staticmethod
    def _calculate_total_years(work_history: list[WorkEntry]) -> float | None:
        """Sum durations from work entries, capping at calendar span."""
        if not work_history:
            return None

        durations = [e.duration_years for e in work_history if e.duration_years]
        if not durations:
            return None

        total = sum(durations)
        return round(total, 1)

    @staticmethod
    def _detect_role_categories(work_history: list[WorkEntry]) -> list[str]:
        """Map work history job titles to role categories."""
        if not work_history:
            return []

        category_counts: dict[str, int] = {}
        for entry in work_history:
            title_lower = entry.title.lower()
            for category, keywords in ROLE_CATEGORY_MAP.items():
                for kw in keywords:
                    if kw in title_lower:
                        category_counts[category] = category_counts.get(category, 0) + 1
                        break

        if not category_counts:
            return []

        return sorted(category_counts, key=category_counts.get, reverse=True)  # type: ignore[arg-type]

    @staticmethod
    def _detect_education_status(text: str) -> tuple[str | None, str | None]:
        """Detect if candidate is currently pursuing a degree and graduation proximity."""
        text_lower = text.lower()

        # Check for pursuing indicators
        is_pursuing = bool(_PURSUING_RE.search(text_lower))

        # Check for graduation year
        grad_year: int | None = None
        grad_match = _GRADUATION_YEAR_RE.search(text_lower)
        if grad_match:
            for g in grad_match.groups():
                if g and g.isdigit():
                    grad_year = int(g)
                    break

        if not is_pursuing and grad_year:
            # "Class of 2027" or "Expected graduation 2027" implies pursuing
            current_year = date.today().year
            if grad_year >= current_year:
                is_pursuing = True

        if not is_pursuing:
            # Check if education section mentions completed degrees without future dates
            if re.search(r"\b(?:bachelor|master|ph\.?d|mba)\b", text_lower):
                return "completed", None
            return None, None

        # Determine proximity
        current_year = date.today().year
        if grad_year:
            if grad_year - current_year > 1:
                return "pursuing", "far"
            else:
                return "pursuing", "near"

        return "pursuing", "near"  # default to near if no year found

    @staticmethod
    def _infer_level(
        keyword_level: str | None,
        years: int | None,
        calculated_years: float | None,
        education_status: str | None,
        graduation_proximity: str | None,
        work_history: list[WorkEntry],
    ) -> str | None:
        """Enhanced level inference combining multiple signals."""
        total_work_years = calculated_years or 0.0

        # 1. Student currently pursuing a degree with no/little work experience
        if education_status == "pursuing" and total_work_years < 1:
            if graduation_proximity == "far":
                return "intern"
            return "entry"

        # 2. Student pursuing but has significant work experience → use years
        # 3. Use best years estimate
        best_years: float | None = None
        if calculated_years is not None and years is not None:
            best_years = max(calculated_years, float(years))
        elif calculated_years is not None:
            best_years = calculated_years
        elif years is not None:
            best_years = float(years)

        if best_years is not None:
            if best_years < 1:
                return "intern"
            elif best_years <= 2:
                return "entry"
            elif best_years <= 4:
                return "mid"
            elif best_years <= 7:
                return "senior"
            elif best_years <= 10:
                return "lead"
            else:
                return "director"

        # 4. Fall back to keyword level
        if keyword_level:
            return keyword_level

        return None

    @staticmethod
    def _best_years_estimate(
        parsed_years: int | None,
        calculated_years: float | None,
    ) -> int | None:
        """Return the best estimate of total years of experience."""
        if calculated_years is not None and parsed_years is not None:
            return int(round(max(calculated_years, float(parsed_years))))
        if calculated_years is not None:
            return int(round(calculated_years))
        return parsed_years


# =====================================================================
# Helpers (module-level, used by KeywordExtractor)
# =====================================================================


def _extract_title_and_company(
    lines: list[str], date_line_idx: int, date_match: re.Match,
) -> tuple[str | None, str | None]:
    """Extract job title and company from the line with a date range or adjacent lines."""
    line = lines[date_line_idx]

    # Remove the date portion to isolate title/company info
    text_before_date = line[:date_match.start()].strip()
    text_after_date = line[date_match.end():].strip()

    # Try to find candidate text
    candidate = text_before_date
    if not candidate and text_after_date:
        candidate = text_after_date

    # Also check the line above (common resume format: title on one line, date below)
    if not candidate and date_line_idx > 0:
        candidate = lines[date_line_idx - 1].strip()

    if not candidate:
        return None, None

    # Clean up: remove bullet points, leading/trailing separators
    candidate = re.sub(r"^[\s\-•*·]+", "", candidate)
    candidate = re.sub(r"[\s|,]+$", "", candidate)

    # Extract company BEFORE splitting title
    company: str | None = None
    title = candidate

    # "Title at Company" → split into title + company
    at_split = re.split(r"\s+at\s+", candidate, maxsplit=1)
    if len(at_split) == 2 and len(at_split[0]) >= 3:
        title = at_split[0].strip()
        company = at_split[1].strip().rstrip(" |,–—")

    # "Title, Company" or "Title | Company" → split into title + company
    if not company:
        parts = re.split(r"\s*[|–—]\s*|\s*,\s+", candidate, maxsplit=1)
        if len(parts) == 2 and len(parts[0]) >= 3:
            title = parts[0].strip()
            company = parts[1].strip().rstrip(" |,–—")

    # Validate title
    if len(title) < 3 or len(title) > 80:
        return None, None

    # Discard if it looks like a bullet point description
    if title.lower().startswith(("developed ", "built ", "managed ", "led ",
                                  "created ", "designed ", "implemented ")):
        return None, None

    # Validate company
    if company and (len(company) < 2 or len(company) > 60):
        company = None

    return title, company
