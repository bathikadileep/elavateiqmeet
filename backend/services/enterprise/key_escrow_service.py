"""
Media Encryption Key Escrow & Enterprise PKI Authority Service
==============================================================
Implements cryptographic threshold key escrow (Shamir's Secret Sharing over GF(p))
and enterprise DTLS/WebRTC PKI certificate management for regulatory compliance
(FINRA, SEC Rule 17a-4, HIPAA, GDPR e-Discovery).

Allows end-to-end encrypted meeting recordings to be held in multi-custodian escrow
where at least `k` of `n` authorized enterprise trustees must combine cryptographic
shares to reconstruct a session decryption key.
"""

from __future__ import annotations

import base64
import enum
import hashlib
import hmac
import logging
import os
import secrets
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger("elevateiq.services.enterprise.key_escrow")

# Standard 256-bit prime for finite field polynomial arithmetic
# 2^256 - 189 (Largest prime below 2^256)
FIELD_PRIME = 115792089237316195423570985008687907853269984665640564039457584007913129639747


class EscrowStatus(str, enum.Enum):
    LOCKED = "LOCKED"
    PENDING_APPROVALS = "PENDING_APPROVALS"
    QUORUM_MET = "QUORUM_MET"
    RECONSTRUCTED = "RECONSTRUCTED"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"


class TrusteeRole(str, enum.Enum):
    CHIEF_LEGAL_OFFICER = "CHIEF_LEGAL_OFFICER"
    DATA_PROTECTION_OFFICER = "DATA_PROTECTION_OFFICER"
    SECURITY_OPERATIONS_LEAD = "SECURITY_OPERATIONS_LEAD"
    COMPLIANCE_AUDITOR = "COMPLIANCE_AUDITOR"
    EXTERNAL_ESCROW_AGENT = "EXTERNAL_ESCROW_AGENT"


