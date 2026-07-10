"""
Pydantic schemas for API endpoints.
"""

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Payload sent by the client to chat with the AI assistant."""
    session_id: str = Field(..., examples=[""])
    message: str = Field(..., min_length=1, examples=[""])


class ChatResponse(BaseModel):
    """Payload returned by the /chat endpoint containing only the AI reply."""
    reply: str


class SaveConversationRequest(BaseModel):
    """Payload sent to save conversation history to PostgreSQL."""
    session_id: str = Field(..., examples=[""])
