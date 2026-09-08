"""
Keyword Extractor Service
=========================
TF-IDF based keyword and keyphrase extraction from meeting transcripts.
Supports single-document and multi-document corpus modes.
"""

from __future__ import annotations

import math
import re
import string
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple


@dataclass
class Keyword:
    term: str
    tf_idf: float
    frequency: int
    documents: int
    is_phrase: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "term": self.term,
            "tf_idf": round(self.tf_idf, 6),
            "frequency": self.frequency,
            "documents": self.documents,
            "is_phrase": self.is_phrase,
        }


@dataclass
class ExtractionResult:
    document_id: str
    keywords: List[Keyword] = field(default_factory=list)
    keyphrases: List[Keyword] = field(default_factory=list)
    total_words: int = 0
    unique_terms: int = 0
    top_keyword: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "document_id": self.document_id,
            "keywords": [k.to_dict() for k in self.keywords],
            "keyphrases": [k.to_dict() for k in self.keyphrases],
            "total_words": self.total_words,
            "unique_terms": self.unique_terms,
            "top_keyword": self.top_keyword,
        }


class KeywordExtractor:
    """
    TF-IDF keyword extractor with stopword filtering and bigram/trigram support.
    """

    _STOPWORDS: Set[str] = {
        "a", "an", "the", "is", "it", "in", "on", "at", "to", "for",
        "of", "and", "or", "but", "so", "yet", "nor", "not", "no",
        "we", "i", "you", "he", "she", "they", "them", "their", "our",
        "this", "that", "these", "those", "be", "was", "were", "are",
        "have", "has", "had", "do", "does", "did", "will", "would",
        "could", "should", "may", "might", "shall", "can", "just",
        "very", "also", "about", "with", "from", "by", "as", "if",
        "then", "than", "when", "where", "who", "which", "what", "how",
        "there", "here", "my", "your", "its", "up", "down", "out",
        "more", "some", "any", "all", "each", "every", "both", "few",
        "into", "through", "during", "before", "after", "above",
        "below", "between", "while", "because", "although", "since",
    }

    def __init__(
        self,
        max_keywords: int = 20,
        min_word_length: int = 3,
        include_phrases: bool = True,
        phrase_max_words: int = 3,
    ) -> None:
        self.max_keywords = max_keywords
        self.min_word_length = min_word_length
        self.include_phrases = include_phrases
        self.phrase_max_words = phrase_max_words
        self._corpus_idf: Dict[str, float] = {}
        self._corpus_docs: int = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def extract(self, text: str, document_id: str = "doc0") -> ExtractionResult:
        """Single-document keyword extraction."""
        tokens = self._tokenize(text)
        tf = self._compute_tf(tokens)
        idf = self._compute_idf_single(tf)
        tfidf = {term: tf[term] * idf[term] for term in tf}

        keywords = self._build_keywords(tfidf, tf)
        keyphrases = self._extract_phrases(text) if self.include_phrases else []

        result = ExtractionResult(
            document_id=document_id,
            keywords=keywords[: self.max_keywords],
            keyphrases=keyphrases[:10],
            total_words=len(tokens),
            unique_terms=len(tf),
            top_keyword=keywords[0].term if keywords else None,
        )
        return result

    def extract_batch(
        self, documents: Dict[str, str]
    ) -> Dict[str, ExtractionResult]:
        """Multi-document corpus extraction with shared IDF."""
        self._fit_corpus(list(documents.values()))
        results: Dict[str, ExtractionResult] = {}
        for doc_id, text in documents.items():
            tokens = self._tokenize(text)
            tf = self._compute_tf(tokens)
            tfidf = {
                term: tf[term] * self._corpus_idf.get(term, 1.0)
                for term in tf
            }
            keywords = self._build_keywords(tfidf, tf)
            phrases = self._extract_phrases(text) if self.include_phrases else []
            results[doc_id] = ExtractionResult(
                document_id=doc_id,
                keywords=keywords[: self.max_keywords],
                keyphrases=phrases[:10],
                total_words=len(tokens),
                unique_terms=len(tf),
                top_keyword=keywords[0].term if keywords else None,
            )
        return results

    def get_top_terms(self, text: str, n: int = 10) -> List[str]:
        """Quick top-N term extraction."""
        result = self.extract(text)
        return [kw.term for kw in result.keywords[:n]]

    # ------------------------------------------------------------------
    # Corpus fitting
    # ------------------------------------------------------------------

    def _fit_corpus(self, texts: List[str]) -> None:
        self._corpus_docs = len(texts)
        doc_freq: Dict[str, int] = defaultdict(int)
        for text in texts:
            tokens = set(self._tokenize(text))
            for token in tokens:
                doc_freq[token] += 1
        self._corpus_idf = {
            term: math.log((self._corpus_docs + 1) / (df + 1)) + 1
            for term, df in doc_freq.items()
        }

    # ------------------------------------------------------------------
    # TF / IDF
    # ------------------------------------------------------------------

    def _tokenize(self, text: str) -> List[str]:
        text = text.lower()
        text = re.sub(r"[^\w\s]", " ", text)
        tokens = text.split()
        return [
            t for t in tokens
            if t not in self._STOPWORDS
            and len(t) >= self.min_word_length
            and not t.isdigit()
        ]

    def _compute_tf(self, tokens: List[str]) -> Dict[str, float]:
        if not tokens:
            return {}
        counter = Counter(tokens)
        max_count = max(counter.values())
        return {term: count / max_count for term, count in counter.items()}

    def _compute_idf_single(self, tf: Dict[str, float]) -> Dict[str, float]:
        # For single doc, IDF = log(1 + 1/(tf+1)) as a simple smoothing
        return {term: math.log(1.0 / (v + 0.5) + 1) for term, v in tf.items()}

    # ------------------------------------------------------------------
    # Keyword building
    # ------------------------------------------------------------------

    def _build_keywords(
        self, tfidf: Dict[str, float], tf: Dict[str, float]
    ) -> List[Keyword]:
        raw_freq = Counter({t: round(v * 100) for t, v in tf.items()})
        keywords = [
            Keyword(
                term=term,
                tf_idf=score,
                frequency=raw_freq.get(term, 1),
                documents=1,
                is_phrase=False,
            )
            for term, score in sorted(tfidf.items(), key=lambda x: x[1], reverse=True)
        ]
        return keywords

    # ------------------------------------------------------------------
    # Phrase extraction (bigrams / trigrams)
    # ------------------------------------------------------------------

    def _extract_phrases(self, text: str) -> List[Keyword]:
        words = re.findall(r"\b\w+\b", text.lower())
        filtered = [
            w for w in words
            if w not in self._STOPWORDS and len(w) >= self.min_word_length
        ]
        phrase_counts: Counter = Counter()
        for n in range(2, self.phrase_max_words + 1):
            for i in range(len(filtered) - n + 1):
                phrase = " ".join(filtered[i : i + n])
                phrase_counts[phrase] += 1

        phrases = [
            Keyword(
                term=phrase,
                tf_idf=count * 0.5,
                frequency=count,
                documents=1,
                is_phrase=True,
            )
            for phrase, count in phrase_counts.most_common(20)
            if count >= 2
        ]
        return phrases

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    @staticmethod
    def highlight_keywords(text: str, keywords: List[str], marker: str = "**") -> str:
        """Wrap keyword occurrences in `marker` for display."""
        for kw in sorted(keywords, key=len, reverse=True):
            pattern = re.compile(re.escape(kw), re.IGNORECASE)
            text = pattern.sub(f"{marker}{kw}{marker}", text)
        return text

    @staticmethod
    def keyword_cloud_data(keywords: List[Keyword]) -> List[Dict[str, Any]]:
        """Return word-cloud-compatible weight data."""
        return [{"text": kw.term, "value": round(kw.tf_idf * 100, 2)} for kw in keywords]
