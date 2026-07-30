"""
shared/utils/constants.py

Shared constant values used across the ResearchAgentX pipeline.
"""

# Paper sources
SOURCE_SEMANTIC_SCHOLAR = "semantic_scholar"
SOURCE_ARXIV = "arxiv"
SOURCE_OPENALEX = "openalex"
SOURCE_GOOGLE_SCHOLAR = "google_scholar"
SOURCE_TAVILY = "tavily"

ALL_SOURCES = [
    SOURCE_SEMANTIC_SCHOLAR,
    SOURCE_ARXIV,
    SOURCE_OPENALEX,
    SOURCE_GOOGLE_SCHOLAR,
    SOURCE_TAVILY,
]

# Ranking defaults
DEFAULT_TOP_K = 20
MIN_ABSTRACT_LENGTH = 20

# Date formats
ISO_DATE_FORMAT = "%Y-%m-%d"

# HTTP
DEFAULT_USER_AGENT = "ResearchAgentX/1.0 (literature-ranking-agent)"

# Output paths
DEFAULT_OUTPUT_FILENAME = "papers.json"
