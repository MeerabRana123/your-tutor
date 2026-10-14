# YOUR TUTOR — MODULE INTERFACES SPECIFICATION
**Multimodal AI Hackathon 2026 — Track D: Personalized Tutoring & Adaptive Learning**

---

## 1. Overview & Interface Philosophy

To ensure modularity and high testability without overengineering, **Your Tutor** defines clean, type-hinted abstract base classes (`abc.ABC`) and protocols for each primary subsystem.

Dependencies flow downward: UI components invoke subsystem interfaces; subsystem implementations rely on domain models and SQLite persistence.

```
+-----------------------------------------------------------------------------------------+
|                                    INTERFACE SUMMARY                                    |
+--------------------------+------------------------------+-------------------------------+
| Interface Name           | Core Responsibility          | Implementations               |
+--------------------------+------------------------------+-------------------------------+
| BaseIngestor             | Ingests raw files to chunks  | PDFIngestor, SlideIngestor,   |
|                          |                              | TranscriptIngestor            |
| BaseRetriever            | Hybrid search for chunks     | HybridBM25DenseRetriever      |
| BaseModelProvider        | Decoupled LLM generation     | GeminiProvider, MockProvider  |
| BaseGroundingVerifier    | Audits claims and citations  | DeterministicCitationVerifier |
| BaseAssessmentEngine     | Question gen & answer check  | AdaptiveAssessmentEngine      |
| BaseBKTEngine            | Closed-form BKT mathematics  | CorbettAndersonBKTEngine      |
| BasePrerequisiteGraph    | DAG traversal & remediation  | NetworkXPrerequisiteGraph     |
| BaseEvaluationRunner     | Executes benchmark test sets | ReproducibleBenchmarkRunner   |
+--------------------------+------------------------------+-------------------------------+
```

---

## 2. Ingestion Interfaces (`src/ingestion/`)

```python
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Tuple
from src.core.models import SourceDocument, ContentChunk, VisualAsset

class BaseIngestor(ABC):
    """Abstract interface for ingesting course materials into normalized chunks."""

    @abstractmethod
    def ingest_file(
        self, file_path: Path, document_id: str
    ) -> Tuple[SourceDocument, List[ContentChunk], List[VisualAsset]]:
        """
        Parses a file from disk and returns:
        1. A SourceDocument metadata record
        2. A list of ContentChunks with explicit physical provenance
        3. A list of extracted VisualAssets (figures/diagrams) with source coordinates
        """
        pass

class PDFIngestor(BaseIngestor):
    """Ingests PDF textbooks and lecture notes with page-level bounding boxes."""
    pass

class SlideIngestor(BaseIngestor):
    """Ingests PowerPoint presentations (.pptx) with slide numbers, titles, and notes."""
    pass

class TranscriptIngestor(BaseIngestor):
    """Ingests timestamped subtitle/transcript sidecars (.vtt, .srt, .json)."""
    pass
```

---

## 3. Retrieval & Grounding Interfaces (`src/retrieval/` & `src/grounding/`)

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from src.core.models import ContentChunk

class RetrievalResult:
    def __init__(self, chunk: ContentChunk, score: float, rank: int):
        self.chunk = chunk
        self.score = score
        self.rank = rank

class BaseRetriever(ABC):
    """Abstract interface for indexing and searching course content chunks."""

    @abstractmethod
    def index_chunks(self, chunks: List[ContentChunk]) -> None:
        """Indexes a batch of content chunks into lexical and vector indices."""
        pass

    @abstractmethod
    def search(
        self, query: str, top_k: int = 4, concept_filter: Optional[str] = None
    ) -> List[RetrievalResult]:
        """
        Retrieves the top-k most relevant chunks for a user query.
        Returns empty list if no chunks meet minimum similarity threshold.
        """
        pass

class BaseGroundingVerifier(ABC):
    """Audits generated answers against retrieved source chunks."""

    @abstractmethod
    def verify_response(
        self,
        query: str,
        generated_answer: str,
        retrieved_chunks: List[ContentChunk]
    ) -> Dict[str, Any]:
        """
        Audits answer text for:
        1. Presence of well-formed citations: [Source: <doc>, Page/Slide <N>]
        2. Citation validity (does the cited chunk exist in retrieved_chunks?)
        3. Factual entailment (does the chunk text substantiate the claimed fact?)
        Returns a dictionary with validation status:
        {
            "is_valid": bool,
            "citations_found": List[str],
            "invalid_citations": List[str],
            "unsupported_claims": List[str],
            "refusal_detected": bool
        }
        """
        pass
```

---

## 4. Runtime Model Provider Interface (`src/providers/`)

```python
from abc import ABC, abstractmethod
from typing import List, Optional
from src.core.models import ContentChunk, AssessmentQuestion

