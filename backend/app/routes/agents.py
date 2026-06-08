from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from pydantic import BaseModel as PydanticBaseModel
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
import structlog
from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.user import User
from app.models.agent_config import AgentConfig
from app.models.agent_key_assignment import AgentApiKeyAssignment
from app.models.user_api_key import UserApiKey
from app.schemas.agent_config import (
    AgentConfigCreate, AgentConfigUpdate, AgentConfigResponse
)
from app.config import get_settings

router = APIRouter()


# ---------------------------------------------------------------------------
# Helper: attach key-assignment info to an agent response dict
# ---------------------------------------------------------------------------
def _attach_key_info(db: Session, agent: AgentConfig, agent_dict: dict) -> dict:
    """Augment an agent response dict with key-assignment fields.

    Always safe to call — returns sensible defaults if no assignment exists.
    """
    assignment = (
        db.query(AgentApiKeyAssignment)
        .filter(AgentApiKeyAssignment.agent_id == agent.id)
        .first()
    )
    agent_dict["has_key_assignment"] = assignment is not None
    agent_dict["llm_provider"] = assignment.llm_provider if assignment else None
    agent_dict["tts_provider"] = assignment.tts_provider if assignment else None
    agent_dict["stt_provider"] = assignment.stt_provider if assignment else None
    agent_dict["llm_key_id"] = assignment.llm_api_key_id if assignment else None
    agent_dict["tts_key_id"] = assignment.tts_api_key_id if assignment else None
    agent_dict["stt_key_id"] = assignment.stt_api_key_id if assignment else None
    return agent_dict


