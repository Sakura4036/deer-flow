import json
import logging
import time
import urllib.error
import urllib.parse
import urllib.request
import os

from typing import Any, Dict, Iterator, List

from langchain_core.documents import Document
from pydantic import BaseModel, model_validator, Field

logger = logging.getLogger(__name__)

SEMANTIC_SCHOLAR_API_URL = "https://api.semanticscholar.org/graph/v1"


class SemanticScholarAPIWrapper(BaseModel):
    """
    Wrapper around Semantic Scholar API.

    This wrapper will use the Semantic Scholar API to conduct searches and fetch
    document summaries. By default, it will return the document summaries
    of the top-k results of an input search.

    Parameters:
        top_k_results: number of the top-scored document used for the tool.
          Default is 5 results.
        doc_content_chars_max: maximum length of the document content.
          Content will be truncated if it exceeds this length.
          Default is 2000 characters.
        api_key: API key to be used for the Semantic Scholar API. Reads from
          SEMANTIC_SCHOLAR_API_KEY environment variable by default.
        max_retry: maximum number of retries for a request. Default is 3.
        sleep_time: time to wait between retries. Default is 1 second.
    """

    top_k_results: int = 5
    doc_content_chars_max: int = 2000
    api_key: str = ""
    max_retry: int = 3
    sleep_time: float = 1.0

    def run(self, query: str) -> str:
        """
        Run Semantic Scholar search synchronously and get formatted results.
        """
        try:
            # Retrieve the top-k results for the query using the synchronous load method
            docs = [
                f"Title: {result.get('title', 'No Title')}\n"
                f"URL: {result.get('url', 'No URL')}\n"
                f"Content:\n{result.get('content', 'No content available')}"
                for result in self.load(query)
            ]

            # Join the results and limit the character count
            return (
                "\n\n---\n\n".join(docs)[: self.doc_content_chars_max]
                if docs
                else "No academic papers found matching your search criteria."
            )
        except Exception as ex:
            return f"Semantic Scholar exception: {ex}"

    def lazy_load(self, query: str) -> Iterator[dict]:
        """
        Search Semantic Scholar for documents matching the query.
        Return an iterator of dictionaries containing the document metadata.
        """
        fields = [
            "paperId", "title", "abstract", "year", "referenceCount", "citationCount",
            "url", "authors", "venue", "publicationTypes", "publicationDate"
        ]
        fields_param = ",".join(fields)

        # Construct the URL and parameters for the synchronous request
        url = f"{SEMANTIC_SCHOLAR_API_URL}/paper/search?query={urllib.parse.quote_plus(query)}&limit={self.top_k_results}&fields={fields_param}"

        headers = {"x-api-key": self.api_key}

        retry = 0
        while retry < self.max_retry:
            try:
                # Make the synchronous HTTP request
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req) as response:
                    text = response.read().decode("utf-8")
                    result = json.loads(text)

                # Process and yield results, similar to the process_single_query logic
                results_list = []
                for paper in result.get("data", []):
                    author_names = []
                    if "authors" in paper:
                        author_names = [author.get("name", "") for author in paper.get("authors", [])]

                    content_parts = []
                    if paper.get("abstract"):
                        content_parts.append(f"Abstract: {paper['abstract']}")
                    if author_names:
                        content_parts.append(f"Authors: {', '.join(author_names)}")
                    if paper.get("year"):
                        content_parts.append(f"Year: {paper['year']}")
                    if paper.get("venue"):
                        content_parts.append(f"Venue: {paper['venue']}")
                    if paper.get("citationCount") is not None:
                        content_parts.append(f"Citations: {paper['citationCount']}")
                    if paper.get("referenceCount") is not None:
                        content_parts.append(f"References: {paper['referenceCount']}")

                    content = "\n".join(content_parts)

                    # Optional: Keep score calculation if needed downstream
                    citation_count = paper.get("citationCount", 0) or 0
                    score = min(1.0, citation_count / 1000.0) if citation_count > 0 else 0.5

                    results_list.append({
                        "title": paper.get("title", ""),
                        "url": paper.get("url", ""),
                        "content": content,
                        "score": score,
                        "raw_content": json.dumps(paper)
                    })

                # Yield each result
                for res in results_list:
                    yield res

                return # Exit the retry loop on success

            except urllib.error.HTTPError as e:
                logger.error(f"Semantic Scholar API HTTP error: {e.code} - {e.reason}")
                if e.code == 429 and retry < self.max_retry - 1:
                    # Too Many Requests errors, wait and retry
                    logger.info(f"Too Many Requests, waiting for {self.sleep_time:.2f} seconds before retrying...")
                    time.sleep(self.sleep_time)
                    self.sleep_time *= 2  # Exponential backoff
                    retry += 1
                else:
                    # Re-raise other HTTP errors or if max retries reached
                    raise e
            except Exception as e:
                logger.error(f"Error processing Semantic Scholar query '{query}': {str(e)}")
                # Re-raise other exceptions
                raise e

        # If loop finishes without returning, it means max retries were reached
        raise Exception(f"Failed to retrieve Semantic Scholar results after {self.max_retry} retries.")

    def load(self, query: str) -> List[dict]:
        """
        Search Semantic Scholar for documents matching the query.
        Return a list of dictionaries containing the document metadata.
        """
        return list(self.lazy_load(query))

