import logging
from typing import Optional, Type
from pydantic import Field, BaseModel
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import BaseTool
from src.tools.patents_view.patents_view_api_wrapper import PatentsViewAPIWrapper

logger = logging.getLogger(__name__)


class PatentsViewInput(BaseModel):
    """Input for the PatentsView tool."""

    query: str = Field(description="search query to look up")

class PatentsViewQueryRun(BaseTool):
    """
    Tool for performing patent searches using the PatentsView API.
    It queries for patent_id, title, abstract, claims, assignee, inventors, and year.
    """

    name: str = "patents_view_search"
    description: str = (
        "A patent search tool that queries the PatentsView database. "
        "Input should be a search query string. "
    )
    api_wrapper: PatentsViewAPIWrapper = Field(default_factory=PatentsViewAPIWrapper)
    args_schema: Type[BaseModel] = PatentsViewInput

    def _run(
        self, 
        query: str, 
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """Use the tool to search for patents."""
        return self.api_wrapper.run(query)
