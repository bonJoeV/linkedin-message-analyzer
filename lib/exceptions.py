"""Custom exceptions for LinkedIn Message Analyzer."""


class LinkedInAnalyzerError(Exception):
    """Base exception for LinkedIn Message Analyzer."""
    pass


class FileLoadError(LinkedInAnalyzerError):
    """Raised when the CSV file cannot be loaded."""
    pass


class InvalidCSVError(LinkedInAnalyzerError):
    """Raised when the CSV file has invalid structure."""
    pass


class DateParseError(LinkedInAnalyzerError):
    """Raised when a date cannot be parsed."""
    pass


class ConfigurationError(LinkedInAnalyzerError):
    """Raised when configuration is invalid."""
    pass


class LLMError(LinkedInAnalyzerError):
    """Base exception for LLM-related errors."""
    pass


class RateLimitError(LLMError):
    """Raised when API rate limit is hit (429).

    Attributes:
        retry_after: Seconds to wait before retrying (if provided)
        limit_type: Type of limit hit (requests, tokens, etc.)
    """

    def __init__(
        self,
        message: str,
        retry_after: float | None = None,
        limit_type: str | None = None,
    ):
        super().__init__(message)
        self.retry_after = retry_after
        self.limit_type = limit_type


class QuotaExhaustedError(LLMError):
    """Raised when API quota/credits are exhausted (no retry possible).

    This is different from rate limiting - the user needs to add credits
    or wait for quota reset (usually daily/monthly).
    """
    pass


class ProviderUnavailableError(LLMError):
    """Raised when the provider is temporarily unavailable (503, 500, etc.)."""

    def __init__(self, message: str, retry_after: float | None = None):
        super().__init__(message)
        self.retry_after = retry_after
