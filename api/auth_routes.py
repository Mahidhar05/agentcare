# api/auth_routes.py

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from database.connection import get_db
from database.models import User
from auth.password import verify_password
from auth.jwt_handler import create_access_token
from tools.patient_tools import register_new_patient
from tools.audit_tools import log_audit_event
from schemas.pydantic_schemas import (
    LoginResponse, RegisterRequest, RegisterResponse
)
from config import settings
import logging

router = APIRouter(prefix="/api/auth", tags=["Authentication"])
logger = logging.getLogger(__name__)


@router.post("/login", response_model=LoginResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """
    Authenticates a user and returns a JWT token.
    Accepts email as username field.
    """
    # Find user by email
    user = db.query(User).filter(
        User.email == form_data.username
    ).first()

    if not user or not verify_password(form_data.password, user.password_hash):
        log_audit_event(
            db=db,
            action="login_failed",
            metadata={"email": form_data.username},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive. Contact administrator.",
        )

    # Create JWT token
    token = create_access_token(
        data={
            "sub":  user.email,
            "role": user.role.value,
            "uid":  user.id,
        },
        expires_delta=timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        ),
    )

    log_audit_event(
        db=db,
        action="login_success",
        actor_id=user.id,
        entity_type="User",
        entity_id=user.id,
        metadata={"email": user.email, "role": user.role.value},
    )

    logger.info(f"[AUTH] Login success: {user.email} [{user.role.value}]")

    return LoginResponse(
        access_token=token,
        token_type="bearer",
        user_id=user.id,
        name=user.name,
        email=user.email,
        role=user.role.value,
    )


@router.post("/register", response_model=RegisterResponse, status_code=201)
def register(
    request: RegisterRequest,
    db: Session = Depends(get_db),
):
    """
    Registers a new patient user.
    Only patient self-registration is allowed here.
    Staff/Admin accounts are created by admins only.
    """
    try:
        result = register_new_patient(
            db=db,
            name=request.name,
            email=request.email,
            password=request.password,
            phone=request.phone,
            date_of_birth=request.date_of_birth,
            age=request.age,
            gender=request.gender,
        )

        logger.info(f"[AUTH] New patient registered: {request.email}")

        return RegisterResponse(
            user_id=result["user_id"],
            profile_id=result["profile_id"],
            name=result["name"],
            email=result["email"],
            role=result["role"],
            message="Registration successful! You can now log in.",
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"[AUTH] Registration failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed. Please try again.",
        )


@router.get("/me")
def get_current_user_info(
    db: Session = Depends(get_db),
    token: str = Depends(
        __import__("fastapi.security", fromlist=["OAuth2PasswordBearer"])
        .OAuth2PasswordBearer(tokenUrl="/api/auth/login")
    ),
):
    """Returns current authenticated user info."""
    from auth.dependencies import get_current_user
    from auth.jwt_handler import decode_access_token

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    email = payload.get("sub")
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "user_id": user.id,
        "name":    user.name,
        "email":   user.email,
        "role":    user.role.value,
    }