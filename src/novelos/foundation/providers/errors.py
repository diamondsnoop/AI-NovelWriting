class ProviderError(Exception):
    """Base provider error."""


class ProviderNetworkError(ProviderError):
    """Network or connection failure."""


class ProviderRateLimitError(ProviderError):
    """Rate limit failure."""


class ProviderTokenLimitError(ProviderError):
    """Prompt or response exceeded token constraints."""


class ProviderTimeoutError(ProviderError):
    """Request timed out."""


class ProviderRefusalError(ProviderError):
    """Model refused to answer."""


class ProviderResponseError(ProviderError):
    """Unexpected response or provider-side failure."""
