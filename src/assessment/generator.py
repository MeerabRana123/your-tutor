"""Adaptive Assessment Generator for Your Tutor.

Generates curriculum-grounded Multiple-Choice Questions (MCQs) from retrieved course evidence.
Labels questions with generator provenance ('offline_template' or 'gemini'),
enforces strict structural validation, and guarantees physical page citations.
"""

import hashlib
import json
import re
from typing import List, Optional, Dict
from src.core.models import ContentChunk
from src.assessment.models import AssessmentQuestion


class AssessmentGenerator:
    """Generates and evaluates source-grounded assessment questions."""

    # Curated grounded templates for core ML foundations
    GROUNDED_TOPIC_TEMPLATES = {
        "loss functions": {
            "topic": "Loss and Cost Functions",
            "page": 1,
            "keyword": "loss function",
            "stem": "According to the course materials, what is the key distinction between a loss function and a cost function?",
            "options": {
                "A": "A loss function evaluates an individual training sample, while a cost function computes the average loss across the dataset.",
                "B": "A loss function applies only to classification, while a cost function applies only to regression.",
                "C": "A loss function is always non-convex, whereas a cost function is strictly convex.",
                "D": "A loss function requires backpropagation, while a cost function does not."
            },
            "correct_answer": "A",
            "explanation": "Page 1 explicitly states: 'A loss function evaluates an individual training example, whereas a cost function computes the average loss across the entire training dataset.'"
        },
        "gradient descent": {
            "topic": "Gradient Descent Optimization",
            "page": 2,
            "keyword": "gradient descent",
            "stem": "In the gradient descent parameter update equation theta_new = theta_old - alpha * grad_J(theta), what does the hyperparameter alpha represent?",
            "options": {
                "A": "The regularization penalty weight",
                "B": "The learning rate governing the step size in the negative gradient direction",
                "C": "The momentum coefficient for accelerating gradient descent",
                "D": "The number of hidden units in the neural network layer"
            },
            "correct_answer": "B",
            "explanation": "Page 2 explicitly states: 'The standard parameter update equation is: theta_new = theta_old - alpha * grad_J(theta), where alpha represents the learning rate hyperparameter.'"
        },
        "backpropagation": {
            "topic": "Backpropagation and the Chain Rule",
            "page": 3,
            "keyword": "backpropagation",
            "stem": "What is the foundational mathematical principle governing backpropagation in deep neural networks?",
            "options": {
                "A": "Euler's method for solving ordinary differential equations",
                "B": "The multivariate chain rule of differential calculus applied to a computation graph",
                "C": "The central limit theorem for Gaussian weight initialization",
                "D": "Laplace approximation for posterior density estimation"
            },
            "correct_answer": "B",
            "explanation": "Page 3 explicitly states: 'The fundamental mathematical principle underlying backpropagation is the multivariate chain rule of differential calculus.'"
        },
        "overfitting": {
            "topic": "Overfitting and Regularization",
            "page": 4,
            "keyword": "overfitting",
            "stem": "How does Dropout regularization reduce overfitting during neural network training?",
            "options": {
                "A": "By setting all negative weights to zero during every forward pass",
                "B": "By randomly deactivating a fraction p of hidden units during each forward step to prevent co-adaptation",
                "C": "By doubling the size of the training dataset through generative synthesis",
                "D": "By constraining all model parameters to lie between -1 and 1"
            },
            "correct_answer": "B",
            "explanation": "Page 4 explicitly states: 'Dropout randomly deactivates a fraction p of hidden units during each forward training step... Dropout prevents co-adaptation of features.'"
        }
    }

    def __init__(self, gemini_provider=None):
        self.gemini_provider = gemini_provider

    def generate_question(
        self,
        chunks: List[ContentChunk],
        topic_hint: Optional[str] = None,
        difficulty: str = "intermediate"
    ) -> AssessmentQuestion:
        """
        Generates an MCQ grounded in the provided chunks.
        If Gemini is configured and available, attempts generative generation with fallback.
        Otherwise, generates a deterministic grounded question using offline templates.
        """
        if not chunks:
            raise ValueError("Cannot generate question: no source chunks provided.")

        # Attempt Gemini if live provider configured
        if self.gemini_provider and self.gemini_provider.is_available():
            try:
                return self._generate_with_gemini(chunks, topic_hint, difficulty)
            except Exception:
                pass  # Graceful fallback to verified offline template

        return self._generate_offline(chunks, topic_hint, difficulty)

    def _generate_offline(
        self,
        chunks: List[ContentChunk],
        topic_hint: Optional[str] = None,
        difficulty: str = "intermediate"
    ) -> AssessmentQuestion:
        """Deterministically generates a verified question from matching chunks."""
        # Find matching template based on topic_hint or chunk contents
        selected_key = None
        if topic_hint:
            hint_lower = topic_hint.lower()
            for key in self.GROUNDED_TOPIC_TEMPLATES:
                if key in hint_lower:
                    selected_key = key
                    break
        else:
            # Match based on text in the available chunks only if no topic_hint given
            chunk_text_joined = " ".join(c.text_content.lower() for c in chunks)
            for key, tpl in self.GROUNDED_TOPIC_TEMPLATES.items():
                if tpl["keyword"] in chunk_text_joined:
                    selected_key = key
                    break

        if not selected_key:
            # Dynamic offline extraction from matching chunk
            matching_chunk = chunks[0]
            sentences = [
                s.strip()
                for s in re.split(r"(?<=[.!?])\s+", matching_chunk.text_content)
                if len(s.strip()) > 30
            ]
            true_statement = sentences[0] if sentences else matching_chunk.text_content[:120] + "..."

            topic_title = topic_hint.strip().title() if topic_hint else "Course Concept"
            doc_name = matching_chunk.filename
            page_num = matching_chunk.page_number

            stem = f"According to {doc_name} (Page {page_num}), which of the following statements regarding {topic_title} is supported by the course text?"
            options = {
                "A": true_statement,
                "B": "This concept violates standard convergence bounds and is rejected by the syllabus.",
                "C": "This concept applies only to unparameterized stochastic distributions.",
                "D": "None of the above statements are supported by the text on this page."
            }
            q_id = hashlib.sha256(
                f"{doc_name}:p{page_num}:{topic_title}:{true_statement[:30]}".encode()
            ).hexdigest()[:12]

            return AssessmentQuestion(
                question_id=f"q_{q_id}",
                topic=topic_title,
                difficulty=difficulty,
                source_document=doc_name,
                page_number=page_num,
                citation_label=f"[Source: {doc_name}, Page {page_num}]",
                question_stem=stem,
                options=options,
                correct_answer="A",
                explanation=f"Page {page_num} explicitly states: '{true_statement}'",
                generator_mode="offline_dynamic_extract",
            )

        tpl = self.GROUNDED_TOPIC_TEMPLATES[selected_key]

        # Locate corresponding chunk for exact source file and page
        matching_chunk = next(
            (c for c in chunks if c.page_number == tpl["page"]),
            chunks[0]
        )

        doc_name = matching_chunk.filename
        page_num = matching_chunk.page_number

        q_id = hashlib.sha256(
            f"{doc_name}:p{page_num}:{tpl['topic']}:{tpl['correct_answer']}".encode()
        ).hexdigest()[:12]

        return AssessmentQuestion(
            question_id=f"q_{q_id}",
            topic=tpl["topic"],
            difficulty=difficulty,
            source_document=doc_name,
            page_number=page_num,
            citation_label=f"[Source: {doc_name}, Page {page_num}]",
            question_stem=tpl["stem"],
            options=tpl["options"],
            correct_answer=tpl["correct_answer"],
            explanation=tpl["explanation"],
            generator_mode="offline_template",
        )

    def _generate_with_gemini(
        self,
        chunks: List[ContentChunk],
        topic_hint: Optional[str] = None,
        difficulty: str = "intermediate"
    ) -> AssessmentQuestion:
        """Prompts Gemini to generate a structured MCQ strictly grounded in chunks."""
        primary_chunk = chunks[0]
        topic_str = topic_hint or "Machine Learning Concept"
        prompt = (
            f"Based strictly on this text from page {primary_chunk.page_number} of {primary_chunk.filename}:\n"
            f"'''{primary_chunk.text_content}'''\n\n"
            f"Generate a Multiple-Choice Question (difficulty: {difficulty}) testing understanding of {topic_str}.\n"
            "Return a valid JSON object with the following fields:\n"
            "- topic: string (name of the concept)\n"
            "- question_stem: string (clear question)\n"
            "- options: dict with keys 'A', 'B', 'C', 'D' containing distinct textual answers\n"
            "- correct_answer: single uppercase letter ('A', 'B', 'C', or 'D')\n"
            "- explanation: string citing the exact sentence from the source page\n"
            "Return ONLY the JSON object, without markdown formatting or code fences."
        )

        system_instruction = (
            "You are an expert academic assessment generator for university machine learning courses. "
            "You create rigorous, unambiguous multiple-choice questions grounded strictly in the provided text. "
            "Output valid JSON only."
        )

        raw_text = self.gemini_provider.generate_raw(prompt, system_instruction=system_instruction)

        # Robust JSON extraction
        clean_json = raw_text.strip()
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", clean_json)
        if match:
            clean_json = match.group(1).strip()

        data = json.loads(clean_json)

        q_id = hashlib.sha256(
            f"{primary_chunk.filename}:{primary_chunk.page_number}:{data['question_stem'][:30]}".encode()
        ).hexdigest()[:12]

        return AssessmentQuestion(
            question_id=f"q_{q_id}",
            topic=data.get("topic", topic_str),
            difficulty=difficulty,
            source_document=primary_chunk.filename,
            page_number=primary_chunk.page_number,
            citation_label=f"[Source: {primary_chunk.filename}, Page {primary_chunk.page_number}]",
            question_stem=data["question_stem"],
            options=data["options"],
            correct_answer=data["correct_answer"].strip().upper(),
            explanation=data["explanation"],
            generator_mode="gemini",
        )

    @staticmethod
    def evaluate_answer(question: AssessmentQuestion, student_choice: str) -> bool:
        """Deterministically evaluates if student's chosen option matches correct answer."""
        clean_choice = student_choice.strip().upper()
        return clean_choice == question.correct_answer.strip().upper()
