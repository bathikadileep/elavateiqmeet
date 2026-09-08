"""
ElevateIQ — SIP / PSTN Trunking Gateway Service
=================================================
Implements RFC 3261 Session Initiation Protocol (SIP) User Agent Server (UAS)
and PSTN audio bridge for telephone dial-in and dial-out meeting participation.
Handles SDP negotiation, DTMF PIN collection (RFC 4733), and IVR audio prompts.
"""

from __future__ import annotations

import enum
import hashlib
import logging
import random
import re
import secrets
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

log = logging.getLogger("elevateiq.services.media.sip")


class SIPCallState(str, enum.Enum):
    """RFC 3261 SIP Call State Machine."""
    IDLE = "IDLE"
    INVITE_RECEIVED = "INVITE_RECEIVED"
    PROCEEDING = "PROCEEDING"       # 100 Trying
    RINGING = "RINGING"             # 180 Ringing
    EARLY_MEDIA = "EARLY_MEDIA"     # 183 Session Progress
    CONNECTED = "CONNECTED"         # 200 OK & ACK received
    ON_HOLD = "ON_HOLD"
    DISCONNECTING = "DISCONNECTING" # BYE sent / received
    TERMINATED = "TERMINATED"       # Call ended


class AudioCodec(str, enum.Enum):
    """Negotiated VoIP Audio Codecs."""
    OPUS = "opus/48000/2"
    PCMU = "PCMU/8000"              # G.711 u-law (North America PSTN)
    PCMA = "PCMA/8000"              # G.711 a-law (Europe/International PSTN)
    G722 = "G722/8000"              # Wideband HD Voice
    TELEPHONE_EVENT = "telephone-event/8000"  # RFC 2833 / 4733 DTMF


@dataclass
class SDPDescriptor:
    """Session Description Protocol (SDP) Representation."""
    session_id: str
    session_version: int
    originator: str
    connection_ip: str
    audio_port: int
    supported_codecs: List[AudioCodec]
    crypto_suite: Optional[str] = "AES_CM_128_HMAC_SHA1_80"
    crypto_key_base64: Optional[str] = None
    ptime_ms: int = 20

    def serialize(self) -> str:
        """Render standard RFC 4566 SDP message body."""
        lines = [
            "v=0",
            f"o=- {self.session_id} {self.session_version} IN IP4 {self.connection_ip}",
            "s=ElevateIQ SIP Gateway",
            f"c=IN IP4 {self.connection_ip}",
            "t=0 0",
            f"m=audio {self.audio_port} RTP/SAVP 111 0 8 9 101",
            "a=rtpmap:111 opus/48000/2",
            "a=fmtp:111 minptime=10;useinbandfec=1",
            "a=rtpmap:0 PCMU/8000",
            "a=rtpmap:8 PCMA/8000",
            "a=rtpmap:9 G722/8000",
            "a=rtpmap:101 telephone-event/8000",
            "a=fmtp:101 0-16",
            f"a=ptime:{self.ptime_ms}",
            "a=sendrecv",
        ]
        if self.crypto_key_base64:
            lines.append(f"a=crypto:1 {self.crypto_suite} inline:{self.crypto_key_base64}")
        return "\r\n".join(lines) + "\r\n"

    @classmethod
    def parse(cls, raw_sdp: str) -> "SDPDescriptor":
        """Parse incoming SDP offer."""
        conn_ip = "127.0.0.1"
        audio_port = 10000
        codecs: List[AudioCodec] = []

        for line in raw_sdp.splitlines():
            line = line.strip()
            if line.startswith("c=IN IP4"):
                parts = line.split()
                if len(parts) >= 3:
                    conn_ip = parts[2]
            elif line.startswith("m=audio"):
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        audio_port = int(parts[1])
                    except ValueError:
                        pass
            elif line.startswith("a=rtpmap:"):
                rtp_entry = line[9:].strip()
                for c in AudioCodec:
                    if c.value.lower() in rtp_entry.lower():
                        codecs.append(c)

        if not codecs:
            codecs = [AudioCodec.PCMU, AudioCodec.TELEPHONE_EVENT]

        return cls(
            session_id=str(int(time.time())),
            session_version=1,
            originator="elevateiq-uas",
            connection_ip=conn_ip,
            audio_port=audio_port,
            supported_codecs=codecs,
        )


