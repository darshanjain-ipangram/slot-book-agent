"""
Conversation service — handles all database operations for the
'conversation' table.
"""

from sqlalchemy.orm import Session

from app.database.models import Conversation


def save_conversation(
    db: Session,
    session_id: str,
    human_message: str,
    ai_message: str,
) -> Conversation:
    """
    Persist a human ↔ AI message pair to the database.

    Args:
        db:            Active SQLAlchemy session.
        session_id:    Unique identifier for the chat session.
        human_message: The user's input.
        ai_message:    The AI's response.

    Returns:
        The newly created Conversation record.
    """
    record = Conversation(
        session_id=session_id,
        human_message=human_message,
        ai_message=ai_message,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_conversation_history(db: Session, session_id: str) -> list[Conversation]:
    """
    Retrieve all messages for a given session, ordered oldest first.

    Args:
        db:         Active SQLAlchemy session.
        session_id: The session whose history you want.

    Returns:
        A list of Conversation records.
    """
    return (
        db.query(Conversation)
        .filter(Conversation.session_id == session_id)
        .order_by(Conversation.timestamp.asc())
        .all()
    )


def delete_conversation(db: Session, session_id: str) -> int:
    """
    Delete all messages for a given session.

    Args:
        db:         Active SQLAlchemy session.
        session_id: The session to clear.

    Returns:
        Number of rows deleted.
    """
    deleted = (
        db.query(Conversation)
        .filter(Conversation.session_id == session_id)
        .delete()
    )
    db.commit()
    return deleted