@router.get("", response_model=List[AgentConfigResponse])
def list_agents(
    my: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if my:
        agents = db.query(AgentConfig).filter(AgentConfig.user_id == current_user.id).all()
    else:
        # Return own agents + all public/template agents
        agents = (
            db.query(AgentConfig)
            .filter(
                (AgentConfig.user_id == current_user.id)
                | (AgentConfig.is_public == True)
                | (AgentConfig.is_template == True)
            )
            .all()
        )
    # Convert to response model, including owner_username and key info
    result = []
    for agent in agents:
        owner_username = None
        if agent.user:
            owner_username = agent.user.username
        agent_dict = AgentConfigResponse.model_validate(agent).model_dump()
        agent_dict["owner_username"] = owner_username
        _attach_key_info(db, agent, agent_dict)
        result.append(AgentConfigResponse(**agent_dict))
    return result


@router.post("", response_model=AgentConfigResponse, status_code=status.HTTP_201_CREATED)
def create_agent(
    agent_in: AgentConfigCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Check max agents per user
    settings = get_settings()
    current_count = (
        db.query(AgentConfig)
        .filter(AgentConfig.user_id == current_user.id)
        .count()
    )
    if current_count >= settings.max_agents_per_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum number of agents per user exceeded ({settings.max_agents_per_user})",
        )
    # Create agent
    agent = AgentConfig(
        user_id=current_user.id,
        name=agent_in.name,
        description=agent_in.description,
        agent_type=agent_in.agent_type,
        system_prompt=agent_in.system_prompt,
        tools_enabled=agent_in.tools_enabled,
        output_format=agent_in.output_format,
        is_public=agent_in.is_public,
    )
    db.add(agent)
    db.commit()
    db.refresh(agent)

    # Save key assignment immediately after agent creation (if any key was provided)
    if agent_in.llm_key_id or agent_in.tts_key_id or agent_in.stt_key_id:
        assignment = AgentApiKeyAssignment(
            agent_id=agent.id,
            llm_provider=agent_in.llm_provider or "gemini",
            llm_api_key_id=agent_in.llm_key_id,
            tts_provider=agent_in.tts_provider or "browser",
            tts_api_key_id=agent_in.tts_key_id,
            stt_provider=agent_in.stt_provider or "groq",
            stt_api_key_id=agent_in.stt_key_id,
        )
        db.add(assignment)
        db.commit()
        db.refresh(assignment)

    # Return response with owner_username + key info
    agent_dict = AgentConfigResponse.model_validate(agent).model_dump()
    agent_dict["owner_username"] = current_user.username
    _attach_key_info(db, agent, agent_dict)
    return AgentConfigResponse(**agent_dict)


@router.get("/{agent_uuid}", response_model=AgentConfigResponse)
def get_agent(
    agent_uuid: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    agent = db.query(AgentConfig).filter(AgentConfig.uuid == agent_uuid).first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        )
    # Check if agent is accessible: own, public, or template
    if not (
        agent.user_id == current_user.id
        or agent.is_public == True
        or agent.is_template == True
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    # Return response with owner_username + key info
    owner_username = None
    if agent.user:
        owner_username = agent.user.username
    agent_dict = AgentConfigResponse.model_validate(agent).model_dump()
    agent_dict["owner_username"] = owner_username
    _attach_key_info(db, agent, agent_dict)
    return AgentConfigResponse(**agent_dict)


@router.put("/{agent_uuid}", response_model=AgentConfigResponse)
def update_agent(
    agent_uuid: str,
    agent_in: AgentConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    agent = db.query(AgentConfig).filter(AgentConfig.uuid == agent_uuid).first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        )
    # Only owner can update
    if agent.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this agent",
        )

    # Split model fields (AgentConfig columns) from key-assignment fields
    key_assignment_fields = {
        "llm_provider", "llm_key_id",
        "tts_provider", "tts_key_id",
        "stt_provider", "stt_key_id",
    }
    update_data = agent_in.model_dump(exclude_unset=True)
    agent_fields = {k: v for k, v in update_data.items() if k not in key_assignment_fields}
    key_fields = {k: v for k, v in update_data.items() if k in key_assignment_fields}

    # Update agent fields
    for field, value in agent_fields.items():
        setattr(agent, field, value)
    db.commit()
    db.refresh(agent)

    # Update or create key assignment
    if key_fields:
        existing_assignment = (
            db.query(AgentApiKeyAssignment)
            .filter(AgentApiKeyAssignment.agent_id == agent.id)
            .first()
        )

        if existing_assignment:
            if "llm_provider" in key_fields and key_fields["llm_provider"] is not None:
                existing_assignment.llm_provider = key_fields["llm_provider"]
            if "llm_key_id" in key_fields and key_fields["llm_key_id"] is not None:
                existing_assignment.llm_api_key_id = key_fields["llm_key_id"]
            if "tts_provider" in key_fields and key_fields["tts_provider"] is not None:
                existing_assignment.tts_provider = key_fields["tts_provider"]
            if "tts_key_id" in key_fields and key_fields["tts_key_id"] is not None:
                existing_assignment.tts_api_key_id = key_fields["tts_key_id"]
            if "stt_provider" in key_fields and key_fields["stt_provider"] is not None:
                existing_assignment.stt_provider = key_fields["stt_provider"]
            if "stt_key_id" in key_fields and key_fields["stt_key_id"] is not None:
                existing_assignment.stt_api_key_id = key_fields["stt_key_id"]
        else:
            new_assignment = AgentApiKeyAssignment(
                agent_id=agent.id,
                llm_provider=key_fields.get("llm_provider") or "gemini",
                llm_api_key_id=key_fields.get("llm_key_id"),
                tts_provider=key_fields.get("tts_provider") or "browser",
                tts_api_key_id=key_fields.get("tts_key_id"),
                stt_provider=key_fields.get("stt_provider") or "groq",
                stt_api_key_id=key_fields.get("stt_key_id"),
            )
            db.add(new_assignment)
        db.commit()

    # Return response with owner_username + key info
    owner_username = None
    if agent.user:
        owner_username = agent.user.username
    agent_dict = AgentConfigResponse.model_validate(agent).model_dump()
    agent_dict["owner_username"] = owner_username
    _attach_key_info(db, agent, agent_dict)
    return AgentConfigResponse(**agent_dict)


@router.delete("/{agent_uuid}", status_code=status.HTTP_200_OK)
def delete_agent(
    agent_uuid: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    agent = db.query(AgentConfig).filter(AgentConfig.uuid == agent_uuid).first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        )
    # Only owner can delete
    if agent.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this agent",
        )
    db.delete(agent)
    db.commit()
    return {"message": "Agent deleted"}


