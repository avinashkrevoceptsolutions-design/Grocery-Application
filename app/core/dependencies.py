from typing import Any, Callable, Dict, List, Union
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.domain.Users.schemas import UserRole
from app.core.security import decode_access_token
from app.repositarys.user_repository import user_repository

security = HTTPBearer(auto_error=False)


async def get_current_user( credentials: HTTPAuthorizationCredentials = Security(security)) -> Dict[str, Any]:
    """
    Extracts and validates the Bearer JWT token from the Authorization header.
    Returns the user document from the database.
    """
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token is missing",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub") or payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await user_repository.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User associated with token no longer exists",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def require_role(allowed_roles: Union[UserRole, List[UserRole]]) -> Callable:
    """
    Factory that returns a dependency ensuring the current user has one of the allowed roles.
    Raises HTTP 403 Forbidden if user lacks sufficient privileges.
    """
    if isinstance(allowed_roles, UserRole):
        allowed_roles = [allowed_roles]
    
    role_values = [r.value for r in allowed_roles]

    async def role_checker(current_user: Dict[str, Any] = Depends(get_current_user) ) -> Dict[str, Any]:
        user_role = current_user.get("role")
        if user_role not in role_values:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Requires one of roles: {', '.join(role_values)}. Current role: {user_role}"
            )
        return current_user

    return role_checker



require_admin = require_role(UserRole.ADMIN)
require_customer = require_role(UserRole.CUSTOMER)
require_inventory_access = require_role([UserRole.ADMIN, UserRole.CUSTOMER])
