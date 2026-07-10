"""
LangGraph agent state definition.
Defines the shape of data that flows through every node in the graph.
"""

from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """
    State that travels through the LangGraph workflow.

    Fields:
        messages       — Full conversation history (auto-appended by add_messages).
        patient_name   — Name collected from the patient.
        email          — Email collected from the patient.
        selected_date  — Date the patient wants to visit.
        selected_slot  — Time slot chosen by the patient.
        appointment_id — ID returned after a successful booking.
    """

    messages: Annotated[list, add_messages]
    patient_name: str
    email: str
    selected_date: str
    selected_slot: str
    appointment_id: str
    current_step: str
    available_slots: list[dict]
    requested_time: str


