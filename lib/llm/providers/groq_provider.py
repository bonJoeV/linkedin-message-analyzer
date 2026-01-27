"""Groq LLM provider implementation."""

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
class GroqProvider(LLMProvider):
    """Groq fast inference provider.

    Known for extremely fast inference speeds.

    Requires: pip install groq
    Environment variable: GROQ_API_KEY

    Rate limit headers (same as OpenAI):
        x-ratelimit-limit-requests
        x-ratelimit-remaining-requests
        x-ratelimit-reset-requests
        x-ratelimit-limit-tokens
        x-ratelimit-remaining-tokens
        x-ratelimit-reset-tokens
    """

    name = "groq"
    default_model = "llama-3.1-8b-instant"
    env_var = "GROQ_API_KEY"
    requires_api_key = True

    def initialize(self) -> None:
        """Initialize the Groq client."""
        try:
            from groq import Groq
            import groq as groq_module
            self._client = Groq(api_key=self.api_key)
            self._groq_module = groq_module
        except ImportError:
            raise ConfigurationError(
                "Groq package not installed. Run: pip install groq"
            )

    def _parse_rate_limit_headers(self, response: any) -> None:
        """Parse Groq rate limit headers from response."""
        try:
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
                logger.debug(f"Groq rate limits: {self.rate_limit_info}")

        except Exception as e:
            logger.debug(f"Could not parse Groq rate limit headers: {e}")

    def _do_complete(
        self,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.1,
    ) -> str:
        """Get completion from Groq.

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

        except self._groq_module.RateLimitError as e:
            # 429 - Rate limited (common with free tier)
            retry_after = None
            error_msg = str(e)

            # Groq often includes wait time in the error message
            # e.g., "Please try again in 50.597142857s"
            import re
            match = re.search(r'try again in ([\d.]+)s', error_msg)
            if match:
                retry_after = float(match.group(1))
            elif hasattr(e, 'response') and hasattr(e.response, 'headers'):
                retry_after_str = e.response.headers.get('retry-after')
                if retry_after_str:
                    try:
                        retry_after = float(retry_after_str)
                    except ValueError:
                        pass

            # Determine limit type from error message
            limit_type = "tokens" if "token" in error_msg.lower() else "requests"

            raise RateLimitError(
                f"Groq rate limit: {e}",
                retry_after=retry_after,
                limit_type=limit_type,
            )

        except self._groq_module.AuthenticationError as e:
            error_msg = str(e).lower()
            if 'quota' in error_msg or 'limit' in error_msg:
                raise QuotaExhaustedError(f"Groq quota exhausted: {e}")
            raise ConfigurationError(f"Groq authentication failed: {e}")

        except self._groq_module.InternalServerError as e:
            raise ProviderUnavailableError(
                f"Groq server error: {e}",
                retry_after=5.0,
            )

        except self._groq_module.APIStatusError as e:
            if hasattr(e, 'status_code'):
                if e.status_code == 429:
                    raise RateLimitError(f"Groq rate limit: {e}")
                elif e.status_code == 503:
                    raise ProviderUnavailableError(f"Groq overloaded: {e}")
            raise

    @classmethod
    def get_install_instructions(cls) -> str:
        return "pip install groq>=0.11.0"
