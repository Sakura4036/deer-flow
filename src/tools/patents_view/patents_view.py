import logging
from typing import Optional
from pydantic import Field
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import BaseTool

from src.tools.patents_view.patents_view_api_wrapper import PatentsViewAPIWrapper

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
        "Output is a string containing a list of patent information including: "
        "patent_id, title, abstract, claims, assignee, inventors, and patent_date."
    )
    api_wrapper: PatentsViewAPIWrapper = Field(default_factory=PatentsViewAPIWrapper)

    def _run(
        self, 
        query: str, 
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """Use the tool to search for patents."""
        return self.api_wrapper.run(query)
