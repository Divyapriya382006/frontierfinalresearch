"""
Fetches candidate datasets for a topic from multiple sources - Kaggle,
Tavily (open web search), and Papers with Code - and normalizes them into
a single consistent shape for the recommender/agent to work with.

Each source is independent and best-effort: a missing API key or a failed
request just means that source contributes nothing, it never crashes the
pipeline. If ALL sources come up empty (e.g. fully offline, no keys set
anywhere), a small static fallback list keeps the demo alive.
"""
import logging
from typing import List, Dict, Any

from person_3_dataset_planner.dataset.kaggle_client import KaggleClient
from person_3_dataset_planner.dataset.tavily_client import TavilyClient
from person_3_dataset_planner.dataset.paperswithcode import PapersWithCodeClient

logger = logging.getLogger("research_agent_x.benchmark_fetcher")

_FALLBACK_DATASETS = [
    {
        "name": "FLORES-200",
        "description": "Multilingual parallel evaluation benchmark covering 200 languages, many low-resource.",
        "url": "https://paperswithcode.com/dataset/flores-200",
        "task": "machine-translation",
        "num_papers": 45,
        "source": "fallback",
    },
    {
        "name": "MasakhaNER",
        "description": "Named entity recognition dataset for 10 African languages.",
        "url": "https://paperswithcode.com/dataset/masakhaner",
        "task": "named-entity-recognition",
        "num_papers": 22,
        "source": "fallback",
    },
    {
        "name": "XTREME",
        "description": "Cross-lingual benchmark covering 40 languages and 9 tasks for evaluating multilingual representations.",
        "url": "https://paperswithcode.com/dataset/xtreme",
        "task": "cross-lingual-transfer",
        "num_papers": 130,
        "source": "fallback",
    },
]


def _normalize_kaggle(raw: Dict[str, Any]) -> Dict[str, Any]:
    ref = raw.get("ref", "")
    return {
        "name": raw.get("title") or ref or "Unknown Kaggle dataset",
        "description": raw.get("subtitle") or "",
        "url": f"https://www.kaggle.com/datasets/{ref}" if ref else "",
        "task": "",
        "num_papers": 0,
        "source": "kaggle",
    }


def _normalize_tavily(raw: Dict[str, Any]) -> Dict[str, Any]:
    content = raw.get("content") or ""
    return {
        "name": raw.get("title") or "Untitled web result",
        "description": (content[:280] + "...") if len(content) > 280 else content,
        "url": raw.get("url") or "",
        "task": "",
        "num_papers": 0,
        "source": "tavily",
    }


def _normalize_pwc(raw: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "name": raw.get("name") or raw.get("full_name") or "Unknown dataset",
        "description": raw.get("description") or "",
        "url": raw.get("url") or raw.get("homepage") or "",
        "task": (raw.get("tasks") or [{}])[0].get("name") if raw.get("tasks") else raw.get("task", ""),
        "num_papers": raw.get("num_papers", 0),
        "source": "paperswithcode",
    }


def fetch_candidate_datasets(topic: str, max_results: int = 20) -> List[Dict[str, Any]]:
    """
    Returns a merged, de-duplicated list of normalized candidate dataset
    dicts for the given topic, pulled from Kaggle + Tavily + Papers with
    Code (whichever are configured). Falls back to a small static list only
    if every source returns nothing.
    """
    candidates: List[Dict[str, Any]] = []

    kaggle_raw = KaggleClient().search_datasets(topic, max_results=max_results)
    candidates.extend(_normalize_kaggle(r) for r in kaggle_raw)
    logger.info("Kaggle: %d results for %r", len(kaggle_raw), topic)

    tavily_raw = TavilyClient().search_datasets(topic, max_results=max_results)
    candidates.extend(_normalize_tavily(r) for r in tavily_raw)
    logger.info("Tavily: %d results for %r", len(tavily_raw), topic)

    pwc_raw = PapersWithCodeClient().search_datasets(topic, items_per_page=max_results)
    candidates.extend(_normalize_pwc(r) for r in pwc_raw)
    logger.info("Papers with Code: %d results for %r", len(pwc_raw), topic)

    if not candidates:
        logger.info("No live results from any source for %r, using fallback dataset list.", topic)
        return _FALLBACK_DATASETS

    # De-dupe by (lowercased name, url) - cheap, catches the common case of
    # the same dataset surfacing from more than one source.
    seen = set()
    deduped = []
    for c in candidates:
        key = (c["name"].strip().lower(), c["url"].strip().lower())
        if key not in seen:
            seen.add(key)
            deduped.append(c)

    return deduped[:max_results]
