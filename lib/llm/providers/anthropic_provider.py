"""Anthropic Claude LLM provider implementation."""

import logging

from lib.llm.base import LLMProvider, ProviderRegistry, RateLimitInfo
from lib.exceptions import (
    ConfigurationError,
    RateLimitError,
    QuotaExhaustedError,
    ProviderUnavailableError,
)


logger = logging.getLogger(__name__)


@ProviderRegistry.register
class AnthropicProvider(LLMProvider):
    """Anthropic Claude models provider.

    Requires: pip install anthropic
    Environment variable: ANTHROPIC_API_KEY

    Rate limit headers:
        anthropic-ratelimit-requests-limit
        anthropic-ratelimit-requests-remaining
        anthropic-ratelimit-requests-reset
        anthropic-ratelimit-tokens-limit
        anthropic-ratelimit-tokens-remaining
        anthropic-ratelimit-tokens-reset
    """

    name = "anthropic"
    default_model = "claude-3-haiku-20240307"
    env_var = "ANTHROPIC_API_KEY"
    requires_api_key = True

    def initialize(self) -> None:
        """Initialize the Anthropic client."""
        try:
            import anthropic
            self._client = anthropic.Anthropic(api_key=self.api_key)
            self._anthropic_module = anthropic
        except ImportError:
            raise ConfigurationError(
                "Anthropic package not installed. Run: pip install anthropic"
            )

    def _parse_rate_limit_headers(self, response: any) -> None:
        """Parse Anthropic rate limit headers from response."""
        # Anthropic SDK exposes headers via response object
        # Headers are like: anthropic-ratelimit-requests-remaining
        try:
            # The raw response has headers
            if hasattr(response, '_response') and hasattr(response._response, 'headers'):
                headers = response._response.headers
            elif hasattr(response, 'response') and hasattr(response.response, 'headers'):
                headers = response.response.headers
            else:
                return

            def get_header(name: str) -> int | None:
                val = headers.get(name)
                if val:
                    try:
                        return int(val)
                    except ValueError:
                        pass
                return None

            def get_header_float(name: str) -> float | None:
                val = headers.get(name)
                if val:
                    try:
                        return float(val)
                    except ValueError:
                        pass
                return None

            self.rate_limit_info = RateLimitInfo(
                requests_limit=get_header('anthropic-ratelimit-requests-limit'),
                requests_remaining=get_header('anthropic-ratelimit-requests-remaining'),
                requests_reset=get_header_float('anthropic-ratelimit-requests-reset'),
                tokens_limit=get_header('anthropic-ratelimit-tokens-limit'),
                tokens_remaining=get_header('anthropic-ratelimit-tokens-remaining'),
                tokens_reset=get_header_float('anthropic-ratelimit-tokens-reset'),
                retry_after=get_header_float('retry-after'),
            )

            if self.rate_limit_info.requests_remaining is not None:
                logger.debug(f"Anthropic rate limits: {self.rate_limit_info}")

        except Exception as e:
            logger.debug(f"Could not parse Anthropic rate limit headers: {e}")

    def _do_complete(
        self,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.1,
    ) -> str:
        """Get completion from Anthropic Claude.

        Args:
            prompt: The prompt to send
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature

        Returns:
            Text response from the model
        """
        try:
            response = self._client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )

            # Parse headers for rate limit info
            self._parse_rate_limit_headers(response)

            return response.content[0].text

        except self._anthropic_module.RateLimitError as e:
            # 429 - Rate limited
            retry_after = None
            if hasattr(e, 'response') and hasattr(e.response, 'headers'):
                retry_after_str = e.response.headers.get('retry-after')
                if retry_after_str:
                    try:
                        retry_after = float(retry_after_str)
                    except ValueError:
                        pass
            raise RateLimitError(
                f"Anthropic rate limit: {e}",
                retry_after=retry_after,
                limit_type="requests",
            )

        except self._anthropic_module.BadRequestError as e:
            # 400 - Check for quota/credit issues
            error_msg = str(e).lower()
            if 'credit' in error_msg or 'balance' in error_msg or 'billing' in error_msg:
                raise QuotaExhaustedError(
                    f"Anthropic credits exhausted: {e}"
                )
            # Other bad request errors, re-raise
            raise

        except self._anthropic_module.InternalServerError as e:
            # 500 - Server error
            raise ProviderUnavailableError(
                f"Anthropic server error: {e}",
                retry_after=5.0,
            )

        except self._anthropic_module.APIStatusError as e:
            # Check status code for other cases
            if hasattr(e, 'status_code'):
                if e.status_code == 429:
                    raise RateLimitError(f"Anthropic rate limit: {e}")
                elif e.status_code == 503:
                    raise ProviderUnavailableError(f"Anthropic overloaded: {e}")
            raise

    @classmethod
    def get_install_instructions(cls) -> str:
        return "pip install anthropic>=0.18.0"
