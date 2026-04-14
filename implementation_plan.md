d# Phase 4: Agent Brain Implementation Plan

Based on your feedback, here is the revised implementation plan. The Agent Brain will be implemented as a new module within the Athena Core application, ensuring a single backend service for the upcoming Next.js frontend.

## User Review Required

> [!IMPORTANT]
> Please review the finalized API endpoints and tools. Once approved, I will immediately begin execution to build the LangGraph multi-agent system.

## Proposed Architecture

### 1. LLM Strategy
- **Default Provider:** We will exclusively use the **Groq API** (Llama 3.3 70B or similar available dense model) as per your request. The LangChain integration `ChatGroq` will be used for high-speed agentic reasoning.

### 2. State & Memory Management
- **Checkpointer:** We will use LangGraph's `MemorySaver` (in-memory) or `SqliteSaver` (disk-persisted) to maintain conversational thread history. This ensures the agent remembers context across a multi-turn chat session.

### 3. ATL (Action Tracking Log)
- Every significant decision, risk detection, or Jira mutation proposed by the agent will be logged to an internal Action Tracking Log (a simple SQLite table or in-memory list for this MVP) so the frontend `<ATLViewer />` can display the audit trail.

---

## Proposed Changes

We will create a new Python package `agent_brain/` and mount its routes onto the existing Athena Core FastAPI server.

### 1. LangGraph Core (`agent_brain/`)

#### [NEW] [state.py](file:///home/deepak/Desktop/Athena/agent_brain/state.py)
Defines the `AgentState` using `TypedDict` and the Pydantic schemas for the ATL. State includes: messages array (conversation), `context` (research data), and `pending_action` (for the Human Gate).

#### [NEW] [tools.py](file:///home/deepak/Desktop/Athena/agent_brain/tools.py)
The 15+ Agent Tools. 
- **Read-Only Jira:** Direct wrapper functions calling `requests.get(SIMULATOR_API_URL + ...)`. Because Agent Brain runs within `athena_core`, calling the Simulator directly is the most optimized network path.
- **Modify Jira [NEW]:** Based on feedback, we will add `update_issue_status` and `assign_issue` tools to allow the Executor node to mutate Jira state.
- **Knowledge:** Direct Python function calls to `athena_core.graph_syncer` and `athena_core.vector_indexer`.
- **Utility:** `log_to_atl` tool.

#### [NEW] [nodes.py](file:///home/deepak/Desktop/Athena/agent_brain/nodes.py)
The 6 graph nodes: Planner, Researcher, Alerter, Responder, HumanGate, Executor. 
- The `HumanGate` node will pause execution and return a `pending_action` status.

#### [NEW] [graph.py](file:///home/deepak/Desktop/Athena/agent_brain/graph.py)
Compiles the LangGraph `StateGraph` and attaches the `SqliteSaver` checkpointer.

### 2. API Endpoints for Frontend Dashboard

Per HLD Section 4.6, we must build the remaining 3 endpoints. We will add these to `athena_core/api.py`:

#### [MODIFY] [api.py](file:///home/deepak/Desktop/Athena/athena_core/api.py)
Add the following endpoints for the frontend integration:

1.  `POST /api/v1/query` — **The Chat Interface**
    - Takes `{"query": "string", "thread_id": "string"}`
    - Invokes the LangGraph Agent Brain.
    - Returns the agent's finalized markdown response + citation data.

2.  `GET /api/v1/atl` — **The ATL Viewer**
    - Returns the chronological list of all actions tracked by the system (e.g., "Agent assigned DEV-1 to Alice").

3.  `POST /api/v1/approval/{id}` — **Risk Feed Interactive Approvals**
    - Takes `{"action": "APPROVE" | "REJECT"}`.
    - Resumes the LangGraph from the paused `HumanGate` state to execute Jira modifications.

---

## Verification Plan

### Automated Tests
1.  Verify the Groq LLM binds correctly to the 15 tools via `bind_tools()`.
2.  Test the LangGraph state compilation with `SqliteSaver`.

### End-to-End Manual Verification
1.  Start both Simulator and Athena Core.
2.  Send POST request to `/api/v1/query` with a question requiring Jira retrieval ("What is happening on project X?"). Ensure the agent calls the correct Simulated Jira tool.
3.  Trigger a Chaos Event on the simulator. Ensure the Ingestion Pipeline detects it, passes it to the Agent Brain, which then pauses at the Human Gate.
4.  Test the `/api/v1/approval/{id}` endpoint to un-pause the agent and let it execute its Jira mutation tool.
