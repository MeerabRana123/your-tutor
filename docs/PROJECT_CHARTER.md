# YOUR TUTOR — PROJECT CHARTER
**Multimodal AI Hackathon 2026 — Track D: Personalized Tutoring & Adaptive Learning**

---

## 1. Executive Summary

| Attribute | Details |
| :--- | :--- |
| **Project Title** | **Your Tutor** |
| **Track** | Track D: Personalized Tutoring & Adaptive Learning |
| **Core Principle** | *Every course-grounded answer must be traceable to evidence, every mastery update must be explainable, and every evaluation result must be reproducible.* |
| **Current Project Time** | October 13, 2026, 18:55 PKT |
| **Submission Deadline** | October 14, 2026, 23:45 PKT (~29 hours remaining) |
| **Target Runtime Environment**| Windows 11, Python 3.13, Streamlit, SQLite, Pure Python core |
| **Lead Developer** | Student Developer (Pair Programming with Antigravity AI) |

---

## 2. Problem Statement

Standard Retrieval-Augmented Generation (RAG) chatbots for education suffer from four systemic points of failure:

1. **Illusion of Multimodal Grounding**: Conventional educational chatbots convert slides and lecture videos into raw text transcript dumps. They lose page provenance, slide layout hierarchy, diagram semantics, and timestamp-synchronized video context.
2. **Hallucinated or Superficial Citations**: When students ask complex questions, vanilla LLMs invent citations, blend general internet knowledge with specific course conventions, or extrapolate without citing specific definitions.
3. **Black-Box "Adaptive" Learning**: Most educational apps compute an arbitrary percentage score and label it "adaptive." They lack a formal psychometric model, cannot isolate guess versus slip probabilities, and cannot track prerequisite dependencies when diagnosing student struggles.
4. **Unverifiable Evaluation**: Projects routinely claim high accuracy based on anecdotal test questions rather than systematic, reproducible benchmarks measuring faithfulness, context precision, out-of-domain rejection, and longitudinal learner trajectories.

---

## 3. Product Vision & Differentiators

**Your Tutor** is a source-grounded, multimodal, adaptive learning companion designed for rigorous academic courses. It bridges course ingestion, deterministic psychometric modeling, and grounded multimodal tutoring.

### Core Differentiators

```
+---------------------------------------------------------------------------------------------------+
|                                      YOUR TUTOR DIFFERENTIATORS                                   |
+---------------------------------------------------------------------------------------------------+
| 1. High-Precision Multimodal Grounding:                                                          |
|    - Direct page-level (PDF), slide-level (PPTX), and timestamp-level (Video) provenance.         |
|    - Figure & diagram extraction with spatial metadata, OCR, and visual captioning.              |
|                                                                                                   |
| 2. Verifiable Citation & Refusal Guardrails:                                                     |
|    - Deterministic chunk-level citation validation before answer presentation.                    |
|    - Explicit refusal mechanism for unsupported / out-of-syllabus questions.                     |
|                                                                                                   |
| 3. Standard Bayesian Knowledge Tracing (BKT):                                                    |
|    - Pure Corbett & Anderson (1994) mathematical formulation: P(L0), P(T), P(G), P(S).           |
|    - Closed-form posterior updating; fully explainable mastery progression per concept.          |
|    - Directed Acyclic Graph (DAG) prerequisite remediation routing.                              |
|                                                                                                   |
| 4. Transparent Benchmark Pipeline:                                                               |
|    - Labeled benchmark suite testing in-domain, out-of-domain, and diagram-grounded queries.      |
|    - Multi-session simulation of 3 distinct learner archetypes (Struggling, Inconsistent, Fast). |
|                                                                                                   |
| 5. Multi-Provider Architecture with Deterministic Fallback:                                       |
|    - Pluggable runtime model provider (Gemini / OpenAI / Mock).                                   |
|    - 100% verifiable offline demonstration mode independent of API keys or rate limits.          |
+---------------------------------------------------------------------------------------------------+
```

---

## 4. Target Users & Use Cases

### Target Users
- **Higher Education STEM & Computer Science Students**: Students digesting complex technical courses containing formal proofs, code snippets, architectural diagrams, slide decks, and hours of lecture video.
- **Instructors and Teaching Assistants**: Educators who require that automated tutoring adheres strictly to the official syllabus, without inventing extraneous terminology or misleading answers.

### Primary User Scenarios
1. **Source-Anchored Socratic Study**: A student asks a question about a tricky concept (e.g., "How does backpropagation handle the chain rule in convolutional layers?"). The tutor retrieves the exact slide and textbook page, displays the diagram, cites the specific paragraph, and explains the concept using course-specific notation.
2. **Prerequisite-Aware Adaptive Practice**: A student takes a diagnostic quiz. They fail a question on "Dynamic Programming State Transitions." Instead of merely repeating similar questions, the tutor inspects the prerequisite graph, identifies that the student's mastery in "Recursion with Memoization" has dropped, and routes remediation to the prerequisite concept first.
3. **Audited Exam Prep**: A student reviews past lectures. For every quiz item generated by the tutor, the question stems, correct options, and distractor rationales are explicitly anchored to textbook pages and slide numbers.

