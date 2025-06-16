# Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT

import json
import logging
import os
from typing import Annotated, Literal

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langgraph.types import Command, interrupt
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from src.agents import create_agent
from src.tools import (
    crawl_tool,
    get_web_search_tool,
    python_repl_tool,
    get_patent_search_tool,
    get_literature_search_tool,
)
from src.tools.protein.unsupervise import (
    get_unsupervise_result,
    get_unsupervise_task_status,
    submit_unsupervise_task,
)
from src.graph.types import ProteinSequenceList

from src.config.agents import AGENT_LLM_MAP
from src.config.configuration import Configuration
from src.llms.llm import get_llm_by_type, invoke_llm_with_retry, ainvoke_llm_with_retry, get_agent_llm
from src.prompts.planner_model import Plan, StepType
from src.prompts.template import apply_prompt_template, env
from src.utils.json_utils import repair_json_output

from .types import State, Interrupt

logger = logging.getLogger(__name__)


@tool
def handoff_to_planner(
    task_title: Annotated[str, "The title of the task to be handed off."],
    locale: Annotated[str, "The user's detected language locale (e.g., en-US, zh-CN)."],
):
    """Handoff to planner agent to do plan."""
    # This tool is not returning anything: we're just using it
    # as a way for LLM to signal that it needs to hand off to planner agent
    return

def convert_search_result_to_str(search_results: list[dict] | str) -> str:
    if isinstance(search_results, str):
        return search_results
    if isinstance(search_results, list):
        results = [
            {"title": elem.get("title", ""), "url": elem.get("url", ""), "content": elem.get("content", "")}
            for elem in search_results
        ]
        results = json.dumps(results, ensure_ascii=False)
    else:
        logger.error(f"Web search tool returned unexpected type: {type(search_results)}. Content: {search_results}")
        results = ""
    return results

def background_investigation_node(
    state: State, config: RunnableConfig
) -> Command[Literal["planner"]]:
    logger.info("background investigation node is running.")
    configurable = Configuration.from_runnable_config(config)
    user_query = state["user_query"]
    investigator_messages = apply_prompt_template("background_investigator", state=state)
    investigator_llm = get_agent_llm("background_investigator")
    
    investigator_response = invoke_llm_with_retry(investigator_llm, investigator_messages)
    
    if hasattr(investigator_response, 'content'):
        search_query = investigator_response.content.strip()
    else:
        search_query = str(investigator_response).strip()

    logger.info(f"Generated search query by background_investigator: '{search_query}'")

    # 2. Perform Web Search with the generated query
    if not search_query:
        logger.warning("Background investigator returned an empty search query. Using original user query.")
        search_query = user_query

    background_investigation_results = None
    try:
        search_results_raw = get_web_search_tool( 
            configurable.max_search_results
        ).invoke(search_query)
        background_investigation_results = convert_search_result_to_str(search_results_raw)
    except Exception as e:
        logger.error(f"Error during web search: {e}")
        background_investigation_results = ""

    # 3. Update state and go to planner
    return Command(
        update={
            "background_investigation_results": background_investigation_results
        },
        goto="planner",
    )


def planner_node(
    state: State, config: RunnableConfig
) -> Command[Literal["human_feedback", "reporter"]]:
    """Planner node that generate the full plan."""
    logger.info("Planner generating full plan")
    configurable = Configuration.from_runnable_config(config)
    plan_iterations = state["plan_iterations"] if state.get("plan_iterations", 0) else 0
    messages = apply_prompt_template("planner", state, configurable)

    if (
        plan_iterations == 0
        and state.get("enable_background_investigation")
        and state.get("background_investigation_results")
    ):
        messages += [
            {
                "role": "user",
                "content": (
                    "background investigation results of user query:\n"
                    + state["background_investigation_results"]
                    + "\n"
                ),
            }
        ]

    if AGENT_LLM_MAP["planner"] == "basic":
        llm = get_llm_by_type(AGENT_LLM_MAP["planner"]).with_structured_output(
            Plan,
            method="json_mode",
        )
    else:
        llm = get_llm_by_type(AGENT_LLM_MAP["planner"])

    # if the plan iterations is greater than the max plan iterations, return the reporter node
    if plan_iterations >= configurable.max_plan_iterations:
        return Command(goto="reporter")

    full_response = ""
    if AGENT_LLM_MAP["planner"] == "basic":
        response = invoke_llm_with_retry(llm, messages)
        full_response = response.model_dump_json(indent=4, exclude_none=True)
    else:
        response = invoke_llm_with_retry(llm, messages, stream=True)
        for chunk in response:
            full_response += chunk.content
    logger.debug(f"Current state messages: {state['messages']}")
    logger.info(f"Planner response: {full_response}")

    try:
        curr_plan = json.loads(repair_json_output(full_response))
    except json.JSONDecodeError:
        logger.warning("Planner response is not a valid JSON")
        if plan_iterations > 0:
            return Command(goto="reporter")
        else:
            return Command(goto="__end__")
    if curr_plan.get("has_enough_context"):
        logger.info("Planner response has enough context.")
        new_plan = Plan.model_validate(curr_plan)
        return Command(
            update={
                "messages": [AIMessage(content=full_response, name="planner")],
                "current_plan": new_plan,
            },
            goto="reporter",
        )
    return Command(
        update={
            "messages": [AIMessage(content=full_response, name="planner")],
            "current_plan": full_response,
        },
        goto="human_feedback",
    )


