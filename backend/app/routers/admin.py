from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Optional

from ..database import get_db
from ..models import User
from ..schemas.auth import UserOut
from ..auth.bypass import get_user_dependency, require_admin_dependency
get_current_user = get_user_dependency()
require_admin = require_admin_dependency()

router = APIRouter(
    prefix="/admin/users",
    tags=["admin"],
    dependencies=[Depends(require_admin)],
)


class UserUpdate(BaseModel):
    role: Optional[str] = Field(default=None, pattern="^(admin|staff)$")
    is_active: Optional[bool] = None


@router.get("/", response_model=list[UserOut])
def list_users(
    search: Optional[str] = Query(None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    q = db.query(User)
    if search:
        q = q.filter(User.email.ilike(f"%{search}%"))
    return q.order_by(User.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.id == current_user.id:
        # Admins may not demote themselves or deactivate themselves
        if payload.role is not None and payload.role != current_user.role:
            raise HTTPException(status_code=400, detail="Cannot change your own role")
        if payload.is_active is False:
            raise HTTPException(status_code=400, detail="Cannot deactivate your own account")

    if payload.role is not None:
        user.role = payload.role
    if payload.is_active is not None:
        user.is_active = payload.is_active

    db.commit()
    db.refresh(user)
    return user
