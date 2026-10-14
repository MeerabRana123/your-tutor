# Your Tutor — Source-Grounded Multimodal Adaptive Learning Companion

[![Track](https://img.shields.io/badge/Hackathon-Multimodal%20AI%202026-blue.svg)](https://github.com)
[![Track D](https://img.shields.io/badge/Track%20D-Personalized%20Tutoring%20%26%20Adaptive%20Learning-green.svg)](https://github.com)
[![Python](https://img.shields.io/badge/Python-3.13%2B-blue.svg)](https://python.org)
[![Tests](https://img.shields.io/badge/Tests-20%20Passed%20(100%25)-brightgreen.svg)](tests/)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)

> **Central Product Principle:**
> *Every course-grounded answer must be traceable to evidence, every mastery update must be explainable, and every evaluation result must be reproducible.*

---

## 1. Project Overview & Hackathon MVP

**Your Tutor** is an academic AI learning companion built for rigorous university-level courses (demonstrated on an *Introductory Machine Learning & Deep Learning* curriculum).

Unlike generic conversational RAG wrappers that hallucinate external citations or convert course materials into lossy text dumps, **Your Tutor** enforces **strict physical provenance** down to the source page, an **independent citation auditing layer**, **adaptive multiple-choice assessment generation**, **standard Bayesian Knowledge Tracing (BKT)**, and an **offline deterministic engine** requiring zero external API keys.

---

## 2. System Architecture & Feature Matrix

### Completed MVP Capabilities (Verified & Tested)
- [x] **Page-Aware PDF Ingestion**: Extracts text chunks retaining physical `page_number`, `document_id`, and `filename` using PyMuPDF / PyPDF.
- [x] **Idempotent Ingestion**: Re-uploading a document cleanly replaces records in SQLite without accumulating duplicates.
- [x] **Okapi BM25 Lexical Retrieval**: Query-term coverage guardrails prevent false positives on generic stop words.
- [x] **Grounded Refusal Guardrails**: Out-of-domain queries (*"How do I bake sourdough bread?"*) are safely rejected rather than hallucinating course facts.
- [x] **Independent Citation Auditing**: The `CitationAuditor` verifies that every `[Source: file, Page N]` citation matches retrieved evidence and flags unverified claims.
- [x] **Adaptive Assessment Generation**: Generates 4-option MCQs directly grounded in course text with validated answer keys and transparent generator mode (`offline_template` vs `gemini`).
- [x] **Bayesian Knowledge Tracing (BKT)**: Standard Corbett & Anderson (1994) closed-form posterior updates for $P(L_0)$, $P(T)$, $P(G)$, and $P(S)$ with division-by-zero clamping.
- [x] **Adaptive Personalization**: Responses update topic mastery in real-time. Missed questions trigger grounded revision recommendations citing the exact source page.
- [x] **Reproducible Evaluation Benchmark**: 8-item ground truth suite testing in-domain retrieval and out-of-domain refusal with 100% verified accuracy.
- [x] **Dual-Provider Model Abstraction**:
  - **Google Gemini**: Uses `google.genai` SDK when `GEMINI_API_KEY` is present.
  - **Offline Deterministic Mock**: Runs 100% offline with zero external network or API key requirements.

### Planned / Post-Hackathon Deferred Scope (Honest Boundaries)
- [ ] Direct video audio extraction from raw `.mp4` (deferred due to missing host FFmpeg binary; transcript sidecars supported).
- [ ] Presentation deck (`.pptx`) slide ingestion (designed in architecture, deferred to next release).
- [ ] Multi-skill item response theory (MIRT) and deep knowledge tracing (DKT).
- [ ] Graph-based prerequisite DAG remediation (recommendations are currently topic-grounded page citations).

> **Pedagogical Note on Mastery:**
> Mastery values $P(L)$ are statistical estimates of latent proficiency over practice items under stationary Markov assumptions, not certified or infallible measurements of human intelligence.

---

## 3. Repository Structure

```
Your Tutor/
├── app.py                                        # Streamlit 3-tab web application
├── demo_cli.py                                   # Headless/interactive CLI demonstrator
├── pytest.ini                                    # Pytest configuration (pythonpath = .)
├── requirements.txt                              # Minimal pinned project dependencies
├── .env.example                                  # Environment variable template
├── .gitignore                                    # Git exclusion rules (ignores secrets & DBs)
├── docs/                                         # Complete engineering documentation
│   ├── ARCHITECTURE.md                           # System topology and data flows
│   ├── ARCHITECTURE_DECISIONS.md                 # 7 formal ADRs
│   ├── DATA_MODEL.md                             # Pydantic v2 schemas and SQLite DDL
│   ├── INTERFACES.md                             # Abstract base class specifications
│   ├── REQUIREMENTS.md                           # Formal SRS with unique IDs
│   ├── FEASIBILITY_AND_RISKS.md                  # Feasibility and environment checks
│   ├── SDLC_ROADMAP.md                           # Phased execution plan
│   └── PROJECT_CHARTER.md                        # Vision, scope, and rubric mapping
├── eval/                                         # Reproducible evaluation suite
│   ├── benchmark.py                              # 8-item benchmark runner
│   └── benchmark_report.json                     # Generated empirical evaluation report
├── src/                                          # Core implementation package
│   ├── assessment/
│   │   ├── generator.py                          # Grounded MCQ generator & answer checker
│   │   └── models.py                             # Assessment and submission data models
│   ├── bkt/
│   │   └── engine.py                             # Corbett & Anderson BKT mathematics
│   ├── core/
│   │   ├── database.py                           # SQLite persistence (WAL + foreign keys)
│   │   ├── models.py                             # Core domain models
│   │   └── tutor_service.py                      # Orchestrator service
│   ├── grounding/
│   │   └── citation_auditor.py                   # Independent citation auditor
│   ├── ingestion/
│   │   └── pdf_ingestor.py                       # Page-aware PDF extractor (PyMuPDF + pypdf)
│   ├── providers/
│   │   ├── base.py                               # BaseModelProvider interface
│   │   ├── gemini_provider.py                    # Live Google GenAI SDK provider
│   │   └── mock_provider.py                      # Offline deterministic mock provider
│   └── retrieval/
│       └── retriever.py                          # Okapi BM25 retriever with stopword filtering
└── tests/                                        # Automated test suite (20 tests)
    ├── fixtures/
    │   ├── generate_test_pdf.py                  # Generates synthetic test PDF
    │   └── synthetic_ml_notes.pdf                # 4-page test PDF fixture
    ├── test_assessment_and_personalization.py    # Assessment & personalization tests
    ├── test_bkt_math.py                          # BKT math & parameter tests
    ├── test_evaluation_benchmark.py              # Automated benchmark test
    └── test_milestone1_grounding.py              # 10 grounding & provenance tests
```

---

## 4. Quickstart Guide (Windows PowerShell)

### Step 1: Install Dependencies
Ensure Python 3.11+ is installed:

```powershell
# Navigate to project directory
cd "c:\Users\User\OneDrive\Desktop\Your Tutor"

# Install dependencies
pip install -r requirements.txt
```

### Step 2: (Optional) Configure Gemini API Key
To use live Google Gemini generation, copy `.env.example` to `.env` and set your key:

```powershell
Copy-Item .env.example .env
# Edit .env and set: GEMINI_API_KEY=your_key_here
```
> **Note:** If no key is set, the application automatically runs in **Offline Deterministic Mode**, requiring zero API keys or network access.

### Step 3: Run the Full Test Suite
Run all 20 unit and integration tests across grounding, BKT, assessments, and benchmarks:

```powershell
pytest -v
```

Expected output:
```text
tests/test_assessment_and_personalization.py::test_assessment_question_validation PASSED [  5%]
tests/test_assessment_and_personalization.py::test_grounded_question_generation PASSED [ 10%]
tests/test_assessment_and_personalization.py::test_deterministic_answer_evaluation PASSED [ 15%]
tests/test_assessment_and_personalization.py::test_end_to_end_assessment_personalization_flow PASSED [ 20%]
tests/test_bkt_math.py::test_bkt_parameter_validation PASSED             [ 25%]
tests/test_bkt_math.py::test_bkt_correct_answer_increases_mastery PASSED [ 30%]
tests/test_bkt_math.py::test_bkt_incorrect_answer_decreases_mastery PASSED [ 35%]
tests/test_bkt_math.py::test_bkt_numerical_stability_long_sequence PASSED [ 40%]
tests/test_bkt_math.py::test_bkt_sqlite_persistence PASSED               [ 45%]
tests/test_evaluation_benchmark.py::test_reproducible_evaluation_benchmark PASSED [ 50%]
tests/test_milestone1_grounding.py::test_pdf_extraction_preserves_page_numbers PASSED [ 55%]
tests/test_milestone1_grounding.py::test_empty_or_corrupt_pdf_fails_gracefully PASSED [ 60%]
tests/test_milestone1_grounding.py::test_chunking_preserves_source_provenance PASSED [ 65%]
tests/test_milestone1_grounding.py::test_relevant_question_retrieves_expected_evidence PASSED [ 70%]
tests/test_milestone1_grounding.py::test_returned_citations_refer_to_retrieved_evidence PASSED [ 75%]
tests/test_milestone1_grounding.py::test_unsupported_questions_trigger_insufficient_evidence PASSED [ 80%]
tests/test_milestone1_grounding.py::test_invalid_or_fabricated_citations_fail_audit PASSED [ 85%]
tests/test_milestone1_grounding.py::test_failed_audit_blocks_verified_answer_display PASSED [ 90%]
tests/test_milestone1_grounding.py::test_reingesting_document_does_not_duplicate_chunks PASSED [ 95%]
tests/test_milestone1_grounding.py::test_database_records_remain_correctly_associated PASSED [100%]

============================= 20 passed in 2.68s ==============================
```

### Step 4: Run the Reproducible Evaluation Benchmark
Execute the standalone benchmark runner:

```powershell
python eval/benchmark.py
```

Observed metrics:
- In-Domain Retrieval Precision@1: `100.0%`
- Citation Audit Pass Rate: `100.0%`
- Out-of-Domain Refusal Rate: `100.0%`
- Overall Benchmark Accuracy: `100.0%`

### Step 5: Run the CLI Demonstrator
Test grounded answering and refusal directly in the terminal:

```powershell
# In-Domain Query
python demo_cli.py --query "What is backpropagation and how is the chain rule applied?"

# Out-of-Domain Query (Refusal Demo)
python demo_cli.py --query "What temperature is required to bake a sourdough loaf in a Dutch oven?"
```

### Step 6: Launch the Streamlit Web Application
Launch the interactive 3-tab web dashboard:

```powershell
streamlit run app.py
```
Open `http://localhost:8501` in your browser.

---

## 5. Manual Demonstration Steps (Recording Guide)

Follow these exact steps when recording a demo video for judges:

1. **Ingestion**:
   - In the sidebar, check "Use Synthetic ML Notes Fixture" and click **🚀 Ingest Document**.
   - Note the success message: `✅ Ingested 'synthetic_ml_notes.pdf' (4 pages, 4 chunks)`.
2. **Tab 1: Grounded Q&A**:
   - Select `"What is backpropagation and how does the chain rule apply?"` and click **Submit Question**.
   - Show the answer with `[Source: synthetic_ml_notes.pdf, Page 3]` citation, `Provider: offline_mock`, and `Citation Audit: PASSED ✅`.
   - Select `"What temperature is required to bake a sourdough loaf in a Dutch oven?"` and submit.
   - Show the refusal: *"I could not find sufficient evidence in the uploaded material to answer this question."*
3. **Tab 2: Adaptive Practice & BKT Mastery**:
   - Select topic `"Backpropagation and the Chain Rule"` and click **🎲 Generate Practice Item**.
   - Point out the physical source citation (`[Source: synthetic_ml_notes.pdf, Page 3]`) and generator mode (`offline_template`).
   - Select Option `B` and click **Submit Answer**. Show the success message and positive BKT mastery shift ($\Delta P(L) > 0$).
   - Point out the updated progress bar in the Learner Mastery Dashboard.
   - Generate a question on `"Loss and Cost Functions"`, select an incorrect option, and submit.
   - Show the BKT mastery decrease and the targeted revision recommendation: *"Revision Recommendation: Please review Page 1 of synthetic_ml_notes.pdf"*.
4. **Tab 3: Evaluation Benchmark**:
   - Click **▶️ Execute Benchmark Suite**.
   - Show the 4 metric cards (100% Precision, 100% Audit, 100% Refusal) and the itemized dataframe.
