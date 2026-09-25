import logging
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.database.connection import connect_to_mongo, close_mongo_connection
from app.database.seed import seed_startup_data
from app.api.V1.router import api_v1_router
from app.repositarys.inventory_repository import inventory_repository
from app.services.inventory_rag_service import inventory_rag_service

class ExpiringFileHandler(logging.FileHandler):
    """Delete the active log file once it has reached the retention period."""

    def __init__(self, filename, retention_seconds=24 * 60 * 60, **kwargs):
        self.retention_seconds = retention_seconds
        super().__init__(filename, **kwargs)

    def emit(self, record):
        self.acquire()
        try:
            if (
                self.stream is not None
                and Path(self.baseFilename).exists()
                and time.time() - Path(self.baseFilename).stat().st_mtime
                >= self.retention_seconds
            ):
                self.close()
                Path(self.baseFilename).unlink(missing_ok=True)
                self.stream = self._open()

            super().emit(record)
        finally:
            self.release()


# Configure logging
log_dir = Path(__file__).resolve().parent.parent / "logs"
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s",
    handlers=[
        logging.StreamHandler(),
        ExpiringFileHandler(log_dir / "app.log", encoding="utf-8")
    ]
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager:
    - Connects to MongoDB
    - Ensures user unique indexes
    - Seeds startup data idempotently (1 Admin, 2 Customers)
    - Gracefully closes connections on shutdown
    """
    logger.info("Starting up Authentication & Authorization API...")
    try:
        await connect_to_mongo()
        await seed_startup_data()
        await inventory_rag_service.sync_all(
            await inventory_repository.list_all_items()
        )
    except Exception as e:
        logger.error(f"Error during startup initialization: {e}", exc_info=True)
        raise e

    yield

    logger.info("Shutting down Authentication & Authorization API...")
    await close_mongo_connection()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(api_v1_router, prefix=settings.API_V1_STR)




if __name__ == "__main__":
    import uvicorn
    uvicorn.run("App.main:app", host="0.0.0.0", port=8000, reload=True)