def human_feedback_node(
    state,
) -> Command[Literal["planner", "research_team", "reporter", "__end__"]]:
    current_plan = state.get("current_plan", "")
    # check if the plan is auto accepted
    auto_accepted_plan = state.get("auto_accepted_plan", False)
    if not auto_accepted_plan:
        interrupt_payload: Interrupt = {
            "interrupt_type": "plan_review",
            "content": "Please Review the Plan.",
            "options": [
                {"text": "Edit plan", "value": "edit_plan"},
                {"text": "Start research", "value": "accepted"},
            ],
            "extra_data": {}
        }
        feedback = interrupt(interrupt_payload)

        # if the feedback is not accepted, return the planner node
        if feedback and str(feedback).upper().startswith("[EDIT_PLAN]"):
            return Command(
                update={
                    "messages": [
                        HumanMessage(content=feedback, name="feedback"),
                    ],
                },
                goto="planner",
            )
        elif feedback and str(feedback).upper().startswith("[ACCEPTED]"):
            logger.info("Plan is accepted by user.")
        else:
            raise TypeError(f"Interrupt value of {feedback} is not supported.")

    # if the plan is accepted, run the following node
    plan_iterations = state["plan_iterations"] if state.get("plan_iterations", 0) else 0
    goto = "research_team"
    try:
        current_plan = repair_json_output(current_plan)
        # increment the plan iterations
        plan_iterations += 1
        # parse the plan
        new_plan = json.loads(current_plan)
        if new_plan["has_enough_context"]:
            goto = "reporter"
    except json.JSONDecodeError:
        logger.warning("Planner response is not a valid JSON")
        if plan_iterations > 0:
            return Command(goto="reporter")
        else:
            return Command(goto="__end__")

    return Command(
        update={
            "current_plan": Plan.model_validate(new_plan),
            "plan_iterations": plan_iterations,
            "locale": new_plan["locale"],
        },
        goto=goto,
    )


def coordinator_node(
    state: State,
) -> Command[Literal["planner", "background_investigator", "__end__"]]:
    """Coordinator node that communicate with customers."""
    logger.info("Coordinator talking.")
    messages = apply_prompt_template("coordinator", state)
    user_query = messages[-1].content
    llm = (
        get_llm_by_type(AGENT_LLM_MAP["coordinator"])
        .bind_tools([handoff_to_planner])
    )
    response= invoke_llm_with_retry(llm, messages)
    logger.debug(f"Current state messages: {state['messages']}")

    goto = "__end__"
    locale = state.get("locale", "en-US")  # Default locale if not specified

    if len(response.tool_calls) > 0:
        goto = "planner"
        if state.get("enable_background_investigation"):
            # if the search_before_planning is True, add the web search tool to the planner agent
            goto = "background_investigator"
        try:
            for tool_call in response.tool_calls:
                if tool_call.get("name", "") != "handoff_to_planner":
                    continue
                if tool_locale := tool_call.get("args", {}).get("locale"):
                    locale = tool_locale
                    break
        except Exception as e:
            logger.error(f"Error processing tool calls: {e}")
    else:
        logger.warning(
            "Coordinator response contains no tool calls. Terminating workflow execution."
        )
        logger.debug(f"Coordinator response: {response}")

    return Command(
        update={"locale": locale, "user_query": user_query},
        goto=goto,
    )


