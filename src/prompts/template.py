# Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT

import os
import dataclasses
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape
from langgraph.prebuilt.chat_agent_executor import AgentState
from src.config.configuration import Configuration

# Initialize Jinja2 environment
env = Environment(
    loader=FileSystemLoader(os.path.dirname(__file__)),
    autoescape=select_autoescape(),
    trim_blocks=True,
    lstrip_blocks=True,
)


def get_prompt_template(prompt_name: str) -> str:
    """
    Load and return a prompt template using Jinja2.

    Args:
        prompt_name: Name of the prompt template file (without .md extension)

    Returns:
        The template string with proper variable substitution syntax
    """
    try:
        template = env.get_template(f"{prompt_name}.md")
        return template.render()
    except Exception as e:
        raise ValueError(f"Error loading template {prompt_name}: {e}")


def apply_prompt_template(
    prompt_name: str, state: AgentState, configurable: Configuration = None
) -> list:
    """
    Apply template variables to a prompt template and return formatted messages.

    Args:
        prompt_name: Name of the prompt template to use
        state: Current agent state containing variables to substitute

    Returns:
        List of messages with the system prompt as the first message
    """
    # Convert state to dict for template rendering
    state_vars = {
        "CURRENT_TIME": datetime.now().strftime("%a %b %d %Y %H:%M:%S %z"),
        "locale": state.get("locale", "en-US"),
        **state,
    }
    
    # Add configurable variables
    if configurable:
        state_vars.update(dataclasses.asdict(configurable))

    try:
        template = env.get_template(f"{prompt_name}.md")
        system_prompt = template.render(**state_vars)
        return [{"role": "system", "content": system_prompt}] + state["messages"]
    except Exception as e:
        raise ValueError(f"Error applying template {prompt_name}: {e}")


if __name__ == "__main__":
    # Example usage
    example_state = {'CURRENT_TIME': 'Tue May 27 2025 09:20:28 ', 'messages': [], 'locale': 'zh-CN', 'task_description': '# Current Research Task for Research Team\n\n## Title\nProteinA酶相关产品信息全面收集与初步分析\n\n## Task Description\n1. 识别并收集全球范围内主要的ProteinA酶产品信息，包括产品名称、详细功能描述、技术规格、主要特点（如亲和力、稳定性、特异性等）。2. 收集产品的上市时间、所属生产企业/供应商及其背景。3. 详细获取各产品在不同应用领域（如抗体纯化、诊断试剂、生物传感器等）的具体应用案例和性能表现。4. 收集足以支持进行详细表格对比分析的数据点，包括但不限于产品规格、性能参数、优势和局限性。', 'feedback': '', 'current_step_result': ''}
    print(apply_prompt_template("research_team_router", example_state))
    # Ensure that the example_prompt.md file exists in the same directory as this script