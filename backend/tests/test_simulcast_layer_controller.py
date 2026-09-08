"""
ElevateIQ — Unit Tests for Simulcast Layer Controller & Leaky Bucket Pacer
===========================================================================
Tests LeakyBucket token pacing, queue overflow handling, simulcast layer subscription,
active speaker priority layer assignment, CPU overuse downgrades, and hysteresis dampening.
"""

import time
import unittest
from backend.services.media.simulcast_layer_controller import (
    SimulcastLayerController,
    LeakyBucketPacer,
    SpatialLayer,
    ReceiverSubscription
)


class TestSimulcastLayerController(unittest.TestCase):

    def setUp(self):
        self.controller = SimulcastLayerController(room_code="room-simulcast-808")
        self.pacer = LeakyBucketPacer(target_bitrate_kbps=2000)

    def test_pacer_enqueue_and_release(self):
        pkt1 = b"RTP_DATA_PACKET_1"
        pkt2 = b"RTP_DATA_PACKET_2"
        self.assertTrue(self.pacer.enqueue_packet(pkt1))
        self.assertTrue(self.pacer.enqueue_packet(pkt2))
        self.assertEqual(len(self.pacer.queue), 2)

        # Simulate 100ms time elapsed to leak tokens
        t0 = self.pacer.last_leak_time
        released = self.pacer.process_pacing(current_time=t0 + 0.10)
        self.assertEqual(len(released), 2)
        self.assertEqual(len(self.pacer.queue), 0)

    def test_pacer_queue_overflow(self):
        pacer_tiny = LeakyBucketPacer(target_bitrate_kbps=1000, max_queue_bytes=50)
        pkt = b"A" * 30
        self.assertTrue(pacer_tiny.enqueue_packet(pkt))
        # Second packet exceeds 50 bytes
        self.assertFalse(pacer_tiny.enqueue_packet(pkt))

    def test_subscribe_and_default_layer(self):
        sub = self.controller.subscribe("rec_1", "prod_1", initial_layer=SpatialLayer.MEDIUM)
        self.assertEqual(sub.receiver_id, "rec_1")
        self.assertEqual(sub.current_layer, SpatialLayer.MEDIUM)

    def test_active_speaker_priority_layer(self):
        self.controller.subscribe("viewer_1", "speaker_alice", initial_layer=SpatialLayer.LOW)
        self.controller.subscribe("viewer_1", "listener_bob", initial_layer=SpatialLayer.LOW)

        # Alice becomes active speaker
        self.controller.set_active_speaker("speaker_alice")

        # Alice should get HIGH layer under 1600 kbps downlink
        layer_alice = self.controller.compute_optimal_layer("viewer_1", "speaker_alice", downlink_bandwidth_kbps=1600)
        self.assertEqual(layer_alice, SpatialLayer.HIGH)

        # Bob (non-speaker) remains LOW or MEDIUM
        layer_bob = self.controller.compute_optimal_layer("viewer_1", "listener_bob", downlink_bandwidth_kbps=1600)
        self.assertEqual(layer_bob, SpatialLayer.LOW)

    def test_screen_share_priority(self):
        self.controller.subscribe("viewer_1", "screen_share_prod", initial_layer=SpatialLayer.HIGH, is_screen_share=True)
        layer = self.controller.compute_optimal_layer("viewer_1", "screen_share_prod", downlink_bandwidth_kbps=3000)
        self.assertEqual(layer, SpatialLayer.ULTRA)

    def test_cpu_overuse_downgrade(self):
        self.controller.subscribe("viewer_1", "speaker_alice", initial_layer=SpatialLayer.HIGH)
        self.controller.set_active_speaker("speaker_alice")

        # Notify CPU overuse on viewer_1
        self.controller.set_cpu_overuse("viewer_1", True)

        layer = self.controller.compute_optimal_layer("viewer_1", "speaker_alice", downlink_bandwidth_kbps=5000)
        # Even with 5000 kbps, CPU overuse forces LOW layer
        self.assertEqual(layer, SpatialLayer.LOW)

    def test_layer_switch_hysteresis(self):
        self.controller.subscribe("v1", "p1", initial_layer=SpatialLayer.LOW)
        self.controller.set_active_speaker("p1")
        t0 = time.time()

        # Step 1: Request upgrade to MEDIUM at t0 (bandwidth 600 kbps)
        switched, layer = self.controller.step_layer_switch("v1", "p1", downlink_bandwidth_kbps=600, current_time=t0)
        self.assertTrue(switched)
        self.assertEqual(layer, SpatialLayer.MEDIUM)

        # Step 2: Immediate further upgrade attempt 0.5s later (within 2.0s hysteresis)
        switched_fast, layer_fast = self.controller.step_layer_switch("v1", "p1", downlink_bandwidth_kbps=5000, current_time=t0 + 0.5)
        # Hysteresis should block upgrade
        self.assertFalse(switched_fast)
        self.assertEqual(layer_fast, SpatialLayer.MEDIUM)

        # Step 3: Upgrade attempt after 3.0s (past 2.0s hysteresis)
        switched_after, layer_after = self.controller.step_layer_switch("v1", "p1", downlink_bandwidth_kbps=5000, current_time=t0 + 3.0)
        self.assertTrue(switched_after)
        self.assertEqual(layer_after, SpatialLayer.ULTRA)


if __name__ == "__main__":
    unittest.main()
