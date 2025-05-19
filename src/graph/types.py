# Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT

from typing import List, Dict, Any, TypedDict

from langgraph.graph import MessagesState

from src.prompts.planner_model import Plan


class SearchResult(TypedDict):
    id: str  # Unique identifier for the search result
    title: str  # Title of the search result
    url: str  # URL of the search result
    content: str  # Content of the search result
    relevance_score: float  # Relevance score of the search result
    raw: Dict[str, Any]  # Raw data from the search result
    metadata: Dict[str, Any]  # Metadata associated with the search result


class Observation(TypedDict):
    step_id: str  # Unique identifier for the observation
    title: str  # Title of the observation
    content: str  # Content of the observation
    source: str  # Source of the observation (e.g., researcher， patent researcher)
    relevance_score: float  # Relevance score of the observation


class State(MessagesState):
    """State for the agent system, extends MessagesState with next field."""

    # Runtime Variables
    locale: str = "en-US"
    observations: list[Observation] = []
    plan_iterations: int = 0
    current_plan: Plan | str = None
    final_report: str = ""
    auto_accepted_plan: bool = False
    enable_background_investigation: bool = True
    background_investigation_results: str = None
