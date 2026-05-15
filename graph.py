from langgraph.graph import StateGraph, END
from utils.state import HireIQState

from main import (
    greet_node,
    route_node,
    job_collect_cv_node,
    job_collect_role_node,
    job_collect_email_node,
    interview_node,
    visitor_node,
    rag_node
)

# ─────────────────────────────
# ROUTING LOGIC
# ─────────────────────────────
def route_decision(state: HireIQState):
    return state.get("person_type", "client")


def build_graph():

    graph = StateGraph(HireIQState)

    # ───────── Nodes ─────────
    graph.add_node("greet", greet_node)
    graph.add_node("route", route_node)

    graph.add_node("job_cv", job_collect_cv_node)
    graph.add_node("job_role", job_collect_role_node)
    graph.add_node("job_email", job_collect_email_node)
    graph.add_node("interview", interview_node)

    graph.add_node("visitor", visitor_node)
    graph.add_node("rag", rag_node)

    # ───────── Entry ─────────
    graph.set_entry_point("route")

    # ───────── ROUTING ─────────
    graph.add_conditional_edges(
        "route",
        route_decision,
        {
            "employee": "job_cv",
            "visitor": "visitor",
            "client": "rag",
        }
    )

    # ───────── JOB FLOW ─────────
    graph.add_edge("job_cv", "job_role")
    graph.add_edge("job_role", "job_email")
    graph.add_edge("job_email", "interview")
    graph.add_edge("interview", END)

    # ───────── OTHERS ─────────
    graph.add_edge("visitor", END)
    graph.add_edge("rag", END)

    return graph.compile()