"""Unit and integration test suite for Milestone 1: Grounding Engine.

Validates all 10 core grounding and provenance requirements deterministically:
1. PDF extraction preserves page numbers
2. Empty or unreadable PDFs fail gracefully
3. Chunking preserves source provenance
4. A relevant question retrieves the expected evidence
5. Returned citations refer to retrieved evidence and valid pages
6. Unsupported questions trigger the insufficient-evidence response
7. Invalid or fabricated citations fail the audit
8. A failed audit does not result in a verified answer being shown
9. Re-ingesting a document does not accidentally duplicate chunks
10. Database records remain correctly associated with their source documents
"""

from pathlib import Path
import pytest

from src.core.models import EvidenceItem, ProviderResponse
from src.core.database import Database
from src.ingestion.pdf_ingestor import PDFIngestor, PDFIngestionError
from src.retrieval.retriever import BM25Retriever
from src.providers.mock_provider import MockDeterministicProvider
from src.grounding.citation_auditor import CitationAuditor
from src.core.tutor_service import TutorService


FIXTURE_PDF = Path("tests/fixtures/synthetic_ml_notes.pdf")


@pytest.fixture
def test_db(tmp_path):
    """Provides a fresh isolated SQLite database instance."""
    db_file = tmp_path / "test_tutor.db"
    return Database(db_path=str(db_file))


@pytest.fixture
def tutor_service(test_db):
    """Provides a fully initialized TutorService backed by the isolated test database."""
    retriever = BM25Retriever()
    provider = MockDeterministicProvider()
    auditor = CitationAuditor()
    ingestor = PDFIngestor()
    return TutorService(
        db=test_db,
        retriever=retriever,
        provider=provider,
        auditor=auditor,
        pdf_ingestor=ingestor,
    )


# -----------------------------------------------------------------------------
# REQUIREMENT 1: PDF extraction preserves page numbers
# -----------------------------------------------------------------------------
def test_pdf_extraction_preserves_page_numbers():
    ingestor = PDFIngestor()
    doc, chunks = ingestor.ingest_file(FIXTURE_PDF)

    assert doc.total_pages == 4
    pages_extracted = {chunk.page_number for chunk in chunks}
    assert pages_extracted == {1, 2, 3, 4}, "All 4 physical pages must be preserved in chunks"

    # Verify specific concept presence on respective physical pages
    page_1_chunks = [c for c in chunks if c.page_number == 1]
    assert any("loss and cost functions" in c.text_content.lower() for c in page_1_chunks)

    page_3_chunks = [c for c in chunks if c.page_number == 3]
    assert any("backpropagation" in c.text_content.lower() for c in page_3_chunks)


# -----------------------------------------------------------------------------
# REQUIREMENT 2: Empty or unreadable PDFs fail gracefully
# -----------------------------------------------------------------------------
def test_empty_or_corrupt_pdf_fails_gracefully(tmp_path):
    ingestor = PDFIngestor()

    # 1. Non-existent file
    with pytest.raises(PDFIngestionError) as exc_info:
        ingestor.ingest_file(tmp_path / "non_existent.pdf")
    assert "does not exist" in str(exc_info.value)

    # 2. 0-byte empty file
    empty_file = tmp_path / "empty.pdf"
    empty_file.write_bytes(b"")
    with pytest.raises(PDFIngestionError) as exc_info:
        ingestor.ingest_file(empty_file)
    assert "completely empty" in str(exc_info.value)

    # 3. Corrupt unreadable content
    corrupt_file = tmp_path / "corrupt.pdf"
    corrupt_file.write_bytes(b"%PDF-1.4 garbage corrupted byte sequence not valid pdf header")
    with pytest.raises(PDFIngestionError) as exc_info:
        ingestor.ingest_file(corrupt_file)
    assert "failed" in str(exc_info.value).lower() or "no pages" in str(exc_info.value).lower()


# -----------------------------------------------------------------------------
# REQUIREMENT 3: Chunking preserves source provenance
# -----------------------------------------------------------------------------
def test_chunking_preserves_source_provenance():
    ingestor = PDFIngestor()
    doc, chunks = ingestor.ingest_file(FIXTURE_PDF)

    for chunk in chunks:
        assert chunk.document_id == doc.document_id
        assert chunk.filename == FIXTURE_PDF.name
        assert chunk.page_number in [1, 2, 3, 4]
        assert len(chunk.chunk_id) > 8
        assert chunk.token_count > 0


# -----------------------------------------------------------------------------
# REQUIREMENT 4: A relevant question retrieves the expected evidence
# -----------------------------------------------------------------------------
def test_relevant_question_retrieves_expected_evidence(tutor_service):
    tutor_service.ingest_pdf(FIXTURE_PDF)

    # Query 1: Backpropagation should retrieve Page 3 as top result
    results_bp = tutor_service.retriever.search("What is backpropagation and the chain rule?", top_k=2)
    assert len(results_bp) > 0
    assert results_bp[0].page_number == 3
    assert "backpropagation" in results_bp[0].text_content.lower()

    # Query 2: Gradient descent should retrieve Page 2 as top result
    results_gd = tutor_service.retriever.search("How does gradient descent update parameters?", top_k=2)
    assert len(results_gd) > 0
    assert results_gd[0].page_number == 2
    assert "gradient descent" in results_gd[0].text_content.lower()

    # Query 3: Overfitting and dropout should retrieve Page 4
    results_of = tutor_service.retriever.search("What is overfitting and how does dropout help?", top_k=2)
    assert len(results_of) > 0
    assert results_of[0].page_number == 4
    assert "overfitting" in results_of[0].text_content.lower()


