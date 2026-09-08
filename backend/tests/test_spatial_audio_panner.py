"""Tests for SpatialAudioPanner service."""

import math
import unittest
from backend.services.media.spatial_audio_panner import (
    SpatialAudioPanner,
    SpatialPosition,
    ParticipantAudioNode,
    HRTFConfig,
    RoomShape,
    DistanceModel,
)


class TestSpatialPosition(unittest.TestCase):

    def test_to_spherical_origin(self):
        pos = SpatialPosition(0.0, 0.0, 0.0)
        az, el, dist = pos.to_spherical()
        self.assertEqual(dist, 0.0)

    def test_to_spherical_right(self):
        pos = SpatialPosition(1.0, 0.0, 0.0)
        az, el, dist = pos.to_spherical()
        self.assertAlmostEqual(dist, 1.0, places=4)
        self.assertAlmostEqual(az, 90.0, places=2)

    def test_distance_to(self):
        a = SpatialPosition(0.0, 0.0, 0.0)
        b = SpatialPosition(1.0, 0.0, 0.0)
        self.assertAlmostEqual(a.distance_to(b), 1.0, places=4)


class TestSpatialAudioPanner(unittest.TestCase):

    def setUp(self):
        self.panner = SpatialAudioPanner(room_shape=RoomShape.CIRCLE)

    def test_add_participant(self):
        node = self.panner.add_participant("p1", "Alice")
        self.assertEqual(node.participant_id, "p1")
        self.assertEqual(node.display_name, "Alice")

    def test_remove_participant(self):
        self.panner.add_participant("p2", "Bob")
        self.panner.remove_participant("p2")
        self.assertIsNone(self.panner.get_participant("p2"))

    def test_list_participants(self):
        self.panner.add_participant("p3", "Carol")
        self.panner.add_participant("p4", "Dave")
        self.assertEqual(len(self.panner.list_participants()), 2)

    def test_auto_layout_circle(self):
        for i in range(4):
            self.panner.add_participant(f"user_{i}", f"User {i}")
        positions = self.panner.auto_layout()
        self.assertEqual(len(positions), 4)
        for pid, pos in positions.items():
            dist = math.sqrt(pos.x**2 + pos.y**2 + pos.z**2)
            self.assertAlmostEqual(dist, 1.0, places=4)

    def test_auto_layout_grid(self):
        panner = SpatialAudioPanner(room_shape=RoomShape.GRID)
        for i in range(6):
            panner.add_participant(f"u{i}", f"User {i}")
        positions = panner.auto_layout()
        self.assertEqual(len(positions), 6)

    def test_auto_layout_semicircle(self):
        panner = SpatialAudioPanner(room_shape=RoomShape.SEMICIRCLE)
        for i in range(3):
            panner.add_participant(f"s{i}", f"Speaker {i}")
        positions = panner.auto_layout()
        self.assertEqual(len(positions), 3)

    def test_compute_hrtf_cues(self):
        self.panner.add_participant(
            "p5", "Eve", SpatialPosition(x=0.5, y=0.5, z=0.0)
        )
        cues = self.panner.compute_hrtf_cues("p5")
        self.assertIn("azimuth_deg", cues)
        self.assertIn("itd_ms", cues)
        self.assertIn("ild_db", cues)
        self.assertIn("gain_db", cues)

    def test_hrtf_cues_unknown_participant(self):
        cues = self.panner.compute_hrtf_cues("nonexistent")
        self.assertEqual(cues, {})

    def test_compute_all_hrtf_cues(self):
        self.panner.add_participant("p6", "Frank", SpatialPosition(1.0, 0.0, 0.0))
        self.panner.add_participant("p7", "Grace", SpatialPosition(-1.0, 0.0, 0.0))
        all_cues = self.panner.compute_all_hrtf_cues()
        self.assertIn("p6", all_cues)
        self.assertIn("p7", all_cues)

    def test_itd_symmetric(self):
        """ITD should be symmetric: left ear ~ negative of right ear."""
        p = self.panner.add_participant("p8", "Henry")
        p.position = SpatialPosition(1.0, 0.0, 0.0)
        cues_right = self.panner.compute_hrtf_cues("p8")
        p.position = SpatialPosition(-1.0, 0.0, 0.0)
        cues_left = self.panner.compute_hrtf_cues("p8")
        self.assertAlmostEqual(
            abs(cues_right["itd_ms"]), abs(cues_left["itd_ms"]), places=3
        )

    def test_distance_gain_inverse(self):
        panner = SpatialAudioPanner(distance_model=DistanceModel.INVERSE)
        panner.add_participant("p9", "Iris", SpatialPosition(2.0, 0.0, 0.0))
        cues = panner.compute_hrtf_cues("p9")
        self.assertLess(cues["gain_db"], 0)

    def test_set_speaking(self):
        self.panner.add_participant("p10", "Jack")
        self.panner.set_speaking("p10", True)
        node = self.panner.get_participant("p10")
        self.assertTrue(node.is_speaking)

    def test_get_active_speakers(self):
        self.panner.add_participant("p11", "Kate")
        self.panner.add_participant("p12", "Leo")
        self.panner.set_speaking("p11", True)
        speakers = self.panner.get_active_speakers()
        self.assertIn("p11", speakers)
        self.assertNotIn("p12", speakers)

    def test_get_scene(self):
        self.panner.add_participant("p13", "Mia", SpatialPosition(0.5, 0.5, 0.0))
        scene = self.panner.get_scene()
        self.assertIn("room_shape", scene)
        self.assertIn("participants", scene)
        self.assertIn("hrtf_cues", scene)

    def test_apply_scene(self):
        panner = SpatialAudioPanner()
        panner.add_participant("p14", "Noah", SpatialPosition(0.3, 0.4, 0.0))
        scene = panner.get_scene()
        panner2 = SpatialAudioPanner()
        panner2.apply_scene(scene)
        self.assertIsNotNone(panner2.get_participant("p14"))

    def test_node_to_dict(self):
        node = ParticipantAudioNode(
            "p15", "Olivia", SpatialPosition(1.0, 0.0, 0.0)
        )
        d = node.to_dict()
        self.assertIn("participant_id", d)
        self.assertIn("azimuth_deg", d)
        self.assertIn("distance", d)


if __name__ == "__main__":
    unittest.main()
