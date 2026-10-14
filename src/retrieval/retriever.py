"""Lexical BM25 Retriever for Your Tutor.

Implements pure-Python Okapi BM25 ranking to retrieve page-attributed chunks
with transparent, reproducible relevance scoring without external vector DB dependencies.
"""

import math
import re
from typing import List, Dict, Optional, Set
from src.core.models import ContentChunk, EvidenceItem


class BM25Retriever:
    """Okapi BM25 lexical retriever with provenance preservation."""

    STOPWORDS: Set[str] = {
        "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
        "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being",
        "below", "between", "both", "but", "by", "can", "can't", "cannot", "could", "couldn't",
        "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down", "during",
        "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't",
        "have", "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here",
        "here's", "hers", "herself", "him", "himself", "his", "how", "how's", "i",
        "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it", "it's",
        "its", "itself", "let's", "me", "more", "most", "mustn't", "my", "myself",
        "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought",
        "our", "ours", "ourselves", "out", "over", "own", "same", "shan't", "she",
        "she'd", "she'll", "she's", "should", "shouldn't", "so", "some", "such",
        "than", "that", "that's", "the", "their", "theirs", "them", "themselves",
        "then", "there", "there's", "these", "they", "they'd", "they'll", "they're",
        "they've", "this", "those", "through", "to", "too", "under", "until", "up",
        "very", "was", "wasn't", "we", "we'd", "we'll", "we're", "we've", "were",
        "weren't", "what", "what's", "when", "when's", "where", "where's", "which",
        "while", "who", "who's", "whom", "why", "why's", "with", "won't", "would",
        "wouldn't", "you", "you'd", "you'll", "you're", "you've", "your", "yours",
        "yourself", "yourselves"
    }

    def __init__(self, k1: float = 1.5, b: float = 0.75, min_score_threshold: float = 1.0):
        self.k1 = k1
        self.b = b
        self.min_score_threshold = min_score_threshold
        self.chunks: List[ContentChunk] = []
        self.doc_lengths: List[int] = []
        self.avg_doc_length: float = 0.0
        self.doc_freqs: Dict[str, int] = {}
        self.term_freqs: List[Dict[str, int]] = []
        self.corpus_size: int = 0

    @classmethod
    def _tokenize(cls, text: str) -> List[str]:
        """Tokenizes text into lowercase alphanumeric words, filtering stopwords."""
        words = re.findall(r"\b[a-zA-Z0-9_-]+\b", text.lower())
        return [w for w in words if len(w) > 1 and w not in cls.STOPWORDS]

    def index_chunks(self, chunks: List[ContentChunk]) -> None:
        """Indexes a collection of ContentChunk objects."""
        self.chunks = list(chunks)
        self.corpus_size = len(self.chunks)
        self.doc_freqs.clear()
        self.term_freqs.clear()
        self.doc_lengths.clear()

        if self.corpus_size == 0:
            self.avg_doc_length = 0.0
            return

        total_length = 0
        for chunk in self.chunks:
            tokens = self._tokenize(chunk.text_content)
            doc_len = len(tokens)
            self.doc_lengths.append(doc_len)
            total_length += doc_len

            tf: Dict[str, int] = {}
            seen_tokens: Set[str] = set()
            for token in tokens:
                tf[token] = tf.get(token, 0) + 1
                if token not in seen_tokens:
                    self.doc_freqs[token] = self.doc_freqs.get(token, 0) + 1
                    seen_tokens.add(token)
            self.term_freqs.append(tf)

        self.avg_doc_length = total_length / self.corpus_size if self.corpus_size > 0 else 0.0

    def _idf(self, term: str) -> float:
        """Calculates standard Robertson-Spärck Jones IDF."""
        df = self.doc_freqs.get(term, 0)
        # Smooth IDF formulation
        return math.log(((self.corpus_size - df + 0.5) / (df + 0.5)) + 1.0)

    def search(
        self, query: str, top_k: int = 3, min_score: Optional[float] = None
    ) -> List[EvidenceItem]:
        """
        Ranks indexed chunks against query using Okapi BM25 scoring.
        Returns EvidenceItem objects ordered by score.
        Filters out results below min_score (defaults to self.min_score_threshold).
        """
        threshold = self.min_score_threshold if min_score is None else min_score
        query_tokens = self._tokenize(query)
        if not query_tokens or self.corpus_size == 0:
            return []

        scores: List[float] = [0.0] * self.corpus_size
        for token in query_tokens:
            if token not in self.doc_freqs:
                continue
            idf_val = self._idf(token)
            for doc_idx, tf_dict in enumerate(self.term_freqs):
                freq = tf_dict.get(token, 0)
                if freq == 0:
                    continue
                doc_len = self.doc_lengths[doc_idx]
                numerator = freq * (self.k1 + 1.0)
                denominator = freq + self.k1 * (1.0 - self.b + self.b * (doc_len / self.avg_doc_length))
                scores[doc_idx] += idf_val * (numerator / denominator)

        unique_query_tokens = set(query_tokens)
        query_token_count = len(unique_query_tokens)
        min_term_coverage = 0.40

        # Pair scores with chunk indexes and sort descending
        ranked_indices = sorted(
            range(self.corpus_size), key=lambda i: scores[i], reverse=True
        )

        results: List[EvidenceItem] = []
        rank = 1
        for idx in ranked_indices:
            score = scores[idx]
            if score < threshold:
                break  # Subsequent scores are lower

            # Guardrail: Check query term coverage to avoid spurious matches on generic words
            if query_token_count >= 3:
                matched_tokens = sum(1 for t in unique_query_tokens if self.term_freqs[idx].get(t, 0) > 0)
                coverage = matched_tokens / query_token_count
                if coverage < min_term_coverage:
                    continue

            chunk = self.chunks[idx]
            results.append(
                EvidenceItem(
                    chunk_id=chunk.chunk_id,
                    document_id=chunk.document_id,
                    filename=chunk.filename,
                    page_number=chunk.page_number,
                    text_content=chunk.text_content,
                    score=round(score, 4),
                    rank=rank,
                )
            )
            rank += 1
            if len(results) >= top_k:
                break

        return results
