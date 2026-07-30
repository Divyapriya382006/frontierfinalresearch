# Person 1 — Literature Search & Ranking

Fetches candidate papers from **Semantic Scholar**, **arXiv**, and **OpenAlex**,
removes duplicates, and ranks them by a weighted combination of:

- **Relevance** — TF-IDF cosine similarity between the query and each paper's title+abstract
- **Citation impact** — log-scaled, normalized citation count
- **Recency** — exponential decay based on publication year

## Setup

```bash
cd person_1_literature_ranking
pip install -r requirements.txt
# also install the shared package's needs from the repo root if not already:
pip install -r ../requirements.txt  # if present
```

Copy `.env.example` from the repo root to `.env` and fill in optional keys
(a Semantic Scholar API key raises your rate limit but isn't required).

## Run as an API server

```bash
uvicorn person_1_literature_ranking.main:app --reload --port 8001
```

Then:

```bash
curl -X POST http://localhost:8001/search \
  -H "Content-Type: application/json" \
  -d '{"query": "graph neural networks for drug discovery", "top_k": 10}'
```

or simply `GET http://localhost:8001/search?query=...&top_k=10`.

## Run from the CLI

```bash
python -m person_1_literature_ranking.main "graph neural networks for drug discovery" --top-k 10 --save
```

`--save` writes the ranked results to `outputs/papers.json`, which is the
file format `shared/sample_outputs/papers.json` documents and that Person 2
(summary/gap) and the orchestrator (Person 4) consume.

## Run tests

```bash
pytest person_1_literature_ranking/tests -v
```

## Module layout

```
person_1_literature_ranking/
├── api/                 # Source-specific HTTP clients
│   ├── semantic_scholar.py
│   ├── arxiv.py
│   ├── openalex.py
│   └── paper_fetcher.py # Fans out to all 3 sources concurrently
├── ranking/
│   ├── relevance_score.py   # TF-IDF cosine similarity
│   ├── duplicate_remover.py # Exact + fuzzy dedup across sources
│   ├── score_calculator.py  # Weighted final score
│   └── ranker.py            # Orchestrates the full ranking pipeline
├── services/
│   ├── literature_service.py # Validated fetch-only entry point
│   └── ranking_service.py    # Full fetch -> rank -> (optional) persist
├── tests/
├── outputs/              # papers.json gets written here with --save
├── main.py                # FastAPI app + CLI
└── requirements.txt
```

## Output schema (per paper)

```json
{
  "title": "string",
  "abstract": "string",
  "authors": ["string"],
  "year": 2023,
  "venue": "string",
  "url": "string",
  "pdf_url": "string",
  "doi": "string",
  "source": "semantic_scholar | arxiv | openalex",
  "citation_count": 0,
  "fields_of_study": ["string"],
  "relevance_score": 0.0,
  "citation_score": 0.0,
  "recency_score": 0.0,
  "final_score": 0.0
}
```

## Tuning ranking weights

Set env vars (defaults shown):

```
WEIGHT_RELEVANCE=0.5
WEIGHT_CITATIONS=0.3
WEIGHT_RECENCY=0.2
DUPLICATE_SIMILARITY_THRESHOLD=0.88
```
