"""
FastAPI route definitions.
"""

from fastapi import APIRouter, HTTPException
from langchain_core.messages import HumanMessage, AIMessage

from app.api.schemas import ChatRequest, ChatResponse, SaveConversationRequest
from app.database.database import SessionLocal
from app.services.conversation import save_conversation, delete_conversation
from app.agent.graph import graph

router = APIRouter()


@router.post("/chat", response_model=ChatResponse, tags=["Chat"])
def chat(request: ChatRequest):
    """
    Send a message to the clinic booking assistant and get the response.
    Redis stores the state, and LangGraph coordinates the workflow.
    No PostgreSQL save occurs here.
    """
    config = {"configurable": {"thread_id": request.session_id}}

    try:
        # Run LangGraph state machine
        result = graph.invoke(
            {"messages": [HumanMessage(content=request.message)]},
            config=config,
        )
        ai_reply: str = result["messages"][-1].content
        return ChatResponse(reply=ai_reply)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/save-conversation", tags=["History"])
def save_conversation_endpoint(request: SaveConversationRequest):
    """
    Load the conversation thread from Redis, parse human-AI turns,
    and save them into PostgreSQL.
    """
    config = {"configurable": {"thread_id": request.session_id}}

    try:
        # Retrieve the current state from Redis Checkpointer
        state = graph.get_state(config)
        messages = state.values.get("messages", [])

        # Parse messages into (human, ai) pairs
        turns = []
        human_msg = None
        for msg in messages:
            if isinstance(msg, HumanMessage) or getattr(msg, "type", None) == "human":
                human_msg = msg.content
            elif isinstance(msg, AIMessage) or getattr(msg, "type", None) == "ai":
                if human_msg is not None:
                    turns.append((human_msg, msg.content))
                    human_msg = None

        # Write to PostgreSQL
        db = SessionLocal()
        try:
            # Delete old entries to prevent duplicates and keep history accurate
            delete_conversation(db, request.session_id)
            # Save the new set of parsed turns
            for human, ai in turns:
                save_conversation(db, request.session_id, human, ai)
        finally:
            db.close()

        return {"status": "success", "message": f"Saved {len(turns)} turns to PostgreSQL."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
