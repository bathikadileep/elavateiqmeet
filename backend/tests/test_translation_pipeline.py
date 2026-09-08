"""
ElevateIQ — Unit Test Suite for Neural Translation Pipeline
============================================================
Tests neural text translation across supported target language codes.
"""

import unittest
from backend.services.ai.translation_pipeline import TranslationPipelineEngine


class TranslationPipelineTestSuite(unittest.TestCase):

    def setUp(self):
        self.engine = TranslationPipelineEngine()

    def test_text_translation_spanish(self):
        """Test translating text from English to Spanish."""
        res = self.engine.translate_text("Hello everyone, welcome to the meeting.", source_lang="en", target_lang="es")
        self.assertEqual(res["target_lang"], "es")
        self.assertIn("Hola", res["translated_text"])

    def test_text_translation_french(self):
        """Test translating text from English to French."""
        res = self.engine.translate_text("Hello everyone, welcome to the meeting.", source_lang="en", target_lang="fr")
        self.assertEqual(res["target_lang"], "fr")
        self.assertIn("Bonjour", res["translated_text"])


if __name__ == "__main__":
    unittest.main()
