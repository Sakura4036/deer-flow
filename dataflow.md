### LangGraph State Flow

The LangGraph workflow manages state transitions between agent nodes. Each node processes the current state and returns a `Command` object that updates the state and directs the workflow to the next node:

```mermaid
stateDiagram-v2
    [*] --> coordinator_node
    
    state if_coordinator <<choice>>
    coordinator_node --> if_coordinator
    if_coordinator --> background_investigation_node: enable_background_investigation
    if_coordinator --> planner_node: Has enough context
    if_coordinator --> [*]: No handoff
    
    background_investigation_node --> planner_node
    
    state if_planner <<choice>>
    planner_node --> if_planner
    if_planner --> human_feedback_node: Plan needs review
    if_planner --> reporter_node: Has enough context
    
    state if_feedback <<choice>>
    human_feedback_node --> if_feedback
    if_feedback --> planner_node: Edit plan
    if_feedback --> research_team_node: Accept plan
    
    state if_research <<choice>>
    research_team_node --> if_research
    if_research --> researcher_node: Research step
    if_research --> coder_node: Processing step
    if_research --> reporter_node: All steps completed
    
    researcher_node --> research_team_node
    coder_node --> research_team_node
    reporter_node --> enzyme_retriever_node

    enzyme_retriever_node --> ezyme_parser_node
    ezyme_parser_node --> human_select_node

    state if_selection <<choice>>
    human_select_node --> if_selection: "Wait for Human Input"
    if_selection --> enzyme_designer_node: "Selection provided"
    if_selection --> enzyme_retriever_node: "More info requested"

    state if_designer_action <<choice>>
    enzyme_designer_node --> if_designer_action: "Analyze request"
    if_designer_action --> task_submitted: "No task ID, submit task"
    if_designer_action --> check_status: "Has task ID, check status"

    task_submitted --> [*]: "Inform user and wait"
    
    state if_status <<choice>>
    check_status --> if_status: "Get task status"
    if_status --> get_results: "Completed"
    if_status --> [*]: "Not completed, inform user"

    get_results --> [*]: "Return results to user"
```

Sources:
- src/graph/nodes.py

The state object in LangGraph contains:

| State Key                          | Description                                     |
| ---------------------------------- | ----------------------------------------------- |
| `messages`                         | History of conversation messages                |
| `plan_iterations`                  | Number of plan refinement cycles                |
| `current_plan`                     | The current research plan being executed        |
| `observations`                     | Results collected from research steps           |
| `final_report`                     | The generated report at the end of the workflow |
| `locale`                           | Detected language locale for the conversation   |
| `auto_accepted_plan`               | Whether to automatically accept plans           |
| `enable_background_investigation`  | Whether to perform background searches          |
| `background_investigation_results` | Results from background investigations          |
| `enzyme_retriever_content`         | Results from enzyme retriever node              |
| `enzyme_retriever_sequences`       | Enzyme infos parsed by enzyme parser node       |
| `enzyme_selection_feedback`        | User's natural language selection for design    |
| `design_task_id`                   | The ID of the submitted protein design task     |
| `enzyme_mutant_results`            | Mutant results from enzyme_designer_node        |

Sources:
- src/graph/nodes.py
- src/graph/types.py