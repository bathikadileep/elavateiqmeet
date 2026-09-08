"""
ElevateIQ — Unit Test Suite for Sentiment Analyzer Service
===========================================================
Tests positive and negative sentence sentiment evaluation and overall meeting sentiment curves.
"""

import unittest
from backend.services.ai.sentiment_analyzer import SentimentAnalyzerService


class SentimentAnalysisTestSuite(unittest.TestCase):

    def test_positive_sentence_sentiment(self):
        """Test analyzing positive transcript sentence."""
        res = SentimentAnalyzerService.analyze_line_sentiment("We had an outstanding quarter with awesome sales growth and great team execution!")
        self.assertEqual(res["sentiment"], "positive")
        self.assertGreaterEqual(res["score"], 0.8)

    def test_negative_sentence_sentiment(self):
        """Test analyzing negative transcript sentence."""
        res = SentimentAnalyzerService.analyze_line_sentiment("The outage caused terrible problem, delayed features, and failed deployments.")
        self.assertEqual(res["sentiment"], "negative")
        self.assertLessEqual(res["score"], 0.4)

    def test_meeting_sentiment_curve(self):
        """Test computing overall meeting sentiment trajectory across lines."""
        lines = [
            {"speaker_name": "Alice", "transcript_text": "We faced severe delayed issues."},
            {"speaker_name": "Bob", "transcript_text": "However, the fix is awesome and approved."},
            {"speaker_name": "Alice", "transcript_text": "Great work, thanks everyone!"}
        ]
        curve = SentimentAnalyzerService.calculate_meeting_sentiment_curve(lines)
        self.assertEqual(curve["segment_count"], 3)
        self.assertIn(curve["overall_sentiment"], ["positive", "neutral"])


if __name__ == "__main__":
    unittest.main()
