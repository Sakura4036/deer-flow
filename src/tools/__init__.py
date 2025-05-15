# Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT

import os

from .crawl import crawl_tool
from .python_repl import python_repl_tool
from .search import (
    tavily_search_tool,
    duckduckgo_search_tool,
    brave_search_tool,
    arxiv_search_tool,
    pubmed_search_tool,
    semantic_scholar_search_tool,
    patsnap_search_tool
)
from .tts import VolcengineTTS
from src.config import (
    SELECTED_SEARCH_ENGINE, SearchEngine,
    SELECTED_LITERATURE_SEARCH_ENGINE, LiteratureSearchEngine,
    SELECTED_PATENT_SEARCH_ENGINE, PatentSearchEngine
)

# Map search engine names to their respective tools
search_tool_mappings = {
    SearchEngine.TAVILY.value: tavily_search_tool,
    SearchEngine.DUCKDUCKGO.value: duckduckgo_search_tool,
    SearchEngine.BRAVE_SEARCH.value: brave_search_tool,
    SearchEngine.ARXIV.value: arxiv_search_tool,
}

literature_search_tool_mappings = {
    LiteratureSearchEngine.PUBMED.value: pubmed_search_tool,
    LiteratureSearchEngine.SEMANTIC_SCHOLAR.value: semantic_scholar_search_tool,
    LiteratureSearchEngine.ARXIV.value: arxiv_search_tool,
}

patent_search_tool_mappings = {
    PatentSearchEngine.PATSNAP.value: patsnap_search_tool,
}

web_search_tool = search_tool_mappings.get(SELECTED_SEARCH_ENGINE, tavily_search_tool)
literature_search_tool = literature_search_tool_mappings.get(SELECTED_LITERATURE_SEARCH_ENGINE, pubmed_search_tool)
patent_search_tool = patent_search_tool_mappings.get(SELECTED_PATENT_SEARCH_ENGINE, patsnap_search_tool)

__all__ = [
    "crawl_tool",
    "web_search_tool",
    "python_repl_tool",
    "VolcengineTTS",
    "literature_search_tool",
    "patent_search_tool",
]
