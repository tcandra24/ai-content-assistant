from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import engine, get_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await engine.dispose()  # tutup koneksi saat server berhenti


app = FastAPI(title=settings.app_name, lifespan=lifespan)

DbSession = Annotated[AsyncSession, Depends(get_db)]


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/health/db")
async def health_db(db: DbSession):
    result = await db.execute(text("SELECT version()"))
    return {"status": "ok", "postgres": result.scalar_one()}
