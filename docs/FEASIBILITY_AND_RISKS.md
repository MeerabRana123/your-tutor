# YOUR TUTOR — FEASIBILITY ANALYSIS & RISK ASSESSMENT
**Multimodal AI Hackathon 2026 — Track D: Personalized Tutoring & Adaptive Learning**

---

## 1. Feasibility Analysis

### 1.1 Time Feasibility (The ~29-Hour Hackathon Constraint)
- **Current Timestamp**: October 13, 2026, 18:55 PKT.
- **Submission Deadline**: October 14, 2026, 23:45 PKT.
- **Available Time Window**: **~28 hours and 50 minutes**.

To deliver an exceptional, bug-free, defensible submission within this strict window, we must execute with disciplined agility. Time is allocated across SDLC phases with hard timeboxes:

| Phase | SDLC Stage | Target Window | Budgeted Hours | Gate Deliverable |
| :---: | :--- | :---: | :---: | :--- |
| **Phase 1** | Requirements Engineering & Feasibility | Oct 13, 18:55 – 20:30 | 1.5h | Complete, validated `docs/` specifications |
| **Phase 2** | System Architecture & Interface Design | Oct 13, 20:30 – 22:30 | 2.0h | Architecture doc, module schemas, mock interfaces |
| **Phase 3** | Detailed Design & Data Modeling | Oct 13, 22:30 – 00:30 | 2.0h | Pydantic models, SQLite schema, BKT state transitions |
| **Phase 4** | Incremental Core Implementation | Oct 14, 00:30 – 10:30 | 10.0h | Ingestion, Grounding, BKT, Assessments, Streamlit UI |
| **Phase 5** | Verification & Unit/Integration Testing | Oct 14, 10:30 – 14:00 | 3.5h | Automated Pytest suite passing with 100% assertions |
| **Phase 6** | System Evaluation & Benchmark Runs | Oct 14, 14:00 – 17:30 | 3.5h | 20+ test evaluations, 3 learner profile simulations |
| **Phase 7** | Deployment, Security & Polish | Oct 14, 17:30 – 19:30 | 2.0h | Env config, secret scrub, clean install verification |
| **Phase 8** | Documentation, Walkthrough & Submission | Oct 14, 19:30 – 22:30 | 3.0h | README, architecture diagrams, demo video script |
| **Buffer** | Submission Verification & Contingency | Oct 14, 22:30 – 23:45 | 1.25h | Final smoke test and submission upload |

---

### 1.2 Multimodal Extraction Feasibility: Genuine vs. Approximated vs. Unsupported

We do not pretend that transcript extraction alone constitutes full multimodal understanding. We explicitly declare the technical boundaries of each media type:

```
+---------------------------------------------------------------------------------------------------------+
|                                  MULTIMODAL EXTRACTION CAPABILITY MATRIX                                |
+------------------+--------------------------------+----------------------------+------------------------+
| Media Modality   | Genuinely Extracted            | Approximated / Simplified  | Strictly Unsupported   |
+------------------+--------------------------------+----------------------------+------------------------+
| PDF Textbooks    | - Raw page text via PyMuPDF    | - Multi-column reading     | - Complex handwritten  |
|                  | - Section headings & font size |   order approximated via   |   marginalia without   |
|                  | - Embedded image extraction    |   spatial coordinate sort  |   custom fine-tuning   |
|                  | - Page number metadata         | - Footnote stripping       |                        |
+------------------+--------------------------------+----------------------------+------------------------+
| Presentation     | - Slide titles & text shapes   | - Visual layout hierarchy  | - Embedded video       |
| Decks (.pptx)    | - Slide numbering              |   approximated by shape    |   playback frames      |
|                  | - Speaker notes (`is_notes`)   |   bounding box order       | - Dynamic animations   |
|                  | - Slide-extracted images       |                            |                        |
+------------------+--------------------------------+----------------------------+------------------------+
| Lecture Videos   | - Precise audio transcription  | - Video slide change       | - Unsynchronized video |
|                  |   with millisecond timestamps  |   detection approximated   |   lacking audio or     |
|                  |   (via .vtt/.srt or API)       |   by timestamp-chunk       |   transcripts when     |
|                  | - Segment start/end ranges     |   grouping                 |   ffmpeg is absent     |
+------------------+--------------------------------+----------------------------+------------------------+
| Diagrams and     | - Image extraction to disk     | - Semantic caption         | - 3D scene geometry    |
| Figures          | - Visual captioning via Vision |   approximated using       | - Micro-text OCR in    |
|                  |   model (or OCR text)          |   vision prompt + OCR      |   low-resolution scans |
|                  | - Source page provenance       |                            |                        |
+------------------+--------------------------------+----------------------------+------------------------+
```