def reporter_node(state: State):
    """Reporter node that write a final report."""
    logger.info("Reporter write final report")
    current_plan = state.get("current_plan")
    input_ = {
        "messages": [
            HumanMessage(
                f"# Research Requirements\n\n## Task\n\n{current_plan.title}\n\n## Description\n\n{current_plan.thought}"
            )
        ],
        "locale": state.get("locale", "en-US"),
    }
    invoke_messages = apply_prompt_template("reporter", input_)
    observations = state.get("observations", [])

    # Add a reminder about the new report format, citation style, and table usage
    invoke_messages.append(
        HumanMessage(
            content="IMPORTANT: Structure your report according to the format in the prompt. Remember to include:\n\n1. Key Points - A bulleted list of the most important findings\n2. Overview - A brief introduction to the topic\n3. Detailed Analysis - Organized into logical sections\n4. Survey Note (optional) - For more comprehensive reports\n5. Key Citations - List all references at the end\n\nFor citations, DO NOT include inline citations in the text. Instead, place all citations in the 'Key Citations' section at the end using the format: `- [Source Title](URL)`. Include an empty line between each citation for better readability.\n\nPRIORITIZE USING MARKDOWN TABLES for data presentation and comparison. Use tables whenever presenting comparative data, statistics, features, or options. Structure tables with clear headers and aligned columns. Example table format:\n\n| Feature | Description | Pros | Cons |\n|---------|-------------|------|------|\n| Feature 1 | Description 1 | Pros 1 | Cons 1 |\n| Feature 2 | Description 2 | Pros 2 | Cons 2 |",
            name="system",
        )
    )

    for observation in observations:
        invoke_messages.append(
            HumanMessage(
                content=f"Below are some observations for the research task:\n\n{observation}",
                name="observation",
            )
        )
    logger.debug(f"Current invoke messages: {invoke_messages}")
    llm = get_llm_by_type(AGENT_LLM_MAP["reporter"])
    response = invoke_llm_with_retry(llm, invoke_messages)
    response_content = response.content
    logger.info(f"reporter response: {response_content}")

    return {"final_report": response_content}


def research_team_node(
    state: State,
) -> Command[Literal["planner", "researcher", "coder"]]:
    """Research team node that collaborates on tasks."""
    logger.info("Research team is collaborating on tasks.")
    current_plan = state.get("current_plan")
    if not current_plan or not current_plan.steps:
        return Command(goto="planner")
    if all(step.execution_res for step in current_plan.steps):
        return Command(goto="planner")
    for step in current_plan.steps:
        if not step.execution_res:
            break
    if step.step_type and step.step_type == StepType.RESEARCH:
        return Command(goto="researcher")
    if step.step_type and step.step_type == StepType.PROCESSING:
        return Command(goto="coder")
    return Command(goto="planner")


async def _execute_agent_step(
    state: State, agent, agent_name: str
) -> Command[Literal["research_team"]]:
    """Helper function to execute a step using the specified agent."""
    current_plan = state.get("current_plan")
    observations = state.get("observations", [])

    # Find the first unexecuted step
    current_step = None
    completed_steps = []
    for step in current_plan.steps:
        if not step.execution_res:
            current_step = step
            break
        else:
            completed_steps.append(step)

    if not current_step:
        logger.warning("No unexecuted step found")
        return Command(goto="research_team")

    logger.info(f"Executing step: {current_step.title}")

    # Format completed steps information
    completed_steps_info = ""
    if completed_steps:
        completed_steps_info = "# Existing Research Findings\n\n"
        for i, step in enumerate(completed_steps):
            completed_steps_info += f"## Existing Finding {i+1}: {step.title}\n\n"
            completed_steps_info += f"<finding>\n{step.execution_res}\n</finding>\n\n"

    # Prepare the input for the agent with completed steps info
    agent_input = {
        "messages": [
            HumanMessage(
                content=f"{completed_steps_info}# Current Task\n\n## Title\n\n{current_step.title}\n\n## Description\n\n{current_step.description}\n\n## Locale\n\n{state.get('locale', 'en-US')}"
            )
        ]
    }

    # Add citation reminder for researcher agent
    if agent_name == "researcher":
        agent_input["messages"].append(
            HumanMessage(
                content="IMPORTANT: DO NOT include inline citations in the text. Instead, track all sources and include a References section at the end using link reference format. Include an empty line between each citation for better readability. Use this format for each reference:\n- [Source Title](URL)\n\n- [Another Source](URL)",
                name="system",
            )
        )

    # Invoke the agent
    default_recursion_limit = 25
    try:
        env_value_str = os.getenv("AGENT_RECURSION_LIMIT", str(default_recursion_limit))
        parsed_limit = int(env_value_str)

        if parsed_limit > 0:
            recursion_limit = parsed_limit
            logger.info(f"Recursion limit set to: {recursion_limit}")
        else:
            logger.warning(
                f"AGENT_RECURSION_LIMIT value '{env_value_str}' (parsed as {parsed_limit}) is not positive. "
                f"Using default value {default_recursion_limit}."
            )
            recursion_limit = default_recursion_limit
    except ValueError:
        raw_env_value = os.getenv("AGENT_RECURSION_LIMIT")
        logger.warning(
            f"Invalid AGENT_RECURSION_LIMIT value: '{raw_env_value}'. "
            f"Using default value {default_recursion_limit}."
        )
        recursion_limit = default_recursion_limit

    result = await ainvoke_llm_with_retry(agent, agent_input, config={"recursion_limit": recursion_limit}
    )

    # Process the result
    response_content = result["messages"][-1].content
    logger.debug(f"{agent_name.capitalize()} full response: {response_content}")

    # Update the step with the execution result
    current_step.execution_res = response_content
    logger.info(f"Step '{current_step.title}' execution completed by {agent_name}")

    return Command(
        update={
            "messages": [
                HumanMessage(
                    content=response_content,
                    name=agent_name,
                )
            ],
            "observations": observations + [response_content],
        },
        goto="research_team",
    )
    

