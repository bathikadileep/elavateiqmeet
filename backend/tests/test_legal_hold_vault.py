"""
Tests for Enterprise E-Discovery Legal Hold & Custody Archive Vault
===================================================================
Validates FRCP Rule 37(e) litigation hold creation, WORM asset locking,
spoliation prevention, overlapping hold resolution, and cryptographic manifests.
"""

import hashlib
import unittest
from backend.services.enterprise.legal_hold_vault import (
    LegalHoldVault,
    MatterStatus,
    ResourceCategory,
)


class TestLegalHoldVault(unittest.TestCase):

    def setUp(self):
        self.tenant_id = "tenant_apex_holdings"
        self.vault = LegalHoldVault(tenant_id=self.tenant_id)

    def test_create_matter_and_lock_artifact(self):
        matter = self.vault.create_legal_matter(
            case_number="CIV-2026-9941",
            title="Securities Investigation Hold",
            description="Preserve all board meeting recordings and chat logs",
            jurisdiction="US District Court S.D.N.Y.",
            issuing_authority="SEC Enforcement Division",
            custodian_user_ids=["usr_cfo_1", "usr_ceo_1"],
        )

        self.assertEqual(matter.status, MatterStatus.ACTIVE)
        self.assertIn("usr_cfo_1", matter.custodians)

        # Lock a board meeting recording artifact
        video_bytes = b"FAKE_ENCRYPTED_MP4_VIDEO_STREAM_BYTES"
        art = self.vault.lock_artifact(
            matter_id=matter.matter_id,
            category=ResourceCategory.RECORDING,
            resource_id="rec_board_q3_2026",
            owner_user_id="usr_cfo_1",
            content_bytes=video_bytes,
            content_uri="s3://elevateiq-vault/apex/rec_board_q3.mp4",
        )

        self.assertEqual(art.sha256_hash, hashlib.sha256(video_bytes).hexdigest())
        self.assertTrue(art.is_locked)

        # Anti-spoliation test: resource must be locked
        self.assertTrue(self.vault.is_resource_locked("rec_board_q3_2026"))
        can_del, reason = self.vault.can_delete_resource("rec_board_q3_2026")
        self.assertFalse(can_del)
        self.assertIn("RESOURCE_LOCKED_BY_LEGAL_HOLD", reason)

    def test_overlapping_concurrent_matters(self):
        # Create Matter 1 (DOJ)
        m1 = self.vault.create_legal_matter(
            case_number="DOJ-2026-001",
            title="Antitrust Inquiry",
            description="DOJ Hold",
            jurisdiction="US District Court D.D.C.",
            issuing_authority="DOJ",
            custodian_user_ids=["usr_exec_1"],
        )

        # Create Matter 2 (Civil Litigation)
        m2 = self.vault.create_legal_matter(
            case_number="CIV-2026-7788",
            title="Shareholder Derivative Suit",
            description="Civil Hold",
            jurisdiction="Delaware Court of Chancery",
            issuing_authority="Court of Chancery",
            custodian_user_ids=["usr_exec_1"],
        )

        # Lock same transcript under both matters
        transcript_bytes = b"EXECUTIVE_TRANSCRIPT_TRANSCRIPTION_DATA"
        self.vault.lock_artifact(m1.matter_id, ResourceCategory.TRANSCRIPT, "tx_exec_101", "usr_exec_1", transcript_bytes, "s3://tx1.json")
        self.vault.lock_artifact(m2.matter_id, ResourceCategory.TRANSCRIPT, "tx_exec_101", "usr_exec_1", transcript_bytes, "s3://tx1.json")

        # Release Matter 1
        self.vault.release_legal_matter(m1.matter_id, released_by="General Counsel", reason="DOJ inquiry closed without action")
        self.assertEqual(m1.status, MatterStatus.RELEASED)

        # Resource MUST STILL BE LOCKED because Matter 2 is still active!
        self.assertTrue(self.vault.is_resource_locked("tx_exec_101"))
        can_del, _ = self.vault.can_delete_resource("tx_exec_101")
        self.assertFalse(can_del)

        # Now release Matter 2
        self.vault.release_legal_matter(m2.matter_id, released_by="Special Litigation Committee", reason="Settlement executed")
        self.assertFalse(self.vault.is_resource_locked("tx_exec_101"))
        can_del_final, _ = self.vault.can_delete_resource("tx_exec_101")
        self.assertTrue(can_del_final)

    def test_e_discovery_manifest_generation(self):
        matter = self.vault.create_legal_matter(
            case_number="SEC-2026-5544",
            title="Insider Trading Investigation",
            description="Hold on executive chat logs",
            jurisdiction="SEC NYRO",
            issuing_authority="SEC",
            custodian_user_ids=["usr_vp_sales"],
        )

        # Lock 2 artifacts
        self.vault.lock_artifact(matter.matter_id, ResourceCategory.CHAT_MESSAGE, "chat_msg_1", "usr_vp_sales", b"chat 1", "s3://c1")
        self.vault.lock_artifact(matter.matter_id, ResourceCategory.CHAT_MESSAGE, "chat_msg_2", "usr_vp_sales", b"chat 2", "s3://c2")

        manifest = self.vault.generate_e_discovery_manifest(matter.matter_id)
        self.assertEqual(manifest.case_number, "SEC-2026-5544")
        self.assertEqual(manifest.total_artifacts, 2)
        self.assertIsNotNone(manifest.manifest_sha256)
        self.assertEqual(len(manifest.artifact_hashes), 2)


if __name__ == "__main__":
    unittest.main()
