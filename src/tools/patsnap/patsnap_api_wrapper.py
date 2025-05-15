import logging
from typing import Any, Dict, Iterator, List

from pydantic import BaseModel, Field, ConfigDict

from .patsnap_client import PatsnapAPIClient

logger = logging.getLogger(__name__)


class PatsnapAPIWrapper(BaseModel):
    """
    Wrapper around the PatSnap API.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)

    patsnap_client: PatsnapAPIClient = Field(default_factory=PatsnapAPIClient)
    top_k_results: int = 3
    lang: str = "en"
    search_kwargs: dict = Field(default_factory=dict)
    get_title_abstract: bool = True
    get_claims: bool = False
    get_legal_status: bool = False

    sleep_time: float = 0.2

    doc_content_chars_max: int = 4000

    def run(self, query: str) -> str:
        try:
            docs = [
                self._format_patent(patent) for patent in self.load(query)
            ]

            return (
                "\n\n".join(docs)[:self.doc_content_chars_max]
                if docs
                else "No good Patent Result was found"
            )
        except Exception as e:
            return f"Patsnap exception: {e}."

    def load(self, query: str) -> List[Dict[str, Any]]:
        return list(self.lazy_load(query))

    def lazy_load(self, query: str) -> Iterator[Dict[str, Any]]:
        """
        Fetch results from the PatSnap API using the provided query.
        """
        try:
            patent_search_list = self.patsnap_client.patent_search(query, limit=self.top_k_results, **self.search_kwargs)
        except Exception as e:
            logger.error(f"Error fetching results: {e}")
            import traceback
            logger.error(traceback.print_exc())
            return

        if not patent_search_list:
            logger.warning("No results found.")
            return

        for patent in patent_search_list:
            # get patent details
            patent_details = self.patsnap_client.get_patent_content(patent_id=patent['patent_id'],
                                                                    title_abstract=self.get_title_abstract,
                                                                    claims=self.get_claims,
                                                                    legal_status=self.get_legal_status,
                                                                    lang=self.lang)
            patent.update(patent_details)

            yield patent

    def _format_patent(self, patent: Dict[str, Any]) -> str:
        """
        Format the patent data into a string.
        """
        patent_str = f"Patent ID: {patent.get('patent_id')}\n"
        patent_str += f"Patent Number: {patent.get('pn')}\n"
        patent_str += f"Title: {patent['title']}\n"
        patent_str += f"Inventor: {patent['inventor']}\n"
        patent_str += f"Current Assignee: {patent.get('current_assignee', 'N/A')}\n"
        patent_str += f"Abstract: {patent.get('abstract', 'N/A')}\n"

        for key, value in patent.items():
            if key not in ['patent_id', 'pn', 'title', 'inventor', 'current_assignee', 'Abstract']:
                patent_str += f"{key.replace('_', ' ').upper()}: {value}\n"

        return patent_str
