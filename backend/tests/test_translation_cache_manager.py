"""
ElevateIQ — Unit Test Suite for Translation Cache Manager
==========================================================
Tests sentence translation caching and retrieval.
"""

import unittest
from backend.services.ai.translation_cache_manager import TranslationCacheManager


class TranslationCacheManagerTestSuite(unittest.TestCase):

    def setUp(self):
        self.cache = TranslationCacheManager()

    def test_caching_and_retrieval(self):
        """Test caching and fetching sentence translation."""
        self.cache.cache_translation("Hello world", "es", "Hola mundo")
        cached = self.cache.get_cached_translation("Hello world", "es")
        self.assertEqual(cached, "Hola mundo")

        missing = self.cache.get_cached_translation("Unknown text", "es")
        self.assertIsNone(missing)


if __name__ == "__main__":
    unittest.main()
