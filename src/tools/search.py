# Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT

import json
import logging
import os

from langchain_community.tools import BraveSearch, DuckDuckGoSearchResults, PubmedQueryRun
from langchain_community.tools.arxiv import ArxivQueryRun
from langchain_community.utilities import ArxivAPIWrapper, BraveSearchWrapper, PubMedAPIWrapper

from src.config import SEARCH_MAX_RESULTS, SearchEngine, SEARCH_CONTENT_MAX_LENGTH
from src.tools.tavily_search.tavily_search_results_with_images import (
    TavilySearchResultsWithImages,
)
from src.tools.patsnap import PatsnapAPIClient, PatsnapQueryRun, PatsnapAPIWrapper
from src.tools.semantic_scholar import SemanticScholarAPIWrapper, SemanticScholarQueryRun
from src.tools.decorators import create_logged_tool

logger = logging.getLogger(__name__)

LoggedTavilySearch = create_logged_tool(TavilySearchResultsWithImages)
if os.getenv("SEARCH_API", "") == SearchEngine.TAVILY.value:
    tavily_search_tool = LoggedTavilySearch(
        name="web_search",
        max_results=SEARCH_MAX_RESULTS,
        include_raw_content=True,
        include_images=True,
        include_image_descriptions=True,
    )
else:
    tavily_search_tool = None

LoggedDuckDuckGoSearch = create_logged_tool(DuckDuckGoSearchResults)
duckduckgo_search_tool = LoggedDuckDuckGoSearch(
    name="web_search", max_results=SEARCH_MAX_RESULTS
)

LoggedBraveSearch = create_logged_tool(BraveSearch)
brave_search_tool = LoggedBraveSearch(
    name="web_search",
    search_wrapper=BraveSearchWrapper(
        api_key=os.getenv("BRAVE_SEARCH_API_KEY", ""),
        search_kwargs={"count": SEARCH_MAX_RESULTS},
    ),
)

LoggedArxivSearch = create_logged_tool(ArxivQueryRun)
arxiv_search_tool = LoggedArxivSearch(
    name="web_search",
    api_wrapper=ArxivAPIWrapper(
        top_k_results=SEARCH_MAX_RESULTS,
        load_max_docs=SEARCH_MAX_RESULTS,
        load_all_available_meta=True,
    ),
)

LoggedPubmedSearch = create_logged_tool(PubmedQueryRun)
pubmed_search_tool = LoggedPubmedSearch(
    name="web_search",
    api_wrapper=PubMedAPIWrapper(
        top_k_results=SEARCH_MAX_RESULTS,
        doc_content_chars_max=SEARCH_CONTENT_MAX_LENGTH,
        api_key=os.getenv("PUBMED_SEARCH_API_KEY", ""),
    ),
)


LoggedSemanticScholarSearch = create_logged_tool(SemanticScholarQueryRun)
semantic_scholar_search_tool = LoggedSemanticScholarSearch(
    name="web_search",
    api_wrapper=SemanticScholarAPIWrapper(
        top_k_results=SEARCH_MAX_RESULTS,
        doc_content_chars_max=SEARCH_CONTENT_MAX_LENGTH,
        api_key=os.getenv("SEMANTIC_SCHOLAR_API_KEY", ""),
    ),
)


LoggedPatsnapSearch = create_logged_tool(PatsnapQueryRun)
patsnap_search_tool = LoggedPatsnapSearch(
    name="web_search",
    api_wrapper=PatsnapAPIWrapper(
        patsnap_client=PatsnapAPIClient(),
        top_k_results=SEARCH_MAX_RESULTS,
        doc_content_chars_max=SEARCH_CONTENT_MAX_LENGTH,
    ),
)

if __name__ == "__main__":
    # results = LoggedDuckDuckGoSearch(
    #     name="web_search", max_results=SEARCH_MAX_RESULTS, output_format="list"
    # ).invoke("cute panda")
    # print(json.dumps(results, indent=2, ensure_ascii=False))

    # results = pubmed_search_tool.invoke("panda")
    # print(results)
    # print("-="*30+'\n\n')

    # results = arxiv_search_tool.invoke("panda")
    # print(results)
    # print("-="*30+'\n\n')

    results = patsnap_search_tool.invoke("panda")
    print(results)
    print("-="*30+'\n\n')
