"""
ElevateIQ — RFC 6184 H.264 Video RTP Depacketizer Engine
==========================================================
Reassembles H.264 / AVC video streams received over WebRTC RTP payloads.
Supports Single NAL Units, STAP-A Aggregation Packets, and FU-A Fragmentation Units.
Produces clean Annex B formatted byte streams for hardware video decoders.
"""

from __future__ import annotations

import enum
import logging
import struct
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

log = logging.getLogger("elevateiq.services.media.h264")

# Standard Annex B NAL start code prefix
ANNEX_B_START_CODE = b"\x00\x00\x00\x01"


class NALUnitType(int, enum.Enum):
    """H.264 NAL Unit Types (RFC 6184 Table 1)."""
    UNSPECIFIED = 0
    NON_IDR_SLICE = 1          # P-frame / B-frame slice
    DATA_PARTITION_A = 2
    DATA_PARTITION_B = 3
    DATA_PARTITION_C = 4
    IDR_SLICE = 5              # Keyframe (Instantaneous Decoding Refresh)
    SEI = 6                    # Supplemental Enhancement Information
    SPS = 7                    # Sequence Parameter Set
    PPS = 8                    # Picture Parameter Set
    AUD = 9                    # Access Unit Delimiter
    END_OF_SEQUENCE = 10
    END_OF_STREAM = 11
    FILLER_DATA = 12
    STAP_A = 24                # Single-Time Aggregation Packet type A
    STAP_B = 25
    MTAP16 = 26
    MTAP24 = 27
    FU_A = 28                  # Fragmentation Unit type A
    FU_B = 29


@dataclass
class NALUnit:
    """Individual H.264 NAL Unit."""
    unit_type: NALUnitType
    nal_ref_idc: int           # 2-bit priority (0 = non-reference, 3 = critical)
    payload: bytes
    is_keyframe: bool = False

    @property
    def raw_annex_b(self) -> bytes:
        """Render NAL unit with 4-byte start code prefix."""
        header = bytes([((self.nal_ref_idc & 0x03) << 5) | (self.unit_type & 0x1F)])
        return ANNEX_B_START_CODE + header + self.payload


@dataclass
class VideoFrame:
    """Complete reassembled video access unit."""
    timestamp_rtp: int
    nal_units: List[NALUnit] = field(default_factory=list)
    is_keyframe: bool = False

    @property
    def annex_b_stream(self) -> bytes:
        """Concatenate all NAL units in this frame into a single Annex B stream."""
        return b"".join(n.raw_annex_b for n in self.nal_units)

    @property
    def total_bytes(self) -> int:
        return sum(len(n.payload) + 5 for n in self.nal_units)


