"""
Agent Brain — Node Definitions
Each function here is a LangGraph node. Nodes read from AgentState,
perform their work, and return a dict of state updates.

Node Flow (per diagram):
  SemanticRouter → Planner[QUERY/RISK/GEN] → Researcher / Alerter → Responder → HumanGate → Executor / LogOnly
"""
import json
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_groq import ChatGroq

from athena_core import config
from .state import AgentState
from .tools import (
    ALL_TOOLS, READ_TOOLS, KNOWLEDGE_TOOLS, UTILITY_TOOLS,
    log_to_atl, draft_alert_message, classify_severity, get_risk_chain,
    search_graph, search_docs, get_blocked_tickets,
    update_issue_status, assign_issue
)

# ─── LLM Initialisation (Groq — Llama 3.3 70B) ──────────────
_llm = None

def get_llm():
    """Lazy-init Groq LLM with all tools bound."""
    global _llm
    if _llm is None:
        _llm = ChatGroq(
            api_key=config.GROQ_API_KEY,
            model_name="llama-3.3-70b-versatile",
            temperature=0.1,          # Low temp for factual, deterministic reasoning
            max_tokens=2048,
        ).bind_tools(ALL_TOOLS)
    return _llm

def get_llm_plain():
    """Plain LLM without tools (for response formatting nodes)."""
    return ChatGroq(
        api_key=config.GROQ_API_KEY,
        model_name="llama-3.3-70b-versatile",
        temperature=0.2,
        max_tokens=2048,
    )


# ═══════════════════════════════════════════════════════════════
#  NODE 0: SEMANTIC ROUTER
#  Classifies the incoming input into a route type.
# ═══════════════════════════════════════════════════════════════

ROUTER_SYSTEM_PROMPT = """You are a routing classifier for an AI Program Management assistant called Athena.
Classify the user input into exactly ONE of these categories:

- "query"      → User is asking a specific question about project data (tickets, teams, status, blockers, sprints)
- "risk_event" → This is an automated risk alert or notification about a blocked ticket, milestone slip, or escalation
- "general"    → General conversation, greetings, help requests, or meta questions about Athena itself

Respond with ONLY the category word. No explanation."""

def semantic_router(state: AgentState) -> dict:
    """
    Node 0: Classify the incoming input to determine the processing path.
    Sets state['input_type'] to 'query', 'risk_event', or 'general'.
    """
    # Get the latest human message
    last_message = ""
    for msg in reversed(state["messages"]):
        if isinstance(msg, HumanMessage):
            last_message = msg.content
            break

    llm = get_llm_plain()
    response = llm.invoke([
        SystemMessage(content=ROUTER_SYSTEM_PROMPT),
        HumanMessage(content=last_message)
    ])

    raw = response.content.strip().lower()

    # Normalize to one of the valid route types
    if "risk" in raw:
        route = "risk_event"
    elif "query" in raw or "question" in raw:
        route = "query"
    else:
        route = "general"

    print(f"[SemanticRouter] Input classified as: '{route}'")
    return {"input_type": route}


# ═══════════════════════════════════════════════════════════════
#  NODE 1: PLANNER
#  Creates an execution plan based on the input type.
# ═══════════════════════════════════════════════════════════════

PLANNER_PROMPTS = {
    "query": """You are the Planner for Athena, an AI PMO assistant.
The user has a specific question about project data. Create a concise research plan.
Identify what Jira data and graph/vector information needs to be fetched.
State your plan clearly in 2-3 bullet points. Be specific about what tools are needed.""",

    "risk_event": """You are the Planner for Athena handling a RISK EVENT.
A risk has been detected. Your job is to plan a thorough impact assessment:
1. What graph queries will reveal the impact chain?
2. What tickets are blocked and who is affected?
3. What action should be recommended?
State your plan in 2-3 bullet points.""",

    "general": """You are the Planner for Athena, an AI PMO assistant.
The user has a general question or greeting. Keep the plan simple:
- This is a conversational response. No deep data retrieval needed.
- Prepare to respond helpfully about what Athena can do.""",
}

