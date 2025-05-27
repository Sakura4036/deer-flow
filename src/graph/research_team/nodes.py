# Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT

import json
import logging
from typing import List, Literal, Dict

from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool
from langgraph.graph import StateGraph, END, START
from langgraph.types import Command

from src.agents import create_agent
from src.config.configuration import Configuration
from src.graph.types import ResearchTeamSubgraphState, TaskPlan, SummaryOutput
from src.llms.llm import get_agent_llm, invoke_llm_with_retry, ainvoke_llm_with_retry
from src.prompts.template import apply_prompt_template
from src.prose.graph import state
from src.tools import get_web_search_tool, crawl_tool, python_repl_tool, get_patent_search_tool, get_literature_search_tool

logger = logging.getLogger(__name__)


def router_node(
        state: ResearchTeamSubgraphState, config: RunnableConfig
) -> Command[Literal["researcher"]]:
    """
    Router node analyzes the main task and creates a plan with subtasks 
    assigned to specific researcher types.
    
    Args:
        state: The current state of the research team subgraph
        config: Configuration for the runnable
        
    Returns:
        Command to update state and route to researcher node
    """
    logger.info("Router node planning research subtasks")
    current_plan_description = state.get("current_plan_description", "")
    current_step = state.get('current_step')
    observations = state.get("observations")
    state['task_description'] = f"# Current Research Task for Research Team\n\n## Title\n{current_step.title}\n\n## Task Description\n{current_step.description}"

    # Apply prompt template for router
    _input_state = {
        "messages":[],
        "locale": state.get("locale", "en-US"),
        "task_description": state['task_description'],
        "feedback": state.get("feedback", ""),
        "current_step_result": state.get("current_step_result", ""),
    }
    messages = apply_prompt_template("research_team_router", _input_state)
    # Add context from main graph observations if available
    if observations:
        context_message = "# Additional Context From Previous Research\n\n"
        for obs in observations:
            context_message += f"## {obs.get('title', 'Observation')}\n{obs.get('content', '')}\n\n"

        messages.append(HumanMessage(content=context_message))

    messages.append(HumanMessage(content="You should think step by step and provide a detailed plan for the Research task."))

    llm = get_agent_llm("research_team_router").with_structured_output(
        TaskPlan,
        method="json_mode",
    )
    response = invoke_llm_with_retry(llm, messages)

    # Parse the response and validate
    sub_tasks = response.sub_tasks

    logger.info(f"Created {len(sub_tasks)} sub-tasks for research")

    return Command(
        update={
            "task_plan": sub_tasks,
            "task_description": state['task_description'],
            "current_sub_task_index": 0,
        },
        goto="researcher"
    )


def _get_tools_for_researcher(researcher_type: str, config: RunnableConfig) -> List[BaseTool]:
    """
    Helper function to get appropriate tools based on researcher type
    
    Args:
        researcher_type: Type of researcher
        config: Configuration for the runnable
        
    Returns:
        List of tools for the researcher
    """
    configurable = Configuration.from_runnable_config(config)

    if researcher_type == "web_search_researcher":
        return [get_web_search_tool(configurable.max_search_results), crawl_tool]
    elif researcher_type == "patent_researcher":
        return [get_patent_search_tool(configurable.max_search_results), get_web_search_tool(configurable.max_search_results), crawl_tool]
    elif researcher_type == "literature_researcher":
        return [get_literature_search_tool(configurable.max_search_results), crawl_tool]
    elif researcher_type == "coding_researcher":
        return [python_repl_tool]
    else:
        raise ValueError(f"{researcher_type} are not supported!")


