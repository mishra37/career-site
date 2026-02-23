"""Tests for the keyword extraction module."""

from __future__ import annotations

from keyword_extractor import KeywordExtractor

extractor = KeywordExtractor()


class TestSkillExtraction:
    def test_extract_common_skills(self):
        text = "Experience with Python, JavaScript, React, and Node.js"
        kw = extractor.extract(text)
        assert "python" in kw.skills
        assert "javascript" in kw.skills
        assert "react" in kw.skills

    def test_multi_word_skills(self):
        text = "Proficient in machine learning, natural language processing, and project management"
        kw = extractor.extract(text)
        assert "machine learning" in kw.skills

    def test_no_duplicate_skills(self):
        text = "Python Python Python developer with Python skills"
        kw = extractor.extract(text)
        assert kw.skills.count("python") == 1


class TestExperienceLevel:
    def test_detect_senior(self):
        text = "Senior Software Engineer with extensive experience"
        kw = extractor.extract(text)
        assert kw.experience_level == "senior"

    def test_detect_entry(self):
        text = "Entry level position, junior developer looking for first role"
        kw = extractor.extract(text)
        assert kw.experience_level in ("entry", "junior")

    def test_infer_from_years(self):
        text = "Developer with 8 years of experience in various technologies"
        kw = extractor.extract(text)
        # 8 years should map to senior or lead
        assert kw.experience_level in ("senior", "lead")


class TestYearsExtraction:
    def test_extract_years(self):
        text = "5 years of professional software engineering experience"
        kw = extractor.extract(text)
        assert kw.years_of_experience == 5

    def test_extract_years_plus(self):
        text = "10+ years of experience in web development"
        kw = extractor.extract(text)
        assert kw.years_of_experience == 10

    def test_no_years(self):
        text = "Recent computer science graduate"
        kw = extractor.extract(text)
        assert kw.years_of_experience is None or kw.years_of_experience == 0


class TestEducation:
    def test_detect_masters(self):
        text = "M.S. in Computer Science from MIT"
        kw = extractor.extract(text)
        found = any("master" in e.lower() for e in kw.education)
        assert found

    def test_detect_bachelors(self):
        text = "Bachelor's degree in Electrical Engineering"
        kw = extractor.extract(text)
        found = any("bachelor" in e.lower() for e in kw.education)
        assert found

    def test_detect_phd(self):
        text = "Ph.D. in Machine Learning from Stanford University"
        kw = extractor.extract(text)
        found = any("phd" in e.lower() or "ph.d" in e.lower() for e in kw.education)
        assert found


class TestDomainDetection:
    def test_engineering_domain(self):
        text = "Software engineer with backend development, API design, and code review experience"
        kw = extractor.extract(text)
        assert "engineering" in kw.domains

    def test_healthcare_domain(self):
        text = "Registered nurse with patient care, clinical assessment, and hospital experience"
        kw = extractor.extract(text)
        assert "healthcare" in kw.domains

    def test_empty_text(self):
        kw = extractor.extract("")
        assert kw.skills == []
        assert kw.domains == []
