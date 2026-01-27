"""Base pattern matching utilities and registry."""

import re
from typing import Callable


class PatternRegistry:
    """Registry for pattern collections with plugin support.

    Allows registering custom patterns for different categories
    without modifying core code.
    """

    def __init__(self) -> None:
        self._patterns: dict[str, list[str]] = {}
        self._weighted_patterns: dict[str, list[tuple[str, int]]] = {}

    def register(self, name: str, patterns: list[str]) -> None:
        """Register a pattern collection.

        Args:
            name: Category name (e.g., 'time_requests', 'financial_advisor')
            patterns: List of regex patterns
        """
        self._patterns[name] = patterns

    def register_weighted(self, name: str, patterns: list[tuple[str, int]]) -> None:
        """Register a weighted pattern collection.

        Args:
            name: Category name
            patterns: List of (pattern, weight) tuples
        """
        self._weighted_patterns[name] = patterns

    def get(self, name: str) -> list[str]:
        """Get patterns for a category.

        Args:
            name: Category name

        Returns:
            List of patterns, or empty list if not found
        """
        return self._patterns.get(name, [])

    def get_weighted(self, name: str) -> list[tuple[str, int]]:
        """Get weighted patterns for a category.

        Args:
            name: Category name

        Returns:
            List of (pattern, weight) tuples, or empty list if not found
        """
        return self._weighted_patterns.get(name, [])

    def extend(self, name: str, patterns: list[str]) -> None:
        """Add patterns to an existing category.

        Args:
            name: Category name
            patterns: Additional patterns to add
        """
        if name not in self._patterns:
            self._patterns[name] = []
        self._patterns[name].extend(patterns)

    def list_categories(self) -> list[str]:
        """List all registered pattern categories."""
        return list(set(self._patterns.keys()) | set(self._weighted_patterns.keys()))


class PatternMatcher:
    """Utility class for matching text against regex patterns."""

    def __init__(self, patterns: list[str]) -> None:
        """Initialize with a list of regex patterns.

        Args:
            patterns: List of regex pattern strings
        """
        self.patterns = patterns
        # Pre-compile patterns for performance
        self._compiled = [re.compile(p, re.IGNORECASE) for p in patterns]

    def match(self, text: str) -> list[str]:
        """Find all patterns that match the text.

        Args:
            text: Text to search in

        Returns:
            List of patterns that matched
        """
        if not text:
            return []

        matches: list[str] = []
        text_lower = text.lower()

        for pattern, compiled in zip(self.patterns, self._compiled):
            if compiled.search(text_lower):
                matches.append(pattern)

        return matches

    def has_match(self, text: str) -> bool:
        """Check if any pattern matches the text.

        Args:
            text: Text to search in

        Returns:
            True if any pattern matches
        """
        if not text:
            return False

        text_lower = text.lower()
        return any(compiled.search(text_lower) for compiled in self._compiled)


class WeightedPatternMatcher:
    """Utility class for matching text against weighted patterns."""

    def __init__(self, patterns: list[tuple[str, int]]) -> None:
        """Initialize with weighted patterns.

        Args:
            patterns: List of (regex_pattern, weight) tuples
        """
        self.patterns = patterns
        self._compiled = [(re.compile(p, re.IGNORECASE), w) for p, w in patterns]

    def score(self, text: str) -> tuple[int, list[str]]:
        """Calculate weighted score for text.

        Args:
            text: Text to search in

        Returns:
            Tuple of (total_score, list of matched patterns)
        """
        if not text:
            return 0, []

        total_score = 0
        matched: list[str] = []
        text_lower = text.lower()

        for (pattern, weight), (compiled, _) in zip(self.patterns, self._compiled):
            matches = compiled.findall(text_lower)
            if matches:
                total_score += weight * len(matches)
                matched.extend(matches if isinstance(matches[0], str) else [m[0] for m in matches])

        return total_score, matched


# Global registry instance
_registry: PatternRegistry | None = None


def get_pattern_registry() -> PatternRegistry:
    """Get the global pattern registry, initializing if needed."""
    global _registry
    if _registry is None:
        _registry = PatternRegistry()
        _initialize_default_patterns(_registry)
    return _registry


def register_pattern(category: str, patterns: list[str]) -> None:
    """Register custom patterns for a category.

    This is the main API for extending the analyzer with custom patterns.

    Args:
        category: Pattern category name
        patterns: List of regex patterns to add

    Example:
        >>> from lib.patterns import register_pattern
        >>> register_pattern('custom_spam', [
        ...     r'\\bmy custom pattern\\b',
        ...     r'\\banother pattern\\b',
        ... ])
    """
    get_pattern_registry().extend(category, patterns)


def _initialize_default_patterns(registry: PatternRegistry) -> None:
    """Initialize the registry with default patterns."""
    from lib.patterns.time_requests import (
        TIME_REQUEST_KEYWORDS,
        TIME_ESTIMATES,
    )
    from lib.patterns.outreach import (
        FINANCIAL_ADVISOR_PATTERNS,
        FRANCHISE_CONSULTANT_PATTERNS,
        EXPERT_NETWORK_PATTERNS,
        ANGEL_INVESTOR_PATTERNS,
        RECRUITER_PATTERNS,
    )
    from lib.patterns.quality import (
        FAKE_PERSONALIZATION_PATTERNS,
        FLATTERY_PATTERNS,
        TEMPLATE_INDICATORS,
    )

    # Register all default patterns
    registry.register('time_requests', TIME_REQUEST_KEYWORDS)
    registry.register('financial_advisor', FINANCIAL_ADVISOR_PATTERNS)
    registry.register('franchise_consultant', FRANCHISE_CONSULTANT_PATTERNS)
    registry.register('expert_network', EXPERT_NETWORK_PATTERNS)
    registry.register('angel_investor', ANGEL_INVESTOR_PATTERNS)
    registry.register('recruiter', RECRUITER_PATTERNS)
    registry.register('fake_personalization', FAKE_PERSONALIZATION_PATTERNS)
    registry.register('template', TEMPLATE_INDICATORS)

    # Register weighted patterns
    registry.register_weighted('flattery', FLATTERY_PATTERNS)
