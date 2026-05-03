"""
Inter-user direct + broadcast messaging.

Polling-first design (matches the relay/todos/announcements pattern).
Endpoints:
    GET    /api/messages/inbox            -> {messages, unread_count}
    GET    /api/messages/thread/{user_id} -> [messages]   (full conversation between me and other_user)
    POST   /api/messages                  -> send a message
    PATCH  /api/messages/{id}/read        -> mark message read
    GET    /api/users                     -> [{id, username, display_name, chip_color, profile_picture, online}]
                                            online = last_seen_at within the last 90s
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, List
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc

from database import get_db
from models_user import User
from models.messages import UserMessage
from auth.utils import get_current_user_or_key, require_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["messages"])

PRESENCE_WINDOW = timedelta(seconds=90)  # online if last_seen_at within this


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class MessageOut(BaseModel):
    id: int
    from_user_id: int
    from_username: Optional[str]
    from_display: Optional[str]
    to_user_id: Optional[int]
    content: str
    sent_at: datetime
    read_at: Optional[datetime]
    reply_to: Optional[int]


class SendMessageIn(BaseModel):
    to_user_id: Optional[int] = None  # None => broadcast (admin only)
    content: str
    reply_to: Optional[int] = None


class UserOut(BaseModel):
    id: int
    username: str
    display_name: Optional[str]
    chip_color: Optional[str]
    profile_picture: Optional[str]
    online: bool
    last_seen_at: Optional[datetime]
    current_location: Optional[dict] = None
    location_updated_at: Optional[datetime] = None


class LocationIn(BaseModel):
    """Public presence location written by the current user."""
    view: Optional[str] = None
    episode_number: Optional[str] = None
    segment_id: Optional[str] = None
    segment_title: Optional[str] = None
    mode: Optional[str] = None


def _user_id(current_user: dict) -> int:
    uid = current_user.get("id")
    if not uid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated principal has no user id (likely an API key)"
        )
    return int(uid)


def _msg_to_out(m: UserMessage) -> MessageOut:
    return MessageOut(
        id=m.id,
        from_user_id=m.from_user_id,
        from_username=getattr(m.sender, "username", None) if m.sender else None,
        from_display=(
            getattr(m.sender, "display_name", None)
            or getattr(m.sender, "username", None)
            if m.sender else None
        ),
        to_user_id=m.to_user_id,
        content=m.content,
        sent_at=m.sent_at,
        read_at=m.read_at,
        reply_to=m.reply_to,
    )


# ---------------------------------------------------------------------------
# Inbox + threads + send + read
# ---------------------------------------------------------------------------

@router.get("/messages/inbox")
async def get_inbox(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_key),
    limit: int = 50,
):
    """Most-recent messages addressed to me (or broadcasts), plus unread count."""
    me = _user_id(current_user)
    q = (
        db.query(UserMessage)
        .filter(or_(UserMessage.to_user_id == me, UserMessage.to_user_id.is_(None)))
        .order_by(desc(UserMessage.sent_at))
        .limit(limit)
    )
    rows = q.all()
    unread = (
        db.query(UserMessage)
        .filter(or_(UserMessage.to_user_id == me, UserMessage.to_user_id.is_(None)))
        .filter(UserMessage.read_at.is_(None))
        .filter(UserMessage.from_user_id != me)
        .count()
    )
    return {
        "messages": [_msg_to_out(m).model_dump() for m in rows],
        "unread_count": unread,
    }


@router.get("/messages/thread/{user_id}")
async def get_thread(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_key),
    limit: int = 200,
) -> List[dict]:
    """Full conversation between me and the given other user, oldest-first."""
    me = _user_id(current_user)
    if user_id == me:
        return []
    rows = (
        db.query(UserMessage)
        .filter(
            or_(
                and_(UserMessage.from_user_id == me, UserMessage.to_user_id == user_id),
                and_(UserMessage.from_user_id == user_id, UserMessage.to_user_id == me),
            )
        )
        .order_by(UserMessage.sent_at)
        .limit(limit)
        .all()
    )
    return [_msg_to_out(m).model_dump() for m in rows]


@router.post("/messages")
async def send_message(
    body: SendMessageIn,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_key),
):
    """Send a direct message (or, for admins, a broadcast when to_user_id is null)."""
    me = _user_id(current_user)
    content = (body.content or "").strip()
    if not content:
        raise HTTPException(status_code=400, detail="Empty message")
    if len(content) > 8000:
        raise HTTPException(status_code=400, detail="Message too long")

    if body.to_user_id is None:
        # Broadcast — admin only.
        access = current_user.get("access_level")
        if access != "admin":
            raise HTTPException(status_code=403, detail="Only admins can send broadcast messages")
    else:
        recipient = db.query(User).filter(User.id == body.to_user_id).first()
        if not recipient:
            raise HTTPException(status_code=404, detail="Recipient not found")

    msg = UserMessage(
        from_user_id=me,
        to_user_id=body.to_user_id,
        content=content,
        reply_to=body.reply_to,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return _msg_to_out(msg).model_dump()


@router.patch("/messages/{message_id}/read")
async def mark_read(
    message_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_key),
):
    me = _user_id(current_user)
    msg = db.query(UserMessage).filter(UserMessage.id == message_id).first()
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    # Only the recipient (or any user, for broadcasts) can mark read.
    if msg.to_user_id is not None and msg.to_user_id != me:
        raise HTTPException(status_code=403, detail="Not your message")
    if not msg.read_at:
        msg.read_at = datetime.now(timezone.utc)
        db.commit()
    return {"success": True, "id": msg.id, "read_at": msg.read_at}


# ---------------------------------------------------------------------------
# User directory + presence
# ---------------------------------------------------------------------------

@router.get("/users")
async def list_users(
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user_or_key),
):
    """All active, non-test users with current presence flag."""
    rows = (
        db.query(User)
        .filter(User.is_active == True, User.is_test_data == False)  # noqa: E712
        .order_by(User.username)
        .all()
    )
    cutoff = datetime.now(timezone.utc) - PRESENCE_WINDOW
    out = []
    for u in rows:
        last_seen = u.last_seen_at
        # naive datetimes from DB → assume UTC for comparison
        if last_seen and last_seen.tzinfo is None:
            last_seen = last_seen.replace(tzinfo=timezone.utc)
        online = bool(last_seen and last_seen >= cutoff)
        loc_updated = u.location_updated_at
        if loc_updated and loc_updated.tzinfo is None:
            loc_updated = loc_updated.replace(tzinfo=timezone.utc)
        out.append(UserOut(
            id=u.id,
            username=u.username,
            display_name=u.display_name or f"{(u.first_name or '').strip()} {(u.last_name or '').strip()}".strip() or u.username,
            chip_color=u.chip_color,
            profile_picture=u.profile_picture,
            online=online,
            last_seen_at=last_seen,
            current_location=u.current_location if online else None,
            location_updated_at=loc_updated if online else None,
        ).model_dump())
    return out


@router.get("/users/me")
async def get_my_profile(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_key),
):
    """Return the current user's profile (the bits that drive the
    presence/messaging UI)."""
    me = _user_id(current_user)
    user = db.query(User).filter(User.id == me).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    last_seen = user.last_seen_at
    if last_seen and last_seen.tzinfo is None:
        last_seen = last_seen.replace(tzinfo=timezone.utc)
    return UserOut(
        id=user.id,
        username=user.username,
        display_name=user.display_name or f"{(user.first_name or '').strip()} {(user.last_name or '').strip()}".strip() or user.username,
        chip_color=user.chip_color,
        profile_picture=user.profile_picture,
        online=True,
        last_seen_at=last_seen,
    ).model_dump()


# Admin-only placeholder for future user profile updates from a UI.
@router.patch("/users/me")
async def update_my_profile(
    body: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_key),
):
    """Update the current user's display_name / chip_color. Profile picture
    stays through existing user-management endpoints."""
    me = _user_id(current_user)
    user = db.query(User).filter(User.id == me).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if "display_name" in body:
        v = body["display_name"]
        user.display_name = v[:100] if isinstance(v, str) else None
    if "chip_color" in body:
        v = body["chip_color"]
        user.chip_color = v[:40] if isinstance(v, str) else None
    db.commit()
    return {"success": True, "id": user.id, "display_name": user.display_name, "chip_color": user.chip_color}


@router.put("/users/me/location")
async def set_my_location(
    body: LocationIn,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_key),
):
    """Public presence location. Visible to all logged-in users via
    /api/users. The frontend writes this from useSessionResume so other
    users can see "Lisa is editing 0271" in PresenceMenu."""
    me = _user_id(current_user)
    user = db.query(User).filter(User.id == me).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    payload = {k: v for k, v in body.model_dump().items() if v not in (None, "")}
    user.current_location = payload or None
    user.location_updated_at = datetime.now(timezone.utc)
    db.commit()
    return {"success": True, "location": payload}


# Reserved for the next phase: presence touch debounce wrapper.
_ = require_admin
