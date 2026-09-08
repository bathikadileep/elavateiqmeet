"""
ElevateIQ — Unit Test Suite for RFC 6184 H.264 RTP Depacketizer
================================================================
Tests Single NAL Units, STAP-A Aggregation Packets, and FU-A Fragmentation
Unit reassembly with Annex B formatting.
"""

import struct
import unittest
from backend.services.media.h264_rtp_depacketizer import (
    H264RTPDepacketizer,
    NALUnitType,
    ANNEX_B_START_CODE,
)


class H264RTPDepacketizerTestSuite(unittest.TestCase):

    def setUp(self):
        self.depacketizer = H264RTPDepacketizer()

    def test_single_nal_unit_depacketization(self):
        """Test Single NAL unit packet (Type 1 non-IDR slice)."""
        # Header: ref_idc=2 (0x40), nal_type=1 (0x01) -> 0x41
        payload = b"\x41" + b"\x12\x34\x56\x78"
        frame = self.depacketizer.depacketize(
            payload=payload,
            rtp_timestamp=90000,
            rtp_marker=True,
            sequence_number=1001,
        )

        self.assertIsNotNone(frame)
        self.assertEqual(len(frame.nal_units), 1)
        self.assertEqual(frame.nal_units[0].unit_type, NALUnitType.NON_IDR_SLICE)
        self.assertEqual(frame.nal_units[0].nal_ref_idc, 2)
        self.assertEqual(frame.nal_units[0].payload, b"\x12\x34\x56\x78")

        # Verify Annex B stream start code
        stream = frame.annex_b_stream
        self.assertTrue(stream.startswith(ANNEX_B_START_CODE))
        self.assertEqual(stream, ANNEX_B_START_CODE + b"\x41\x12\x34\x56\x78")

    def test_stap_a_aggregation_packet(self):
        """Test STAP-A containing SPS and PPS parameter sets."""
        sps_payload = b"\x67\x42\x00\x1f\xe9"  # SPS
        pps_payload = b"\x68\xce\x38\x80"      # PPS

        # STAP-A header byte = 0x78 (ref_idc=3, type=24)
        stap_payload = (
            bytes([0x78])
            + struct.pack("!H", len(sps_payload)) + sps_payload
            + struct.pack("!H", len(pps_payload)) + pps_payload
        )

        frame = self.depacketizer.depacketize(
            payload=stap_payload,
            rtp_timestamp=90000,
            rtp_marker=True,
            sequence_number=1002,
        )

        self.assertIsNotNone(frame)
        self.assertEqual(len(frame.nal_units), 2)
        self.assertEqual(frame.nal_units[0].unit_type, NALUnitType.SPS)
        self.assertEqual(frame.nal_units[1].unit_type, NALUnitType.PPS)
        self.assertTrue(self.depacketizer.has_parameter_sets)

    def test_fu_a_fragmentation_reassembly(self):
        """Test FU-A splitting an IDR keyframe slice across 3 RTP packets."""
        # Target NAL: IDR Slice (type=5, ref_idc=3 -> 0x65)
        raw_slice_body = b"A" * 1500 + b"B" * 1500 + b"C" * 500

        # Chunk 1: Start Bit (S=1, E=0, Type=5 -> 0x85)
        # FU Indicator: ref_idc=3, type=28 -> 0x7C
        p1 = bytes([0x7C, 0x85]) + raw_slice_body[:1500]

        # Chunk 2: Middle Bit (S=0, E=0, Type=5 -> 0x05)
        p2 = bytes([0x7C, 0x05]) + raw_slice_body[1500:3000]

        # Chunk 3: End Bit (S=0, E=1, Type=5 -> 0x45)
        p3 = bytes([0x7C, 0x45]) + raw_slice_body[3000:]

        ts = 180000
        # Send chunk 1 (no marker)
        f1 = self.depacketizer.depacketize(p1, ts, rtp_marker=False, sequence_number=2001)
        self.assertIsNone(f1)

        # Send chunk 2 (no marker)
        f2 = self.depacketizer.depacketize(p2, ts, rtp_marker=False, sequence_number=2002)
        self.assertIsNone(f2)

        # Send chunk 3 with RTP marker = True (frame complete)
        f3 = self.depacketizer.depacketize(p3, ts, rtp_marker=True, sequence_number=2003)
        self.assertIsNotNone(f3)
        self.assertTrue(f3.is_keyframe)
        self.assertEqual(len(f3.nal_units), 1)
        self.assertEqual(f3.nal_units[0].unit_type, NALUnitType.IDR_SLICE)
        self.assertEqual(f3.nal_units[0].payload, raw_slice_body)

    def test_invalid_forbidden_zero_bit_dropped(self):
        """Test packet with forbidden_zero_bit=1 is safely dropped."""
        invalid_payload = bytes([0x81, 0x00, 0x00])  # MSB=1
        frame = self.depacketizer.depacketize(invalid_payload, 90000, True, 3001)
        self.assertIsNone(frame)


if __name__ == "__main__":
    unittest.main()
