"""Base classes for LLM provider plugin system."""

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from lib.exceptions import (
    ConfigurationError,
    RateLimitError,
    QuotaExhaustedError,
    ProviderUnavailableError,
)


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ProviderMetadata:
    """User-facing metadata about an LLM provider."""

    name: str
    default_model: str
    env_var: str
    requires_api_key: bool
    install: str
    setup_url: str = ""
    description: str = ""
    recommended_models: tuple[str, ...] = ()
    config_fields: tuple[tuple[str, str], ...] = ()
    notes: tuple[str, ...] = ()

    @property
    def provider_type(self) -> str:
        """Return a simple user-facing provider type label."""
        if self.requires_api_key:
            return "hosted api"
        return "local / self-hosted"

    def as_dict(self) -> dict[str, Any]:
        """Convert metadata into a JSON/CLI-friendly shape."""
        return {
            "name": self.name,
            "provider_type": self.provider_type,
            "default_model": self.default_model,
            "env_var": self.env_var,
            "requires_api_key": self.requires_api_key,
            "install": self.install,
            "setup_url": self.setup_url,
            "description": self.description,
            "recommended_models": list(self.recommended_models),
            "config_fields": [
                {"name": field_name, "description": description}
                for field_name, description in self.config_fields
            ],
            "notes": list(self.notes),
        }


@dataclass
class RateLimitInfo:
    """Rate limit information from API response headers.

    Tracks both request and token limits where available.
    """

    # Request limits
    requests_limit: int | None = None
    requests_remaining: int | None = None
    requests_reset: float | None = None  # Seconds until reset

    # Token limits
    tokens_limit: int | None = None
    tokens_remaining: int | None = None
    tokens_reset: float | None = None

    # General
    retry_after: float | None = None  # From Retry-After header
    last_updated: float = field(default_factory=time.time)

    @property
    def is_near_limit(self) -> bool:
        """Check if we're approaching rate limits (< 10% remaining)."""
        if self.requests_remaining is not None and self.requests_limit:
            if self.requests_remaining / self.requests_limit < 0.1:
                return True
        if self.tokens_remaining is not None and self.tokens_limit:
            if self.tokens_remaining / self.tokens_limit < 0.1:
                return True
        return False

    @property
    def should_backoff(self) -> bool:
        """Check if we should proactively back off."""
        if self.requests_remaining is not None and self.requests_remaining <= 1:
            return True
        return False

    @property
    def suggested_wait(self) -> float:
        """Suggest wait time based on rate limit info."""
        if self.retry_after:
            return self.retry_after
        if self.requests_reset:
            return min(self.requests_reset, 60.0)  # Cap at 60s
        if self.tokens_reset:
            return min(self.tokens_reset, 60.0)
        return 1.0  # Default 1 second

    def __str__(self) -> str:
        parts = []
        if self.requests_remaining is not None:
            parts.append(f"requests: {self.requests_remaining}/{self.requests_limit}")
        if self.tokens_remaining is not None:
            parts.append(f"tokens: {self.tokens_remaining}/{self.tokens_limit}")
        if self.retry_after:
            parts.append(f"retry_after: {self.retry_after}s")
        return ", ".join(parts) if parts else "no rate limit info"


