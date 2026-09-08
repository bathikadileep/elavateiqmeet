"""
ElevateIQ — Redis Subtitle & Translation In-Memory Cache Manager
=================================================================
Caches translated transcript sentences to eliminate duplicate AI model inference latency.
"""

import logging
from typing import Dict, Any, Optional

log = logging.getLogger("elevateiq.services.ai.translation_cache")


class TranslationCacheManager:
    """In-Memory Translation Sentence Cache."""

    def __init__(self):
        self._cache: Dict[str, str] = {}

    def get_cached_translation(self, text: str, target_lang: str) -> Optional[str]:
        """Retrieve cached translation if present."""
        key = f"{target_lang}:{text.strip().lower()}"
        return self._cache.get(key)

    def cache_translation(self, text: str, target_lang: str, translated_text: str) -> None:
        """Store translation result in cache."""
        key = f"{target_lang}:{text.strip().lower()}"
        self._cache[key] = translated_text
        log.debug("Cached translation for key '%s'", key)
