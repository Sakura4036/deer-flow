# Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT

import operator
from typing import Annotated, Optional

from langgraph.graph import MessagesState
from pydantic import BaseModel

from src.prompts.planner_model import Plan


class ProteinSequence(BaseModel):
    protein_name:str
    accession:Optional[str] = None
    organism_name:Optional[str] = None
    sequence:str
    gene_name: Optional[str] = None


class State(MessagesState):
    """State for the agent system, extends MessagesState with next field."""

    # Runtime Variables
    user_query: str = ""
    locale: str = "en-US"
    observations: list[str] = []
    plan_iterations: int = 0
    current_plan: Plan | str = None
    final_report: str = ""
    auto_accepted_plan: bool = False
    enable_background_investigation: bool = True
    background_investigation_results: str = None
    enzyme_retriever_results: str = ""
    design_task_id: Optional[str] = None
    enzyme_mutant_results: list[dict] = []
