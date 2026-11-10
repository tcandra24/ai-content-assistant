from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.dependencies import CurrentUser, DbSession, OwnedIdea
from app.models import Idea
from app.schemas import (
    IdeaCreate,
    IdeaDetail,
    IdeaPage,
    IdeaRead,
    IdeaStatus,
    IdeaUpdate,
    Platform,
)

router = APIRouter(prefix="/ideas", tags=["ideas"])


@router.get("", response_model=IdeaPage)
async def list_ideas(
    db: DbSession,
    current_user: CurrentUser,
    status_filter: Annotated[IdeaStatus | None, Query(alias="status")] = None,
    platform: Platform | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    filters = [Idea.user_id == current_user.id]
    if status_filter:
        filters.append(Idea.status == status_filter)
    if platform:
        filters.append(Idea.platform == platform)

    total = await db.scalar(select(func.count()).select_from(Idea).where(*filters))
    result = await db.scalars(
        select(Idea)
        .where(*filters)
        .order_by(Idea.created_at.desc(), Idea.id.desc())
        .limit(limit)
        .offset(offset)
    )
    return {"items": result.all(), "total": total, "limit": limit, "offset": offset}


@router.post("", response_model=IdeaRead, status_code=status.HTTP_201_CREATED)
async def create_idea(payload: IdeaCreate, db: DbSession, current_user: CurrentUser):
    idea = Idea(user_id=current_user.id, **payload.model_dump())
    db.add(idea)
    await db.commit()
    await db.refresh(idea)  # muat created_at/updated_at yang diisi database
    return idea


@router.get("/{idea_id}", response_model=IdeaDetail)
async def get_idea(idea_id: int, db: DbSession, current_user: CurrentUser):
    idea = await db.scalar(
        select(Idea)
        .options(selectinload(Idea.scripts))  # muat relasi secara eksplisit
        .where(Idea.id == idea_id, Idea.user_id == current_user.id)
    )
    if idea is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Ide tidak ditemukan")

    detail = IdeaDetail.model_validate(idea)
    detail.scripts.sort(key=lambda s: s.version)
    return detail


@router.patch("/{idea_id}", response_model=IdeaRead)
async def update_idea(payload: IdeaUpdate, idea: OwnedIdea, db: DbSession):
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        # Hanya description yang boleh dikosongkan (null)
        if value is None and field != "description":
            continue
        setattr(idea, field, value)

    await db.commit()
    await db.refresh(idea)
    return idea


@router.delete("/{idea_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_idea(idea: OwnedIdea, db: DbSession):
    await db.delete(idea)  # naskah dan riwayat generate ikut terhapus (cascade)
    await db.commit()
    