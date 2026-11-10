from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

GenerationKind = Literal["hook", "script", "caption"]


# ---------- Bentuk output yang dipaksakan ke AI ----------
class HookOutput(BaseModel):
    hooks: list[str] = Field(
        min_length=3,
        max_length=5,
        description="Kalimat pembuka untuk 1-3 detik pertama video, masing-masing dengan gaya berbeda",
    )


class Scene(BaseModel):
    visual: str = Field(description="Deskripsi visual adegan secara sinematik")
    narration: str = Field(description="Teks narasi yang diucapkan pada adegan ini")
    duration_seconds: int = Field(ge=1, le=30, description="Durasi adegan dalam detik")


class ScriptOutput(BaseModel):
    title: str = Field(description="Judul video yang menarik")
    scenes: list[Scene] = Field(min_length=3, max_length=10)


class CaptionOutput(BaseModel):
    caption: str = Field(description="Caption siap posting, tanpa hashtag")
    hashtags: list[str] = Field(
        min_length=3,
        max_length=10,
        description="Hashtag relevan, masing-masing diawali tanda #",
    )


# ---------- Request dan response API ----------
class GenerateRequest(BaseModel):
    kind: GenerationKind
    extra_instructions: str | None = Field(default=None, max_length=1000)


class GenerationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    idea_id: int
    kind: GenerationKind
    output: dict
    model: str
    created_at: datetime
    