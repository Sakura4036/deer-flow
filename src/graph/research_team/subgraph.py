# Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT

import json
import logging
from typing import List, Literal

from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool
from langgraph.graph import StateGraph, END, START
from langgraph.types import Command

from src.agents import create_agent
from src.config.configuration import Configuration
from src.graph.types import ResearchTeamSubgraphState, TaskPlan, SummaryOutput
from src.llms.llm import get_agent_llm
from src.prompts.template import apply_prompt_template
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

    # Apply prompt template for router
    messages = apply_prompt_template("research_team_router", state)

    # Add context from main graph observations if available
    if state.get("task_context"):
        context_message = "# Additional Context From Previous Research\n\n"
        for obs in state.get("task_context", []):
            context_message += f"## {obs.get('title', 'Observation')}\n{obs.get('content', '')}\n\n"

        messages.append(HumanMessage(content=context_message))

    # Prepare LLM with structured output for JSON response
    llm = get_agent_llm("router").with_structured_output(
        TaskPlan,
        method="json_mode",
    )

    # Invoke LLM to create sub-task plan
    response = llm.invoke(messages)
    logger.debug(f"Router response: {response}")

    # Parse the response and validate
    sub_tasks = response.sub_tasks

    logger.info(f"Created {len(sub_tasks)} sub-tasks for research")

    return Command(
        update={
            "task_plan": sub_tasks,
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
        return [get_patent_search_tool(configurable.max_search_results)]
    elif researcher_type == "literature_researcher":
        return [get_literature_search_tool(configurable.max_search_results)]
    elif researcher_type == "coding_researcher":
        return [python_repl_tool]
    else:
        return [get_web_search_tool(configurable.max_search_results), crawl_tool]


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
    current_index = state.get("current_sub_task_index", 0)

    # Check if we've completed all subtasks
    if not task_plan or current_index >= len(task_plan):
        logger.info("All subtasks completed, moving to summary node")
        return Command(goto="summary")

    current_subtask = task_plan[current_index]
    researcher_type = current_subtask.assigned_researcher_type

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
                content=f"# Research Subtask\n\n## Task Description\n\n{current_subtask.description}\n\n"
            )
        ]
    }

    observations = state.get("observations", [])
    for obs in observations:
        agent_input["messages"].append(
            HumanMessage(
                content=f"Below are some observations for the Subtask:\n\n{obs['content']}",
                name="observation",
            )
        )

    # Add input data if available
    if current_subtask.input_data:
        agent_input["messages"].append(
            HumanMessage(
                content=f"## Additional Input Data\n\n```json\n{json.dumps(current_subtask.input_data, indent=2)}\n```"
            )
        )

    # Invoke the agent
    try:
        result = await agent.ainvoke(
            input=agent_input,
            config={"recursion_limit": 25}
        )

        response_content = result["messages"][-1].content
        logger.debug(f"Researcher response: {response_content}")

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
        observations.append(observation)

        # Move to next subtask
        next_index = current_index + 1
        goto = "summary" if next_index >= len(task_plan) else "researcher"

        return Command(
            update={
                "current_sub_task_index": next_index,
                "observations": observations,
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
                "current_sub_task_index": next_index,
                "error_log": error_log,
                "task_plan": task_plan  # Update with the failed task
            },
            goto=goto
        )


