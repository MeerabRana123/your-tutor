# YOUR TUTOR — SDLC ROADMAP & EXECUTION PLAN
**Multimodal AI Hackathon 2026 — Track D: Personalized Tutoring & Adaptive Learning**

---

## 1. Roadmap Overview & Timeline

This roadmap outlines the disciplined, staged execution of **Your Tutor** across the remaining ~29-hour window leading to the submission deadline of **October 14, 2026 at 23:45 PKT**.

```mermaid
gantt
    title Your Tutor SDLC Execution Roadmap (Oct 13-14, 2026)
    dateFormat  YYYY-MM-DD HH:mm
    axisFormat  %m-%d %H:%M
    
    section Phase 1-3: Foundations
    Phase 1: Requirements & Feasibility    :done, p1, 2026-10-13 18:55, 2026-10-13 20:30
    Phase 2: System Architecture           :active, p2, 2026-10-13 20:30, 2026-10-13 22:30
    Phase 3: Detailed Design & Models      :p3, 2026-10-13 22:30, 2026-10-14 00:30
    
    section Phase 4: Core Implementation
    Module Ingestion & Multimodal Store    :p4a, 2026-10-14 00:30, 2026-10-14 03:00
    Module Grounding, Retrieval & Verif    :p4b, 2026-10-14 03:00, 2026-10-14 05:30
    Module BKT Engine & Prerequisite DAG   :p4c, 2026-10-14 05:30, 2026-10-14 07:30
    Module Adaptive Assessments & Quiz     :p4d, 2026-10-14 07:30, 2026-10-14 09:00
    Module Streamlit UI Integration        :p4e, 2026-10-14 09:00, 2026-10-14 10:30
    
    section Phase 5-7: Verification & Eval
    Phase 5: Automated Testing Suite       :p5, 2026-10-14 10:30, 2026-10-14 14:00
    Phase 6: Evaluation & Simulation Runs  :p6, 2026-10-14 14:00, 2026-10-14 17:30
    Phase 7: Deployment & Security Review  :p7, 2026-10-14 17:30, 2026-10-14 19:30
    
    section Phase 8-9: Polish & Submission
    Phase 8: Documentation & Demo Video    :p8, 2026-10-14 19:30, 2026-10-14 22:30
    Phase 9: Final Package & Submission    :p9, 2026-10-14 22:30, 2026-10-14 23:45
```

---

## 2. SDLC Phase Breakdown & Quality Gates

### Phase 1: Requirements Engineering & Feasibility Analysis *(Current Stage)*
- **Objective**: Establish rock-solid scope, define testable acceptance criteria, and perform environment reality checks.
- **Deliverables**:
  - `docs/PROJECT_CHARTER.md`
  - `docs/REQUIREMENTS.md`
  - `docs/FEASIBILITY_AND_RISKS.md`
  - `docs/SDLC_ROADMAP.md`
  - `docs/ASSUMPTIONS_AND_OPEN_QUESTIONS.md`
- **Testing Gate**: Zero ambiguous requirements; all 6 hackathon rubric categories mapped to concrete artifacts; time feasibility established.
- **Exit Criteria**: All 5 Phase 1 documents reviewed and confirmed with the student developer.

---

### Phase 2: System Architecture & Component Interface Design
- **Objective**: Define high-level module architecture, data flows, and clean component interfaces (Separation of Concerns).
- **Deliverables**:
  - `docs/ARCHITECTURE.md` (System topology, data flow, component boundaries).
  - Abstract Interface Contracts:
    - `BaseIngestor` for PDF, PPTX, Video transcripts.
    - `BaseRetriever` and `BaseGroundingVerifier`.
    - `BaseModelProvider` (Gemini, OpenAI, Mock).
    - `BaseBKTEngine` and `PrerequisiteGraph`.
- **Testing Gate**: Interface signatures typed with Python `typing` / `abc` without circular dependencies.
- **Exit Criteria**: Architecture document finalized; no code implementation started yet.

---

### Phase 3: Detailed Design & Data Modeling
- **Objective**: Formalize Pydantic data models, SQLite schema DDL, citation schema, and BKT state transition logic.
- **Deliverables**:
  - `docs/DATA_MODEL.md` (Entity schemas: `DocumentChunk`, `FigureMetadata`, `ConceptNode`, `LearnerState`, `AssessmentItem`, `ResponseLog`).
  - Database schema definition (`schema.sql` design).
  - Explicit BKT transition matrix and parameter bounding rules.
  - Evaluation dataset specification schema (`eval/benchmark_schema.json`).
