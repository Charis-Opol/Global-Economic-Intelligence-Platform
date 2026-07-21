"""
Simple JWT auth (Day 2, Step 7).

One admin credential from env vars - no user table, no registration flow,
no refresh tokens. `POST /auth/login` exchanges that credential for a
short-lived JWT; `get_current_user` is the dependency every other router
(everything except `/health` and `/auth/login` itself) is gated behind - see
`app/main.py` for where it's attached.
"""
from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from app.core.config import settings

router = APIRouter(tags=["auth"])
_bearer_scheme = HTTPBearer(auto_error=False)


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


def create_access_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


@router.post("/auth/login", response_model=TokenResponse)
def login(credentials: LoginRequest) -> TokenResponse:
    # secrets.compare_digest rather than `==`: a plain string comparison
    # leaks how many leading characters matched through response timing.
    valid_username = secrets.compare_digest(credentials.username, settings.auth_admin_username)
    valid_password = secrets.compare_digest(credentials.password, settings.auth_admin_password)
    if not (valid_username and valid_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password"
        )
    return TokenResponse(access_token=create_access_token(credentials.username))


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> str:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = jwt.decode(
            credentials.credentials, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload["sub"]
