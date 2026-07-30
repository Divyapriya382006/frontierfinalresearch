"""
Cheap keyword-overlap ranking used to pre-filter candidate datasets before
handing a shortlist to the LLM agent (keeps prompts small and cheap).
"""
import re
from typing import List, Dict, Any

_WORD_RE = re.compile(r"[a-zA-Z]+")


def _tokenize(text: str) -> set:
    return {w.lower() for w in _WORD_RE.findall(text or "")}


def rank_by_keyword_overlap(topic: str, candidates: List[Dict[str, Any]], top_k: int = 10) -> List[Dict[str, Any]]:
    """
    Scores each candidate dataset by token overlap between the topic and the
    dataset's name/description/task, then returns the top_k highest-scoring
    candidates (stable sort, ties broken by original order).
    """
    topic_tokens = _tokenize(topic)
    if not topic_tokens:
        return candidates[:top_k]

    scored = []
    for idx, candidate in enumerate(candidates):
        text = " ".join([
            candidate.get("name", ""),
            candidate.get("description", ""),
            candidate.get("task", ""),
        ])
        candidate_tokens = _tokenize(text)
        overlap = len(topic_tokens & candidate_tokens)
        scored.append((overlap, -idx, candidate))

    scored.sort(key=lambda t: (t[0], t[1]), reverse=True)
    return [c for _, _, c in scored[:top_k]]
