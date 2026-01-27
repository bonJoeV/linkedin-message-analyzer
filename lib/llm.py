"""LLM-powered message analysis.

This module re-exports from lib.llm package for backward compatibility.

For the new modular implementation, see:
    - lib/llm/base.py - Provider base class and registry
    - lib/llm/analyzer.py - LLMAnalyzer class
    - lib/llm/providers/ - Individual provider implementations

Supported providers:
    - openai: GPT models (requires OPENAI_API_KEY)
    - anthropic: Claude models (requires ANTHROPIC_API_KEY)
    - ollama: Local models (free, no API key needed)
    - gemini: Google Gemini (requires GOOGLE_API_KEY)
    - groq: Fast inference (requires GROQ_API_KEY)
    - mistral: Mistral AI (requires MISTRAL_API_KEY)

Example:
    >>> from lib.llm import LLMAnalyzer
    >>> analyzer = LLMAnalyzer(provider='ollama')  # Free, local!
    >>> result = analyzer.analyze_message("Message text...")
"""

# Re-export from new module location for backward compatibility
from lib.llm.analyzer import LLMAnalyzer
from lib.llm.base import LLMProvider, ProviderRegistry

__all__ = [
    "LLMAnalyzer",
    "LLMProvider",
    "ProviderRegistry",
]
