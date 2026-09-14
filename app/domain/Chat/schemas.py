from typing import Literal

from pydantic import BaseModel, Field


class AdminChatRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
    )


class AdminChatResponse(BaseModel):
    conversation_id: str
    answer: str
    # source: Literal["structured", "rag"]