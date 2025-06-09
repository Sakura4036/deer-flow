### High-Level Architecture

```mermaid
graph TB
    subgraph "Frontend (Next.js)"
        direction TB
        WebUI["Web UI Components"]
        Store["useStore (store.ts)"]
        SettingsStore["useSettingsStore (settings-store.ts)"]
        ChatAPI["chatStream() (chat.ts)"]
    end
    
    subgraph "Backend (FastAPI)"
        direction TB
        Server["FastAPI App (app.py)"]
        ChatEndpoint["/api/chat/stream endpoint"]
        GraphBuilder["build_graph_with_memory()"]
        
        subgraph "Agent Nodes (nodes.py)"
            CoordinatorNode["coordinator_node()"]
            PlannerNode["planner_node()"]
            ResearchTeamNode["research_team_node()"]
            ResearcherNode["researcher_node()"]
            CoderNode["coder_node()"]
            ReporterNode["reporter_node()"]
            EnzymeRetrieverNode["enzyme_retriever_node()"]
            HumanSelectNode["human_select_node()"]
            EnzymeDesignerNode["enzyme_designer_node()"]
        end
        
        subgraph "Tools"
            WebSearchTool["web_search_tool"]
            CrawlTool["crawl_tool"]
            PatentSearchTool["patent_search_tool"]
            LitertureSearchTool["literture_search_tool"]
            PythonREPLTool["python_repl_tool"]
            ProteinDesignTools["protein.unsupervise tools"]
            MCPTools["MCP integration"]
        end
    end
    
    WebUI --> Store
    WebUI --> SettingsStore
    Store --> ChatAPI
    ChatAPI --> Server
    Server --> ChatEndpoint
    ChatEndpoint --> GraphBuilder
    GraphBuilder --> CoordinatorNode
    CoordinatorNode --> PlannerNode
    PlannerNode --> ResearchTeamNode
    ResearchTeamNode --> ResearcherNode
    ResearchTeamNode --> CoderNode
    ResearcherNode --> ResearchTeamNode
    CoderNode --> ResearchTeamNode
    ResearchTeamNode --> ReporterNode
    ReporterNode --> EnzymeRetrieverNode
    EnzymeRetrieverNode --> HumanSelectNode
    HumanSelectNode -- "User approves selection" --> EnzymeDesignerNode
    HumanSelectNode -- "User requests more info" --> EnzymeRetrieverNode
    
    ResearcherNode --> WebSearchTool
    ResearcherNode --> CrawlTool
    ResearcherNode --> PatentSearchTool
    ResearcherNode --> LitertureSearchTool
    ResearcherNode --> MCPTools
    CoderNode --> PythonREPLTool
    EnzymeRetrieverNode --> WebSearchTool
    EnzymeRetrieverNode --> CrawlTool
    EnzymeRetrieverNode --> MCPTools
    EnzymeDesignerNode --> ProteinDesignTools
```

The high-level architecture consists of two main components:

1. **Frontend**: A Next.js web application that provides the user interface and manages client-side state.
   - Uses Zustand stores (`useStore` and `useSettingsStore`) for state management
   - Communicates with the backend through the `chatStream()` function

2. **Backend**: A FastAPI server that processes requests and orchestrates the research workflow.
   - Implements the LangGraph workflow for agent coordination
   - Provides REST API endpoints for chat, text-to-speech, and content generation
   - Integrates tools for web search, crawling, and code execution

Sources: [web/src/core/store/store.ts](), [web/src/core/api/chat.ts](), [src/server/app.py](), [src/graph/nodes.py]()