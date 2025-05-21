from typing import Optional, Type

from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import BaseTool
from pydantic import Field, BaseModel

from .patsnap_api_wrapper import PatsnapAPIWrapper


class PatsnapInput(BaseModel):
    """Input for the Patsnap tool."""

    query: str = Field(description="search query to look up")   


class PatsnapQueryRun(BaseTool):  # type: ignore[override]
    """Tool that searches the PubMed API."""

    name: str = "patsnap"
    description: str = (
        "A wrapper around Patsnap. "
        "Useful for when you need to answer questions about patent topics "
        "Input should be a search query."
    )
    args_schema: Type[BaseModel] = PatsnapInput
    api_wrapper: PatsnapAPIWrapper = Field(default_factory=PatsnapAPIWrapper)  # type: ignore[arg-type]

    def _run(
        self,
        query: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Use the PubMed tool."""
        return self.api_wrapper.run(query)