@dataclass
class KeyShare:
    """A cryptographic share (x, y) generated via Shamir's polynomial."""
    share_index: int  # x coordinate (1-indexed)
    share_value: int  # y coordinate (f(x) mod p)
    trustee_id: str
    fingerprint: str  # SHA-256 of share value for integrity check

    def to_dict(self) -> Dict[str, Any]:
        return {
            "share_index": self.share_index,
            "share_value_b64": base64.b64encode(
                self.share_value.to_bytes((self.share_value.bit_length() + 7) // 8, byteorder="big")
            ).decode("ascii"),
            "trustee_id": self.trustee_id,
            "fingerprint": self.fingerprint,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KeyShare":
        val_bytes = base64.b64decode(data["share_value_b64"])
        val_int = int.from_bytes(val_bytes, byteorder="big")
        return cls(
            share_index=int(data["share_index"]),
            share_value=val_int,
            trustee_id=data["trustee_id"],
            fingerprint=data["fingerprint"],
        )


@dataclass
class Trustee:
    """Authorized enterprise custodian holding an escrow share."""
    trustee_id: str
    tenant_id: str
    email: str
    role: TrusteeRole
    public_key_pem: str
    is_active: bool = True
    assigned_at: float = field(default_factory=time.time)


@dataclass
class EscrowSessionRecord:
    """Escrow metadata and share custody ledger for an encrypted meeting session."""
    session_id: str
    tenant_id: str
    threshold_k: int
    total_shares_n: int
    status: EscrowStatus
    created_at: float
    expires_at: float
    key_fingerprint: str  # Hash of original session master key
    trustee_ids: List[str]
    shares: Dict[str, KeyShare] = field(default_factory=dict)  # trustee_id -> KeyShare
    approval_tokens: Dict[str, Dict[str, Any]] = field(default_factory=dict)  # trustee_id -> approval info
    reconstructed_at: Optional[float] = None
    audit_trail: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class CertificateRecord:
    """Managed DTLS/WebRTC client or media node identity certificate."""
    cert_id: str
    tenant_id: str
    common_name: str
    fingerprint_sha256: str
    serial_number: str
    issued_at: float
    expires_at: float
    is_revoked: bool = False
    revocation_reason: Optional[str] = None


class ShamirThresholdMath:
    """
    Finite Field Galois Arithmetic over large prime modulo P (2^256 - 189).
    Implements secure polynomial evaluation and Lagrange polynomial interpolation.
    """

    @staticmethod
    def mod_inverse(a: int, p: int = FIELD_PRIME) -> int:
        """Computes modular multiplicative inverse using Extended Euclidean Algorithm."""
        if a % p == 0:
            raise ValueError("Zero has no modular inverse")
        # pow(a, p - 2, p) via Fermat's Little Theorem
        return pow(a, p - 2, p)

    @classmethod
    def evaluate_polynomial(cls, coefficients: List[int], x: int, p: int = FIELD_PRIME) -> int:
        """Evaluates f(x) = c0 + c1*x + c2*x^2 + ... mod p using Horner's method."""
        y = 0
        for coeff in reversed(coefficients):
            y = (y * x + coeff) % p
        return y

    @classmethod
    def split_secret(cls, secret_bytes: bytes, k: int, n: int, p: int = FIELD_PRIME) -> List[Tuple[int, int]]:
        """
        Splits a secret into n shares such that any k shares can reconstruct it.
        Returns list of (x, y) coordinates for x in [1..n].
        """
        if k > n:
            raise ValueError(f"Threshold k ({k}) cannot exceed total shares n ({n})")
        if k < 2:
            raise ValueError("Threshold k must be at least 2")

        secret_int = int.from_bytes(secret_bytes, byteorder="big")
        if secret_int >= p:
            raise ValueError("Secret integer exceeds finite field prime modulus")

        # Random polynomial: f(x) = secret + a1*x + a2*x^2 + ... + a_(k-1)*x^(k-1)
        coefficients = [secret_int]
        for _ in range(k - 1):
            coefficients.append(secrets.randbelow(p))

        shares: List[Tuple[int, int]] = []
        for x in range(1, n + 1):
            y = cls.evaluate_polynomial(coefficients, x, p)
            shares.append((x, y))

        return shares

    @classmethod
    def reconstruct_secret(cls, shares: List[Tuple[int, int]], p: int = FIELD_PRIME) -> bytes:
        """
        Reconstructs secret f(0) using Lagrange interpolation from any k shares:
        L_i(0) = product_{j != i} (x_j / (x_j - x_i)) mod p
        Secret = sum_{i} (y_i * L_i(0)) mod p
        """
        if len(shares) < 2:
            raise ValueError("Reconstruction requires at least 2 shares")

        xs = [s[0] for s in shares]
        if len(xs) != len(set(xs)):
            raise ValueError("Duplicate share indices provided")

        secret_int = 0
        k = len(shares)

        for i in range(k):
            xi, yi = shares[i]
            numerator = 1
            denominator = 1

            for j in range(k):
                if i == j:
                    continue
                xj, _ = shares[j]
                numerator = (numerator * (-xj)) % p
                denominator = (denominator * (xi - xj)) % p

            inv_denominator = cls.mod_inverse(denominator, p)
            lagrange_basis = (numerator * inv_denominator) % p
            term = (yi * lagrange_basis) % p
            secret_int = (secret_int + term) % p

        # Convert back to standard 32-byte representation (for 256-bit AES keys)
        byte_len = (secret_int.bit_length() + 7) // 8
        if byte_len == 0:
            byte_len = 32
        else:
            byte_len = max(byte_len, 32)
        return secret_int.to_bytes(byte_len, byteorder="big")[-32:]


class KeyEscrowService:
    """
    Enterprise Key Escrow and PKI Certificate Lifecycle Management.
    Provides threshold key generation, custody splitting, trustee approval verification,
    and audit verification for secure enterprise collaboration sessions.
    """

    def __init__(self) -> None:
        self.trustees: Dict[str, Trustee] = {}  # trustee_id -> Trustee
        self.sessions: Dict[str, EscrowSessionRecord] = {}  # session_id -> Record
        self.certificates: Dict[str, CertificateRecord] = {}  # cert_id -> Record
        self.crl: Set[str] = set()  # Set of revoked serial numbers / cert_ids

    # -------------------------------------------------------------------------
    # Trustee Management
    # -------------------------------------------------------------------------
    def register_trustee(
        self,
        tenant_id: str,
        email: str,
        role: TrusteeRole,
        public_key_pem: str = ""
    ) -> Trustee:
        """Registers an authorized enterprise custodian for key share custody."""
        trustee_id = f"trustee_{uuid.uuid4().hex[:12]}"
        trustee = Trustee(
            trustee_id=trustee_id,
            tenant_id=tenant_id,
            email=email,
            role=role,
            public_key_pem=public_key_pem or f"-----BEGIN PUBLIC KEY-----\nMOCK_{trustee_id}\n-----END PUBLIC KEY-----",
        )
        self.trustees[trustee_id] = trustee
        logger.info("Registered escrow trustee %s (%s) for tenant %s", trustee_id, email, tenant_id)
        return trustee

    def get_tenant_trustees(self, tenant_id: str, active_only: bool = True) -> List[Trustee]:
        return [
            t for t in self.trustees.values()
            if t.tenant_id == tenant_id and (not active_only or t.is_active)
        ]

    # -------------------------------------------------------------------------
    # Escrow Session Creation & Secret Splitting
    # -------------------------------------------------------------------------
    def create_escrow_session(
        self,
        session_id: str,
        tenant_id: str,
        threshold_k: int = 3,
        total_shares_n: int = 5,
        master_key_bytes: Optional[bytes] = None,
        retention_days: int = 90
    ) -> EscrowSessionRecord:
        """
        Creates an escrow session, splits the master encryption key into (k, n) shares,
        and assigns shares to registered tenant trustees.
        """
        if master_key_bytes is None:
            # Generate cryptographic 256-bit AES master key
            master_key_bytes = secrets.token_bytes(32)

        if len(master_key_bytes) != 32:
            raise ValueError("Master key must be exactly 32 bytes (256-bit AES)")

        trustees = self.get_tenant_trustees(tenant_id)
        if len(trustees) < total_shares_n:
            raise ValueError(
                f"Tenant {tenant_id} has only {len(trustees)} active trustees, but {total_shares_n} shares required"
            )

        # Generate Shamir shares
        raw_shares = ShamirThresholdMath.split_secret(master_key_bytes, threshold_k, total_shares_n)
        key_fp = hashlib.sha256(master_key_bytes).hexdigest()

        selected_trustees = trustees[:total_shares_n]
        assigned_shares: Dict[str, KeyShare] = {}

        for idx, (x, y) in enumerate(raw_shares):
            trustee = selected_trustees[idx]
            y_bytes = y.to_bytes((y.bit_length() + 7) // 8, byteorder="big")
            share_fp = hashlib.sha256(y_bytes).hexdigest()
            assigned_shares[trustee.trustee_id] = KeyShare(
                share_index=x,
                share_value=y,
                trustee_id=trustee.trustee_id,
                fingerprint=share_fp,
            )

        now = time.time()
        record = EscrowSessionRecord(
            session_id=session_id,
            tenant_id=tenant_id,
            threshold_k=threshold_k,
            total_shares_n=total_shares_n,
            status=EscrowStatus.LOCKED,
            created_at=now,
            expires_at=now + (retention_days * 86400),
            key_fingerprint=key_fp,
            trustee_ids=[t.trustee_id for t in selected_trustees],
            shares=assigned_shares,
        )

        record.audit_trail.append({
            "event": "ESCROW_CREATED",
            "timestamp": now,
            "threshold_k": threshold_k,
            "total_shares_n": total_shares_n,
            "key_fingerprint": key_fp,
        })

        self.sessions[session_id] = record
        logger.info(
            "Created escrow session %s (Tenant: %s, Threshold: %d/%d, KeyFP: %s)",
            session_id, tenant_id, threshold_k, total_shares_n, key_fp[:12]
        )
        return record

    # -------------------------------------------------------------------------
    # Trustee Approval & Quorum Recombination
    # -------------------------------------------------------------------------
    def submit_trustee_approval(
        self,
        session_id: str,
        trustee_id: str,
        authorization_reason: str,
        signature_b64: str = ""
    ) -> EscrowSessionRecord:
        """
        Records a trustee's formal cryptographic approval to release their share for decryption.
        """
        record = self.sessions.get(session_id)
        if not record:
            raise ValueError(f"Escrow session '{session_id}' not found")

        if trustee_id not in record.shares:
            raise ValueError(f"Trustee '{trustee_id}' is not an assigned custodian for session '{session_id}'")

        if record.status in (EscrowStatus.REVOKED, EscrowStatus.EXPIRED):
            raise ValueError(f"Cannot submit approval: session is {record.status.value}")

        now = time.time()
        record.approval_tokens[trustee_id] = {
            "approved_at": now,
            "reason": authorization_reason,
            "signature_b64": signature_b64 or base64.b64encode(b"MOCK_SIGNATURE").decode(),
        }

        record.audit_trail.append({
            "event": "TRUSTEE_APPROVED",
            "trustee_id": trustee_id,
            "reason": authorization_reason,
            "timestamp": now,
        })

        # Check if threshold k is reached
        if len(record.approval_tokens) >= record.threshold_k:
            record.status = EscrowStatus.QUORUM_MET
            logger.info("Escrow session %s reached trustee quorum (%d/%d approvals)", session_id, len(record.approval_tokens), record.threshold_k)
        else:
            record.status = EscrowStatus.PENDING_APPROVALS

        return record

    def reconstruct_escrow_key(self, session_id: str, requester_id: str) -> bytes:
        """
        Recombines the cryptographic shares of approving trustees to reconstitute
        the session master decryption key. Requires quorum.
        """
        record = self.sessions.get(session_id)
        if not record:
            raise ValueError(f"Escrow session '{session_id}' not found")

        if record.status != EscrowStatus.QUORUM_MET and len(record.approval_tokens) < record.threshold_k:
            raise ValueError(
                f"Quorum not met: required {record.threshold_k} approvals, but only {len(record.approval_tokens)} submitted"
            )

        # Gather shares from approving trustees
        participating_shares: List[Tuple[int, int]] = []
        for t_id in record.approval_tokens.keys():
            share_obj = record.shares.get(t_id)
            if share_obj:
                participating_shares.append((share_obj.share_index, share_obj.share_value))
            if len(participating_shares) == record.threshold_k:
                break

        reconstructed_key = ShamirThresholdMath.reconstruct_secret(participating_shares)

        # Integrity check against fingerprint
        calc_fp = hashlib.sha256(reconstructed_key).hexdigest()
        if calc_fp != record.key_fingerprint:
            raise ValueError("Reconstructed key failed cryptographic fingerprint integrity check!")

        record.status = EscrowStatus.RECONSTRUCTED
        record.reconstructed_at = time.time()
        record.audit_trail.append({
            "event": "KEY_RECONSTRUCTED",
            "requester_id": requester_id,
            "participating_trustees": list(record.approval_tokens.keys())[:record.threshold_k],
            "timestamp": record.reconstructed_at,
        })

        logger.warning("Session master key for %s successfully RECONSTRUCTED by %s", session_id, requester_id)
        return reconstructed_key

    # -------------------------------------------------------------------------
    # Enterprise PKI Certificate Authority
    # -------------------------------------------------------------------------
    def issue_webrtc_certificate(
        self,
        tenant_id: str,
        common_name: str,
        validity_days: int = 365
    ) -> CertificateRecord:
        """
        Issues an enterprise WebRTC media node or client DTLS certificate
        conforming to RFC 8122 with formatted SHA-256 fingerprint.
        """
        cert_id = f"cert_{uuid.uuid4().hex[:12]}"
        serial = f"{int(time.time() * 1000):x}-{secrets.token_hex(4)}"

        # Generate mock certificate bytes & compute RFC 8122 formatted fingerprint
        raw_cert_bytes = hashlib.sha256(f"{tenant_id}:{common_name}:{serial}".encode()).digest()
        fp_raw = hashlib.sha256(raw_cert_bytes).hexdigest().upper()
        # Format as standard XX:XX:XX:...
        fp_formatted = ":".join(fp_raw[i:i + 2] for i in range(0, len(fp_raw), 2))

        now = time.time()
        record = CertificateRecord(
            cert_id=cert_id,
            tenant_id=tenant_id,
            common_name=common_name,
            fingerprint_sha256=fp_formatted,
            serial_number=serial,
            issued_at=now,
            expires_at=now + (validity_days * 86400),
        )

        self.certificates[cert_id] = record
        logger.info("Issued WebRTC DTLS cert %s for CN=%s (Fingerprint: %s)", cert_id, common_name, fp_formatted[:24])
        return record

    def revoke_certificate(self, cert_id: str, reason: str = "KeyCompromise") -> bool:
        """Revokes a certificate and appends serial to Certificate Revocation List (CRL)."""
        cert = self.certificates.get(cert_id)
        if not cert:
            return False

        cert.is_revoked = True
        cert.revocation_reason = reason
        self.crl.add(cert.serial_number)
        logger.warning("Revoked certificate %s (Serial: %s, Reason: %s)", cert_id, cert.serial_number, reason)
        return True

    def verify_certificate_status(self, cert_id: str) -> Dict[str, Any]:
        """Checks certificate expiration and revocation status."""
        cert = self.certificates.get(cert_id)
        if not cert:
            return {"valid": False, "error": "Certificate not found"}

        now = time.time()
        if cert.is_revoked or cert.serial_number in self.crl:
            return {"valid": False, "error": "Certificate is revoked", "reason": cert.revocation_reason}

        if now > cert.expires_at:
            return {"valid": False, "error": "Certificate has expired"}

        return {
            "valid": True,
            "cert_id": cert.cert_id,
            "common_name": cert.common_name,
            "fingerprint": cert.fingerprint_sha256,
            "serial": cert.serial_number,
        }
