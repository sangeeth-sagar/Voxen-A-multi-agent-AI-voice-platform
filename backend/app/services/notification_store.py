"""
Session-scoped notification store.

IMPORTANT: This is intentionally NOT a database table. Notifications
live in memory only, keyed by user_id, and are cleared when the
session ends (logout or idle timeout). This is a deliberate design
choice — notifications here are ephemeral session feedback, not a
permanent record requiring database persistence.

Storage: a simple in-process dict. Fine for a single-instance deployment.
If this app is ever horizontally scaled across multiple processes/
containers, this would need to move to Redis — noted for future work,
not required now.
"""
import threading
from datetime import datetime, timedelta
from typing import Literal, TypedDict
import uuid

NotificationType = Literal["voice_session", "agent_update", "admin_action", "system"]


class Notification(TypedDict):
    id: str
    type: NotificationType
    title: str
    message: str
    severity: Literal["success", "error", "info", "warning"]
    created_at: str  # ISO format


_lock = threading.Lock()
_store: dict[int, list[Notification]] = {}
_seen_counts: dict[int, int] = {}

MAX_NOTIFICATIONS_PER_USER = 50  # cap to prevent unbounded memory growth


def add_notification(
    user_id: int,
    type: NotificationType,
    title: str,
    message: str,
    severity: str = "info",
) -> Notification:
    """Add a notification for a user. Thread-safe."""
    notification: Notification = {
        "id": str(uuid.uuid4()),
        "type": type,
        "title": title,
        "message": message,
        "severity": severity,
        "created_at": datetime.utcnow().isoformat(),
    }
    with _lock:
        if user_id not in _store:
            _store[user_id] = []
        _store[user_id].insert(0, notification)  # newest first
        _store[user_id] = _store[user_id][:MAX_NOTIFICATIONS_PER_USER]
    return notification


def get_notifications(user_id: int) -> list[Notification]:
    """Get all notifications for a user, newest first."""
    with _lock:
        return list(_store.get(user_id, []))


def mark_all_seen(user_id: int) -> None:
    """Call this when the user opens the notification panel.
    Sets the 'seen' watermark to the current total count."""
    with _lock:
        _seen_counts[user_id] = len(_store.get(user_id, []))


def clear_notifications(user_id: int) -> None:
    """Clear all notifications for a user. Called on logout/session end."""
    with _lock:
        _store.pop(user_id, None)
        _seen_counts.pop(user_id, None)


def get_unread_count(user_id: int) -> int:
    """Returns only the count of notifications added SINCE the user
    last opened the panel — this is what drives the badge number."""
    with _lock:
        total = len(_store.get(user_id, []))
        seen = _seen_counts.get(user_id, 0)
        return max(0, total - seen)
