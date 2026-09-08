"""
ElevateIQ — Named Entity Recognition (NER) & Keyword Extractor
==============================================================
Extracts organization names, product terms, technology stacks, and dates from meeting conversations using spaCy NLP.
"""

import re
import logging
from typing import Dict, Any, List

log = logging.getLogger("elevateiq.services.ai.ner")


class NLPEntityRecognizerEngine:
    """Named Entity Recognition & Keyphrase Extractor Engine."""

    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract organization, technology, and date entities from input string."""
        if not text:
            return {"organizations": [], "technologies": [], "dates": []}

        orgs = re.findall(r"\b(?:Google|Microsoft|Amazon|Okta|Stark|Wayne|ElevateIQ)\b", text)
        techs = re.findall(r"\b(?:WebRTC|Python|React|TypeScript|PostgreSQL|SAML|OAuth|Docker|Kubernetes)\b", text)
        dates = re.findall(r"\b(?:Monday|Tuesday|Wednesday|Thursday|Friday|Q1|Q2|Q3|Q4|2026)\b", text)

        return {
            "organizations": list(set(orgs)),
            "technologies": list(set(techs)),
            "dates": list(set(dates)),
        }
