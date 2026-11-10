from functools import lru_cache

from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.models.openrouter import OpenRouterModel
from pydantic_ai.providers.openrouter import OpenRouterProvider

from app.config import settings
from app.schemas_ai import CaptionOutput, GenerationKind, HookOutput, ScriptOutput

BASE_INSTRUCTIONS = (
    "Kamu adalah asisten kreator konten video pendek berbahasa Indonesia. "
    "Tulis dengan bahasa Indonesia yang natural, kuat secara visual, dan sesuai platform. "
)

INSTRUCTIONS: dict[str, str] = {
    "hook": BASE_INSTRUCTIONS
    + "Tugasmu membuat hook: kalimat pembuka yang membuat penonton berhenti scroll.",
    "script": BASE_INSTRUCTIONS
    + "Tugasmu menulis naskah video yang dibagi per adegan, lengkap dengan visual dan narasi.",
    "caption": BASE_INSTRUCTIONS
    + "Tugasmu menulis caption posting beserta hashtag.",
}

OUTPUT_TYPES: dict[str, type[BaseModel]] = {
    "hook": HookOutput,
    "script": ScriptOutput,
    "caption": CaptionOutput,
}


@lru_cache
def get_model() -> OpenRouterModel:
    return OpenRouterModel(
        settings.openrouter_model,
        provider=OpenRouterProvider(
            api_key=settings.openrouter_api_key,
            app_title=settings.app_name,
        ),
    )


@lru_cache
def get_agent(kind: str) -> Agent:
    # Agent dibuat sekali per jenis lalu dipakai ulang, bukan dibuat di setiap request
    return Agent(
        get_model(),
        output_type=OUTPUT_TYPES[kind],
        instructions=INSTRUCTIONS[kind],
        model_settings={"timeout": 60.0},
    )


def build_prompt(
    *,
    title: str,
    description: str | None,
    platform: str,
    extra_instructions: str | None,
) -> str:
    parts = [f"Judul ide: {title}", f"Platform: {platform}"]
    if description:
        parts.append(f"Deskripsi: {description}")
    if extra_instructions:
        parts.append(f"Arahan tambahan: {extra_instructions}")
    return "\n".join(parts)


async def run_generation(
    kind: GenerationKind,
    *,
    title: str,
    description: str | None,
    platform: str,
    extra_instructions: str | None,
) -> dict:
    prompt = build_prompt(
        title=title,
        description=description,
        platform=platform,
        extra_instructions=extra_instructions,
    )
    result = await get_agent(kind).run(prompt)
    return result.output.model_dump()
