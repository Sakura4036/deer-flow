# Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT
from enum import Enum
from typing import Literal

# Define available LLM types
LLMType = Literal["basic", "reasoning", "vision"]

class AgentType(str, Enum):
    COORDINATOR = "coordinator"
    PLANNER = "planner"
    RESEARCHER = "researcher"
    CODER = "coder"
    REPORTER = "reporter"
    PODCAST_SCRIPT_WRITER = "podcast_script_writer"
    PPT_COMPOSER = "ppt_composer"
    PROSE_WRITER = "prose_writer"
    ENZYME_RETRIEVER = "enzyme_retriever"

# Define agent-LLM mapping
AGENT_LLM_MAP: dict[str, LLMType] = {
    "coordinator": "basic",
    "planner": "reasoning",
    "researcher": "reasoning",
    "coder": "basic",
    "reporter": "reasoning",
    "podcast_script_writer": "basic",
    "ppt_composer": "basic",
    "prose_writer": "basic",
    "enzyme_retriever": "reasoning",
}
