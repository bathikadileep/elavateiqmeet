"""
ElevateIQ — Unit Test Suite for Topic Segmentation Engine
==========================================================
Tests semantic transcript topic partitioning into chapters.
"""

import unittest
from backend.services.ai.topic_segmentation_engine import TopicSegmentationEngine


class TopicSegmentationEngineTestSuite(unittest.TestCase):

    def setUp(self):
        self.engine = TopicSegmentationEngine()

    def test_topic_segmentation(self):
        """Test partitioning transcript lines by topic transitions."""
        lines = [
            {"speaker_name": "Alice", "transcript_text": "Let us review the architecture for next sprint."},
            {"speaker_name": "Bob", "transcript_text": "Moving on to budget allocation questions."}
        ]

        res = self.engine.segment_transcript_topics(lines)
        self.assertGreaterEqual(res["total_topics"], 1)


if __name__ == "__main__":
    unittest.main()
