import structlog
from app.models.agent_memory import AgentMemory

logger = structlog.get_logger()

async def summarize_session_memory(db, agent, conversation_history, llm_provider, api_key):
    if not conversation_history:
        return
        
    # Format the conversation text
    lines = []
    for role, content in conversation_history:
        speaker = "User" if role == "human" else "Agent"
        lines.append(f"{speaker}: {content}")
    conversation_text = "\n".join(lines)

    # Get previous memory summary
    db_mem = db.query(AgentMemory).filter(AgentMemory.agent_id == agent.id).first()
    prev_summary = db_mem.summary if db_mem else "No previous memory."

    prompt = f"""You are a memory processor. Below is the previous memory summary of the agent, and the new conversation history.
Generate a single consolidated summary (under 4 sentences) of what the agent learned about the user, their preferences, or the state of their conversation, to be used in future conversations.
Keep it concise, matter-of-fact, and focus on details the agent should remember next time.

Previous Memory: {prev_summary}

New Conversation:
{conversation_text}

New consolidated summary:"""

    try:
        from app.llm_router import get_llm
        llm = get_llm(llm_provider, api_key)
        response = await llm.ainvoke([("human", prompt)])
        summary_text = response.content
        if isinstance(summary_text, list):
            summary_text = "".join(
                p.get("text", "") if isinstance(p, dict) else (str(p) if p else "")
                for p in summary_text
            )
        
        summary_text = summary_text.strip()
        if summary_text:
            if not db_mem:
                db_mem = AgentMemory(agent_id=agent.id, summary=summary_text)
                db.add(db_mem)
            else:
                db_mem.summary = summary_text
            db.commit()
            logger.info("session_memory_summarized", agent_uuid=agent.uuid)
    except Exception as e:
        logger.warning(f"Memory summarization failed: {e}")
