"""SQLite persistence layer for Your Tutor.

Enforces relational foreign keys, parameterization, WAL journaling,
and idempotent document/chunk storage.
"""

import sqlite3
from pathlib import Path
from typing import List, Optional
from src.core.models import SourceDocument, ContentChunk, SourceType


class Database:
    """Encapsulates SQLite database operations with foreign key enforcement."""

    def __init__(self, db_path: str = "data/your_tutor.db"):
        self.db_path = db_path
        if db_path != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Returns a connection with foreign key enforcement and row factory."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        if self.db_path != ":memory:":
            conn.execute("PRAGMA journal_mode = WAL;")
        return conn

    def init_db(self) -> None:
        """Initializes database schema with constraints and indexes."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS source_documents (
                    document_id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL UNIQUE,
                    source_type TEXT NOT NULL,
                    total_pages INTEGER,
                    file_size_bytes INTEGER NOT NULL,
                    uploaded_at TEXT NOT NULL
                );
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS content_chunks (
                    chunk_id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL REFERENCES source_documents(document_id) ON DELETE CASCADE,
                    filename TEXT NOT NULL,
                    source_type TEXT NOT NULL,
                    page_number INTEGER NOT NULL,
                    text_content TEXT NOT NULL,
                    token_count INTEGER NOT NULL
                );
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_chunks_doc ON content_chunks(document_id);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_chunks_page ON content_chunks(page_number);")
            conn.commit()

    def save_document(self, doc: SourceDocument) -> None:
        """Inserts or updates a source document record."""
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO source_documents (
                    document_id, filename, source_type, total_pages, file_size_bytes, uploaded_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(filename) DO UPDATE SET
                    document_id = excluded.document_id,
                    source_type = excluded.source_type,
                    total_pages = excluded.total_pages,
                    file_size_bytes = excluded.file_size_bytes,
                    uploaded_at = excluded.uploaded_at;
            """, (
                doc.document_id,
                doc.filename,
                doc.source_type.value,
                doc.total_pages,
                doc.file_size_bytes,
                doc.uploaded_at,
            ))
            conn.commit()

    def save_chunks(self, chunks: List[ContentChunk]) -> None:
        """
        Saves chunks for a document.
        Idempotent: Replaces any existing chunks for the same document to prevent duplicates.
        """
        if not chunks:
            return

        document_id = chunks[0].document_id
        with self._get_connection() as conn:
            # Clean up existing chunks for this document to prevent duplicate accumulation
            conn.execute("DELETE FROM content_chunks WHERE document_id = ?;", (document_id,))
            conn.executemany("""
                INSERT INTO content_chunks (
                    chunk_id, document_id, filename, source_type, page_number, text_content, token_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?);
            """, [
                (
                    c.chunk_id,
                    c.document_id,
                    c.filename,
                    c.source_type.value,
                    c.page_number,
                    c.text_content,
                    c.token_count,
                )
                for c in chunks
            ])
            conn.commit()

    def get_document(self, document_id: str) -> Optional[SourceDocument]:
        """Retrieves a document by document_id."""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM source_documents WHERE document_id = ?;", (document_id,)
            ).fetchone()
            if not row:
                return None
            return SourceDocument(
                document_id=row["document_id"],
                filename=row["filename"],
                source_type=SourceType(row["source_type"]),
                total_pages=row["total_pages"],
                file_size_bytes=row["file_size_bytes"],
                uploaded_at=row["uploaded_at"],
            )

    def get_document_by_filename(self, filename: str) -> Optional[SourceDocument]:
        """Retrieves a document by filename."""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM source_documents WHERE filename = ?;", (filename,)
            ).fetchone()
            if not row:
                return None
            return SourceDocument(
                document_id=row["document_id"],
                filename=row["filename"],
                source_type=SourceType(row["source_type"]),
                total_pages=row["total_pages"],
                file_size_bytes=row["file_size_bytes"],
                uploaded_at=row["uploaded_at"],
            )

    def get_chunks_by_document(self, document_id: str) -> List[ContentChunk]:
        """Retrieves all chunks belonging to a document ordered by page number."""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM content_chunks WHERE document_id = ? ORDER BY page_number ASC;",
                (document_id,)
            ).fetchall()
            return [
                ContentChunk(
                    chunk_id=r["chunk_id"],
                    document_id=r["document_id"],
                    filename=r["filename"],
                    source_type=SourceType(r["source_type"]),
                    page_number=r["page_number"],
                    text_content=r["text_content"],
                    token_count=r["token_count"],
                )
                for r in rows
            ]

    def get_all_chunks(self) -> List[ContentChunk]:
        """Retrieves all chunks across all ingested documents."""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM content_chunks ORDER BY filename, page_number ASC;"
            ).fetchall()
            return [
                ContentChunk(
                    chunk_id=r["chunk_id"],
                    document_id=r["document_id"],
                    filename=r["filename"],
                    source_type=SourceType(r["source_type"]),
                    page_number=r["page_number"],
                    text_content=r["text_content"],
                    token_count=r["token_count"],
                )
                for r in rows
            ]

    def delete_document(self, document_id: str) -> None:
        """Deletes a document and cascades deletion to all associated chunks."""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM source_documents WHERE document_id = ?;", (document_id,))
            conn.commit()
