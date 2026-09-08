"""
ElevateIQ — Unit Test Suite for SAML 2.0 Metadata XML Parser
============================================================
Tests parsing IdP EntityDescriptor XML files and extracting SSO endpoints.
"""

import unittest
from backend.services.enterprise.saml_metadata_parser import SAMLMetadataParser


class SAMLMetadataParserTestSuite(unittest.TestCase):

    def setUp(self):
        self.parser = SAMLMetadataParser()

    def test_parse_valid_idp_metadata_xml(self):
        """Test parsing valid XML metadata string."""
        sample_xml = (
            '<md:EntityDescriptor xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata" entityID="https://idp.okta.com/exk999">'
            '<md:IDPSSODescriptor>'
            '<md:SingleSignOnService Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST" Location="https://idp.okta.com/sso"/>'
            '</md:IDPSSODescriptor>'
            '</md:EntityDescriptor>'
        )

        res = self.parser.parse_idp_metadata_xml(sample_xml)
        self.assertEqual(res["entity_id"], "https://idp.okta.com/exk999")
        self.assertEqual(res["sso_url"], "https://idp.okta.com/sso")


if __name__ == "__main__":
    unittest.main()