@router.post("/{agent_uuid}/clone", response_model=AgentConfigResponse)
def clone_agent(
    agent_uuid: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Get source agent
    source_agent = db.query(AgentConfig).filter(AgentConfig.uuid == agent_uuid).first()
    if not source_agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        )
    # Check if source agent is public or template
    if not (source_agent.is_public == True or source_agent.is_template == True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Agent is not available for cloning",
        )
    # Check max agents per user
    settings = get_settings()
    current_count = (
        db.query(AgentConfig)
        .filter(AgentConfig.user_id == current_user.id)
        .count()
    )
    if current_count >= settings.max_agents_per_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum number of agents per user exceeded ({settings.max_agents_per_user})",
        )
    # Create cloned agent
    cloned_agent = AgentConfig(
        user_id=current_user.id,
        name=f"Copy of {source_agent.name}",
        description=source_agent.description,
        agent_type=source_agent.agent_type,
        system_prompt=source_agent.system_prompt,
        tools_enabled=source_agent.tools_enabled,
        output_format=source_agent.output_format,
        is_public=False,  # Clone is private by default
        is_template=False,
        # Voice agent fields
        is_voice_agent=source_agent.is_voice_agent,
        voice_language=source_agent.voice_language,
        voice_system_prompt=source_agent.voice_system_prompt,
        knowledge_base_text=source_agent.knowledge_base_text,
    )
    db.add(cloned_agent)
    # Increment source agent's use_count
    source_agent.use_count += 1
    db.commit()
    db.refresh(cloned_agent)
    # Return response with owner_username + key info
    owner_username = None
    if cloned_agent.user:
        owner_username = cloned_agent.user.username
    agent_dict = AgentConfigResponse.model_validate(cloned_agent).model_dump()
    agent_dict["owner_username"] = owner_username
    _attach_key_info(db, cloned_agent, agent_dict)
    return AgentConfigResponse(**agent_dict)


# New endpoints for voice agent features

@router.post("/{agent_uuid}/activate", response_model=AgentConfigResponse)
def activate_agent(
    agent_uuid: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Activate an agent for voice interactions.
    Generates webhook_id and webhook_url.
    Only the agent owner can activate.
    """
    agent = db.query(AgentConfig).filter(AgentConfig.uuid == agent_uuid).first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        )
    # Only owner can activate
    if agent.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to activate this agent",
        )
    
    # Generate webhook_id and webhook_url
    settings = get_settings()
    webhook_id = str(uuid.uuid4()).replace("-", "")[:24]
    webhook_url = f"{settings.webhook_base_url}/api/v1/webhook/{webhook_id}"
    
    # Update agent
    agent.is_active = True
    agent.webhook_id = webhook_id
    agent.webhook_url = webhook_url

    db.commit()
    db.refresh(agent)

    # Log activation
    import structlog
    logger = structlog.get_logger()
    logger.info("agent_activated", agent_uuid=agent.uuid, webhook_id=webhook_id)

    # Check for key assignment and warn if missing
    assignment = (
        db.query(AgentApiKeyAssignment)
        .filter(AgentApiKeyAssignment.agent_id == agent.id)
        .first()
    )

    if not assignment or not assignment.llm_api_key_id:
        logger.warning(
            "agent_activated_without_key",
            agent_uuid=agent.uuid,
            message="Agent activated but has no LLM key — voice will fail",
        )
    
    # Return response with owner_username + key info
    owner_username = None
    if agent.user:
        owner_username = agent.user.username
    agent_dict = AgentConfigResponse.model_validate(agent).model_dump()
    agent_dict["owner_username"] = owner_username
    _attach_key_info(db, agent, agent_dict)
    return AgentConfigResponse(**agent_dict)


@router.post("/{agent_uuid}/deactivate", response_model=AgentConfigResponse)
def deactivate_agent(
    agent_uuid: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Deactivate an agent for voice interactions.
    Only the agent owner can deactivate.
    """
    agent = db.query(AgentConfig).filter(AgentConfig.uuid == agent_uuid).first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        )
    # Only owner can deactivate
    if agent.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to deactivate this agent",
        )
    
    # Update agent
    agent.is_active = False
    agent.webhook_id = None
    agent.webhook_url = None
    
    db.commit()
    db.refresh(agent)
    
    # Log deactivation
    import structlog
    logger = structlog.get_logger()
    logger.info("agent_deactivated", agent_uuid=agent.uuid)
    
    # Return response with owner_username + key info
    owner_username = None
    if agent.user:
        owner_username = agent.user.username
    agent_dict = AgentConfigResponse.model_validate(agent).model_dump()
    agent_dict["owner_username"] = owner_username
    _attach_key_info(db, agent, agent_dict)
    return AgentConfigResponse(**agent_dict)


# ---------------------------------------------------------------------------
# Test endpoint — direct LLM call using the agent's assigned key
# ---------------------------------------------------------------------------
class AgentTestRequest(PydanticBaseModel):
    text: str
    language: str = "en"