class LLMProvider(ABC):
    """Abstract base class for LLM providers.

    Subclass this to add support for a new LLM provider.

    Class Attributes:
        name: Provider identifier (e.g., 'openai', 'ollama')
        default_model: Default model to use if none specified
        env_var: Environment variable for API key
        requires_api_key: Whether this provider needs an API key
    """

    name: str = ""
    default_model: str = ""
    env_var: str = ""
    requires_api_key: bool = True
    description: str = ""
    setup_url: str = ""
    recommended_models: tuple[str, ...] = ()
    config_fields: tuple[tuple[str, str], ...] = ()
    notes: tuple[str, ...] = ()

    # Retry configuration
    max_retries: int = 3
    initial_backoff: float = 1.0
    max_backoff: float = 60.0
    backoff_multiplier: float = 2.0

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the provider.

        Args:
            api_key: API key (or use environment variable)
            model: Model to use (or use default)
            **kwargs: Provider-specific configuration
        """
        self.api_key = api_key
        self.model = model or self.default_model
        self._client: Any = None
        self._initialized = False
        self.extra_config = kwargs

        # Rate limit tracking
        self.rate_limit_info = RateLimitInfo()
        self._consecutive_errors = 0
        self._quota_exhausted = False

    @abstractmethod
    def initialize(self) -> None:
        """Initialize the provider client.

        Called lazily on first use. Should set self._client.

        Raises:
            ConfigurationError: If package not installed or config invalid
        """
        pass

    @abstractmethod
    def _do_complete(
        self,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.1,
    ) -> str:
        """Internal completion method - implement in subclasses.

        This method should:
        1. Make the API call
        2. Update self.rate_limit_info with response headers
        3. Return the response text
        4. Raise RateLimitError, QuotaExhaustedError, or ProviderUnavailableError as appropriate
        """
        pass

    def complete(
        self,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.1,
    ) -> str:
        """Send a prompt and get a completion with automatic retry.

        Args:
            prompt: The prompt to send
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature

        Returns:
            Raw text response from the LLM

        Raises:
            QuotaExhaustedError: If credits/quota exhausted (no retry)
            RateLimitError: If rate limit hit and retries exhausted
            ProviderUnavailableError: If provider unavailable after retries
        """
        self.ensure_initialized()

        # Check if quota was previously exhausted
        if self._quota_exhausted:
            raise QuotaExhaustedError(
                f"{self.name}: Quota exhausted. Please add credits or wait for reset."
            )

        # Proactive backoff if near limits
        if self.rate_limit_info.should_backoff:
            wait_time = self.rate_limit_info.suggested_wait
            logger.info(f"{self.name}: Near rate limit, waiting {wait_time:.1f}s")
            time.sleep(wait_time)

        backoff = self.initial_backoff
        last_error: Exception | None = None

        for attempt in range(self.max_retries + 1):
            try:
                result = self._do_complete(prompt, max_tokens, temperature)
                self._consecutive_errors = 0
                return result

            except QuotaExhaustedError:
                # No retry for quota exhaustion
                self._quota_exhausted = True
                raise

            except RateLimitError as e:
                last_error = e
                self._consecutive_errors += 1

                if attempt < self.max_retries:
                    # Use retry_after if provided, otherwise exponential backoff
                    wait_time = e.retry_after if e.retry_after else backoff
                    wait_time = min(wait_time, self.max_backoff)

                    logger.warning(
                        f"{self.name}: Rate limited ({e.limit_type or 'unknown'}), "
                        f"attempt {attempt + 1}/{self.max_retries + 1}, "
                        f"waiting {wait_time:.1f}s"
                    )
                    time.sleep(wait_time)
                    backoff = min(backoff * self.backoff_multiplier, self.max_backoff)
                else:
                    logger.error(f"{self.name}: Rate limit retries exhausted")
                    raise

            except ProviderUnavailableError as e:
                last_error = e
                self._consecutive_errors += 1

                if attempt < self.max_retries:
                    wait_time = e.retry_after if e.retry_after else backoff
                    wait_time = min(wait_time, self.max_backoff)

                    logger.warning(
                        f"{self.name}: Provider unavailable, "
                        f"attempt {attempt + 1}/{self.max_retries + 1}, "
                        f"waiting {wait_time:.1f}s"
                    )
                    time.sleep(wait_time)
                    backoff = min(backoff * self.backoff_multiplier, self.max_backoff)
                else:
                    logger.error(f"{self.name}: Provider unavailable after retries")
                    raise

        # Should not reach here, but just in case
        if last_error:
            raise last_error
        raise RuntimeError("Unexpected state in complete()")

    def ensure_initialized(self) -> None:
        """Lazy initialization wrapper."""
        if not self._initialized:
            self.initialize()
            self._initialized = True

    def reset_quota_status(self) -> None:
        """Reset quota exhausted flag (call after credits added)."""
        self._quota_exhausted = False
        self._consecutive_errors = 0

    @classmethod
    def get_install_instructions(cls) -> str:
        """Return installation instructions for this provider.

        Returns:
            pip install command or similar instructions
        """
        return f"pip install {cls.name}"

    @classmethod
    def get_provider_metadata(cls) -> ProviderMetadata:
        """Return structured metadata for this provider."""
        models = tuple(dict.fromkeys((cls.default_model, *cls.recommended_models)))
        return ProviderMetadata(
            name=cls.name,
            default_model=cls.default_model,
            env_var=cls.env_var,
            requires_api_key=cls.requires_api_key,
            install=cls.get_install_instructions(),
            setup_url=cls.setup_url,
            description=cls.description,
            recommended_models=models,
            config_fields=cls.config_fields,
            notes=cls.notes,
        )


class ProviderRegistry:
    """Registry for LLM providers with auto-discovery.

    Use the @register decorator or register() method to add providers.
    """

    _providers: dict[str, type[LLMProvider]] = {}

    @classmethod
    def register(cls, provider_class: type[LLMProvider]) -> type[LLMProvider]:
        """Decorator to register a provider.

        Example:
            @ProviderRegistry.register
            class MyProvider(LLMProvider):
                name = "my_provider"
                ...
        """
        cls._providers[provider_class.name] = provider_class
        return provider_class

    @classmethod
    def get(cls, name: str) -> type[LLMProvider]:
        """Get a provider class by name.

        Args:
            name: Provider identifier (e.g., 'openai', 'ollama')

        Returns:
            Provider class

        Raises:
            ConfigurationError: If provider not found
        """
        if name not in cls._providers:
            available = ", ".join(sorted(cls._providers.keys()))
            raise ConfigurationError(
                f"Unknown LLM provider: {name}. Available: {available}"
            )
        return cls._providers[name]

    @classmethod
    def list_providers(cls) -> list[str]:
        """List all registered provider names.

        Returns:
            List of provider identifiers
        """
        return list(cls._providers.keys())

    @classmethod
    def get_provider_info(cls) -> dict[str, dict[str, Any]]:
        """Get metadata about all registered providers.

        Returns:
            Dict mapping provider name to metadata dict
        """
        return {
            name: provider_class.get_provider_metadata().as_dict()
            for name, p in cls._providers.items()
            for provider_class in [p]
        }

    @classmethod
    def is_registered(cls, name: str) -> bool:
        """Check if a provider is registered.

        Args:
            name: Provider identifier

        Returns:
            True if provider is registered
        """
        return name in cls._providers
