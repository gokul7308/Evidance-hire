import unittest
from backend.models.schemas import JDRequirement, CandidateField, FieldStatus, MatchStatus, RequirementCategory, Importance
from backend.analysis.skill_analyzer import analyze_skill

class TestSkillAnalyzer(unittest.TestCase):
    def setUp(self):
        self.req_python = JDRequirement("R1", RequirementCategory.SKILL, "Python", Importance.REQUIRED, "Python required", 1)
        self.req_react = JDRequirement("R2", RequirementCategory.SKILL, "React", Importance.REQUIRED, "React required", 2)
        self.req_java = JDRequirement("R3", RequirementCategory.SKILL, "Java", Importance.REQUIRED, "Java required", 3)
        self.req_aws = JDRequirement("R4", RequirementCategory.SKILL, "AWS", Importance.REQUIRED, "AWS required", 4)
        self.req_docker = JDRequirement("R5", RequirementCategory.SKILL, "Docker", Importance.REQUIRED, "Docker required", 5)

        self.candidate_skills = CandidateField("SKILLS", "Skills", FieldStatus.FOUND, "Python\nJava\nSQL", "Python\nJava\nSQL", "SKILLS")
        self.candidate_skills_javascript = CandidateField("SKILLS", "Skills", FieldStatus.FOUND, "JavaScript", "JavaScript", "SKILLS")
        
    def test_critical_no_hallucination_and_exact_matching(self):
        # 16. CRITICAL NO-HALLUCINATION TEST
        # Candidate has Python, Java, SQL
        # JD requires Python, Java, React, Docker, AWS
        
        res_python = analyze_skill(self.req_python, self.candidate_skills)
        res_java = analyze_skill(self.req_java, self.candidate_skills)
        res_react = analyze_skill(self.req_react, self.candidate_skills)
        res_docker = analyze_skill(self.req_docker, self.candidate_skills)
        res_aws = analyze_skill(self.req_aws, self.candidate_skills)
        
        self.assertEqual(res_python.match_status, MatchStatus.HIGH_MATCH)
        self.assertEqual(res_java.match_status, MatchStatus.HIGH_MATCH)
        self.assertEqual(res_react.match_status, MatchStatus.SKILL_GAP)
        self.assertEqual(res_docker.match_status, MatchStatus.SKILL_GAP)
        self.assertEqual(res_aws.match_status, MatchStatus.SKILL_GAP)
        
    def test_java_vs_javascript(self):
        # 8. Java vs JavaScript
        res_java_vs_js = analyze_skill(self.req_java, self.candidate_skills_javascript)
        # Should not match Java to JavaScript
        self.assertEqual(res_java_vs_js.match_status, MatchStatus.SKILL_GAP)
        
    def test_missing_or_ambiguous_skills(self):
        ambiguous_skills = CandidateField("SKILLS", "Skills", FieldStatus.AMBIGUOUS, None, None, "SKILLS")
        res = analyze_skill(self.req_python, ambiguous_skills)
        self.assertEqual(res.match_status, MatchStatus.SKILL_GAP)

if __name__ == '__main__':
    unittest.main()
