
import logging
from typing import Any, Dict, List, Optional
from uuid import NAMESPACE_URL, uuid5

from langchain_core.embeddings import Embeddings

from app.core.config import settings

logger = logging.getLogger(__name__)


class FastEmbedEmbeddings(Embeddings):
    def __init__(self, service):
        self.service = service

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        vectors = self.service._get_embedding_model().embed(texts)
        return [vector.tolist() for vector in vectors]

    def embed_query(self, text: str) -> List[float]:
        return self.service._embed(text)


class InventoryRagService:
    def __init__(self):
        self.client = None
        self.embedding_model = None
        self.vector_store = None

    def _is_configured(self):
        return bool(settings.QDRANT_URL)

    def _get_client(self):
        if self.client is None:
            from qdrant_client import QdrantClient

            self.client = QdrantClient(
                url=settings.QDRANT_URL,
                api_key=settings.QDRANT_API_KEY,
            )

        return self.client

    def _get_embedding_model(self):
        if self.embedding_model is None:
            from fastembed import TextEmbedding

            self.embedding_model = TextEmbedding(
                model_name=settings.EMBEDDING_MODEL
            )

        return self.embedding_model

    def _embed(self, text: str):
        vector = next(self._get_embedding_model().embed([text]))
        return vector.tolist()

    def _make_text(self, item: Dict[str, Any]):
        return (
            f"Product: {item.get('name', '')}\n"
            f"Price: {item.get('price', 0)}\n"
            f"Quantity available: {item.get('quantity_available', 0)}\n"
            f"Status: {item.get('status', '')}\n"
            f"Last updated: {item.get('updated_at', item.get('created_at', ''))}"
        )

    def _get_point_id(self, item_id: str):
        return str(uuid5(NAMESPACE_URL, f"inventory:{item_id}"))

    def _create_collection(self, vector_size: int):
        from qdrant_client.http import models

        client = self._get_client()

        collections = client.get_collections().collections
        names = [collection.name for collection in collections]

        if settings.QDRANT_COLLECTION not in names:
            client.create_collection(
                collection_name=settings.QDRANT_COLLECTION,
                vectors_config=models.VectorParams(
                    size=vector_size,
                    distance=models.Distance.COSINE,
                ),
            )

    def _get_vector_store(self):
        if not self._is_configured():
            return None

        if self.vector_store is None:
            from langchain_qdrant import QdrantVectorStore

            self.vector_store = QdrantVectorStore.from_existing_collection(
                embedding=FastEmbedEmbeddings(self),
                collection_name=settings.QDRANT_COLLECTION,
                url=settings.QDRANT_URL,
                api_key=settings.QDRANT_API_KEY,
                content_payload_key="text",
                metadata_payload_key="metadata",
            )

        return self.vector_store

    def get_retriever(self, top_k=5):
        store = self._get_vector_store()

        if store is None:
            return None

        return store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": top_k},
        )

    def retrieve_documents(self, question: str, top_k=5):
        retriever = self.get_retriever(top_k)

        if retriever is None:
            logger.warning("Qdrant is not configured")
            return []

        return retriever.invoke(question)

    def retrieve_context(self, question: str, top_k=5):
        documents = self.retrieve_documents(question, top_k)

        return "\n\n---\n\n".join(
            document.page_content for document in documents
        )

    async def upsert_item(self, item: Dict[str, Any]):
        if not self._is_configured():
            logger.warning("Qdrant is not configured")
            return

        from qdrant_client.http import models

        text = self._make_text(item)
        vector = self._embed(text)

        self._create_collection(len(vector))

        self._get_client().upsert(
            collection_name=settings.QDRANT_COLLECTION,
            points=[
                models.PointStruct(
                    id=self._get_point_id(item["id"]),
                    vector=vector,
                    payload={
                        "inventory_id": item["id"],
                        "name": item.get("name"),
                        "quantity_available": item.get(
                            "quantity_available", 0
                        ),
                        "status": item.get("status"),
                        "text": text,
                    },
                )
            ],
        )

    async def delete_item(self, item_id: str):
        if not self._is_configured():
            return

        from qdrant_client.http import models

        self._get_client().delete(
            collection_name=settings.QDRANT_COLLECTION,
            points_selector=models.PointIdsList(
                points=[self._get_point_id(item_id)]
            ),
        )

    async def sync_all(self, items: List[Dict[str, Any]]):
        if not self._is_configured():
            logger.info("Qdrant is not configured")
            return

        for item in items:
            await self.upsert_item(item)

        current_ids = {
            self._get_point_id(item["id"])
            for item in items
        }

        points, _ = self._get_client().scroll(
            collection_name=settings.QDRANT_COLLECTION,
            limit=10000,
            with_payload=False,
            with_vectors=False,
        )

        old_ids = [
            point.id
            for point in points
            if str(point.id) not in current_ids
        ]

        if old_ids:
            from qdrant_client.http import models

            self._get_client().delete(
                collection_name=settings.QDRANT_COLLECTION,
                points_selector=models.PointIdsList(points=old_ids),
            )

        logger.info("Synced %d inventory items", len(items))


inventory_rag_service = InventoryRagService()