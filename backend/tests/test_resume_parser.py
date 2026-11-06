from io import BytesIO

import fitz
import pytest
from docx import Document

from job_agent.services.resume_parser import ResumeParseError, extract_resume_text


def test_extracts_text_from_pdf() -> None:
    pdf = fitz.open()
    page = pdf.new_page()
    page.insert_text((72, 72), "Jordan Example - Python Developer")
    content = pdf.tobytes()

    assert "Jordan Example" in extract_resume_text("resume.pdf", content, 1_000_000)


def test_extracts_text_from_docx() -> None:
    document = Document()
    document.add_paragraph("Jordan Example - Python Developer")
    buffer = BytesIO()
    document.save(buffer)

    assert "Python Developer" in extract_resume_text("resume.docx", buffer.getvalue(), 1_000_000)


@pytest.mark.parametrize(
    ("filename", "content"),
    [("resume.txt", b"plain text"), ("resume.pdf", b"not a pdf"), ("resume.docx", b"not a zip")],
)
def test_rejects_unsupported_or_mislabeled_files(filename: str, content: bytes) -> None:
    with pytest.raises(ResumeParseError):
        extract_resume_text(filename, content, 1_000_000)


def test_rejects_oversized_file() -> None:
    with pytest.raises(ResumeParseError, match="exceeds"):
        extract_resume_text("resume.pdf", b"%PDF-" + b"a" * 20, 10)
