"""
SomaAgent — LangGraph Orchestrator
Defines the autonomous agent pipeline as a directed state graph.

Flow: perception → reasoning → log → publish → END
"""
from langgraph.graph import StateGraph, END

from agent.state import AgentState
from agent.nodes.perception import perception_node
from agent.nodes.reasoning import reasoning_node
from agent.nodes.log_node import log_node
from agent.nodes.publish import publish_node


def _route_after_perception(state: AgentState) -> str:
    """Route: if perception failed, go to end. Otherwise reason."""
    if state.get("status") == "error":
        return "end"
    return "reasoning"


def _route_after_reasoning(state: AgentState) -> str:
    """Route: if reasoning failed, still try to log (partial data is useful)."""
    if state.get("status") == "error":
        return "end"
    return "log"


def _route_after_log(state: AgentState) -> str:
    """Route: always try to publish after logging."""
    if state.get("status") == "error":
        return "end"
    return "publish"


def build_graph() -> StateGraph:
    """
    Build and compile the SomaAgent LangGraph.

    Returns a compiled graph ready to invoke.
    """
    graph = StateGraph(AgentState)

    # ─── Register Nodes ───────────────────────────────────────────────────────
    graph.add_node("perception", perception_node)
    graph.add_node("reasoning",  reasoning_node)
    graph.add_node("log",        log_node)
    graph.add_node("publish",    publish_node)

    # ─── Entry Point ──────────────────────────────────────────────────────────
    graph.set_entry_point("perception")

    # ─── Conditional Edges (smart routing) ───────────────────────────────────
    graph.add_conditional_edges(
        "perception",
        _route_after_perception,
        {"reasoning": "reasoning", "end": END}
    )

    graph.add_conditional_edges(
        "reasoning",
        _route_after_reasoning,
        {"log": "log", "end": END}
    )

    graph.add_conditional_edges(
        "log",
        _route_after_log,
        {"publish": "publish", "end": END}
    )

    graph.add_edge("publish", END)
        """
        SomaAgent — LangGraph Orchestrator
        """

# ─── Convenience function ─────────────────────────────────────────────────────

def run_agent(initial_state: dict = None) -> AgentState:
    """Run the full SomaAgent pipeline."""
    app = build_graph()

    state = AgentState(
        raw_landmarks=None,
        laban_scores=None,
        dominant_movement=None,
        movement_confidence=None,
        reasoning_chain=None,
        artistic_interpretation=None,
        nft_title=None,
        nft_description=None,
        visual_keywords=None,
        emotion_tag=None,
        session_id=None,
        log_entries=None,
        log_hash=None,
        prev_log_hash=None,
        ipfs_cid=None,
        ipfs_url=None,
        tx_hash=None,
        error=None,
        status="running",
        next_action="perception"
    )

    if initial_state:
        state.update(initial_state)

    final_state = app.invoke(state)
    return final_state
