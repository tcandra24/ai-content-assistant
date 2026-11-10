from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

GenerationKind = Literal["hook", "script", "caption", "video_prompt"]


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

class VideoClip(BaseModel):
    clip_number: int = Field(ge=1, description="Nomor urut klip, mulai dari 1")
    prompt: str = Field(
        description=(
            "Prompt video dalam bahasa Inggris, siap ditempel ke tool AI video. "
            "Memuat subjek, aksi, lingkungan, pencahayaan, dan gaya sinematik, "
            "serta mengulang deskripsi karakter agar konsisten antar klip"
        )
    )
    camera_motion: str = Field(
        description="Gerak kamera, misalnya slow dolly in, static shot, atau tracking shot"
    )
    duration_seconds: int = Field(
        ge=1, le=10, description="Durasi klip dalam detik, umumnya 5 sampai 10"
    )
    negative_prompt: str | None = Field(
        default=None, description="Hal yang harus dihindari pada klip ini"
    )


class VideoPromptOutput(BaseModel):
    style_guide: str = Field(
        description=(
            "Panduan gaya visual global (palet warna, pencahayaan, mood, deskripsi "
            "karakter utama) yang berlaku untuk semua klip"
        )
    )
    clips: list[VideoClip] = Field(min_length=1, max_length=20)


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