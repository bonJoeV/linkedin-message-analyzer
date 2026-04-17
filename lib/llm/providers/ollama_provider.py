"""Ollama local LLM provider implementation."""

import logging

from lib.llm.base import LLMProvider, ProviderRegistry
from lib.exceptions import (
    ConfigurationError,
    ProviderUnavailableError,
)

logger = logging.getLogger(__name__)


@ProviderRegistry.register
class OllamaProvider(LLMProvider):
    """Ollama local LLM provider.

    Runs models locally - free and private!

    Requires:
        1. Install Ollama: https://ollama.ai
        2. pip install ollama
        3. Pull a model: ollama pull llama3.2

    No API key needed.
    No rate limits (local).
    """

    name = "ollama"
    default_model = "llama3.2"
    env_var = ""  # No API key needed
    requires_api_key = False
    description = "Local inference with no API key requirement and configurable server base URL."
    setup_url = "https://ollama.com/download"
    recommended_models = ("llama3.2", "qwen2.5:7b")
    config_fields = (
        ("base_url", "Ollama server base URL, for example http://localhost:11434"),
    )
    notes = (
        "Pull the configured model locally before running analysis.",
    )

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        **kwargs,
    ) -> None:
        super().__init__(api_key, model, **kwargs)
        self.base_url = kwargs.get("base_url", "http://localhost:11434")

    def initialize(self) -> None:
        """Initialize the Ollama client and verify connection."""
        try:
            import ollama
            self._client = ollama.Client(host=self.base_url)
            self._ollama_module = ollama
            # Verify connection by listing models
            self._client.list()
            logger.debug(f"Connected to Ollama at {self.base_url}")
        except ImportError:
            raise ConfigurationError(
                "Ollama package not installed. Run: pip install ollama"
            )
        except Exception as e:
            raise ConfigurationError(
                f"Cannot connect to Ollama at {self.base_url}. "
                f"Make sure Ollama is running: ollama serve\n"
                f"Error: {e}"
            )

    def _do_complete(
        self,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.1,
    ) -> str:
        """Get completion from Ollama.

        Args:
            prompt: The prompt to send
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature

        Returns:
            Text response from the model
        """
        # Ollama needs explicit JSON instruction
        json_prompt = prompt + "\n\nRespond with valid JSON only, no markdown code blocks."

        try:
            response = self._client.generate(
                model=self.model,
                prompt=json_prompt,
                options={
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
                format="json",
            )
            return response["response"]

        except Exception as e:
            error_msg = str(e).lower()

            # Connection errors
            if any(x in error_msg for x in ['connection', 'refused', 'timeout', 'unreachable']):
                raise ProviderUnavailableError(
                    f"Ollama not available at {self.base_url}: {e}",
                    retry_after=2.0,
                )

            # Model not found
            if 'model' in error_msg and 'not found' in error_msg:
                raise ConfigurationError(
                    f"Ollama model '{self.model}' not found. "
                    f"Pull it first: ollama pull {self.model}"
                )

            # Re-raise unknown errors
            raise

    @classmethod
    def get_install_instructions(cls) -> str:
        return (
            "1. Install Ollama: https://ollama.com/download\n"
            "2. pip install ollama>=0.6.0\n"
            "3. Pull a model: ollama pull llama3.2"
        )
