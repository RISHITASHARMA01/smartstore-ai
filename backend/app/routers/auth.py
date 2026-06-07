from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User, LoginAttempt, TokenBlocklist, AuditLog
from ..schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserOut,
    RefreshRequest,
)
from ..auth.utils import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from ..auth.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])

# Lockout policy
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_WINDOW_MINUTES = 15


def _get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _check_lockout(email: str, db: Session) -> None:
    """Raise 429 if the account has too many recent failed logins."""
    window_start = datetime.now(timezone.utc) - timedelta(minutes=LOCKOUT_WINDOW_MINUTES)
    failed = (
        db.query(LoginAttempt)
        .filter(
            LoginAttempt.email == email,
            LoginAttempt.success == False,
            LoginAttempt.attempted_at >= window_start,
        )
        .count()
    )
    if failed >= MAX_FAILED_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Account temporarily locked. Too many failed login attempts. "
                   f"Try again in {LOCKOUT_WINDOW_MINUTES} minutes.",
        )


def _record_attempt(email: str, ip: str, success: bool, db: Session) -> None:
    db.add(LoginAttempt(email=email, ip_address=ip, success=success))
    db.commit()


def _audit(user_id, action: str, ip: str, db: Session, resource_type=None, resource_id=None, details=None):
    db.add(AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        ip_address=ip,
        details=details,
    ))
    db.commit()


@router.post("/register", response_model=UserOut, status_code=201)
def register(payload: RegisterRequest, request: Request, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    user = User(
        email=payload.email,
        password=hash_password(payload.password),
        role=payload.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    _audit(user.id, "register", _get_client_ip(request), db, "user", user.id)
    return user


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    ip = _get_client_ip(request)

    # Check lockout before touching the DB for user lookup
    _check_lockout(payload.email, db)

    user = (
        db.query(User)
        .filter(User.email == payload.email, User.is_active == True)
        .first()
    )
    if not user or not verify_password(payload.password, user.password):
        _record_attempt(payload.email, ip, False, db)
        _audit(None, "failed_login", ip, db, details={"email": payload.email})
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    _record_attempt(payload.email, ip, True, db)
    _audit(user.id, "login", ip, db, "user", user.id)

    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
        user=UserOut.model_validate(user),
    )


@router.post("/logout", status_code=200)
def logout(request: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Revoke the current access token so it can't be reused after logout."""
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.removeprefix("Bearer ").strip()
    if token:
        payload = decode_token(token)
        jti = payload.get("jti")
        exp = payload.get("exp")
        if jti:
            expires_at = datetime.fromtimestamp(exp, tz=timezone.utc) if exp else datetime.now(timezone.utc)
            db.add(TokenBlocklist(jti=jti, expires_at=expires_at))
            db.commit()

    _audit(current_user.id, "logout", _get_client_ip(request), db, "user", current_user.id)
    return {"detail": "Logged out successfully"}


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(payload: RefreshRequest, db: Session = Depends(get_db)):
    data = decode_token(payload.refresh_token)
    if data.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )
    user = (
        db.query(User)
        .filter(User.id == int(data["sub"]), User.is_active == True)
        .first()
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
        user=UserOut.model_validate(user),
    )
