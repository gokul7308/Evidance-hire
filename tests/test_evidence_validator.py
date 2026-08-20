import unittest
from backend.models.schemas import CandidateField, FieldStatus, Section
from backend.validation.evidence_validator import validate_field, validate_profile

class TestEvidenceValidator(unittest.TestCase):

    def setUp(self):
        self.raw_text = "Name: Rahul Kumar\nSkills:\nPython\nJava\nSQL\nEducation: B.S."
        self.sections = [
            Section("Contact", "CONTACT", "Name: Rahul Kumar", 0, 1, "Contact"),
            Section("Skills", "SKILLS", "Python\nJava\nSQL", 1, 4, "Skills"),
            Section("Education", "EDUCATION", "B.S.", 4, 5, "Education"),
        ]

    def test_valid_evidence(self):
        field = CandidateField("SKILLS", "Skills", FieldStatus.FOUND, "Python", "Python\nJava\nSQL", "SKILLS")
        result = validate_field(field, self.raw_text, self.sections)
        self.assertTrue(result.is_valid)

    def test_evidence_missing(self):
        field = CandidateField("SKILLS", "Skills", FieldStatus.FOUND, "Python", None, "SKILLS")
        result = validate_field(field, self.raw_text, self.sections)
        self.assertFalse(result.is_valid)
        self.assertIn("No evidence provided", result.validation_message)

    def test_evidence_not_present_in_resume(self):
        field = CandidateField("SKILLS", "Skills", FieldStatus.FOUND, "Python", "Python and C++", "SKILLS")
        result = validate_field(field, self.raw_text, self.sections)
        self.assertFalse(result.is_valid)
        self.assertIn("Evidence not found in the extracted resume text", result.validation_message)

    def test_fabricated_field_value_and_evidence_does_not_support_value(self):
        # 13. IMPORTANT ANTI-HALLUCINATION TEST
        field = CandidateField("SKILLS", "Skills", FieldStatus.FOUND, "AWS", "Python\nJava\nSQL", "SKILLS")
        result = validate_field(field, self.raw_text, self.sections)
        self.assertFalse(result.is_valid)
        self.assertIn("Value is not supported by the provided evidence", result.validation_message)

    def test_valid_not_found_field(self):
        field = CandidateField("PHONE", "Personal", FieldStatus.NOT_FOUND, None, None, None)
        result = validate_field(field, self.raw_text, self.sections)
        self.assertTrue(result.is_valid)
        self.assertIn("NOT_FOUND", result.validation_message)

    def test_valid_ambiguous_field(self):
        field = CandidateField("LOCATION", "Personal", FieldStatus.AMBIGUOUS, None, None, None)
        result = validate_field(field, self.raw_text, self.sections)
        self.assertTrue(result.is_valid)
        self.assertIn("AMBIGUOUS", result.validation_message)

    def test_invalid_source_section(self):
        # The section is wrong
        field = CandidateField("SKILLS", "Skills", FieldStatus.FOUND, "Python", "Python\nJava\nSQL", "FAKE_SECTION")
        result = validate_field(field, self.raw_text, self.sections)
        self.assertFalse(result.is_valid)
        self.assertIn("Source section not found", result.validation_message)

    def test_evidence_with_whitespace_variation(self):
        # Resume has "Python\nJava\nSQL". Evidence has "Python Java SQL"
        field = CandidateField("SKILLS", "Skills", FieldStatus.FOUND, "Python", "Python   Java SQL", "SKILLS")
        result = validate_field(field, self.raw_text, self.sections)
        self.assertTrue(result.is_valid)

    def test_multiple_fields_validation(self):
        fields = [
            CandidateField("SKILLS", "Skills", FieldStatus.FOUND, "Python", "Python\nJava\nSQL", "SKILLS"),
            CandidateField("DEGREE", "Education", FieldStatus.FOUND, "B.S.", "B.S.", "EDUCATION")
        ]
        results = validate_profile(fields, self.raw_text, self.sections)
        self.assertTrue(all(r.is_valid for r in results))

    def test_multiple_fields_one_invalid(self):
        fields = [
            CandidateField("SKILLS", "Skills", FieldStatus.FOUND, "Python", "Python\nJava\nSQL", "SKILLS"),
            CandidateField("DEGREE", "Education", FieldStatus.FOUND, "Ph.D.", "B.S.", "EDUCATION") # INVALID
        ]
        results = validate_profile(fields, self.raw_text, self.sections)
        self.assertTrue(results[0].is_valid)
        self.assertFalse(results[1].is_valid)

if __name__ == '__main__':
    unittest.main()
