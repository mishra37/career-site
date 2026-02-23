"""
Keyword Matcher — scores and ranks jobs against extracted resume keywords.

Combined scoring (100 points max):
  ┌──────────────────────┬────────┬───────────────────────────────────────┐
  │ Signal               │ Weight │ How                                   │
  ├──────────────────────┼────────┼───────────────────────────────────────┤
  │ TF-IDF similarity    │ 25 pts │ cosine similarity × 25                │
  │ Skill match          │ 35 pts │ % of job skills found in resume       │
  │ Title relevance      │  5 pts │ resume keywords that appear in title  │
  │ Domain alignment     │ 15 pts │ detected domain matches department    │
  │ Level proximity      │ 10 pts │ experience level distance scoring     │
  │ Role category match  │ 10 pts │ work history roles match job type     │
  └──────────────────────┴────────┴───────────────────────────────────────┘

  Plus a domain penalty (0.3×–0.5×) for completely unrelated fields
  (e.g. a software engineer resume vs. a nursing role).
"""

from __future__ import annotations

from models import Job, MatchResult, ExtractedKeywords
from keyword_extractor import DOMAIN_KEYWORDS

# Experience-level ordering for distance calculation
_LEVEL_ORDER: list[str] = [
    "Intern", "Entry", "Mid", "Senior", "Lead",
    "Manager", "Director", "VP", "C-Suite",
]
_LEVEL_INDEX: dict[str, int] = {
    lvl.lower(): i for i, lvl in enumerate(_LEVEL_ORDER)
}

# Maps role categories to keywords found in job titles/departments
_JOB_ROLE_KEYWORDS: dict[str, list[str]] = {
    "swe": [
        "software", "developer", "frontend", "backend", "full-stack",
        "full stack", "devops", "sre", "platform", "mobile",
        "ios", "android", "qa", "embedded", "engineer",
    ],
    "ml": [
        "machine learning", "ml ", "deep learning", "ai ",
        "artificial intelligence", "nlp", "computer vision",
        "applied scientist",
    ],
    "data_science": [
        "data scien", "data analy", "analytics",
        "data engineer", "business intelligence",
    ],
    "product": ["product manager", "product owner", "program manager"],
    "design": ["designer", "ux ", "ui ", "design lead"],
    "management": [
        "engineering manager", "director of engineering",
        "vp of engineering", "cto",
    ],
}

# Maps role categories to compatible departments
_DEPT_AFFINITY: dict[str, list[str]] = {
    "swe": ["engineering"],
    "ml": ["engineering", "data science", "ai"],
    "data_science": ["data science", "ai", "engineering"],
    "product": ["product"],
    "design": ["design"],
    "management": ["engineering"],
}


