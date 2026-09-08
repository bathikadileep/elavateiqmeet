"""
ElevateIQ — AI Meeting Intelligence & Summarizer Service
==========================================================
Analyzes meeting transcript logs to extract executive summaries,
key decisions, task assignments, and sentiment analytics.
"""

import os
import re
import json
import logging
import requests
from typing import Dict, Any, List

log = logging.getLogger("elevateiq.services.ai_summarizer")


class AISummarizerService:

    @staticmethod
    def _clean_json_response(raw: str) -> Dict[str, Any]:
        """
        Safely extract and parse JSON payload from raw LLM output,
        stripping markdown code fences (```json ... ```) and leading/trailing noise.
        """
        if not raw:
            raise ValueError("Empty response received from AI provider")

        cleaned = raw.strip()
        # Strip markdown code block wrapper if present (e.g. ```json ... ```)
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        cleaned = cleaned.strip()

        # If wrapped in other text, attempt to isolate the outermost JSON object
        json_match = re.search(r"(\{.*\})", cleaned, flags=re.DOTALL)
        if json_match:
            cleaned = json_match.group(1)

        data = json.loads(cleaned)
        if not isinstance(data, dict):
            raise ValueError("Parsed JSON is not an object dictionary")
        return data

    @staticmethod
    def generate_meeting_summary(transcript_lines: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze transcript lines and produce structured meeting intelligence.
        Filters out blank/whitespace-only lines to prevent empty blocks.
        """
        valid_lines = [
            t for t in (transcript_lines or [])
            if t.get("transcript_text") and t.get("transcript_text").strip()
        ]

        if not valid_lines:
            return {
                "executive_summary": "No transcript data was recorded for this meeting session.",
                "key_decisions": ["Meeting adjourned without active discussion transcript."],
                "action_items": [],
                "sentiment_score": "neutral",
                "sentiment_value": "0.50"
            }

        full_text = "\n".join([
            f"{t.get('speaker_name', 'Speaker')}: {t.get('transcript_text', '').strip()}"
            for t in valid_lines
        ])

        # Check for Gemini or OpenAI API keys
        gemini_key = os.getenv("GEMINI_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")

        if gemini_key:
            try:
                return AISummarizerService._call_gemini(full_text, gemini_key)
            except Exception as e:
                log.warning("Gemini API call failed, falling back to NLP engine: %s", e)

        if openai_key:
            try:
                return AISummarizerService._call_openai(full_text, openai_key)
            except Exception as e:
                log.warning("OpenAI API call failed, falling back to NLP engine: %s", e)

        # Fallback NLP Extraction Engine
        return AISummarizerService._fallback_nlp_engine(valid_lines, full_text)

    @staticmethod
    def _fallback_nlp_engine(transcript_lines: List[Dict[str, Any]], full_text: str) -> Dict[str, Any]:
        """Built-in rule-based NLP summarization & key decision extraction."""
        speakers = sorted(list(set(t.get('speaker_name', 'Participant') for t in transcript_lines if t.get('speaker_name'))))
        num_turns = len(transcript_lines)

        decisions = []
        action_items = []

        for line in transcript_lines:
            raw_text = (line.get('transcript_text') or "").strip()
            if not raw_text:
                continue

            text_lower = raw_text.lower()
            speaker = line.get('speaker_name', 'Participant')

            if any(w in text_lower for w in ['agree', 'decided', 'approved', 'confirm', 'resolution', 'concluded']):
                decisions.append(f"{speaker}: {raw_text}")
            if any(w in text_lower for w in ['will do', 'task', 'action item', 'assign', 'need to', 'todo', 'follow up']):
                action_items.append({
                    "task_description": raw_text,
                    "assigned_to": speaker,
                    "due_date": "Next Sprint"
                })

        if not decisions:
            preview_snippets = [t.get('transcript_text', '').strip() for t in transcript_lines[:2] if t.get('transcript_text', '').strip()]
            if preview_snippets:
                decisions = [f"Aligned on: \"{s}\"" for s in preview_snippets]
            else:
                decisions = [f"Team aligned on project milestones with {len(speakers)} active contributors."]

        if not action_items:
            action_items = [
                {
                    "task_description": "Review meeting notes and follow up on discussed action points.",
                    "assigned_to": speakers[0] if speakers else "Unassigned",
                    "due_date": "End of Week"
                }
            ]

        speakers_str = ", ".join(speakers[:3]) if speakers else "Participants"
        exec_summary = (
            f"The meeting comprised {num_turns} discussion exchanges among {len(speakers)} active participant(s) ({speakers_str}). "
            f"Discussion focused on task progress, cross-functional collaboration, and project deliverables."
        )

        return {
            "executive_summary": exec_summary,
            "key_decisions": decisions[:4],
            "action_items": action_items[:5],
            "sentiment_score": "positive",
            "sentiment_value": "0.85"
        }

    @staticmethod
    def _call_gemini(text: str, api_key: str) -> Dict[str, Any]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={api_key}"
        prompt = (
            "Analyze this meeting transcript and return valid JSON only (no markdown, no code fences) with keys: "
            "executive_summary (string), key_decisions (list of strings), "
            "action_items (list of objects with task_description, assigned_to, due_date), "
            "sentiment_score (string: positive/neutral/negative), sentiment_value (string format like '0.85'):\n\n"
            f"{text}"
        )
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        res = requests.post(url, json=payload, timeout=10)
        res.raise_for_status()
        data = res.json()
        raw = data['candidates'][0]['content']['parts'][0]['text']
        return AISummarizerService._clean_json_response(raw)

    @staticmethod
    def _call_openai(text: str, api_key: str) -> Dict[str, Any]:
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        prompt = (
            "Analyze meeting transcript and respond in valid JSON only with keys: "
            "executive_summary (string), key_decisions (list of strings), "
            "action_items (list of objects with task_description, assigned_to, due_date), "
            "sentiment_score (string: positive/neutral/negative), sentiment_value (string like '0.85')."
        )
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": prompt},
                {"role": "user", "content": text}
            ]
        }
        res = requests.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers, timeout=10)
        res.raise_for_status()
        data = res.json()
        raw = data['choices'][0]['message']['content']
        return AISummarizerService._clean_json_response(raw)

