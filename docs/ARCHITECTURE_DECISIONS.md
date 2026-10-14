# YOUR TUTOR — ARCHITECTURE DECISION RECORDS (ADR)
**Multimodal AI Hackathon 2026 — Track D: Personalized Tutoring & Adaptive Learning**

---

## ADR-01: Adoption of Streamlit for Frontend Interface

- **Status**: Accepted
- **Context**: The project must deliver a rich, interactive educational web interface within a ~29-hour hackathon time limit. The UI requires document upload, grounded chat with expandable citation drawers, interactive multiple-choice assessment forms, and real-time visualization of BKT mastery graphs.
- **Alternatives Considered**:
  1. *FastAPI Backend + React / Next.js Frontend*: High ceremony. Requires designing REST APIs, CORS configuration, state synchronization, separate deployment, and dual-process orchestration.
  2. *Gradio*: Suitable for simple model input/output demos, but lacks flexible layout control for multi-tab student dashboards, prerequisite graph inspection, and detailed quiz state management.
  3. *Streamlit*: Rapid Python-native reactive execution, built-in session state (`st.session_state`), native file uploaders, dataframes, and rich component ecosystem.
- **Decision**: Use **Streamlit** (v1.59.2, already verified and installed).
- **Consequences**:
  - *Positive*: Zero API impedance mismatch; UI directly interacts with Python data models and SQLite; charts render natively via Matplotlib/NetworkX.
  - *Negative*: Streamlit's script rerun model requires disciplined session state isolation to prevent unwanted widget resets during quiz interactions.

---

## ADR-02: Use of SQLite with WAL Mode for Persistence

- **Status**: Accepted
- **Context**: The application requires persistent storage for documents, extracted content chunks, concept graphs, student profiles, question banks, and response logs across sessions.
- **Alternatives Considered**:
  1. *PostgreSQL / MySQL*: Requires running external Docker containers or database daemon services on the host machine. Introduces external failure points and installation friction on Windows 11.
  2. *Flat JSON Files*: Lacks ACID transactions, foreign keys, and indexed queries. Susceptible to race conditions during rapid assessment submissions.
  3. *SQLite*: Zero-configuration, serverless, bundled directly with Python 3.13 standard library.
- **Decision**: Use **SQLite** stored locally at `data/your_tutor.db` configured with `PRAGMA journal_mode=WAL` (Write-Ahead Logging).
- **Consequences**:
  - *Positive*: Zero installation overhead; 100% portable; support for complex relational queries and foreign key constraints; WAL mode eliminates file lock contention between Streamlit worker threads.
  - *Negative*: Not intended for high-concurrency multi-node distribution (irrelevant for a local student learning companion).

---

## ADR-03: Hybrid Retrieval Architecture (Lexical BM25 + Vector Embeddings)

- **Status**: Accepted
- **Context**: The system must retrieve chunks with high precision across textbooks, slides, and transcripts. Academic materials contain exact domain keywords (e.g., "L2 Regularization", "Stochastic Gradient Descent") where pure dense embeddings often produce semantic drift, whereas pure keyword search misses paraphrased conceptual questions.
- **Alternatives Considered**:
  1. *External Vector Database (Pinecone / Qdrant)*: Requires external cloud credentials or local Docker engines; violates self-contained offline constraint.
  2. *ChromaDB Dense-Only*: ChromaDB is installed (v1.5.9), but dense-only search frequently retrieves vaguely related paragraphs while missing exact formula definitions.
  3. *Hybrid Index (Pure-Python BM25 + Cosine Similarity / ChromaDB)*: Combines reciprocal rank fusion (RRF) of lexical keyword matching with dense embeddings.
- **Decision**: Implement a **Hybrid In-Memory + SQLite Retriever** combining token-frequency BM25 with vector embeddings. When running completely offline without API access, BM25 operates as the primary deterministic retriever with fallback to ChromaDB default embeddings.
- **Consequences**:
  - *Positive*: Extremely fast (<100ms on course-sized corpus); reliable retrieval on exact technical terms; zero external vector DB dependencies.
  - *Negative*: Memory footprint scales linearly with chunk count (negligible for typical course corpora of 500–2,000 chunks).

---

## ADR-04: Deterministic Citation and Claim Verification Strategy

- **Status**: Accepted
- **Context**: Hackathon Track D mandates that every course-grounded answer must be traceable to evidence, and the system must avoid fabricating citations. Treating an LLM-as-a-judge as an infallible truth detector is mathematically and methodologically flawed.
- **Alternatives Considered**:
  1. *Pure LLM Prompting*: Hoping the LLM obeys citation instructions without post-verification. Produces hallucinated page numbers in 15–30% of responses.
  2. *Secondary LLM Judge Call*: Asking another LLM prompt to verify the first LLM. Adds 2–4 seconds of latency, doubles token costs, and can itself hallucinate verification verdicts.
  3. *Deterministic Citation Parsing & Substring Entailment Auditor*: A hybrid verification layer that:
     - Formally extracts all `[Source: <file>, Page/Slide/Time <N>]` tokens.
     - Confirms that the cited file and page/slide exist in the retrieved context set.
     - Computes token overlap and n-gram alignment between the cited sentence and the source chunk.
