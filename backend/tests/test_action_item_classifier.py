"""
ElevateIQ — Unit Test Suite for Action Item NLP Classifier
===========================================================
Tests action item extraction from transcript lines.
"""

import unittest
from backend.services.ai.action_item_classifier import ActionItemClassifierEngine


class ActionItemClassifierTestSuite(unittest.TestCase):

    def setUp(self):
        self.engine = ActionItemClassifierEngine()

    def test_extract_action_items(self):
        """Test extracting action items from transcript lines."""
        lines = [
            {"speaker_name": "Alice", "transcript_text": "I will do the API benchmarks by tomorrow."},
            {"speaker_name": "Bob", "transcript_text": "Action item for frontend team to update styling."}
        ]

        items = self.engine.extract_action_items(lines)
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]["assigned_to"], "Alice")


if __name__ == "__main__":
    unittest.main()
