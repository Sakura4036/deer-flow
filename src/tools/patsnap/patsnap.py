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
        "Guidelines: "
        """Mandatory Format: Primarily use `TACD:(keywords)`. `TACD` targets Title, Abstract, Claims, and Description.
        Keyword Derivation: `keywords` within `TACD:(...)` MUST be meticulously derived from the research step's objective. Focus on enzyme names (e.g., lipase, amylase, protease), EC numbers, company names, application areas (e.g., detergent, biofuel, food processing), and specific technical terms (e.g., site-directed mutagenesis, immobilization, expression host *Pichia pastoris*).
        Keyword Purity: DO NOT include generic terms like "patent", "专利", "invention", "文献" within the `keywords` string itself for `patent_search`.
        Boolean/Proximity Operators: Utilize operators like `AND`, `OR`, `NOT` for precision.
            Example for Enzyme Variants: `TACD:(amylase AND variant AND thermostability AND "Bacillus licheniformis")`
            Example for Production Method: `TACD:("enzyme production" AND "Pichia pastoris" AND high yield)`
        Time/Date Restrictions in `patent_search` Query:
            Default: DO NOT add any year or time range restrictions UNLESS explicitly specified by the research plan or user.
            User-Specified Time: If a time range is given, use appropriate date range syntax (e.g., `PBD:[YYYYMMDD TO YYYYMMDD]`, `APD:[YYYYMMDD TO YYYYMMDD]`)."""
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
