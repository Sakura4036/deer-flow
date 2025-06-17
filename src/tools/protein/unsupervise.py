
import logging
import traceback
from typing import Annotated, List
import requests
import os
from typing import TypedDict
from langchain_core.tools import tool
from src.tools.decorators import log_io


logger = logging.getLogger(__name__)


_api_url = os.getenv("PROTEIN_API_URL", "http://192.168.1.5:8005")


class APIResponse(TypedDict):
    code: int
    data: dict | str | list
    error_code: int
    message: str
    requests: str


@tool
@log_io
def submit_unsupervise_task(
    protein_sequences: Annotated[List[str], "The protein sequence to analyze."],
) -> str:
    """Use this to generate unsupervise mutation of a protein, return the task"""
    
    try:
        url = f"{_api_url}/api/task/unsupervise/submit"
        response = requests.post(url, json={"seqs": protein_sequences})
        response.raise_for_status()
        response_json = response.json()
        if response_json["code"] == 200:
            return response_json["data"]
        else:
            return response_json["message"]
    except Exception as e:
        logger.error(f"Error generating unsupervise mutation: {e}")
        traceback.print_exc()
        return f"Error: {e}"

@tool
@log_io
def get_unsupervise_task_status(
    task_id: Annotated[str, "The task id to get the result."],
) -> str:
    """Use this to get the status of unsupervise mutation task."""
    try:
        url = f"{_api_url}/api/task/unsupervise/progress/{task_id}"
        response = requests.get(url)
        response.raise_for_status()
        response_json = response.json()
        if response_json["code"] == 200:
            status = response_json["data"]
            status_mapping = {
                1: "pending",
                2: "running",
                3: "completed",
                4: "failed",
            }
            return status_mapping[status]
        else:
            return response_json["message"]
    except Exception as e:
        logger.error(f"Error getting unsupervise mutation result: {e}")
        return f"Error: {e}"


class Mutation(TypedDict):
    mutant:str  # The mutant site, e.g. "A100B"


class UnsuperviseMutationResult(TypedDict):
    # fasta: str  # The fasta sequence of the protein
    id: str  # The id of the protein
    pdb: str  # The pdb file content of the protein
    select: List[Mutation]  # The top mutation sites and corresponding scores


class UnsuperviseTaskResult(APIResponse):
    data: List[UnsuperviseMutationResult]


@tool
@log_io
def get_unsupervise_result(
    task_id: Annotated[str, "The task id to get the result."],
) -> str | List[UnsuperviseMutationResult]:
    """Use this to get the result of mutation: The top mutation sites."""
    try:
        url = f"{_api_url}/api/task/unsupervise/result/{task_id}"
        response = requests.get(url)
        response.raise_for_status()
        response_json = response.json()
        if response_json["code"] == 200:
            results = []
            for r in response_json["data"]:
                r.pop("fasta")
                results.append(r)
            return results
        else:
            return response_json["message"]
    except Exception as e:
        logger.error(f"Error getting unsupervise mutation result: {e}")
        return f"Error: {e}"
