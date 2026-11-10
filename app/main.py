from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.database import engine
from app.routers import auth, generate, ideas, scripts


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await engine.dispose()  # tutup koneksi saat server berhenti


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.include_router(auth.router)
app.include_router(ideas.router)
app.include_router(scripts.router)
app.include_router(generate.router)


@app.get("/health")
async def health():
    # Sengaja tidak menyentuh database agar cepat dan tidak gagal karena cold start
    return {"status": "ok"}