class H264RTPDepacketizer:
    """
    RTP Depacketizer for H.264 / AVC video streams (RFC 6184).
    Reassembles fragmented FU-A packets and decodes STAP-A aggregation units.
    """

    def __init__(self):
        # FU-A reassembly buffers: timestamp -> list of chunks
        self._fua_buffer: Dict[int, List[bytes]] = {}
        self._fua_headers: Dict[int, Tuple[int, NALUnitType]] = {} # ts -> (nal_ref_idc, nal_type)
        self._current_frame: Optional[VideoFrame] = None
        self._total_packets_processed: int = 0
        self._total_frames_completed: int = 0
        self._sps_cache: Optional[bytes] = None
        self._pps_cache: Optional[bytes] = None

    def depacketize(
        self,
        payload: bytes,
        rtp_timestamp: int,
        rtp_marker: bool,
        sequence_number: int
    ) -> Optional[VideoFrame]:
        """
        Process incoming RTP packet payload.
        Returns VideoFrame when RTP marker bit indicates the end of a video access unit.
        """
        if not payload:
            return None

        self._total_packets_processed += 1
        first_byte = payload[0]
        forbidden_zero_bit = (first_byte >> 7) & 0x01
        if forbidden_zero_bit != 0:
            log.warning("H.264 RTP Depacketizer: Dropping packet with invalid forbidden_zero_bit")
            return None

        nal_ref_idc = (first_byte >> 5) & 0x03
        nal_type_raw = first_byte & 0x1F

        try:
            nal_type = NALUnitType(nal_type_raw)
        except ValueError:
            nal_type = NALUnitType.UNSPECIFIED

        # Initialize current frame if new timestamp
        if not self._current_frame or self._current_frame.timestamp_rtp != rtp_timestamp:
            self._current_frame = VideoFrame(timestamp_rtp=rtp_timestamp)

        # 1. Single NAL Unit Packet (Type 1 - 23)
        if 1 <= nal_type <= 23:
            unit = NALUnit(
                unit_type=nal_type,
                nal_ref_idc=nal_ref_idc,
                payload=payload[1:],  # Exclude NAL header byte
                is_keyframe=(nal_type == NALUnitType.IDR_SLICE),
            )
            self._cache_parameters(unit)
            self._current_frame.nal_units.append(unit)
            if unit.is_keyframe:
                self._current_frame.is_keyframe = True

        # 2. STAP-A: Aggregation Packet (Type 24)
        elif nal_type == NALUnitType.STAP_A:
            self._process_stap_a(payload[1:], self._current_frame)

        # 3. FU-A: Fragmentation Unit (Type 28)
        elif nal_type == NALUnitType.FU_A:
            self._process_fu_a(payload, rtp_timestamp, self._current_frame)

        # If RTP marker bit is set, the full access unit (frame) is complete!
        if rtp_marker and self._current_frame:
            frame = self._current_frame
            self._current_frame = None
            self._total_frames_completed += 1
            return frame

        return None

    # -------------------------------------------------------------------------
    # Internal Depacketization Handlers
    # -------------------------------------------------------------------------

    def _process_stap_a(self, payload: bytes, frame: VideoFrame):
        """Parse multiple NAL units packed in a single STAP-A packet."""
        offset = 0
        while offset + 2 <= len(payload):
            # 2-byte NAL size prefix
            nal_size = struct.unpack("!H", payload[offset : offset + 2])[0]
            offset += 2
            if offset + nal_size > len(payload):
                break

            nal_data = payload[offset : offset + nal_size]
            offset += nal_size

            if nal_data:
                header = nal_data[0]
                n_ref = (header >> 5) & 0x03
                n_type_raw = header & 0x1F
                try:
                    n_type = NALUnitType(n_type_raw)
                except ValueError:
                    n_type = NALUnitType.UNSPECIFIED

                unit = NALUnit(
                    unit_type=n_type,
                    nal_ref_idc=n_ref,
                    payload=nal_data[1:],
                    is_keyframe=(n_type == NALUnitType.IDR_SLICE),
                )
                self._cache_parameters(unit)
                frame.nal_units.append(unit)
                if unit.is_keyframe:
                    frame.is_keyframe = True

    def _process_fu_a(self, payload: bytes, rtp_timestamp: int, frame: VideoFrame):
        """Reassemble fragmented NAL unit slices (FU-A)."""
        if len(payload) < 2:
            return

        fu_indicator = payload[0]
        fu_header = payload[1]

        nal_ref_idc = (fu_indicator >> 5) & 0x03
        is_start = bool(fu_header & 0x80)
        is_end = bool(fu_header & 0x40)
        nal_type_raw = fu_header & 0x1F

        try:
            nal_type = NALUnitType(nal_type_raw)
        except ValueError:
            nal_type = NALUnitType.UNSPECIFIED

        fu_payload = payload[2:]

        if is_start:
            self._fua_buffer[rtp_timestamp] = [fu_payload]
            self._fua_headers[rtp_timestamp] = (nal_ref_idc, nal_type)
        elif rtp_timestamp in self._fua_buffer:
            self._fua_buffer[rtp_timestamp].append(fu_payload)

        if is_end and rtp_timestamp in self._fua_buffer:
            full_payload = b"".join(self._fua_buffer.pop(rtp_timestamp))
            ref_idc, n_type = self._fua_headers.pop(rtp_timestamp, (nal_ref_idc, nal_type))

            unit = NALUnit(
                unit_type=n_type,
                nal_ref_idc=ref_idc,
                payload=full_payload,
                is_keyframe=(n_type == NALUnitType.IDR_SLICE),
            )
            self._cache_parameters(unit)
            frame.nal_units.append(unit)
            if unit.is_keyframe:
                frame.is_keyframe = True

    def _cache_parameters(self, unit: NALUnit):
        """Save SPS and PPS parameter sets for out-of-band decoder init."""
        if unit.unit_type == NALUnitType.SPS:
            self._sps_cache = unit.payload
        elif unit.unit_type == NALUnitType.PPS:
            self._pps_cache = unit.payload

    # -------------------------------------------------------------------------
    # Diagnostics & Status
    # -------------------------------------------------------------------------

    @property
    def has_parameter_sets(self) -> bool:
        return bool(self._sps_cache and self._pps_cache)

    @property
    def stats(self) -> Dict[str, int]:
        return {
            "packets_processed": self._total_packets_processed,
            "frames_completed": self._total_frames_completed,
            "pending_fua_buffers": len(self._fua_buffer),
        }
