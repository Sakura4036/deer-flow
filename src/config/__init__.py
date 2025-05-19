# Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT

from .tools import (
    SEARCH_MAX_RESULTS, SELECTED_SEARCH_ENGINE, SearchEngine, SEARCH_CONTENT_MAX_LENGTH,
    SELECTED_LITERATURE_SEARCH_ENGINE, LiteratureSearchEngine, 
    SELECTED_PATENT_SEARCH_ENGINE, PatentSearchEngine
)
from .loader import load_yaml_config
from .questions import BUILT_IN_QUESTIONS, BUILT_IN_QUESTIONS_ZH_CN

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Team configuration
TEAM_MEMBER_CONFIGURATIONS = {
    "researcher": {
        "name": "researcher",
        "desc": (
            "Responsible for searching and collecting relevant information, understanding user needs and conducting research analysis"
        ),
        "desc_for_llm": (
            "Uses search engines and web crawlers to gather information from the internet. "
            "Outputs a Markdown report summarizing findings. Researcher can not do math or programming."
        ),
        "is_optional": False,
    },
    "literature_researcher": {
        "name": "literature_researcher",
        "desc": (
            "专门负责学术文献检索、分析与归纳，提供高质量学术证据和理论基础"
        ),
        "desc_for_llm": (
            "Uses academic literature search tools and databases to gather, analyze, and summarize papers, reviews, and citations. Outputs a Markdown report focused on academic findings."
        ),
        "is_optional": True,
    },
    "patent_researcher": {
        "name": "patent_researcher",
        "desc": (
            "专门负责专利数据库检索、分析与归纳，提供创新点、专利布局等相关内容"
        ),
        "desc_for_llm": (
            "Uses patent search tools and databases to gather, analyze, and summarize patent applications, grants, and legal status. Outputs a Markdown report focused on patent findings."
        ),
        "is_optional": True,
    },
    "coder": {
        "name": "coder",
        "desc": (
            "Responsible for code implementation, debugging and optimization, handling technical programming tasks"
        ),
        "desc_for_llm": (
            "Executes Python or Bash commands, performs mathematical calculations, and outputs a Markdown report. "
            "Must be used for all mathematical computations."
        ),
        "is_optional": True,
    },
}

TEAM_MEMBERS = list(TEAM_MEMBER_CONFIGURATIONS.keys())

__all__ = [
    # Other configurations
    "TEAM_MEMBERS",
    "TEAM_MEMBER_CONFIGURATIONS",
    "SEARCH_MAX_RESULTS",
    "SEARCH_CONTENT_MAX_LENGTH",
    "SELECTED_SEARCH_ENGINE",
    "SearchEngine",
    "BUILT_IN_QUESTIONS",
    "BUILT_IN_QUESTIONS_ZH_CN",
    "SELECTED_PATENT_SEARCH_ENGINE",
    "PatentSearchEngine",
    "SELECTED_LITERATURE_SEARCH_ENGINE",
    "LiteratureSearchEngine"
]
