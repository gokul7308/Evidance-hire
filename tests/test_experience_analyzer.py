import unittest
from backend.models.schemas import JDRequirement, RequirementCategory, Importance, ExperienceStatus
from backend.analysis.experience_analyzer import analyze_experience

class TestExperienceAnalyzer(unittest.TestCase):
    def setUp(self):
        self.req_general = JDRequirement("R1", RequirementCategory.EXPERIENCE, "3+ years of experience", Importance.REQUIRED, "3+ years of experience", 1)
        self.req_python = JDRequirement("R2", RequirementCategory.EXPERIENCE, "3+ years Python experience", Importance.REQUIRED, "3+ years Python experience", 2)
        
    def test_3_years_satisfied(self):
        exp_text = """
Software Engineer
2020 - 2024
Worked on cool stuff.
"""
        res = analyze_experience(self.req_general, exp_text)
        self.assertEqual(res.status, ExperienceStatus.MATCHED)
        self.assertGreaterEqual(res.candidate_experience_years, 3.0)

    def test_overlapping_employment(self):
        exp_text = """
Job A
2020 - 2023

Job B
2021 - 2024
"""
        res = analyze_experience(self.req_general, exp_text)
        self.assertEqual(res.status, ExperienceStatus.MATCHED)
        self.assertEqual(res.candidate_experience_years, 4.0) # 2020 to 2024 is 4 years total, not 6.

    def test_skill_specific_experience_match(self):
        exp_text = """
Software Engineer
2020 - 2024
Built systems with Python and Django.
"""
        res = analyze_experience(self.req_python, exp_text)
        # Python is in the block, so it counts.
        self.assertEqual(res.status, ExperienceStatus.MATCHED)
        self.assertGreaterEqual(res.candidate_experience_years, 3.0)

    def test_skill_specific_experience_no_match(self):
        exp_text = """
Software Engineer
2020 - 2024
Built systems with Java and Spring.
"""
        res = analyze_experience(self.req_python, exp_text)
        # Python is NOT in the block, so years should be 0.
        self.assertEqual(res.status, ExperienceStatus.MISSING)
        self.assertEqual(res.candidate_experience_years, 0.0)

    def test_present_current_employment(self):
        exp_text = """
Software Engineer
2022 - Present
"""
        res = analyze_experience(self.req_general, exp_text)
        self.assertTrue(res.candidate_experience_years >= 2.0)

    def test_ambiguous_or_missing_dates(self):
        exp_text = """
Software Engineer
Worked for a few years.
"""
        res = analyze_experience(self.req_general, exp_text)
        self.assertEqual(res.status, ExperienceStatus.MISSING)
        self.assertEqual(res.candidate_experience_years, 0.0)

if __name__ == '__main__':
    unittest.main()