def planner(state: AgentState) -> dict:
    """
    Node 1: Create a research/execution plan based on the classified input type.
    Appends the plan as an AIMessage to the conversation.
    """
    input_type = state.get("input_type", "general")
    system_prompt = PLANNER_PROMPTS.get(input_type, PLANNER_PROMPTS["general"])

    llm = get_llm_plain()
    response = llm.invoke(
        [SystemMessage(content=system_prompt)] + list(state["messages"])
    )

    plan_text = f"[Planner:{input_type.upper()}] {response.content}"
    print(f"[Planner] Type={input_type} | Plan created.")
    return {"messages": [AIMessage(content=plan_text)]}


# ═══════════════════════════════════════════════════════════════
#  NODE 2: RESEARCHER
#  Calls tools to gather data from Jira + Neo4j + Pinecone.
# ═══════════════════════════════════════════════════════════════

RESEARCHER_SYSTEM_PROMPT = """You are the Researcher agent for Athena PMO.
Your job is to gather comprehensive data to answer the user's question.

You have access to these tools:
- Jira read tools: get_all_projects, get_project_stories, get_story_details, get_all_users, get_user_info, get_active_sprints, get_blocked_tickets
- Knowledge tools: search_graph (Cypher queries), search_docs (semantic search), get_risk_chain (impact analysis)

Call the relevant tools to gather the data needed. Be thorough but efficient.
After gathering data, synthesize a clear context summary."""

def researcher(state: AgentState) -> dict:
    """
    Node 2: Researcher — calls tools to fetch data and builds a context string.
    Used for both QUERY and RISK routes.
    """
    llm = get_llm()
    messages = [SystemMessage(content=RESEARCHER_SYSTEM_PROMPT)] + list(state["messages"])

    # Agentic loop: keep calling tools until the LLM stops requesting them
    tool_map = {t.name: t for t in READ_TOOLS + KNOWLEDGE_TOOLS}
    context_parts = []

    for _ in range(5):  # Max 5 tool call rounds
        response = llm.invoke(messages)
        messages.append(response)

        if not response.tool_calls:
            # LLM has finished gathering data — extract context
            context_parts.append(response.content)
            break

        # Execute tool calls
        for tc in response.tool_calls:
            tool_fn = tool_map.get(tc["name"])
            if tool_fn:
                try:
                    result = tool_fn.invoke(tc["args"])
                    result_str = json.dumps(result, default=str)[:3000]  # Truncate large results
                except Exception as e:
                    result_str = f"Tool error: {e}"

                from langchain_core.messages import ToolMessage
                messages.append(ToolMessage(
                    content=result_str,
                    tool_call_id=tc["id"],
                    name=tc["name"]
                ))
                context_parts.append(f"[{tc['name']}]: {result_str[:500]}")

    context = "\n\n".join(context_parts)
    print(f"[Researcher] Context gathered: {len(context)} chars.")
    return {
        "context": context,
        "messages": [AIMessage(content=f"[Researcher] Data gathered successfully. Context length: {len(context)} chars.")]
    }


# ═══════════════════════════════════════════════════════════════
#  NODE 3: ALERTER
#  Drafts a risk alert with severity classification.
# ═══════════════════════════════════════════════════════════════

ALERTER_SYSTEM_PROMPT = """You are the Alerter agent for Athena PMO.
You have detected a risk event. Using the context provided, you must:
1. Classify the severity using classify_severity tool
2. Draft a clear stakeholder alert using draft_alert_message tool
3. Log the risk to ATL using log_to_atl tool

Be precise and cite specific ticket keys. Always recommend a specific action."""