- **Testing Gate**: Schema validation passes in isolation; model relationships are normalized and unambiguous.
- **Exit Criteria**: Data schemas and entity models fully specified before any operational logic is written.

---

### Phase 4: Incremental Core Implementation

#### Milestone 1: Core Grounding Vertical Slice (The Primary Implementation Target)
Before assembling secondary features, the team must complete and verify the core vertical slice:
`PDF Ingestion` ➔ `Page-Aware Chunking` ➔ `Hybrid Retrieval` ➔ `Evidence-Backed Answer` ➔ `Citation Verification` ➔ `Automated Test Suite`.

```
[Sample Course PDF] ➔ [PyMuPDF Parser] ➔ [SQLite Chunk Store (with Page Numbers)]
                                                  │
                                                  ▼
[Student Query] ➔ [BM25/Dense Retriever] ➔ [Retrieved Context Chunks]
                                                  │
                                                  ▼
[Grounded Model Provider] ➔ [Synthesized Answer with [Source: file, Page N]]
                                                  │
                                                  ▼
[Citation Auditor] ➔ [Verification Status: Verified / Flagged] ➔ [Passed to Student/UI]
```

##### Exact Acceptance Tests for Milestone 1:
1. **`test_pdf_page_aware_extraction`**:
   - Ingests a multi-page ML textbook excerpt (`sample_ml_textbook.pdf`).
   - Asserts that 100% of generated `ContentChunk` records have non-null `page_number` matching the physical source page.
   - Asserts that chunk token lengths stay within $[150, 450]$ words.
2. **`test_hybrid_retrieval_ranking`**:
   - Executes queries with known ground truth locations (e.g., *"What is backpropagation?"*).
   - Asserts that the expected source page chunk appears in the top-2 retrieved results with similarity $> 0.40$.
3. **`test_evidence_backed_answer_with_citations`**:
   - Sends retrieved chunks to `BaseModelProvider` (both `GeminiProvider` and `MockDeterministicProvider`).
   - Asserts that the generated answer contains valid citation format `[Source: sample_ml_textbook.pdf, Page <N>]`.
   - Asserts that the cited page matches one of the chunks supplied in context.
4. **`test_citation_verification_auditor`**:
   - Evaluates generated response through `BaseGroundingVerifier`.
   - Asserts `is_valid == True` and `invalid_citations == []` when citations match context.
5. **`test_unsupported_query_refusal`**:
   - Queries an out-of-domain topic (e.g., *"How do I bake sourdough bread?"*).
   - Asserts that retrieval score is below threshold $\theta = 0.35$.
   - Asserts that the response explicitly states refusal and generates zero citations.

##### Expected Failure Behavior & Graceful Recovery:
- **Corrupted / Password-Protected PDF**: Ingestor catches `fitz.FileDataError` / `pypdf.errors.PdfReadError`, logs a human-readable error to SQLite, and alerts the user in Streamlit without halting the application.
- **Empty / Irrelevant Retrieval Context**: System immediately halts LLM generation, bypassing token spend, and directly emits the standard grounded refusal message.
- **Model Citation Hallucination**: If the model provider hallucinates a page number not in the retrieved set (e.g., citing Page 99 when only Pages 12–15 were retrieved), `CitationAuditor` detects the discrepancy, marks `invalid_citations`, and appends an explicit visual alert badge: `⚠️ Citation unverified in course materials`.

---

#### Implementation Sub-Stages (Sequenced)
1. **Stage 4.1**: `src/core/models/` and `src/core/database.py` (Persistence and Pydantic schemas).
2. **Stage 4.2**: `src/ingestion/` (PDF parser with page coordinates, PPTX parser, video transcript parser).
3. **Stage 4.3**: `src/retrieval/` and `src/grounding/` (Hybrid index, citation builder, verification filter, out-of-domain refusal).
4. **Stage 4.4**: `src/bkt/` (Corbett & Anderson BKT engine, prerequisite DAG graph).
5. **Stage 4.5**: `src/assessment/` (Item generator, deterministic grading, distractor analysis).
6. **Stage 4.6**: `src/providers/` (Pluggable `GeminiProvider` and `MockDeterministicProvider`).
7. **Stage 4.7**: `src/ui/` (Streamlit app with ingestion, chat, quiz, mastery dashboard, and benchmark viewer).
- **Testing Gate**: Each module must pass accompanying automated smoke tests before proceeding to the next sub-stage.
- **Exit Criteria**: End-to-end user workflow runs without errors using both live API and offline mock provider.

