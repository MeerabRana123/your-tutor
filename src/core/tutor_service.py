"""Tutor Service for Your Tutor.

Coordinates PDF ingestion, BM25 retrieval, model provider synthesis,
and citation auditing into a cohesive, verified instructional workflow.
"""

from pathlib import Path
from typing import Optional, List
from src.core.models import (
    SourceDocument,
    ContentChunk,
    TutorResponse,
    AuditResult,
)
from src.core.database import Database
from src.ingestion.pdf_ingestor import PDFIngestor
from src.retrieval.retriever import BM25Retriever
from src.providers.base import BaseModelProvider
from src.providers.mock_provider import MockDeterministicProvider
from src.providers.gemini_provider import GeminiProvider
from src.grounding.citation_auditor import CitationAuditor


class TutorService:
    """Core service orchestrating the Milestone 1 grounding pipeline."""

    INSUFFICIENT_EVIDENCE_MSG = "I could not find sufficient evidence in the uploaded material to answer this question."

    def __init__(
        self,
        db: Optional[Database] = None,
        retriever: Optional[BM25Retriever] = None,
        provider: Optional[BaseModelProvider] = None,
        auditor: Optional[CitationAuditor] = None,
        pdf_ingestor: Optional[PDFIngestor] = None,
    ):
        self.db = db or Database()
        self.retriever = retriever or BM25Retriever()
        self.auditor = auditor or CitationAuditor()
        self.pdf_ingestor = pdf_ingestor or PDFIngestor()

        # Set provider: default to Gemini if configured, otherwise Mock
        if provider:
            self.provider = provider
        else:
            gemini = GeminiProvider()
            self.provider = gemini if gemini.is_available() else MockDeterministicProvider()

        # Load existing chunks from DB into retriever if available
        self._refresh_retriever_index()

    def _refresh_retriever_index(self) -> None:
        """Loads all persisted chunks from database into the in-memory retriever."""
        all_chunks = self.db.get_all_chunks()
        self.retriever.index_chunks(all_chunks)

    def set_provider(self, provider: BaseModelProvider) -> None:
        """Dynamically switches active model provider."""
        self.provider = provider

    def ingest_pdf(self, file_path: Path) -> SourceDocument:
        """
        Ingests a PDF, saves document metadata and chunks to SQLite,
        and refreshes the retrieval index.
        """
        doc, chunks = self.pdf_ingestor.ingest_file(file_path)
        self.db.save_document(doc)
        self.db.save_chunks(chunks)
        self._refresh_retriever_index()
        return doc

    def answer_question(
        self, query: str, top_k: int = 3, min_score: Optional[float] = None
    ) -> TutorResponse:
        """
        Executes end-to-end grounded Q&A workflow:
        1. Retrieves relevant evidence chunks via BM25
        2. Handles insufficient evidence directly if nothing relevant retrieved
        3. Invokes model provider with retrieved evidence
        4. Audits citations independently
        5. Returns verified or audit-flagged TutorResponse
        """
        clean_query = query.strip()
        if not clean_query:
            return self._build_refusal_response("Please enter a question.")

        # 1. Retrieve evidence
        evidence = self.retriever.search(clean_query, top_k=top_k, min_score=min_score)

        # 2. Check for insufficient evidence
        if not evidence:
            return self._build_refusal_response(clean_query)

        # 3. Call model provider
        provider_resp = self.provider.generate_grounded_answer(clean_query, evidence)

        # 4. Independent citation audit
        audit_result = self.auditor.audit_response(
            generated_text=provider_resp.text,
            retrieved_evidence=evidence,
            is_refusal=provider_resp.is_refusal,
        )

        # 5. Enforce Rule 9: If audit fails, do not silently display answer as verified
        if not audit_result.is_valid:
            safe_answer = (
                "⚠️ [Citation Audit Failed: Unverified Source Locations Detected]\n\n"
                "The generated response contained citations that could not be verified against "
                "the retrieved course materials. For academic integrity, unverified claims have been withheld.\n\n"
                f"Audit Details: {audit_result.details}"
            )
            return TutorResponse(
                query=clean_query,
                answer=safe_answer,
                provider_name=provider_resp.provider_name,
                mode=provider_resp.mode,
                is_refusal=False,
                audit_passed=False,
                audit_result=audit_result,
                retrieved_evidence=evidence,
            )

        # Audit passed (or legitimate refusal)
        return TutorResponse(
            query=clean_query,
            answer=provider_resp.text,
            provider_name=provider_resp.provider_name,
            mode=provider_resp.mode,
            is_refusal=provider_resp.is_refusal,
            audit_passed=True,
            audit_result=audit_result,
            retrieved_evidence=evidence,
        )

    def _build_refusal_response(self, query: str) -> TutorResponse:
        """Constructs a clean refusal response when evidence is insufficient."""
        audit = AuditResult(
            is_valid=True,
            citations_found=[],
            valid_citations=[],
            invalid_citations=[],
            unsupported_claims=[],
            details="No evidence found above relevance threshold; legitimate refusal emitted.",
        )
        return TutorResponse(
            query=query,
            answer=self.INSUFFICIENT_EVIDENCE_MSG,
            provider_name=self.provider.provider_name,
            mode="refusal",
            is_refusal=True,
            audit_passed=True,
            audit_result=audit,
            retrieved_evidence=[],
        )
