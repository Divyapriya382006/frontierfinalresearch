# Person 2 — Summary & Gap Finder

This module owns two things in ResearchAgentX's pipeline:

1. **Summarizer** — turns a list of papers (from Person 1) into per-paper
   structured summaries plus one overall narrative synthesis.
2. **Gap Finder** — takes those summaries, detects novelty/limitations per
   paper, and synthesizes cross-paper research gaps + opportunities.

## Layout

```
person_2_summary_gap/
├── main.py                     FastAPI app (routes: /summarize, /find-gaps, /pipeline)
├── summarizer/
│   ├── paper_summary.py        prompt building + response parsing for ONE paper
│   ├── summary_agent.py        calls Claude, orchestrates all papers
│   └── overall_summary.py      aggregates PaperSummary list -> OverallSummary
├── gap_finder/
│   ├── novelty_detector.py     per-paper: what's novel about this paper?
│   ├── limitation_detector.py  per-paper: what does this paper NOT address?
│   └── gap_agent.py            synthesizes cross-paper gaps from the above
├── services/
│   ├── summary_service.py      API-facing wrapper, saves outputs/summary.json
│   └── gap_service.py          API-facing wrapper, saves outputs/gaps.json
└── tests/
    ├── test_summarizer.py      offline, mocks the Anthropic client
    └── test_gap_finder.py      offline, mocks the Anthropic client
```

Depends on `shared/schemas`, `shared/prompts`, and `shared/utils` (also
included in this zip) — these are common contracts the whole team uses,
so don't fork them locally.

## Setup

```bash
cd ResearchAgentX
pip install -r person_2_summary_gap/requirements.txt
cp .env.example .env      # then fill in ANTHROPIC_API_KEY
```

## Run the service standalone

```bash
uvicorn person_2_summary_gap.main:app --reload --port 8002
```

Then:

```bash
curl -X POST http://localhost:8002/summarize \
  -H "Content-Type: application/json" \
  -d '{"papers": [{"id": "p1", "title": "Example Paper", "abstract": "..."}]}'
```

`/pipeline` runs summarize -> gap-finding in one call, which is the shape
Person 4's orchestrator will most likely use.

## Run tests

```bash
pytest person_2_summary_gap/tests -v
```

Tests mock the Anthropic client entirely (no API key/network needed) so
they're fast and safe to run in CI.

## Output contracts

- `OverallSummary` / `PaperSummary` — see `shared/schemas/summary_schema.py`
- `GapAnalysis` / `ResearchGap` — see `shared/schemas/gap_schema.py`

Both are also written to `person_2_summary_gap/outputs/*.json` on every run
so Person 3/4 can consume them as files if they'd rather not call the API.

## What's still TODO / open for you to extend

- Swap the local keyword-counting in `overall_summary.py` for something
  smarter (e.g. embedding-based clustering) if time allows.
- Add caching so re-running the same paper doesn't re-call the API.
- Wire `main.py` into Person 4's orchestrator graph (`backend/orchestrator/graph.py`).
- Add real integration tests once a live `ANTHROPIC_API_KEY` is available.