class KeywordMatcher:
    """
    Matches a set of extracted resume keywords against the job catalog.

    Usage:
        matcher = KeywordMatcher()
        results = matcher.match(extracted_keywords, jobs, tfidf_scores)
    """

    MIN_SCORE = 15         # jobs below this are excluded (raised for 1000 jobs)
    MAX_RESULTS = 100      # return top N

    # ── public API ──────────────────────────────────────────

    def match(
        self,
        keywords: ExtractedKeywords,
        jobs: list[Job],
        tfidf_scores: dict[str, float] | None = None,
    ) -> list[MatchResult]:
        results: list[MatchResult] = []

        for job in jobs:
            tfidf_score = (tfidf_scores or {}).get(job.id, 0.0)
            score, reasons = self._score_job(keywords, job, tfidf_score)
            if score >= self.MIN_SCORE:
                results.append(
                    MatchResult(
                        job=job,
                        score=min(round(score), 100),
                        reason=(
                            ". ".join(reasons[:3]) + "."
                            if reasons
                            else "Partial match based on your profile."
                        ),
                    )
                )

        results.sort(key=lambda r: r.score, reverse=True)
        return results[: self.MAX_RESULTS]

    # ── scoring logic ───────────────────────────────────────

    def _score_job(
        self,
        kw: ExtractedKeywords,
        job: Job,
        tfidf_score: float = 0.0,
    ) -> tuple[float, list[str]]:
        score = 0.0
        reasons: list[str] = []

        # ─── 1. TF-IDF text similarity (25 pts) ─────────────
        tfidf_pts = min(tfidf_score * 25, 25)
        score += tfidf_pts

        # ─── 2. Direct skill match (35 pts) ─────────────────
        job_skills_lower = [s.lower() for s in job.skills]
        matched_skills: list[str] = []

        for resume_skill in kw.skills:
            for js in job_skills_lower:
                if resume_skill == js:
                    matched_skills.append(js)
                    break

        unique_matched = list(dict.fromkeys(matched_skills))
        if job_skills_lower:
            skill_score = (len(unique_matched) / len(job_skills_lower)) * 35
            score += skill_score
            if unique_matched:
                display = [s.title() for s in unique_matched[:6]]
                reasons.append(f"Skills match: {', '.join(display)}")

        # ─── 3. Title relevance (5 pts) ────────────────────
        title_lower = job.title.lower()
        title_hits = sum(
            1 for sk in kw.skills if sk in title_lower
        )
        title_words = [
            w for w in title_lower.split()
            if len(w) > 2
        ]
        if title_words:
            title_score = min((title_hits / len(title_words)) * 5, 5)
            score += title_score

        # ─── 4. Domain alignment (15 pts) ───────────────────
        if kw.domains:
            job_dept = job.department.lower()
            domain_matched = False
            for det in kw.domains:
                if det in job_dept or job_dept in det:
                    score += 15
                    reasons.append(f"Domain alignment with {job.department}")
                    domain_matched = True
                    break
            if not domain_matched:
                for det in kw.domains:
                    hits = sum(
                        1
                        for dkw in DOMAIN_KEYWORDS.get(det, [])
                        if dkw in job.description.lower()
                    )
                    if hits >= 2:
                        score += 6
                        break

        # ─── 5. Experience-level bonus (10 pts) ─────────────
        if kw.experience_level:
            lvl_score = self._level_proximity(kw.experience_level, job.level)
            bonus = lvl_score * 10
            score += bonus
            if lvl_score > 0.6:
                reasons.append(f"Experience level aligns with {job.level} role")

        # ─── 6. Role category match (10 pts) ────────────────
        if kw.role_categories:
            role_pts = self._role_category_score(kw.role_categories, job)
            score += role_pts
            if role_pts >= 8:
                cat_display = kw.role_categories[0].replace("_", " ").upper()
                reasons.append(f"Your {cat_display} background matches this role")

        # ─── 7. Domain penalty ──────────────────────────────
        healthcare_job = "healthcare" in job.department.lower()
        healthcare_resume = "healthcare" in kw.domains
        if healthcare_job and not healthcare_resume:
            score *= 0.3
        elif (
            not healthcare_job
            and healthcare_resume
            and kw.domains
            and kw.domains[0] == "healthcare"
        ):
            score *= 0.5

        # ─── 7b. General cross-domain penalty ─────────────
        if kw.domains:
            job_dept_lower = job.department.lower()
            primary_domain = kw.domains[0]

            # Map of incompatible domain→department pairs
            _INCOMPATIBLE = {
                "engineering": {"design", "marketing", "hospitality & tourism", "human resources", "legal"},
                "design": {"engineering", "healthcare", "legal", "hospitality & tourism"},
                "hospitality": {"engineering", "data science", "legal", "finance"},
                "legal": {"engineering", "data science", "design", "hospitality & tourism"},
                "finance": {"engineering", "design", "healthcare", "hospitality & tourism"},
            }
            incompatible_depts = _INCOMPATIBLE.get(primary_domain, set())
            if incompatible_depts and job_dept_lower in incompatible_depts:
                # Skip penalty if role categories indicate tech background in tech job
                tech_cats = {"swe", "ml", "data_science", "management"}
                tech_depts = {"engineering", "data science", "ai & data science"}
                has_tech_bg = bool(tech_cats & set(kw.role_categories)) if kw.role_categories else False
                if not (has_tech_bg and job_dept_lower in tech_depts):
                    score *= 0.5

        return score, reasons

    # ── helpers ──────────────────────────────────────────────

    @staticmethod
    def _level_proximity(resume_level: str, job_level: str) -> float:
        """
        Return 0.0-1.0 based on how close the candidate's detected
        experience level is to the job's stated level.
        """
        ri = _LEVEL_INDEX.get(resume_level, -1)
        ji = _LEVEL_INDEX.get(job_level.lower(), -1)
        if ri < 0 or ji < 0:
            return 0.3          # unknown → neutral
        dist = abs(ri - ji)
        return {0: 1.0, 1: 0.7, 2: 0.4, 3: 0.2}.get(dist, 0.05)

    @staticmethod
    def _role_category_score(role_categories: list[str], job: Job) -> float:
        """Score 0-10 based on how well resume role categories match the job."""
        title_lower = job.title.lower()
        dept_lower = job.department.lower()

        # Check for direct title/dept keyword match (full 10 pts)
        for cat in role_categories:
            cat_keywords = _JOB_ROLE_KEYWORDS.get(cat, [])
            for kw in cat_keywords:
                if kw in title_lower or kw in dept_lower:
                    return 10.0

        # Check for department affinity (partial 5 pts)
        for cat in role_categories:
            for dept_kw in _DEPT_AFFINITY.get(cat, []):
                if dept_kw in dept_lower:
                    return 5.0

        return 0.0