async def _setup_and_execute_agent_step(
    state: State,
    config: RunnableConfig,
    agent_type: str,
    default_tools: list,
) -> Command[Literal["research_team"]]:
    """Helper function to set up an agent with appropriate tools and execute a step.

    This function handles the common logic for both researcher_node and coder_node:
    1. Configures MCP servers and tools based on agent type
    2. Creates an agent with the appropriate tools or uses the default agent
    3. Executes the agent on the current step

    Args:
        state: The current state
        config: The runnable config
        agent_type: The type of agent ("researcher" or "coder")
        default_tools: The default tools to add to the agent

    Returns:
        Command to update state and go to research_team
    """
    configurable = Configuration.from_runnable_config(config)
    mcp_servers = {}
    enabled_tools = {}

    # Extract MCP server configuration for this agent type
    if configurable.mcp_settings:
        for server_name, server_config in configurable.mcp_settings["servers"].items():
            if (
                server_config["enabled_tools"]
                and agent_type in server_config["add_to_agents"]
            ):
                mcp_servers[server_name] = {
                    k: v
                    for k, v in server_config.items()
                    if k in ("transport", "command", "args", "url", "env")
                }
                for tool_name in server_config["enabled_tools"]:
                    enabled_tools[tool_name] = server_name

    # Create and execute agent with MCP tools if available
    if mcp_servers:
        async with MultiServerMCPClient(mcp_servers) as client:
            loaded_tools = default_tools[:]
            for tool in client.get_tools():
                if tool.name in enabled_tools:
                    tool.description = (
                        f"Powered by '{enabled_tools[tool.name]}'.\n{tool.description}"
                    )
                    loaded_tools.append(tool)
            agent = create_agent(agent_type, agent_type, loaded_tools, agent_type)
            return await _execute_agent_step(state, agent, agent_type)
    else:
        # Use default tools if no MCP servers are configured
        agent = create_agent(agent_type, agent_type, default_tools, agent_type)
        return await _execute_agent_step(state, agent, agent_type)


async def researcher_node(
    state: State, config: RunnableConfig
) -> Command[Literal["research_team"]]:
    """Researcher node that conducts research."""
    logger.info("Researcher searching for information.")
    configurable = Configuration.from_runnable_config(config)
    web_search_tool = get_web_search_tool(configurable.max_search_results)
    # patent_search_tool = get_patent_search_tool(configurable.max_search_results)
    literture_search_tool = get_literature_search_tool(configurable.max_search_results)

    default_tools = [
        web_search_tool,
        crawl_tool,
        # patent_search_tool,
        literture_search_tool,
    ]
    return await _setup_and_execute_agent_step(
        state, config, "researcher", default_tools
    )


async def coder_node(
    state: State, config: RunnableConfig
) -> Command[Literal["research_team"]]:
    """Coder node that executes code."""
    logger.info("Coder executing code.")
    return await _setup_and_execute_agent_step(
        state, config, "coder", [python_repl_tool]
    )


