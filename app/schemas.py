from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

Platform = Literal["tiktok", "reels", "shorts"]
IdeaStatus = Literal["draft", "in_progress", "done"]


# ---------- Auth ----------
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---------- Script ----------
class ScriptCreate(BaseModel):
    content: str = Field(min_length=1, max_length=20000)


class ScriptUpdate(BaseModel):
    is_final: bool


class ScriptRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    idea_id: int
    content: str
    version: int
    is_final: bool
    created_at: datetime


# ---------- Idea ----------
class IdeaCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    platform: Platform
    status: IdeaStatus = "draft"


class IdeaUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    platform: Platform | None = None
    status: IdeaStatus | None = None


class IdeaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    platform: Platform
    status: IdeaStatus
    created_at: datetime
    updated_at: datetime


class IdeaDetail(IdeaRead):
    scripts: list[ScriptRead] = []


class IdeaPage(BaseModel):
    items: list[IdeaRead]
    total: int
    limit: int
    offset: int