"""Data models for Adaptive Assessments and Bayesian Knowledge Tracing."""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field, model_validator


class AssessmentOption(BaseModel):
    """An option choice in a Multiple-Choice Question."""
    key: str = Field(description="Option identifier: A, B, C, or D")
    text: str = Field(description="Option text")


class AssessmentQuestion(BaseModel):
    """A course-grounded Multiple-Choice Question."""
    question_id: str = Field(description="Deterministic unique question identifier")
    topic: str = Field(description="Curriculum topic e.g., 'Backpropagation', 'Gradient Descent'")
    difficulty: str = Field(default="intermediate", description="'novice', 'intermediate', or 'advanced'")
    source_document: str = Field(description="Originating PDF filename")
    page_number: int = Field(ge=1, description="Physical source page number")
    citation_label: str = Field(description="Formatted citation e.g., [Source: file.pdf, Page 3]")
    question_stem: str = Field(description="The question prompt")
    options: Dict[str, str] = Field(description="Mapping of keys ('A','B','C','D') to option text")
    correct_answer: str = Field(description="The correct key e.g., 'A', 'B', 'C', or 'D'")
    explanation: str = Field(description="Grounded explanation citing course evidence")
    generator_mode: str = Field(description="Generator provenance: 'offline_template' or 'gemini'")

    @model_validator(mode="after")
    def validate_options_and_key(self) -> "AssessmentQuestion":
        if not self.options or len(self.options) < 2:
            raise ValueError("AssessmentQuestion must have at least 2 options.")
        if self.correct_answer not in self.options:
            raise ValueError(
                f"Invalid answer key '{self.correct_answer}': must be one of options {list(self.options.keys())}"
            )
        if not self.source_document.strip():
            raise ValueError("source_document cannot be empty.")
        if self.page_number < 1:
            raise ValueError("page_number must be >= 1.")
        return self


class AssessmentResult(BaseModel):
    """Result of an evaluated student assessment submission."""
    question_id: str
    topic: str
    student_choice: str
    is_correct: bool
    correct_answer: str
    explanation: str
    citation_label: str
    prior_mastery: float
    posterior_mastery: float
    mastery_delta: float
    revision_recommendation: Optional[str] = None
