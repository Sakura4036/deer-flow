# Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT

from pathlib import Path
from typing import Any, Dict
import logging
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from langchain.chat_models import init_chat_model
from tenacity import retry, stop_after_attempt
from src.config import load_yaml_config
from src.config.agents import LLMType, AgentType, AGENT_LLM_MAP

logger = logging.getLogger(__name__)

# Cache for LLM instances
_llm_cache: dict[LLMType, ChatOpenAI] = {}


def _create_llm_use_conf(llm_type: LLMType, conf: Dict[str, Any]) -> ChatOpenAI:
    llm_type_map = {
        "reasoning": conf.get("REASONING_MODEL"),
        "basic": conf.get("BASIC_MODEL"),
        "vision": conf.get("VISION_MODEL"),
    }
    llm_conf = llm_type_map.get(llm_type)
    if not llm_conf:
        raise ValueError(f"Unknown LLM type: {llm_type}")
    if not isinstance(llm_conf, dict):
        raise ValueError(f"Invalid LLM Conf: {llm_type}")
    # return ChatOpenAI(**llm_conf)
    return init_chat_model(**llm_conf, model_provider=llm_conf.get("provider", 'openai'))


def get_llm_by_type(
    llm_type: LLMType,
) -> ChatOpenAI:
    """
    Get LLM instance by type. Returns cached instance if available.
    """
    if llm_type in _llm_cache:
        return _llm_cache[llm_type]

    conf = load_yaml_config(
        str((Path(__file__).parent.parent.parent / "conf.yaml").resolve())
    )
    llm = _create_llm_use_conf(llm_type, conf)
    _llm_cache[llm_type] = llm
    return llm


def get_agent_llm_type(agent_type: str | AgentType = None) -> ChatOpenAI:
    return AGENT_LLM_MAP.get(agent_type, "basic")


def get_agent_llm(agent_type: str | AgentType = None) -> ChatOpenAI:
    llm_type = AGENT_LLM_MAP.get(agent_type, "basic")
    logger.info(f"get {llm_type} llm for {agent_type}")
    return get_llm_by_type(llm_type)


@retry(stop=stop_after_attempt(3))
def invoke_llm_with_retry(llm, messages, **kwargs):
    response = llm.invoke(messages, **kwargs)
    return response

@retry(stop=stop_after_attempt(3))
async def ainvoke_llm_with_retry(llm, messages, **kwargs):
    response = await llm.ainvoke(messages, **kwargs)
    return response


# Initialize LLMs for different purposes - now these will be cached
basic_llm = get_llm_by_type("basic")
reasoning_llm = get_llm_by_type("reasoning")

# In the future, we will use reasoning_llm and vl_llm for different purposes
# reasoning_llm = get_llm_by_type("reasoning")
# vl_llm = get_llm_by_type("vision")


if __name__ == "__main__":
    print(reasoning_llm.invoke("Hello"))
