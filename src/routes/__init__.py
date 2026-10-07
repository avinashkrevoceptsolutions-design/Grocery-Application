from src.routes.auth_routes import router as auth_router
from src.routes.password_reset_routes import router as password_reset_router

__all__ = ["auth_router", "password_reset_router"]
