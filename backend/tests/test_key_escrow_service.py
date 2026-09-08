"""
Tests for Media Encryption Key Escrow & Enterprise PKI Authority Service
========================================================================
Validates Shamir's Secret Sharing (k, n) threshold cryptography over GF(p),
trustee quorum approvals, key reconstruction integrity, and WebRTC DTLS PKI lifecycle.
"""

import hashlib
import os
import unittest
from backend.services.enterprise.key_escrow_service import (
    KeyEscrowService,
    ShamirThresholdMath,
    TrusteeRole,
    EscrowStatus,
)


class TestKeyEscrowService(unittest.TestCase):

    def setUp(self):
        self.service = KeyEscrowService()
        self.tenant_id = "tenant_megacorp"

        # Pre-register 5 trustees for the tenant
        self.trustees = [
            self.service.register_trustee(self.tenant_id, "clo@megacorp.com", TrusteeRole.CHIEF_LEGAL_OFFICER),
            self.service.register_trustee(self.tenant_id, "dpo@megacorp.com", TrusteeRole.DATA_PROTECTION_OFFICER),
            self.service.register_trustee(self.tenant_id, "sec@megacorp.com", TrusteeRole.SECURITY_OPERATIONS_LEAD),
            self.service.register_trustee(self.tenant_id, "auditor@megacorp.com", TrusteeRole.COMPLIANCE_AUDITOR),
            self.service.register_trustee(self.tenant_id, "escrow@megacorp.com", TrusteeRole.EXTERNAL_ESCROW_AGENT),
        ]

    def test_shamir_math_direct_reconstruction(self):
        # Test basic mathematical splitting and recovery
        secret = os.urandom(32)
        k, n = 3, 5
        shares = ShamirThresholdMath.split_secret(secret, k, n)
        self.assertEqual(len(shares), 5)

        # Reconstruct with first 3 shares (1, 2, 3)
        subset_1 = shares[:3]
        rec_1 = ShamirThresholdMath.reconstruct_secret(subset_1)
        self.assertEqual(rec_1, secret)

        # Reconstruct with different 3 shares (2, 4, 5)
        subset_2 = [shares[1], shares[3], shares[4]]
        rec_2 = ShamirThresholdMath.reconstruct_secret(subset_2)
        self.assertEqual(rec_2, secret)

    def test_escrow_session_creation_and_shares(self):
        session_id = "meet_sec_conf_101"
        secret_key = os.urandom(32)
        record = self.service.create_escrow_session(
            session_id=session_id,
            tenant_id=self.tenant_id,
            threshold_k=3,
            total_shares_n=5,
            master_key_bytes=secret_key,
        )

        self.assertEqual(record.session_id, session_id)
        self.assertEqual(record.status, EscrowStatus.LOCKED)
        self.assertEqual(len(record.shares), 5)
        self.assertEqual(record.key_fingerprint, hashlib.sha256(secret_key).hexdigest())

    def test_quorum_approval_and_key_reconstruction(self):
        session_id = "meet_audit_202"
        secret_key = os.urandom(32)
        self.service.create_escrow_session(
            session_id=session_id,
            tenant_id=self.tenant_id,
            threshold_k=3,
            total_shares_n=5,
            master_key_bytes=secret_key,
        )

        # 1st approval -> PENDING_APPROVALS
        rec = self.service.submit_trustee_approval(
            session_id, self.trustees[0].trustee_id, "Court Subpoena Case #4491"
        )
        self.assertEqual(rec.status, EscrowStatus.PENDING_APPROVALS)

        # Attempting reconstruction before quorum should fail
        with self.assertRaises(ValueError) as ctx:
            self.service.reconstruct_escrow_key(session_id, requester_id="legal_investigator")
        self.assertIn("Quorum not met", str(ctx.exception))

        # 2nd approval
        rec = self.service.submit_trustee_approval(
            session_id, self.trustees[1].trustee_id, "DPO Signoff"
        )
        self.assertEqual(rec.status, EscrowStatus.PENDING_APPROVALS)

        # 3rd approval -> QUORUM_MET
        rec = self.service.submit_trustee_approval(
            session_id, self.trustees[2].trustee_id, "InfoSec Forensic Authorization"
        )
        self.assertEqual(rec.status, EscrowStatus.QUORUM_MET)

        # Now reconstruct key!
        recovered_key = self.service.reconstruct_escrow_key(session_id, requester_id="legal_investigator")
        self.assertEqual(recovered_key, secret_key)
        self.assertEqual(self.service.sessions[session_id].status, EscrowStatus.RECONSTRUCTED)

    def test_webrtc_pki_issuance_and_revocation(self):
        cert = self.service.issue_webrtc_certificate(
            tenant_id=self.tenant_id,
            common_name="sfu-edge-01.megacorp.internal",
            validity_days=90,
        )

        self.assertIsNotNone(cert.cert_id)
        self.assertIn(":", cert.fingerprint_sha256)  # Check RFC 8122 colon formatting
        self.assertEqual(len(cert.fingerprint_sha256.split(":")), 32)

        # Status check - valid
        status = self.service.verify_certificate_status(cert.cert_id)
        self.assertTrue(status["valid"])
        self.assertEqual(status["fingerprint"], cert.fingerprint_sha256)

        # Revocation
        self.service.revoke_certificate(cert.cert_id, reason="KeyCompromise")
        rev_status = self.service.verify_certificate_status(cert.cert_id)
        self.assertFalse(rev_status["valid"])
        self.assertEqual(rev_status["error"], "Certificate is revoked")

    def test_invalid_trustee_count_raises(self):
        with self.assertRaises(ValueError):
            # Tenant only has 5 trustees, requesting 10 should fail
            self.service.create_escrow_session(
                session_id="invalid_session",
                tenant_id=self.tenant_id,
                threshold_k=6,
                total_shares_n=10,
            )


if __name__ == "__main__":
    unittest.main()
