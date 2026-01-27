"""Reporter system for LinkedIn Message Analyzer.

Provides different output formats for analysis results.

Example - Using built-in reporters:
    >>> from lib.reporters import ConsoleReporter, JSONReporter
    >>> reporter = ConsoleReporter()
    >>> reporter.generate(analyzer)

Example - Registering custom reporters:
    >>> from lib.reporters import register_reporter
    >>> @register_reporter('csv')
    ... class CSVReporter:
    ...     def generate(self, analyzer): ...
"""

from lib.reporters.console import ConsoleReporter
from lib.reporters.json_export import JSONReporter
from lib.reporters.html import HTMLReporter, generate_html_report
from lib.reporters.stats import StatsDashboard, generate_stats_dashboard

# Reporter registry for extensibility
_reporter_registry: dict[str, type] = {
    'console': ConsoleReporter,
    'json': JSONReporter,
    'html': HTMLReporter,
    'stats': StatsDashboard,
}


def register_reporter(name: str):
    """Decorator to register a custom reporter.

    Args:
        name: Name to register the reporter under

    Example:
        >>> @register_reporter('csv')
        ... class CSVReporter:
        ...     def generate(self, analyzer): ...
    """
    def decorator(cls):
        _reporter_registry[name] = cls
        return cls
    return decorator


def get_reporter(name: str):
    """Get a reporter class by name.

    Args:
        name: Reporter name

    Returns:
        Reporter class

    Raises:
        KeyError: If reporter not found
    """
    if name not in _reporter_registry:
        available = ', '.join(_reporter_registry.keys())
        raise KeyError(f"Unknown reporter: {name}. Available: {available}")
    return _reporter_registry[name]


def list_reporters() -> list[str]:
    """List all registered reporter names."""
    return list(_reporter_registry.keys())


__all__ = [
    'ConsoleReporter',
    'JSONReporter',
    'HTMLReporter',
    'generate_html_report',
    'StatsDashboard',
    'generate_stats_dashboard',
    'register_reporter',
    'get_reporter',
    'list_reporters',
]
