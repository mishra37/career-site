"""Tests for the TF-IDF search index."""

from __future__ import annotations

from tfidf_index import TFIDFIndex
from tests.conftest import SAMPLE_JOBS


def _build_index(jobs=None):
    index = TFIDFIndex()
    index.build(jobs or SAMPLE_JOBS)
    return index


class TestBuild:
    def test_build_index(self):
        index = _build_index()
        assert index.is_built
        assert len(index.job_ids) == len(SAMPLE_JOBS)

    def test_build_empty(self):
        index = TFIDFIndex()
        index.build([])
        assert not index.is_built

    def test_rebuild(self):
        index = _build_index()
        assert index.is_built
        # Rebuild with fewer jobs
        index.build(SAMPLE_JOBS[:3])
        assert len(index.job_ids) == 3


class TestSearch:
    def test_search_relevance(self):
        index = _build_index()
        results = index.search("python machine learning")
        assert len(results) > 0
        # Data Scientist (job-4) should rank high
        top_ids = [r[0] for r in results[:3]]
        assert "job-4" in top_ids

    def test_search_nursing(self):
        index = _build_index()
        results = index.search("patient care nursing")
        assert len(results) > 0
        # Nurse (job-3) should rank first
        assert results[0][0] == "job-3"

    def test_search_empty_query(self):
        index = _build_index()
        results = index.search("")
        assert results == []

    def test_search_no_match(self):
        index = _build_index()
        results = index.search("quantum submarine")
        # Might return some very low scores or empty
        if results:
            assert results[0][1] < 0.1

    def test_search_not_built(self):
        index = TFIDFIndex()
        assert index.search("python") == []


class TestResumeScoring:
    def test_resume_scoring(self):
        index = _build_index()
        resume = "Python developer with 5 years experience in React and AWS"
        scores = index.score_resume(resume)
        assert len(scores) == len(SAMPLE_JOBS)
        # Engineering jobs should score higher than nurse/marketing
        assert scores["job-1"] > scores["job-3"]
        assert scores["job-1"] > scores["job-5"]

    def test_resume_scoring_empty(self):
        index = _build_index()
        scores = index.score_resume("")
        assert scores == {}

    def test_resume_scoring_all_floats(self):
        index = _build_index()
        scores = index.score_resume("Python developer")
        for score in scores.values():
            assert isinstance(score, float)
            assert 0.0 <= score <= 1.0
