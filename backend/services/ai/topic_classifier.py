"""
ElevateIQ — Multi-Label Topic Taxonomy Classifier
==================================================
Classifies meeting discussion content into enterprise domain taxonomies
(Engineering, Product Design, Sales Pipeline, Security/Compliance, HR/Hiring, Executive Strategy).
"""

import re
import json
import logging
from typing import Dict, Any, List, Optional

log = logging.getLogger("elevateiq.services.ai.topic")


TAXONOMY_KEYWORDS: Dict[str, List[str]] = {
    "Engineering & Architecture": ["api", "bug", "deploy", "database", "backend", "frontend", "server", "code", "architecture", "refactor", "docker", "test"],
    "Product & UX Design": ["wireframe", "figma", "user story", "ux", "ui", "customer feedback", "feature", "prototype", "roadmap"],
    "Sales & Marketing": ["pipeline", "prospect", "deal", "revenue", "lead", "campaign", "conversion", "pricing", "quota"],
    "Security & Compliance": ["gdpr", "soc2", "audit", "encryption", "vulnerability", "auth", "sso", "cert", "privacy", "dlp"],
    "Executive & Finance": ["budget", "margin", "forecast", "board", "q3", "q4", "investor", "valuation", "kpi", "okr"],
    "HR & Talent": ["hiring", "candidate", "interview", "onboarding", "culture", "performance", "benefits", "retention"],
}


class TopicClassifierService:
    """Enterprise Topic Taxonomy Classifier."""

    @staticmethod
    def classify_transcript_topics(lines: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Classify overall transcript into taxonomy topics with relevance scores."""
        full_text = " ".join([l.get("transcript_text", "").lower() for l in lines])
        words = set(re.findall(r"\w+", full_text))

        category_scores: Dict[str, float] = {}
        for category, keywords in TAXONOMY_KEYWORDS.items():
            matches = sum(1 for kw in keywords if kw in words or kw in full_text)
            if matches > 0:
                category_scores[category] = round((matches / len(keywords)) * 100.0, 1)

        sorted_topics = sorted(category_scores.items(), key=lambda x: x[1], reverse=True)
        primary_topic = sorted_topics[0][0] if sorted_topics else "General Workspace Discussion"

        return {
            "primary_topic": primary_topic,
            "taxonomy_matches": [{"topic": k, "relevance_pct": v} for k, v in sorted_topics[:4]],
            "total_transcript_words": len(full_text.split())
        }
