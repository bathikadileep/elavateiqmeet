"""
Tests for Enterprise Audit Log Immutability Ledger & Merkle Tree Cryptographic Anchor
=====================================================================================
Validates RFC 6962 Merkle tree construction, cryptographic inclusion proof verification,
block chain linkage, and tamper detection.
"""

import hashlib
import unittest
from backend.services.enterprise.merkle_audit_ledger import (
    MerkleTreeEngine,
    MerkleAuditLedger,
    AuditRecord,
    MerkleInclusionProof,
)


class TestMerkleAuditLedger(unittest.TestCase):

    def setUp(self):
        self.tenant_id = "tenant_cyber_defense"
        self.ledger = MerkleAuditLedger(tenant_id=self.tenant_id)

    def test_merkle_tree_math_and_inclusion_proof_even_leaves(self):
        leaf_hashes = [
            hashlib.sha256(f"leaf_{i}".encode()).hexdigest() for i in range(4)
        ]
        root = MerkleTreeEngine.compute_root_from_leaves(leaf_hashes)
        self.assertIsNotNone(root)
        self.assertEqual(len(root), 64)

        # Generate and verify proof for leaf 2
        proof = MerkleTreeEngine.generate_inclusion_proof(leaf_hashes, target_index=2)
        self.assertEqual(proof.leaf_index, 2)
        self.assertEqual(proof.root_hash, root)
        self.assertTrue(MerkleTreeEngine.verify_inclusion_proof(proof))

    def test_merkle_tree_odd_number_of_leaves(self):
        leaf_hashes = [
            hashlib.sha256(f"odd_leaf_{i}".encode()).hexdigest() for i in range(5)
        ]
        root = MerkleTreeEngine.compute_root_from_leaves(leaf_hashes)

        # Verify proof for last leaf (index 4)
        proof = MerkleTreeEngine.generate_inclusion_proof(leaf_hashes, target_index=4)
        self.assertTrue(MerkleTreeEngine.verify_inclusion_proof(proof))

    def test_tampered_inclusion_proof_rejected(self):
        leaf_hashes = [
            hashlib.sha256(f"entry_{i}".encode()).hexdigest() for i in range(4)
        ]
        proof = MerkleTreeEngine.generate_inclusion_proof(leaf_hashes, target_index=1)

        # Alter proof leaf hash
        tampered_proof = MerkleInclusionProof(
            leaf_index=proof.leaf_index,
            tree_size=proof.tree_size,
            leaf_hash=hashlib.sha256(b"malicious_tampered_content").hexdigest(),
            root_hash=proof.root_hash,
            audit_path=proof.audit_path,
        )
        self.assertFalse(MerkleTreeEngine.verify_inclusion_proof(tampered_proof))

    def test_audit_ledger_event_recording_and_block_sealing(self):
        # Record 3 events
        e1 = self.ledger.record_event("user.login", "usr_101", "neo@matrix.io", "Session", "ses_99", event_id="evt_1")
        e2 = self.ledger.record_event("meeting.create", "usr_101", "neo@matrix.io", "Room", "room_z1", event_id="evt_2")
        e3 = self.ledger.record_event("recording.start", "usr_101", "neo@matrix.io", "Recording", "rec_a2", event_id="evt_3")

        # Seal block #0
        block_0 = self.ledger.seal_current_block()
        self.assertIsNotNone(block_0)
        self.assertEqual(block_0.block_index, 0)
        self.assertEqual(block_0.record_count, 3)
        self.assertEqual(block_0.previous_block_hash, "0" * 64)

        # Verify inclusion proof for event 2
        proof = self.ledger.get_inclusion_proof_for_event("evt_2")
        self.assertIsNotNone(proof)
        self.assertEqual(proof.root_hash, block_0.merkle_root)
        self.assertTrue(MerkleTreeEngine.verify_inclusion_proof(proof))

        # Record 2 more events and seal block #1
        self.ledger.record_event("role.grant", "usr_adm", "admin@matrix.io", "User", "usr_101")
        self.ledger.record_event("export.audit", "usr_adm", "admin@matrix.io", "Audit", "all")
        block_1 = self.ledger.seal_current_block()
        self.assertEqual(block_1.block_index, 1)

        # Verify cryptographic chain integrity across blocks
        valid, err = self.ledger.verify_ledger_chain_integrity()
        self.assertTrue(valid)
        self.assertIsNone(err)

    def test_chain_tamper_detection(self):
        self.ledger.record_event("login", "u1", "u1@test.com", "App", "a1")
        self.ledger.seal_current_block()
        self.ledger.record_event("logout", "u1", "u1@test.com", "App", "a1")
        self.ledger.seal_current_block()

        # Malicious actor tampers with root of block 0
        self.ledger.anchored_blocks[0].merkle_root = hashlib.sha256(b"forged_root").hexdigest()

        valid, err = self.ledger.verify_ledger_chain_integrity()
        self.assertFalse(valid)
        self.assertIn("Invalid signature on block index 0", err)


if __name__ == "__main__":
    unittest.main()