#### Crucial Environment Finding: System FFmpeg Absence
- **Discovery**: Inspection of the host Windows 11 environment confirmed that `ffmpeg` is **not installed** on the system PATH.
- **Impact**: Extracting raw audio tracks directly from heavy `.mp4` or `.mkv` video files locally via Whisper CLI or PyDub fails without an FFmpeg binary.
- **Architectural Solution**:
  1. We provide native support for **companion transcript files** (`.vtt`, `.srt`, or structured `.json` sidecars) alongside video files.
  2. For video processing in Python, we integrate `imageio-ffmpeg` or standard transcript streaming when available.
  3. Sample course materials will include verified timestamped transcript sidecars for demonstration, ensuring 100% test reliability without relying on missing OS binaries.

---

### 1.3 Model Access Feasibility: Coding Assistant vs. Application Runtime

An essential architectural distinction exists between the development assistant and the application runtime:

| Dimension | Development Environment (Antigravity IDE) | Application Runtime (Your Tutor App) |
| :--- | :--- | :--- |
| **Context** | IDE Coding Assistant | Python Application process run by student |
| **Model** | Gemini 3.8 Flash (High) | Configurable LLM Provider via Python API |
| **Access Key**| Integrated via IDE session token | Driven by host environment variables |
| **Current State**| Active and responsive | `GEMINI_API_KEY`: **Not set**<br>`GOOGLE_API_KEY`: **Not set**<br>`OPENAI_API_KEY`: **Not set** |

#### Pluggable Runtime Architecture & Deterministic Fallback
To ensure that **Your Tutor** is never held hostage by missing API keys, rate limits, network outages, or expired quotas, we establish a formal `BaseModelProvider` interface with three concrete implementations:

1. **`GeminiProvider`**: Uses the official Google GenAI / Gemini API (e.g., `gemini-2.5-flash` or `gemini-1.5-flash`) when `GEMINI_API_KEY` is present.
2. **`OpenAICompatibleProvider`**: Uses any OpenAI-compatible endpoint (LiteLLM, Local Ollama, Groq, or OpenAI) when configured.
3. **`MockDeterministicProvider` (Zero-Key Offline Fallback)**:
   - A fully functional, high-fidelity deterministic provider that uses the ingested course text, BM25 retrieval, and template synthesis to generate grounded answers, citations, and evaluation outputs.
   - **Crucial Rule**: The mock provider will **never** falsely represent precomputed responses as live LLM calls. It displays an explicit status badge: `[Provider: Offline Deterministic Engine]` so judges and users have complete transparency.
   - This guarantees that automated tests, benchmarks, and interactive demos run with 100% reliability even if disconnected from the internet.

---

### 1.4 Bayesian Knowledge Tracing (BKT) Feasibility & Pedagogical Integrity

The prompt mandates standard **Corbett & Anderson (1994) BKT**, explicitly rejecting simplistic heuristics mislabeled as BKT.

#### Mathematical Equations
For each concept node $k$, the state is defined by four probabilities:
- $P(L_0)$: Initial prior mastery probability before practice.
- $P(T)$: Probability that an unlearned skill transitions to learned on a practice opportunity.
- $P(G)$: Probability that a student who has not mastered the skill guesses correctly.
- $P(S)$: Probability that a student who has mastered the skill slips (makes an unforced error).

Given observation $obs_t \in \{0, 1\}$ (where 1 is correct, 0 is incorrect):

**Step 1: Compute Posterior Mastery Given Observation**
$$P(L_t \mid obs_t = 1) = \frac{P(L_{t-1}) \cdot (1 - P(S))}{P(L_{t-1}) \cdot (1 - P(S)) + (1 - P(L_{t-1})) \cdot P(G)}$$

$$P(L_t \mid obs_t = 0) = \frac{P(L_{t-1}) \cdot P(S)}{P(L_{t-1}) \cdot P(S) + (1 - P(L_{t-1})) \cdot (1 - P(G))}$$

**Step 2: Account for Learning Transition (Prior for Next Step)**
$$P(L_{t+1}) = P(L_t \mid obs_t) + (1 - P(L_t \mid obs_t)) \cdot P(T)$$

#### Pedagogical Bounds & Assumptions
1. **Parameter Constraints**: Degeneracy occurs if $P(G) + P(S) \ge 1.0$ (learning signal inverts or disappears). Our model enforces:
   $$0.05 \le P(G) \le 0.35, \quad 0.05 \le P(S) \le 0.25, \quad 0.05 \le P(T) \le 0.40$$
