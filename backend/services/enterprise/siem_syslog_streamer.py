"""
ElevateIQ — Enterprise Audit Log Vault & SIEM Syslog Streamer (CEF / RFC 5424)
================================================================================
Formats security, compliance, and meeting audit records into Common Event Format (CEF)
and RFC 5424 Syslog standards. Manages buffered streaming to enterprise SIEM platforms
(Splunk, Datadog, QRadar, Sentinel) with cryptographic HMAC batch sealing.
"""

import time
import hmac
import hashlib
import json
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum

log = logging.getLogger("elevateiq.services.enterprise.siem")


class SiemSeverity(int, Enum):
    """CEF standard normalized severity levels (0-10)."""
    INFO = 1
    LOW = 3
    MEDIUM = 5
    HIGH = 8
    CRITICAL = 10


@dataclass
class SiemAuditEvent:
    """Represents a structured enterprise security or audit event."""
    event_id: str
    tenant_id: str
    event_class: str          # e.g., 'AUTH_MFA_FAILURE', 'E2EE_KEY_ROTATED', 'DLP_BLOCKED'
    event_name: str
    severity: SiemSeverity
    actor_id: str
    actor_ip: str
    room_code: Optional[str] = None
    target_resource: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


@dataclass
class LogBatchSeal:
    """Cryptographic seal for a batch of forwarded audit logs."""
    batch_id: str
    event_count: int
    first_event_id: str
    last_event_id: str
    merkle_root: str
    hmac_signature: str
    timestamp: float = field(default_factory=time.time)


class SiemSyslogStreamer:
    """
    Enterprise SIEM Forwarding Engine & Log Vault.
    Converts events to CEF / RFC 5424 and manages buffered delivery queues.
    """

    CEF_VENDOR = "ElevateIQ"
    CEF_PRODUCT = "MeetingPlatform"
    CEF_VERSION = "2.4.0"

    def __init__(self, hmac_key: str = "elevateiq-siem-seal-key-2026", max_batch_size: int = 50):
        self.hmac_key = hmac_key.encode("utf-8")
        self.max_batch_size = max_batch_size
        self.buffer: List[SiemAuditEvent] = []
        self.archived_batches: List[LogBatchSeal] = []

    def format_to_cef(self, event: SiemAuditEvent) -> str:
        """
        Format event into ArcSight Common Event Format (CEF).
        Format: CEF:Version|Device Vendor|Device Product|Device Version|Signature ID|Name|Severity|Extension
        """
        # Escape pipe and backslash characters in header fields
        escaped_name = event.event_name.replace("\\", "\\\\").replace("|", "\\|")
        escaped_class = event.event_class.replace("\\", "\\\\").replace("|", "\\|")

        # Construct extension dictionary
        extensions = [
            f"actId={event.actor_id}",
            f"src={event.actor_ip}",
            f"deviceTenantId={event.tenant_id}",
            f"rt={int(event.timestamp * 1000)}"
        ]
        if event.room_code:
            extensions.append(f"cs1={event.room_code}")
            extensions.append("cs1Label=RoomCode")
        if event.target_resource:
            extensions.append(f"target={event.target_resource}")

        for k, v in sorted(event.details.items()):
            clean_k = k.replace(" ", "_")
            clean_v = str(v).replace("=", "\\=")
            extensions.append(f"cn1={clean_v}")
            extensions.append(f"cn1Label={clean_k}")

        ext_str = " ".join(extensions)

        return (
            f"CEF:0|{self.CEF_VENDOR}|{self.CEF_PRODUCT}|{self.CEF_VERSION}|"
            f"{escaped_class}|{escaped_name}|{event.severity.value}|{ext_str}"
        )

    def format_to_rfc5424(self, event: SiemAuditEvent, hostname: str = "elevateiq-core-edge") -> str:
        """
        Format event into RFC 5424 Syslog standard message.
        Format: <PRI>VERSION TIMESTAMP HOSTNAME APP-NAME PROCID MSGID STRUCTURED-DATA MSG
        """
        # Priority = Facility * 8 + Severity
        # Facility 10 = security/authorization messages
        pri = (10 * 8) + (10 - event.severity.value)
        iso_ts = time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime(event.timestamp))

        # Structured Data
        sd = (
            f'[audit@elevateiq '
            f'tenant="{event.tenant_id}" '
            f'actor="{event.actor_id}" '
            f'ip="{event.actor_ip}" '
            f'class="{event.event_class}"]'
        )

        msg = f"{event.event_name} - {json.dumps(event.details)}"

        return f"<{pri}>1 {iso_ts} {hostname} elevateiq-audit 1 {event.event_id} {sd} {msg}"

    def emit_event(
        self,
        tenant_id: str,
        event_class: str,
        event_name: str,
        severity: SiemSeverity,
        actor_id: str,
        actor_ip: str,
        room_code: Optional[str] = None,
        target_resource: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> SiemAuditEvent:
        """Record an event into the live streamer buffer."""
        event_id = f"evt_{int(time.time() * 1000)}_{len(self.buffer) + 1}"
        event = SiemAuditEvent(
            event_id=event_id,
            tenant_id=tenant_id,
            event_class=event_class,
            event_name=event_name,
            severity=severity,
            actor_id=actor_id,
            actor_ip=actor_ip,
            room_code=room_code,
            target_resource=target_resource,
            details=details or {}
        )
        self.buffer.append(event)
        log.info("SiemSyslog: Emitted audit event %s (%s) for tenant %s",
                 event_id, event_class, tenant_id)
        return event

    def seal_and_flush_batch(self) -> Optional[Tuple[LogBatchSeal, List[str]]]:
        """
        Seal the currently buffered events into an immutable cryptographic batch.
        Computes Merkle hash chain and returns (LogBatchSeal, formatted_cef_lines).
        """
        if not self.buffer:
            return None

        events_to_flush = list(self.buffer)
        self.buffer.clear()

        # Compute Merkle tree root hash of event payloads
        leaf_hashes = [
            hashlib.sha256(json.dumps({
                "id": e.event_id,
                "class": e.event_class,
                "actor": e.actor_id,
                "ts": e.timestamp
            }, sort_keys=True).encode("utf-8")).digest()
            for e in events_to_flush
        ]

        current_level = leaf_hashes
        while len(current_level) > 1:
            next_level = []
            for i in range(0, len(current_level), 2):
                if i + 1 < len(current_level):
                    combined = current_level[i] + current_level[i + 1]
                else:
                    combined = current_level[i] + current_level[i]
                next_level.append(hashlib.sha256(combined).digest())
            current_level = next_level

        merkle_root = current_level[0].hex()

        # Sign the Merkle root
        batch_id = f"batch_{int(time.time())}_{len(self.archived_batches) + 1}"
        sign_payload = f"{batch_id}:{len(events_to_flush)}:{merkle_root}".encode("utf-8")
        signature = hmac.new(self.hmac_key, sign_payload, hashlib.sha256).hexdigest()

        seal = LogBatchSeal(
            batch_id=batch_id,
            event_count=len(events_to_flush),
            first_event_id=events_to_flush[0].event_id,
            last_event_id=events_to_flush[-1].event_id,
            merkle_root=merkle_root,
            hmac_signature=signature
        )
        self.archived_batches.append(seal)

        cef_lines = [self.format_to_cef(e) for e in events_to_flush]
        log.info("SiemSyslog: Sealed batch %s (%d events, Merkle: %s)",
                 batch_id, len(events_to_flush), merkle_root[:16])
        return seal, cef_lines
