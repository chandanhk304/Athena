"""
Agent Brain — Tool Definitions
All tools available to the LangGraph agent nodes.

Tool Categories:
  READ  — Query the Simulator's Jira-like API (read-only)
  WRITE — Mutate Jira state (Assign, Update Status)
  KNOWLEDGE — Query Neo4j graph + Pinecone vectors
  UTILITY — Draft messages, classify severity, log to ATL
"""
import uuid
import requests
from datetime import datetime, timezone
from langchain_core.tools import tool

from athena_core import config
from athena_core import graph_syncer
from athena_core import vector_indexer


# ═══════════════════════════════════════════════════════════════
#  READ TOOLS — Jira Simulator (read-only)
# ═══════════════════════════════════════════════════════════════

@tool
def get_all_projects() -> list[dict]:
    """
    Fetch a summary of all known projects from the Jira Simulator.
    Uses /issues/search with a broad JQL to infer distinct projects via epics.
    Returns a list of project summary dicts.
    """
    # The simulator has no GET /projects list endpoint.
    # We fetch distinct project summaries by querying known project keys.
    # Known keys are seeded by timeline_sim; we fall back to searching all issues.
    url = f"{config.SIMULATOR_API_URL}/issues/search"
    try:
        resp = requests.get(url, params={"jql": "status=OPEN", "analyze_by_component": "true"}, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        # Return component breakdown as a proxy for project overview
        breakdown = data.get("component_breakdown", {})
        return [{"project_component": k, "stats": v} for k, v in breakdown.items()]
    except Exception as e:
        return [{"error": str(e)}]


@tool
def get_project_details(project_key: str) -> dict:
    """Fetch detailed summary of a specific project by its key (e.g. 'CAT')."""
    url = f"{config.SIMULATOR_API_URL}/projects/{project_key}/summary"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}


@tool
def get_project_stories(project_key: str, status: str = None) -> list[dict]:
    """
    Fetch all stories/tickets for a project.
    Optionally filter by status (e.g. 'BLOCKED', 'IN_PROGRESS', 'OPEN', 'CLOSED').
    """
    url = f"{config.SIMULATOR_API_URL}/projects/{project_key}/issues"
    params = {}
    if status:
        params["status"] = status
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get("issues", data) if isinstance(data, dict) else data
    except Exception as e:
        return [{"error": str(e)}]


@tool
def get_story_details(story_key: str) -> dict:
    """Fetch full details of a specific ticket/story by its key (e.g. 'CAT-42')."""
    url = f"{config.SIMULATOR_API_URL}/issues/{story_key}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}



@tool
def get_all_users() -> list[dict]:
    """Fetch all users/team members from the Jira Simulator."""
    url = f"{config.SIMULATOR_API_URL}/users"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return [{"error": str(e)}]


@tool
def get_user_info(user_id: str) -> dict:
    """Fetch profile and assigned issues for a specific user by their ID or username."""
    url = f"{config.SIMULATOR_API_URL}/users/{user_id}/issues"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}


@tool
def get_active_sprints(project_key: str = None) -> list[dict]:
    """Get issues in the current active sprint. Optionally filter by sprint_name."""
    url = f"{config.SIMULATOR_API_URL}/sprints/issues"
    params = {}
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return [response.json()]  # Returns single sprint dict with issues
    except Exception as e:
        return [{"error": str(e)}]


