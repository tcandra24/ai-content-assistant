from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.concurrency import run_in_threadpool
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.dependencies import CurrentUser, DbSession
from app.models import User
from app.schemas import Token, UserCreate, UserRead
from app.security import (
    DUMMY_HASH,
    create_access_token,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, db: DbSession):
    email = payload.email.lower()

    existing = await db.scalar(select(User).where(User.email == email))
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Email sudah terdaftar")

    # Hashing argon2 itu CPU-bound (memblokir), jadi dilempar ke threadpool
    hashed = await run_in_threadpool(hash_password, payload.password)
    user = User(email=email, password_hash=hashed)
    db.add(user)

    try:
        await db.commit()
    except IntegrityError:  # dua request bersamaan dengan email yang sama
        await db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Email sudah terdaftar")

    await db.refresh(user)  # muat created_at yang diisi oleh database
    return user


@router.post("/login", response_model=Token)
async def login(
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: DbSession,
):
    # OAuth2 mewajibkan nama field "username"; di sini isinya email
    user = await db.scalar(select(User).where(User.email == form.username.lower()))

    hash_to_check = user.password_hash if user else DUMMY_HASH
    valid = await run_in_threadpool(verify_password, form.password, hash_to_check)

    if user is None or not valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email atau password salah",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return Token(access_token=create_access_token(user.id))


@router.get("/me", response_model=UserRead)
async def me(current_user: CurrentUser):
    return current_user
