import unittest
import tempfile
import os
from backend.models.schemas import CandidateField, FieldStatus, DuplicateStatus
from backend.identity.duplicate_detector import detect_duplicate, ExistingCandidate, calculate_file_hash, calculate_content_hash

class TestDuplicateDetector(unittest.TestCase):

    def setUp(self):
        # Create some temporary files to test exact file hash matches
        self.fd1, self.path1 = tempfile.mkstemp()
        with os.fdopen(self.fd1, 'wb') as f:
            f.write(b"Hello Resume 1")
            
        self.fd2, self.path2 = tempfile.mkstemp()
        with os.fdopen(self.fd2, 'wb') as f:
            f.write(b"Hello Resume 1") # Exact same content as path1

        self.fd3, self.path3 = tempfile.mkstemp()
        with os.fdopen(self.fd3, 'wb') as f:
            f.write(b"Different Resume Content")

        self.hash1 = calculate_file_hash(self.path1)
        self.content_hash1 = calculate_content_hash("Hello Resume 1 text extracted.")

        self.existing_cands = [
            ExistingCandidate(
                candidate_id="CAND-001",
                file_hash=self.hash1,
                content_hash=self.content_hash1,
                fields=[
                    CandidateField("FULL-NAME", "Personal", FieldStatus.FOUND, "John Smith"),
                    CandidateField("EMAIL", "Personal", FieldStatus.FOUND, "john@example.com"),
                    CandidateField("PHONE", "Personal", FieldStatus.FOUND, "555-1234"),
                    CandidateField("INSTITUTION", "Education", FieldStatus.FOUND, "ABC University"),
                    CandidateField("MOST-RECENT-JOB", "Experience", FieldStatus.FOUND, "Software Engineer")
                ]
            )
        ]

    def tearDown(self):
        os.remove(self.path1)
        os.remove(self.path2)
        os.remove(self.path3)

    def test_exact_duplicate_and_already_it_exist_message(self):
        # Uploading path2 which has same content as path1, so same file hash
        # We simulate that the user uploaded an exactly identical file
        res = detect_duplicate(
            self.path1,
            "Hello Resume 1 text extracted.",
            [], # fields don't matter for exact hash
            self.existing_cands
        )
        self.assertEqual(res.status, DuplicateStatus.EXACT_DUPLICATE)
        self.assertEqual(res.message, "Already it exist")

    def test_same_content_different_filename(self):
        # Different file hash (e.g. metadata changed) but exact same extracted text content hash
        # To simulate this, we use path3 (different file hash) but the same raw_text
        res = detect_duplicate(
            self.path3,
            "Hello Resume 1 text extracted.",
            [], 
            self.existing_cands
        )
        self.assertEqual(res.status, DuplicateStatus.SAME_CANDIDATE)
        self.assertIn("Same content", res.message)

    def test_same_candidate_changed_resume(self):
        # Different file hash, different content hash, but same email
        fields = [
            CandidateField("FULL-NAME", "Personal", FieldStatus.FOUND, "John Smith"),
            CandidateField("EMAIL", "Personal", FieldStatus.FOUND, "john@example.com")
        ]
        res = detect_duplicate(
            self.path3,
            "Changed resume text",
            fields,
            self.existing_cands
        )
        self.assertEqual(res.status, DuplicateStatus.SAME_CANDIDATE)

    def test_same_name_different_candidate(self):
        # Same name, but totally different other fields (email, inst, job)
        fields = [
            CandidateField("FULL-NAME", "Personal", FieldStatus.FOUND, "John Smith"),
            CandidateField("EMAIL", "Personal", FieldStatus.FOUND, "john.other@example.com"),
            CandidateField("INSTITUTION", "Education", FieldStatus.FOUND, "XYZ University"),
        ]
        res = detect_duplicate(
            self.path3,
            "Changed resume text",
            fields,
            self.existing_cands
        )
        self.assertEqual(res.status, DuplicateStatus.NEW_CANDIDATE)

    def test_different_candidates(self):
        fields = [
            CandidateField("FULL-NAME", "Personal", FieldStatus.FOUND, "Alice Brown"),
            CandidateField("EMAIL", "Personal", FieldStatus.FOUND, "alice@example.com"),
        ]
        res = detect_duplicate(
            self.path3,
            "Alice's resume text",
            fields,
            self.existing_cands
        )
        self.assertEqual(res.status, DuplicateStatus.NEW_CANDIDATE)

    def test_weak_identity_match(self):
        # Same name and institution, no strong signals
        fields = [
            CandidateField("FULL-NAME", "Personal", FieldStatus.FOUND, "John Smith"),
            CandidateField("INSTITUTION", "Education", FieldStatus.FOUND, "ABC University"),
        ]
        res = detect_duplicate(
            self.path3,
            "New text",
            fields,
            self.existing_cands
        )
        self.assertEqual(res.status, DuplicateStatus.POSSIBLE_SAME_CANDIDATE)

    def test_strong_identity_different_name(self):
        # Email matches, but name differs (e.g. name change or shared email)
        fields = [
            CandidateField("FULL-NAME", "Personal", FieldStatus.FOUND, "Johnny S"),
            CandidateField("EMAIL", "Personal", FieldStatus.FOUND, "john@example.com"),
        ]
        res = detect_duplicate(
            self.path3,
            "New text",
            fields,
            self.existing_cands
        )
        self.assertEqual(res.status, DuplicateStatus.POSSIBLE_SAME_CANDIDATE)

    def test_missing_strong_signals_no_weak_match(self):
        # Missing email, phone, linkedin. Name matches but inst/job don't.
        fields = [
            CandidateField("FULL-NAME", "Personal", FieldStatus.FOUND, "John Smith"),
        ]
        res = detect_duplicate(
            self.path3,
            "New text",
            fields,
            self.existing_cands
        )
        self.assertEqual(res.status, DuplicateStatus.NEW_CANDIDATE)

if __name__ == '__main__':
    unittest.main()
