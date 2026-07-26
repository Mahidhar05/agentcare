# auth/jwt_handler.py

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from config import settings
import logging

logger = logging.getLogger(__name__)


# ── Create Access Token ───────────────────────────────────────
def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Creates a signed JWT access token.

    Args:
        data: payload dict — must include 'sub' (subject = user email)
        expires_delta: optional custom expiry duration

    Returns:
        Signed JWT token string
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),        # issued at
        "iss": settings.APP_NAME,        # issuer
    })

    try:
        encoded_jwt = jwt.encode(
            to_encode,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
        return encoded_jwt
    except Exception as e:
        logger.error(f"Token creation failed: {e}")
        raise


# ── Decode & Verify Token ─────────────────────────────────────
def decode_access_token(token: str) -> Optional[dict]:
    """
    Decodes and validates a JWT token.

    Returns:
        Payload dict if valid
        None if invalid or expired
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError as e:
        logger.warning(f"Token decode failed: {e}")
        return None


# ── Extract Email from Token ──────────────────────────────────
def get_email_from_token(token: str) -> Optional[str]:
    """
    Extracts the email (subject) from a JWT token.

    Returns:
        Email string if valid
        None if invalid
    """
    payload = decode_access_token(token)
    if payload:
        return payload.get("sub")
    return None


# ── Extract Role from Token ───────────────────────────────────
def get_role_from_token(token: str) -> Optional[str]:
    """
    Extracts the user role from a JWT token.

    Returns:
        Role string if valid
        None if invalid
    """
    payload = decode_access_token(token)
    if payload:
        return payload.get("role")
    return None