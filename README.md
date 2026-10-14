# Your Tutor — Source-Grounded Multimodal Adaptive Learning Companion

[![Track](https://img.shields.io/badge/Hackathon-Multimodal%20AI%202026-blue.svg)](https://github.com)
[![Track D](https://img.shields.io/badge/Track%20D-Personalized%20Tutoring%20%26%20Adaptive%20Learning-green.svg)](https://github.com)
[![Python](https://img.shields.io/badge/Python-3.13%2B-blue.svg)](https://python.org)
[![Tests](https://img.shields.io/badge/Tests-10%20Passed%20(100%25)-brightgreen.svg)](tests/)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)

> **Central Product Principle:**
> *Every course-grounded answer must be traceable to evidence, every mastery update must be explainable, and every evaluation result must be reproducible.*

---

## 1. Project Overview

**Your Tutor** is an academic AI learning companion built for rigorous university-level courses (exemplar curriculum: *Introductory Machine Learning & Deep Learning*).

Unlike generic conversational RAG wrappers that hallucinate external citations or convert course materials into lossy text dumps, **Your Tutor** enforces **strict physical provenance** down to the source page, slide number, or video timestamp, coupled with an **independent citation verification layer** and **offline deterministic fallback**.

---

## 2. Milestone 1: Grounding Engine (Current Implementation)

Milestone 1 delivers the complete, verified, end-to-end vertical slice of the source-grounded tutoring engine:

```
[PDF Upload]
     │
     ▼
[PDF Ingestor (PyMuPDF / PyPDF Fallback)]
     │
     ▼
[SQLite Document & Chunk Store (Foreign Keys + WAL Mode)]
     │
     ▼
[Okapi BM25 Lexical Retriever (Stopword Filter + Robertson-Spärck Jones IDF)]
     │
     ├──────────────────────────────────────────────┐
     ▼ (Evidence Above Threshold)                   ▼ (Below Threshold / Out-of-Domain)
[Model Provider (Gemini / Offline Mock)]       [Standard Grounded Refusal]
     │                                              │
     ▼                                              ▼
[Citation Auditor (Validates [Source, Page])]  [Safe, Verified Response to Student]
```

### Milestone 1 Key Capabilities
1. **Physical Page Provenance**: Every extracted text chunk carries its physical `page_number`, `document_id`, and `filename`.
2. **Idempotent Ingestion**: Re-uploading a document cleanly replaces chunks in SQLite without duplicating content.
3. **Calibrated BM25 Retrieval**: Ranks course chunks with term-frequency and document-length normalization; drops below-threshold queries.
4. **Strict Grounded Refusal**: Rejects out-of-domain or unsupported queries (*"I could not find sufficient evidence..."*) rather than hallucinating course facts.
5. **Independent Citation Auditing**: The `CitationAuditor` parses all `[Source: <filename>, Page <N>]` tokens, asserting that each citation maps to an actual chunk in the retrieved context set.
6. **Guardrail Protection**: If an audit fails (e.g., an LLM produces a hallucinated page number), the answer is withheld and an explicit audit warning is displayed.
7. **Dual-Provider Architecture**:
   - **Google Gemini**: Uses `google.genai` SDK when `GEMINI_API_KEY` is present.
   - **Offline Deterministic Mock**: Runs 100% offline with zero external network or API key requirements, enabling reproducible testing and zero-token demonstrations.

---

## 3. Repository Structure

```
Your Tutor/
├── app.py                            # Streamlit web application
├── demo_cli.py                       # Command-line demonstration tool
├── pytest.ini                        # Pytest configuration (pythonpath = .)
├── requirements.txt                  # Minimal pinned project dependencies
├── .env.example                      # Environment variable template
├── .gitignore                        # Git exclusion rules (ignores secrets & DBs)
├── docs/                             # Complete Phase 1 & 2 engineering documentation
│   ├── ARCHITECTURE.md               # System topology, data flows, and security
│   ├── ARCHITECTURE_DECISIONS.md     # 7 formal Architecture Decision Records (ADRs)
│   ├── DATA_MODEL.md                 # Pydantic v2 schemas and SQLite DDL
│   ├── INTERFACES.md                 # Abstract base class interface specifications
│   ├── REQUIREMENTS.md               # Formal SRS with unique IDs and criteria
│   ├── FEASIBILITY_AND_RISKS.md      # Feasibility analysis and empirical checks
│   ├── SDLC_ROADMAP.md               # 9-stage roadmap and milestone definitions
│   └── PROJECT_CHARTER.md            # Vision, scope, and rubric mapping
├── src/                              # Core implementation package
│   ├── core/
│   │   ├── database.py               # SQLite persistence layer (WAL + foreign keys)
│   │   ├── models.py                 # Pydantic models for chunks, evidence, and audit
│   │   └── tutor_service.py          # Orchestrator service
│   ├── ingestion/
│   │   └── pdf_ingestor.py           # Page-aware PDF text extractor (PyMuPDF + pypdf)
│   ├── retrieval/
│   │   └── retriever.py              # Pure-Python Okapi BM25 retriever
│   ├── providers/
│   │   ├── base.py                   # BaseModelProvider abstract interface
│   │   ├── mock_provider.py          # Offline deterministic mock provider
│   │   └── gemini_provider.py        # Live Google GenAI (Gemini) provider
│   └── grounding/
│       └── citation_auditor.py       # Independent citation auditing engine
└── tests/
    ├── fixtures/
    │   ├── generate_test_pdf.py      # Synthetic 4-page ML PDF fixture generator
    │   └── synthetic_ml_notes.pdf    # Generated test PDF fixture
    └── test_milestone1_grounding.py  # 10 automated unit & integration tests
```

---

## 4. Quickstart Guide (Windows PowerShell)

### Step 1: Environment Setup
Ensure Python 3.11+ is installed. Clone the repository and install requirements:

```powershell
# Navigate to project directory
cd "c:\Users\User\OneDrive\Desktop\Your Tutor"

# Install dependencies
pip install -r requirements.txt
```

### Step 2: (Optional) Configure Gemini API Key
To use live Google Gemini generation, copy `.env.example` to `.env` and insert your key:

```powershell
Copy-Item .env.example .env
# Edit .env and set: GEMINI_API_KEY=your_key_here
```
> **Note:** If no key is set, the application automatically runs in **Offline Deterministic Mode**, which requires zero API keys or network access.

### Step 3: Run the Automated Test Suite
Execute the 10-point grounding and audit test suite:

```powershell
pytest -v
```

Expected output:
```text
tests/test_milestone1_grounding.py::test_pdf_extraction_preserves_page_numbers PASSED
tests/test_milestone1_grounding.py::test_empty_or_corrupt_pdf_fails_gracefully PASSED
tests/test_milestone1_grounding.py::test_chunking_preserves_source_provenance PASSED
tests/test_milestone1_grounding.py::test_relevant_question_retrieves_expected_evidence PASSED
tests/test_milestone1_grounding.py::test_returned_citations_refer_to_retrieved_evidence PASSED
tests/test_milestone1_grounding.py::test_unsupported_questions_trigger_insufficient_evidence PASSED
tests/test_milestone1_grounding.py::test_invalid_or_fabricated_citations_fail_audit PASSED
tests/test_milestone1_grounding.py::test_failed_audit_blocks_verified_answer_display PASSED
tests/test_milestone1_grounding.py::test_reingesting_document_does_not_duplicate_chunks PASSED
tests/test_milestone1_grounding.py::test_database_records_remain_correctly_associated PASSED

============================= 10 passed in 3.50s ==============================
```

### Step 4: Run the CLI Demonstration
Execute the terminal demonstrator with sample in-domain and out-of-domain queries:

```powershell
# In-Domain Query (Backpropagation)
python demo_cli.py --query "What is backpropagation and how is the chain rule applied?"

# Out-of-Domain Query (Demonstrates Grounded Refusal)
python demo_cli.py --query "How do I make chocolate chip cookies?"
```

### Step 5: Launch the Streamlit Web App
Launch the interactive web interface:

```powershell
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## 5. Troubleshooting & FAQ

- **Q: Does this project require Docker or an external vector database?**
  - **A:** No. Milestone 1 runs entirely in pure Python using SQLite and in-memory BM25 indexing. No Docker, Redis, or external vector daemon is needed.
- **Q: What happens if `GEMINI_API_KEY` is not set?**
  - **A:** The system operates using the `MockDeterministicProvider`. It produces extractive answers with verifiable citations directly from course materials, clearly labeled with `[Provider: offline_mock]`.
- **Q: How does the system handle corrupted or 0-byte PDFs?**
  - **A:** The `PDFIngestor` catches file format errors and raises a typed `PDFIngestionError`, logging the issue without halting the application.
