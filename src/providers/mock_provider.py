"""Offline Deterministic Mock Provider for Your Tutor.

Provides deterministic, reproducible, extractive responses with explicit citations
for automated testing, continuous integration, and zero-API-key demonstrations.
Does NOT fabricate knowledge or claim to be a generative LLM.
"""

import re
from typing import List
from src.core.models import EvidenceItem, ProviderResponse
from src.providers.base import BaseModelProvider


class MockDeterministicProvider(BaseModelProvider):
    """Offline provider that synthesizes extractive responses directly from retrieved evidence."""

    INSUFFICIENT_EVIDENCE_MSG = "I could not find sufficient evidence in the uploaded material to answer this question."

    @property
    def provider_name(self) -> str:
        return "offline_mock"

    def is_available(self) -> bool:
        return True

    def generate_grounded_answer(
        self, query: str, evidence: List[EvidenceItem]
    ) -> ProviderResponse:
        """
        Extracts salient statements from the top evidence chunks and formats with citations.
        Returns insufficient evidence message if evidence list is empty.
        """
        if not evidence:
            return ProviderResponse(
                text=self.INSUFFICIENT_EVIDENCE_MSG,
                provider_name=self.provider_name,
                mode="offline_extract",
                is_refusal=True,
                raw_metadata={"evidence_count": 0},
            )

        # Select sentences from top evidence items that have token overlap with query
        query_words = set(re.findall(r"\b[a-zA-Z0-9_-]+\b", query.lower()))
        response_paragraphs = []

        for item in evidence:
            sentences = re.split(r"(?<=[.!?])\s+", item.text_content)
            matching_sentences = []
            for s in sentences:
                s_words = set(re.findall(r"\b[a-zA-Z0-9_-]+\b", s.lower()))
                # If sentence shares words with query or is the lead sentence of the chunk
                if (query_words & s_words) or (len(matching_sentences) == 0 and len(s.strip()) > 20):
                    matching_sentences.append(s.strip())
                if len(matching_sentences) >= 2:
                    break

            if not matching_sentences:
                # Fall back to first 25 words of the chunk
                matching_sentences = [" ".join(item.text_content.split()[:25]) + "..."]

            chunk_summary = " ".join(matching_sentences)
            citation = f"[Source: {item.filename}, Page {item.page_number}]"
            response_paragraphs.append(f"{chunk_summary} {citation}")

        synthesis = "\n\n".join(response_paragraphs)
        full_text = (
            f"[Offline Extractive Mode]\n\n"
            f"Based on the uploaded course materials:\n\n{synthesis}"
        )

        return ProviderResponse(
            text=full_text,
            provider_name=self.provider_name,
            mode="offline_extract",
            is_refusal=False,
            raw_metadata={"evidence_count": len(evidence)},
        )