@dataclass
class SIPCallSession:
    """Active SIP Inbound / Outbound Call Session."""
    call_id: str
    from_uri: str
    to_uri: str
    caller_caller_id: str
    remote_ip: str
    state: SIPCallState = SIPCallState.IDLE
    meeting_id: Optional[str] = None
    entered_pin: str = ""
    is_authenticated: bool = False
    start_time: float = field(default_factory=time.time)
    connected_time: Optional[float] = None
    remote_sdp: Optional[SDPDescriptor] = None
    local_sdp: Optional[SDPDescriptor] = None
    dtmf_buffer: List[str] = field(default_factory=list)
    jitter_ms: float = 0.0
    packets_lost: int = 0
    rtp_rx_count: int = 0
    rtp_tx_count: int = 0

    @property
    def duration_seconds(self) -> float:
        if not self.connected_time:
            return 0.0
        return time.time() - self.connected_time


class SIPTrunkingGateway:
    """
    SIP/PSTN Conference Bridge Gateway.
    Allows telephone callers to dial into ElevateIQ rooms via E.164 phone numbers.
    """

    def __init__(self, bind_ip: str = "0.0.0.0", sip_port: int = 5060):
        self.bind_ip = bind_ip
        self.sip_port = sip_port
        self._active_calls: Dict[str, SIPCallSession] = {}
        self._room_pin_cache: Dict[str, str] = {}  # meeting_id -> 6-digit PIN
        self._pin_to_room: Dict[str, str] = {}     # 6-digit PIN -> meeting_id

    # -------------------------------------------------------------------------
    # Conference Room PIN Registry
    # -------------------------------------------------------------------------

    def register_meeting_dialin_pin(self, meeting_id: str, pin: Optional[str] = None) -> str:
        """Assign a unique 6-digit dial-in PIN to a meeting."""
        if not pin:
            pin = f"{random.randint(100000, 999999)}"
        self._room_pin_cache[meeting_id] = pin
        self._pin_to_room[pin] = meeting_id
        log.info("Registered Dial-In PIN '%s' for meeting %s", pin, meeting_id)
        return pin

    def get_meeting_for_pin(self, pin: str) -> Optional[str]:
        """Resolve entered conference PIN to internal meeting ID."""
        return self._pin_to_room.get(pin.strip("#* \t\r\n"))

    # -------------------------------------------------------------------------
    # SIP Signaling State Machine
    # -------------------------------------------------------------------------

    def handle_inbound_invite(
        self,
        call_id: str,
        from_uri: str,
        to_uri: str,
        remote_ip: str,
        raw_sdp: str
    ) -> Tuple[int, str, Optional[str]]:
        """
        Process an inbound SIP INVITE request.
        Returns: (sip_status_code, status_reason, response_sdp_or_none)
        """
        if call_id in self._active_calls:
            session = self._active_calls[call_id]
            if session.state in (SIPCallState.RINGING, SIPCallState.CONNECTED):
                return 200, "OK", session.local_sdp.serialize() if session.local_sdp else None

        # Extract caller ID from From header: sip:+15550192834@trunk.sip.provider.com
        caller_match = re.search(r"sip:([+0-9a-zA-Z]+)@", from_uri)
        caller_id = caller_match.group(1) if caller_match else "Anonymous"

        remote_sdp = SDPDescriptor.parse(raw_sdp)
        local_port = random.randint(20000, 40000)
        local_sdp = SDPDescriptor(
            session_id=str(int(time.time())),
            session_version=1,
            originator="elevateiq-bridge",
            connection_ip=self.bind_ip if self.bind_ip != "0.0.0.0" else "127.0.0.1",
            audio_port=local_port,
            supported_codecs=[AudioCodec.OPUS, AudioCodec.PCMU, AudioCodec.PCMA, AudioCodec.TELEPHONE_EVENT],
            crypto_key_base64=secrets.token_urlsafe(30),
        )

        session = SIPCallSession(
            call_id=call_id,
            from_uri=from_uri,
            to_uri=to_uri,
            caller_caller_id=caller_id,
            remote_ip=remote_ip,
            state=SIPCallState.CONNECTED,
            connected_time=time.time(),
            remote_sdp=remote_sdp,
            local_sdp=local_sdp,
        )

        self._active_calls[call_id] = session
        log.info("SIP UAS: Accepted INVITE from %s (Call-ID: %s, Assigned Port: %d)",
                 caller_id, call_id, local_port)

        return 200, "OK", local_sdp.serialize()

    def handle_dtmf_digit(self, call_id: str, digit: str) -> Dict[str, Any]:
        """
        Receive DTMF digit from RFC 2833 / RFC 4733 RTP packet or SIP INFO message.
        Accumulates digits until pound ('#') key confirms conference PIN entry.
        """
        session = self._active_calls.get(call_id)
        if not session:
            return {"error": "Call not found", "status": "UNKNOWN_CALL"}

        clean_digit = digit.strip()
        if not clean_digit:
            return {"status": "IGNORED"}

        session.dtmf_buffer.append(clean_digit)
        log.debug("SIP Call %s received DTMF digit: '%s' (Buffer: %s)",
                  call_id, clean_digit, "".join(session.dtmf_buffer))

        # Check for terminator '#'
        if clean_digit == "#":
            entered_code = "".join(session.dtmf_buffer[:-1])  # Exclude '#'
            session.dtmf_buffer.clear()
            session.entered_pin = entered_code

            meeting_id = self.get_meeting_for_pin(entered_code)
            if meeting_id:
                session.meeting_id = meeting_id
                session.is_authenticated = True
                log.info("SIP Call %s authenticated into meeting %s via PIN %s",
                         call_id, meeting_id, entered_code)
                return {
                    "status": "AUTHENTICATED",
                    "meeting_id": meeting_id,
                    "prompt": "You are now joining the meeting.",
                }
            else:
                session.is_authenticated = False
                log.warning("SIP Call %s entered INVALID PIN '%s'", call_id, entered_code)
                return {
                    "status": "INVALID_PIN",
                    "entered_code": entered_code,
                    "prompt": "That meeting code is invalid. Please try again.",
                }

        return {
            "status": "COLLECTING",
            "digits_received": len(session.dtmf_buffer),
        }

    def handle_inbound_bye(self, call_id: str) -> Tuple[int, str]:
        """Process SIP BYE request and teardown call session."""
        session = self._active_calls.pop(call_id, None)
        if not session:
            return 481, "Call/Transaction Does Not Exist"

        session.state = SIPCallState.TERMINATED
        duration = session.duration_seconds
        log.info("SIP Call %s terminated by caller %s (Duration: %.2fs, Rx Packets: %d)",
                 call_id, session.caller_caller_id, duration, session.rtp_rx_count)
        return 200, "OK"

    def terminate_call(self, call_id: str, reason: str = "Host Ended Meeting") -> bool:
        """Server-initiated teardown of SIP caller."""
        session = self._active_calls.pop(call_id, None)
        if not session:
            return False
        session.state = SIPCallState.TERMINATED
        log.info("Server terminated SIP call %s: %s", call_id, reason)
        return True

    # -------------------------------------------------------------------------
    # Telemetry & Diagnostics
    # -------------------------------------------------------------------------

    def record_rtp_telemetry(self, call_id: str, rx_packets: int, tx_packets: int, lost: int, jitter_ms: float):
        """Update live RTP quality metrics for VoIP call."""
        session = self._active_calls.get(call_id)
        if session:
            session.rtp_rx_count += rx_packets
            session.rtp_tx_count += tx_packets
            session.packets_lost += lost
            session.jitter_ms = jitter_ms

    def get_active_calls_summary(self) -> List[Dict[str, Any]]:
        """Return list of active SIP bridge sessions."""
        return [
            {
                "call_id": s.call_id,
                "caller_id": s.caller_caller_id,
                "from_uri": s.from_uri,
                "meeting_id": s.meeting_id,
                "is_authenticated": s.is_authenticated,
                "duration_seconds": round(s.duration_seconds, 1),
                "state": s.state.value,
                "packets_rx": s.rtp_rx_count,
                "packets_lost": s.packets_lost,
                "jitter_ms": s.jitter_ms,
            }
            for s in self._active_calls.values()
        ]