def alerter(state: AgentState) -> dict:
    """
    Node 3: Alerter — classifies severity, drafts the alert message, logs to ATL.
    Used for risk_event routes.
    """
    llm_with_tools = ChatGroq(
        api_key=config.GROQ_API_KEY,
        model_name="llama-3.3-70b-versatile",
        temperature=0.1,
        max_tokens=1024,
    ).bind_tools([classify_severity, draft_alert_message, log_to_atl])

    context = state.get("context", "No context available.")
    messages = [
        SystemMessage(content=ALERTER_SYSTEM_PROMPT),
        HumanMessage(content=f"Risk context:\n{context}\n\nDraft an alert and log it to the ATL.")
    ]

    tool_map = {t.name: t for t in [classify_severity, draft_alert_message, log_to_atl]}
    atl_entries = list(state.get("atl_entries", []))
    alert_draft = ""

    for _ in range(4):
        response = llm_with_tools.invoke(messages)
        messages.append(response)

        if not response.tool_calls:
            alert_draft = response.content
            break

        for tc in response.tool_calls:
            tool_fn = tool_map.get(tc["name"])
            if tool_fn:
                try:
                    result = tool_fn.invoke(tc["args"])
                    result_str = json.dumps(result, default=str)

                    # Capture ATL entries and alert draft
                    if tc["name"] == "log_to_atl" and isinstance(result, dict):
                        atl_entries.append(result)
                    if tc["name"] == "draft_alert_message":
                        alert_draft = result if isinstance(result, str) else result_str

                except Exception as e:
                    result_str = f"Tool error: {e}"
                    result = result_str

                from langchain_core.messages import ToolMessage
                messages.append(ToolMessage(
                    content=json.dumps(result, default=str),
                    tool_call_id=tc["id"],
                    name=tc["name"]
                ))

    print(f"[Alerter] Alert drafted. ATL entries: {len(atl_entries)}")
    return {
        "final_response": alert_draft,
        "atl_entries": atl_entries,
        "messages": [AIMessage(content=f"[Alerter] Risk alert drafted with {len(atl_entries)} ATL entries.")]
    }


# ═══════════════════════════════════════════════════════════════
#  NODE 4: RESPONDER
#  Formats the final response with citations and markdown.
# ═══════════════════════════════════════════════════════════════

RESPONDER_SYSTEM_PROMPT = """You are the Responder for Athena PMO — an AI assistant for Program Managers.
Using the context gathered by the Researcher, provide a clear, well-structured answer.

Rules:
- Use markdown formatting (headers, bullet points, tables where appropriate)
- Always cite specific ticket keys (e.g., DEV-42) when referencing data
- Be concise but complete
- If data was not found, say so clearly — do NOT hallucinate
- End with a brief "Data Sources" section listing where information came from"""

def responder(state: AgentState) -> dict:
    """
    Node 4: Responder — formats the final markdown response using gathered context.
    Used for query and general routes.
    """
    context = state.get("context", "")
    llm = get_llm_plain()

    # Get original user question
    user_question = ""
    for msg in state["messages"]:
        if isinstance(msg, HumanMessage):
            user_question = msg.content

    response = llm.invoke([
        SystemMessage(content=RESPONDER_SYSTEM_PROMPT),
        HumanMessage(content=f"User question: {user_question}\n\nResearch context:\n{context}\n\nProvide the final response.")
    ])

    print(f"[Responder] Response formatted: {len(response.content)} chars.")
    return {
        "final_response": response.content,
        "messages": [AIMessage(content=response.content)]
    }


# ═══════════════════════════════════════════════════════════════
#  NODE 5: HUMAN GATE
#  Pauses graph for RISK/ACTION routes. Auto-passes QUERY routes.
# ═══════════════════════════════════════════════════════════════

def human_gate(state: AgentState) -> dict:
    """
    Node 5: Human Gate — checks if the current action requires human approval.
    - For query/general routes: auto-passes (no pending_action set).
    - For risk routes with write actions: sets pending_action and pauses.
    The graph uses a conditional edge to route to Executor or LogOnly.
    """
    input_type = state.get("input_type", "general")

    # Queries auto-pass the gate
    if input_type == "query" or input_type == "general":
        print("[HumanGate] Auto-pass for non-risk route.")
        return {"pending_action": None}

    # Risk events: check if there's a pending write action
    atl_entries = state.get("atl_entries", [])
    pending = None
    for entry in atl_entries:
        if entry.get("status") == "PENDING_APPROVAL":
            pending = entry
            break

    if pending:
        print(f"[HumanGate] ⏸️  PAUSED — pending approval for: {pending.get('action_type')}")
    else:
        print("[HumanGate] No pending write actions — auto-pass.")

    return {"pending_action": pending}


