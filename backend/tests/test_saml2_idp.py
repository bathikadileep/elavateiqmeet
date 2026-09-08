"""
ElevateIQ — Unit Test Suite for SAML 2.0 Identity Provider & SSO Service
========================================================================
Tests SAML IdP registration, AuthnRequest generation, and SAML response assertion decoding.
"""

import unittest
import base64
from backend.services.enterprise.saml2_identity_provider import SAML2IdentityProviderService


class SAML2IdentityProviderTestSuite(unittest.TestCase):

    def setUp(self):
        self.service = SAML2IdentityProviderService(sp_entity_id="https://meet.elevateiq.com/saml/metadata")
        self.service.register_idp(
            entity_id="https://idp.okta.com/exk12345",
            sso_url="https://idp.okta.com/app/sso",
            x509_cert_pem="-----BEGIN CERTIFICATE-----\nMIIC...=\n-----END CERTIFICATE-----"
        )

    def test_authn_request_generation(self):
        """Test generating Base64 encoded SAML 2.0 AuthnRequest payload."""
        res = self.service.create_authn_request(
            idp_entity_id="https://idp.okta.com/exk12345",
            assertion_consumer_service_url="https://meet.elevateiq.com/saml/acs"
        )

        self.assertTrue(res["request_id"].startswith("ONELOGIN_"))
        self.assertIn("SAMLRequest=", res["redirect_url"])

    def test_process_saml_response(self):
        """Test decoding Base64 SAML response XML assertion."""
        raw_xml = "<samlp:Response><saml:NameID>john_saml@okta.com</saml:NameID></samlp:Response>"
        b64_resp = base64.b64encode(raw_xml.encode("utf-8")).decode("utf-8")

        res = self.service.process_saml_response(b64_resp)
        self.assertEqual(res["status"], "SUCCESS")
        self.assertEqual(res["email"], "john_saml@okta.com")


if __name__ == "__main__":
    unittest.main()
