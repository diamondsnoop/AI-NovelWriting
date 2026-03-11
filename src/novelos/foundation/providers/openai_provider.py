from __future__ import annotations

import os
import time

from novelos.foundation.providers.base_provider import BaseProvider, ProviderRequest, ProviderResponse
from novelos.foundation.providers.errors import (
    ProviderNetworkError,
    ProviderRateLimitError,
    ProviderRefusalError,
    ProviderResponseError,
    ProviderTimeoutError,
    ProviderTokenLimitError,
)


class OpenAIProvider(BaseProvider):
    provider_name = "openai"

    def __init__(
        self,
        model_name: str,
        timeout_seconds: float = 60.0,
        max_retries: int = 2,
        base_url: str | None = None,
        api_mode: str = "responses",
    ) -> None:
        super().__init__(
            model_name=model_name,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
            base_url=base_url,
        )
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL") or None
        self.api_mode = api_mode or os.getenv("OPENAI_API_MODE", "responses")

    def generate(self, request: ProviderRequest) -> ProviderResponse:
        if not self.api_key:
            raise ProviderResponseError("OPENAI_API_KEY is not set.")

        try:
            from openai import OpenAI
            from openai import (
                APIConnectionError,
                APITimeoutError,
                BadRequestError,
                RateLimitError,
            )
        except ImportError as exc:
            raise ProviderResponseError("openai package is not installed.") from exc

        client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout_seconds,
            max_retries=0,
        )

        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            started = time.monotonic()
            try:
                response = self._create_response(client, request)
                latency_ms = int((time.monotonic() - started) * 1000)
                text = self._extract_text(response)
                usage = self._extract_usage(response)
                return ProviderResponse(
                    text=text,
                    provider=self.provider_name,
                    model=self.model_name,
                    usage=usage,
                    latency_ms=latency_ms,
                )
            except RateLimitError as exc:
                last_error = ProviderRateLimitError(str(exc))
            except APITimeoutError as exc:
                last_error = ProviderTimeoutError(str(exc))
            except APIConnectionError as exc:
                last_error = ProviderNetworkError(str(exc))
            except BadRequestError as exc:
                message = str(exc)
                if self._is_token_limit_error(message):
                    raise ProviderTokenLimitError(message) from exc
                raise ProviderResponseError(message) from exc
            except ProviderRefusalError:
                raise
            except Exception as exc:  # pragma: no cover - provider-specific fallback
                raise ProviderResponseError(str(exc)) from exc

            if attempt >= self.max_retries:
                assert last_error is not None
                raise last_error
            time.sleep(min(2 ** attempt, 4))

        assert last_error is not None
        raise last_error

    def _create_response(self, client, request: ProviderRequest):
        if self.api_mode == "chat_completions":
            return client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a long-form fiction writing assistant.",
                    },
                    {
                        "role": "user",
                        "content": f"{request.prompt}\n\nContext:\n{request.context}",
                    },
                ],
                stream=request.stream,
            )

        return client.responses.create(
            model=self.model_name,
            input=[
                {
                    "role": "system",
                    "content": "You are a long-form fiction writing assistant.",
                },
                {
                    "role": "user",
                    "content": f"{request.prompt}\n\nContext:\n{request.context}",
                },
            ],
            stream=request.stream,
        )

    def _extract_text(self, response: object) -> str:
        choices = getattr(response, "choices", None)
        if choices:
            choice = choices[0]
            message = getattr(choice, "message", None)
            content = getattr(message, "content", "") if message else ""
            refusal = getattr(message, "refusal", None) if message else None
            if content:
                return content.strip()
            if refusal:
                raise ProviderRefusalError(str(refusal))

        output_text = getattr(response, "output_text", "") or ""
        if output_text.strip():
            return output_text

        output = getattr(response, "output", []) or []
        refusal_messages: list[str] = []
        text_parts: list[str] = []
        for item in output:
            content_list = getattr(item, "content", []) or []
            for content in content_list:
                content_type = getattr(content, "type", "")
                if content_type == "output_text":
                    text_value = getattr(content, "text", "")
                    if text_value:
                        text_parts.append(text_value)
                elif content_type == "refusal":
                    refusal_text = getattr(content, "refusal", "") or getattr(content, "text", "")
                    if refusal_text:
                        refusal_messages.append(refusal_text)

        if text_parts:
            return "\n".join(text_parts).strip()
        if refusal_messages:
            raise ProviderRefusalError("\n".join(refusal_messages))
        raise ProviderResponseError("Response did not contain text output.")

    def _extract_usage(self, response: object) -> dict | None:
        usage = getattr(response, "usage", None)
        if usage is None:
            return None
        if isinstance(usage, dict):
            return usage
        input_tokens = getattr(usage, "input_tokens", None) or getattr(usage, "prompt_tokens", None)
        output_tokens = getattr(usage, "output_tokens", None) or getattr(usage, "completion_tokens", None)
        total_tokens = getattr(usage, "total_tokens", None)
        return {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
        }

    def _is_token_limit_error(self, message: str) -> bool:
        lowered = message.lower()
        return "maximum context length" in lowered or "too many tokens" in lowered or "context_length" in lowered