# ═══════════════════════════════════════════════════════════════
#  NODE 6: EXECUTOR
#  Executes the approved write action (assign, update status, etc.)
# ═══════════════════════════════════════════════════════════════

def executor(state: AgentState) -> dict:
    """
    Node 6: Executor — runs the approved write tool and logs the result to ATL.
    Only reached after human approval via /api/v1/approval/{id}.
    """
    pending = state.get("pending_action")
    atl_entries = list(state.get("atl_entries", []))

    if not pending:
        return {"messages": [AIMessage(content="[Executor] No pending action to execute.")]}

    tool_name = pending.get("tool_name")
    tool_args = pending.get("tool_args", {})

    write_tool_map = {
        "update_issue_status": update_issue_status,
        "assign_issue": assign_issue,
    }

    result_msg = ""
    tool_fn = write_tool_map.get(tool_name)

    if tool_fn:
        try:
            result = tool_fn.invoke(tool_args)
            result_msg = f"✅ Executed {tool_name}: {json.dumps(result, default=str)}"

            # Log execution to ATL
            atl_entry = log_to_atl.invoke({
                "action_type": f"EXECUTED_{tool_name.upper()}",
                "description": f"Human approved. Executed: {tool_name} with args {tool_args}",
                "entity_key": tool_args.get("story_key"),
                "status": "EXECUTED",
                "metadata": {"result": result}
            })
            atl_entries.append(atl_entry)

        except Exception as e:
            result_msg = f"❌ Execution failed: {e}"
    else:
        result_msg = f"[Executor] Unknown tool: {tool_name}"

    print(f"[Executor] {result_msg}")
    return {
        "pending_action": None,
        "atl_entries": atl_entries,
        "messages": [AIMessage(content=result_msg)]
    }


# ═══════════════════════════════════════════════════════════════
#  NODE 7: LOG ONLY
#  Called when human rejects an action — logs rejection to ATL.
# ═══════════════════════════════════════════════════════════════

def log_only(state: AgentState) -> dict:
    """
    Node 7: LogOnly — called when a human rejects a proposed action.
    Logs the rejection to ATL and returns a confirmation.
    """
    pending = state.get("pending_action")
    atl_entries = list(state.get("atl_entries", []))

    if pending:
        atl_entry = log_to_atl.invoke({
            "action_type": "ACTION_REJECTED",
            "description": f"Human rejected: {pending.get('description', 'Unknown action')}",
            "entity_key": pending.get("entity_key"),
            "status": "REJECTED",
        })
        atl_entries.append(atl_entry)

    return {
        "pending_action": None,
        "atl_entries": atl_entries,
        "messages": [AIMessage(content="[LogOnly] Action rejected by human. Logged to ATL.")]
    }


# ═══════════════════════════════════════════════════════════════
#  CONDITIONAL EDGE FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def route_after_router(state: AgentState) -> str:
    """Routes to 'planner' after Semantic Router classification."""
    return "planner"


def route_after_planner(state: AgentState) -> str:
    """Routes Planner output to correct next node based on input_type."""
    input_type = state.get("input_type", "general")
    if input_type == "query":
        return "researcher"
    elif input_type == "risk_event":
        return "researcher"  # Researcher → Alerter (chained)
    else:
        return "responder"


def route_after_researcher(state: AgentState) -> str:
    """Routes Researcher output — risk goes to Alerter, query goes to Responder."""
    input_type = state.get("input_type", "general")
    if input_type == "risk_event":
        return "alerter"
    return "responder"


def route_after_human_gate(state: AgentState) -> str:
    """
    The critical routing decision:
    - If pending_action exists → PAUSED (return 'paused' — graph suspends)
    - If no pending_action → Auto-pass to END
    This is handled at graph compile time with interrupt_before.
    """
    pending = state.get("pending_action")
    if pending:
        return "executor"   # Will only reach here after approval resumes graph
    return "__end__"
