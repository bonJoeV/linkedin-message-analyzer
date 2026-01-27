# Architecture Overview

This document describes the architecture and data flow of the LinkedIn Message Analyzer.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CLI (lib/cli.py)                            │
│  Parses arguments, orchestrates analysis, calls reporters          │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  LinkedInMessageAnalyzer (lib/analyzer.py)          │
│  Core engine: loads CSV, runs analyses, stores results             │
└─────────────────────────────────────────────────────────────────────┘
           │                        │                        │
           ▼                        ▼                        ▼
┌─────────────────┐    ┌─────────────────────┐    ┌─────────────────┐
│ Pattern System  │    │   LLM Analyzer      │    │  User Profile   │
│ lib/patterns/   │    │   lib/llm.py        │    │  lib/profile.py │
└─────────────────┘    └─────────────────────┘    └─────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Reporters (lib/reporters/)                     │
│  console.py │ json_export.py │ html.py │ stats.py                  │
└─────────────────────────────────────────────────────────────────────┘
```

## Data Flow

```
messages.csv
     │
     ▼ [Load & Parse]
┌─────────────┐
│ Raw Rows    │  CSV parsing, encoding detection, date parsing
└─────────────┘
     │
     ▼ [Normalize]
┌─────────────┐
│ Messages[]  │  Structured message objects with typed fields
└─────────────┘
     │
     ├──────────────────────────────────────────┐
     │                                          │
     ▼ [Pattern Analysis]                       ▼ [LLM Analysis]
┌─────────────────────┐              ┌─────────────────────┐
│ Pattern Matchers    │              │ LLM API Calls       │
│ - Time requests     │              │ - Intent classify   │
│ - FA detection      │              │ - Authenticity      │
│ - AI detection      │              │ - Recommendations   │
│ - Flattery scoring  │              └─────────────────────┘
└─────────────────────┘                         │
     │                                          │
     ▼                                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        Analysis Results                             │
│  time_requests[] │ fa_messages[] │ flattery_scores[] │ llm_analyses│
└─────────────────────────────────────────────────────────────────────┘
     │
     ▼ [Format]
┌─────────────────────────────────────────────────────────────────────┐
│                          Output                                     │
│  Console Report │ JSON File │ HTML Report │ Bingo Card             │
└─────────────────────────────────────────────────────────────────────┘
```

## Component Details

### CLI Layer (`lib/cli.py`)

Entry point that:
- Parses command-line arguments
- Initializes components (UserProfile, LLMAnalyzer)
- Creates and configures LinkedInMessageAnalyzer
- Calls appropriate reporters based on flags

### Core Analyzer (`lib/analyzer.py`)

The main analysis engine:

```python
class LinkedInMessageAnalyzer:
    # Initialization
    def __init__(csv_path, user_profile, llm_analyzer)

    # Data Loading
    def load_messages() -> self          # Parse CSV
    def _detect_encoding() -> str        # Handle encodings
    def _parse_row(row) -> dict          # Normalize row

    # Analysis Methods
    def run_all_analyses() -> self       # Run everything
    def analyze_time_requests()          # Individual analyses
    def detect_financial_advisors()
    def detect_ai_generated()
    def analyze_flattery()
    # ... etc

    # Results
    def calculate_audacity_metrics() -> dict
    def get_flattery_summary() -> dict
    def get_weekly_summary() -> dict
```

### Pattern System (`lib/patterns/`)

Extensible regex pattern matching:

```
lib/patterns/
├── base.py              # PatternRegistry, PatternMatcher classes
├── time_requests.py     # Time/meeting request patterns
├── outreach.py          # FA, recruiters, expert networks
├── quality.py           # Flattery, fake personalization
├── ai_generated.py      # ChatGPT/AI detection
├── linkedin_lunatics.py # Humblebrags, crypto, MLM
└── sales_coaching.py    # Sales pitches, courses
```

**Key Classes:**

- `PatternRegistry`: Global registry for pattern categories
- `PatternMatcher`: Simple match/no-match detection
- `WeightedPatternMatcher`: Scoring with weighted patterns

### LLM Integration (`lib/llm.py`)

Optional AI-powered analysis:

```python
class LLMAnalyzer:
    def __init__(provider, api_key, model)
    def analyze_message(content, sender_name, context) -> dict
    def analyze_batch(messages, progress_callback) -> list[dict]
```

**Providers:** OpenAI, Anthropic (more planned)

**Returns:**
```python
{
    'intent': 'sales_pitch',
    'authenticity_score': 3,
    'personalization_quality': 'template',
    'manipulation_tactics': ['urgency', 'flattery'],
    'red_flags': ['unsolicited pitch'],
    'recommendation': 'ignore',
}
```

### User Profile (`lib/profile.py`)

Personalization context:

```python
class UserProfile:
    name: str
    industries: list[str]
    roles: list[str]
    interests: list[str]
    ignore_senders: list[str]
```

**Industry Presets:** `tech`, `finance`, `healthcare`, `real_estate`, etc.

### Reporters (`lib/reporters/`)

Output formatting:

```
lib/reporters/
├── console.py      # Terminal output with ANSI formatting
├── json_export.py  # Structured JSON export
├── html.py         # Interactive HTML with SVG charts
└── stats.py        # Shareable statistics
```

### Supporting Modules

| Module | Purpose |
|--------|---------|
| `types.py` | TypedDict definitions (Message, TimeRequest, etc.) |
| `constants.py` | Magic numbers, limits, defaults |
| `exceptions.py` | Custom exception classes |
| `config.py` | Configuration file loading |
| `bingo.py` | Bingo card generation |
| `anonymizer.py` | Privacy-preserving name anonymization |
| `response_generator.py` | Decline response templates |

## Extension Points

### 1. Adding Patterns

Register new patterns without modifying core code:

```python
from lib.patterns import register_pattern
register_pattern('my_category', [r'\bmy pattern\b'])
```

### 2. Custom Reporters

Create new output formats:

```python
class MyReporter:
    def __init__(self, analyzer: LinkedInMessageAnalyzer):
        self.analyzer = analyzer

    def generate(self) -> str:
        # Access self.analyzer.time_requests, etc.
        return formatted_output
```

### 3. LLM Providers

Add new providers by extending the LLM module (plugin system planned).

### 4. Analysis Methods

Add new detection methods to LinkedInMessageAnalyzer:

```python
def detect_my_category(self) -> None:
    matcher = PatternMatcher(MY_PATTERNS)
    for msg in self.messages:
        if matcher.has_match(msg['content']):
            self.my_category_messages.append(msg)
```

## Error Handling

Custom exceptions in `lib/exceptions.py`:

```python
LinkedInAnalyzerError      # Base exception
├── FileLoadError          # File not found/unreadable
├── InvalidCSVError        # Bad CSV structure
├── DateParseError         # Unparseable date
└── ConfigurationError     # Invalid config
```

## Configuration

Two configuration methods:

1. **CLI Arguments**: `--my-name`, `--industries`, etc.
2. **Config File**: `config.json` with full settings

```json
{
  "user_profile": {
    "name": "Your Name",
    "industries": ["tech"]
  },
  "custom_patterns": {
    "recruiter": ["\\bmy extra pattern\\b"]
  }
}
```

## Performance Considerations

- **Pattern Compilation**: Regex patterns are pre-compiled on init
- **Lazy Loading**: LLM client initialized on first use
- **Rate Limiting**: 0.2s delay between LLM API calls
- **Encoding Detection**: Samples first 10KB for charset detection
- **Message Filtering**: LLM analysis can filter by category to reduce costs