async def enzyme_retriever_node(
    state: State, config: RunnableConfig
) -> dict[str, any]:
    """Enzyme sequence retriever node that retrieve enzyme sequence."""
    logger.info("Enzyme sequence retriever node is retrieving.")
    
    # Base prompt on the final report
    final_report = state.get("final_report", "")
    input_content = final_report

    # Check for feedback from the user and add it to the prompt
    last_message = state["messages"][-1]
    if (
        isinstance(last_message, HumanMessage)
        and last_message.content
        and last_message.content.upper().startswith("[REQUEST_MORE_INFO]")
    ):
        logger.info("Enzyme retriever has received feedback from the user.")
        feedback_content = (
            "\n\nThe user has requested more information. Please address this feedback:\n"
            f"{last_message.content}"
        )
        input_content += feedback_content

    _input_state = {
        "messages": [HumanMessage(content=input_content)],
        "locale": state.get("locale", "en-US"),
    }
    agent_name = "enzyme_retriever"
    template = env.get_template(f"{agent_name}.md")
    prompt = template.render(**_input_state)
    
    input_ = {"messages": [HumanMessage(content=input_content, name="human")]}

    configurable = Configuration.from_runnable_config(config)
    mcp_servers = {}
    enabled_tools = {}

    # Extract MCP server configuration for this agent type
    if configurable.mcp_settings:
        for server_name, server_config in configurable.mcp_settings["servers"].items():
            if server_config["enabled_tools"]:
                mcp_servers[server_name] = {
                    k: v
                    for k, v in server_config.items()
                    if k in ("transport", "command", "args", "url", "env")
                }
                for tool_name in server_config["enabled_tools"]:
                    enabled_tools[tool_name] = server_name

    tools = [get_web_search_tool(configurable.max_search_results), crawl_tool]
    # Create and execute agent with MCP tools if available
    if mcp_servers:
        async with MultiServerMCPClient(mcp_servers) as client:
            for tool in client.get_tools():
                if tool.name in enabled_tools:
                    tool.description = (
                        f"Powered by '{enabled_tools[tool.name]}'.\n{tool.description}"
                    )
                    tools.append(tool)
            agent = create_react_agent(
                name=agent_name,
                model=get_llm_by_type(AGENT_LLM_MAP[agent_name]),
                tools=tools,
                prompt=prompt,
            )
            response = await ainvoke_llm_with_retry(
                agent, input_, must_used_tool=True, config={"recursion_limit": 25}
            )
    else:
        agent = create_react_agent(
            name=agent_name,
            model=get_llm_by_type(AGENT_LLM_MAP[agent_name]),
            tools=tools,
            prompt=prompt,
        )
        response = await ainvoke_llm_with_retry(
            agent, input_, must_used_tool=True, config={"recursion_limit": 25}
        )
    enzyme_retriever_content = response["messages"][-1].content
    logger.info(f"Enzyme retriever content: {enzyme_retriever_content}")

    return {"enzyme_retriever_content": enzyme_retriever_content}

async def enzyme_parser_node(
    state: State, config: RunnableConfig
) -> dict[str, any]:
    """Enzyme parser node that parses the enzyme retriever content."""
    logger.info("Enzyme parser node is parsing.")
    enzyme_retriever_content = state.get("enzyme_retriever_content", "")

    try:
        parser_agent_name = "enzyme_parser"
        parser_template_str = env.get_template(f"{parser_agent_name}.md").render()
        parser_llm = get_llm_by_type(AGENT_LLM_MAP[parser_agent_name]).with_structured_output(ProteinSequenceList, method="json_mode")
        messages = [
            SystemMessage(content=parser_template_str),
            HumanMessage(content=enzyme_retriever_content)
        ]
        logger.info("Parsing enzyme retriever results.")
        parsed_results = await ainvoke_llm_with_retry(parser_llm, messages, config=config)
        logger.info("Successfully parsed enzyme results into structured data.")
        logger.info(f"Parsed results: {parsed_results}")
        enzyme_retriever_sequences = parsed_results.protein_sequences

    except Exception as e:
        logger.error(f"Failed to parse enzyme retriever results, falling back to markdown. Error: {e}")
        # Fallback to returning the original markdown content if parsing fails
        enzyme_retriever_sequences = []

    return {"enzyme_retriever_sequences": enzyme_retriever_sequences}


