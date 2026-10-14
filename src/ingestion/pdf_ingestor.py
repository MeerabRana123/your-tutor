"""Page-aware PDF Ingestor for Your Tutor.

Extracts text from PDF documents while preserving physical page numbers,
file provenance, and creating bounded chunks with deterministic identifiers.
Uses PyMuPDF (pymupdf) when available, falling back to pypdf.
"""

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Tuple, Optional

from src.core.models import SourceDocument, ContentChunk, SourceType


class PDFIngestionError(Exception):
    """Raised when a PDF cannot be ingested or parsed."""
    pass


class PDFIngestor:
    """Extracts text from PDF files with strict physical page provenance."""

    def __init__(self, target_chunk_words: int = 250, chunk_overlap_words: int = 40):
        self.target_chunk_words = target_chunk_words
        self.chunk_overlap_words = chunk_overlap_words

    @staticmethod
    def _compute_document_id(file_path: Path) -> str:
        """Computes deterministic SHA256 of the PDF file content."""
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest()[:16]

    def ingest_file(self, file_path: Path) -> Tuple[SourceDocument, List[ContentChunk]]:
        """
        Parses a PDF file into a SourceDocument record and page-attributed ContentChunks.
        Raises PDFIngestionError if the file is invalid, empty, or unreadable.
        """
        path = Path(file_path)
        if not path.exists():
            raise PDFIngestionError(f"PDF file does not exist: {path}")

        file_size = path.stat().st_size
        if file_size == 0:
            raise PDFIngestionError(f"PDF file is completely empty (0 bytes): {path.name}")

        document_id = self._compute_document_id(path)
        filename = path.name

        # Extract page text using PyMuPDF or pypdf fallback
        pages_text = self._extract_pages_text(path)
        if not pages_text:
            raise PDFIngestionError(f"No pages or text could be extracted from: {filename}")

        # Check if the document has any non-whitespace text at all
        total_text_length = sum(len(txt.strip()) for _, txt in pages_text)
        if total_text_length == 0:
            raise PDFIngestionError(f"PDF document contains no extractable text: {filename}")

        total_pages = len(pages_text)
        doc = SourceDocument(
            document_id=document_id,
            filename=filename,
            source_type=SourceType.PDF,
            total_pages=total_pages,
            file_size_bytes=file_size,
            uploaded_at=datetime.now(timezone.utc).isoformat(),
        )

        chunks: List[ContentChunk] = []
        for page_num, raw_text in pages_text:
            cleaned_text = self._normalize_text(raw_text)
            if not cleaned_text:
                continue

            page_chunks = self._chunk_page_text(
                document_id=document_id,
                filename=filename,
                page_num=page_num,
                text=cleaned_text,
            )
            chunks.extend(page_chunks)

        if not chunks:
            raise PDFIngestionError(f"No valid text chunks could be formed from {filename}")

        return doc, chunks

    def _extract_pages_text(self, path: Path) -> List[Tuple[int, str]]:
        """Attempts PyMuPDF extraction, then pypdf fallback."""
        try:
            return self._extract_with_pymupdf(path)
        except Exception as e_fitz:
            try:
                return self._extract_with_pypdf(path)
            except Exception as e_pypdf:
                raise PDFIngestionError(
                    f"Failed to extract PDF text with both PyMuPDF ({e_fitz}) and pypdf ({e_pypdf})"
                )

    def _extract_with_pymupdf(self, path: Path) -> List[Tuple[int, str]]:
        """Extracts text using PyMuPDF."""
        try:
            import pymupdf as fitz
        except ImportError:
            import fitz  # Fallback to legacy import name

        results = []
        try:
            doc = fitz.open(str(path))
            for page_index in range(len(doc)):
                page = doc[page_index]
                text = page.get_text()
                # 1-indexed page number
                results.append((page_index + 1, text))
            doc.close()
            return results
        except Exception as e:
            raise PDFIngestionError(f"PyMuPDF failed to parse {path.name}: {e}")

    def _extract_with_pypdf(self, path: Path) -> List[Tuple[int, str]]:
        """Extracts text using pypdf fallback."""
        import pypdf

        results = []
        try:
            reader = pypdf.PdfReader(str(path))
            for page_index, page in enumerate(reader.pages):
                text = page.extract_text() or ""
                results.append((page_index + 1, text))
            return results
        except Exception as e:
            raise PDFIngestionError(f"pypdf failed to parse {path.name}: {e}")

    @staticmethod
    def _normalize_text(text: str) -> str:
        """Cleans control characters, whitespace and line breaks."""
        lines = [line.strip() for line in text.splitlines()]
        cleaned = " ".join(line for line in lines if line)
        return cleaned.strip()

    def _chunk_page_text(
        self, document_id: str, filename: str, page_num: int, text: str
    ) -> List[ContentChunk]:
        """
        Splits a single page's text into bounded chunks strictly anchored to page_num.
        """
        words = text.split()
        if not words:
            return []

        chunks = []
        # If the page fits in one or two chunks, chunk bounded by word count
        step = max(1, self.target_chunk_words - self.chunk_overlap_words)
        chunk_idx = 0

        for i in range(0, len(words), step):
            chunk_words = words[i : i + self.target_chunk_words]
            chunk_text = " ".join(chunk_words).strip()
            if not chunk_text:
                continue

            chunk_id = hashlib.sha256(
                f"{document_id}:{page_num}:{chunk_idx}:{chunk_text[:50]}".encode()
            ).hexdigest()[:16]

            chunks.append(
                ContentChunk(
                    chunk_id=chunk_id,
                    document_id=document_id,
                    filename=filename,
                    source_type=SourceType.PDF,
                    page_number=page_num,
                    text_content=chunk_text,
                    token_count=len(chunk_words),
                )
            )
            chunk_idx += 1
            if i + self.target_chunk_words >= len(words):
                break

        return chunks
