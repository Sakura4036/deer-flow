# Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT
import logging

from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, END, START
from src.graph.research_team.nodes import researcher_node, router_node, summary_node
from src.graph.types import ResearchTeamSubgraphState

logger = logging.getLogger(__name__)


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
    task_description = "Write a market and application research report on ProteinA enzyme products"
    task_context = []
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
