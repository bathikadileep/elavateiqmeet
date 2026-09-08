"""
Tests for Enterprise SAML 2.0 Identity Provider & SP Federation Engine
======================================================================
Validates SAML 2.0 Web Browser SSO profile, metadata XML synthesis,
AuthnRequest generation, XML assertion parsing, anti-replay mitigation,
and cross-vendor claim normalization.
"""

import base64
import time
import unittest
from backend.services.enterprise.saml_federation_engine import (
    SamlFederationEngine,
    NAMEID_FORMAT_EMAIL,
    SAML_PROTOCOL_NS,
    SAML_ASSERTION_NS,
)


class TestSamlFederationEngine(unittest.TestCase):

    def setUp(self):
        self.engine = SamlFederationEngine(
            sp_entity_id="https://elevateiq.com/saml/sp",
            acs_url="https://elevateiq-backend.onrender.com/api/sso/saml/acs",
        )
        self.tenant_id = "org_wayne_enterprises"
        self.idp_entity_id = "https://identity.wayne.com/adfs/services/trust"
        self.engine.register_tenant_idp(
            tenant_id=self.tenant_id,
            entity_id=self.idp_entity_id,
            sso_url="https://identity.wayne.com/adfs/ls/",
            x509_cert_pem="MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAzMockCert",
        )

    def _build_mock_saml_response(
        self,
        assertion_id="assert_mock_101",
        issuer="https://identity.wayne.com/adfs/services/trust",
        email="bruce.wayne@wayne.com",
        first_name="Bruce",
        last_name="Wayne",
        audience="https://elevateiq.com/saml/sp",
        is_expired=False,
        status_code="urn:oasis:names:tc:SAML:2.0:status:Success",
    ) -> str:
        now_ts = time.time()
        not_before = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_ts - 60))
        not_after_ts = now_ts - 3600 if is_expired else now_ts + 3600
        not_after = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(not_after_ts))

        xml = f"""<samlp:Response xmlns:samlp="{SAML_PROTOCOL_NS}"
                 xmlns:saml="{SAML_ASSERTION_NS}"
                 ID="resp_mock_99"
                 Version="2.0">
  <samlp:Status>
    <samlp:StatusCode Value="{status_code}"/>
  </samlp:Status>
  <saml:Assertion ID="{assertion_id}" Version="2.0">
    <saml:Issuer>{issuer}</saml:Issuer>
    <saml:Subject>
      <saml:NameID Format="{NAMEID_FORMAT_EMAIL}">{email}</saml:NameID>
    </saml:Subject>
    <saml:Conditions NotBefore="{not_before}" NotOnOrAfter="{not_after}">
      <saml:AudienceRestriction>
        <saml:Audience>{audience}</saml:Audience>
      </saml:AudienceRestriction>
    </saml:Conditions>
    <saml:AttributeStatement>
      <saml:Attribute Name="http://schemas.xmlsoap.org/ws/2005/05/identity/claims/givenname">
        <saml:AttributeValue>{first_name}</saml:AttributeValue>
      </saml:Attribute>
      <saml:Attribute Name="http://schemas.xmlsoap.org/ws/2005/05/identity/claims/surname">
        <saml:AttributeValue>{last_name}</saml:AttributeValue>
      </saml:Attribute>
      <saml:Attribute Name="http://schemas.microsoft.com/ws/2008/06/identity/claims/groups">
        <saml:AttributeValue>ExecutiveBoard</saml:AttributeValue>
        <saml:AttributeValue>SecurityAdmins</saml:AttributeValue>
      </saml:Attribute>
      <saml:Attribute Name="department">
        <saml:AttributeValue>Executive</saml:AttributeValue>
      </saml:Attribute>
    </saml:AttributeStatement>
  </saml:Assertion>
</samlp:Response>"""
        return base64.b64encode(xml.encode("utf-8")).decode("ascii")

    def test_sp_metadata_xml_generation(self):
        metadata_xml = self.engine.generate_sp_metadata_xml()
        self.assertIn("EntityDescriptor", metadata_xml)
        self.assertIn("https://elevateiq.com/saml/sp", metadata_xml)
        self.assertIn("AssertionConsumerService", metadata_xml)
        self.assertIn("HTTP-POST", metadata_xml)

    def test_authn_request_generation(self):
        redirect_url, req_id = self.engine.generate_authn_request(
            self.tenant_id, relay_state="/room/instant-boardroom"
        )
        self.assertTrue(redirect_url.startswith("https://identity.wayne.com/adfs/ls/"))
        self.assertIn("SAMLRequest=", redirect_url)
        self.assertIn("RelayState=", redirect_url)
        self.assertIn(req_id, self.engine.pending_requests)

    def test_successful_saml_response_validation(self):
        saml_b64 = self._build_mock_saml_response()
        result = self.engine.validate_saml_response(self.tenant_id, saml_b64)

        self.assertTrue(result.is_valid)
        self.assertIsNotNone(result.user_profile)
        self.assertEqual(result.user_profile.email, "bruce.wayne@wayne.com")
        self.assertEqual(result.user_profile.first_name, "Bruce")
        self.assertEqual(result.user_profile.last_name, "Wayne")
        self.assertEqual(result.user_profile.display_name, "Bruce Wayne")
        self.assertIn("ExecutiveBoard", result.user_profile.roles)
        self.assertEqual(result.user_profile.department, "Executive")

    def test_replay_attack_detection(self):
        saml_b64 = self._build_mock_saml_response(assertion_id="assert_replay_once")
        # 1st time -> valid
        res1 = self.engine.validate_saml_response(self.tenant_id, saml_b64)
        self.assertTrue(res1.is_valid)

        # 2nd time -> rejected by anti-replay cache!
        res2 = self.engine.validate_saml_response(self.tenant_id, saml_b64)
        self.assertFalse(res2.is_valid)
        self.assertIn("Replay attack detected", res2.error_message)

    def test_issuer_mismatch_rejected(self):
        saml_b64 = self._build_mock_saml_response(issuer="https://evil-hacker.com/idp")
        result = self.engine.validate_saml_response(self.tenant_id, saml_b64)
        self.assertFalse(result.is_valid)
        self.assertIn("Issuer mismatch", result.error_message)

    def test_expired_assertion_rejected(self):
        saml_b64 = self._build_mock_saml_response(is_expired=True)
        result = self.engine.validate_saml_response(self.tenant_id, saml_b64)
        self.assertFalse(result.is_valid)
        self.assertIn("Assertion has expired", result.error_message)

    def test_audience_mismatch_rejected(self):
        saml_b64 = self._build_mock_saml_response(audience="https://different-sp.com")
        result = self.engine.validate_saml_response(self.tenant_id, saml_b64)
        self.assertFalse(result.is_valid)
        self.assertIn("Audience mismatch", result.error_message)


if __name__ == "__main__":
    unittest.main()
