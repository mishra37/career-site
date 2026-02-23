"""
TF-IDF search index for CareerMatch.

Uses scikit-learn's TfidfVectorizer to build an in-memory index over job
documents. Supports two query modes:

1. search(query) — for the browse page keyword search, returns ranked job IDs
2. score_resume(text) — for resume matching, returns per-job similarity scores

The index builds in ~100-150ms for 1000 jobs and queries in <5ms.
Rebuilt on startup and when new jobs are added via the admin API.
"""

from __future__ import annotations

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class TFIDFIndex:
    """In-memory TF-IDF index over job documents."""

    def __init__(self) -> None:
        self.vectorizer = TfidfVectorizer(
            stop_words="english",
            max_features=8000,
            ngram_range=(1, 2),       # unigrams + bigrams
            sublinear_tf=True,        # log(1 + tf) dampening
            min_df=1,
            max_df=0.95,
        )
        self.tfidf_matrix = None      # sparse CSR matrix (n_jobs × n_features)
        self.job_ids: list[str] = []
        self._built = False

    @property
    def is_built(self) -> bool:
        return self._built

    def build(self, jobs: list[dict]) -> None:
        """
        Build the index from a list of job dicts.

        Each job is turned into a single document by concatenating fields with
        weighting: title ×4, department ×3, skills ×2, description ×1, requirements ×1.
        """
        if not jobs:
            self._built = False
            return

        self.job_ids = [j["id"] for j in jobs]
        documents = []

        for job in jobs:
            title = job.get("title", "")
            department = job.get("department", "")
            skills = job.get("skills", [])
            if isinstance(skills, str):
                skills = [skills]
            skills_text = " ".join(skills)
            description = job.get("description", "")
            requirements = job.get("requirements", [])
            if isinstance(requirements, str):
                requirements = [requirements]
            req_text = " ".join(requirements)

            # Weight fields by repeating them
            doc = " ".join([
                title, title, title, title,               # title ×4
                department, department, department,       # department ×3
                skills_text, skills_text,                 # skills ×2
                description,                              # description ×1
                req_text,                                 # requirements ×1
            ])
            documents.append(doc)

        self.tfidf_matrix = self.vectorizer.fit_transform(documents)
        self._built = True

    def search(self, query: str, top_n: int = 200) -> list[tuple[str, float]]:
        """
        Search for jobs matching a text query.

        Returns a list of (job_id, relevance_score) tuples sorted by score
        descending. Only returns results with score > 0.01.
        """
        if not self._built or not query.strip():
            return []

        query_vec = self.vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self.tfidf_matrix).flatten()

        # Get indices sorted by score descending
        ranked_indices = np.argsort(scores)[::-1][:top_n]

        results = []
        for i in ranked_indices:
            s = float(scores[i])
            if s > 0.01:
                results.append((self.job_ids[i], s))
            else:
                break  # since sorted, remaining are all <= 0.01

        return results

    def score_resume(self, resume_text: str) -> dict[str, float]:
        """
        Score all jobs against a resume text.

        Returns {job_id: cosine_similarity_score} for all jobs.
        Scores are 0.0 to 1.0 floats.
        """
        if not self._built or not resume_text.strip():
            return {}

        resume_vec = self.vectorizer.transform([resume_text])
        scores = cosine_similarity(resume_vec, self.tfidf_matrix).flatten()

        return {
            self.job_ids[i]: float(scores[i])
            for i in range(len(self.job_ids))
        }


# Singleton instance — initialized by main.py on startup
tfidf_index = TFIDFIndex()