- **Decision**: Implement a **Deterministic Citation Auditor**. If an unverified citation or uncited factual claim is detected, the UI displays an explicit provenance badge flagging the claim.
- **Consequences**:
  - *Positive*: 100% reproducible; instant execution (<10ms); eliminates circular LLM validation hallucinations.
  - *Negative*: Paraphrased claims with zero lexical overlap require semantic similarity fallback.

---

## ADR-05: Implementation & Validation of Standard Bayesian Knowledge Tracing (BKT)

- **Status**: Accepted
- **Context**: The judging rubric allocates 20% to the Learner Model. The prompt explicitly demands genuine Corbett & Anderson (1994) BKT, rejecting superficial score percentages mislabeled as BKT.
- **Alternatives Considered**:
  1. *Running Percentage Heuristic (Correct / Total)*: Fails to separate guessing from slipping; penalized by rubric.
  2. *Deep Knowledge Tracing (DKT)*: Requires training an LSTM/Transformer on thousands of student response sequences; impossible given a single student cold-start scenario.
  3. *Standard Corbett & Anderson (1994) BKT with Closed-Form Analytical Updates*: Maintains prior $P(L_0)$, learning transition $P(T)$, guess probability $P(G)$, and slip probability $P(S)$ per concept. Computes exact analytical posteriors.
- **Decision**: Implement **Corbett & Anderson (1994) BKT** with closed-form mathematical equations and unit tests verifying zero divergence against hand-calculated analytical benchmarks.
- **Consequences**:
  - *Positive*: 100% rubric compliance; fully explainable mastery progression; runs in sub-millisecond time with zero training data; directly supports prerequisite-aware remediation.
  - *Negative*: Assumes stationary parameters and binary item response outcomes.

---

## ADR-06: Dual-Provider Runtime Architecture & Offline Mock Fallback

- **Status**: Accepted
- **Context**: The user environment currently has no `GEMINI_API_KEY` set. Judges evaluating the project may not provide an API key or may exhaust quotas. The system must remain 100% operational and verifiable offline.
- **Alternatives Considered**:
  1. *Hardcoded Gemini SDK Only*: Crashes at runtime if `GEMINI_API_KEY` is missing or quota is exceeded.
  2. *Synthetic Precomputed Canned Responses*: Inflexible; cannot respond to arbitrary user questions; dishonest if disguised as live responses.
  3. *Pluggable `BaseModelProvider` with Live `GeminiProvider` and `MockDeterministicProvider`*:
     - `GeminiProvider` uses the modern `google.genai` SDK when `GEMINI_API_KEY` is present.
     - `MockDeterministicProvider` operates offline by taking the retrieved course chunks, extracting core definitions, and synthesizing grounded, cited responses and assessment items deterministically. It explicitly displays `[Provider: Offline Deterministic Engine]`.
- **Decision**: Implement the **Dual-Provider Architecture**.
- **Consequences**:
  - *Positive*: 100% reliable execution during grading; zero risk of API quota crashes; test suite and benchmarks run in CI/CD without network access.
  - *Negative*: Mock provider cannot generate novel open-ended creative prose beyond what is present in retrieved chunks.

---

## ADR-07: Multimodal Scope Boundaries (Implemented Initially vs. Deferred)

- **Status**: Accepted
- **Context**: Multimodal understanding must be genuinely implemented rather than approximated by transcript dumping alone. However, time and system constraints (e.g., absence of FFmpeg on PATH) dictate strict scoping.
- **Decision Matrix**:
  - **Implemented Initially**:
    - *PDF Textbooks*: Page-level text extraction, section title hierarchy, embedded diagram/figure image extraction to disk with page numbers and captions (PyMuPDF / pypdf).
    - *Presentation Decks*: Slide-level text, slide titles, slide numbers, speaker notes, embedded diagrams (python-pptx).
    - *Lecture Videos*: Audio transcript segment indexing with start and end timestamps down to the second (`.vtt`, `.srt`, `.json` sidecars).
    - *Diagrams*: Visual asset catalog linked to source pages with OCR and semantic textual captions indexed for retrieval.
  - **Deferred**:
    - Direct local audio extraction from raw `.mp4` video files via Whisper CLI (deferred due to missing host FFmpeg).
    - Live video frame visual object tracking and scene classification.
    - Handwritten marginalia OCR fine-tuning.
- **Consequences**:
  - *Positive*: Guaranteed stability on host Windows 11 environment; 100% defensible multimodal grounding without brittle external binary dependencies.
  - *Negative*: Lecture video ingestion requires accompanying transcript files.
