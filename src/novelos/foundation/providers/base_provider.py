from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(slots=True)
class ProviderRequest:
    task_type: str
    prompt: str
    context: dict
    stream: bool = False


@dataclass(slots=True)
class ProviderResponse:
    text: str
    provider: str
    model: str
    usage: dict | None = None
    latency_ms: int | None = None


class BaseProvider(ABC):
    def __init__(
        self,
        model_name: str,
        timeout_seconds: float = 60.0,
        max_retries: int = 2,
        base_url: str | None = None,
        api_mode: str | None = None,
    ) -> None:
        self.model_name = model_name
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.base_url = base_url
        self.api_mode = api_mode

    @abstractmethod
    def generate(self, request: ProviderRequest) -> ProviderResponse:
        raise NotImplementedError
