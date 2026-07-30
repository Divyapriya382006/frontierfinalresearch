"""
person_1_literature_ranking/main.py

Entry point for Person 1's module. Exposes:
  1. A FastAPI app with a /search endpoint (so person 4's orchestrator can
     call this module as a microservice), and
  2. A CLI mode for standalone testing: `python main.py "your query"`

Run the API server:
    uvicorn person_1_literature_ranking.main:app --reload --port 8001

Run the CLI:
    python -m person_1_literature_ranking.main "graph neural networks for drug discovery"
"""

import argparse
import json
import sys

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional

from shared.utils.config import settings
from shared.utils.constants import DEFAULT_TOP_K
from shared.utils.logger import get_logger
from shared.utils.validators import ValidationError

from person_1_literature_ranking.services.ranking_service import RankingService

logger = get_logger(__name__)

app = FastAPI(
    title="ResearchAgentX - Literature Search & Ranking",
    description="Person 1's module: fetches papers from Semantic Scholar, arXiv, "
    "OpenAlex, Google Scholar, and Tavily, deduplicates them, and ranks "
    "them by relevance, citation impact, and recency.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

ranking_service = RankingService()


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Research topic / search query")
    top_k: int = Field(DEFAULT_TOP_K, ge=1, le=100)
    sources: Optional[List[str]] = Field(
        default=None,
        description="Subset of ['semantic_scholar', 'arxiv', 'openalex', 'google_scholar', 'tavily']",
    )
    save: bool = Field(default=False, description="Persist results to outputs/papers.json")


class PaperResponse(BaseModel):
    title: str
    abstract: str
    authors: List[str]
    year: Optional[int]
    venue: Optional[str]
    url: Optional[str]
    pdf_url: Optional[str]
    doi: Optional[str]
    source: str
    citation_count: int
    fields_of_study: List[str]
    relevance_score: float
    citation_score: float
    recency_score: float
    final_score: float


class SearchResponse(BaseModel):
    query: str
    count: int
    papers: List[PaperResponse]


@app.get("/health")
def health():
    return {"status": "ok", "service": "person_1_literature_ranking"}


@app.post("/search", response_model=SearchResponse)
def search(request: SearchRequest):
    """Fetch, dedup, and rank papers for the given query."""
    try:
        papers = ranking_service.search_and_rank(
            query=request.query,
            top_k=request.top_k,
            sources=request.sources,
            save=request.save,
        )
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:  # noqa: BLE001
        logger.exception("Unexpected error during /search")
        raise HTTPException(status_code=500, detail="Internal error while ranking papers") from exc

    return SearchResponse(
        query=request.query,
        count=len(papers),
        papers=[PaperResponse(**p.to_dict()) for p in papers],
    )


@app.get("/search", response_model=SearchResponse)
def search_get(
    query: str = Query(..., min_length=1),
    top_k: int = Query(DEFAULT_TOP_K, ge=1, le=100),
):
    """Convenience GET variant for quick manual testing / browser use."""
    return search(SearchRequest(query=query, top_k=top_k))


def _run_cli():
    parser = argparse.ArgumentParser(description="Search and rank academic literature.")
    parser.add_argument("query", type=str, help="Research topic to search for")
    parser.add_argument("--top-k", type=int, default=DEFAULT_TOP_K, help="Number of results to return")
    parser.add_argument(
        "--limit-per-source",
        type=int,
        default=None,
        help="How many candidates to request from each source before ranking",
    )
    parser.add_argument(
        "--min-year",
        type=int,
        default=None,
        help="Only keep papers published in or after this year",
    )
    parser.add_argument(
        "--sources",
        type=str,
        default=None,
        help="Comma-separated sources: semantic_scholar,arxiv,openalex,google_scholar,tavily",
    )
    parser.add_argument("--save", action="store_true", help="Save results to outputs/papers.json")
    args = parser.parse_args()

    sources = args.sources.split(",") if args.sources else None

    try:
        papers = ranking_service.search_and_rank(
            query=args.query,
            top_k=args.top_k,
            sources=sources,
            limit_per_source=args.limit_per_source,
            min_year=args.min_year,
            save=args.save,
        )
    except ValidationError as exc:
        print(f"Invalid input: {exc}", file=sys.stderr)
        sys.exit(1)

    print(json.dumps([p.to_dict() for p in papers], indent=2, ensure_ascii=False))
    print(f"\n{len(papers)} papers returned for query: {args.query!r}", file=sys.stderr)


if __name__ == "__main__":
    _run_cli()
