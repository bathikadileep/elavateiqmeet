"""
ElevateIQ — Unit Test Suite for NLP Entity Recognizer
=====================================================
Tests extracting organizations, technologies, and dates from text.
"""

import unittest
from backend.services.ai.nlp_entity_recognizer import NLPEntityRecognizerEngine


class NLPEntityRecognizerTestSuite(unittest.TestCase):

    def setUp(self):
        self.engine = NLPEntityRecognizerEngine()

    def test_entity_extraction(self):
        """Test extracting Google, WebRTC, and Monday from string."""
        text = "Google team will update WebRTC server by Monday."
        entities = self.engine.extract_entities(text)

        self.assertIn("Google", entities["organizations"])
        self.assertIn("WebRTC", entities["technologies"])
        self.assertIn("Monday", entities["dates"])


if __name__ == "__main__":
    unittest.main()