@tool
def get_blocked_tickets(project_key: str = None) -> list[dict]:
    """
    Get all blocked tickets using JQL search.
    If project_key is provided, filter to that project only.
    Useful for risk assessment.
    """
    url = f"{config.SIMULATOR_API_URL}/issues/search"
    jql = "status=BLOCKED"
    if project_key:
        jql += f" project={project_key}"
    try:
        response = requests.get(url, params={"jql": jql}, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get("issues", []) if isinstance(data, dict) else data
    except Exception as e:
        return [{"error": str(e)}]


# ═══════════════════════════════════════════════════════════════
#  WRITE TOOLS — Mutate Jira state (require Human Gate approval)
# ═══════════════════════════════════════════════════════════════

@tool
def update_issue_status(story_key: str, new_status: str) -> dict:
    """
    Update the status of a Jira ticket.
    Valid statuses: OPEN, IN_PROGRESS, BLOCKED, CLOSED.
    REQUIRES human approval before execution.
    story_key must be in format 'CAT-42' (used to look up the story ID).
    """
    # First resolve key → id
    lookup = f"{config.SIMULATOR_API_URL}/issues/{story_key}"
    try:
        resp = requests.get(lookup, timeout=10)
        resp.raise_for_status()
        story_id = resp.json().get("id")
        if not story_id:
            return {"success": False, "error": "Could not resolve story ID from key"}
        url = f"{config.SIMULATOR_API_URL}/stories/{story_id}"
        response = requests.patch(url, json={"status": new_status}, timeout=10)
        response.raise_for_status()
        return {"success": True, "story_key": story_key, "new_status": new_status}
    except Exception as e:
        return {"success": False, "error": str(e)}


@tool
def assign_issue(story_key: str, assignee_id: str) -> dict:
    """
    Assign a Jira ticket to a specific user by their user ID.
    REQUIRES human approval before execution.
    story_key must be in format 'CAT-42'.
    """
    lookup = f"{config.SIMULATOR_API_URL}/issues/{story_key}"
    try:
        resp = requests.get(lookup, timeout=10)
        resp.raise_for_status()
        story_id = resp.json().get("id")
        if not story_id:
            return {"success": False, "error": "Could not resolve story ID from key"}
        url = f"{config.SIMULATOR_API_URL}/stories/{story_id}"
        response = requests.patch(url, json={"assignee_id": assignee_id}, timeout=10)
        response.raise_for_status()
        return {"success": True, "story_key": story_key, "assignee_id": assignee_id}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ═══════════════════════════════════════════════════════════════
#  KNOWLEDGE TOOLS — Neo4j Graph + Pinecone Vectors
# ═══════════════════════════════════════════════════════════════

@tool
def search_graph(cypher_query: str, params: dict = None) -> list[dict]:
    """
    Execute a Cypher query on the Neo4j knowledge graph.
    Use for structured queries: finding relationships, blocked chains, team workloads.
    Example: 'MATCH (t:Task {status: "BLOCKED"})-[:BELONGS_TO]->(e:Epic) RETURN t,e'
    """
    try:
        return graph_syncer.search_graph(cypher_query, params or {})
    except Exception as e:
        return [{"error": str(e)}]


@tool
def search_docs(query_text: str, k: int = 5, filter_by_type: str = None) -> list[dict]:
    """
    Semantic similarity search on Pinecone vectors.
    Use for natural language searches: 'infrastructure delays', 'authentication issues'.
    filter_by_type: optionally restrict to 'story', 'comment', or 'epic'.
    """
    filter_dict = {"entity_type": filter_by_type} if filter_by_type else None
    try:
        return vector_indexer.search_docs(query_text, k=k, filter_dict=filter_dict)
    except Exception as e:
        return [{"error": str(e)}]


@tool
def get_risk_chain(task_id: str) -> list[dict]:
    """
    Graph traversal: given a blocked task ID, find all downstream epics and milestones at risk.
    Returns the chain of impacted entities.
    """
    cypher = """
        MATCH (t:Task {id: $task_id})-[:HAS_RISK]->(r:Risk)
        OPTIONAL MATCH (t)-[:BELONGS_TO]->(e:Epic)
        OPTIONAL MATCH (e)-[:PART_OF]->(p:Project)
        RETURN t.key AS task, t.status AS status, 
               r.type AS risk_type, r.severity AS severity,
               e.title AS epic, p.name AS project
    """
    try:
        return graph_syncer.search_graph(cypher, {"task_id": task_id})
    except Exception as e:
        return [{"error": str(e)}]


# ═══════════════════════════════════════════════════════════════
#  UTILITY TOOLS
# ═══════════════════════════════════════════════════════════════

@tool
def classify_severity(description: str, context: str) -> str:
    """
    Classify the severity of a risk or issue as: CRITICAL, HIGH, MEDIUM, or LOW.
    Based on the description and surrounding context.
    Returns a single severity string.
    """
    desc_lower = description.lower()
    if any(w in desc_lower for w in ["critical", "blocked", "milestone", "deadline", "escalat"]):
        return "CRITICAL"
    if any(w in desc_lower for w in ["overdue", "delayed", "risk", "high priority"]):
        return "HIGH"
    if any(w in desc_lower for w in ["slow", "concern", "watch", "monitor"]):
        return "MEDIUM"
    return "LOW"


@tool
def draft_alert_message(
    risk_type: str,
    entity_key: str,
    severity: str,
    description: str,
    recommended_action: str
) -> str:
    """
    Draft a formatted stakeholder alert message with citation.
    Returns a markdown-formatted alert string ready for the PMO dashboard.
    """
    severity_emoji = {
        "CRITICAL": "🔴",
        "HIGH": "🟠",
        "MEDIUM": "🟡",
        "LOW": "🟢"
    }.get(severity, "⚪")

    message = f"""## {severity_emoji} {severity} Risk Alert — {entity_key}

**Risk Type:** {risk_type}  
**Ticket:** `{entity_key}`  
**Severity:** {severity}

**Issue:**  
{description}

**Recommended Action:**  
{recommended_action}

---
*Alert generated by Athena at {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}*  
*Source: Neo4j Knowledge Graph + Pinecone Vector Index*
"""
    return message


@tool
def log_to_atl(
    action_type: str,
    description: str,
    entity_id: str = None,
    entity_key: str = None,
    severity: str = None,
    status: str = "LOGGED",
    metadata: dict = None
) -> dict:
    """
    Log a significant agent action to the Action Tracking Log.
    Returns the ATL entry dict with a generated ID.
    """
    entry = {
        "id": f"ATL-{uuid.uuid4().hex[:8].upper()}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action_type": action_type,
        "description": description,
        "entity_id": entity_id,
        "entity_key": entity_key,
        "severity": severity,
        "status": status,
        "metadata": metadata or {}
    }
    return entry


# ═══════════════════════════════════════════════════════════════
#  TOOL REGISTRY — exported for use in nodes.py / graph.py
# ═══════════════════════════════════════════════════════════════

# Read-only tools (safe to auto-execute)
READ_TOOLS = [
    get_all_projects,
    get_project_details,
    get_project_stories,
    get_story_details,
    get_all_users,
    get_user_info,
    get_active_sprints,
    get_blocked_tickets,
]

# Knowledge tools (safe to auto-execute)
KNOWLEDGE_TOOLS = [
    search_graph,
    search_docs,
    get_risk_chain,
]

# Utility tools (safe to auto-execute)
UTILITY_TOOLS = [
    classify_severity,
    draft_alert_message,
    log_to_atl,
]

# Write tools (REQUIRE human approval)
WRITE_TOOLS = [
    update_issue_status,
    assign_issue,
]

# All tools combined (bound to the LLM)
ALL_TOOLS = READ_TOOLS + KNOWLEDGE_TOOLS + UTILITY_TOOLS + WRITE_TOOLS
