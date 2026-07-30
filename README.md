# Person 3 — Dataset Recommendation & Experiment Planner

Owns: dataset discovery (Kaggle + Tavily + Papers with Code), dataset
recommendation agent, and experiment planning agent (methodology +
evaluation + timeline).

## Contract with the rest of the team

Per `docs/api_contract.md`:

```
POST /planner
Input:  { "topic": str, "summary"?: str, "gaps"?: str, "total_weeks"?: float }
Output: { "datasets": DatasetRecommendation, "experiment": ExperimentPlan }
```

Writes:
- `outputs/datasets.json` — matches `shared/schemas/dataset_schema.py`
- `outputs/experiment.json` — matches `shared/schemas/experiment_schema.py`

Person 4's connector reads both files (or hits `/planner` directly) to build
the final proposal.

## Setup

```bash
cd person_3_dataset_planner
pip install -r requirements.txt
```

### Dataset discovery sources (Kaggle + Tavily + Papers with Code)

`dataset_service.py` pulls candidates from all three sources and merges/de-dupes
them. Each is independent and optional — if a key is missing, that source
just contributes nothing (never a crash). Set whichever you're using:

**Kaggle** (https://www.kaggle.com/settings/account → "Create New Token"):
```bash
export KAGGLE_USERNAME=your-kaggle-username
export KAGGLE_KEY=your-kaggle-api-key
```

**Tavily** (https://app.tavily.com → API Keys) — a web-search API for AI
agents; it crawls and returns clean results server-side, so this covers
datasets that live outside Kaggle/Papers with Code (gov portals, GitHub, university pages):
```bash
export TAVILY_API_KEY=tvly-...
```

**Papers with Code** needs no key — always attempted automatically.

If none of the above return anything (all offline/unconfigured), a small
static fallback list keeps the pipeline from breaking.

### LLM provider (planner + dataset justification)

Set `LLM_PROVIDER` to pick which backend the agents use. Pick ONE:

**Groq (free tier, very fast — https://console.groq.com/keys):**
```bash
export LLM_PROVIDER=groq
export GROQ_API_KEY=gsk_...
```

**Google Gemini (free tier — https://aistudio.google.com/apikey):**
```bash
pip install google-genai
export LLM_PROVIDER=gemini
export GEMINI_API_KEY=...
```

**Anthropic Claude:**
```bash
export LLM_PROVIDER=anthropic
export ANTHROPIC_API_KEY=sk-ant-...
```

**Ollama (fully local, no key/cost at all — https://ollama.com):**
```bash
# 1. Install Ollama, then in a separate terminal:
ollama pull llama3.1
ollama serve
# 2. Point this service at it:
export LLM_PROVIDER=ollama
```

If none of these are configured, everything runs in DRY_RUN mode automatically (see below) — no crash, just stub output.

## Run standalone (no server, uses mock Person 2 data)

```bash
# from the repo root, so shared/ and person_3_dataset_planner/ are importable
python -m person_3_dataset_planner.main
```

This uses `shared/sample_outputs/summary.json` and `gaps.json` as stand-ins
for Person 2's real output, so you can build and test this module before
integration day. `summary` and `gaps` are also optional fields on the
`POST /planner` request — you can omit them entirely (empty string default)
and the pipeline still runs fine, just with less context for the LLM to
work with.

## Run as a service

```bash
uvicorn person_3_dataset_planner.main:app --reload --port 8003
```

```bash
curl -X POST http://localhost:8003/planner \
  -H "Content-Type: application/json" \
  -d '{"topic": "Efficient fine-tuning of LLMs for low-resource languages", "total_weeks": 8}'
```

## DRY_RUN mode

If no LLM_PROVIDER key is configured, every agent falls back to
deterministic stub output instead of crashing — this exists so the demo
never breaks on stage because of a missing env var. Set a key (Groq,
Gemini, Anthropic, or run Ollama locally) to get real LLM-generated dataset
justifications, methodology, and evaluation plans. Dataset discovery
(Kaggle/Tavily/Papers with Code) is independent of this — it's live
whenever those keys are set, regardless of your LLM_PROVIDER choice.

## Run tests

```bash
pytest person_3_dataset_planner/tests -v
```

## Module layout

```
person_3_dataset_planner/
├── main.py                      # FastAPI app, POST /planner
├── dataset/
│   ├── kaggle_client.py         # Kaggle dataset search
│   ├── tavily_client.py         # Tavily web search (finds datasets off Kaggle/PWC)
│   ├── paperswithcode.py        # Papers with Code client (no key needed)
│   ├── benchmark_fetcher.py     # merges + normalizes candidates from all 3 sources
│   ├── recommender.py           # cheap keyword-overlap pre-filter
│   └── dataset_agent.py         # LLM: final pick + justification
├── planner/
│   ├── methodology.py           # default/fallback methodology
│   ├── evaluation.py            # default/fallback evaluation plan
│   ├── timeline.py              # deterministic timeline builder
│   └── planner_agent.py         # LLM: methodology + evaluation + timeline
├── services/
│   ├── dataset_service.py       # pipeline glue -> outputs/datasets.json
│   └── planner_service.py       # pipeline glue -> outputs/experiment.json
├── tests/
└── outputs/
```
