"""In-memory extraction of text from supported resume formats."""

from __future__ import annotations

from io import BytesIO
from zipfile import ZipFile

import fitz
from docx import Document


class ResumeParseError(ValueError):
    """Resume file is unsupported, unsafe, or has no extractable text."""


def extract_resume_text(filename: str, content: bytes, max_bytes: int) -> str:
    """Validate the file type and extract text without saving the original file."""

    if not content:
        raise ResumeParseError("The uploaded file is empty")
    if len(content) > max_bytes:
        raise ResumeParseError(f"File exceeds the {max_bytes // (1024 * 1024)} MB upload limit")

    suffix = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    if suffix == "pdf" and content.startswith(b"%PDF-"):
        text = _extract_pdf(content)
    elif suffix == "docx" and content.startswith(b"PK"):
        text = _extract_docx(content)
    else:
        raise ResumeParseError("Only valid PDF and DOCX resume files are supported")

    normalized = "\n".join(line.strip() for line in text.splitlines() if line.strip())
    if not normalized:
        raise ResumeParseError("No readable text was found; scanned PDFs need OCR support")
    if len(normalized) > 100_000:
        raise ResumeParseError("Extracted resume text exceeds the 100,000 character limit")
    return normalized


def _extract_pdf(content: bytes) -> str:
    try:
        with fitz.open(stream=content, filetype="pdf") as document:
            if document.is_encrypted:
                raise ResumeParseError("Password-protected PDFs are not supported")
            if len(document) > 50:
                raise ResumeParseError("PDF contains more than 50 pages")
            return "\n".join(page.get_text("text") for page in document)
    except ResumeParseError:
        raise
    except Exception as exc:
        raise ResumeParseError("The PDF could not be read") from exc


def _extract_docx(content: bytes) -> str:
    try:
        with ZipFile(BytesIO(content)) as archive:
            members = archive.infolist()
            if len(members) > 500 or sum(item.file_size for item in members) > 25 * 1024 * 1024:
                raise ResumeParseError("DOCX archive is larger than the supported limit")
            names = {item.filename for item in members}
            if "[Content_Types].xml" not in names or "word/document.xml" not in names:
                raise ResumeParseError("The uploaded DOCX file is not a valid Word document")
        document = Document(BytesIO(content))
        paragraphs = [paragraph.text for paragraph in document.paragraphs]
        paragraphs.extend(
            " | ".join(cell.text for cell in row.cells)
            for table in document.tables
            for row in table.rows
        )
        return "\n".join(paragraphs)
    except ResumeParseError:
        raise
    except Exception as exc:
        raise ResumeParseError("The DOCX file could not be read") from exc