def summary_node(
        state: ResearchTeamSubgraphState, config: RunnableConfig
) -> Command[Literal["router"]]:
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

    # Apply prompt template for summary
    messages = apply_prompt_template("research_team_summary", state)

    # Add the main task objective
    messages.append(
        HumanMessage(
            content=f"# Main Research Task\n\n{state.get('task_description', 'No task specified')}"
        )
    )

    # Add all subtask results
    task_plan = state.get("task_plan", [])
    subtask_results = "# Subtask Results\n\n"

    for i, subtask in enumerate(task_plan):
        subtask_results += f"## Subtask {i + 1}: {subtask.sub_task_id}\n"
        subtask_results += f"**Type**: {subtask.assigned_researcher_type}\n"
        subtask_results += f"**Description**: {subtask.description}\n"
        subtask_results += f"**Status**: {subtask.status}\n\n"

        if subtask.result:
            subtask_results += f"**Results**:\n{subtask.result}\n\n"
        else:
            subtask_results += "**Results**: No results available\n\n"

    messages.append(HumanMessage(content=subtask_results))

    # Add errors if any
    error_log = state.get("error_log", [])
    if error_log:
        error_content = "# Errors Encountered\n\n"
        for error in error_log:
            error_content += f"- Subtask {error.get('subtask_id')}: {error.get('error')}\n"
        messages.append(HumanMessage(content=error_content))

    # Prepare LLM with structured output
    llm = get_agent_llm("research_team_summary").with_structured_output(
        SummaryOutput,
        method="json_mode",
    )

    # Invoke LLM to create summary
    response = llm.invoke(messages)
    logger.debug(f"Summary response: {response}")

    summary = response.summary

    # If task is complete, return final summary and end
    if response.completed:
        logger.info("Research task completed successfully")
        return {"task_summary": summary}

    # If task is not complete, return to router with recommendations
    logger.info("Research task incomplete, returning to router")
    return Command(
        update={
            "feedback": response.feedback,
            "task_summary": summary,
            "task_plan": None,  # Reset the plan for new planning
            "current_sub_task_index": 0
        },
        goto="router"
    )


def build_research_team_subgraph():
    """
    Builds and returns the research team subgraph with router, researcher, and summary nodes.
    
    Returns:
        Compiled research team subgraph
    """
    # Create the subgraph
    research_team_graph = StateGraph(ResearchTeamSubgraphState)

    # Add nodes
    research_team_graph.add_edge(START, "router")
    research_team_graph.add_node("router", router_node)
    research_team_graph.add_node("researcher", researcher_node)
    research_team_graph.add_node("summary", summary_node)
    research_team_graph.add_edge("summary", END)

    # Compile the graph
    return research_team_graph.compile()


# Function to initialize and run the subgraph
async def run_research_team_subgraph(task_description: str, task_context=None, config: RunnableConfig = None):
    """
    Initialize and run the research team subgraph with the given task objective.
    
    Args:
        task_description: The high-level task description
        task_context: Optional context from the parent graph
        config: Configuration for the runnable
        
    Returns:
        The final state of the subgraph after execution
    """
    subgraph = build_research_team_subgraph()

    # Initialize the state
    initial_state = {
        "task_description": task_description,
        "task_context": task_context or [],
        "observations": [],
        "task_plan": None,
        "current_sub_task_index": 0,
        "task_summary": None,
        "error_log": [],
        "messages": [],
    }

    # Run the subgraph
    result = await subgraph.ainvoke(initial_state, config=config, stream_mode="update")

    # state = subgraph.get_state(config)

    return result


if __name__ == "__main__":
    import asyncio

    # 示例任务描述和上下文
    task_description = "Research the latest advancements in quantum computing."
    task_context = [
        {"title": "Previous Finding", "content": "Quantum supremacy was demonstrated by Google in 2019."}
    ]
    config = {
        "configurable": {
            "thread_id": "default",
        },
        "recursion_limit": 100,
    }

    async def main():
        subgraph = build_research_team_subgraph()

        # Initialize the state
        initial_state = {
            "task_description": task_description,
            "task_context": task_context or [],
            "observations": [],
            "task_plan": None,
            "current_sub_task_index": 0,
            "task_summary": None,
            "error_log": [],
            "messages": [],
        }

        # Run the subgraph
        async for event in subgraph.astream_events(initial_state, config):
            kind = event["event"]
            if kind == "on_chat_model_stream":
                content = event["data"]["chunk"].content
                if content:
                    print(content, end='') # Print LLM tokens as they stream
                    pass
            elif kind == "on_tool_start":
                print("--")
                print(f"Starting tool: {event['name']} with inputs: {event['data'].get('input')}")
            elif kind == "on_tool_end":
                print(f"Tool {event['name']} finished.")
                print(f"Tool output: {event['data'].get('output')}")
                print("--")
            elif kind == "on_llm_end":
                # print(f"LLM finished: {event['data']}")
                pass # Avoid printing full LLM end data for brevity
            elif kind == "on_chain_end":
                if event["name"] == "LangGraph": # Print final state
                    print("--- Final State ---")
                    print(event["data"]["output"])

    asyncio.run(main())