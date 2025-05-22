# Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT

import json
import logging
import os

from langchain_community.tools import BraveSearch, DuckDuckGoSearchResults
from langchain_community.tools.arxiv import ArxivQueryRun
from langchain_community.utilities import ArxivAPIWrapper, BraveSearchWrapper, PubMedAPIWrapper

from src.config import (SearchEngine, SELECTED_SEARCH_ENGINE,
                        PatentSearchEngine, SELECTED_PATENT_ENGINE,
                        LiteratureSearchEngine, SELECTED_LITERATURE_ENGINE
                        )
from src.tools.tavily_search.tavily_search_results_with_images import (
    TavilySearchResultsWithImages,
)
from src.tools.pubmed import MyPubmedQueryRun
from src.tools.patsnap import PatsnapAPIClient, PatsnapQueryRun, PatsnapAPIWrapper
from src.tools.patents_view import PatentsViewAPIClient, PatentsViewQueryRun, PatentsViewAPIWrapper
from src.tools.semantic_scholar import SemanticScholarAPIWrapper, SemanticScholarQueryRun
from src.tools.decorators import create_logged_tool

logger = logging.getLogger(__name__)

# Create logged versions of the search tools
LoggedTavilySearch = create_logged_tool(TavilySearchResultsWithImages)
LoggedDuckDuckGoSearch = create_logged_tool(DuckDuckGoSearchResults)
LoggedBraveSearch = create_logged_tool(BraveSearch)
LoggedArxivSearch = create_logged_tool(ArxivQueryRun)


# Get the selected search tool
def get_web_search_tool(max_search_results: int):
    if SELECTED_SEARCH_ENGINE == SearchEngine.TAVILY.value:
        return LoggedTavilySearch(
            name="web_search",
            max_results=max_search_results,
            include_raw_content=True,
            include_images=True,
            include_image_descriptions=True,
        )
    elif SELECTED_SEARCH_ENGINE == SearchEngine.DUCKDUCKGO.value:
        return LoggedDuckDuckGoSearch(name="web_search", max_results=max_search_results)
    elif SELECTED_SEARCH_ENGINE == SearchEngine.BRAVE_SEARCH.value:
        return LoggedBraveSearch(
            name="web_search",
            search_wrapper=BraveSearchWrapper(
                api_key=os.getenv("BRAVE_SEARCH_API_KEY", ""),
                search_kwargs={"count": max_search_results},
            ),
        )
    elif SELECTED_SEARCH_ENGINE == SearchEngine.ARXIV.value:
        return LoggedArxivSearch(
            name="web_search",
            api_wrapper=ArxivAPIWrapper(
                top_k_results=max_search_results,
                load_max_docs=max_search_results,
                load_all_available_meta=True,
            ),
        )
    else:
        raise ValueError(f"Unsupported search engine: {SELECTED_SEARCH_ENGINE}")


LoggedPubmedSearch = create_logged_tool(MyPubmedQueryRun)
LoggedSemanticScholarSearch = create_logged_tool(SemanticScholarQueryRun)


def get_literature_search_tool(max_search_results: int, max_content_length: int = 4000):
    if SELECTED_LITERATURE_ENGINE == LiteratureSearchEngine.PUBMED.value:
        return LoggedPubmedSearch(
            name="literature_search",
            api_wrapper=PubMedAPIWrapper(
                top_k_results=max_search_results,
                doc_content_chars_max=max_content_length,
                api_key=os.getenv("PUBMED_SEARCH_API_KEY", ""),
            ))
    elif SELECTED_LITERATURE_ENGINE == LiteratureSearchEngine.SEMANTIC_SCHOLAR.value:
        return LoggedSemanticScholarSearch(
            name="literature_search",
            api_wrapper=SemanticScholarAPIWrapper(
                top_k_results=max_search_results,
                doc_content_chars_max=max_content_length,
                api_key=os.getenv("SEMANTIC_SCHOLAR_API_KEY", ""),
            ),
        )
    else:
        raise ValueError(f"Unsupported search engine: {SELECTED_LITERATURE_ENGINE}")


LoggedPatsnapSearch = create_logged_tool(PatsnapQueryRun)
LoggedPatentsViewSearch = create_logged_tool(PatentsViewQueryRun)


def get_patent_search_tool(max_search_results: int, max_content_length: int = 0):
    if SELECTED_PATENT_ENGINE == PatentSearchEngine.PATSNAP.value:
        return LoggedPatsnapSearch(
            name="patent_search",
            api_wrapper=PatsnapAPIWrapper(
                patsnap_client=PatsnapAPIClient(),
                top_k_results=max_search_results,
                get_claims=True,
                doc_content_chars_max=max_content_length,
                claims_content_chars_max=4000,
            ),
        )
    elif SELECTED_PATENT_ENGINE == PatentSearchEngine.PATENTS_VIEW.value:
        return LoggedPatentsViewSearch(
            name="patent_search",
            api_wrapper=PatentsViewAPIWrapper(
                client=PatentsViewAPIClient(api_key=os.getenv("PATENTSVIEW_API_KEY")),
                top_k_results=max_search_results,
                doc_content_chars_max=0,
                get_claims=True,
                claims_content_chars_max=2000,
            ),
        )
    else:
        raise ValueError(f"Unsupported search engine: {SELECTED_PATENT_ENGINE}")


if __name__ == "__main__":
    # results = LoggedDuckDuckGoSearch(
    #     name="web_search", max_results=3, output_format="list"
    # ).invoke("cute panda")
    # print(json.dumps(results, indent=2, ensure_ascii=False))

    result = get_literature_search_tool(3).invoke("monoclonal antibody production ProteinA")
    print(result)