"""Base Model Provider Interface for Your Tutor.

Defines the contract for generative and offline model providers.
"""

from abc import ABC, abstractmethod
from typing import List
from src.core.models import EvidenceItem, ProviderResponse


class BaseModelProvider(ABC):
    """Abstract interface decoupling tutor synthesis from specific model implementations."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name identifying the provider implementation."""
        pass

    @abstractmethod
    def generate_grounded_answer(
        self, query: str, evidence: List[EvidenceItem]
    ) -> ProviderResponse:
        """
        Generates an instructional answer strictly grounded in the provided evidence.
        Must handle empty or insufficient evidence by setting is_refusal=True.
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Returns True if the provider is active, authenticated, and ready."""
        pass
