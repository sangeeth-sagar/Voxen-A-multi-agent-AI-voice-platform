import structlog
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.plan import ConversationSession
from app.models.agent_config import AgentConfig
from datetime import datetime

logger = structlog.get_logger()

async def create_session(
    db: Session,
    user_id: int = None,
    agent_id: int = None
) -> ConversationSession:
    """
    Creates new session record in DB.
    messages starts as empty list [].
    Returns the session object.
    """
    session = ConversationSession(
        user_id=user_id,
        agent_id=agent_id,
        messages=[]
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    if agent_id:
        agent = db.query(AgentConfig).filter(AgentConfig.id == agent_id).first()
        if agent:
            agent.use_count = (agent.use_count or 0) + 1
            db.commit()

    logger.info("session_created", session_id=session.session_id, user_id=user_id, agent_id=agent_id)
    return session

async def get_session(
    db: Session,
    session_id: str
) -> Optional[ConversationSession]:
    """
    Fetch session by session_id.
    Returns None if not found.
    """
    session = db.query(ConversationSession).filter(ConversationSession.session_id == session_id).first()
    if session:
        logger.debug("session_found", session_id=session_id)
    else:
        logger.debug("session_not_found", session_id=session_id)
    return session

async def add_message(
    db: Session,
    session_id: str,
    role: str,
    content: str
) -> ConversationSession:
    """
    role is "user" or "assistant"
    Appends {"role": role, "content": content, 
    "timestamp": datetime.utcnow().isoformat()} 
    to messages JSON array
    Updates updated_at
    Commits and returns updated session
    """
    session = db.query(ConversationSession).filter(ConversationSession.session_id == session_id).first()
    if not session:
        logger.error("session_not_found_for_add_message", session_id=session_id)
        raise ValueError(f"Session not found: {session_id}")
    
    # Prepare the new message
    new_message = {
        "role": role,
        "content": content,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Append to messages
    session.messages = list(session.messages or []) + [new_message]
    
    # Update the timestamp
    session.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(session)
    logger.debug("message_added", session_id=session_id, role=role)
    return session

async def get_session_messages(
    db: Session,
    session_id: str,
    last_n: int = 10
) -> List[dict]:
    """
    Returns last_n messages from session
    Each message is {"role": ..., "content": ...}
    Returns [] if session not found
    """
    session = db.query(ConversationSession).filter(ConversationSession.session_id == session_id).first()
    if not session:
        logger.debug("session_not_found_for_get_messages", session_id=session_id)
        return []
    
    messages = session.messages or []
    # Return last_n messages
    return messages[-last_n:] if last_n > 0 else []

async def end_session(
    db: Session,
    session_id: str
) -> bool:
    """
    Sets is_active = False
    Commits
    Returns True
    """
    session = db.query(ConversationSession).filter(ConversationSession.session_id == session_id).first()
    if not session:
        logger.debug("session_not_found_for_end", session_id=session_id)
        return False
    
    session.is_active = False
    session.updated_at = datetime.utcnow()
    db.commit()
    logger.info("session_ended", session_id=session_id)
    return True

async def get_user_sessions(
    db: Session,
    user_id: int,
    agent_id: int = None,
    limit: int = 20
) -> List[dict]:
    """
    Returns last N sessions for a user
    Filter by agent_id if provided
    Order by created_at desc
    Each session includes: session_id, agent_id, 
    created_at, updated_at, message_count (len of messages)
    """
    query = db.query(ConversationSession).filter(ConversationSession.user_id == user_id)
    if agent_id is not None:
        query = query.filter(ConversationSession.agent_id == agent_id)
    
    sessions = query.order_by(ConversationSession.created_at.desc()).limit(limit).all()
    
    result = []
    for session in sessions:
        result.append({
            "session_id": session.session_id,
            "agent_id": session.agent_id,
            "created_at": session.created_at.isoformat() if session.created_at else None,
            "updated_at": session.updated_at.isoformat() if session.updated_at else None,
            "message_count": len(session.messages) if session.messages else 0
        })
    
    logger.debug("user_sessions_retrieved", user_id=user_id, count=len(result))
    return result