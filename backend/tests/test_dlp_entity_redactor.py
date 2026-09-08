"""
Tests for Enterprise Meeting Transcription Entity Redactor & DLP Masker
=======================================================================
Validates Luhn algorithm verification, PII redaction (SSN, Email, CC),
cloud secret masking (AWS, GitHub PAT), and risk scoring.
"""

import unittest
from backend.services.ai.dlp_entity_redactor import (
    DlpEntityRedactor,
    EntityType,
    RedactionStrategy,
    LuhnValidator,
)


class TestDlpEntityRedactor(unittest.TestCase):

    def setUp(self):
        self.redactor = DlpEntityRedactor(hmac_key="test-audit-salt")

    def test_luhn_validator_accuracy(self):
        # Valid test Visa number (4532... standard test card)
        valid_card = "4532 0150 0000 0007"
        self.assertTrue(LuhnValidator.is_valid(valid_card))

        # Invalid checksum
        invalid_card = "4532 0150 0000 0009"
        self.assertFalse(LuhnValidator.is_valid(invalid_card))

    def test_credit_card_redaction_label_strategy(self):
        transcript = "Please charge 4532-0150-0000-0007 for the enterprise license."
        res = self.redactor.scan_and_redact(transcript, strategy=RedactionStrategy.LABEL)

        self.assertTrue(res.has_violations)
        self.assertEqual(len(res.entities), 1)
        self.assertEqual(res.entities[0].entity_type, EntityType.CREDIT_CARD)
        self.assertIn("[CONFIDENTIAL_CREDIT_CARD]", res.redacted_text)
        self.assertNotIn("4532", res.redacted_text)

    def test_credit_card_mask_strategy(self):
        transcript = "Card on file is 4532015000000007."
        res = self.redactor.scan_and_redact(transcript, strategy=RedactionStrategy.MASK)

        self.assertIn("****-****-****-0007", res.redacted_text)

    def test_aws_access_key_detection_and_high_risk(self):
        transcript = "Deploy using AKIAIOSFODNN7EXAMPLE credentials."
        res = self.redactor.scan_and_redact(transcript)

        self.assertTrue(res.has_violations)
        self.assertEqual(res.entities[0].entity_type, EntityType.AWS_ACCESS_KEY)
        self.assertGreaterEqual(res.risk_score, 0.75)

    def test_ssn_redaction_and_tokenization(self):
        transcript = "Participant SSN is 012-34-5678."
        res = self.redactor.scan_and_redact(transcript, strategy=RedactionStrategy.TOKENIZE)

        self.assertTrue(res.has_violations)
        self.assertEqual(res.entities[0].entity_type, EntityType.SSN)
        self.assertIn("[TOKEN:SSN:", res.redacted_text)

    def test_multiple_mixed_pii_in_transcript(self):
        transcript = (
            "Contact john.doe@elevateiq.com or call 415-555-2671. "
            "Server IP is 192.168.1.100."
        )
        res = self.redactor.scan_and_redact(transcript, strategy=RedactionStrategy.LABEL)

        self.assertEqual(len(res.entities), 3)
        entity_types = set(e.entity_type for e in res.entities)
        self.assertIn(EntityType.EMAIL, entity_types)
        self.assertIn(EntityType.PHONE_NUMBER, entity_types)
        self.assertIn(EntityType.IP_ADDRESS, entity_types)
        self.assertNotIn("john.doe@elevateiq.com", res.redacted_text)
        self.assertNotIn("415-555-2671", res.redacted_text)

    def test_clean_text_produces_zero_risk(self):
        transcript = "Today we reviewed the quarterly OKRs and roadmap progress."
        res = self.redactor.scan_and_redact(transcript)

        self.assertFalse(res.has_violations)
        self.assertEqual(len(res.entities), 0)
        self.assertEqual(res.risk_score, 0.0)
        self.assertEqual(res.redacted_text, transcript)


if __name__ == "__main__":
    unittest.main()
