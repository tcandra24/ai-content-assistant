from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import DbSession, OwnedIdea
from app.models import Script
from app.schemas import ScriptCreate, ScriptRead, ScriptUpdate

router = APIRouter(prefix="/ideas/{idea_id}/scripts", tags=["scripts"])


async def get_script_or_404(db: AsyncSession, idea_id: int, script_id: int) -> Script:
    script = await db.scalar(
        select(Script).where(Script.id == script_id, Script.idea_id == idea_id)
    )
    if script is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Naskah tidak ditemukan")
    return script


@router.get("", response_model=list[ScriptRead])
async def list_scripts(idea: OwnedIdea, db: DbSession):
    result = await db.scalars(
        select(Script).where(Script.idea_id == idea.id).order_by(Script.version)
    )
    return result.all()


@router.post("", response_model=ScriptRead, status_code=status.HTTP_201_CREATED)
async def create_script(payload: ScriptCreate, idea: OwnedIdea, db: DbSession):
    last_version = await db.scalar(
        select(func.max(Script.version)).where(Script.idea_id == idea.id)
    )
    script = Script(
        idea_id=idea.id,
        content=payload.content,
        version=(last_version or 0) + 1,
    )
    db.add(script)

    try:
        await db.commit()
    except IntegrityError:  # dua request bersamaan mendapat nomor versi yang sama
        await db.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT, detail="Versi bentrok, silakan coba lagi"
        )

    await db.refresh(script)
    return script


@router.get("/{script_id}", response_model=ScriptRead)
async def get_script(script_id: int, idea: OwnedIdea, db: DbSession):
    return await get_script_or_404(db, idea.id, script_id)


@router.patch("/{script_id}", response_model=ScriptRead)
async def update_script(
    script_id: int, payload: ScriptUpdate, idea: OwnedIdea, db: DbSession
):
    script = await get_script_or_404(db, idea.id, script_id)

    if payload.is_final:
        # Hanya satu naskah final per ide
        await db.execute(
            update(Script)
            .where(Script.idea_id == idea.id, Script.id != script.id)
            .values(is_final=False)
        )

    script.is_final = payload.is_final
    await db.commit()
    await db.refresh(script)
    return script


@router.delete("/{script_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_script(script_id: int, idea: OwnedIdea, db: DbSession):
    script = await get_script_or_404(db, idea.id, script_id)
    await db.delete(script)
    await db.commit()