def human_select_node(
    state: State,
) -> Command[Literal["enzyme_designer", "enzyme_retriever"]]:
    """
    Interrupts the workflow to allow the user to select enzymes for design
    or request more information. The user's response should start with:
    - [ACCEPT_SEQUENCES] to proceed with design.
    - [REQUEST_MORE_INFO] to ask for more details.
    """
    logger.info("Awaiting user selection for enzyme design.")

    sequences = state.get("enzyme_retriever_sequences", [])
    # Convert Pydantic objects to dicts for JSON serialization
    sequences_as_dicts = [seq.model_dump() for seq in sequences]

    interrupt_payload: Interrupt = {
        "interrupt_type": "enzyme_selection",
        "content": (
            "Please review the enzyme information. \n"
        ),
        "options": [
            {"text": "Accept Sequences", "value": "accept_sequences"},
            {"text": "Request More Info", "value": "request_more_info"},
        ],
        "extra_data": {
            "sequences": sequences_as_dicts
        }
    }

    feedback = interrupt(interrupt_payload)

    # The user's response is prefixed with the option value, e.g., '[accept_sequences] ...'
    # The prefix is added in app.py. The content of the user's response is also in `feedback`.
    full_message = HumanMessage(content=str(feedback), name="human_selection")

    if feedback and str(feedback).upper().startswith("[ACCEPT_SEQUENCES]"):
        logger.info("User accepted sequences. Routing to enzyme designer.")
        return Command(
            update={"messages": state["messages"] + [full_message]},
            goto="enzyme_designer",
        )

    # Default to requesting more info, which is the safer option.
    # This also covers the `startswith("[REQUEST_MORE_INFO]")` case.
    logger.info("User requested more information. Routing back to enzyme retriever.")
    return Command(
        update={"messages": state["messages"] + [full_message]},
        goto="enzyme_retriever",
    )


async def enzyme_designer_node(state: State, config: RunnableConfig):
    """
    Handles protein design tasks. It can either submit a new task
    or check the status of an existing task based on user input.
    """
    user_message = state["messages"][-1].content
    retrieved_enzymes = state.get("enzyme_retriever_sequences", [])
    retrieved_enzymes_str = ""
    for seq in retrieved_enzymes:
        retrieved_enzymes_str += f"### {seq.protein_name}\n"
        retrieved_enzymes_str += f"Sequence: {seq.sequence}\n"
        retrieved_enzymes_str += f"Organism: {seq.organism_name}\n"
        retrieved_enzymes_str += f"Accession: {seq.accession}\n"
        retrieved_enzymes_str += f"Gene Name: {seq.gene_name}\n"
        retrieved_enzymes_str += "\n"

    task_id = state.get("design_task_id")

    # Create a tool-augmented LLM to decide the next step
    designer_llm = get_agent_llm("enzyme_designer")
    tools = [
        submit_unsupervise_task,
        get_unsupervise_task_status,
        get_unsupervise_result,
    ]
    agent_name = "enzyme_designer"
    enzyme_retriever_content = state.get("enzyme_retriever_content", "")
    messges = [
        AIMessage(content=enzyme_retriever_content),
    ]
    
    designer_agent = create_agent(
        llm=designer_llm,
        tools=tools,
        agent_type=agent_name,
        messages=apply_prompt_template(
            agent_name,
            {
                "user_request": user_message,
                "retrieved_enzymes": retrieved_enzymes_str,
                "task_id": task_id,
                "messages": messges
            },
        ),
    )

    # Invoke the agent
    response = await ainvoke_llm_with_retry(
        designer_agent,
        llm_input=[HumanMessage(content=user_message)],
        # must_used_tool=True,
    )

    # If the agent calls a tool, we process it
    if response.tool_calls:
        # For now, we assume one tool call at a time for simplicity
        tool_call = response.tool_calls[0]
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]

        tool_map = {tool.name: tool for tool in tools}
        tool_to_call = tool_map.get(tool_name)

        if not tool_to_call:
            # Handle error: tool not found
            return {
                "messages": state["messages"] + [AIMessage(content=f"Error: Tool '{tool_name}' not found.")]
            }

        # Call the tool and get the result
        observation = tool_to_call.invoke(tool_args)

        # Update state based on the tool called
        update_dict = {
            "messages": state["messages"] + [
                response,
                ToolMessage(content=str(observation), tool_call_id=tool_call["id"]),
            ]
        }

        if tool_name == "submit_unsupervise_task":
            update_dict["design_task_id"] = str(observation)
        elif tool_name == "get_unsupervise_result":
            update_dict["enzyme_mutant_results"] = observation

        return update_dict

    # If no tool is called, just return the text response
    return {"messages": state["messages"] + [response]}


if __name__ == "__main__":
    agent_name = 'enzyme_retriever'
    _input_state = {
            "messages": [],
            "locale": "en-US",
    }
    pass
