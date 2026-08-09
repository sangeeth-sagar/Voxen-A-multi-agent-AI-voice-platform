import httpx
import structlog
from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.models.agent_config import AgentConfig
from app.models.telegram_bot_config import TelegramBotConfig
from app.services.chat_core import run_chat_core
from app.config import settings

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1/telegram", tags=["telegram-gateway"])

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class TelegramBotCreate(BaseModel):
    agent_id: int
    telegram_token: str
    voxen_api_key_id: Optional[int] = None

class TelegramBotVerify(BaseModel):
    telegram_token: str

@router.post("/verify")
async def verify_bot(
    body: TelegramBotVerify,
    current_user: User = Depends(get_current_user)
):
    """
    Checks if a Telegram Bot token is valid using getMe and returns basic info.
    """
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(f"https://api.telegram.org/bot{body.telegram_token}/getMe")
            if resp.status_code != 200:
                raise HTTPException(status_code=400, detail="Invalid Telegram Token")
            bot_info = resp.json().get("result", {})
            return {
                "ok": True,
                "username": bot_info.get("username"),
                "first_name": bot_info.get("first_name"),
            }
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid Telegram Token or connection timeout")

# ---------------------------------------------------------------------------
# Telegram Bot Webhook Listener
# ---------------------------------------------------------------------------
@router.post("/webhook/{bot_token}")
async def telegram_webhook(
    bot_token: str,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Receives incoming updates from the Telegram Bot API, parses user texts,
    and runs the Unified Chat Core in a background task to reply to users asynchronously.
    """
    try:
        update = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid payload")

    message = update.get("message")
    if not message:
        return {"status": "ignored", "reason": "no message update"}

    chat = message.get("chat")
    user_text = message.get("text")
    if not chat or not user_text:
        return {"status": "ignored", "reason": "no text or chat info"}

    chat_id = chat.get("id")
    if not chat_id:
        return {"status": "ignored"}

    # Resolve bot configuration
    bot_config = (
        db.query(TelegramBotConfig)
        .filter(TelegramBotConfig.telegram_token == bot_token, TelegramBotConfig.is_active == True)
        .first()
    )
    if not bot_config:
        return {"status": "error", "message": "Bot config not found or inactive"}
    if not bot_config.agent or not bot_config.agent.is_active:
        return {"status": "error", "message": "Associated agent is inactive"}

    # Check if this bot configuration requires a valid Voxen API Key
    if bot_config.voxen_api_key_id:
        from app.models.voxen_api_key import VoxenApiKey
        active_key = db.query(VoxenApiKey).filter(
            VoxenApiKey.id == bot_config.voxen_api_key_id,
            VoxenApiKey.is_active == True
        ).first()
        if not active_key:
            logger.warning("telegram_webhook_rejected_revoked_key", bot_username=bot_config.bot_username, voxen_api_key_id=bot_config.voxen_api_key_id)
            return {"status": "error", "message": "The associated Voxen API key for this bot has been revoked or is inactive"}

    # Run chat session asynchronously using chat_id as session ID
    session_id = f"tg_{chat_id}"
    background_tasks.add_task(
        process_telegram_message_task, 
        bot_config.agent_id, 
        bot_token, 
        user_text, 
        chat_id, 
        session_id
    )
    return {"status": "queued"}


async def process_telegram_message_task(
    agent_id: int, 
    bot_token: str, 
    text: str, 
    chat_id: int, 
    session_id: str
):
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        # 1. Run Core Chat Engine
        result = await run_chat_core(
            db=db,
            agent_id=agent_id,
            text=text,
            session_id=session_id,
            language="en"
        )
        
        reply_text = result["response"]
        
        # 2. Post answer to Telegram Bot API
        async with httpx.AsyncClient(timeout=10.0) as client:
            tg_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            await client.post(tg_url, json={"chat_id": chat_id, "text": reply_text})
            
    except Exception as e:
        logger.error("telegram_send_failed", error=str(e), chat_id=chat_id)
    finally:
        db.close()


# ---------------------------------------------------------------------------
# CRUD Bot Configurations (Admin / User Dashboard panels)
# ---------------------------------------------------------------------------
@router.post("/bots")
async def register_bot(
    body: TelegramBotCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Registers a Telegram token for an agent, gets the bot details, 
    and sets up the Telegram API webhook redirect callback.
    """
    # Verify agent ownership
    agent = (
        db.query(AgentConfig)
        .filter(AgentConfig.id == body.agent_id, AgentConfig.user_id == current_user.id)
        .first()
    )
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Call getMe to check token validity and retrieve bot details
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(f"https://api.telegram.org/bot{body.telegram_token}/getMe")
            if resp.status_code != 200:
                raise HTTPException(status_code=400, detail="Invalid Telegram Token")
            bot_info = resp.json().get("result", {})
            bot_username = bot_info.get("username")
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid Telegram Token or connection timeout")

    # Save bot configuration to database
    bot_config = (
        db.query(TelegramBotConfig)
        .filter(TelegramBotConfig.telegram_token == body.telegram_token)
        .first()
    )
    if bot_config:
        bot_config.agent_id = body.agent_id
        bot_config.voxen_api_key_id = body.voxen_api_key_id
        bot_config.is_active = True
    else:
        bot_config = TelegramBotConfig(
            agent_id=body.agent_id,
            telegram_token=body.telegram_token,
            bot_username=bot_username,
            voxen_api_key_id=body.voxen_api_key_id,
            is_active=True
        )
        db.add(bot_config)
    
    db.commit()
    db.refresh(bot_config)

    # Set webhook on Telegram Bot API
    webhook_url = f"{settings.webhook_base_url}/api/v1/telegram/webhook/{body.telegram_token}"
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            set_webhook_url = f"https://api.telegram.org/bot{body.telegram_token}/setWebhook"
            resp = await client.post(set_webhook_url, json={"url": webhook_url})
            resp.raise_for_status()
            res_json = resp.json()
            if not res_json.get("ok"):
                error_desc = res_json.get("description", "Unknown error")
                raise HTTPException(status_code=400, detail=f"Telegram API rejected webhook: {error_desc}")
            logger.info("telegram_webhook_set", bot_username=bot_username, url=webhook_url)
        except httpx.HTTPStatusError as e:
            try:
                err_data = e.response.json()
                err_msg = err_data.get("description", str(e))
            except Exception:
                err_msg = str(e)
            raise HTTPException(status_code=400, detail=f"Telegram API error: {err_msg}")
        except HTTPException:
            raise
        except Exception as e:
            logger.error("telegram_webhook_set_failed", error=str(e))
            raise HTTPException(status_code=400, detail=f"Webhook connection error: {str(e)}")

    return {
        "id": bot_config.id,
        "bot_username": bot_username,
        "webhook_url": webhook_url,
        "message": "Telegram Bot registered and webhook set successfully"
    }


@router.get("/bots")
async def list_bots(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lists registered Telegram bots owned by the caller."""
    bots = (
        db.query(TelegramBotConfig)
        .join(AgentConfig)
        .filter(AgentConfig.user_id == current_user.id)
        .all()
    )
    return [
        {
            "id": b.id,
            "agent_id": b.agent_id,
            "agent_name": b.agent.name,
            "bot_username": b.bot_username,
            "is_active": b.is_active,
            "created_at": b.created_at,
            "webhook_url": f"{settings.webhook_base_url}/api/v1/telegram/webhook/{b.telegram_token[:4]}...{b.telegram_token[-4:]}" if len(b.telegram_token) > 8 else "Invalid Token",
            "webhook_base_url": settings.webhook_base_url,
            "voxen_api_key_id": b.voxen_api_key_id
        }
        for b in bots
    ]


@router.delete("/bots/{bot_id}")
async def delete_bot(
    bot_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Deletes/deconfigures a Telegram bot."""
    bot = (
        db.query(TelegramBotConfig)
        .join(AgentConfig)
        .filter(TelegramBotConfig.id == bot_id, AgentConfig.user_id == current_user.id)
        .first()
    )
    if not bot:
        raise HTTPException(status_code=404, detail="Bot configuration not found")
        
    # Unset webhook before delete
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            await client.post(f"https://api.telegram.org/bot{bot.telegram_token}/deleteWebhook")
        except Exception:
            pass

    db.delete(bot)
    db.commit()
    return {"message": "Telegram Bot removed successfully"}
