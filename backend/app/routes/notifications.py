"""
Notification routes — session-scoped, in-memory only.
"""
from fastapi import APIRouter, Depends
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.services.notification_store import get_notifications, get_unread_count, mark_all_seen

router = APIRouter()


@router.get("")
def list_notifications(current_user: User = Depends(get_current_user)):
    """Get all notifications for the current session."""
    return {
        "notifications": get_notifications(current_user.id),
        "count": get_unread_count(current_user.id),
    }


@router.get("/count")
def notification_count(current_user: User = Depends(get_current_user)):
    """Lightweight endpoint just for the bell icon dot/badge."""
    return {"count": get_unread_count(current_user.id)}


@router.post("/mark-seen")
def mark_seen(current_user: User = Depends(get_current_user)):
    """Call this when the notification panel is opened — clears the
    badge count without deleting the notifications themselves."""
    mark_all_seen(current_user.id)
    return {"message": "Marked as seen"}
