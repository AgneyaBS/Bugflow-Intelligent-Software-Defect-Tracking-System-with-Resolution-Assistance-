from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.database import get_db
from app.models.notification import Notification
from app.models.user import User


router = APIRouter(
    prefix="/api/v1/notifications",
    tags=["Notifications"]
)


# ============================================================
# GET NOTIFICATIONS
# ============================================================

@router.get("/")
def get_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get notifications for the logged-in user.

    Deleted notifications are never returned.
    Newest notifications appear first.
    """

    notifications = (
        db.query(Notification)
        .filter(
            Notification.user_id == current_user.id,
            Notification.is_deleted == False
        )
        .order_by(
            Notification.created_at.desc()
        )
        .all()
    )

    return [
        {
            "id": notification.id,
            "notification_type": notification.notification_type,
            "title": notification.title,
            "message": notification.message,
            "issue_id": notification.issue_id,
            "is_read": notification.is_read,
            "created_at": notification.created_at
        }
        for notification in notifications
    ]


# ============================================================
# UNREAD COUNT
# ============================================================

@router.get("/unread-count")
def get_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Return the number of unread notifications.
    """

    count = (
        db.query(Notification)
        .filter(
            Notification.user_id == current_user.id,
            Notification.is_read == False,
            Notification.is_deleted == False
        )
        .count()
    )

    return {
        "unread_count": count
    }


# ============================================================
# MARK ONE AS READ
# ============================================================

@router.patch("/{notification_id}/read")
def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    notification = (
        db.query(Notification)
        .filter(
            Notification.id == notification_id,
            Notification.user_id == current_user.id,
            Notification.is_deleted == False
        )
        .first()
    )

    if not notification:
        raise HTTPException(
            status_code=404,
            detail="Notification not found"
        )

    notification.is_read = True

    db.commit()

    return {
        "success": True,
        "message": "Notification marked as read."
    }


# ============================================================
# MARK ALL AS READ
# ============================================================

@router.patch("/read-all")
def mark_all_notifications_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    (
        db.query(Notification)
        .filter(
            Notification.user_id == current_user.id,
            Notification.is_deleted == False
        )
        .update(
            {
                Notification.is_read: True
            },
            synchronize_session=False
        )
    )

    db.commit()

    return {
        "success": True,
        "message": "All notifications marked as read."
    }
# ============================================================
# DELETE SELECTED NOTIFICATIONS
# ============================================================

@router.delete("/selected")
def delete_selected_notifications(
    notification_ids: list[int],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not notification_ids:
        raise HTTPException(
            status_code=400,
            detail="No notifications selected."
        )

    notifications = (
        db.query(Notification)
        .filter(
            Notification.id.in_(notification_ids),
            Notification.user_id == current_user.id,
            Notification.is_deleted == False
        )
        .all()
    )

    if not notifications:
        raise HTTPException(
            status_code=404,
            detail="No matching notifications found."
        )

    for notification in notifications:
        notification.is_deleted = True

    db.commit()

    return {
        "success": True,
        "message": f"{len(notifications)} notification(s) deleted."
    }


# ============================================================
# DELETE ONE NOTIFICATION
# ============================================================

@router.delete("/{notification_id}/delete")
def delete_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    notification = (
        db.query(Notification)
        .filter(
            Notification.id == notification_id,
            Notification.user_id == current_user.id,
            Notification.is_deleted == False
        )
        .first()
    )

    if not notification:
        raise HTTPException(
            status_code=404,
            detail="Notification not found."
        )

    notification.is_deleted = True

    db.commit()

    return {
        "success": True,
        "message": "Notification deleted."
    }


# ============================================================
# DELETE ALL NOTIFICATIONS
# ============================================================

@router.delete("/")
def delete_all_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    (
        db.query(Notification)
        .filter(
            Notification.user_id == current_user.id,
            Notification.is_deleted == False
        )
        .update(
            {
                Notification.is_deleted: True
            },
            synchronize_session=False
        )
    )

    db.commit()

    return {
        "success": True,
        "message": "All notifications deleted."
    }
@router.websocket("/ws")
async def notification_websocket(
    websocket: WebSocket,
    db: Session = Depends(get_db)
):
    user_id = None

    try:

        # Accept connection
        await websocket.accept()

        # Browser sends JWT as first message
        token = await websocket.receive_text()

        payload = decode_access_token(token)

        if not payload:
            await websocket.send_json({
                "success": False,
                "message": "Invalid or expired token."
            })
            await websocket.close()
            return

        user_id = payload.get("sub")

        if not user_id:
            await websocket.close()
            return

        try:
            user_id = int(user_id)

        except (TypeError, ValueError):
            await websocket.close()
            return

        user = (
            db.query(User)
            .filter(
                User.id == user_id,
                User.is_active == True
            )
            .first()
        )

        if not user:
            await websocket.close()
            return

        # Only Admin users receive real-time notifications

        # Register Admin connection
        await notification_manager.connect(
            user_id,
            websocket
        )

        # Keep connection alive
        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:

        if user_id is not None:

            notification_manager.disconnect(
                user_id,
                websocket
            )

    except Exception:

        if user_id is not None:

            notification_manager.disconnect(
                user_id,
                websocket
            )