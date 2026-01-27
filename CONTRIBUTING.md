# Contributing to LinkedIn Message Analyzer

Thanks for wanting to contribute! Whether you've found a new type of LinkedIn spam or want to add a creative feature, your help is welcome.

## Development Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/linkedin-message-analyzer.git
cd linkedin-message-analyzer

# Install dependencies
pip install -r requirements.txt

# Optional: Install LLM dependencies for testing
pip install openai anthropic
```

## Project Structure

```
linkedin-message-analyzer/
├── linkedin_message_analyzer.py   # Entry point (delegates to lib/cli.py)
├── lib/
│   ├── __init__.py               # Public API exports
│   ├── analyzer.py               # Core LinkedInMessageAnalyzer class
│   ├── cli.py                    # Command-line interface
│   ├── llm.py                    # LLM-powered analysis
│   ├── config.py                 # Configuration loading
│   ├── profile.py                # User profile management
│   ├── types.py                  # TypedDict definitions
│   ├── constants.py              # Constants and limits
│   ├── exceptions.py             # Custom exceptions
│   ├── response_generator.py     # Decline response templates
│   ├── bingo.py                  # Bingo card generator
│   ├── anonymizer.py             # Name anonymization
│   ├── patterns/                 # Pattern detection system
│   │   ├── base.py               # PatternRegistry, PatternMatcher
│   │   ├── time_requests.py      # Time request patterns
│   │   ├── outreach.py           # FA, recruiters, expert networks
│   │   ├── quality.py            # Flattery, fake personalization
│   │   ├── ai_generated.py       # AI/ChatGPT detection
│   │   ├── linkedin_lunatics.py  # Humblebrags, crypto, MLM
│   │   └── sales_coaching.py     # Sales pitches, courses
│   └── reporters/                # Output formatters
│       ├── console.py            # Terminal output
│       ├── json_export.py        # JSON export
│       ├── html.py               # HTML reports
│       └── stats.py              # Statistics
├── samples/                       # Sample CSV files for testing
└── docs/                          # Documentation
```

## Adding Custom Patterns

The pattern system is the easiest way to extend the analyzer.

### Quick Start

Add patterns to an existing category:

```python
from lib.patterns import register_pattern

# Add to existing category
register_pattern('recruiter', [
    r'\bmy new recruiter phrase\b',
    r'\bexciting stealth startup\b',
])
```

### Creating a New Pattern Category

1. Create a new file in `lib/patterns/`:

```python
# lib/patterns/my_category.py
"""Patterns for detecting [your category]."""

MY_CATEGORY_PATTERNS = [
    r'\bpattern one\b',
    r'\bpattern two\b',
    r'(?:phrase with|alternatives)\s+here',
]

# For patterns that should contribute to a score:
MY_WEIGHTED_PATTERNS = [
    (r'\bminor indicator\b', 1),     # 1 point
    (r'\bstrong indicator\b', 3),    # 3 points
    (r'\bdead giveaway\b', 5),       # 5 points
]
```

2. Register in `lib/patterns/base.py`:

```python
# In _initialize_default_patterns():
from lib.patterns.my_category import MY_CATEGORY_PATTERNS, MY_WEIGHTED_PATTERNS

registry.register('my_category', MY_CATEGORY_PATTERNS)
registry.register_weighted('my_category_weighted', MY_WEIGHTED_PATTERNS)
```

3. Use in `lib/analyzer.py`:

```python
# In LinkedInMessageAnalyzer:
from lib.patterns import PatternMatcher, get_pattern_registry

registry = get_pattern_registry()
self.my_matcher = PatternMatcher(registry.get('my_category'))
```

### Pattern Writing Tips

- Use `\b` for word boundaries to avoid partial matches
- Use `(?:...)` for non-capturing groups
- Test patterns against sample messages before committing
- Keep patterns case-insensitive (the matcher handles this)

**Good patterns:**
```python
r'\bquick call\b'              # Matches "quick call" but not "quickcall"
r'\b(?:15|15-minute)\s+call\b' # Matches "15 call" or "15-minute call"
r'northwestern\s*mutual'       # Handles spacing variations
```

**Bad patterns:**
```python
r'call'                        # Too broad - matches "callback", "recall"
r'[A-Z]+'                      # Don't rely on case - text is lowercased
```

## Adding a New Reporter

Reporters format output in different ways (console, JSON, HTML).

### Creating a Custom Reporter

```python
# lib/reporters/my_reporter.py
"""Custom reporter for [format]."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lib.analyzer import LinkedInMessageAnalyzer


class MyReporter:
    """Outputs analysis in [format]."""

    def __init__(self, analyzer: 'LinkedInMessageAnalyzer'):
        self.analyzer = analyzer

    def generate(self) -> str:
        """Generate the report."""
        # Access analyzer data:
        # - self.analyzer.messages
        # - self.analyzer.time_requests
        # - self.analyzer.financial_advisors
        # - self.analyzer.calculate_audacity_metrics()
        # etc.
        return "Your formatted output"

    def save(self, filepath: str) -> None:
        """Save report to file."""
        content = self.generate()
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
```

## Code Style

- **Type hints**: Use throughout (Python 3.9+ syntax: `list[str]` not `List[str]`)
- **Docstrings**: Google style for public functions
- **Max line length**: 100 characters
- **Imports**: Standard library, then third-party, then local

Example:
```python
"""Module docstring."""

import re
from datetime import datetime
from typing import Any

import chardet  # Third-party

from lib.types import Message  # Local
from lib.exceptions import ConfigurationError


def my_function(text: str, count: int = 10) -> list[str]:
    """Short description.

    Args:
        text: The text to process
        count: Maximum items to return

    Returns:
        List of processed strings
    """
    ...
```

## Testing

### Manual Testing

```bash
# Basic test
python linkedin_message_analyzer.py samples/sample_tech.csv

# Test with LLM
export OPENAI_API_KEY="your-key"
python linkedin_message_analyzer.py samples/sample_tech.csv --llm openai

# Test specific output
python linkedin_message_analyzer.py samples/sample_tech.csv --export-json test.json
python linkedin_message_analyzer.py samples/sample_tech.csv --export-html test.html
```

### Testing Patterns

```python
# Quick pattern test
from lib.patterns import PatternMatcher

patterns = [r'\bmy new pattern\b']
matcher = PatternMatcher(patterns)

test_messages = [
    "This has my new pattern in it",
    "This should not match",
]

for msg in test_messages:
    print(f"{msg}: {matcher.has_match(msg)}")
```

## Pull Request Guidelines

1. **Keep PRs focused** - One feature or fix per PR
2. **Test your changes** - Run against sample CSVs
3. **Update docs** - If you add features, update README/docs
4. **Follow existing patterns** - Match the code style you see

### PR Checklist

- [ ] Tested with sample CSV files
- [ ] Type hints added for new functions
- [ ] Docstrings added for public functions
- [ ] README updated if needed
- [ ] No breaking changes to existing CLI flags

## Ideas for Contributions

### High Value
- New spam detection patterns (especially industry-specific)
- Improved HTML report visualizations
- Browser extension for real-time analysis
- Advanced LLM features (conversation summarization, message clustering)

### Medium Value
- New bingo card themes
- Additional response tones for decline templates
- Performance optimizations for large CSV files

### Fun Ideas
- New snarky output messages
- Easter eggs in reports
- Achievement badges ("Survived 100 FA pitches!")

## Questions?

Open an issue or start a discussion!
