from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from pydantic_ai.exceptions import ModelHTTPError, UnexpectedModelBehavior
from sqlalchemy import select

from app.config import settings
from app.dependencies import DbSession, OwnedIdea
from app.models import Generation
from app.schemas_ai import GenerateRequest, GenerationKind, GenerationRead
from app.services.ai import run_generation

router = APIRouter(prefix="/ideas/{idea_id}", tags=["generate"])


@router.post(
    "/generate",
    response_model=GenerationRead,
    status_code=status.HTTP_201_CREATED,
)
async def generate(payload: GenerateRequest, idea: OwnedIdea, db: DbSession):
    # Simpan data yang dibutuhkan ke variabel lokal...
    idea_id = idea.id
    title = idea.title
    description = idea.description
    platform = idea.platform

    # ...lalu lepas koneksi database sebelum menunggu AI (bisa puluhan detik).
    # Aman karena expire_on_commit=False.
    await db.commit()

    try:
        output = await run_generation(
            payload.kind,
            title=title,
            description=description,
            platform=platform,
            extra_instructions=payload.extra_instructions,
        )
    except (ModelHTTPError, UnexpectedModelBehavior):
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            detail="Layanan AI gagal merespons, silakan coba lagi",
        )

    generation = Generation(
        idea_id=idea_id,
        kind=payload.kind,
        output=output,
        model=settings.openrouter_model,
    )
    db.add(generation)
    await db.commit()
    await db.refresh(generation)
    return generation


@router.get("/generations", response_model=list[GenerationRead])
async def list_generations(
    idea: OwnedIdea,
    db: DbSession,
    kind: GenerationKind | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    filters = [Generation.idea_id == idea.id]
    if kind:
        filters.append(Generation.kind == kind)

    result = await db.scalars(
        select(Generation)
        .where(*filters)
        .order_by(Generation.created_at.desc(), Generation.id.desc())
        .limit(limit)
        .offset(offset)
    )
    return result.all()
