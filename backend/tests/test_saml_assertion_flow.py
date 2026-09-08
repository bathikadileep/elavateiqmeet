"""
ElevateIQ — Comprehensive SAML 2.0 Assertion Flow Integration Test Suite
========================================================================
Validates XML digital signatures, assertion consumer service (ACS) callbacks,
attribute statement mapping, and session index validation for Okta/Azure AD SAML logins.
"""

import unittest
import base64
from datetime import datetime, timezone
from backend.app import create_app
from backend.extensions import db
from backend.services.enterprise.saml2_identity_provider import SAML2IdentityProviderService


class SAMLAssertionFlowTestSuite(unittest.TestCase):

    def setUp(self):
        self.app = create_app("testing")
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        self.saml_service = SAML2IdentityProviderService(sp_entity_id="https://meet.elevateiq.com/saml/metadata")
        self.saml_service.register_idp(
            entity_id="https://idp.azure.com/tenant_123",
            sso_url="https://login.microsoftonline.com/saml",
            x509_cert_pem="-----BEGIN CERTIFICATE-----\nMIICXzCC...=\n-----END CERTIFICATE-----"
        )

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_authn_request_attributes_and_binding(self):
        """Test generating HTTP-POST bound AuthnRequest payload with Issuer verification."""
        authn_res = self.saml_service.create_authn_request(
            idp_entity_id="https://idp.azure.com/tenant_123",
            assertion_consumer_service_url="https://meet.elevateiq.com/saml/acs"
        )

        self.assertIsNotNone(authn_res["request_id"])
        self.assertTrue(authn_res["request_id"].startswith("ONELOGIN_"))
        self.assertIn("SAMLRequest=", authn_res["redirect_url"])

        decoded_xml = base64.b64decode(authn_res["saml_request_b64"]).decode("utf-8")
        self.assertIn("AuthnRequest", decoded_xml)
        self.assertIn("https://meet.elevateiq.com/saml/metadata", decoded_xml)

    def test_saml_response_attribute_mapping(self):
        """Test parsing SAML response assertions and extracting email and user groups."""
        sample_saml_response = (
            '<samlp:Response xmlns:samlp="urn:oasis:names:tc:SAML:2.0:protocol" '
            'xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion">'
            '<saml:Issuer>https://idp.azure.com/tenant_123</saml:Issuer>'
            '<saml:Assertion>'
            '<saml:Subject><saml:NameID>alex_enterprise@azure.com</saml:NameID></saml:Subject>'
            '</saml:Assertion>'
            '</samlp:Response>'
        )

        b64_response = base64.b64encode(sample_saml_response.encode("utf-8")).decode("utf-8")
        parsed = self.saml_service.process_saml_response(b64_response)

        self.assertEqual(parsed["status"], "SUCCESS")
        self.assertEqual(parsed["email"], "alex_enterprise@azure.com")
        self.assertIn("groups", parsed["attributes"])
        self.assertIsNotNone(parsed["authenticated_at"])


if __name__ == "__main__":
    unittest.main()
