# auth/dependencies.py

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from database.connection import get_db
from database.models import User, UserRole
from auth.jwt_handler import decode_access_token
import logging

logger = logging.getLogger(__name__)

# ── OAuth2 scheme ─────────────────────────────────────────────
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Decodes JWT token and returns the current authenticated User.
    Raises 401 if token is invalid or user not found.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials. Please log in again.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(token)
    if payload is None:
        logger.warning("Invalid or expired token received")
        raise credentials_exception

    email = payload.get("sub")
    if email is None:
        logger.warning("Token missing 'sub' field")
        raise credentials_exception

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        logger.warning(f"Token valid but user not found: {email}")
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive. Contact administrator."
        )

    return user


def require_patient(
    current_user: User = Depends(get_current_user)
) -> User:
    """Enforces patient role."""
    if current_user.role != UserRole.patient:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"Access denied. Patient role required. "
                f"Your role: {current_user.role.value}"
            )
        )
    return current_user


def require_staff(
    current_user: User = Depends(get_current_user)
) -> User:
    """Enforces staff or admin role."""
    if current_user.role not in [UserRole.staff, UserRole.admin]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"Access denied. Staff or Admin role required. "
                f"Your role: {current_user.role.value}"
            )
        )
    return current_user


def require_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """Enforces admin-only role."""
    if current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"Access denied. Admin role required. "
                f"Your role: {current_user.role.value}"
            )
        )
    return current_user

def require_doctor(
    current_user: User = Depends(get_current_user)
) -> User:
    """Enforces doctor role."""
    if current_user.role != UserRole.doctor:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"Access denied. Doctor role required. "
                f"Your role: {current_user.role.value}"
            )
        )
    return current_user


def require_authenticated(
    current_user: User = Depends(get_current_user)
) -> User:
    """Any authenticated user."""
    return current_user


def get_optional_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Returns the current user if token is valid, else None.
    """
    try:
        return get_current_user(token=token, db=db)
    except HTTPException:
        return None