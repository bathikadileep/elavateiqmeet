"""
ElevateIQ — AI Meeting Coach & Real-Time Engagement Analytics Engine
=====================================================================
Analyzes participant conversational dynamics, talk-time balance, monologue duration,
speech cadence, interruption patterns, and inclusivity metrics in real time.
Produces post-meeting executive coach scorecards with actionable recommendations.
"""

import time
import math
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

log = logging.getLogger("elevateiq.services.ai.coach")


@dataclass
class SpeakerTurn:
    """Represents a single conversational turn by a participant."""
    turn_id: str
    user_id: str
    display_name: str
    start_time: float
    end_time: float
    word_count: int
    sentiment_score: float = 0.0  # -1.0 to +1.0
    energy_level: float = 0.5     # 0.0 to 1.0


@dataclass
class InterruptionEvent:
    """Records an interruption between two participants."""
    interrupter_id: str
    interrupter_name: str
    interruptee_id: str
    interruptee_name: str
    timestamp: float
    overlap_duration_sec: float


@dataclass
class ParticipantMetrics:
    """Aggregated engagement metrics for a single participant."""
    user_id: str
    display_name: str
    total_talk_time_sec: float = 0.0
    turn_count: int = 0
    total_words: int = 0
    monologue_count: int = 0
    max_monologue_sec: float = 0.0
    interruptions_initiated: int = 0
    interruptions_received: int = 0
    average_wpm: float = 0.0
    average_sentiment: float = 0.0
    average_energy: float = 0.5


