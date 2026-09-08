"""
ElevateIQ — Sentiment Analysis & Emotional Curve Engine
========================================================
Calculates sentiment score trajectories (positive, neutral, negative) and engagement levels
across meeting transcripts for participant emotional health analytics.
"""

import re
import json
import logging
from typing import Dict, Any, List, Optional

log = logging.getLogger("elevateiq.services.ai.sentiment")

POSITIVE_WORDS = {"agree", "great", "excellent", "awesome", "good", "perfect", "resolved", "approved", "thanks", "thank"}
NEGATIVE_WORDS = {"issue", "problem", "bug", "delayed", "blocked", "failed", "error", "disagree", "frustrated", "concern"}


class SentimentAnalyzerService:
    """Sentiment & Engagement Score Analyzer."""

    @staticmethod
    def analyze_line_sentiment(text: str) -> Dict[str, Any]:
        """Analyze individual transcript line sentiment score."""
        words = set(re.findall(r"\w+", (text or "").lower()))

        pos_count = len(words.intersection(POSITIVE_WORDS))
        neg_count = len(words.intersection(NEGATIVE_WORDS))

        if pos_count > neg_count:
            sentiment = "positive"
            score = 0.85
        elif neg_count > pos_count:
            sentiment = "negative"
            score = 0.25
        else:
            sentiment = "neutral"
            score = 0.50

        return {"sentiment": sentiment, "score": score, "positive_count": pos_count, "negative_count": neg_count}

    @staticmethod
    def calculate_meeting_sentiment_curve(lines: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate overall meeting sentiment trajectory across timeline segments."""
        if not lines:
            return {"overall_sentiment": "neutral", "overall_score": 0.50, "timeline": []}

        timeline = []
        total_score = 0.0

        for idx, line in enumerate(lines):
            text = line.get("transcript_text", "")
            eval_res = SentimentAnalyzerService.analyze_line_sentiment(text)
            total_score += eval_res["score"]

            timeline.append({
                "segment_index": idx,
                "speaker_name": line.get("speaker_name", "Speaker"),
                "sentiment": eval_res["sentiment"],
                "score": eval_res["score"],
            })

        avg_score = round(total_score / len(lines), 2)
        if avg_score >= 0.65:
            overall = "positive"
        elif avg_score <= 0.40:
            overall = "negative"
        else:
            overall = "neutral"

        return {
            "overall_sentiment": overall,
            "overall_score": avg_score,
            "segment_count": len(lines),
            "timeline": timeline,
        }
