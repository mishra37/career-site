"""Tests for the keyword matching and scoring module."""

from __future__ import annotations

from keyword_matcher import KeywordMatcher
from models import ExtractedKeywords, Job, Salary


def _make_job(**overrides) -> Job:
    defaults = {
        "id": "test-1",
        "title": "Software Engineer",
        "company": "TestCo",
        "department": "Engineering",
        "industry": "Technology",
        "location": "San Francisco, CA",
        "type": "Full-time",
        "level": "Mid",
        "remote_type": "On-site",
        "salary": Salary(min=100000, max=150000),
        "description": "Build software applications.",
        "requirements": ["Python experience"],
        "responsibilities": ["Write code"],
        "skills": ["Python", "React", "AWS"],
        "posted_date": "2026-01-15",
    }
    defaults.update(overrides)
    return Job(**defaults)


def _make_keywords(**overrides) -> ExtractedKeywords:
    defaults = {
        "skills": ["python", "react", "aws"],
        "experience_level": "mid",
        "years_of_experience": 4,
        "education": ["Bachelor's"],
        "domains": ["engineering"],
    }
    defaults.update(overrides)
    return ExtractedKeywords(**defaults)


matcher = KeywordMatcher()


class TestSkillScoring:
    def test_high_skill_overlap(self):
        job = _make_job(skills=["Python", "React", "AWS"])
        kw = _make_keywords(skills=["python", "react", "aws"])
        results = matcher.match(kw, [job])
        assert len(results) == 1
        assert results[0].score > 50

    def test_no_skill_overlap(self):
        job = _make_job(skills=["Java", "Spring", "Oracle"])
        kw = _make_keywords(skills=["python", "react", "aws"])
        results = matcher.match(kw, [job])
        # Might still match from domain/level, but score should be lower
        if results:
            assert results[0].score < 50

    def test_more_skills_higher_score(self):
        job = _make_job(skills=["Python", "React", "AWS", "Docker", "PostgreSQL"])
        kw_few = _make_keywords(skills=["python"])
        kw_many = _make_keywords(skills=["python", "react", "aws", "docker"])
        r_few = matcher.match(kw_few, [job])
        r_many = matcher.match(kw_many, [job])
        if r_few and r_many:
            assert r_many[0].score >= r_few[0].score


class TestDomainPenalty:
    def test_healthcare_job_eng_resume(self):
        job = _make_job(
            department="Healthcare",
            skills=["Patient Care", "Clinical"],
        )
        kw = _make_keywords(domains=["engineering"])
        results = matcher.match(kw, [job])
        # Should be penalized heavily or filtered out
        if results:
            assert results[0].score < 30

    def test_eng_job_healthcare_resume(self):
        job = _make_job(department="Engineering")
        kw = _make_keywords(
            skills=["patient care", "clinical assessment"],
            domains=["healthcare"],
        )
        results = matcher.match(kw, [job])
        if results:
            assert results[0].score < 40


class TestLevelProximity:
    def test_exact_level_match(self):
        job = _make_job(level="Mid")
        kw = _make_keywords(experience_level="mid")
        results = matcher.match(kw, [job])
        assert len(results) >= 1

    def test_distant_level_low_bonus(self):
        job_exact = _make_job(id="exact", level="Mid")
        job_far = _make_job(id="far", level="Director")
        kw = _make_keywords(experience_level="entry")
        r_exact = matcher.match(kw, [job_exact])
        r_far = matcher.match(kw, [job_far])
        if r_exact and r_far:
            assert r_exact[0].score >= r_far[0].score


class TestScoreBounds:
    def test_score_max_100(self):
        job = _make_job(skills=["Python", "React", "AWS"])
        kw = _make_keywords()
        results = matcher.match(kw, [job])
        for r in results:
            assert r.score <= 100

    def test_score_min_threshold(self):
        job = _make_job(skills=["Obscure Skill 1", "Obscure Skill 2"])
        kw = _make_keywords(skills=["unrelated1", "unrelated2"], domains=[])
        results = matcher.match(kw, [job])
        # Results below MIN_SCORE should be filtered out
        for r in results:
            assert r.score >= matcher.MIN_SCORE


class TestTFIDFIntegration:
    def test_tfidf_boosts_score(self):
        job = _make_job()
        kw = _make_keywords()
        # Without TF-IDF
        results_no_tfidf = matcher.match(kw, [job], tfidf_scores=None)
        # With high TF-IDF score
        results_with_tfidf = matcher.match(
            kw, [job], tfidf_scores={job.id: 0.8}
        )
        if results_no_tfidf and results_with_tfidf:
            assert results_with_tfidf[0].score >= results_no_tfidf[0].score

    def test_reasons_populated(self):
        job = _make_job()
        kw = _make_keywords()
        results = matcher.match(kw, [job])
        assert len(results) >= 1
        assert results[0].reason  # non-empty reason string
