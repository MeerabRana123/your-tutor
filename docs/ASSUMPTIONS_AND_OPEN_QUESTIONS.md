# YOUR TUTOR — ASSUMPTIONS & OPEN QUESTIONS
**Multimodal AI Hackathon 2026 — Track D: Personalized Tutoring & Adaptive Learning**

---

## 1. Verified Facts (Environment & Context Ground Truth)

The following statements are confirmed ground truth verified directly against the host system:

1. **System Time & Deadline**:
   - Current local time: **October 13, 2026, ~18:55 PKT**.
   - Hackathon deadline: **October 14, 2026, 23:45 PKT**.
   - Exactly **~28 hours and 50 minutes** remain before submission.
2. **Host OS & Architecture**:
   - Operating System: **Windows 11** on 64-bit architecture.
   - Python: **Python 3.13.7** installed and functional.
   - Git: **Git version 2.54.0.windows.1** installed and functional.
   - Shell: PowerShell 5.1.
3. **Missing System Binaries**:
   - `ffmpeg` is **NOT installed** or available on system PATH.
4. **Installed Python Packages**:
   - `streamlit 1.59.2`, `pydantic 2.12.5`, `pypdf 6.14.2`, `pillow 10.4.0`, `networkx 3.6.1`, `numpy 2.5.0`, `pandas 2.3.3`, `pytest 9.1.1`, `openai 2.24.0`, `litellm 1.83.14` are present.
   - `sqlite3` is built into Python.
5. **Runtime API Key Environment**:
   - `GEMINI_API_KEY`: **Not set** (`False`).
   - `GOOGLE_API_KEY`: **Not set** (`False`).
   - `OPENAI_API_KEY`: **Not set** (`False`).
6. **Development Assistant vs. Runtime Application**:
   - Development Assistant: Antigravity IDE (Gemini 3.8 Flash High) active for pair programming.
   - Application Runtime: Runs independently in a local Python process and currently has no active external API keys configured.

---

## 2. Core Architectural & Technical Assumptions

| ID | Assumption | Rationale | Impact If Invalid |
| :---: | :--- | :--- | :--- |
| **ASM-01** | **Exemplar Course Domain Selection** | We assume an exemplar course domain with rich multimodal content (e.g., *Introduction to Deep Learning* or *Computer Systems Architecture*) will be used for standard demonstration and benchmarking. | If the user prefers a different subject (e.g., Biology, Organic Chemistry, Calculus), the schema remains identical, but the seed materials and benchmark questions will simply target that curriculum. |
| **ASM-02** | **Transcript Sidecars for Lecture Video Ingestion** | Because system `ffmpeg` is absent on Windows 11, we assume lecture videos are paired with companion transcript files (`.vtt`, `.srt`, or structured `.json` with millisecond timestamps). | If raw video audio extraction must occur without sidecars, we must install `imageio-ffmpeg` or an external FFmpeg binary onto the user's path. |
| **ASM-03** | **Zero-Key Offline Fallback Priority** | We assume judges or evaluators may run the application without providing their own `GEMINI_API_KEY`. Therefore, the app must include a high-fidelity `MockDeterministicProvider` that allows full end-to-end evaluation and UI demonstration offline. | If the app strictly required a live paid key, judges without keys or quota would encounter fatal startup errors. |
| **ASM-04** | **BKT Parameter Priors from Literature** | We assume standard literature-backed BKT parameter defaults per concept: $P(L_0)=0.20$, $P(T)=0.15$, $P(G)=0.20$, $P(S)=0.10$. | If concept-specific empirical logs are unavailable, literature priors prevent model collapse while still demonstrating genuine Bayesian updating. |
| **ASM-05** | **Prerequisite Graph Structure** | We assume the course curriculum can be represented as an explicit Directed Acyclic Graph (DAG) with 5–10 core concepts, rather than requiring dynamic unsupervised ontology extraction from raw text. | An explicit, curated DAG provides 100% deterministic remediation routing and prevents cycle errors. |
| **ASM-06** | **Evaluation Ground Truth Independence** | We assume evaluation benchmarks must contain fixed, human-verified ground truth questions and citations rather than purely automated LLM-as-a-judge scoring. | Eliminates evaluation circularity and model hallucination during benchmarking. |

---

## 3. Open Questions for the Student Developer

These questions require clarification during Phase 2 or Phase 3 to fine-tune implementation details:

### Question 1: Course Subject Matter & Seed Material
- **Context**: The multimodal knowledge base requires sample course materials (a textbook excerpt PDF, a lecture slide deck PPTX, and a timestamped video lecture transcript).
- **Options**:
  - *Option A (Recommended)*: **Computer Science / Machine Learning** (e.g., *Neural Networks, Gradient Descent, Backpropagation, and Overfitting*) — Excellent diagrams, equations, and clear prerequisite relationships.
  - *Option B*: **Operating Systems / Computer Architecture** (e.g., *Processes, Virtual Memory, Caching, Paging*).
  - *Option C*: User-supplied custom course materials already saved on disk.
- **Impact**: Determines the initial seed documents and benchmark test questions placed in `data/sample_course/`.

### Question 2: Runtime LLM API Key Availability
- **Context**: The application runtime currently has no environment variables set (`GEMINI_API_KEY`, etc.).
- **Options**:
  - *Option A*: The student will add a personal `GEMINI_API_KEY` to a `.env` file for live testing.
  - *Option B*: The student does not have an API key right now; the application should be developed and tested primarily against the `MockDeterministicProvider`, with Gemini integration tested when a key is available.
- **Impact**: Both modes will be supported seamlessly via our pluggable `BaseModelProvider` interface.

### Question 3: PyMuPDF (`fitz`) vs. `pypdf`
- **Context**: `pypdf` is already installed in the environment. PyMuPDF (`fitz`) offers faster rendering and built-in image extraction bounding boxes.
- **Options**:
  - *Option A (Recommended)*: Install `pymupdf` (`pip install pymupdf`) for advanced diagram extraction.
  - *Option B*: Rely exclusively on pre-installed `pypdf` and `pillow`.
- **Impact**: PyMuPDF simplifies diagram extraction; testing PyMuPDF installation on Windows 11 will be done in Phase 2.

---

## 4. Architectural Decision Log (ADL)

| Decision | Alternatives Considered | Selected Choice | Rationale |
| :--- | :--- | :--- | :--- |
| **Frontend Framework** | FastAPI + React, Next.js, Streamlit | **Streamlit** | Enables rich interactive UI, stateful sessions, and charting within the ~29h time budget without frontend-backend API synchronization overhead. |
| **Database & Persistence** | PostgreSQL, MongoDB, SQLite | **SQLite (via Python built-in)** | Zero configuration, zero external service dependency, fully persistent, supports atomic transactions and rapid testing. |
| **Vector Storage** | Qdrant, Pinecone, ChromaDB, In-Memory Hybrid | **In-Memory + SQLite Hybrid (BM25 + Dense Embeddings)** | Avoids native compilation or C++ dependency issues on Windows 11; lightweight, deterministic, and instant for course-sized corpora (<1,000 chunks). |
| **Model Provider Interface** | Hardcoded Google GenAI SDK | **Pluggable `BaseModelProvider`** | Decouples application logic from specific LLM vendors; enables seamless zero-key mock execution for offline testing and evaluation. |
| **Learner Modeling** | Simple percentage heuristic, Deep Knowledge Tracing (DKT), BKT | **Corbett & Anderson Bayesian Knowledge Tracing (BKT)** | Required by rubric; mathematically rigorous, completely explainable, and analytically provable with zero neural network training required. |
