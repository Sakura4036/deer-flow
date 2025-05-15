import logging
from typing import Any, Dict, Optional

from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import BaseTool

from src.tools.patents_view.patents_view_api_wrapper import PatentsViewAPIWrapper
from src.config import SEARCH_MAX_RESULTS, SEARCH_CONTENT_MAX_LENGTH # For default values

logger = logging.getLogger(__name__)

class PatentsViewQueryRun(BaseTool):
    """
    Tool for performing patent searches using the PatentsView API.
    It queries for patent_id, title, abstract, claims, assignee, inventors, and year.
    """

    name: str = "patents_view_search"
    description: str = (
        "A patent search tool that queries the PatentsView database. "
        "Input should be a search query string. "
        "Output is a JSON string containing a list of patent information including: "
        "patent_id, title, abstract, claims, assignee, inventors, and patent_date."
    )
    api_wrapper: PatentsViewAPIWrapper

    def __init__(self, api_wrapper: Optional[PatentsViewAPIWrapper] = None, **kwargs: Any):
        """
        Initialize the tool with an API wrapper.
        """
        super().__init__(**kwargs)
        self.api_wrapper = api_wrapper or PatentsViewAPIWrapper(
            # The client inside wrapper will use PATENTSVIEW_API_KEY env var by default
            top_k_results=kwargs.get("top_k_results", SEARCH_MAX_RESULTS),
            doc_content_chars_max=kwargs.get("doc_content_chars_max", SEARCH_CONTENT_MAX_LENGTH)
        )

    def _run(
        self, 
        query: str, 
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """Use the tool to search for patents."""
        return self.api_wrapper.run(query)
