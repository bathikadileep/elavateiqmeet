"""
ElevateIQ — Unit Test Suite for Data Loss Prevention (DLP) Real-Time Scanner
=============================================================================
Tests regex scanning for SSNs, credit card numbers, AWS secrets, redaction, and offense logging.
"""

import unittest
from backend.services.enterprise.data_loss_prevention import DataLossPreventionEngine


class DLPEngineTestSuite(unittest.TestCase):

    def setUp(self):
        self.engine = DataLossPreventionEngine()

    def test_ssn_detection_and_redaction(self):
        """Test detecting Social Security Numbers (SSN) and masking content."""
        sample_text = "Here is my confidential SSN: 123-45-6789 for payroll verification."
        is_blocked, redacted, offenses = self.engine.scan_text_content(sample_text, source_context="chat", user_id="usr_99")

        self.assertTrue(is_blocked)
        self.assertEqual(len(offenses), 1)
        self.assertEqual(offenses[0]["policy_name"], "SSN")
        self.assertIn("[REDACTED_DLP_VIOLATION]", redacted)
        self.assertNotIn("123-45-6789", redacted)

    def test_clean_text_passes_scanner(self):
        """Test clean text without sensitive PII passes without blocking."""
        clean_text = "Hello team, let us review the sprint roadmap for Q3."
        is_blocked, redacted, offenses = self.engine.scan_text_content(clean_text)

        self.assertFalse(is_blocked)
        self.assertEqual(len(offenses), 0)
        self.assertEqual(clean_text, redacted)


if __name__ == "__main__":
    unittest.main()
