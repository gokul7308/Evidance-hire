import unittest
from backend.models.schemas import RequirementCategory, Importance
from backend.parsing.jd_parser import parse_jd

class TestJDParser(unittest.TestCase):

    def test_required_and_preferred_skills(self):
        jd_text = """
Required Skills:
Python
Java

Preferred Skills:
Docker
AWS
"""
        reqs = parse_jd(jd_text)
        self.assertEqual(len(reqs), 4)
        
        self.assertEqual(reqs[0].requirement_text, "Python")
        self.assertEqual(reqs[0].category, RequirementCategory.SKILL)
        self.assertEqual(reqs[0].importance, Importance.REQUIRED)
        
        self.assertEqual(reqs[2].requirement_text, "Docker")
        self.assertEqual(reqs[2].category, RequirementCategory.SKILL)
        self.assertEqual(reqs[2].importance, Importance.PREFERRED)

    def test_education_experience_certification_location_other(self):
        jd_text = """
Bachelor's degree in Computer Science required.
3+ years of Python development experience.
AWS Certified Developer certification preferred.
Must be located in Bangalore.
Excellent communication skills.
"""
        reqs = parse_jd(jd_text)
        self.assertEqual(len(reqs), 5)
        
        # Education
        self.assertEqual(reqs[0].category, RequirementCategory.EDUCATION)
        self.assertEqual(reqs[0].importance, Importance.REQUIRED) # from inline 'required'
        
        # Experience
        self.assertEqual(reqs[1].category, RequirementCategory.EXPERIENCE)
        
        # Certification
        self.assertEqual(reqs[2].category, RequirementCategory.CERTIFICATION)
        self.assertEqual(reqs[2].importance, Importance.PREFERRED) # from inline 'preferred'
        
        # Location
        self.assertEqual(reqs[3].category, RequirementCategory.LOCATION)
        
        # Other / Skill
        # "Excellent communication skills." is 3 words long, so the simple fallback puts it in SKILL.
        self.assertEqual(reqs[4].category, RequirementCategory.SKILL)

    def test_mixed_and_evidence_preservation(self):
        jd_text = """
Nice to have: Docker
"""
        reqs = parse_jd(jd_text)
        self.assertEqual(len(reqs), 1)
        self.assertEqual(reqs[0].importance, Importance.PREFERRED)
        self.assertEqual(reqs[0].evidence, "Nice to have: Docker")

    def test_no_inference_regression(self):
        jd_text = "Experience with AWS."
        reqs = parse_jd(jd_text)
        self.assertEqual(len(reqs), 1)
        self.assertEqual(reqs[0].category, RequirementCategory.EXPERIENCE)
        
        # Verify no inferred sub-skills exist
        inferred_skills = [r.requirement_text for r in reqs if r.requirement_text in ["EC2", "S3", "Lambda", "CloudFormation"]]
        self.assertEqual(len(inferred_skills), 0)

    def test_deterministic_output(self):
        jd_text = "Python\nJava"
        reqs1 = parse_jd(jd_text)
        reqs2 = parse_jd(jd_text)
        
        self.assertEqual(reqs1[0].requirement_text, reqs2[0].requirement_text)
        self.assertEqual(reqs1[1].requirement_text, reqs2[1].requirement_text)

if __name__ == '__main__':
    unittest.main()
