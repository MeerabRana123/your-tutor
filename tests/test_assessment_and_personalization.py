"""Integration tests for Adaptive Assessments and Personalization flow.

Validates:
1. Assessment question structural validation (answer key in options, required fields)
2. Grounded question generation preserving source filename and physical page number
3. Offline generator provenance labeling ('offline_template')
4. Deterministic answer evaluation
5. End-to-end personalization: submission -> BKT update -> grounded revision recommendation
"""

from pathlib import Path
import pytest
from pydantic import ValidationError

from src.assessment.models import AssessmentQuestion
from src.assessment.generator import AssessmentGenerator
from src.core.database import Database
from src.core.tutor_service import TutorService
from src.ingestion.pdf_ingestor import PDFIngestor
from src.retrieval.retriever import BM25Retriever
from src.providers.mock_provider import MockDeterministicProvider
from src.grounding.citation_auditor import CitationAuditor
from src.bkt.engine import BKTEngine


FIXTURE_PDF = Path("tests/fixtures/synthetic_ml_notes.pdf")


@pytest.fixture
def tutor_service(tmp_path):
    db_file = tmp_path / "personalization_test.db"
    db = Database(db_path=str(db_file))
    service = TutorService(
        db=db,
        retriever=BM25Retriever(),
        provider=MockDeterministicProvider(),
        auditor=CitationAuditor(),
        pdf_ingestor=PDFIngestor(),
        bkt_engine=BKTEngine(p_l0=0.20, p_t=0.15, p_g=0.20, p_s=0.10),
    )
    service.ingest_pdf(FIXTURE_PDF)
    return service


def test_assessment_question_validation():
    # Valid question passes
    q = AssessmentQuestion(
        question_id="q_test_1",
        topic="Backpropagation",
        difficulty="intermediate",
        source_document="notes.pdf",
        page_number=3,
        citation_label="[Source: notes.pdf, Page 3]",
        question_stem="What is the chain rule used for?",
        options={"A": "Forward pass", "B": "Computing gradients", "C": "Loss scaling", "D": "Data augmentation"},
        correct_answer="B",
        explanation="Page 3 states gradients are computed via the chain rule.",
        generator_mode="offline_template",
    )
    assert q.correct_answer == "B"

    # Invalid answer key: 'Z' is not in options
    with pytest.raises(ValidationError):
        AssessmentQuestion(
            question_id="q_test_2",
            topic="Backpropagation",
            source_document="notes.pdf",
            page_number=3,
            citation_label="[Source: notes.pdf, Page 3]",
            question_stem="What is the chain rule used for?",
            options={"A": "Option 1", "B": "Option 2"},
            correct_answer="Z",
            explanation="Test",
            generator_mode="offline_template",
        )


def test_grounded_question_generation(tutor_service):
    # Generate question for gradient descent
    question = tutor_service.generate_assessment(topic_hint="gradient descent")

    assert "Gradient Descent" in question.topic
    assert question.page_number == 2
    assert question.source_document == FIXTURE_PDF.name
    assert question.generator_mode == "offline_template"
    assert len(question.options) == 4
    assert question.correct_answer in question.options
    assert FIXTURE_PDF.name in question.citation_label
    assert "Page 2" in question.citation_label


def test_deterministic_answer_evaluation():
    q = AssessmentQuestion(
        question_id="q_eval_1",
        topic="Optimization",
        source_document="notes.pdf",
        page_number=2,
        citation_label="[Source: notes.pdf, Page 2]",
        question_stem="Identify the learning rate symbol.",
        options={"A": "beta", "B": "alpha", "C": "gamma", "D": "lambda"},
        correct_answer="B",
        explanation="alpha is the learning rate.",
        generator_mode="offline_template",
    )

    assert AssessmentGenerator.evaluate_answer(q, "B") is True
    assert AssessmentGenerator.evaluate_answer(q, "b") is True  # Case insensitive
    assert AssessmentGenerator.evaluate_answer(q, "A") is False
    assert AssessmentGenerator.evaluate_answer(q, "D") is False


