from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Idea, User
from app.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

DbSession = Annotated[AsyncSession, Depends(get_db)]


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: DbSession,
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token tidak valid atau sudah kedaluwarsa",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        user_id = int(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError):
        raise credentials_exception

    user = await db.get(User, user_id)
    if user is None:
        raise credentials_exception
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def get_owned_idea(
    idea_id: int,
    db: DbSession,
    current_user: CurrentUser,
) -> Idea:
    """Ambil ide berdasarkan idea_id di path, hanya jika milik user yang login."""
    idea = await db.scalar(
        select(Idea).where(Idea.id == idea_id, Idea.user_id == current_user.id)
    )
    if idea is None:
        # 404 (bukan 403) agar keberadaan ide milik orang lain tidak bocor
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Ide tidak ditemukan")
    return idea


OwnedIdea = Annotated[Idea, Depends(get_owned_idea)]