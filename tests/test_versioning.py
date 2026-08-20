import unittest
from backend.models.schemas import CandidateField, FieldStatus, ResumeVersion
from backend.identity.version_manager import add_resume_version, compare_versions

class TestResumeVersioning(unittest.TestCase):

    def setUp(self):
        self.existing_versions = []
        self.fields_v1 = [
            CandidateField("SKILLS", "Skills", FieldStatus.FOUND, "Python\nJava", "Python\nJava", "SKILLS"),
            CandidateField("PHONE", "Personal", FieldStatus.FOUND, "123-456", "123-456", "CONTACT")
        ]
        
        self.fields_v2 = [
            CandidateField("SKILLS", "Skills", FieldStatus.FOUND, "Python\nJava\nDocker\nAWS", "Python\nJava\nDocker\nAWS", "SKILLS"),
            CandidateField("PHONE", "Personal", FieldStatus.NOT_FOUND, None, None, None), # removed
            CandidateField("EMAIL", "Personal", FieldStatus.FOUND, "a@b.com", "a@b.com", "CONTACT") # added
        ]

    def test_version_numbering_and_current_status(self):
        # 1. First resume becomes v1
        v1 = add_resume_version("C-001", "U-1", "hash1", self.fields_v1, self.existing_versions)
        self.assertEqual(v1.version_number, 1)
        self.assertTrue(v1.is_current)
        self.assertEqual(len(self.existing_versions), 1)

        # 2. Updated same-candidate resume becomes v2
        v2 = add_resume_version("C-001", "U-2", "hash2", self.fields_v2, self.existing_versions)
        self.assertEqual(v2.version_number, 2)
        self.assertTrue(v2.is_current)
        self.assertFalse(v1.is_current) # 6. Only latest is current
        self.assertEqual(len(self.existing_versions), 2) # 5. Previous remain available

        # 3. Third update becomes v3
        v3 = add_resume_version("C-001", "U-3", "hash3", self.fields_v2, self.existing_versions)
        self.assertEqual(v3.version_number, 3)
        self.assertTrue(v3.is_current)
        self.assertFalse(v2.is_current)
        self.assertEqual(len(self.existing_versions), 3)
        
    def test_version_comparison_logic(self):
        v1 = add_resume_version("C-001", "U-1", "hash1", self.fields_v1, self.existing_versions)
        v2 = add_resume_version("C-001", "U-2", "hash2", self.fields_v2, self.existing_versions)
        
        comp = compare_versions(v1, v2)
        
        # 7. Added field detection (EMAIL)
        self.assertEqual(len(comp.added), 1)
        self.assertEqual(comp.added[0].field_id, "EMAIL")
        
        # 8. Removed field detection (PHONE)
        self.assertEqual(len(comp.removed), 1)
        self.assertEqual(comp.removed[0].field_id, "PHONE")
        
        # 9. Changed field detection (SKILLS)
        self.assertEqual(len(comp.changed), 1)
        self.assertEqual(comp.changed[0]["old"].field_id, "SKILLS")
        self.assertNotEqual(comp.changed[0]["old"].value, comp.changed[0]["new"].value)
        
        # 10. Unchanged field detection
        # Since v1 and v2 only have the above fields, there are no unchanged fields.
        # Let's add an unchanged field.
        fields_v3 = list(self.fields_v2) # same fields
        v3 = add_resume_version("C-001", "U-3", "hash3", fields_v3, self.existing_versions)
        
        comp2 = compare_versions(v2, v3)
        self.assertEqual(len(comp2.added), 0)
        self.assertEqual(len(comp2.removed), 0)
        self.assertEqual(len(comp2.changed), 0)
        self.assertEqual(len(comp2.unchanged), len(fields_v3)) # All unchanged

    def test_evidence_backed_changes(self):
        # 11. Evidence-backed changes
        v1 = add_resume_version("C-001", "U-1", "hash1", self.fields_v1, self.existing_versions)
        v2 = add_resume_version("C-001", "U-2", "hash2", self.fields_v2, self.existing_versions)
        
        comp = compare_versions(v1, v2)
        
        self.assertEqual(comp.added[0].evidence, "a@b.com") # explicitly bound to evidence
        self.assertEqual(comp.changed[0]["new"].evidence, "Python\nJava\nDocker\nAWS")

if __name__ == '__main__':
    unittest.main()
