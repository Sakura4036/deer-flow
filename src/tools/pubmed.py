from typing import Type
from langchain_community.tools import PubmedQueryRun
from pydantic import Field, BaseModel
from typing import Optional
import time
from langchain_core.callbacks import CallbackManagerForToolRun


class PubmedInput(BaseModel):
    """Input for the Pubmed tool."""

    query: str = Field(description="search query to look up in PubMed. Query language must be english.")


class MyPubmedQueryRun(PubmedQueryRun):
    args_schema: Type[BaseModel] = PubmedInput
    description: str = ("""For searching academic literature from databases. Guidelines:
Language: All search queries MUST be in **English**.
Format: Queries MUST be structured like a typical academic database search query (e.g., suitable for PubMed, Scopus, Web of Science). **DO NOT use natural language questions or conversational phrases.**
Key elements:
    Employ precise **keywords** and **key phrases**.
    Use **Boolean operators** (e.g., `AND`, `OR`, `NOT`). Explicit use is preferred.
    Utilize **parentheses** `()` for grouping.
    Use **quotation marks** `""` for exact phrases (e.g., `"climate change"`).
Time/Year Restrictions in Queries:
    General Rule: By default, **DO NOT** include year or time range restrictions (e.g., `year:2023-2025`, `year>2025`, `after:2020`) in the search query string itself, 
    If the user's request implies a time constraint (e.g., "latest research," "recent findings") but doesn't provide specific years, prioritize recent publications when selecting from search results, but do not arbitrarily add date filters to the query.
Good Query Example: `(("machine learning" OR "deep learning") AND ("medical imaging" OR "radiology") AND (diagnosis OR prediction))`
Bad Query Example (AVOID): `What are the latest applications of machine learning in medical imaging for diagnosis after 2020?`
""")

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
