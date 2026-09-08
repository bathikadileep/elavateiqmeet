"""
ElevateIQ — Meeting Participant Interaction Graph Builder
==========================================================
Constructs directed interaction graphs showing participant-to-participant dialogue flow,
cross-talk density matrices, and centrality scores.
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

log = logging.getLogger("elevateiq.services.ai.graph")


class MeetingGraphBuilderService:
    """Participant Interaction Graph & Social Network Centrality Engine."""

    @staticmethod
    def build_interaction_graph(transcript_lines: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Build adjacency matrix of directed dialogue exchanges between consecutive speakers.
        """
        if not transcript_lines:
            return {"nodes": [], "edges": [], "centrality": {}}

        nodes_set = set()
        edges_map: Dict[str, int] = {}
        speaker_turn_count: Dict[str, int] = {}

        for i in range(len(transcript_lines)):
            curr_speaker = (transcript_lines[i].get("speaker_name") or "Participant").strip()
            nodes_set.add(curr_speaker)
            speaker_turn_count[curr_speaker] = speaker_turn_count.get(curr_speaker, 0) + 1

            if i > 0:
                prev_speaker = (transcript_lines[i - 1].get("speaker_name") or "Participant").strip()
                if prev_speaker != curr_speaker:
                    edge_key = f"{prev_speaker}->{curr_speaker}"
                    edges_map[edge_key] = edges_map.get(edge_key, 0) + 1

        nodes = [{"id": n, "label": n, "turns": speaker_turn_count.get(n, 0)} for n in nodes_set]
        edges = []
        for edge_key, weight in edges_map.items():
            source, target = edge_key.split("->")
            edges.append({"source": source, "target": target, "weight": weight})

        # Calculate Degree Centrality
        total_interactions = sum(edges_map.values())
        centrality = {}
        for n in nodes_set:
            interactions_for_n = sum(w for k, w in edges_map.items() if n in k)
            centrality[n] = round((interactions_for_n / max(total_interactions, 1)) * 100.0, 1)

        return {
            "nodes": nodes,
            "edges": edges,
            "degree_centrality_pct": centrality,
            "total_exchanges": total_interactions,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
