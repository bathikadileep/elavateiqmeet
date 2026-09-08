"""
ElevateIQ — AI Real-Time Caption Punctuation Restorer & Speaker Diarization
============================================================================
Processes streaming unpunctuated ASR (Automatic Speech Recognition) text chunks,
restores natural punctuation and sentence capitalization, maps diarization timestamps
to active room participants, and applies enterprise profanity filtering.
"""

import re
import time
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field

log = logging.getLogger("elevateiq.services.ai.caption")


@dataclass
class CaptionSegment:
    """Represents a formatted, punctuated caption fragment with speaker attribution."""
    segment_id: str
    user_id: str
    speaker_name: str
    raw_text: str
    formatted_text: str
    start_time_sec: float
    end_time_sec: float
    confidence: float = 0.95
    is_final: bool = True


class CaptionPunctuationRestorer:
    """
    Real-time NLP caption post-processor.
    Applies rule-based grammar heuristics, question detection, and speaker diarization.
    """

    QUESTION_STARTERS = {
        "who", "what", "where", "when", "why", "how",
        "is", "are", "was", "were", "can", "could", "would", "should", "do", "does", "did"
    }

    DEFAULT_PROFANITY_LIST = {
        "damn", "hell", "crap", "shit", "fuck", "asshole", "bitch", "bastard"
    }

    def __init__(self, filter_profanity: bool = True):
        self.filter_profanity = filter_profanity
        self.profanity_set = set(self.DEFAULT_PROFANITY_LIST)
        self.history_segments: List[CaptionSegment] = []

    def add_custom_profanity_words(self, words: List[str]) -> None:
        """Register custom tenant-specific banned terminology."""
        for w in words:
            self.profanity_set.add(w.lower().strip())

    def redact_profanity(self, text: str) -> str:
        """Replace offensive words with asterisks while preserving first letter."""
        if not self.filter_profanity or not text:
            return text

        words = text.split()
        redacted_words = []
        for word in words:
            # Strip punctuation for check
            clean = re.sub(r"[^\w]", "", word).lower()
            if clean in self.profanity_set:
                masked = clean[0] + "*" * (len(clean) - 1)
                # Re-apply any trailing punctuation
                trailing = word[len(clean):]
                redacted_words.append(masked + trailing)
            else:
                redacted_words.append(word)

        return " ".join(redacted_words)

    def restore_punctuation_and_case(self, raw_text: str) -> str:
        """
        Transform raw lowercased streaming text into natural punctuated sentences.
        Example: 'hello everyone can you hear me clearly' -> 'Hello everyone, can you hear me clearly?'
        """
        cleaned = raw_text.strip()
        if not cleaned:
            return ""

        words = cleaned.split()
        if not words:
            return ""

        # Step 1: Capitalize first word
        words[0] = words[0].capitalize()

        # Step 2: Capitalize 'i' -> 'I'
        for i in range(len(words)):
            if words[i].lower() == "i":
                words[i] = "I"
            elif words[i].lower().startswith("i'") or words[i].lower().startswith("i’"):
                words[i] = "I" + words[i][1:]

        # Step 3: Insert comma after introductory phrases
        introductory = {"well", "hello", "hi", "hey", "so", "actually", "basically"}
        if len(words) > 2 and words[0].lower() in introductory and not words[0].endswith(","):
            words[0] = words[0] + ","

        # Step 4: Determine terminal punctuation (Question mark vs Period)
        last_word = words[-1]
        has_terminal = last_word.endswith((".", "?", "!"))

        if not has_terminal:
            first_word_lower = words[0].rstrip(",").lower()
            if first_word_lower in self.QUESTION_STARTERS:
                words[-1] = last_word + "?"
            else:
                words[-1] = last_word + "."

        result = " ".join(words)

        # Step 5: Filter profanity if enabled
        return self.redact_profanity(result)

    def align_diarization(
        self,
        raw_text: str,
        start_time_sec: float,
        end_time_sec: float,
        speaker_energy_profiles: Dict[str, Tuple[str, float]] # user_id -> (display_name, avg_energy)
    ) -> CaptionSegment:
        """
        Match raw text chunk to the participant with highest acoustic energy during interval.
        Returns a fully attributed and punctuated CaptionSegment.
        """
        # Find speaker with maximum energy
        if speaker_energy_profiles:
            best_speaker_id, (best_name, max_energy) = max(
                speaker_energy_profiles.items(),
                key=lambda item: item[1][1]
            )
        else:
            best_speaker_id = "unknown_speaker"
            best_name = "Unknown Speaker"

        formatted = self.restore_punctuation_and_case(raw_text)
        segment_id = f"cap_{int(start_time_sec * 1000)}_{int(end_time_sec * 1000)}"

        segment = CaptionSegment(
            segment_id=segment_id,
            user_id=best_speaker_id,
            speaker_name=best_name,
            raw_text=raw_text,
            formatted_text=formatted,
            start_time_sec=start_time_sec,
            end_time_sec=end_time_sec
        )
        self.history_segments.append(segment)
        log.info("CaptionNLP: Attributed caption '%s...' to %s (Confidence: %.2f)",
                 formatted[:25], best_name, segment.confidence)
        return segment

    def get_transcript_summary(self) -> Dict[str, Any]:
        """Aggregate all diarized caption segments into full meeting transcript."""
        lines = []
        for s in self.history_segments:
            timestamp_str = f"[{int(s.start_time_sec // 60):02d}:{int(s.start_time_sec % 60):02d}]"
            lines.append(f"{timestamp_str} {s.speaker_name}: {s.formatted_text}")

        return {
            "total_segments": len(self.history_segments),
            "total_words": sum(len(s.formatted_text.split()) for s in self.history_segments),
            "formatted_transcript": "\n".join(lines)
        }
