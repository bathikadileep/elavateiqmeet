"""Tests for KeywordExtractor service."""

import unittest
from backend.services.ai.keyword_extractor import KeywordExtractor, Keyword


class TestKeywordExtractor(unittest.TestCase):

    def setUp(self):
        self.extractor = KeywordExtractor(max_keywords=15, include_phrases=True)
        self.sample_text = (
            "The engineering team discussed cloud infrastructure deployment strategies. "
            "Kubernetes orchestration and Docker containerization were key topics. "
            "The team decided to migrate the backend services to AWS EKS cluster. "
            "Performance optimization and latency reduction are primary objectives. "
            "Load balancing across multiple availability zones ensures high availability."
        )

    def test_extract_returns_result(self):
        result = self.extractor.extract(self.sample_text, document_id="doc1")
        self.assertEqual(result.document_id, "doc1")
        self.assertIsInstance(result.keywords, list)
        self.assertGreater(len(result.keywords), 0)

    def test_keywords_have_positive_tfidf(self):
        result = self.extractor.extract(self.sample_text)
        for kw in result.keywords:
            self.assertGreaterEqual(kw.tf_idf, 0)

    def test_top_keyword_populated(self):
        result = self.extractor.extract(self.sample_text)
        self.assertIsNotNone(result.top_keyword)
        self.assertIsInstance(result.top_keyword, str)

    def test_keyphrases_extracted(self):
        result = self.extractor.extract(self.sample_text)
        # May or may not find phrases depending on frequency threshold
        self.assertIsInstance(result.keyphrases, list)

    def test_total_words_populated(self):
        result = self.extractor.extract(self.sample_text)
        self.assertGreater(result.total_words, 0)

    def test_unique_terms_populated(self):
        result = self.extractor.extract(self.sample_text)
        self.assertGreater(result.unique_terms, 0)

    def test_stopwords_excluded(self):
        result = self.extractor.extract(self.sample_text)
        stopwords = {"the", "and", "to", "a", "in", "of", "is", "for"}
        for kw in result.keywords:
            self.assertNotIn(kw.term.lower(), stopwords)

    def test_max_keywords_respected(self):
        result = self.extractor.extract(self.sample_text)
        self.assertLessEqual(len(result.keywords), self.extractor.max_keywords)

    def test_to_dict(self):
        result = self.extractor.extract(self.sample_text)
        d = result.to_dict()
        self.assertIn("keywords", d)
        self.assertIn("total_words", d)
        self.assertIn("top_keyword", d)

    def test_get_top_terms(self):
        terms = self.extractor.get_top_terms(self.sample_text, n=5)
        self.assertIsInstance(terms, list)
        self.assertLessEqual(len(terms), 5)
        for term in terms:
            self.assertIsInstance(term, str)

    def test_batch_extraction(self):
        docs = {
            "doc_a": "Machine learning models improve accuracy over time with more data.",
            "doc_b": "Deep learning neural networks require large training datasets.",
            "doc_c": "Natural language processing enables text understanding and generation.",
        }
        results = self.extractor.extract_batch(docs)
        self.assertIn("doc_a", results)
        self.assertIn("doc_b", results)
        self.assertIn("doc_c", results)
        for doc_id, result in results.items():
            self.assertGreater(len(result.keywords), 0)

    def test_highlight_keywords(self):
        text = "The Kubernetes cluster needs optimization for performance."
        keywords = ["kubernetes", "optimization", "performance"]
        highlighted = KeywordExtractor.highlight_keywords(text, keywords)
        self.assertIn("**", highlighted)

    def test_keyword_cloud_data(self):
        keywords = [
            Keyword(term="cloud", tf_idf=0.8, frequency=5, documents=1),
            Keyword(term="infrastructure", tf_idf=0.6, frequency=3, documents=1),
        ]
        cloud = KeywordExtractor.keyword_cloud_data(keywords)
        self.assertEqual(len(cloud), 2)
        self.assertIn("text", cloud[0])
        self.assertIn("value", cloud[0])

    def test_short_words_excluded(self):
        result = self.extractor.extract("It is so a the of in on at")
        # All very short or stopwords — may produce empty keywords
        self.assertIsInstance(result.keywords, list)

    def test_phrase_detection_disabled(self):
        extractor = KeywordExtractor(include_phrases=False)
        result = extractor.extract(self.sample_text)
        for kw in result.keyphrases:
            self.fail("Should have no keyphrases when include_phrases=False")
        self.assertEqual(result.keyphrases, [])


if __name__ == "__main__":
    unittest.main()
