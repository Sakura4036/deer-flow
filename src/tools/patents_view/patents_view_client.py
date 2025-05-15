import os
import requests
import json
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class PatentsViewAPIClient:
    """
    Client for interacting with the PatentsView API.
    Handles request authentication and basic API call structure.
    # swagger url: https://search.patentsview.org/swagger-ui/
    # api doc url: https://search.patentsview.org/docs/docs/Search%20API/SearchAPIReference 
    """
    DEFAULT_BASE_URL = "https://search.patentsview.org/api/v1/"

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """
        Initialize the PatentsViewAPIClient.

        Args:
            api_key: The API key for PatentsView. If None, tries to read from PATENTSVIEW_API_KEY env var.
            base_url: The base URL for the PatentsView API. Defaults to official API.
        """
        self.api_key = api_key or os.getenv("PATENTSVIEW_API_KEY")
        if not self.api_key:
            logger.warning("PatentsView API key not provided. API calls may fail.")
        self.base_url = base_url or self.DEFAULT_BASE_URL
        self.headers = {
            "Content-Type": "application/json",
            "X-Api-Key": self.api_key or ""
        }

    def _request(self, method: str, endpoint: str, params: Optional[Dict[str, Any]] = None, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make a request to the PatentsView API.

        Args:
            method: HTTP method (GET or POST).
            endpoint: API endpoint path (e.g., 'patent/').
            params: URL parameters for GET requests.
            data: JSON body for POST requests.

        Returns:
            The JSON response from the API as a dictionary.

        Raises:
            requests.exceptions.RequestException: If the request fails.
        """
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        logger.debug(f"Making {method} request to {url} with data: {data}")
        
        try:
            if method.upper() == "POST":
                response = requests.post(url, headers=self.headers, json=data, params=params)
            elif method.upper() == "GET":
                response = requests.get(url, headers=self.headers, params=params)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()  # Raises an HTTPError for bad responses (4XX or 5XX)
            return response.json()
        except requests.exceptions.HTTPError as http_err:
            logger.error(f"HTTP error occurred: {http_err} - Response: {response.text}")
            # Try to parse error details from PatentsView if available
            try:
                err_details = response.json()
                logger.error(f"PatentsView API error details: {err_details}")
            except json.JSONDecodeError:
                pass # No JSON in error response
            raise
        except requests.exceptions.RequestException as req_err:
            logger.error(f"Request exception occurred: {req_err}")
            raise
        except json.JSONDecodeError as json_err:
            logger.error(f"Failed to decode JSON response: {json_err} - Response text: {response.text}")
            raise


    def _search_patents(self, query_obj: Dict[str, Any], fields: list[str]=None, options: Optional[Dict[str, Any]] = None, sortings: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Search for patents.
        Endpoint: /patent/

        Args:
            query_obj: The 'q' parameter (JSON object) for filtering data.
            fields: The 'f' parameter (list of strings) to specify fields to return.
            options: The 'o' parameter (JSON object) for pagination and other options.
            sortings: The 's' parameter (list of dictionaries) to specify sorting order.

        Returns:
            The API response dictionary.
            example:
            {
                "error": false,
                "count": 100,
                "total_hits": 10000,
                "patents": [
                    {
                        "patent_id": "1234567890",
                        "patent_title": "Example Patent",
                        "patent_date": "2021-01-01",
                        "patent_abstract": "This is an example patent abstract.",
                        "patent_type": "Utility"
                        "inventors": [
                            {
                                "inventor_name_first": "John",
                                "inventor_name_last": "Doe",
                                "inventor_city": "New York",
                                "inventor_country": "US"
                            }
                        ],
                        "assignees": [
                            {
                                "assignee_organization": "Example Company",
                                "assignee_city": "New York",
                                "assignee_country": "US"
                            }
                        ],
                    }
                ]
            }
        """
        payload = {
            "q": query_obj,
            "f": fields or ["patent_id", "patent_title", "patent_date", "inventors.inventor", "patent_abstract", "patent_type"]
        }
        if options:
            payload["o"] = options
        else:
            payload["o"] = {"size": 10}

        if sortings :
            payload['s'] = sortings 
        else:
            payload['s'] = [{"patent_date":"desc"}]
        return self._request("POST", "patent/", data=payload)

    def get_patent_claims(self, patent_id: str, fields: Optional[list[str]] = None, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get claims for a specific patent.
        Endpoint: /g_claim/

        Args:
            patent_id: The ID of the patent.
            fields: List of fields to return for claims (e.g., ["claim_text", "claim_sequence"]). Defaults to ["claim_text"].
            options: Additional options for the request.

        Returns:
            The API response dictionary containing claims.
            example:
            {
                "error": false,
                "count": 100,
                "total_hits": 10000,
                "g_claims": [
                    {   
                        "claim_number": "0001",
                        "claim_text": "This is an example claim text.",
                        "claim_sequence": 0
                    },
                    {
                        "claim_number": "0002",
                        "claim_text": "This is another example claim text.",
                        "claim_sequence": 1
                    }
                ]
            }
            
        """
        query_obj = {"_eq": {"patent_id": patent_id}}
        fields_to_fetch = fields or ["claim_text", "claim_sequence"]
        
        payload = {
            "q": query_obj,
            "f": fields_to_fetch
        }
        if options:
            payload["o"] = options
            
        return self._request("POST", "g_claim/", data=payload)

    def search_patents(self, query:str, max_results:int=10, fuzzy_search:bool=False, get_claims:bool=False) -> List[Dict[str, Any]]:
        """
        Search for patents.
        Args:
            query: The query string to search for.
            max_results: The maximum number of results to return.
            fuzzy_search: Whether to use fuzzy search.
            get_claims: Whether to get claims for the patents.
        Returns:
            A list of patents.  
        """
        if fuzzy_search:
            search_eq = "_text_any"
        else:
            search_eq = "_text_phrase"
        query_obj = {
            "_or": [
                {search_eq: {"patent_title": query}},
                {search_eq: {"patent_abstract": query}}
            ]
        }
        fields = ["patent_id", "patent_title", "patent_date", "inventors", "patent_abstract", "patent_type", "assignees"]
        options = {"size": max_results}
        result = self._search_patents(query_obj, fields=fields, options=options)

        patents = result["patents"]

        if get_claims:
            for patent in patents:
                claims = self.get_patent_claims(patent["patent_id"])
                patent["g_claims"] = claims["g_claims"]

        # Format the results    
        patents = self._format_results(patents)
        return patents
    
    def _format_results(self, patents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Format the results to be more readable.
        """
        for patent in patents:
            if inventors:=patent.get("inventors", None):
                patent["inventors"] = [inventor.get("inventor_name_first", "") + " " + inventor.get("inventor_name_last", "") for inventor in inventors]
            if assignees:=patent.get("assignees", None):
                patent["assignees"] = [
                    "{} {},{}".format(assignee.get("assignee_organization", ""), assignee.get("assignee_city", ""), assignee.get("assignee_country", ""))
                    for assignee in assignees if assignee.get("assignee_organization")
                ]
            if g_claims:=patent.get("g_claims", None):
                g_claims = sorted(g_claims, key=lambda x: x.get("claim_sequence", 0))
                patent["g_claims"] = "\n".join([claim.get("claim_text", "") for claim in g_claims])

        return patents

if __name__ == '__main__':
    # This is for basic testing of the client
    # Ensure PATENTSVIEW_API_KEY is set in your environment
    logging.basicConfig(level=logging.DEBUG)
    client = PatentsViewAPIClient()
    
    if not client.api_key:
        print("PATENTSVIEW_API_KEY environment variable not set. Skipping live API test.")
    else:
        print("Testing patent search...")
        try:
            results = client.search_patents("machine learning", max_results=2, fuzzy_search=True)
            print(f"Search results: {json.dumps(results, indent=2)}")

            if results and results.get("patents"):
                test_patent_id = results["patents"][0]["patent_id"]
                print(f"\\nTesting get claims for patent_id: {test_patent_id}...")
                claims_results = client.get_patent_claims(test_patent_id)
                print(f"Claims results: {json.dumps(claims_results, indent=2)}")

        except Exception as e:
            print(f"An error occurred during testing: {e}") 