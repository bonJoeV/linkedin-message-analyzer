# Pattern System

The pattern system enables extensible detection of message categories using regex patterns.

## Overview

The analyzer uses regex patterns to detect various message types:

- **Simple patterns**: Match or no match
- **Weighted patterns**: Contribute to a score (used for AI detection, flattery)

## Quick Start

### Adding Patterns to Existing Categories

```python
from lib.patterns import register_pattern

# Extend an existing category
register_pattern('recruiter', [
    r'\bstealth startup\b',
    r'\bground floor opportunity\b',
])

# Now these patterns will be detected as recruiter messages
```

### Using Pattern Matchers Directly

```python
from lib.patterns import PatternMatcher, WeightedPatternMatcher

# Simple matching
matcher = PatternMatcher([
    r'\bquick call\b',
    r'\b15 minutes\b',
])

if matcher.has_match("Can we hop on a quick call?"):
    print("Time request detected!")

# Get all matches
matches = matcher.match("I'd love a quick call, just 15 minutes")
print(matches)  # ['quick call', '15 minutes']
```

### Weighted Scoring

```python
from lib.patterns import WeightedPatternMatcher

patterns = [
    (r'\bimpressive\b', 1),      # 1 point
    (r'\bthought leader\b', 2),  # 2 points
    (r'\blove your work\b', 3),  # 3 points
]

matcher = WeightedPatternMatcher(patterns)
score, matches = matcher.score("Your impressive work as a thought leader...")
print(f"Score: {score}, Matches: {matches}")  # Score: 3, Matches: ['impressive', 'thought leader']
```

## Pattern Registry

The global registry manages all pattern categories.

### Accessing the Registry

```python
from lib.patterns import get_pattern_registry

registry = get_pattern_registry()

# List all categories
categories = registry.list_categories()
print(categories)  # ['time_requests', 'financial_advisor', 'recruiter', ...]

# Get patterns for a category
patterns = registry.get('recruiter')
```

### Built-in Categories

| Category | Type | Description |
|----------|------|-------------|
| `time_requests` | Simple | Meeting/call requests |
| `financial_advisor` | Simple | FA outreach patterns |
| `franchise_consultant` | Simple | Franchise pitches |
| `expert_network` | Simple | GLG, AlphaSights, etc. |
| `angel_investor` | Simple | Investment pitches |
| `recruiter` | Simple | Recruiting outreach |
| `fake_personalization` | Simple | Template indicators |
| `template` | Simple | Obvious templates |
| `flattery` | Weighted | Flattery scoring |
| `ai_generated` | Weighted | ChatGPT detection |

## Creating Custom Pattern Files

### 1. Create the Pattern File

```python
# lib/patterns/my_category.py
"""Custom patterns for detecting [your category]."""

# Simple patterns (match = detected)
MY_CATEGORY_PATTERNS = [
    r'\bexact phrase\b',
    r'(?:alternative|options)\s+here',
    r'\d+[x%]\s+(?:return|growth)',  # Numbers with keywords
]

# Weighted patterns (contribute to score)
MY_CATEGORY_WEIGHTED = [
    (r'\bminor indicator\b', 1),
    (r'\bmoderate indicator\b', 2),
    (r'\bstrong indicator\b', 3),
]
```

### 2. Register in base.py

```python
# In lib/patterns/base.py, add to _initialize_default_patterns():

from lib.patterns.my_category import MY_CATEGORY_PATTERNS, MY_CATEGORY_WEIGHTED

registry.register('my_category', MY_CATEGORY_PATTERNS)
registry.register_weighted('my_category_weighted', MY_CATEGORY_WEIGHTED)
```

### 3. Use in Analyzer

