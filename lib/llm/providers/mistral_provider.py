"""Mistral AI LLM provider implementation."""

import logging

from lib.llm.base import LLMProvider, ProviderRegistry
from lib.exceptions import (
    ConfigurationError,
    RateLimitError,
    QuotaExhaustedError,
    ProviderUnavailableError,
)


logger = logging.getLogger(__name__)


@ProviderRegistry.register
class MistralProvider(LLMProvider):
    """Mistral AI models provider.

    EU-based AI company with strong open-weight models.

    Requires: pip install mistralai
    Environment variable: MISTRAL_API_KEY

    Rate limit headers:
        Retry-After (on 429)
    """

    name = "mistral"
    default_model = "mistral-small-latest"
    env_var = "MISTRAL_API_KEY"
    requires_api_key = True

    def initialize(self) -> None:
        """Initialize the Mistral client."""
        try:
            from mistralai import Mistral
            import mistralai
            self._client = Mistral(api_key=self.api_key)
            self._mistral_module = mistralai
        except ImportError:
            raise ConfigurationError(
                "Mistral AI package not installed. Run: pip install mistralai"
            )

    def _do_complete(
        self,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.1,
    ) -> str:
        """Get completion from Mistral.

        Args:
            prompt: The prompt to send
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature

        Returns:
            Text response from the model
        """
        try:
            response = self._client.chat.complete(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return response.choices[0].message.content or ""

        except Exception as e:
            error_msg = str(e).lower()
            error_type = type(e).__name__

            # Check for rate limit errors (429)
            if '429' in error_msg or 'rate limit' in error_msg or 'too many requests' in error_msg:
                # Try to parse retry time from error or headers
                retry_after = None
                import re
                match = re.search(r'retry.* ([\d.]+)\s*(?:second|sec|s)', error_msg)
                if match:
                    retry_after = float(match.group(1))

                # Check for Retry-After in exception
                if hasattr(e, 'response') and hasattr(e.response, 'headers'):
                    retry_str = e.response.headers.get('Retry-After')
                    if retry_str:
                        try:
                            retry_after = float(retry_str)
                        except ValueError:
                            pass

                raise RateLimitError(
                    f"Mistral rate limit: {e}",
                    retry_after=retry_after,
                    limit_type="requests",
                )

            # Check for quota/billing issues
            if any(x in error_msg for x in ['quota', 'billing', 'credit', 'payment', '402']):
                raise QuotaExhaustedError(f"Mistral quota exhausted: {e}")

            # Check for authentication errors
            if '401' in error_msg or 'unauthorized' in error_msg or 'authentication' in error_msg:
                raise ConfigurationError(f"Mistral authentication failed: {e}")

            # Server errors
            if any(x in error_msg for x in ['500', '502', '503', 'unavailable', 'server error']):
                raise ProviderUnavailableError(
                    f"Mistral unavailable: {e}",
                    retry_after=5.0,
                )

            # Re-raise unknown errors
            raise

    @classmethod
    def get_install_instructions(cls) -> str:
        return "pip install mistralai>=1.0.0"
