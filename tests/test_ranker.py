import unittest
from backend.models.schemas import CandidateRankingInput, ScoreResult, RequirementScore, JDRequirement, RequirementCategory, Importance, ScoreMatchStatus
from backend.scoring.ranker import rank_candidates

class TestRanker(unittest.TestCase):
    def setUp(self):
        self.req_python = JDRequirement("R1", RequirementCategory.SKILL, "Python", Importance.REQUIRED, "Python required", 1)
        self.req_react = JDRequirement("R2", RequirementCategory.SKILL, "React", Importance.REQUIRED, "React required", 2)
        
        self.req_res_matched = RequirementScore(self.req_python, ScoreMatchStatus.MATCHED, "matched", "ev", 100.0)
        self.req_res_missing = RequirementScore(self.req_react, ScoreMatchStatus.MISSING, "missing", None, 100.0)
        
    def _make_score(self, fit: float, conf: float, match: int, missing: int, cid: str) -> ScoreResult:
        return ScoreResult(
            candidate_id=cid,
            fit_score=fit,
            confidence_score=conf,
            matched_count=match,
            partial_count=0,
            missing_count=missing,
            requirement_results=[self.req_res_matched, self.req_res_missing],
            explanation="Test"
        )
        
    def _make_input(self, cid: str, cname: str, version: int, is_current: bool, fit: float, conf: float = 100.0, match: int = 1, missing: int = 1) -> CandidateRankingInput:
        return CandidateRankingInput(
            candidate_id=cid,
            candidate_name=cname,
            resume_version=version,
            is_current=is_current,
            score_result=self._make_score(fit, conf, match, missing, cid)
        )

    def test_fit_score_ordering(self):
        c1 = self._make_input("c1", "A", 1, True, 80.0)
        c2 = self._make_input("c2", "B", 1, True, 90.0)
        c3 = self._make_input("c3", "C", 1, True, 70.0)
        
        ranked = rank_candidates([c1, c2, c3])
        self.assertEqual(len(ranked), 3)
        self.assertEqual(ranked[0].candidate_id, "c2")
        self.assertEqual(ranked[1].candidate_id, "c1")
        self.assertEqual(ranked[2].candidate_id, "c3")

    def test_tie_breaking(self):
        # Tie on fit score, broken by confidence
        c1 = self._make_input("c1", "A", 1, True, 80.0, conf=90.0)
        c2 = self._make_input("c2", "B", 1, True, 80.0, conf=95.0)
        ranked = rank_candidates([c1, c2])
        self.assertEqual(ranked[0].candidate_id, "c2")
        
        # Tie on fit and conf, broken by matched_count
        c3 = self._make_input("c3", "C", 1, True, 80.0, conf=90.0, match=2)
        c4 = self._make_input("c4", "D", 1, True, 80.0, conf=90.0, match=3)
        ranked2 = rank_candidates([c3, c4])
        self.assertEqual(ranked2[0].candidate_id, "c4")
        
        # Tie on fit, conf, match, broken by missing_count (lower is better)
        c5 = self._make_input("c5", "E", 1, True, 80.0, conf=90.0, match=2, missing=2)
        c6 = self._make_input("c6", "F", 1, True, 80.0, conf=90.0, match=2, missing=1)
        ranked3 = rank_candidates([c5, c6])
        self.assertEqual(ranked3[0].candidate_id, "c6")
        
        # All equal, stable ID
        c7 = self._make_input("Z", "Z", 1, True, 80.0, conf=90.0, match=2, missing=1)
        c8 = self._make_input("A", "A", 1, True, 80.0, conf=90.0, match=2, missing=1)
        ranked4 = rank_candidates([c7, c8])
        self.assertEqual(ranked4[0].candidate_id, "A") # A < Z

    def test_duplicate_candidate_test(self):
        # 15. CRITICAL DUPLICATE TEST
        # Candidate A: v1, Fit 80 (not current)
        # Candidate A: v2, Fit 90 (current)
        # Candidate B: v1, Fit 85 (current)
        
        c_a_v1 = self._make_input("c_a", "John Smith", 1, False, 80.0)
        c_a_v2 = self._make_input("c_a", "John Smith", 2, True, 90.0)
        c_b_v1 = self._make_input("c_b", "Priya Kumar", 1, True, 85.0)
        
        ranked = rank_candidates([c_a_v1, c_a_v2, c_b_v1])
        
        self.assertEqual(len(ranked), 2)
        self.assertEqual(ranked[0].candidate_name, "John Smith")
        self.assertEqual(ranked[0].resume_version, 2)
        self.assertEqual(ranked[0].fit_score, 90.0)
        
        self.assertEqual(ranked[1].candidate_name, "Priya Kumar")
        self.assertEqual(ranked[1].fit_score, 85.0)

    def test_empty_candidates(self):
        ranked = rank_candidates([])
        self.assertEqual(ranked, [])
        
    def test_deterministic_repeated(self):
        c1 = self._make_input("c1", "A", 1, True, 80.0)
        c2 = self._make_input("c2", "B", 1, True, 90.0)
        
        ranked_first = rank_candidates([c1, c2])
        for _ in range(5):
            ranked_next = rank_candidates([c1, c2])
            self.assertEqual(ranked_first, ranked_next)

if __name__ == '__main__':
    unittest.main()
