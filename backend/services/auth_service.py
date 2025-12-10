# ============================================================================
# FILE: src/services/auth_service.py
# ============================================================================
"""Authentication and authorization service."""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from backend.config.settings import settings
from backend.models.auth import TokenData, UserCreate, UserInDB


class AuthService:
    """Service for authentication and user management."""

    # Password hashing context with bcrypt compatibility fixes
    _pwd_context = CryptContext(
        schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12, bcrypt__ident="2b"
    )

    # Users storage file
    _users_file = Path("users.json")

    @staticmethod
    def _ensure_users_file():
        """Private: Ensure users file exists with admin user."""
        if not AuthService._users_file.exists():
            # Truncate password to 72 bytes for bcrypt compatibility
            admin_password = settings.ADMIN_PASSWORD
            if len(admin_password.encode("utf-8")) > 72:
                admin_password = admin_password.encode("utf-8")[:72].decode(
                    "utf-8", errors="ignore"
                )

            admin_user = {
                "id": "admin_001",
                "username": settings.ADMIN_USERNAME,
                "email": settings.ADMIN_EMAIL,
                "full_name": "Administrator",
                "hashed_password": AuthService._get_password_hash(admin_password),
                "is_active": True,
                "is_admin": True,
                "created_at": datetime.now().isoformat(),
            }

            users_data = {settings.ADMIN_USERNAME: admin_user}

            with open(AuthService._users_file, "w", encoding="utf-8") as f:
                json.dump(users_data, f, indent=2)

    @staticmethod
    def _load_users() -> Dict:
        """Private: Load users from file."""
        AuthService._ensure_users_file()
        with open(AuthService._users_file, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def _save_users(users_data: Dict):
        """Private: Save users to file."""
        with open(AuthService._users_file, "w", encoding="utf-8") as f:
            json.dump(users_data, f, indent=2)

    @staticmethod
    def _get_password_hash(password: str) -> str:
        """
        Private: Hash a password.
        Bcrypt has a 72-byte limit, so we truncate if needed.
        """
        # Ensure password is within bcrypt's 72-byte limit
        password_bytes = password.encode("utf-8")
        if len(password_bytes) > 72:
            password = password_bytes[:72].decode("utf-8", errors="ignore")

        return AuthService._pwd_context.hash(password)

    @staticmethod
    def _verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Private: Verify a password against its hash.
        Truncates password to 72 bytes for bcrypt compatibility.
        """
        # Ensure password is within bcrypt's 72-byte limit
        password_bytes = plain_password.encode("utf-8")
        if len(password_bytes) > 72:
            plain_password = password_bytes[:72].decode("utf-8", errors="ignore")

        return AuthService._pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def _create_access_token(
        data: dict, expires_delta: Optional[timedelta] = None
    ) -> str:
        """Private: Create JWT access token."""
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
            )

        to_encode.update({"exp": expire, "type": "access"})

        encoded_jwt = jwt.encode(
            to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
        )

        return encoded_jwt

    @staticmethod
    def _create_refresh_token(data: dict) -> str:
        """Private: Create JWT refresh token."""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(
            days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
        )

        to_encode.update({"exp": expire, "type": "refresh"})

        encoded_jwt = jwt.encode(
            to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
        )

        return encoded_jwt

    @staticmethod
    def authenticate_user(username: str, password: str) -> Optional[UserInDB]:
        """
        Public: Authenticate a user with username and password.

        Args:
            username: Username
            password: Plain text password

        Returns:
            UserInDB object or None
        """
        users = AuthService._load_users()

        if username not in users:
            return None

        user_data = users[username]

        if not AuthService._verify_password(password, user_data["hashed_password"]):
            return None

        return UserInDB(**user_data)

    @staticmethod
    def create_tokens(user: UserInDB) -> Dict[str, str]:
        """
        Public: Create access and refresh tokens for a user.

        Args:
            user: UserInDB object

        Returns:
            Dictionary with access_token and refresh_token
        """
        token_data = {"sub": user.username, "user_id": user.id, "email": user.email}

        access_token = AuthService._create_access_token(token_data)
        refresh_token = AuthService._create_refresh_token(token_data)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    @staticmethod
    def verify_token(token: str, token_type: str = "access") -> Optional[TokenData]:
        """
        Public: Verify and decode a JWT token.

        Args:
            token: JWT token string
            token_type: Type of token (access or refresh)

        Returns:
            TokenData object or None
        """
        try:
            payload = jwt.decode(
                token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
            )

            # Check token type
            if payload.get("type") != token_type:
                return None

            username: str = payload.get("sub")
            user_id: str = payload.get("user_id")

            if username is None:
                return None

            return TokenData(username=username, user_id=user_id)

        except JWTError:
            return None

    @staticmethod
    def get_user_by_username(username: str) -> Optional[UserInDB]:
        """
        Public: Get user by username.

        Args:
            username: Username

        Returns:
            UserInDB object or None
        """
        users = AuthService._load_users()

        if username not in users:
            return None

        return UserInDB(**users[username])

    @staticmethod
    def create_user(user_create: UserCreate) -> UserInDB:
        """
        Public: Create a new user.

        Args:
            user_create: UserCreate object

        Returns:
            UserInDB object
        """
        users = AuthService._load_users()

        if user_create.username in users:
            raise ValueError("Username already exists")

        user_id = f"user_{int(datetime.now().timestamp())}"

        user_data = {
            "id": user_id,
            "username": user_create.username,
            "email": user_create.email,
            "full_name": user_create.full_name,
            "hashed_password": AuthService._get_password_hash(user_create.password),
            "is_active": True,
            "is_admin": False,
            "created_at": datetime.now().isoformat(),
        }

        users[user_create.username] = user_data
        AuthService._save_users(users)

        return UserInDB(**user_data)

    @staticmethod
    def refresh_access_token(refresh_token: str) -> Optional[str]:
        """
        Public: Create new access token from refresh token.

        Args:
            refresh_token: Refresh token string

        Returns:
            New access token or None
        """
        token_data = AuthService.verify_token(refresh_token, token_type="refresh")

        if not token_data:
            return None

        # Get user
        user = AuthService.get_user_by_username(token_data.username)

        if not user:
            return None

        # Create new access token
        new_token_data = {"sub": user.username, "user_id": user.id, "email": user.email}

        return AuthService._create_access_token(new_token_data)
