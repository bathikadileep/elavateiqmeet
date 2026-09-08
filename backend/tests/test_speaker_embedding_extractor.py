"""
ElevateIQ — Unit Test Suite for Speaker Embedding Neural Extractor
===================================================================
Tests 192-dimensional vector embedding extraction and cosine similarity matching.
"""

import unittest
from backend.services.ai.speaker_embedding_extractor import SpeakerEmbeddingExtractor


class SpeakerEmbeddingExtractorTestSuite(unittest.TestCase):

    def setUp(self):
        self.extractor = SpeakerEmbeddingExtractor()

    def test_extract_and_similarity(self):
        """Test extracting embedding vector and calculating cosine similarity."""
        pcm1 = b"\x10\x20\x30\x40" * 100
        pcm2 = b"\x10\x20\x30\x40" * 100

        vec1 = self.extractor.extract_embedding_vector(pcm1)
        vec2 = self.extractor.extract_embedding_vector(pcm2)

        self.assertEqual(len(vec1), 192)
        sim = self.extractor.compute_cosine_similarity(vec1, vec2)
        self.assertEqual(sim, 1.0)


if __name__ == "__main__":
    unittest.main()
