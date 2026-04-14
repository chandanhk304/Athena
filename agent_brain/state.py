"""
Agent Brain — State Definitions
Defines AgentState (the shared memory that flows through every node)
and ATL (Action Tracking Log) Pydantic schemas.

AgentState fields:
  - messages:       Full conversation history (LangChain BaseMessage list)
  - input_type:     Classified route — "query", "risk_event", "general"
  - context:        Research data gathered by Researcher node (string)
  - pending_action: Dict describing an action awaiting human approval
  - atl_entries:    In-memory list of Action Tracking Log records
  - final_response: The formatted markdown response to return to the user
"""
from __future__ import annotations

from typing import Annotated, Any, Optional
from typing_extensions import TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field
from datetime import datetime, timezone


# ═══════════════════════════════════════════════════════════════
#  ATL SCHEMAS  (Action Tracking Log)
# ═══════════════════════════════════════════════════════════════

class ATLEntry(BaseModel):
    """A single entry in the Action Tracking Log."""
    id: str = Field(description="Unique ATL entry ID")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    action_type: str = Field(description="e.g. RISK_DETECTED, ALERT_DRAFTED, TICKET_ASSIGNED")
    description: str = Field(description="Human-readable description of what happened")
    entity_id: Optional[str] = Field(default=None, description="Jira ticket ID if relevant")
    entity_key: Optional[str] = Field(default=None, description="Jira ticket key e.g. DEV-42")
    severity: Optional[str] = Field(default=None, description="CRITICAL / HIGH / MEDIUM / LOW")
    status: str = Field(default="LOGGED", description="LOGGED | PENDING_APPROVAL | APPROVED | REJECTED | EXECUTED")
    metadata: dict[str, Any] = Field(default_factory=dict)


class PendingAction(BaseModel):
    """An action that has been paused at the Human Gate awaiting approval."""
    atl_id: str = Field(description="ID of the ATL entry this action is associated with")
    action_type: str = Field(description="e.g. ASSIGN_TICKET, UPDATE_STATUS")
    description: str
    tool_name: str = Field(description="The agent tool to call upon approval")
    tool_args: dict[str, Any] = Field(default_factory=dict)
    severity: Optional[str] = None


# ═══════════════════════════════════════════════════════════════
#  AGENT STATE
# ═══════════════════════════════════════════════════════════════

class AgentState(TypedDict):
    """
    The shared state object that flows through the entire LangGraph.
    Each node reads and writes to this state.
    """
    # Conversation history — LangGraph handles merging via add_messages
    messages: Annotated[list[BaseMessage], add_messages]

    # Input classification — set by SemanticRouter
    input_type: str  # "query" | "risk_event" | "general"

    # Research context — set by Researcher, consumed by Responder/Alerter
    context: str

    # Pending action waiting at the Human Gate (None if not applicable)
    pending_action: Optional[dict[str, Any]]

    # In-memory ATL entries accumulated during this session
    atl_entries: list[dict[str, Any]]

    # Final formatted response to return to the user
    final_response: str

    # Thread / session ID for checkpointer memory
    thread_id: str
