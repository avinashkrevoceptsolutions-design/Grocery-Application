from typing import Any, Dict, List
from fastapi import APIRouter, Depends
from app.domain.Users.schemas import UserResponse
from app.core.dependencies import require_admin
from app.repositarys.user_repository import user_repository

router = APIRouter(
    prefix="/admin",
    tags=["Admin Management"],
    dependencies=[Depends(require_admin)]
)


@router.get(
    "/dashboard",
    summary="Admin Dashboard Stats"
)
async def get_dashboard_stats(admin_user: Dict[str, Any] = Depends(require_admin)):
    all_users = await user_repository.list_users(limit=1000)
    admins_count = sum(1 for u in all_users if u.get("role") == "ADMIN")
    customers_count = sum(1 for u in all_users if u.get("role") == "CUSTOMER")
    
    return {
        "message": f"Welcome to Admin Dashboard, {admin_user.get('first_name')}!",
        "stats": {
            "total_users": len(all_users),
            "admin_count": admins_count,
            "customer_count": customers_count
        }
    }


@router.get( "/users", response_model=List[UserResponse], summary="List All Users (Admin Only)"
)
async def list_all_users(
    skip: int = 0,
    limit: int = 50,
    admin_user: Dict[str, Any] = Depends(require_admin)
):
    users = await user_repository.list_users(skip=skip, limit=limit)
    return [UserResponse(**u) for u in users]
