"""Authentication API routes."""

from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, status

from backend.models.auth import (
    LoginRequest,
    RefreshTokenRequest,
    Token,
    UserCreate,
    UserInDB,
    UserResponse,
)
from backend.services.auth_service import AuthService
from backend.utils.dependencies import get_current_active_user, get_current_admin_user

router = APIRouter()


@router.post("/login", response_model=Token)
async def login(login_request: LoginRequest):
    """
    Login endpoint - authenticate user and return tokens.

    Args:
        login_request: Username and password

    Returns:
        Access token and refresh token
    """
    user = AuthService.authenticate_user(login_request.username, login_request.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )

    tokens = AuthService.create_tokens(user)

    return Token(**tokens)


@router.post("/refresh", response_model=Dict[str, str])
async def refresh_token(refresh_request: RefreshTokenRequest):
    """
    Refresh access token using refresh token.

    Args:
        refresh_request: Refresh token

    Returns:
        New access token
    """
    new_access_token = AuthService.refresh_access_token(refresh_request.refresh_token)

    if not new_access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {"access_token": new_access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: UserInDB = Depends(get_current_active_user),
):
    """
    Get current user information.

    Returns:
        Current user details
    """
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        is_admin=current_user.is_admin,
        created_at=current_user.created_at,
    )


@router.post("/register", response_model=UserResponse)
async def register_user(
    user_create: UserCreate,
    _: UserInDB = Depends(get_current_admin_user),  # Only admins can create users
):
    """
    Register a new user (Admin only).

    Args:
        user_create: User creation data

    Returns:
        Created user details
    """
    try:
        user = AuthService.create_user(user_create)
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            is_admin=user.is_admin,
            created_at=user.created_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.post("/logout")
async def logout(current_user: UserInDB = Depends(get_current_active_user)):
    """
    Logout endpoint (client should discard token).

    Returns:
        Success message
    """
    return {"message": "Successfully logged out", "username": current_user.username}
