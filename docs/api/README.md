# API Reference

Use the LinkedIn Message Analyzer programmatically in your own Python scripts.

## Quick Start

```python
from lib import LinkedInMessageAnalyzer, UserProfile

# Basic usage
analyzer = LinkedInMessageAnalyzer('messages.csv')
analyzer.load_messages().run_all_analyses()

# Access results
print(f"Total messages: {len(analyzer.messages)}")
print(f"Time requests: {len(analyzer.time_requests)}")

# Get metrics
metrics = analyzer.calculate_audacity_metrics()
print(f"Hours requested per week: {metrics['hours_per_week']}")
```

## Installation for Programmatic Use

```bash
pip install -r requirements.txt
```

## Core Classes

### LinkedInMessageAnalyzer

The main analysis engine. See [analyzer.md](analyzer.md) for full documentation.

```python
from lib import LinkedInMessageAnalyzer

analyzer = LinkedInMessageAnalyzer(
    messages_csv_path='messages.csv',
    user_profile=None,  # Optional UserProfile
    llm_analyzer=None,  # Optional LLMAnalyzer
)
```

### UserProfile

Customize analysis based on your industry and preferences. See [profile.md](profile.md).

```python
from lib import UserProfile, INDUSTRY_PRESETS

profile = UserProfile(
    name="Your Name",
    industries=['tech', 'finance'],
    roles=['software engineer', 'tech lead'],
    ignore_senders=['Colleague Name'],
)
```

### LLMAnalyzer

Enable AI-powered analysis. See [llm.md](llm.md).

```python
from lib import LLMAnalyzer

llm = LLMAnalyzer(provider='openai', api_key='sk-...', model='gpt-4.1-mini')
```

If you prefer config-driven defaults, `config.json` now supports an `llm` block with `provider`, `model`, `max_messages`, `filter`, and `provider_options`.

### Pattern System

Extend detection with custom patterns. See [patterns.md](patterns.md).

```python
from lib.patterns import register_pattern, PatternMatcher

# Add custom patterns
register_pattern('my_category', [r'\bmy pattern\b'])

# Use pattern matcher directly
matcher = PatternMatcher([r'\bquick call\b', r'\bcoffee chat\b'])
if matcher.has_match(message_text):
    print("Time request detected!")
```

## Module Reference

| Module | Description |
|--------|-------------|
| [analyzer.md](analyzer.md) | LinkedInMessageAnalyzer class |
| [patterns.md](patterns.md) | Pattern matching system |
| [reporters.md](reporters.md) | Output formatters |
| [profile.md](profile.md) | User profile system |
| [llm.md](llm.md) | LLM integration |
| [types.md](types.md) | Type definitions |

## Examples

See the [examples/](examples/) directory for complete working scripts:

- [basic_usage.py](examples/basic_usage.py) - Simple analysis script
- [custom_patterns.py](examples/custom_patterns.py) - Adding custom patterns
- [custom_reporter.py](examples/custom_reporter.py) - Creating custom output

## Common Patterns

### Analyze and Export to JSON

```python
from lib import LinkedInMessageAnalyzer
from lib.reporters import JSONExporter

analyzer = LinkedInMessageAnalyzer('messages.csv')
analyzer.load_messages().run_all_analyses()

exporter = JSONExporter(analyzer)
exporter.save('results.json')
```

### Filter Specific Message Types

```python
analyzer = LinkedInMessageAnalyzer('messages.csv')
analyzer.load_messages().run_all_analyses()

# Get only high-flattery messages
high_flattery = [
    msg for msg in analyzer.flattery_scores
    if msg['score'] >= 10
]

# Get AI-generated messages
ai_messages = analyzer.ai_generated_messages
```

### Custom Analysis Pipeline

```python
analyzer = LinkedInMessageAnalyzer('messages.csv')
analyzer.load_messages()

# Run only specific analyses
analyzer.analyze_time_requests()
analyzer.detect_financial_advisors()
# Skip other analyses...

# Access partial results
print(f"Time requests: {len(analyzer.time_requests)}")
```

### With LLM Enhancement

```python
from lib import LinkedInMessageAnalyzer, LLMAnalyzer

llm = LLMAnalyzer(provider='openai', model='gpt-4.1-mini')
analyzer = LinkedInMessageAnalyzer('messages.csv', llm_analyzer=llm)
analyzer.load_messages().run_all_analyses()

# LLM analysis results
for analysis in analyzer.llm_analyses:
    print(f"Intent: {analysis['intent']}")
    print(f"Authenticity: {analysis['authenticity_score']}/10")
```

For provider setup and current recommended models, see [llm.md](llm.md).