class ProviderResponse:
    def __init__(
        self,
        text: str,
        provider_name: str,
        is_fallback: bool,
        raw_metadata: Optional[dict] = None
    ):
        self.text = text
        self.provider_name = provider_name
        self.is_fallback = is_fallback
        self.raw_metadata = raw_metadata or {}

class BaseModelProvider(ABC):
    """Pluggable runtime interface for LLM synthesis and question generation."""

    @abstractmethod
    def generate_grounded_answer(
        self, query: str, context_chunks: List[ContentChunk]
    ) -> ProviderResponse:
        """
        Synthesizes a response strictly grounded in context_chunks.
        Must refuse if context_chunks is empty or insufficient.
        """
        pass

    @abstractmethod
    def generate_assessment_question(
        self,
        concept_id: str,
        concept_name: str,
        difficulty: str,
        context_chunks: List[ContentChunk]
    ) -> AssessmentQuestion:
        """Generates a multiple-choice or short-answer question tied to context chunks."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Returns True if the provider is fully configured with credentials and network access."""
        pass
```

---

## 5. Bayesian Knowledge Tracing & Prerequisite Graph (`src/bkt/`)

```python
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from src.core.models import ConceptMasteryState, ConceptNode

class BaseBKTEngine(ABC):
    """Standard Corbett & Anderson (1994) BKT mathematical update engine."""

    @abstractmethod
    def update_mastery(
        self,
        prior_p_l: float,
        is_correct: bool,
        p_t: float,
        p_g: float,
        p_s: float
    ) -> Tuple[float, float]:
        """
        Calculates:
        1. Posterior mastery immediately following observation: P(L_t | obs)
        2. Next step prior mastery after learning opportunity: P(L_{t+1})
        Returns: (posterior_p_l, next_prior_p_l)
        """
        pass

    @abstractmethod
    def get_or_initialize_state(
        self, student_id: str, concept: ConceptNode
    ) -> ConceptMasteryState:
        """Loads current mastery from database or initializes using concept priors."""
        pass

class BasePrerequisiteGraph(ABC):
    """Curriculum DAG traversal and remediation routing."""

    @abstractmethod
    def get_prerequisites(self, concept_id: str) -> List[str]:
        """Returns list of direct prerequisite concept IDs."""
        pass

    @abstractmethod
    def get_unmastered_ancestors(
        self, student_id: str, concept_id: str, threshold: float = 0.60
    ) -> List[str]:
        """
        Traverses prerequisite DAG upstream. Returns prerequisite concept IDs
        where student's mastery P(L) is strictly below threshold.
        """
        pass

    @abstractmethod
    def validate_dag(self) -> bool:
        """Returns True if curriculum graph is a valid Directed Acyclic Graph with zero cycles."""
        pass
```

---

## 6. Assessment Engine Interface (`src/assessment/`)

```python
from abc import ABC, abstractmethod
from typing import Tuple, Optional
from src.core.models import AssessmentQuestion

class BaseAssessmentEngine(ABC):
    """Generates questions, checks answers, and tracks question history."""

    @abstractmethod
    def get_next_question(
        self, student_id: str, target_concept_id: Optional[str] = None
    ) -> AssessmentQuestion:
        """
        Selects or generates the next question for a student.
        Guarantees that the question has not been answered in the active session.
        """
        pass

    @abstractmethod
    def evaluate_answer(
        self, question: AssessmentQuestion, student_submission: str
    ) -> Tuple[bool, str]:
        """
        Deterministically evaluates student response against answer key.
        Returns: (is_correct, explanatory_feedback_with_citations)
        """
        pass
```

---

## 7. Evaluation & Benchmark Interface (`src/eval/`)

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from src.core.models import EvaluationItem, EvaluationResult

class BaseEvaluationRunner(ABC):
    """Executes evaluation benchmarks and exports reproducible reports."""

    @abstractmethod
    def run_benchmark(
        self, benchmark_file_path: str, output_report_path: str
    ) -> Dict[str, float]:
        """
        Executes benchmark test cases and writes evaluation results.
        Returns summary metrics:
        {
            "context_precision": float,
            "context_recall": float,
            "faithfulness": float,
            "citation_accuracy": float,
            "out_of_domain_refusal_rate": float
        }
        """
        pass

    @abstractmethod
    def simulate_learner_profile(
        self,
        profile_name: str,
        true_latent_p_l0: float,
        p_guess: float,
        p_slip: float,
        steps: int = 15
    ) -> List[Dict[str, Any]]:
        """
        Simulates student responses over multi-trial trajectory and tracks
        estimated BKT mastery curve vs. true underlying skill.
        """
        pass
```
