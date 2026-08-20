import unittest
import os
from pathlib import Path
from backend.ingestion.extractor import extract_file
from backend.models.schemas import ExtractionStatus

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"

class TestResumeExtraction(unittest.TestCase):
    
    def test_valid_pdf(self):
        result = extract_file(str(FIXTURE_DIR / "valid.pdf"))
        self.assertEqual(result.status, ExtractionStatus.SUCCESS)
        self.assertEqual(result.file_type, ".pdf")
        self.assertIn("Hello, world!", result.raw_text)
        
    def test_no_text_pdf(self):
        result = extract_file(str(FIXTURE_DIR / "no_text.pdf"))
        self.assertEqual(result.status, ExtractionStatus.UNKNOWN)
        self.assertEqual(result.file_type, ".pdf")
        self.assertIn("no extractable text layer", result.error_message)

    def test_valid_docx(self):
        result = extract_file(str(FIXTURE_DIR / "valid.docx"))
        self.assertEqual(result.status, ExtractionStatus.SUCCESS)
        self.assertEqual(result.file_type, ".docx")
        self.assertIn("Hello, DOCX!", result.raw_text)

    def test_unsupported_file(self):
        result = extract_file(str(FIXTURE_DIR / "unsupported.txt"))
        self.assertEqual(result.status, ExtractionStatus.ERROR)
        self.assertEqual(result.file_type, ".txt")
        self.assertIn("Unsupported file type", result.error_message)

    def test_missing_file(self):
        result = extract_file(str(FIXTURE_DIR / "does_not_exist.pdf"))
        self.assertEqual(result.status, ExtractionStatus.ERROR)
        self.assertIn("does not exist", result.error_message)

    def test_empty_file(self):
        result = extract_file(str(FIXTURE_DIR / "empty.pdf"))
        self.assertEqual(result.status, ExtractionStatus.ERROR)
        self.assertIn("empty", result.error_message)

    def test_corrupted_pdf(self):
        result = extract_file(str(FIXTURE_DIR / "corrupted.pdf"))
        self.assertEqual(result.status, ExtractionStatus.ERROR)
        self.assertEqual(result.file_type, ".pdf")
        self.assertIn("PDF extraction failed", result.error_message)

    def test_corrupted_docx(self):
        result = extract_file(str(FIXTURE_DIR / "corrupted.docx"))
        self.assertEqual(result.status, ExtractionStatus.ERROR)
        self.assertEqual(result.file_type, ".docx")
        self.assertIn("DOCX extraction failed", result.error_message)

if __name__ == '__main__':
    unittest.main()