def test_end_to_end_assessment_personalization_flow(tutor_service):
    student_id = "student_bob"

    # 1. Generate Question on Backpropagation (Page 3)
    q_bp = tutor_service.generate_assessment(topic_hint="backpropagation")
    assert q_bp.page_number == 3

    # Student submits CORRECT answer
    res_correct = tutor_service.submit_assessment(
        student_id=student_id,
        question=q_bp,
        student_choice=q_bp.correct_answer,
    )

    assert res_correct.is_correct is True
    assert res_correct.prior_mastery == 0.20  # default p_l0
    assert res_correct.posterior_mastery > 0.20  # mastery increased
    assert res_correct.mastery_delta > 0
    assert res_correct.revision_recommendation is None

    # Check persistence in database
    db_mastery = tutor_service.db.get_topic_mastery(student_id, q_bp.topic)
    assert db_mastery == res_correct.posterior_mastery

    # 2. Generate Question on Overfitting (Page 4)
    q_of = tutor_service.generate_assessment(topic_hint="overfitting")
    assert q_of.page_number == 4

    # Student submits INCORRECT answer
    wrong_choice = "A" if q_of.correct_answer != "A" else "C"
    res_wrong = tutor_service.submit_assessment(
        student_id=student_id,
        question=q_of,
        student_choice=wrong_choice,
    )

    assert res_wrong.is_correct is False
    assert res_wrong.revision_recommendation is not None
    assert f"Page {q_of.page_number}" in res_wrong.revision_recommendation
    assert q_of.source_document in res_wrong.revision_recommendation

    # Verify both topics are tracked in student profile
    all_masteries = tutor_service.get_student_masteries(student_id)
    assert q_bp.topic in all_masteries
    assert q_of.topic in all_masteries


def test_dynamic_offline_extraction_for_custom_topics(tutor_service):
    """Verifies that an arbitrary topic not in fixed templates dynamically extracts an MCQ."""
    q_custom = tutor_service.generate_assessment(topic_hint="unseen advanced topic")
    assert q_custom is not None
    assert q_custom.generator_mode == "offline_dynamic_extract"
    assert q_custom.correct_answer == "A"
    assert len(q_custom.options) == 4
    assert q_custom.source_document == FIXTURE_PDF.name
    assert q_custom.page_number >= 1
    assert "unseen advanced topic".title() in q_custom.topic


def test_mocked_gemini_assessment_generation():
    """Verifies that AssessmentGenerator parses valid JSON from a live/mocked Gemini provider."""
    class FakeGeminiProvider:
        def is_available(self):
            return True
        def generate_raw(self, prompt, system_instruction=None):
            return '''```json
            {
                "topic": "Neural Architectures",
                "question_stem": "What is the primary function of an activation function?",
                "options": {
                    "A": "To introduce non-linearity into the network",
                    "B": "To sort training records",
                    "C": "To compress weights into 8-bit integers",
                    "D": "To halt execution when loss diverges"
                },
                "correct_answer": "A",
                "explanation": "Page 1 notes that activation functions introduce non-linearities."
            }
            ```'''

    gen = AssessmentGenerator(gemini_provider=FakeGeminiProvider())
    from src.core.models import ContentChunk, SourceType
    dummy_chunk = ContentChunk(
        chunk_id="chk_1",
        document_id="doc_1",
        filename="custom_guide.pdf",
        source_type=SourceType.PDF,
        page_number=5,
        text_content="Activation functions introduce non-linearities into neural computation.",
    )

    q = gen.generate_question([dummy_chunk], topic_hint="Neural Architectures")
    assert q.generator_mode == "gemini"
    assert q.topic == "Neural Architectures"
    assert q.correct_answer == "A"
    assert q.page_number == 5
    assert q.source_document == "custom_guide.pdf"
    assert q.citation_label == "[Source: custom_guide.pdf, Page 5]"

