


import re
from typing import Any, Dict, Optional
from uuid import uuid4

from fastapi import HTTPException, status
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.repositarys.admin_chat_repository import admin_chat_repository
from app.services.inventory_rag_service import inventory_rag_service
from app.services.inventory_service import inventory_service


class AdminChatbotService:

    def _get_admin_id(self, admin_user: Dict[str, Any]):
        return str(
            admin_user.get("id")
            or admin_user.get("email")
            or admin_user.get("username")
        )

    def _get_threshold(self, question: str):
        match = re.search(
            r"(?:less than|under|below|fewer than)\s+(\d+)",
            question.lower(),
        )

        if match:
            return int(match.group(1))

        return None

    async def _get_inventory_context(self, question: str):
        question = question.lower()
        threshold = self._get_threshold(question)

        if threshold is None and any(
            word in question
            for word in [
                "low in stock",
                "low stock",
                "getting out of stock",
                "running out of stock",
            ]
        ):
            threshold = settings.LOW_STOCK_THRESHOLD

        if threshold is not None:
            count = await inventory_service.count_items_with_quantity_less_than(
                threshold
            )

            items = await inventory_service.list_low_stock_items(threshold)

            names = ", ".join(
                f"{item.name} ({item.quantity_available})"
                for item in items
            )

            return (
                "STRUCTURED_DATABASE_RESULT\n"
                f"Count with quantity less than {threshold}: {count}\n"
                f"Matching products: {names or 'None'}"
            )

        if "out of stock" in question or "out-of-stock" in question:
            items = await inventory_service.list_out_of_stock_items()

            names = ", ".join(
                f"{item.name} ({item.quantity_available})"
                for item in items
            )

            return (
                "STRUCTURED_DATABASE_RESULT\n"
                f"Out-of-stock products: {names or 'None'}"
            )

        if "highest quantity" in question or "most stock" in question:
            item = await inventory_service.get_highest_quantity_item()

            if item:
                result = f"{item.name}: {item.quantity_available}"
            else:
                result = "None"

            return (
                "STRUCTURED_DATABASE_RESULT\n"
                f"Highest quantity product: {result}"
            )

        if not settings.QDRANT_URL:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Qdrant is not configured for inventory retrieval.",
            )

        try:
            context = inventory_rag_service.retrieve_context(
                question,
                top_k=5,
            )
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Inventory retrieval is temporarily unavailable.",
            )

        return (
            "RETRIEVED_QDRANT_CONTEXT\n"
            f"{context or 'No matching inventory context found.'}"
        )

    def _get_llm(self):
        api_key = settings.GROK_API_KEY or settings.GROQ_API_KEY

        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Groq is not configured.",
            )

        return ChatOpenAI(
            model=settings.GROQ_MODEL,
            api_key=api_key,
            base_url=settings.GROQ_BASE_URL,
            temperature=0,
        )

    async def ask( self, admin_user: Dict[str, Any], question: str, conversation_id: Optional[str] = None, ):
        if not question.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Question cannot be empty",
            )

        admin_id = self._get_admin_id(admin_user)

        if not conversation_id:
            conversation_id = await admin_chat_repository.get_latest_conversation_id(
                admin_id
            )

        if not conversation_id:
            conversation_id = str(uuid4())

        history = await admin_chat_repository.list_messages(
            admin_id,
            conversation_id,
        )

        context = await self._get_inventory_context(question)

        messages = [
            SystemMessage(
                content=(
                   "You are an admin grocery inventory assistant. "
                   "Answer only using the inventory context and chat history. "
                   "Do not make up product names, quantities, counts or prices. "
                    "Keep answers short. "
                    "Do not show your reasoning or thinking process. "
                   "Return only the final answer."
                )
            )
        ]

        for message in history:
            if message["role"] == "user":
                messages.append(
                    HumanMessage(content=message["content"])
                )

            elif message["role"] == "assistant":
                messages.append(
                    AIMessage(content=message["content"])
                )

        messages.append(
            HumanMessage(
                content=(
                    f"Inventory context:\n{context}\n\n"
                    f"Question: {question}"
                )
            )
        )

        try:
            response = await self._get_llm().ainvoke(messages)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Could not get response from Groq.",
            )

        # if isinstance(response.content, str):
        #     answer = response.content
        # else:
        #     answer = str(response.content)
        
        answer = str(response.content)
        answer = re.sub(r"<think>.*?</think>","",answer,flags=re.DOTALL,).strip()

        
        await admin_chat_repository.add_message(
            admin_id,
            conversation_id,
            "user",
            question.strip(),
        )

        await admin_chat_repository.add_message(
            admin_id,
            conversation_id,
            "assistant",
            answer,
        )

        return {
            "conversation_id": conversation_id,
            "answer": answer,
        }


admin_chatbot_service = AdminChatbotService()