---

## 5. Scope & Prioritization (29-Hour Constraint)

Given the ~29-hour hackathon timeframe, features are strictly triaged into P0 (Core MVP), P1 (High-Value Differentiators), P2 (Polishing), and Deferred.

| Priority | Scope Item | Justification |
| :--- | :--- | :--- |
| **P0 (Must Have)** | PyMuPDF PDF extraction with page metadata | 20% Multimodal Grounding rubric |
| **P0 (Must Have)** | python-pptx slide deck extraction with slide index | 20% Multimodal Grounding rubric |
| **P0 (Must Have)** | Pre-indexed/transcribed video lectures with timestamp alignment | 20% Multimodal Grounding rubric |
| **P0 (Must Have)** | Figure & diagram extraction with captions and page anchor | 20% Multimodal Grounding rubric |
| **P0 (Must Have)** | Lexical/Dense hybrid chunk retrieval with source provenance | 20% Grounding rubric |
| **P0 (Must Have)** | Grounded Q&A with strict citations `[Source: File, Page/Slide/Time]` | 20% Grounding rubric |
| **P0 (Must Have)** | Out-of-domain and insufficient evidence refusal | 20% Grounding rubric |
| **P0 (Must Have)** | Standard BKT implementation with tested mathematical update equations | 20% Personalization rubric |
| **P0 (Must Have)** | Explicit prerequisite DAG for concept hierarchy | 20% Personalization rubric |
| **P0 (Must Have)** | Adaptive MCQ and Short-Answer quiz generation | 15% Assessment rubric |
| **P0 (Must Have)** | Reproducible evaluation script with labeled test set | 15% Evaluation rubric |
| **P0 (Must Have)** | 3 Simulated learner profile benchmark runs over multiple sessions | 15% Evaluation rubric |
| **P0 (Must Have)** | Streamlit interface with grounding inspector & mastery dashboard | 15% UX / 15% Tech Implementation |
| **P0 (Must Have)** | Configurable model provider (Gemini + Offline Mock Provider) | Technical reliability / zero-key fallback |
| **P1 (Should Have)**| Diagram-focused question generation (asking questions about visual figures) | High differentiator for Multimodal track |
| **P1 (Should Have)**| Visual prerequisite graph rendering (NetworkX + Streamlit) | Visual appeal and pedagogical clarity |
| **P1 (Should Have)**| RAGAS-style automated metric reporting (Faithfulness, Precision) | Evaluation rigor |
| **P2 (Nice to Have)**| Numerical question checking with deterministic tolerance | Assessment diversity |
| **P2 (Nice to Have)**| Study plan export / Markdown summary generation | Extra student utility |
| **Deferred** | Multi-agent LangGraph / CrewAI orchestration | Unnecessary latency and architectural risk |
| **Deferred** | External Vector Database (Qdrant / Pinecone / Milvus) | Unnecessary infrastructure overhead |
| **Deferred** | Live speech-to-speech audio conversation | Out of scope for 29h window |
| **Deferred** | Full-stack FastAPI + React/Next.js rewrite | Streamlit is optimal for rapid, reliable delivery |

---

## 6. Success Criteria & Rubric Alignment

| Rubric Category | Weight | Target Metric / Evidence of Success |
| :--- | :---: | :--- |
| **1. Multimodal Knowledge Base** | **20%** | Ingestion of PDF, PPTX, Video Transcripts + Timestamps, and extracted Diagrams. 100% of chunks retain exact source metadata (filename, page, slide, timestamp). Documented boundaries of extraction capabilities. |
| **2. Source Grounding** | **20%** | Zero fabricated citations. 100% of in-domain queries cite verified source chunks. Greater than 90% accuracy on detecting and rejecting unsupported/out-of-syllabus questions on the labeled benchmark. |
| **3. Adaptive Assessments** | **15%** | Deterministic answer validation for MCQs. Cited feedback explaining why answers are correct or incorrect. Zero question duplicates within a single learner session. |
| **4. Learner Model (Personalization)** | **20%** | Mathematically rigorous BKT implementation with unit test validation of update equations. Observable mastery progression across sessions. Prerequisite remediation routing demonstrated. |
| **5. System Evaluation** | **15%** | Labeled test suite (>20 curated multimodal questions). Automated evaluation script outputting precision, recall, faithfulness, and citation validity. 3 simulated learner profiles reporting distinct mastery trajectories. |
| **6. UX & Technical Implementation** | **15%** | Responsive Streamlit application. Clean, modular Python architecture (Separation of Concerns). Zero hardcoded keys. 100% automated test pass rate. Complete documentation and run instructions. |
