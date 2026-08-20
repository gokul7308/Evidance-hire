import unittest
from backend.parsing.segmenter import segment_resume

class TestResumeSegmentation(unittest.TestCase):

    def test_clean_resume(self):
        text = "John Smith\nemail@email.com\n\nEDUCATION\nB.E. Computer Science\n\nSKILLS\nPython\nJava"
        sections = segment_resume(text)
        
        self.assertEqual(len(sections), 3)
        self.assertEqual(sections[0].section_id, "CONTACT")
        self.assertIn("John Smith", sections[0].text)
        
        self.assertEqual(sections[1].section_id, "EDUCATION")
        self.assertIn("B.E. Computer Science", sections[1].text)
        
        self.assertEqual(sections[2].section_id, "SKILLS")
        self.assertIn("Python\nJava", sections[2].text)

    def test_uppercase_headings(self):
        text = "John Smith\n\nEXPERIENCE\nCompany A\n\nPROJECTS\nProject A"
        sections = segment_resume(text)
        self.assertEqual(sections[1].section_id, "EXPERIENCE")
        self.assertEqual(sections[2].section_id, "PROJECTS")

    def test_lowercase_headings(self):
        text = "John Smith\n\nexperience\nCompany A\n\nskills\nPython"
        sections = segment_resume(text)
        self.assertEqual(sections[1].section_id, "EXPERIENCE")
        self.assertEqual(sections[2].section_id, "SKILLS")

    def test_heading_variations(self):
        text = "Contact info\n\nProfessional Summary\nI am a dev\n\nWork Experience\nJob 1\n\nTechnical Skills & Tools\nPython"
        sections = segment_resume(text)
        
        self.assertEqual(sections[1].section_id, "SUMMARY")
        self.assertEqual(sections[2].section_id, "EXPERIENCE")
        self.assertEqual(sections[3].section_id, "SKILLS")

    def test_missing_sections(self):
        # Only contact info
        text = "John Smith\nemail@email.com"
        sections = segment_resume(text)
        self.assertEqual(len(sections), 1)
        self.assertEqual(sections[0].section_id, "CONTACT")

    def test_unknown_headings(self):
        text = "John Smith\n\nCAREER HIGHLIGHTS\nPython\nJava"
        sections = segment_resume(text)
        # "CAREER HIGHLIGHTS" is not in the mapping, so it remains in the CONTACT section.
        self.assertEqual(len(sections), 1)
        self.assertEqual(sections[0].section_id, "CONTACT")
        self.assertIn("CAREER HIGHLIGHTS", sections[0].text)

    def test_messy_whitespace(self):
        text = "John Smith\n\n   EDUCATION :  \n\nB.E.\n\n\t SKILLS\t \n\nPython"
        sections = segment_resume(text)
        self.assertEqual(sections[1].section_id, "EDUCATION")
        self.assertEqual(sections[2].section_id, "SKILLS")

    def test_multiple_page_extracted_text(self):
        # E.g. page breaks might add extra newlines or form feed characters depending on extractor
        text = "John Smith\n\nEDUCATION\nB.E.\n\n\x0c\n\nSKILLS\nPython"
        sections = segment_resume(text)
        self.assertEqual(len(sections), 3)
        self.assertEqual(sections[1].section_id, "EDUCATION")
        self.assertEqual(sections[2].section_id, "SKILLS")
        self.assertIn("Python", sections[2].text)

    def test_section_ordering_and_boundaries(self):
        text = (
            "Name\n"
            "EDUCATION\n"
            "Degree\n"
            "EXPERIENCE\n"
            "Job 1\n"
            "Job 2\n"
            "SKILLS\n"
            "Skill 1\n"
            "Skill 2\n"
        )
        sections = segment_resume(text)
        
        # We expect Contact, Education, Experience, Skills in that exact order
        self.assertEqual(sections[0].section_id, "CONTACT")
        self.assertEqual(sections[1].section_id, "EDUCATION")
        self.assertEqual(sections[2].section_id, "EXPERIENCE")
        self.assertEqual(sections[3].section_id, "SKILLS")
        
        # Verify boundary correctness
        self.assertEqual(sections[2].text, "Job 1\nJob 2")
        self.assertEqual(sections[3].text, "Skill 1\nSkill 2")

if __name__ == '__main__':
    unittest.main()