```python
# In lib/analyzer.py:

from lib.patterns import PatternMatcher, WeightedPatternMatcher, get_pattern_registry

class LinkedInMessageAnalyzer:
    def __init__(self, ...):
        ...
        registry = get_pattern_registry()
        self._my_category_matcher = PatternMatcher(registry.get('my_category'))
        self.my_category_messages: list[dict] = []

    def detect_my_category(self) -> None:
        """Detect my custom category."""
        for msg in self.messages:
            if self._my_category_matcher.has_match(msg.get('content', '')):
                self.my_category_messages.append(msg)
```

## Pattern Writing Guide

### Word Boundaries

Use `\b` to match whole words:

```python
r'\bcall\b'      # Matches "call" but not "callback"
r'\bFA\b'        # Matches "FA" but not "FAQ"
```

### Alternatives

Use `(?:...|...)` for alternatives:

```python
r'\b(?:quick|brief|short)\s+call\b'  # "quick call", "brief call", etc.
r'(?:15|15-minute|fifteen)\s+minutes?'
```

### Optional Parts

Use `?` for optional elements:

```python
r'\bcoffee\s*(?:chat)?\b'  # "coffee" or "coffee chat"
r'\b(?:just\s+)?15\s+minutes?\b'  # "15 minutes" or "just 15 minutes"
```

### Case Sensitivity

Patterns are matched case-insensitively by default:

```python
r'\bCEO\b'  # Matches "CEO", "ceo", "Ceo"
```

### Testing Patterns

```python
from lib.patterns import PatternMatcher

patterns = [r'\bmy new pattern\b']
matcher = PatternMatcher(patterns)

test_cases = [
    ("This has my new pattern", True),
    ("This has mynewpattern", False),  # No word boundary
    ("This is unrelated", False),
]

for text, expected in test_cases:
    result = matcher.has_match(text)
    status = "PASS" if result == expected else "FAIL"
    print(f"{status}: '{text}' -> {result}")
```

## Existing Pattern Examples

### Time Request Patterns

```python
TIME_REQUEST_KEYWORDS = [
    r'\bquick call\b',
    r'\bcoffee chat\b',
    r'\bpick your brain\b',
    r'\b15 minutes?\b',
    r'\bhalf an hour\b',
    r'\blet\'s connect\b',
    r'\bschedule.*(?:call|meeting|chat)\b',
]
```

### AI Detection (Weighted)

```python
AI_GENERATED_PATTERNS = [
    (r'\bi hope this (?:message |email )?finds you well\b', 3),
    (r'\bi wanted to reach out\b', 2),
    (r'\bin today\'s fast-paced\b', 2),
    (r'\bsynergy\b', 1),
    (r'\bleverage\b', 1),
    (r'\bthought leader\b', 2),
]
```

### Flattery (Weighted)

```python
FLATTERY_PATTERNS = [
    (r'\bimpressive\b', 1),
    (r'\bincredible\b', 1),
    (r'\blove what you\'re doing\b', 2),
    (r'\byour profile stood out\b', 2),
    (r'\bthought leader\b', 2),
    (r'\btruly inspiring\b', 3),
]
```

## API Reference

### PatternRegistry

```python
class PatternRegistry:
    def register(self, name: str, patterns: list[str]) -> None
    def register_weighted(self, name: str, patterns: list[tuple[str, int]]) -> None
    def get(self, name: str) -> list[str]
    def get_weighted(self, name: str) -> list[tuple[str, int]]
    def extend(self, name: str, patterns: list[str]) -> None
    def list_categories(self) -> list[str]
```

### PatternMatcher

```python
class PatternMatcher:
    def __init__(self, patterns: list[str]) -> None
    def match(self, text: str) -> list[str]  # Returns all matching patterns
    def has_match(self, text: str) -> bool   # Returns True if any match
```

### WeightedPatternMatcher

```python
class WeightedPatternMatcher:
    def __init__(self, patterns: list[tuple[str, int]]) -> None
    def score(self, text: str) -> tuple[int, list[str]]  # Returns (score, matches)
```

### Convenience Functions

```python
def register_pattern(category: str, patterns: list[str]) -> None
def get_pattern_registry() -> PatternRegistry
```
