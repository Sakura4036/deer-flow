import json
import logging
from typing import List, Dict, Any, Optional
import os
from pydantic import BaseModel, Field, ConfigDict
from src.tools.patents_view.patents_view_client import PatentsViewAPIClient
from src.config import SEARCH_MAX_RESULTS, SEARCH_CONTENT_MAX_LENGTH

logger = logging.getLogger(__name__)

class PatentsViewAPIWrapper(BaseModel):
    """
    Wrapper for the PatentsView API.
    Provides a method to search for patents and retrieve specified details,
    including claims, assignees, and inventors.

    Args:
            client: An instance of PatentsViewAPIClient. If None, a new one will be created.
            top_k_results: Maximum number of patent results to return.
            doc_content_chars_max: Max characters for lengthy text fields (currently not strictly enforced in truncation).
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)

    client: PatentsViewAPIClient = Field(default_factory=PatentsViewAPIClient)
    top_k_results: int = SEARCH_MAX_RESULTS
    doc_content_chars_max: int = SEARCH_CONTENT_MAX_LENGTH
    get_claims: bool = False
    claims_content_chars_max: int = 1000

    def _parse_patent_data(self, patent_data: Dict[str, Any]) -> str:
        """
        Parse individual patent data from the client and return a formatted string.
        Assumes patent_data is already processed by client._format_results and
        reflects the structure from the user's uncommitted changes (e.g., uses 'patent_date', 'g_claims').
        """
        patent_id = patent_data.get("patent_id", "N/A")
        title = patent_data.get("patent_title", "N/A")
        abstract = patent_data.get("patent_abstract", "N/A")
        # Use 'patent_date' as per user's uncommitted changes
        patent_date = patent_data.get("patent_date", "N/A")

        assignees = patent_data.get("assignees", []) # Expected to be a list of strings
        assignees_str = ", ".join(assignees) if assignees else "N/A"

        inventors = patent_data.get("inventors", []) # Expected to be a list of strings
        inventors_str = ", ".join(inventors) if inventors else "N/A"
        
        # Use 'g_claims' as a string, as per user's uncommitted changes for the dictionary output
        # Defaulting to "N/A" if empty or not present for clearer output
        claims_content = patent_data.get("g_claims", "") 
        claims_display_str = claims_content if claims_content else "N/A"
        claims_display_str = claims_display_str[:self.claims_content_chars_max] if len(claims_display_str) > self.claims_content_chars_max else claims_display_str

        # Construct the formatted string
        # Each piece of information is on a new line.
        lines = [
            f"Patent ID: {patent_id}",
            f"Title: {title}",
            f"Abstract: {abstract}",
            f"Publication Date: {patent_date}",
            f"Assignees: {assignees_str}",
            f"Inventors: {inventors_str}",
            "Claims:", claims_display_str # This is the direct string content from g_claims or "N/A"
        ]
        return "\n".join(lines)

    def run(self, query: str) -> str:
        """
        Search for patents using a query string and return a JSON string
        representing a list of formatted patent information strings.

        Args:
            query: The search query string.

        Returns:
            A JSON string representing a list of formatted patent strings.
            Each string in the list contains details for one patent:
            patent_id, title, abstract, publication date, assignees, inventors, and claims.
        """
        try:
            logger.debug(f"Searching patents with query: '{query}' using client.search_patents, top_k_results={self.top_k_results}")
            
            # Call the modified search_patents method from the client
            # This method now handles query construction, field selection, claims fetching, and initial formatting.
            # We pass fuzzy_search=True as the original wrapper implied it with _text_any.
            # We pass get_claims=True as the wrapper was originally fetching claims.
            patents_data = self.client.search_patents(
                query=query,
                max_results=self.top_k_results,
                fuzzy_search=True, 
                get_claims=self.get_claims
            )
            
            # The client's search_patents method returns a list of already somewhat formatted patents.
            # It does not return total_hits directly, so logging is adjusted.
            logger.info(f"Received {len(patents_data)} patent results from client.search_patents.")

            results = []
            if patents_data:
                for patent_data_from_client in patents_data:
                    # _parse_patent_data now returns a formatted string for each patent
                    formatted_patent_string = self._parse_patent_data(patent_data_from_client)
                    results.append(formatted_patent_string)
            
            return (
                "\n\n".join(results)[:self.doc_content_chars_max]
                if results
                else "No good Patent Result was found"
            )

        except Exception as e:
            logger.error(f"Error during PatentsView search for query '{query}': {e}")
            return json.dumps([{"error": str(e)}])
