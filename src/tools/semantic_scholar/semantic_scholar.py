import asyncio
from typing import Optional, Type

from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import BaseTool
from pydantic import Field, BaseModel

from src.tools.semantic_scholar.semantic_scholar_api_wrapper import SemanticScholarAPIWrapper


class SemanticScholarInput(BaseModel):
    """Input for the Semantic Scholar tool."""

    query: str = Field(description="Analytics search query to look up")


class SemanticScholarQueryRun(BaseTool):
    """Tool that searches the Semantic Scholar API."""

    name: str = "semantic_scholar"
    description: str = (
        "A wrapper around Semantic Scholar. "
        "Useful for when you need to answer questions about academic papers, "
        "research, and scholarly literature. "
        "Input should be a Analytics search query."
    )
    args_schema: Type[BaseModel] = SemanticScholarInput
    api_wrapper: SemanticScholarAPIWrapper = Field(default_factory=SemanticScholarAPIWrapper)

    def _run(
        self,
        query: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Use the Semantic Scholar tool synchronously."""
        # Call the synchronous run method of the API wrapper
        return self.api_wrapper.run(query)
