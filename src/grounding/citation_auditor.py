"""Citation Auditor for Your Tutor.

Independently audits citations in generated responses against the set of
retrieved evidence items. Distinguishes citation location existence from
semantic text support, and ensures failed audits are never masked as verified.
"""

import re
from typing import List, Tuple, Set
from src.core.models import EvidenceItem, AuditResult


class CitationAuditor:
    """Audits tutor response citations against retrieved evidence."""

    # Matches patterns like [Source: filename.pdf, Page 3] or [Source: filename.pdf, Page 12]
    CITATION_PATTERN = re.compile(
        r"\[Source:\s*([^,\]]+),\s*Page\s*(\d+)\]", re.IGNORECASE
    )

    def audit_response(
        self,
        generated_text: str,
        retrieved_evidence: List[EvidenceItem],
        is_refusal: bool = False
    ) -> AuditResult:
        """
        Audits citations in generated_text against retrieved_evidence.
        If is_refusal is True, zero citations are expected and the audit passes cleanly.
        """
        # If response is a refusal, no citations are required
        if is_refusal:
            citations_found = self._extract_citations(generated_text)
            return AuditResult(
                is_valid=True,
                citations_found=[c[0] for c in citations_found],
                valid_citations=[],
                invalid_citations=[],
                unsupported_claims=[],
                details="Response is a legitimate refusal due to insufficient evidence.",
            )

        citations_found = self._extract_citations(generated_text)
        if not citations_found:
            return AuditResult(
                is_valid=False,
                citations_found=[],
                valid_citations=[],
                invalid_citations=[],
                unsupported_claims=[],
                details="Audit Failed: Factual response generated without required source citations.",
            )

        # Build index of valid (filename.lower(), page_number) in retrieved evidence
        valid_evidence_keys: Set[Tuple[str, int]] = {
            (item.filename.strip().lower(), item.page_number)
            for item in retrieved_evidence
        }

        valid_citations: List[str] = []
        invalid_citations: List[str] = []
        raw_found_strings: List[str] = []

        for full_tag, filename, page_str in citations_found:
            raw_found_strings.append(full_tag)
            page_num = int(page_str)
            key = (filename.strip().lower(), page_num)

            if key in valid_evidence_keys:
                valid_citations.append(full_tag)
            else:
                invalid_citations.append(full_tag)

        # Rule 8: Separate check for semantic textual support
        unsupported_claims = self._check_textual_support(
            generated_text, retrieved_evidence
        )

        # Audit verdict
        is_valid = len(invalid_citations) == 0 and len(valid_citations) > 0

        if not is_valid:
            details = (
                f"Audit Failed: Detected {len(invalid_citations)} unverified or fabricated citation(s): "
                f"{', '.join(invalid_citations)}"
            )
        elif unsupported_claims:
            details = (
                f"Audit Passed with Warnings: All {len(valid_citations)} citations point to retrieved pages, "
                f"but {len(unsupported_claims)} claim(s) showed low textual overlap with cited excerpts."
            )
        else:
            details = (
                f"Audit Passed: All {len(valid_citations)} citation(s) independently verified against "
                f"retrieved course evidence."
            )

        return AuditResult(
            is_valid=is_valid,
            citations_found=raw_found_strings,
            valid_citations=valid_citations,
            invalid_citations=invalid_citations,
            unsupported_claims=unsupported_claims,
            details=details,
        )

    def _extract_citations(self, text: str) -> List[Tuple[str, str, str]]:
        """
        Finds all citations in text.
        Returns list of tuples: (full_matched_tag, filename, page_number_str)
        """
        matches = []
        for m in self.CITATION_PATTERN.finditer(text):
            matches.append((m.group(0), m.group(1).strip(), m.group(2).strip()))
        return matches

    def _check_textual_support(
        self, generated_text: str, retrieved_evidence: List[EvidenceItem]
    ) -> List[str]:
        """
        Separately inspects whether cited sentences have token overlap with cited chunks.
        Keeps citation existence validation distinct from semantic faithfulness.
        """
        unsupported = []
        # Split into sentences containing citations
        sentences = re.split(r"(?<=[.!?])\s+", generated_text)
        for sentence in sentences:
            citation_match = self.CITATION_PATTERN.search(sentence)
            if not citation_match:
                continue

            cited_filename = citation_match.group(1).strip().lower()
            cited_page = int(citation_match.group(2).strip())

            # Find matching evidence items
            matching_items = [
                item for item in retrieved_evidence
                if item.filename.strip().lower() == cited_filename and item.page_number == cited_page
            ]
            if not matching_items:
                continue  # Handled by invalid_citations check

            # Tokenize claim sentence (excluding citation tag itself)
            clean_sentence = self.CITATION_PATTERN.sub("", sentence)
            sentence_words = set(re.findall(r"\b[a-zA-Z]{4,}\b", clean_sentence.lower()))
            if not sentence_words:
                continue

            # Compare against evidence tokens
            evidence_words = set()
            for itm in matching_items:
                evidence_words.update(re.findall(r"\b[a-zA-Z]{4,}\b", itm.text_content.lower()))

            overlap = sentence_words & evidence_words
            overlap_ratio = len(overlap) / len(sentence_words) if sentence_words else 1.0

            # If overlap is suspiciously low (< 25%), flag claim
            if overlap_ratio < 0.25:
                unsupported.append(sentence.strip())

        return unsupported
