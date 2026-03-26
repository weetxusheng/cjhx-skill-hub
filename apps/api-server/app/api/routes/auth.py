from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_current_user, get_db
from app.core.config import get_settings
from app.core.rate_limit import enforce_rate_limit
from app.models.user import User
from app.schemas.auth import LoginRequest, LogoutRequest, RefreshRequest
from app.schemas.common import success_response
from app.services.auth import authenticate_user, build_user_summary, issue_tokens, refresh_tokens, revoke_refresh_token

router = APIRouter()
settings = get_settings()


@router.post("/login")
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)) -> dict:
    client_host = request.client.host if request.client else "anonymous"
    enforce_rate_limit(scope="auth-login", actor_key=f"{client_host}:{payload.username}", rule_raw=settings.login_rate_limit)
    user = authenticate_user(db, payload.username, payload.password)
    access_token, refresh_token = issue_tokens(db, user)
    return success_response(
        {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": build_user_summary(db, user).model_dump(mode="json"),
        }
    )


@router.post("/refresh")
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)) -> dict:
    user, access_token, refresh_token = refresh_tokens(db, payload.refresh_token)
    return success_response(
        {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": build_user_summary(db, user).model_dump(mode="json"),
        }
    )


@router.post("/logout")
def logout(payload: LogoutRequest, db: Session = Depends(get_db)) -> dict:
    revoke_refresh_token(db, payload.refresh_token)
    return success_response({"logged_out": True})


@router.get("/me")
def me(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    user = db.execute(select(User).where(User.id == current_user.id)).scalar_one()
    return success_response(build_user_summary(db, user).model_dump(mode="json"))
