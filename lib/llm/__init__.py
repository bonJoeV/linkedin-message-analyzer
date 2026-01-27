"""LLM-powered analysis module.

This module provides LLM integration for deeper message analysis using
multiple providers including OpenAI, Anthropic, Ollama, Gemini, Groq,
and Mistral.

Example:
    >>> from lib.llm import LLMAnalyzer
    >>> analyzer = LLMAnalyzer(provider='openai')
    >>> result = analyzer.analyze_message("Hello, I'd love to connect...")
    >>> print(result['intent'])

    # List available providers
    >>> from lib.llm import LLMAnalyzer
    >>> print(LLMAnalyzer.list_providers())
    ['openai', 'anthropic', 'ollama', 'gemini', 'groq', 'mistral']
"""

from lib.llm.analyzer import LLMAnalyzer, AnalysisStats
from lib.llm.base import LLMProvider, ProviderRegistry, RateLimitInfo

__all__ = [
    "LLMAnalyzer",
    "AnalysisStats",
    "LLMProvider",
    "ProviderRegistry",
    "RateLimitInfo",
]
