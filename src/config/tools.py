# Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT

import os
import enum
from dotenv import load_dotenv

load_dotenv()


class SearchEngine(enum.Enum):
    TAVILY = "tavily"
    DUCKDUCKGO = "duckduckgo"
    BRAVE_SEARCH = "brave_search"
    ARXIV = "arxiv"


class LiteratureSearchEngine(enum.Enum):
    PUBMED = "pubmed"
    SEMANTIC_SCHOLAR = "semantic_scholar"
    ARXIV = "arxiv"

class PatentSearchEngine(enum.Enum):
    PATSNAP = "patsnap"
    PATENTS_VIEW = "patents_view"

# Tool configuration
SELECTED_SEARCH_ENGINE = os.getenv("SEARCH_API", SearchEngine.TAVILY.value)
SELECTED_LITERATURE_SEARCH_ENGINE = os.getenv("LITERATURE_SEARCH_API", LiteratureSearchEngine.PUBMED.value)
SELECTED_PATENT_SEARCH_ENGINE = os.getenv("PATENT_SEARCH_API", PatentSearchEngine.PATSNAP.value)

SEARCH_MAX_RESULTS = 5
SEARCH_CONTENT_MAX_LENGTH = 4000