---

### Phase 5: Automated Testing Suite (Unit, Integration & Regression)
- **Objective**: Validate correctness, edge cases, and robustness across all modules.
- **Deliverables**:
  - Unit tests: `tests/test_bkt_math.py` (proves BKT posterior formulas against hand-calculated analytical truth).
  - Unit tests: `tests/test_ingestion.py` (validates PDF and PPTX page/slide indexing).
  - Unit tests: `tests/test_retrieval_grounding.py` (tests citation generation and out-of-domain rejection).
  - Integration tests: `tests/test_end_to_end.py` (exercises complete user session: ingest -> chat -> quiz -> BKT update).
- **Testing Gate**: `pytest` executes with 100% pass rate; zero warnings or uncaught exceptions.
- **Exit Criteria**: Automated test suite integrated and runnable via single command `pytest tests/`.

---

### Phase 6: System Evaluation & Benchmarking
- **Objective**: Run reproducible benchmark evaluation and simulated multi-session learner trajectories.
- **Deliverables**:
  - `eval/benchmark_dataset.json` (Curated test set with 20+ multimodal items).
  - `eval/run_benchmark.py` (Computes Precision, Recall, Faithfulness, Citation Hit Rate).
  - `eval/simulate_learners.py` (Simulates 3 student archetypes over 15 sessions: Struggling, Guessing/Inconsistent, Fast).
  - `eval/EVALUATION_REPORT.md` (Documented results, metric tables, trajectory graphs, and honest limitations).
- **Testing Gate**: All metrics reproducible from fixed seeds; simulated results explicitly labeled as simulation.
- **Exit Criteria**: Complete, un-manipulated benchmark report generated.

---

### Phase 7: Deployment, Security Review & Sanitization
- **Objective**: Verify security, eliminate hardcoded secrets, test clean install on Windows 11.
- **Deliverables**:
  - `.gitignore` audit (ensure `.env`, DB caches, API keys are completely ignored).
  - `requirements.txt` with pinned, compatible versions.
  - Security audit report documenting file upload sanitization and API key protection.
- **Testing Gate**: Clean environment test in a virtual environment (`python -m venv test_env`).
- **Exit Criteria**: Zero secret leaks; clean installation verified.

---

### Phase 8: Documentation, Walkthrough Video Script & Final Polish
- **Objective**: Prepare submission collateral that makes evaluation effortless for hackathon judges.
- **Deliverables**:
  - Root `README.md` (Professional, GitHub-ready, badges, architecture diagram, 3-minute quickstart).
  - `docs/DEMO_WALKTHROUGH.md` (Step-by-step judge demonstration guide and video recording script).
  - UI polishing: consistent typography, error state cards, helpful tooltips.
- **Testing Gate**: A non-technical user can follow `README.md` and launch the app in under 3 minutes.
- **Exit Criteria**: All submission documentation complete.

---

### Phase 9: Final Submission Package & Submission
- **Objective**: Verify all rubric criteria are fulfilled, commit to Git, and finalize submission.
- **Deliverables**:
  - Clean Git commit history.
  - Final submission checklist signed off.
- **Testing Gate**: Final smoke test against hackathon track criteria.
- **Exit Criteria**: Submitted before October 14, 2026 at 23:45 PKT.

---

## 3. Hackathon Rubric Mapping

| Rubric Category | Weight | Primary Roadmap Phase | Key Verification Evidence |
| :--- | :---: | :---: | :--- |
| **Multimodal Knowledge Base** | 20% | Phases 4.2, 5 | Ingestion tests verifying PDF page, PPTX slide, Video timestamp, and Figure metadata retention. |
| **Source Grounding** | 20% | Phases 4.3, 5, 6 | Citation checker asserting 100% chunk-level accuracy; refusal metric $> 90\%$ on out-of-domain benchmark. |
| **Adaptive Assessments** | 15% | Phases 4.5, 5 | Deterministic MCQ checking; duplicate test proving 0% repetition across 15 practice items. |
| **Learner Model (Personalization)** | 20% | Phases 4.4, 5, 6 | Mathematical unit tests proving BKT equations; prerequisite graph traversal logs; multi-session simulated trajectories. |
| **System Evaluation** | 15% | Phase 6 | Reproducible benchmark script (`run_benchmark.py`), metric report, 3 simulated learner profiles. |
| **UX & Technical Quality** | 10% UX + 10% Tech | Phases 4.7, 7, 8 | Polished Streamlit UI, modular codebase, clean install, zero secrets, comprehensive documentation. |