class MeetingCoachService:
    """
    Enterprise Meeting Coach Service for real-time conversational intelligence.
    Computes inclusivity indices, monologue alerts, and conversational turn-taking.
    """

    DEFAULT_MONOLOGUE_THRESHOLD_SEC = 120.0  # 2 minutes continuous speech
    TARGET_SPEAKING_RATE_MIN_WPM = 110.0     # Ideal conversational cadence
    TARGET_SPEAKING_RATE_MAX_WPM = 160.0

    def __init__(self, room_code: str, monologue_threshold_sec: float = DEFAULT_MONOLOGUE_THRESHOLD_SEC):
        self.room_code = room_code
        self.monologue_threshold_sec = monologue_threshold_sec
        self.turns: List[SpeakerTurn] = []
        self.interruptions: List[InterruptionEvent] = []
        self.participants: Dict[str, ParticipantMetrics] = {}
        self.meeting_start_time = time.time()
        self.is_active = True
        self._current_speaker_id: Optional[str] = None
        self._current_turn_start: Optional[float] = None
        self._current_word_count: int = 0

    def register_participant(self, user_id: str, display_name: str) -> ParticipantMetrics:
        """Register or retrieve a meeting participant for coaching tracking."""
        if user_id not in self.participants:
            self.participants[user_id] = ParticipantMetrics(
                user_id=user_id,
                display_name=display_name
            )
            log.info("MeetingCoach [%s]: Registered participant %s (%s)", self.room_code, display_name, user_id)
        return self.participants[user_id]

    def record_speech_turn(
        self,
        user_id: str,
        display_name: str,
        duration_sec: float,
        word_count: int,
        sentiment: float = 0.0,
        energy: float = 0.5,
        timestamp: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Record a speech segment or conversational turn.
        Detects monologues and updates running averages.
        """
        now = timestamp or time.time()
        start_t = now - duration_sec
        turn_id = f"turn_{len(self.turns) + 1}_{int(now)}"

        turn = SpeakerTurn(
            turn_id=turn_id,
            user_id=user_id,
            display_name=display_name,
            start_time=start_t,
            end_time=now,
            word_count=word_count,
            sentiment_score=max(-1.0, min(1.0, sentiment)),
            energy_level=max(0.0, min(1.0, energy))
        )
        self.turns.append(turn)

        # Update participant record
        metrics = self.register_participant(user_id, display_name)
        metrics.total_talk_time_sec += duration_sec
        metrics.turn_count += 1
        metrics.total_words += word_count

        # Check monologue trigger
        is_monologue = duration_sec >= self.monologue_threshold_sec
        if is_monologue:
            metrics.monologue_count += 1
            log.warning("MeetingCoach [%s]: Monologue detected for %s (Duration: %.1fs)",
                        self.room_code, display_name, duration_sec)

        if duration_sec > metrics.max_monologue_sec:
            metrics.max_monologue_sec = duration_sec

        # Recalculate Words Per Minute (WPM)
        if metrics.total_talk_time_sec > 0:
            metrics.average_wpm = round((metrics.total_words / metrics.total_talk_time_sec) * 60.0, 1)

        # Recalculate running sentiment and energy
        user_turns = [t for t in self.turns if t.user_id == user_id]
        if user_turns:
            metrics.average_sentiment = round(sum(t.sentiment_score for t in user_turns) / len(user_turns), 2)
            metrics.average_energy = round(sum(t.energy_level for t in user_turns) / len(user_turns), 2)

        return {
            "turn_id": turn_id,
            "user_id": user_id,
            "duration_sec": round(duration_sec, 2),
            "is_monologue": is_monologue,
            "wpm": metrics.average_wpm,
            "total_talk_time_sec": round(metrics.total_talk_time_sec, 2)
        }

    def record_interruption(
        self,
        interrupter_id: str,
        interrupter_name: str,
        interruptee_id: str,
        interruptee_name: str,
        overlap_duration_sec: float = 0.5,
        timestamp: Optional[float] = None
    ) -> InterruptionEvent:
        """Record an overlapping speech event where one speaker interrupts another."""
        now = timestamp or time.time()
        event = InterruptionEvent(
            interrupter_id=interrupter_id,
            interrupter_name=interrupter_name,
            interruptee_id=interruptee_id,
            interruptee_name=interruptee_name,
            timestamp=now,
            overlap_duration_sec=overlap_duration_sec
        )
        self.interruptions.append(event)

        p_interrupter = self.register_participant(interrupter_id, interrupter_name)
        p_interrupter.interruptions_initiated += 1

        p_interruptee = self.register_participant(interruptee_id, interruptee_name)
        p_interruptee.interruptions_received += 1

        log.info("MeetingCoach [%s]: Interruption! %s interrupted %s (Overlap: %.2fs)",
                 self.room_code, interrupter_name, interruptee_name, overlap_duration_sec)
        return event

    def get_talk_time_distribution(self) -> Dict[str, Any]:
        """
        Calculate talk-time percentages across all participants.
        Returns percentage breakdown and total elapsed speech time.
        """
        total_talk = sum(p.total_talk_time_sec for p in self.participants.values())
        distribution = {}

        for uid, p in self.participants.items():
            pct = round((p.total_talk_time_sec / total_talk * 100.0), 1) if total_talk > 0 else 0.0
            distribution[uid] = {
                "display_name": p.display_name,
                "talk_time_sec": round(p.total_talk_time_sec, 1),
                "percentage": pct,
                "turn_count": p.turn_count,
                "monologues": p.monologue_count
            }

        return {
            "total_speech_time_sec": round(total_talk, 1),
            "participant_count": len(self.participants),
            "distribution": distribution
        }

    def compute_inclusivity_index(self) -> float:
        """
        Compute conversational equality using the Gini coefficient.
        Returns a score from 0.0 to 100.0 (100 = perfectly balanced participation).
        """
        if len(self.participants) <= 1:
            return 100.0

        times = sorted([p.total_talk_time_sec for p in self.participants.values()])
        n = len(times)
        total = sum(times)

        if total == 0:
            return 100.0

        # Calculate Gini coefficient: G = (2 * sum(i * y_i) - (n + 1) * sum(y_i)) / (n * sum(y_i))
        weighted_sum = sum((i + 1) * val for i, val in enumerate(times))
        gini = (2.0 * weighted_sum) / (n * total) - ((n + 1.0) / n)

        # Invert Gini: 0 Gini = 100 Inclusivity (perfect balance), 1 Gini = 0 Inclusivity (monopolized)
        inclusivity = max(0.0, min(100.0, (1.0 - gini) * 100.0))
        return round(inclusivity, 1)

    def generate_coach_scorecard(self) -> Dict[str, Any]:
        """
        Generate comprehensive post-meeting executive coach scorecard.
        Includes engagement score, pace evaluation, and coaching recommendations.
        """
        total_speech = sum(p.total_talk_time_sec for p in self.participants.values())
        inclusivity_score = self.compute_inclusivity_index()
        recommendations: List[str] = []

        # Analyze talk-time dominators
        for uid, p in self.participants.items():
            if total_speech > 60:
                pct = (p.total_talk_time_sec / total_speech) * 100.0
                if pct > 60.0 and len(self.participants) >= 3:
                    recommendations.append(
                        f"{p.display_name} spoke for {pct:.0f}% of the meeting. Try passing the floor to other team members."
                    )
                elif pct < 5.0 and len(self.participants) >= 2:
                    recommendations.append(
                        f"{p.display_name} spoke for under 5% of the time. Encourage their input in future agenda items."
                    )

            # Analyze pacing
            if p.turn_count >= 2:
                if p.average_wpm > self.TARGET_SPEAKING_RATE_MAX_WPM:
                    recommendations.append(
                        f"{p.display_name}'s speech rate was {p.average_wpm} WPM (brisk). Consider pausing between points for comprehension."
                    )
                elif p.average_wpm < self.TARGET_SPEAKING_RATE_MIN_WPM and p.average_wpm > 0:
                    recommendations.append(
                        f"{p.display_name}'s speech rate was {p.average_wpm} WPM. A slightly more energetic cadence can elevate engagement."
                    )

            # Analyze interruptions
            if p.interruptions_initiated >= 4:
                recommendations.append(
                    f"{p.display_name} initiated {p.interruptions_initiated} interruptions. Practice active listening to allow peers to complete ideas."
                )

        if not recommendations:
            recommendations.append("Excellent conversational balance and respectful turn-taking observed throughout the session!")

        # Overall meeting effectiveness score (composite of inclusivity, interruptions, and monologues)
        penalty = sum(p.monologue_count * 5 for p in self.participants.values())
        penalty += len(self.interruptions) * 3
        overall_score = max(30.0, min(100.0, inclusivity_score - penalty))

        return {
            "room_code": self.room_code,
            "overall_effectiveness_score": round(overall_score, 1),
            "inclusivity_index": inclusivity_score,
            "total_speech_time_sec": round(total_speech, 1),
            "total_turns": len(self.turns),
            "total_interruptions": len(self.interruptions),
            "participants": {
                uid: {
                    "display_name": p.display_name,
                    "talk_time_sec": round(p.total_talk_time_sec, 1),
                    "turn_count": p.turn_count,
                    "average_wpm": p.average_wpm,
                    "monologue_count": p.monologue_count,
                    "interruptions_initiated": p.interruptions_initiated,
                    "interruptions_received": p.interruptions_received,
                    "average_sentiment": p.average_sentiment,
                    "average_energy": p.average_energy
                }
                for uid, p in self.participants.items()
            },
            "recommendations": recommendations
        }
