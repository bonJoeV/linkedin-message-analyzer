"""OpenAI LLM provider implementation."""

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
class OpenAIProvider(LLMProvider):
    """OpenAI GPT models provider.

    Requires: pip install openai
    Environment variable: OPENAI_API_KEY

    Rate limit headers:
        x-ratelimit-limit-requests
        x-ratelimit-remaining-requests
        x-ratelimit-reset-requests
        x-ratelimit-limit-tokens
        x-ratelimit-remaining-tokens
        x-ratelimit-reset-tokens
    """

    name = "openai"
    default_model = "gpt-4o-mini"
    env_var = "OPENAI_API_KEY"
    requires_api_key = True

    def initialize(self) -> None:
        """Initialize the OpenAI client."""
        try:
            import openai
            self._client = openai.OpenAI(api_key=self.api_key)
            self._openai_module = openai
        except ImportError:
            raise ConfigurationError(
                "OpenAI package not installed. Run: pip install openai"
            )

    def _parse_rate_limit_headers(self, response: any) -> None:
        """Parse OpenAI rate limit headers from response."""
        try:
            # OpenAI SDK exposes headers via response._response or similar
            headers = None
            if hasattr(response, '_response') and hasattr(response._response, 'headers'):
                headers = response._response.headers
            elif hasattr(response, 'response') and hasattr(response.response, 'headers'):
                headers = response.response.headers

            if not headers:
                return

            def get_header(name: str) -> int | None:
                val = headers.get(name)
                if val:
                    try:
                        return int(val)
                    except ValueError:
                        pass
                return None

            def parse_reset(val: str | None) -> float | None:
                """Parse reset time (could be 'XXms' or 'XXs')."""
                if not val:
                    return None
                try:
                    if val.endswith('ms'):
                        return float(val[:-2]) / 1000.0
                    elif val.endswith('s'):
                        return float(val[:-1])
                    else:
                        return float(val)
                except ValueError:
                    return None

            self.rate_limit_info = RateLimitInfo(
                requests_limit=get_header('x-ratelimit-limit-requests'),
                requests_remaining=get_header('x-ratelimit-remaining-requests'),
                requests_reset=parse_reset(headers.get('x-ratelimit-reset-requests')),
                tokens_limit=get_header('x-ratelimit-limit-tokens'),
                tokens_remaining=get_header('x-ratelimit-remaining-tokens'),
                tokens_reset=parse_reset(headers.get('x-ratelimit-reset-tokens')),
                retry_after=parse_reset(headers.get('retry-after')),
            )

            if self.rate_limit_info.requests_remaining is not None:
                logger.debug(f"OpenAI rate limits: {self.rate_limit_info}")

        except Exception as e:
            logger.debug(f"Could not parse OpenAI rate limit headers: {e}")

    def _do_complete(
        self,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.1,
    ) -> str:
        """Get completion from OpenAI.

        Args:
            prompt: The prompt to send
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature

        Returns:
            Text response from the model
        """
        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                max_tokens=max_tokens,
                temperature=temperature,
            )

            # Parse headers for rate limit info
            self._parse_rate_limit_headers(response)

            return response.choices[0].message.content or ""

        except self._openai_module.RateLimitError as e:
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
                f"OpenAI rate limit: {e}",
                retry_after=retry_after,
                limit_type="requests",
            )

        except self._openai_module.AuthenticationError as e:
            # 401 - Invalid API key or quota issues
            error_msg = str(e).lower()
            if 'quota' in error_msg or 'billing' in error_msg or 'exceeded' in error_msg:
                raise QuotaExhaustedError(f"OpenAI quota exhausted: {e}")
            raise ConfigurationError(f"OpenAI authentication failed: {e}")

        except self._openai_module.InternalServerError as e:
            # 500 - Server error
            raise ProviderUnavailableError(
                f"OpenAI server error: {e}",
                retry_after=5.0,
            )

        except self._openai_module.APIStatusError as e:
            if hasattr(e, 'status_code'):
                if e.status_code == 429:
                    raise RateLimitError(f"OpenAI rate limit: {e}")
                elif e.status_code == 503:
                    raise ProviderUnavailableError(f"OpenAI overloaded: {e}")
                elif e.status_code == 402:
                    raise QuotaExhaustedError(f"OpenAI payment required: {e}")
            raise

    @classmethod
    def get_install_instructions(cls) -> str:
        return "pip install openai>=1.0.0"