async def researcher_node(
        state: ResearchTeamSubgraphState, config: RunnableConfig
) -> Command[Literal["researcher", "summary"]]:
    """
    Researcher node executes the current subtask using the appropriate 
    researcher agent type.
    
    Args:
        state: The current state of the research team subgraph
        config: Configuration for the runnable
        
    Returns:
        Command to update state and route to next node
    """
    logger.info("Researcher node executing subtask")

    # Get current subtask
    task_plan = state.get("task_plan", [])
    task_description = state.get("task_description", "")
    current_index = state.get("current_sub_task_index", 0)

    # Check if we've completed all subtasks
    if not task_plan or current_index >= len(task_plan):
        logger.info("All subtasks completed, moving to summary node")
        return Command(goto="summary")

    current_subtask = task_plan[current_index]
    researcher_type = current_subtask.researcher_type

    logger.info(f"Executing subtask {current_index + 1}/{len(task_plan)}: {current_subtask.sub_task_id}")
    logger.info(f"Using researcher type: {researcher_type}")

    # Get appropriate tools for this researcher
    tools = _get_tools_for_researcher(researcher_type, config)

    # Create the agent with appropriate tools
    agent = create_agent(
        agent_type=researcher_type,
        agent_name=researcher_type,
        tools=tools,
        prompt_template=researcher_type
    )

    # Prepare agent input with context
    agent_input = {
        "messages": [
            HumanMessage(
                content=f"{task_description}\n\n ## Your SubTask Description\n\n{current_subtask.description}\n\n"
                        "You should think step by step to solve the task. "
            )
        ]
    }

    task_observations = state.get("task_observations", [])
    if task_observations:
        # only get observations from same researcher
        # task_observations = [obs for obs in task_observations if obs['source'] == researcher_type]
        context_message = "# Additional Context From Previous Research\n\n"
        for obs in task_observations:
            context_message += f"## {obs.get('title', 'Observation')}\n{obs.get('content', '')}\nSource: {obs.get('source')}\n\n"
    
        agent_input["messages"].append(
            HumanMessage(content=context_message, name="observations")
        )

    # Invoke the agent
    try:
        config = {"recursion_limit": 25}
        try:
            result = await ainvoke_llm_with_retry(agent, agent_input, config=config)
        except Exception as e:
            logger.error(f"Error invoking agent: {e}")
            result = await agent.ainvoke(agent_input, config=config)

        response_content = result["messages"][-1].content
        logger.info(f"Researcher response: {response_content}")

        # Update the subtask with results
        current_subtask.result = response_content
        current_subtask.status = "completed"

        # Add to observations
        observation = {
            "id": current_subtask.sub_task_id,
            "title": f"Subtask {current_index + 1}: {current_subtask.sub_task_id}",
            "content": response_content,
            "source": researcher_type
        }
        task_observations.append(observation)

        # Move to next subtask
        next_index = current_index + 1
        goto = "summary" if next_index >= len(task_plan) else "researcher"

        return Command(
            update={
                # "messages": [HumanMessage(
                #     content=response_content,
                #     name=researcher_type
                # )],
                "current_sub_task_index": next_index,
                "task_observations": task_observations,
                "task_plan": task_plan  # Update with the completed task
            },
            goto=goto
        )

    except Exception as e:
        logger.error(f"Error executing subtask: {e}")
        current_subtask.status = "failed"

        # Log the error
        error_log = state.get("error_log", [])
        error_log.append({
            "subtask_id": current_subtask.sub_task_id,
            "error": str(e),
            "researcher_type": researcher_type
        })

        # Move to next subtask despite error
        next_index = current_index + 1
        goto = "summary" if next_index >= len(task_plan) else "researcher"

        return Command(
            update={
                # "messages": [HumanMessage(
                #     content=f"Error executing subtask {current_subtask.sub_task_id}:\n {e}\n",
                #     name=researcher_type
                # )],
                "current_sub_task_index": next_index,
                "error_log": error_log,
                "task_plan": task_plan  # Update with the failed task
            },
            goto=goto
        )


async def summary_node(
        state: ResearchTeamSubgraphState, config: RunnableConfig
) -> Dict[str, any] | Command[Literal["router"]]:
    """
    Summary node evaluates all subtask results, summarizes findings,
    and determines if the task is complete or needs more research.
    
    Args:
        state: The current state of the research team subgraph
        config: Configuration for the runnable
        
    Returns:
        Command to update state and route to next node or END
    """
    logger.info("Summary node evaluating research results")

    task_description = state.get("task_description", "")

    # Apply prompt template for summary
    messages = apply_prompt_template("research_team_summary", state)

    messages.append(HumanMessage(content=task_description))

    # # Add all subtask results
    task_plan = state.get("task_plan", [])
    context = "# Below are the results of each subtask performed by the research team.\n\n"
    for i, subtask in enumerate(task_plan):
        context += f"## Subtask {i + 1}: {subtask.sub_task_id}\n"
        context += f"Researcher Type: {subtask.researcher_type}\n\n"
        context += f"**Results**:\n{subtask.result if subtask.result else 'No results available'}\n\n"

    messages.append(HumanMessage(content=context, name="observations"))

    # Add errors if any
    error_log = state.get("error_log", [])
    if error_log:
        error_content = "# Errors Encountered\n\n"
        for error in error_log:
            error_content += f"- Subtask {error.get('subtask_id')}: {error.get('error')}\n"
        messages.append(HumanMessage(content=error_content, name="observations"))

    # Prepare LLM with structured output
    llm = get_agent_llm("research_team_summary").with_structured_output(SummaryOutput, method='json_mode')

    # Invoke LLM to create summary
    response = invoke_llm_with_retry(llm, messages)
    logger.info(f"Summary response: {response}")
    logger.info("Research task completed successfully")

    if response.completed:
        return {"current_step_result": response.summary}
    else:
        return Command(goto="router", update={"current_step_result": response.summary, "feedback": response.feedback})
