# ============================================================================
# FILE: src/utils/dependencies.py (NEW)
# ============================================================================
"""FastAPI dependencies for authentication."""

from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.models.auth import UserInDB
from backend.services.auth_service import AuthService

# Security scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> UserInDB:
    """
    Dependency to get current authenticated user.

    Args:
        credentials: Bearer token from request header

    Returns:
        UserInDB object

    Raises:
        HTTPException: If token is invalid
    """
    token = credentials.credentials

    token_data = AuthService.verify_token(token, token_type="access")

    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = AuthService.get_user_by_username(token_data.username)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )

    return user


async def get_current_active_user(
    current_user: UserInDB = Depends(get_current_user),
) -> UserInDB:
    """
    Dependency to get current active user.

    Args:
        current_user: Current user from get_current_user

    Returns:
        UserInDB object

    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )
    return current_user


async def get_current_admin_user(
    current_user: UserInDB = Depends(get_current_active_user),
) -> UserInDB:
    """
    Dependency to verify user is admin.

    Args:
        current_user: Current active user

    Returns:
        UserInDB object

    Raises:
        HTTPException: If user is not admin
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
        )
    return current_user


def optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    ),
) -> Optional[UserInDB]:
    """
    Dependency for optional authentication.

    Args:
        credentials: Optional bearer token

    Returns:
        UserInDB object or None
    """
    if not credentials:
        return None

    token = credentials.credentials
    token_data = AuthService.verify_token(token, token_type="access")

    if token_data is None:
        return None

    user = AuthService.get_user_by_username(token_data.username)
    return user
