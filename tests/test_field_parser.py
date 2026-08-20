import unittest
from backend.models.schemas import Section, FieldStatus
from backend.parsing.field_parser import parse_fields

class TestFieldParser(unittest.TestCase):

    def setUp(self):
        self.sections_valid = [
            Section("Contact", "CONTACT", "John Doe\njohn@example.com\n(555) 123-4567\nlinkedin.com/in/johndoe\nNew York, NY", 0, 5, ""),
            Section("Education", "EDUCATION", "Stanford University\nB.S. Computer Science\n2020", 5, 8, "EDUCATION"),
            Section("Experience", "EXPERIENCE", "Software Engineer at Google\nWorked on search.", 8, 10, "EXPERIENCE"),
            Section("Skills", "SKILLS", "Python, Java", 10, 11, "SKILLS"),
            Section("Certifications", "CERTIFICATIONS", "AWS Certified Solutions Architect", 11, 12, "CERTIFICATIONS"),
            Section("Projects", "PROJECTS", "Built a parser.", 12, 13, "PROJECTS"),
        ]

        self.sections_empty = []

        self.sections_ambiguous = [
            Section("Contact", "CONTACT", "John Doe\njohn@example.com\njohn2@example.com\n(555) 123-4567\n(555) 987-6543\nNew York, NY\nAustin, TX", 0, 7, ""),
            Section("Education", "EDUCATION", "Stanford University\nHarvard University\nB.S. Computer Science\nM.S. Computer Science\n2020\n2022", 7, 13, "EDUCATION"),
        ]

    def test_found_fields(self):
        fields = parse_fields(self.sections_valid)
        field_dict = {f.field_id: f for f in fields}

        # Check all 12 fields
        self.assertEqual(field_dict["FULL-NAME"].status, FieldStatus.FOUND)
        self.assertEqual(field_dict["FULL-NAME"].value, "John Doe")

        self.assertEqual(field_dict["EMAIL"].status, FieldStatus.FOUND)
        self.assertEqual(field_dict["EMAIL"].value, "john@example.com")

        self.assertEqual(field_dict["PHONE"].status, FieldStatus.FOUND)
        self.assertEqual(field_dict["PHONE"].value, "(555) 123-4567")

        self.assertEqual(field_dict["LINKEDIN-PORTFOLIO"].status, FieldStatus.FOUND)
        self.assertEqual(field_dict["LINKEDIN-PORTFOLIO"].value, "linkedin.com/in/johndoe")

        self.assertEqual(field_dict["LOCATION"].status, FieldStatus.FOUND)
        self.assertEqual(field_dict["LOCATION"].value, "New York, NY")

        self.assertEqual(field_dict["HIGHEST-DEGREE"].status, FieldStatus.FOUND)
        self.assertEqual(field_dict["HIGHEST-DEGREE"].value, "B.S.")

        self.assertEqual(field_dict["INSTITUTION"].status, FieldStatus.FOUND)
        self.assertEqual(field_dict["INSTITUTION"].value, "Stanford University")

        self.assertEqual(field_dict["GRADUATION-YEAR"].status, FieldStatus.FOUND)
        self.assertEqual(field_dict["GRADUATION-YEAR"].value, "2020")

        self.assertEqual(field_dict["MOST-RECENT-JOB"].status, FieldStatus.FOUND)
        self.assertEqual(field_dict["MOST-RECENT-JOB"].value, "Software Engineer at Google")

        self.assertEqual(field_dict["SKILLS-LIST"].status, FieldStatus.FOUND)
        self.assertEqual(field_dict["SKILLS-LIST"].value, "Python, Java")

        self.assertEqual(field_dict["CERTIFICATIONS"].status, FieldStatus.FOUND)
        self.assertEqual(field_dict["CERTIFICATIONS"].value, "AWS Certified Solutions Architect")

        self.assertEqual(field_dict["PROJECTS"].status, FieldStatus.FOUND)
        self.assertEqual(field_dict["PROJECTS"].value, "Built a parser.")

    def test_not_found_fields(self):
        fields = parse_fields(self.sections_empty)
        for f in fields:
            self.assertEqual(f.status, FieldStatus.NOT_FOUND)

    def test_ambiguous_fields(self):
        fields = parse_fields(self.sections_ambiguous)
        field_dict = {f.field_id: f for f in fields}

        # Name is not ambiguous, it just takes the first line
        self.assertEqual(field_dict["FULL-NAME"].status, FieldStatus.FOUND)
        
        self.assertEqual(field_dict["EMAIL"].status, FieldStatus.AMBIGUOUS)
        self.assertEqual(field_dict["PHONE"].status, FieldStatus.AMBIGUOUS)
        self.assertEqual(field_dict["LOCATION"].status, FieldStatus.AMBIGUOUS)
        self.assertEqual(field_dict["HIGHEST-DEGREE"].status, FieldStatus.AMBIGUOUS)
        self.assertEqual(field_dict["INSTITUTION"].status, FieldStatus.AMBIGUOUS)
        self.assertEqual(field_dict["GRADUATION-YEAR"].status, FieldStatus.AMBIGUOUS)

if __name__ == '__main__':
    unittest.main()
