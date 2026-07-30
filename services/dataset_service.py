"""
Orchestrates the dataset-recommendation pipeline end to end and writes
outputs/datasets.json (the file the connector/Person 4 consumes).
"""
import json
import logging
from pathlib import Path
from typing import Optional

from person_3_dataset_planner.dataset.benchmark_fetcher import fetch_candidate_datasets
from person_3_dataset_planner.dataset.recommender import rank_by_keyword_overlap
from person_3_dataset_planner.dataset.dataset_agent import recommend_datasets
from shared.schemas.dataset_schema import DatasetRecommendation

logger = logging.getLogger("research_agent_x.dataset_service")

OUTPUT_DIR = Path(__file__).resolve().parents[1] / "outputs"


def run_dataset_pipeline(
    topic: str,
    summary: str = "",
    gaps: str = "",
    max_candidates: int = 20,
    shortlist_size: int = 10,
    write_output: bool = True,
) -> DatasetRecommendation:
    """
    Full pipeline: fetch candidates from Papers with Code -> pre-filter by
    keyword overlap -> ask the LLM agent to pick and justify the final list.
    """
    logger.info("Fetching candidate datasets for topic: %r", topic)
    raw_candidates = fetch_candidate_datasets(topic, max_results=max_candidates)

    shortlist = rank_by_keyword_overlap(topic, raw_candidates, top_k=shortlist_size)
    logger.info("Shortlisted %d/%d candidates.", len(shortlist), len(raw_candidates))

    recommendation = recommend_datasets(topic, shortlist, summary=summary, gaps=gaps)

    if write_output:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        out_path = OUTPUT_DIR / "datasets.json"
        out_path.write_text(json.dumps(recommendation.to_dict(), indent=2), encoding="utf-8")
        logger.info("Wrote %s", out_path)

    return recommendation


def _coerce_person2_payload(payload: Optional[dict]) -> str:
    if not payload:
        return ""
    if isinstance(payload, str):
        return payload
    if isinstance(payload, dict):
        if "overall_summary" in payload and isinstance(payload["overall_summary"], dict):
            summary = payload["overall_summary"]
            if "synthesis" in summary and summary["synthesis"]:
                return summary["synthesis"]
            if "key_trends" in summary and summary["key_trends"]:
                return summary["key_trends"]
            if "paper_summaries" in summary and isinstance(summary["paper_summaries"], list):
                parts = []
                for paper in summary["paper_summaries"]:
                    if isinstance(paper, dict):
                        title = paper.get("title") or ""
                        tldr = paper.get("tldr") or paper.get("summary") or ""
                        if title or tldr:
                            parts.append(f"{title}: {tldr}".strip())
                if parts:
                    return " | ".join(parts)
        if "gaps" in payload and isinstance(payload["gaps"], dict):
            return json.dumps(payload["gaps"], indent=2)
        return json.dumps(payload, indent=2)
    return str(payload)


def load_context_from_person2(
    summary_path: Optional[Path] = None,
    gaps_path: Optional[Path] = None,
    summary_payload: Optional[dict] = None,
    gaps_payload: Optional[dict] = None,
) -> tuple:
    """
    Convenience loader for Person 2's summary and gaps payloads, so this
    module can be tested standalone before integration. Falls back to the
    shared sample outputs if no real files or payloads are provided yet.
    """
    root = Path(__file__).resolve().parents[2]
    summary_path = summary_path or root / "shared" / "sample_outputs" / "summary.json"
    gaps_path = gaps_path or root / "shared" / "sample_outputs" / "gaps.json"

    summary_text, gaps_text = "", ""
    if summary_payload is not None:
        summary_text = _coerce_person2_payload(summary_payload)
    elif summary_path.exists():
        summary_text = json.dumps(json.loads(summary_path.read_text(encoding="utf-8")))

    if gaps_payload is not None:
        gaps_text = _coerce_person2_payload(gaps_payload)
    elif gaps_path.exists():
        gaps_text = json.dumps(json.loads(gaps_path.read_text(encoding="utf-8")))

    return summary_text, gaps_text
