from typing import Any, Dict

from fastapi import APIRouter, Depends, status

from app.core.dependencies import require_admin
from app.domain.Chat.schemas import AdminChatRequest, AdminChatResponse
from app.services.admin_chatbot_service import admin_chatbot_service


router = APIRouter(
    prefix="/admin",
    tags=["Admin AI Chatbot"],
)


@router.post(
    "/chat",
    response_model=AdminChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Ask the Admin Inventory Chatbot",
)
async def ask_admin_chatbot(
    request: AdminChatRequest,
    admin_user: Dict[str, Any] = Depends(require_admin),
) -> AdminChatResponse:
    result = await admin_chatbot_service.ask(
        admin_user=admin_user,
        question=request.message,
    )
    return AdminChatResponse(**result)