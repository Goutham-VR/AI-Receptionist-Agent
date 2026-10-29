from fastapi import FastAPI
from sqlalchemy import text
from pydantic import BaseModel, Field
from app.agent import receptionist_agent
from app.database import engine
import logging

logger = logging.getLogger(__name__)

from datetime import datetime
from app.models import Booking, CalendarSlot
from fastapi import Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import (
    router as auth_router,
    get_current_admin,
)
from app.models import AdminUser
from app.tools.calendar_tools import check_slots
from app.tools.approval_tools import reject_booking

from fastapi import Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.tools.approval_tools import (
    get_pending_approvals,
    approve_booking,
)


app = FastAPI(
    title="AI Receptionist Agent",
    description=(
        "An AI agent with tool calling, human approval, "
        "execution traces, and bounded execution."
    ),
    version="0.1.0",
)
app.include_router(auth_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatMessage(BaseModel):
    role: str
    content: str = Field(min_length=1, max_length=2000)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    conversation_history: list[ChatMessage] = Field(
        default_factory=list,
        max_length=20,
    )


@app.post("/agent/chat")
def chat_with_agent(payload: ChatRequest):
    message = payload.message.strip()

    if not message:
        raise HTTPException(
            status_code=422,
            detail="Message cannot be empty.",
        )

    history = [
        item.model_dump()
        for item in payload.conversation_history
    ]

    try:
        reply = receptionist_agent(
            user_message=message,
            conversation_history=history,
        )

        return {
            "success": True,
            "reply": reply,
        }

    except Exception:
        logger.exception("Public AI chat request failed")

        raise HTTPException(
            status_code=502,
            detail=(
                "The AI agent could not process your message. "
                "Please try again."
            ),
        )

    
@app.get("/")
def home():
    return {
        "project": "AI Receptionist Agent",
        "status": "running",
        "message": "Welcome to the AI Receptionist Agent API",
    }


@app.get("/health")
def health():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "status": "healthy",
            "database": "connected",
        }

    except Exception:
        return {
            "status": "unhealthy",
            "database": "connection failed",
        }

@app.get("/tools/check-slots")
def check_slots_endpoint(
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    db: Session = Depends(get_db),
):
    return check_slots(
        db=db,
        start_time=start_time,
        end_time=end_time,
    )


@app.get("/approvals/pending")
def list_pending_approvals(
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
):
    return get_pending_approvals(db)

@app.get("/bookings")
def list_bookings(
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
):
    bookings = (
        db.query(Booking, CalendarSlot)
        .join(
            CalendarSlot,
            Booking.slot_id == CalendarSlot.id,
        )
        .order_by(Booking.created_at.desc())
        .all()
    )

    return {
        "success": True,
        "count": len(bookings),
        "bookings": [
            {
                "id": booking.id,
                "slot_id": slot.id,
                "customer_name": booking.customer_name,
                "customer_email": booking.customer_email,
                "status": booking.status,
                "start_time": slot.start_time.isoformat(),
                "end_time": slot.end_time.isoformat(),
                "created_at": (
                    booking.created_at.isoformat()
                    if booking.created_at
                    else None
                ),
            }
            for booking, slot in bookings
        ],
    }

@app.post("/approvals/{approval_id}/approve")
def approve_booking_endpoint(
    approval_id: int,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
):
    result = approve_booking(
        db=db,
        approval_id=approval_id,
        reviewed_by=current_admin.email,
    )

    if not result["success"]:
        message = result["message"]

        if message == "Approval request not found.":
            raise HTTPException(
                status_code=404,
                detail=message,
            )

        raise HTTPException(
            status_code=409,
            detail=message,
        )

    return result

@app.post("/approvals/{approval_id}/reject")
def reject_approval(
    approval_id: int,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
):
    result = reject_booking(
        db=db,
        approval_id=approval_id,
        reviewed_by=current_admin.email,
    )

    if not result["success"]:
        message = result["message"]

        if message == "Approval request not found.":
            raise HTTPException(
                status_code=404,
                detail=message,
            )

        raise HTTPException(
            status_code=409,
            detail=message,
        )

    return result