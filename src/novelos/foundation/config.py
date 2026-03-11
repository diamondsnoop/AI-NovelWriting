from dataclasses import dataclass
import os

from novelos.foundation.dotenv import load_dotenv


@dataclass(slots=True)
class AppConfig:
    llm_provider: str = "mock"
    model_name: str = "skeleton-writer"
    base_url: str | None = None
    api_mode: str = "responses"
    timeout_seconds: float = 150.0
    plan_timeout_seconds: float = 150.0
    write_timeout_seconds: float = 240.0
    write_max_retries: int = 0
    review_timeout_seconds: float = 150.0
    summary_timeout_seconds: float = 150.0
    extraction_timeout_seconds: float = 150.0
    character_profile_timeout_seconds: float = 150.0
    max_retries: int = 2


def load_config() -> AppConfig:
    load_dotenv()
    return AppConfig(
        llm_provider=os.getenv("NOVEL_LLM_PROVIDER", "mock"),
        model_name=os.getenv("NOVEL_LLM_MODEL", "skeleton-writer"),
        base_url=os.getenv("OPENAI_BASE_URL") or None,
        api_mode=os.getenv("OPENAI_API_MODE", "responses"),
        timeout_seconds=float(os.getenv("NOVEL_LLM_TIMEOUT_SECONDS", "150")),
        plan_timeout_seconds=float(os.getenv("NOVEL_PLAN_TIMEOUT_SECONDS", os.getenv("NOVEL_LLM_TIMEOUT_SECONDS", "150"))),
        write_timeout_seconds=float(os.getenv("NOVEL_WRITE_TIMEOUT_SECONDS", "240")),
        write_max_retries=int(os.getenv("NOVEL_WRITE_MAX_RETRIES", "0")),
        review_timeout_seconds=float(os.getenv("NOVEL_REVIEW_TIMEOUT_SECONDS", os.getenv("NOVEL_LLM_TIMEOUT_SECONDS", "150"))),
        summary_timeout_seconds=float(os.getenv("NOVEL_SUMMARY_TIMEOUT_SECONDS", os.getenv("NOVEL_LLM_TIMEOUT_SECONDS", "150"))),
        extraction_timeout_seconds=float(os.getenv("NOVEL_EXTRACTION_TIMEOUT_SECONDS", os.getenv("NOVEL_LLM_TIMEOUT_SECONDS", "150"))),
        character_profile_timeout_seconds=float(
            os.getenv("NOVEL_CHARACTER_PROFILE_TIMEOUT_SECONDS", os.getenv("NOVEL_LLM_TIMEOUT_SECONDS", "150"))
        ),
        max_retries=int(os.getenv("NOVEL_LLM_MAX_RETRIES", "2")),
    )
