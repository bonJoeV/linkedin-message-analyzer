"""Google Gemini LLM provider implementation."""

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
class GeminiProvider(LLMProvider):
    """Google Gemini models provider.

    Supports both the new google-genai SDK (recommended) and the
    legacy google-generativeai package.

    Requires: pip install google-genai
    Environment variable: GOOGLE_API_KEY

    Note: Gemini has limited rate limit header support.
    429 responses include info about which quota was exceeded.
    """

    name = "gemini"
    default_model = "gemini-2.0-flash"
    env_var = "GOOGLE_API_KEY"
    requires_api_key = True

    def initialize(self) -> None:
        """Initialize the Gemini client."""
        self._use_new_sdk = False
        self._error_classes = {}

        # Try new google-genai SDK first (recommended)
        try:
            from google import genai
            from google.genai import errors as genai_errors

            self._client = genai.Client(api_key=self.api_key)
            self._use_new_sdk = True
            self._error_classes = {
                'ClientError': getattr(genai_errors, 'ClientError', Exception),
                'ServerError': getattr(genai_errors, 'ServerError', Exception),
            }
            return
        except ImportError:
            pass

        # Fall back to legacy google-generativeai
        try:
            import google.generativeai as genai_legacy
            from google.api_core import exceptions as google_exceptions

            genai_legacy.configure(api_key=self.api_key)
            self._client = genai_legacy.GenerativeModel(
                self.model,
                generation_config=genai_legacy.GenerationConfig(
                    response_mime_type="application/json"
                ),
            )
            self._use_new_sdk = False
            self._error_classes = {
                'ResourceExhausted': google_exceptions.ResourceExhausted,
                'TooManyRequests': google_exceptions.TooManyRequests,
                'ServiceUnavailable': google_exceptions.ServiceUnavailable,
                'InvalidArgument': google_exceptions.InvalidArgument,
            }
        except ImportError:
            raise ConfigurationError(
                "Google GenAI package not installed. "
                "Run: pip install google-genai"
            )

    def _do_complete(
        self,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.1,
    ) -> str:
        """Get completion from Gemini.

        Args:
            prompt: The prompt to send
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature

        Returns:
            Text response from the model
        """
        try:
            if self._use_new_sdk:
                # New google-genai SDK
                response = self._client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config={
                        "temperature": temperature,
                        "max_output_tokens": max_tokens,
                        "response_mime_type": "application/json",
                    },
                )
                return response.text
            else:
                # Legacy google-generativeai
                response = self._client.generate_content(
                    prompt,
                    generation_config={
                        "temperature": temperature,
                        "max_output_tokens": max_tokens,
                    },
                )
                return response.text

        except Exception as e:
            error_msg = str(e).lower()

            # Check for rate limit / quota errors
            if any(x in error_msg for x in ['429', 'resource exhausted', 'quota', 'rate limit']):
                # Try to parse retry time from error message
                retry_after = None
                import re
                match = re.search(r'retry.* ([\d.]+)\s*(?:second|sec|s)', error_msg)
                if match:
                    retry_after = float(match.group(1))

                # Distinguish between rate limit and quota exhaustion
                if 'quota' in error_msg and 'daily' in error_msg:
                    raise QuotaExhaustedError(
                        f"Gemini daily quota exhausted: {e}"
                    )

                raise RateLimitError(
                    f"Gemini rate limit: {e}",
                    retry_after=retry_after or 60.0,  # Default 60s for Gemini
                    limit_type="requests",
                )

            # Check for billing/credit issues
            if any(x in error_msg for x in ['billing', 'payment', 'credit']):
                raise QuotaExhaustedError(f"Gemini billing issue: {e}")

            # Server errors
            if any(x in error_msg for x in ['503', 'unavailable', 'overloaded']):
                raise ProviderUnavailableError(
                    f"Gemini unavailable: {e}",
                    retry_after=5.0,
                )

            # Re-raise unknown errors
            raise

    @classmethod
    def get_install_instructions(cls) -> str:
        return "pip install google-genai>=1.0.0"