2. **Pedagogical Disclaimer**: We document that BKT estimates are statistical approximations of mastery over binary practice items, not ontological measurements of human intelligence. Mastery thresholds ($\tau = 0.80$) are operational criteria for adaptive routing.

---

## 2. Risk Matrix & Mitigation Strategies

| Risk ID | Risk Description | Severity | Probability | Impact | Concrete Mitigation Strategy |
| :---: | :--- | :---: | :---: | :---: | :--- |
| **RSK-01** | **Missing API Keys / Quota Exhaustion at Runtime** | High | High | App crashes or fails during demo | Implement `MockDeterministicProvider` with offline BM25 and template grounding. App runs completely offline if no keys are provided. |
| **RSK-02** | **No System FFmpeg on Windows 11** | Medium | High | Video audio extraction fails | Support video transcript sidecars (`.vtt`, `.srt`, `.json`) with timestamp indexing. Provide sample pre-indexed video transcripts in repository. |
| **RSK-03** | **Hallucinated Citations in Tutor Responses** | High | Medium | Violates 20% Grounding rubric | Implement deterministic citation verification: parse every `[Source: ...]` tag, assert that the cited text exists in retrieved chunks, flag ungrounded claims. |
| **RSK-04** | **BKT Math Divergence or Degenerate Parameters** | High | Low | Flawed mastery updates | Write rigorous unit tests with known analytical values for $P(L_t)$. Enforce mathematical assertion bounds on $P(G)$, $P(S)$, and $P(T)$. |
| **RSK-05** | **Evaluation Metric Fabrication / Non-Reproducibility** | High | Low | Disqualification / Judge penalty | Use deterministic test seeds and static benchmark files (`eval/benchmark_dataset.json`). Store raw output logs and publish reproducibility scripts. |
| **RSK-06** | **Scope Creep / Architecture Over-Engineering** | High | Medium | Incomplete project at deadline | Strictly ban Next.js, FastAPI, Docker, and distributed vector DBs. Use Streamlit + SQLite + Pure Python. |
| **RSK-07** | **Secret / API Key Leakage in Version Control** | Critical| Low | Security breach | Use `.gitignore` containing `.env`, `*.key`, `data/secrets/`. Implement automated pre-commit scanning test. |

---

## 3. Empirical Environment Validation Results

Prior to proceeding with core implementation, direct dependency checks were executed against the host Windows 11 / Python 3.13 environment. The findings are recorded below:

| Package / Tool | Version / Status | Test Performed | Finding & Verdict |
| :--- | :---: | :--- | :--- |
| **Python** | `3.13.7` | `python --version` | Verified operational on Windows 11 64-bit. |
| **Streamlit** | `1.59.2` | `import streamlit` | Verified installed and functional. |
| **SQLite3** | Built-in | `import sqlite3` | Verified operational; WAL mode supported. |
| **NetworkX** | `3.6.1` | `import networkx` | Verified operational for DAG cycle validation and prerequisite traversal. |
| **pypdf** | `6.14.2` | `import pypdf` | Verified installed; baseline PDF parser ready. |
| **PyMuPDF (`fitz`)**| `1.28.2` (Available) | `pip install --dry-run pymupdf` | Resolves cleanly to `pymupdf-1.28.2-cp310-abi3-win_amd64.whl`. Zero C++ compilation hurdles on Windows 11. |
| **python-pptx** | `1.0.2` (Available) | `pip install --dry-run python-pptx` | Resolves cleanly to pure-Python wheel with `xlsxwriter`. Ready for slide extraction. |
| **Google GenAI SDK**| Modern `google.genai` | `from google import genai` | Modern `google-genai` SDK is already installed and imports cleanly. Deprecated `google.generativeai` avoided. Client initializable. |
| **ChromaDB** | `1.5.9` | `import chromadb` | Verified installed and operational. |
| **NumPy & Pandas** | `2.5.0` / `2.3.3` | `import numpy, pandas` | Verified operational for BKT vector math and data analysis. |
| **Pytest** | `9.1.1` | `import pytest` | Verified operational for test suite. |
| **System FFmpeg** | **Missing** | `ffmpeg -version` | **Not on PATH**. Video audio extraction requires transcript sidecars (`.vtt`, `.srt`, `.json`) as designed. |

### Validation Gate Sign-Off
- **Zero Blocker Dependencies**: All required packages are either already installed or resolve cleanly to official Windows x64 binary wheels.
- **Model SDK Ready**: `google.genai` SDK is present and functional; runtime provider abstraction allows graceful offline fallback when no API key is supplied.
- **FFmpeg Workaround Verified**: Transcript sidecar ingestion design completely bypasses the missing FFmpeg binary.

