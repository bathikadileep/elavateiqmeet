"""
ElevateIQ — Unit Test Suite for SAML XMLDSig Signature Validator
================================================================
Tests validating XML digital signatures on SAML assertions.
"""

import unittest
from backend.services.enterprise.saml_signature_validator import SAMLSignatureValidator


class SAMLSignatureValidatorTestSuite(unittest.TestCase):

    def setUp(self):
        self.validator = SAMLSignatureValidator()

    def test_signature_validation(self):
        """Test validating XMLDSig signature."""
        xml = "<samlp:Response><ds:Signature>...</ds:Signature></samlp:Response>"
        cert = "-----BEGIN CERTIFICATE-----\nMIIC...\n-----END CERTIFICATE-----"

        valid = self.validator.validate_assertion_signature(xml, cert)
        self.assertTrue(valid)


if __name__ == "__main__":
    unittest.main()
