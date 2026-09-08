"""
ElevateIQ — Unit Test Suite for Advanced AI & Telemetry Services
================================================================
Tests acoustic prosody emotion analysis, participant interaction graphs,
BERTopic taxonomy classification, and WebRTC GCC bandwidth adaptation.
"""

import unittest
from backend.services.ai.speech_emotion_recognizer import SpeechEmotionRecognizerService
from backend.services.ai.meeting_graph_builder import MeetingGraphBuilderService
from backend.services.ai.topic_classifier import TopicClassifierService
from backend.services.telemetry.bandwidth_estimator import BandwidthEstimatorService


class AIAdvancedTestSuite(unittest.TestCase):

    def test_speech_emotion_analysis(self):
        """Test prosody emotional state evaluation."""
        eval_excited = SpeechEmotionRecognizerService.analyze_audio_prosody(audio_duration_sec=10.0, word_count=35, pitch_hz=240.0, volume_db=-5.0)
        self.assertEqual(eval_excited["emotion"], "excited")

        eval_calm = SpeechEmotionRecognizerService.analyze_audio_prosody(audio_duration_sec=15.0, word_count=20, pitch_hz=110.0, volume_db=-20.0)
        self.assertEqual(eval_calm["emotion"], "calm")

    def test_meeting_interaction_graph_builder(self):
        """Test participant dialogue graph construction and degree centrality."""
        lines = [
            {"speaker_name": "Alice", "transcript_text": "Hello everyone."},
            {"speaker_name": "Bob", "transcript_text": "Hi Alice, good morning."},
            {"speaker_name": "Alice", "transcript_text": "Let us review Q3 deliverables."},
            {"speaker_name": "Charlie", "transcript_text": "I agree with Alice."},
        ]

        graph = MeetingGraphBuilderService.build_interaction_graph(lines)
        self.assertEqual(len(graph["nodes"]), 3)
        self.assertGreater(len(graph["edges"]), 0)

    def test_topic_classifier_taxonomy(self):
        """Test multi-label taxonomy keyword classification."""
        lines = [
            {"speaker_name": "Dev", "transcript_text": "We need to fix the database query bug and deploy Docker to backend server."}
        ]

        result = TopicClassifierService.classify_transcript_topics(lines)
        self.assertEqual(result["primary_topic"], "Engineering & Architecture")

    def test_webrtc_bandwidth_adaptation(self):
        """Test GCC bandwidth estimator multiplicative decrease and additive increase."""
        res_decrease = BandwidthEstimatorService.calculate_target_bitrate(current_bitrate_bps=2000000, loss_ratio=0.15, rtt_ms=120.0, delay_gradient_ms=30.0)
        self.assertLess(res_decrease["target_bitrate_kbps"], 2000.0)

        res_increase = BandwidthEstimatorService.calculate_target_bitrate(current_bitrate_bps=2000000, loss_ratio=0.0, rtt_ms=30.0, delay_gradient_ms=2.0)
        self.assertGreater(res_increase["target_bitrate_kbps"], 2000.0)


if __name__ == "__main__":
    unittest.main()