@router.post("/{agent_uuid}/test")
async def test_agent(
    agent_uuid: str,
    body: AgentTestRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Send a single text prompt to the agent's LLM and return the reply.

    Reads the key assignment, decrypts the stored LLM key, invokes the
    configured provider, and returns the raw text response. Used by the
    frontend "Test Agent" panel in AgentBuilder.
    """
    from app.utils.encryption import decrypt_key
    from app.llm_router import get_llm, build_system_prompt

    agent = db.query(AgentConfig).filter(
        AgentConfig.uuid == agent_uuid,
        AgentConfig.user_id == current_user.id
    ).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    assignment = db.query(AgentApiKeyAssignment).filter(
        AgentApiKeyAssignment.agent_id == agent.id
    ).first()
    if not assignment or not assignment.llm_api_key_id:
        raise HTTPException(
            status_code=400,
            detail="No API key attached to this agent. Edit it and attach your Gemini key.",
        )

    llm_key_row = db.query(UserApiKey).filter(
        UserApiKey.id == assignment.llm_api_key_id
    ).first()
    if not llm_key_row:
        raise HTTPException(status_code=400, detail="API key record not found")

    llm_key = decrypt_key(llm_key_row.api_key)

    try:
        llm = get_llm(assignment.llm_provider or "gemini", llm_key)
        system_prompt = build_system_prompt(agent, body.language)
        messages = [("system", system_prompt), ("human", body.text)]
        result = await llm.ainvoke(messages)

        raw = result.content
        if isinstance(raw, list):
            response_text = "".join(
                p.get("text", "") if isinstance(p, dict) else str(p)
                for p in raw
            )
        else:
            response_text = raw if isinstance(raw, str) else str(raw)

        return {"response": response_text, "provider": assignment.llm_provider}
    except Exception as e:
        logger = structlog.get_logger()
        logger.error("agent_test_failed", agent_uuid=agent.uuid, error=str(e))
        raise HTTPException(status_code=500, detail=f"Test failed: {str(e)}")


@router.post("/{agent_uuid}/kb/upload")
async def upload_kb_file(
    agent_uuid: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Upload a file to the agent's knowledge base.
    Only works if kb_enabled is True.
    Only the agent owner can upload.
    """
    from app.services.rag import create_kb_collection, ingest_file
    import structlog

    agent = db.query(AgentConfig).filter(AgentConfig.uuid == agent_uuid).first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        )
    # Only owner can upload
    if agent.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to upload to this agent's knowledge base",
        )

    # Check if KB is enabled
    if not agent.kb_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Knowledge base is not enabled for this agent",
        )

    # Create KB collection if it doesn't exist
    collection_name = agent.kb_collection_name
    if collection_name is None:
        collection_name = f"agent_{agent.uuid}_kb"
        # Create the collection
        collection_name = await create_kb_collection(collection_name)
        # Update agent
        agent.kb_collection_name = collection_name
        db.add(agent)
        db.commit()
        db.refresh(agent)

    # Read file bytes
    file_bytes = file.file.read()

    # Ingest the file
    chunk_count = await ingest_file(collection_name, file_bytes, file.filename)
    
    # Log upload
    logger = structlog.get_logger()
    logger.info("kb_file_uploaded", 
                agent_uuid=agent.uuid,
                filename=file.filename,
                chunks=chunk_count,
                collection=collection_name)
    
    return {
        "message": "File uploaded successfully",
        "chunks": chunk_count,
        "collection": collection_name
    }


@router.delete("/{agent_uuid}/kb")
async def delete_kb(
    agent_uuid: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete the agent's knowledge base.
    Only the agent owner can delete.
    """
    from app.services.rag import delete_kb_collection
    import structlog

    agent = db.query(AgentConfig).filter(AgentConfig.uuid == agent_uuid).first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        )
    # Only owner can delete
    if agent.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this agent's knowledge base",
        )

    # Delete KB collection if it exists
    if agent.kb_collection_name:
        delete_success = await delete_kb_collection(agent.kb_collection_name)
        if delete_success:
            logger = structlog.get_logger()
            logger.info("kb_deleted", agent_uuid=agent.uuid, collection=agent.kb_collection_name)
        # Clear the collection name regardless
        agent.kb_collection_name = None
        db.add(agent)
        db.commit()
        db.refresh(agent)
    
    return {"message": "Knowledge base deleted successfully"}


@router.get("/{agent_uuid}/sessions")
async def get_agent_sessions(
    agent_uuid: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get all sessions for a specific agent.
    Only the agent owner can view.
    """
    from app.services.session_store import get_user_sessions

    agent = db.query(AgentConfig).filter(AgentConfig.uuid == agent_uuid).first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        )
    # Only owner can view sessions
    if agent.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view sessions for this agent",
        )

    # Get sessions for this user and agent
    sessions = await get_user_sessions(db, current_user.id, agent.id)

    return sessions
