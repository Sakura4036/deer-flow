from typing import Type
from langchain_community.tools import PubmedQueryRun
from pydantic import Field, BaseModel
from typing import Optional
import time
from langchain_core.callbacks import CallbackManagerForToolRun


class PubmedInput(BaseModel):
    """Input for the Pubmed tool."""

    query: str = Field(description="search query to look up")


class MyPubmedQueryRun(PubmedQueryRun):
    args_schema: Type[BaseModel] = PubmedInput

    def _run(
        self,
        query: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Use the PubMed tool."""
        # Try up to 3 times if we get a 429 (Too Many Requests) error
        for attempt in range(3):
            res = self.api_wrapper.run(query)
            if "PubMed exception" in str(res) and "429" in str(res) and attempt < 2:  # Only retry if it's a 429 error and not the last attempt
                time.sleep(2 * (attempt + 1))  # Exponential backoff
                continue
            return res
