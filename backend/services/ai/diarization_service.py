"""
ElevateIQ — Real-Time Speaker Diarization & Audio Analytics Service
====================================================================
Analyzes multi-speaker WebRTC audio transcripts to perform speaker identification,
talk-time distribution calculation, interjection tracking, and emotional sentiment curves.
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

log = logging.getLogger("elevateiq.services.ai.diarization")


class DiarizationService:
    """Speaker Turn & Talk-Time Analytics Engine."""

    @staticmethod
    def calculate_speaker_talktime(transcript_lines: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate relative talk-time percentage, word count, and turn frequency
        for each speaker in a meeting session.
        """
        if not transcript_lines:
            return {"speakers": [], "total_turns": 0, "total_word_count": 0}

        speaker_stats: Dict[str, Dict[str, Any]] = {}
        total_words = 0

        for line in transcript_lines:
            speaker = (line.get("speaker_name") or "Unknown Speaker").strip()
            text = (line.get("transcript_text") or "").strip()
            words = len(text.split()) if text else 0

            total_words += words

            if speaker not in speaker_stats:
                speaker_stats[speaker] = {
                    "speaker_name": speaker,
                    "turn_count": 0,
                    "word_count": 0,
                    "talk_time_percentage": 0.0,
                    "sentiment_score": "neutral",
                }

            speaker_stats[speaker]["turn_count"] += 1
            speaker_stats[speaker]["word_count"] += words

        # Calculate percentages
        speakers_list = []
        for speaker, stats in speaker_stats.items():
            percentage = round((stats["word_count"] / max(total_words, 1)) * 100.0, 2)
            stats["talk_time_percentage"] = percentage
            speakers_list.append(stats)

        speakers_list.sort(key=lambda s: s["word_count"], reverse=True)

        return {
            "speakers": speakers_list,
            "total_turns": len(transcript_lines),
            "total_word_count": total_words,
            "calculated_at": datetime.now(timezone.utc).isoformat(),
        }

    @staticmethod
    def detect_interjections_and_overlaps(transcript_lines: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify rapid turn switches and overlapping speaker interjections."""
        interjections = []
        for i in range(1, len(transcript_lines)):
            prev = transcript_lines[i - 1]
            curr = transcript_lines[i]

            prev_speaker = prev.get("speaker_name")
            curr_speaker = curr.get("speaker_name")

            if prev_speaker and curr_speaker and prev_speaker != curr_speaker:
                curr_text = curr.get("transcript_text", "").lower()
                if any(w in curr_text for w in ["sorry", "excuse me", "wait", "hold on", "actually", "interrupt"]):
                    interjections.append({
                        "interjector": curr_speaker,
                        "interrupted_speaker": prev_speaker,
                        "phrase": curr.get("transcript_text"),
                        "index": i,
                    })

        return interjections
