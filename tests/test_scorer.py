import unittest
from backend.models.schemas import (
    JDRequirement, CandidateField, FieldStatus, SkillGapResult, ExperienceResult, 
    RequirementCategory, Importance, MatchStatus, ExperienceStatus, ScoreMatchStatus
)
from backend.scoring.scorer import calculate_score

class TestScorer(unittest.TestCase):
    def setUp(self):
        self.req_python = JDRequirement("R1", RequirementCategory.SKILL, "Python", Importance.REQUIRED, "Python required", 1)
        self.req_react = JDRequirement("R2", RequirementCategory.SKILL, "React", Importance.REQUIRED, "React required", 2)
        self.req_java = JDRequirement("R3", RequirementCategory.SKILL, "Java", Importance.REQUIRED, "Java required", 3)
        self.req_docker = JDRequirement("R4", RequirementCategory.SKILL, "Docker", Importance.REQUIRED, "Docker required", 4)
        self.req_aws = JDRequirement("R5", RequirementCategory.SKILL, "AWS", Importance.REQUIRED, "AWS required", 5)
        self.req_exp = JDRequirement("R6", RequirementCategory.EXPERIENCE, "3+ years Python experience", Importance.REQUIRED, "3+ years Python experience", 6)
        
        self.jd_reqs = [self.req_python, self.req_react, self.req_java, self.req_docker, self.req_aws, self.req_exp]
        
    def test_critical_hallucination_test(self):
        # 6. CRITICAL HALLUCINATION TEST
        # Candidate has Python, Java, SQL
        # Missing React, Docker, AWS
        # Experience is 3 years Python
        
        skill_res_python = SkillGapResult(self.req_python, MatchStatus.HIGH_MATCH, "Python", "Python", "Python required", "Found")
        skill_res_java = SkillGapResult(self.req_java, MatchStatus.HIGH_MATCH, "Java", "Java", "Java required", "Found")
        skill_res_react = SkillGapResult(self.req_react, MatchStatus.SKILL_GAP, None, None, "React required", "Missing")
        skill_res_docker = SkillGapResult(self.req_docker, MatchStatus.SKILL_GAP, None, None, "Docker required", "Missing")
        skill_res_aws = SkillGapResult(self.req_aws, MatchStatus.SKILL_GAP, None, None, "AWS required", "Missing")
        
        exp_res = ExperienceResult(self.req_exp, 3.0, ExperienceStatus.MATCHED, "2022-2025 Python Engineer", "Matched")
        
        skill_results = [skill_res_python, skill_res_java, skill_res_react, skill_res_docker, skill_res_aws]
        
        res = calculate_score(
            candidate_id="c1",
            jd_requirements=self.jd_reqs,
            candidate_fields=[],
            skill_results=skill_results,
            experience_results=[exp_res]
        )
        
        status_map = {r.requirement.requirement_text: r.status for r in res.requirement_results}
        
        self.assertEqual(status_map["Python"], ScoreMatchStatus.MATCHED)
        self.assertEqual(status_map["Java"], ScoreMatchStatus.MATCHED)
        self.assertEqual(status_map["React"], ScoreMatchStatus.MISSING)
        self.assertEqual(status_map["Docker"], ScoreMatchStatus.MISSING)
        self.assertEqual(status_map["AWS"], ScoreMatchStatus.MISSING)
        
        # Experience is MATCHED
        self.assertEqual(status_map["3+ years Python experience"], ScoreMatchStatus.MATCHED)
        
        # Fit score: 3 matched out of 6 required (all required -> weights = 2). 
        # Total possible = 12. Earned = 6. Fit score = 50.0
        self.assertEqual(res.fit_score, 50.0)
        self.assertEqual(res.confidence_score, 100.0)
        self.assertEqual(res.matched_count, 3)
        self.assertEqual(res.missing_count, 3)

    def test_reproducibility(self):
        # 7. REPRODUCIBILITY TEST
        skill_res_python = SkillGapResult(self.req_python, MatchStatus.HIGH_MATCH, "Python", "Python", "Python required", "Found")
        
        results = []
        for _ in range(5):
            res = calculate_score(
                candidate_id="c1",
                jd_requirements=[self.req_python],
                candidate_fields=[],
                skill_results=[skill_res_python],
                experience_results=[]
            )
            results.append(res)
            
        for i in range(1, 5):
            self.assertEqual(results[i].fit_score, results[0].fit_score)
            self.assertEqual(results[i].confidence_score, results[0].confidence_score)
            self.assertEqual(results[i].matched_count, results[0].matched_count)

    def test_required_vs_preferred_weighting(self):
        req_pref = JDRequirement("R10", RequirementCategory.SKILL, "Pref Skill", Importance.PREFERRED, "Pref", 10)
        req_req = JDRequirement("R11", RequirementCategory.SKILL, "Req Skill", Importance.REQUIRED, "Req", 11)
        
        # Only prefer is matched
        sr_pref = SkillGapResult(req_pref, MatchStatus.HIGH_MATCH, "X", "X", "X", "X")
        sr_req = SkillGapResult(req_req, MatchStatus.SKILL_GAP, None, None, "Y", "Y")
        
        res1 = calculate_score(None, [req_pref, req_req], [], [sr_pref, sr_req], [])
        # Pref matched = 1 point. Req missing = 0. Total earned = 1. Total possible = 3. 1/3 = 33.33
        self.assertAlmostEqual(res1.fit_score, 33.33, places=2)
        
        # Only req is matched
        sr_pref2 = SkillGapResult(req_pref, MatchStatus.SKILL_GAP, None, None, "X", "X")
        sr_req2 = SkillGapResult(req_req, MatchStatus.HIGH_MATCH, "Y", "Y", "Y", "Y")
        
        res2 = calculate_score(None, [req_pref, req_req], [], [sr_pref2, sr_req2], [])
        # Pref missing = 0. Req matched = 2 points. Total earned = 2. Total possible = 3. 2/3 = 66.67
        self.assertAlmostEqual(res2.fit_score, 66.67, places=2)

    def test_confidence_reduction(self):
        # UNKNOWN experience
        exp_res = ExperienceResult(self.req_exp, 0.0, ExperienceStatus.UNKNOWN, None, "Unknown exp")
        res = calculate_score(None, [self.req_exp], [], [], [exp_res])
        self.assertEqual(res.confidence_score, 0.0)
        self.assertEqual(res.requirement_results[0].status, ScoreMatchStatus.MISSING)

if __name__ == '__main__':
    unittest.main()
