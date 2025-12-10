"""Authentication related data models."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    """
    Base user model with common attributes.

    Attributes:
        username: Unique username for authentication.
        email: User's email address (validated format).
        full_name: Optional full name of the user.
    """

    username: str
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """
    User creation model with password.

    Extends UserBase with password field for user registration.

    Attributes:
        password: Plain text password (will be hashed before storage).
    """

    password: str


class UserResponse(UserBase):
    """
    User response model for API responses.

    Extends UserBase with additional fields returned from API.
    Excludes sensitive information like password hash.

    Attributes:
        id: Unique user identifier.
        is_active: Whether the user account is active.
        is_admin: Whether the user has admin privileges.
        created_at: Timestamp when user was created.
    """

    id: str
    is_active: bool
    is_admin: bool
    created_at: datetime


class UserInDB(UserBase):
    """
    User model for database storage.

    Complete user model including hashed password and metadata.
    Used internally for authentication and authorization.

    Attributes:
        id: Unique user identifier.
        hashed_password: Bcrypt hashed password.
        is_active: Account active status.
        is_admin: Admin privilege flag.
        created_at: Account creation timestamp.
    """

    id: str
    hashed_password: str
    is_active: bool
    is_admin: bool
    created_at: datetime


class Token(BaseModel):
    """
    JWT token response model.

    Contains both access and refresh tokens returned after successful login.

    Attributes:
        access_token: Short-lived JWT for API authentication (30 min).
        refresh_token: Long-lived JWT for token refresh (7 days).
        token_type: Token type, always "bearer".
    """

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """
    Decoded JWT token data.

    Contains claims extracted from validated JWT token.

    Attributes:
        username: Username from token subject claim.
        user_id: User ID from token custom claim.
    """

    username: Optional[str] = None
    user_id: Optional[str] = None


class LoginRequest(BaseModel):
    """
    Login request model.

    Contains credentials required for user authentication.

    Attributes:
        username: Username for authentication.
        password: Plain text password for verification.
    """

    username: str
    password: str


class RefreshTokenRequest(BaseModel):
    """
    Token refresh request model.

    Contains refresh token for obtaining new access token.

    Attributes:
        refresh_token: Valid refresh token string.
    """

    refresh_token: str
