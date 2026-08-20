import unittest
import os
import sqlite3
from backend.config import Config
from database.db import get_connection, init_db
from backend.models.schemas import DecisionValue
from backend.decisions.decision_manager import (
    get_candidate_decision,
    record_decision,
    get_candidates_by_decision,
    get_decision_history
)

class TestDecisionManager(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Ensure DB is initialized
        init_db()
        
    def setUp(self):
        # Clear the decisions table before each test for clean slate
        with get_connection() as conn:
            conn.execute("DELETE FROM decisions")
            conn.commit()
            
    def test_default_is_pending(self):
        # 1. Default decision is PENDING
        decision = get_candidate_decision("c1", "v1")
        self.assertEqual(decision.decision, DecisionValue.PENDING)
        
    def test_no_automatic_decision(self):
        # 2 & 3. High score/confidence does NOT auto-accept
        # Simulated scenario: candidate has fit=98, conf=99
        # But we never called record_decision
        decision = get_candidate_decision("john_smith", "v2")
        self.assertEqual(decision.decision, DecisionValue.PENDING)

    def test_explicit_accept_reject(self):
        # 4 & 5. Explicit ACCEPT stores ACCEPTED, REJECT stores REJECTED
        record_decision("c1", "v1", DecisionValue.ACCEPTED, ["c1"], ["v1"])
        dec_accept = get_candidate_decision("c1", "v1")
        self.assertEqual(dec_accept.decision, DecisionValue.ACCEPTED)
        
        record_decision("c2", "v1", DecisionValue.REJECTED, ["c2"], ["v1"])
        dec_reject = get_candidate_decision("c2", "v1")
        self.assertEqual(dec_reject.decision, DecisionValue.REJECTED)
        
    def test_retrieval(self):
        # 6 & 7. Accepted/Rejected candidate retrieval
        record_decision("c1", "v1", DecisionValue.ACCEPTED, ["c1", "c2", "c3"], ["v1", "v2"])
        record_decision("c2", "v2", DecisionValue.REJECTED, ["c1", "c2", "c3"], ["v1", "v2"])
        record_decision("c3", "v1", DecisionValue.ACCEPTED, ["c1", "c2", "c3"], ["v1", "v2"])
        
        accepted = get_candidates_by_decision(DecisionValue.ACCEPTED)
        self.assertEqual(len(accepted), 2)
        cand_ids = {a.candidate_id for a in accepted}
        self.assertIn("c1", cand_ids)
        self.assertIn("c3", cand_ids)
        
        rejected = get_candidates_by_decision(DecisionValue.REJECTED)
        self.assertEqual(len(rejected), 1)
        self.assertEqual(rejected[0].candidate_id, "c2")

    def test_db_reload_persistence(self):
        # 8. Database reload test
        record_decision("c_persist", "v1", DecisionValue.ACCEPTED, ["c_persist"], ["v1"])
        
        # Simulate connection reload by grabbing a fresh connection
        conn2 = sqlite3.connect(Config.DB_PATH)
        cursor = conn2.cursor()
        cursor.execute("SELECT * FROM decisions WHERE candidate_id = 'c_persist'")
        row = cursor.fetchone()
        conn2.close()
        
        self.assertIsNotNone(row)
        self.assertEqual(row[3], DecisionValue.ACCEPTED.value) # decision is the 4th column

    def test_candidate_version_relationship(self):
        # 9. Candidate/version relationship
        record_decision("c1", "v1", DecisionValue.ACCEPTED, ["c1"], ["v1", "v2"])
        record_decision("c1", "v2", DecisionValue.REJECTED, ["c1"], ["v1", "v2"])
        
        dec_v1 = get_candidate_decision("c1", "v1")
        dec_v2 = get_candidate_decision("c1", "v2")
        
        self.assertEqual(dec_v1.decision, DecisionValue.ACCEPTED)
        self.assertEqual(dec_v2.decision, DecisionValue.REJECTED)

    def test_duplicate_protection_and_history(self):
        # 10 & 11. Historical decision preservation
        # Idempotency prevents dupes if same state
        record_decision("c1", "v1", DecisionValue.ACCEPTED, ["c1"], ["v1"])
        record_decision("c1", "v1", DecisionValue.ACCEPTED, ["c1"], ["v1"])
        
        history = get_decision_history("c1", "v1")
        self.assertEqual(len(history), 1) # Idempotent, so only 1 record
        
        # Now change decision
        record_decision("c1", "v1", DecisionValue.REJECTED, ["c1"], ["v1"])
        
        history2 = get_decision_history("c1", "v1")
        self.assertEqual(len(history2), 2) # History preserved
        self.assertEqual(history2[0].decision, DecisionValue.ACCEPTED)
        self.assertEqual(history2[1].decision, DecisionValue.REJECTED)
        
        # Latest should be REJECTED
        latest = get_candidate_decision("c1", "v1")
        self.assertEqual(latest.decision, DecisionValue.REJECTED)
        
    def test_invalid_rejection(self):
        # 12 & 13. Invalid candidate/version rejection
        with self.assertRaises(ValueError):
            record_decision("invalid_c", "v1", DecisionValue.ACCEPTED, ["valid_c"], ["v1"])
            
        with self.assertRaises(ValueError):
            record_decision("valid_c", "invalid_v", DecisionValue.ACCEPTED, ["valid_c"], ["valid_v"])

if __name__ == '__main__':
    unittest.main()