# -----------------------------------------------------------------------------
# REQUIREMENT 5: Returned citations refer to retrieved evidence and valid pages
# -----------------------------------------------------------------------------
def test_returned_citations_refer_to_retrieved_evidence(tutor_service):
    tutor_service.ingest_pdf(FIXTURE_PDF)

    response = tutor_service.answer_question("Explain the chain rule in backpropagation.")
    assert response.is_refusal is False
    assert response.audit_passed is True
    assert len(response.retrieved_evidence) > 0

    # Ensure response citations match the retrieved pages
    retrieved_pages = {e.page_number for e in response.retrieved_evidence}
    assert response.audit_result.is_valid is True
    assert len(response.audit_result.valid_citations) > 0

    for citation in response.audit_result.valid_citations:
        assert FIXTURE_PDF.name in citation
        # Citation should point to a page that was actually retrieved
        assert any(f"Page {p}" in citation for p in retrieved_pages)


# -----------------------------------------------------------------------------
# REQUIREMENT 6: Unsupported questions trigger the insufficient-evidence response
# -----------------------------------------------------------------------------
def test_unsupported_questions_trigger_insufficient_evidence(tutor_service):
    tutor_service.ingest_pdf(FIXTURE_PDF)

    # Query about completely unrelated domain
    out_of_domain_query = "What temperature is required to bake a sourdough loaf in a Dutch oven?"
    response = tutor_service.answer_question(out_of_domain_query)

    assert response.is_refusal is True
    assert "could not find sufficient evidence" in response.answer.lower()
    assert response.retrieved_evidence == []
    assert response.audit_result.is_valid is True  # Valid clean refusal
    assert response.audit_result.invalid_citations == []


# -----------------------------------------------------------------------------
# REQUIREMENT 7: Invalid or fabricated citations fail the audit
# -----------------------------------------------------------------------------
def test_invalid_or_fabricated_citations_fail_audit():
    auditor = CitationAuditor()
    evidence = [
        EvidenceItem(
            chunk_id="chk_1",
            document_id="doc_1",
            filename="synthetic_ml_notes.pdf",
            page_number=3,
            text_content="Backpropagation computes derivatives using the chain rule.",
            score=1.5,
            rank=1,
        )
    ]

    # Fabricated citation pointing to Page 99 (not in retrieved evidence)
    fabricated_answer = (
        "Backpropagation uses the chain rule [Source: synthetic_ml_notes.pdf, Page 99]."
    )
    audit = auditor.audit_response(fabricated_answer, evidence)

    assert audit.is_valid is False
    assert len(audit.invalid_citations) == 1
    assert "Page 99" in audit.invalid_citations[0]
    assert "Audit Failed" in audit.details


# -----------------------------------------------------------------------------
# REQUIREMENT 8: A failed audit does not result in a verified answer being shown
# -----------------------------------------------------------------------------
def test_failed_audit_blocks_verified_answer_display(tutor_service):
    tutor_service.ingest_pdf(FIXTURE_PDF)

    # Custom mock provider that intentionally injects a hallucinated citation
    class HallucinatingProvider(MockDeterministicProvider):
        def generate_grounded_answer(self, query, evidence):
            return ProviderResponse(
                text="Gradient descent is an optimizer [Source: nonexistent_book.pdf, Page 42].",
                provider_name="hallucinating_provider",
                mode="rogue",
                is_refusal=False,
            )

    tutor_service.set_provider(HallucinatingProvider())
    response = tutor_service.answer_question("Explain gradient descent.")

    # Must NOT present answer as verified!
    assert response.audit_passed is False
    assert response.audit_result.is_valid is False
    assert "Citation Audit Failed" in response.answer
    assert "withheld" in response.answer.lower()
    assert "nonexistent_book.pdf" in response.audit_result.invalid_citations[0]


# -----------------------------------------------------------------------------
# REQUIREMENT 9: Re-ingesting a document does not accidentally duplicate chunks
# -----------------------------------------------------------------------------
def test_reingesting_document_does_not_duplicate_chunks(tutor_service):
    # Ingest once
    doc1 = tutor_service.ingest_pdf(FIXTURE_PDF)
    initial_chunks = tutor_service.db.get_chunks_by_document(doc1.document_id)
    initial_count = len(initial_chunks)
    assert initial_count > 0

    # Ingest same document second time
    doc2 = tutor_service.ingest_pdf(FIXTURE_PDF)
    post_reingest_chunks = tutor_service.db.get_chunks_by_document(doc2.document_id)
    post_count = len(post_reingest_chunks)

    # Chunk count must remain strictly identical (zero duplicate accumulation)
    assert post_count == initial_count

    all_chunks = tutor_service.db.get_all_chunks()
    assert len(all_chunks) == initial_count


# -----------------------------------------------------------------------------
# REQUIREMENT 10: Database records remain correctly associated with source documents
# -----------------------------------------------------------------------------
def test_database_records_remain_correctly_associated(tutor_service):
    doc = tutor_service.ingest_pdf(FIXTURE_PDF)

    # Retrieve doc record
    retrieved_doc = tutor_service.db.get_document(doc.document_id)
    assert retrieved_doc is not None
    assert retrieved_doc.filename == FIXTURE_PDF.name
    assert retrieved_doc.total_pages == 4

    # Verify all chunks link via foreign key to document_id
    chunks = tutor_service.db.get_chunks_by_document(doc.document_id)
    for chunk in chunks:
        assert chunk.document_id == doc.document_id
        assert chunk.filename == retrieved_doc.filename

    # Verify cascading delete cleans up chunks
    tutor_service.db.delete_document(doc.document_id)
    assert tutor_service.db.get_document(doc.document_id) is None
    assert tutor_service.db.get_chunks_by_document(doc.document_id) == []
