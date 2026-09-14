import asyncio
import logging
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.core.config import settings

logger = logging.getLogger(__name__)


class Database:
    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None
    _loop: Optional[asyncio.AbstractEventLoop] = None


db_manager = Database()


def get_database() -> AsyncIOMotorDatabase:
    """Returns the current MongoDB database instance, reconnecting if event loop changed."""
    try:
        current_loop = asyncio.get_running_loop()
    except RuntimeError:
        current_loop = None

    if db_manager.client is None or (current_loop is not None and db_manager._loop != current_loop):
        clean_url = settings.clean_mongo_url
        db_manager.client = AsyncIOMotorClient(
            clean_url,
            serverSelectionTimeoutMS=5000
        )
        db_manager.db = db_manager.client[settings.DB_NAME]
        db_manager._loop = current_loop
    return db_manager.db


async def connect_to_mongo():
    """Establishes connection to MongoDB and initializes collections."""
    get_database()
    
    await db_manager.client.admin.command("ping")
    logger.info(f"Successfully connected to MongoDB database: {settings.DB_NAME}")
   
    await init_db_indexes()


async def close_mongo_connection():
    """Closes MongoDB connection."""
    if db_manager.client:
        logger.info("Closing MongoDB connection...")
        db_manager.client.close()
        db_manager.client = None
        db_manager.db = None
        db_manager._loop = None
        logger.info("MongoDB connection closed.")


async def init_db_indexes():
    """Creates unique indexes for the users collection."""
    db = get_database()
    users_col = db["users"]
    
    await users_col.create_index("email", unique=True, name="uniq_email_idx")
    await users_col.create_index("username", unique=True, name="uniq_username_idx")
    await users_col.create_index("phone_number", unique=True, name="uniq_phone_idx")

    await db["admin_chat_messages"].create_index(
        [("admin_id", 1), ("conversation_id", 1), ("created_at", 1)],
        name="admin_conversation_history_idx",
    )
    
    logger.info("Users collection unique indexes successfully ensured.")
