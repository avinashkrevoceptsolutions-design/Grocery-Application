from fastapi import APIRouter
from typing import List

from pydantic import BaseModel, EmailStr

from app.services.email_service import EmailService


router = APIRouter(tags=["Email Notifications"])

class EmailRequest(BaseModel):
    to_email: List[EmailStr]
    subject: str
    body: str


@router.post("/send-email")
async def send_email(request: EmailRequest):
    await EmailService.send_email(
        to_email=request.to_email,
        subject=request.subject,
        body=request.body
    )

    return {
        "message": "Email sent successfully"
    }