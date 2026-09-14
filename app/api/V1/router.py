from fastapi import APIRouter
from app.api.auth.routes import router as auth_router
from app.api.admin.routes import router as admin_router
from app.api.admin.chat_routes import router as admin_chat_router
from app.api.inventory.routes import router as inventory_router
from app.api.cart.routes import router as cart_router
from app.api.orders.routes import router as orders_router
from app.api.email.routes import router as email_router
api_v1_router = APIRouter()

api_v1_router.include_router(auth_router)
api_v1_router.include_router(admin_router)
api_v1_router.include_router(admin_chat_router)
api_v1_router.include_router(inventory_router)
api_v1_router.include_router(cart_router)
api_v1_router.include_router(orders_router)
# api_v1_router.include_router(email_router)
