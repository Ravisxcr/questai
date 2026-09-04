import io
from django.test import TestCase
from pypdf import PdfWriter
from apps.services.pdf_extractor import extract_text_from_pdf, chunk_text, clean_text


class PDFExtractorTests(TestCase):
    def test_clean_text(self):
        raw = "Hello   World!\x00\n\n\n\nNew Paragraph"
        cleaned = clean_text(raw)
        self.assertEqual(cleaned, "Hello World!\n\nNew Paragraph")

    def test_chunk_text(self):
        text = "ABCDEFGHIJ" * 200  # 2000 chars
        chunks = chunk_text(text, max_chunk_size=500, overlap=100)
        self.assertTrue(len(chunks) > 1)
        self.assertTrue(all(len(c) <= 500 for c in chunks))

    def test_extract_text_from_empty_or_valid_pdf(self):
        """Create a minimal PDF in-memory and extract text."""
        writer = PdfWriter()
        writer.add_blank_page(width=200, height=200)
        pdf_bytes = io.BytesIO()
        writer.write(pdf_bytes)
        pdf_bytes.seek(0)

        result = extract_text_from_pdf(pdf_bytes)
        self.assertEqual(result["page_count"], 1)
        # Since it's a blank page, full_text will be empty or error reported
        self.assertTrue("page_count" in result)

