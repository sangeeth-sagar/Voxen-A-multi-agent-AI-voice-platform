from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
import structlog
from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.user import User
from app.models.agent_config import AgentConfig
from app.schemas.agent_config import (
    AgentConfigCreate, AgentConfigUpdate, AgentConfigResponse
)
from app.config import get_settings

router = APIRouter()


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
    # Convert to response model, including owner_username
    result = []
    for agent in agents:
        owner_username = None
        if agent.user:
            owner_username = agent.user.username
        agent_dict = AgentConfigResponse.model_validate(agent).model_dump()
        agent_dict["owner_username"] = owner_username
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
    # Return response with owner_username
    agent_dict = AgentConfigResponse.model_validate(agent).model_dump()
    agent_dict["owner_username"] = current_user.username
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
    # Return response with owner_username
    owner_username = None
    if agent.user:
        owner_username = agent.user.username
    agent_dict = AgentConfigResponse.model_validate(agent).model_dump()
    agent_dict["owner_username"] = owner_username
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
    # Update fields if provided
    update_data = agent_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(agent, field, value)
    db.commit()
    db.refresh(agent)
    # Return response with owner_username
    owner_username = None
    if agent.user:
        owner_username = agent.user.username
    agent_dict = AgentConfigResponse.model_validate(agent).model_dump()
    agent_dict["owner_username"] = owner_username
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
    # Return response with owner_username
    owner_username = None
    if cloned_agent.user:
        owner_username = cloned_agent.user.username
    agent_dict = AgentConfigResponse.model_validate(cloned_agent).model_dump()
    agent_dict["owner_username"] = owner_username
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
    
    # Return response with owner_username
    owner_username = None
    if agent.user:
        owner_username = agent.user.username
    agent_dict = AgentConfigResponse.model_validate(agent).model_dump()
    agent_dict["owner_username"] = owner_username
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
    
    # Return response with owner_username
    owner_username = None
    if agent.user:
        owner_username = agent.user.username
    agent_dict = AgentConfigResponse.model_validate(agent).model_dump()
    agent_dict["owner_username"] = owner_username
    return AgentConfigResponse(**agent_dict)


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