from dataclasses import dataclass

from novelos.foundation.dotenv import load_dotenv
from novelos.foundation.logging import get_logger, log_llm_call
from novelos.foundation.providers.base_provider import ProviderRequest
from novelos.foundation.providers.mock_provider_v2 import MockProvider
from novelos.foundation.providers.openai_provider import OpenAIProvider


@dataclass(slots=True)
class LLMRequest:
    task_type: str
    prompt: str
    context: dict
    stream: bool = False


@dataclass(slots=True)
class LLMResponse:
    text: str
    provider: str
    model: str
    usage: dict | None = None
    latency_ms: int | None = None


PROVIDER_REGISTRY = {
    "mock": MockProvider,
    "openai": OpenAIProvider,
}


class LLMClient:
    def __init__(
        self,
        provider: str,
        model_name: str,
        timeout_seconds: float = 60.0,
        max_retries: int = 2,
        base_url: str | None = None,
        api_mode: str = "responses",
    ) -> None:
        load_dotenv()
        self.provider_name = provider
        self.model_name = model_name
        self.logger = get_logger("novelos.llm")
        provider_cls = PROVIDER_REGISTRY.get(provider)
        if provider_cls is None:
            raise ValueError(f"Unsupported provider: {provider}")
        self.provider = provider_cls(
            model_name=model_name,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
            base_url=base_url,
            api_mode=api_mode,
        )

    def generate(self, request: LLMRequest) -> LLMResponse:
        provider_request = ProviderRequest(
            task_type=request.task_type,
            prompt=request.prompt,
            context=request.context,
            stream=request.stream,
        )
        try:
            response = self.provider.generate(provider_request)
        except Exception as exc:
            log_llm_call(
                self.logger,
                {
                    "provider": self.provider_name,
                    "model": self.model_name,
                    "task_type": request.task_type,
                    "stream": request.stream,
                    "error_type": exc.__class__.__name__,
                    "error": str(exc),
                },
            )
            raise
        llm_response = LLMResponse(
            text=response.text,
            provider=response.provider,
            model=response.model,
            usage=response.usage,
            latency_ms=response.latency_ms,
        )
        log_llm_call(
            self.logger,
            {
                "provider": llm_response.provider,
                "model": llm_response.model,
                "task_type": request.task_type,
                "latency_ms": llm_response.latency_ms,
                "usage": llm_response.usage,
                "stream": request.stream,
            },
        )
        return llm_response
