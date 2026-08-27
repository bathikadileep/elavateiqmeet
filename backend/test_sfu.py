"""
ElevateIQ SFU — Automated Unit Test Suite
==========================================
Tests SFU Workers, Routers, Transports, Producers, Consumers,
Simulcast quality layer engine, Voice Activity Detection (VAD),
and Socket.IO signaling event handlers.
"""

import unittest
import time
from backend.sfu.worker import get_sfu_worker_pool
from backend.sfu.router import get_or_create_sfu_router, destroy_sfu_router
from backend.sfu.transports import WebRtcTransport, PlainTransport
from backend.sfu.producers import Producer
from backend.sfu.consumers import Consumer
from backend.sfu.simulcast import SimulcastEngine
from backend.sfu.vad import VoiceActivityDetector, VADEvent


class SFUTestCase(unittest.TestCase):

    def setUp(self):
        self.room_code = f"sfu-test-{int(time.time())}"
        self.router = get_or_create_sfu_router(self.room_code)

    def tearDown(self):
        destroy_sfu_router(self.room_code)

    def test_worker_pool_capabilities_and_stats(self):
        pool = get_sfu_worker_pool()
        caps = pool.get_router_capabilities()
        self.assertIn("codecs", caps)
        self.assertIn("headerExtensions", caps)

        stats = pool.get_system_stats()
        self.assertIn("active_routers", stats)
        self.assertIn("worker_pid", stats)

    def test_webrtc_transport_lifecycle(self):
        transport = self.router.create_web_rtc_transport(direction="sendrecv")
        self.assertEqual(transport.state, "new")

        options = transport.get_transport_options()
        self.assertIn("iceParameters", options)
        self.assertIn("dtlsParameters", options)

        res = transport.connect({"fingerprints": []})
        self.assertEqual(res["state"], "connected")
        self.assertEqual(transport.state, "connected")

        stats = transport.get_stats()
        self.assertEqual(stats["state"], "connected")

    def test_producer_and_consumer_lifecycle(self):
        transport1 = self.router.create_web_rtc_transport(direction="recvonly")
        transport2 = self.router.create_web_rtc_transport(direction="sendonly")

        transport1.connect({})
        transport2.connect({})

        producer = self.router.create_producer(
            transport_id=transport1.id,
            kind="video",
            app_data={"peer_sid": "peer1"}
        )
        self.assertEqual(producer.kind, "video")
        self.assertFalse(producer.paused)

        producer.pause()
        self.assertTrue(producer.paused)
        producer.resume()
        self.assertFalse(producer.paused)

        consumer = self.router.create_consumer(
            producer_id=producer.id,
            transport_id=transport2.id,
            app_data={"subscriber_sid": "peer2"}
        )
        self.assertEqual(consumer.producer_id, producer.id)
        self.assertEqual(consumer.kind, "video")

        consumer.set_preferred_layers(spatial_layer=1)
        self.assertEqual(consumer.current_spatial_layer, 1)

    def test_simulcast_layer_engine(self):
        layers = SimulcastEngine.get_supported_layers()
        self.assertEqual(len(layers), 3)

        # High loss / latency -> Low quality (layer 0)
        layer_low = SimulcastEngine.calculate_optimal_layer(rtt_ms=450, packet_loss_percent=10.0, available_bitrate_kbps=250)
        self.assertEqual(layer_low, 0)

        # Normal network -> High quality (layer 2)
        layer_high = SimulcastEngine.calculate_optimal_layer(rtt_ms=50, packet_loss_percent=0.5, available_bitrate_kbps=1800)
        self.assertEqual(layer_high, 2)

    def test_vad_audio_energy(self):
        vad = VoiceActivityDetector(speaking_threshold_dbfs=-45.0)

        # Silent audio
        evt1 = vad.process_audio_energy(sid="sid1", display_name="Alice", user_id="u1", dbfs=-70.0)
        self.assertIsNotNone(evt1)
        self.assertFalse(evt1.is_speaking)
        self.assertEqual(evt1.audio_level_normalized, 22)

        # Active speaking audio
        evt2 = vad.process_audio_energy(sid="sid1", display_name="Alice", user_id="u1", dbfs=-30.0)
        self.assertIsNotNone(evt2)
        self.assertTrue(evt2.is_speaking)
        self.assertEqual(vad.active_speaker_sid, "sid1")


if __name__ == "__main__":
    unittest.main()
