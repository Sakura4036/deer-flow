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
        "Useful for searching patents and retrieving patent information including title, date, applicant, abstract, claims and other basic details from Patsnap Patent Database. "
        "Input should be a search query to find relevant patents."
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
