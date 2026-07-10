from langgraph.graph import StateGraph, START, END

from app.agent.state import AgentState
from app.agent.nodes import (
    greeting_node,
    collect_name_node,
    collect_intent_node,
    collect_date_node,
    check_slots_node,
    collect_slot_node,
    collect_email_node,
    book_slot_node,
    confirmation_node,
)
from app.agent.memory import memory


def route_by_step(state: AgentState) -> str:
    step = state.get("current_step")
    if not step or step == "completed":
        return "greeting"
    valid_steps = ["greeting", "collect_name", "collect_intent", "collect_date", "collect_slot", "collect_email"]
    if step not in valid_steps:
        return "greeting"
    return step


def route_after_date(state: AgentState) -> str:
    if state.get("selected_date"):
        return "check_slots"
    return END


def route_after_email(state: AgentState) -> str:
    if state.get("email"):
        return "book_slot"
    return END


# ── Build the graph ───────────────────────────────────────────────────────────
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("greeting", greeting_node)
workflow.add_node("collect_name", collect_name_node)
workflow.add_node("collect_intent", collect_intent_node)
workflow.add_node("collect_date", collect_date_node)
workflow.add_node("check_slots", check_slots_node)
workflow.add_node("collect_slot", collect_slot_node)
workflow.add_node("collect_email", collect_email_node)
workflow.add_node("book_slot", book_slot_node)
workflow.add_node("confirmation", confirmation_node)

# Entry point — route dynamically based on current_step
workflow.add_conditional_edges(
    START,
    route_by_step,
    {
        "greeting": "greeting",
        "collect_name": "collect_name",
        "collect_intent": "collect_intent",
        "collect_date": "collect_date",
        "collect_slot": "collect_slot",
        "collect_email": "collect_email",
    }
)

# Define transitions
workflow.add_edge("greeting", END)
workflow.add_edge("collect_name", END)
workflow.add_edge("collect_intent", END)

workflow.add_conditional_edges(
    "collect_date",
    route_after_date,
    {
        "check_slots": "check_slots",
        END: END
    }
)
workflow.add_edge("check_slots", END)
workflow.add_edge("collect_slot", END)

workflow.add_conditional_edges(
    "collect_email",
    route_after_email,
    {
        "book_slot": "book_slot",
        END: END
    }
)
workflow.add_edge("book_slot", "confirmation")
workflow.add_edge("confirmation", END)

# ── Compile with Redis checkpointer ──────────────────────────────────────────
graph = workflow.compile(checkpointer=memory)
