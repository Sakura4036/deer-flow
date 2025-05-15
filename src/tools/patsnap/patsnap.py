from typing import Optional

from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import BaseTool
from pydantic import Field

from .patsnap_api_wrapper import PatsnapAPIWrapper


class PatsnapQueryRun(BaseTool):  # type: ignore[override]
    """Tool that searches the PubMed API."""

    name: str = "patsnap"
    description: str = (
        "A wrapper around Patsnap. "
        "Useful for when you need to answer questions about patent topics "
        "Input should be a search query."
    )
    api_wrapper: PatsnapAPIWrapper = Field(default_factory=PatsnapAPIWrapper)  # type: ignore[arg-type]

    def _run(
        self,
        query: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Use the PubMed tool."""
        return self.api_wrapper.run(query)
