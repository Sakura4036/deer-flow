from typing import Type
from langchain_community.tools import PubmedQueryRun
from pydantic import Field, BaseModel


class PubmedInput(BaseModel):
    """Input for the Pubmed tool."""

    query: str = Field(description="search query to look up")


class MyPubmedQueryRun(PubmedQueryRun):
    args_schema: Type[BaseModel] = PubmedInput
