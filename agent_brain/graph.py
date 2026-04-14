"""
Agent Brain — LangGraph Compilation
Assembles all nodes into a compiled StateGraph with SqliteSaver checkpointer.

Graph topology (matches DFD diagram):
  START → SemanticRouter → Planner → [Researcher|Responder] → [Alerter|Responder]
        → HumanGate → [Executor|LogOnly|END] → END

The Human Gate uses interrupt_before=['executor'] to pause for approval.
Resuming is done by calling graph.invoke() with the same thread_id.
"""
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from .state import AgentState
from .nodes import (
    semantic_router,
    planner,
    researcher,
    alerter,
    responder,
    human_gate,
    executor,
    log_only,
    route_after_planner,
    route_after_researcher,
    route_after_human_gate,
)

# ─── Checkpointer (in-memory for MVP) ───────────────────────
# Persists conversation history across multi-turn sessions per thread_id.
# Replace with SqliteSaver for disk persistence in production.
_checkpointer = MemorySaver()

# ─── Cached compiled graph ───────────────────────────────────
_compiled_graph = None


def _build_graph() -> StateGraph:
    """Build and return the compiled LangGraph StateGraph."""
    builder = StateGraph(AgentState)

    # ── Add all nodes ─────────────────────────────────────────
    builder.add_node("semantic_router", semantic_router)
    builder.add_node("planner",         planner)
    builder.add_node("researcher",      researcher)
    builder.add_node("alerter",         alerter)
    builder.add_node("responder",       responder)
    builder.add_node("human_gate",      human_gate)
    builder.add_node("executor",        executor)
    builder.add_node("log_only",        log_only)

    # ── Entry Point ───────────────────────────────────────────
    builder.set_entry_point("semantic_router")

    # ── Fixed edges ───────────────────────────────────────────
    builder.add_edge("semantic_router", "planner")
    builder.add_edge("alerter",         "human_gate")
    builder.add_edge("responder",       "human_gate")
    builder.add_edge("executor",        END)
    builder.add_edge("log_only",        END)

    # ── Conditional edges ─────────────────────────────────────
    # After Planner: route to Researcher (query/risk) or Responder (general)
    builder.add_conditional_edges(
        "planner",
        route_after_planner,
        {
            "researcher": "researcher",
            "responder":  "responder",
        }
    )

    # After Researcher: route to Alerter (risk) or Responder (query)
    builder.add_conditional_edges(
        "researcher",
        route_after_researcher,
        {
            "alerter":   "alerter",
            "responder": "responder",
        }
    )

    # After Human Gate: route to Executor (approved), LogOnly (rejected), or END (auto-pass)
    builder.add_conditional_edges(
        "human_gate",
        route_after_human_gate,
        {
            "executor":  "executor",
            "__end__":   END,
        }
    )

    return builder


def compile() -> object:
    """
    Compile the LangGraph with checkpointer and interrupt_before the executor.
    The interrupt allows the Human Gate to pause and wait for approval.

    Returns the compiled runnable graph.
    """
    global _compiled_graph
    if _compiled_graph is None:
        builder = _build_graph()

        # interrupt_before=['executor'] means the graph automatically pauses
        # right before executing any write actions, waiting for human approval.
        _compiled_graph = builder.compile(
            checkpointer=_checkpointer,
            interrupt_before=["executor"]
        )
        print("[AgentBrain] LangGraph compiled successfully.")
    return _compiled_graph


def get_graph() -> object:
    """Get the compiled graph (lazy-init)."""
    return compile()
