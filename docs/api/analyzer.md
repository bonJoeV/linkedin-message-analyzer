# LinkedInMessageAnalyzer

The core analysis engine for processing LinkedIn message exports.

## Import

```python
from lib import LinkedInMessageAnalyzer
```

## Constructor

```python
LinkedInMessageAnalyzer(
    messages_csv_path: str | Path,
    user_profile: UserProfile | None = None,
    llm_analyzer: LLMAnalyzer | None = None,
)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `messages_csv_path` | `str \| Path` | Path to LinkedIn messages.csv export |
| `user_profile` | `UserProfile \| None` | Optional profile for personalization |
| `llm_analyzer` | `LLMAnalyzer \| None` | Optional LLM for AI analysis |

### Example

```python
from lib import LinkedInMessageAnalyzer, UserProfile

profile = UserProfile(name="Jane Doe", industries=['tech'])
analyzer = LinkedInMessageAnalyzer('messages.csv', user_profile=profile)
```

## Methods

### load_messages()

Load and parse the LinkedIn CSV export.

```python
analyzer.load_messages() -> LinkedInMessageAnalyzer
```

Returns `self` for method chaining.

**Raises:**
- `FileLoadError`: File not found or unreadable
- `InvalidCSVError`: Invalid CSV structure

### run_all_analyses()

Run all detection analyses on loaded messages.

```python
analyzer.run_all_analyses() -> LinkedInMessageAnalyzer
```

Returns `self` for method chaining.

### Individual Analysis Methods

Run specific analyses independently:

```python
analyzer.analyze_time_requests()      # Detect time/meeting requests
analyzer.detect_financial_advisors()  # Find FA outreach
analyzer.detect_franchise_consultants()
analyzer.detect_expert_networks()
analyzer.detect_recruiters()
analyzer.detect_ai_generated()        # ChatGPT detection
analyzer.analyze_flattery()           # Score flattery
analyzer.detect_fake_personalization()
analyzer.detect_repeat_offenders()
analyzer.analyze_time_patterns()      # Hour/day patterns
```

### calculate_audacity_metrics()

Calculate time-request summary statistics.

```python
metrics = analyzer.calculate_audacity_metrics() -> dict
```

**Returns:**

```python
{
    'total_hours': 47.5,           # Total hours requested
    'hours_per_week': 4.2,         # Average weekly hours
    'percent_of_work_week': 10.5,  # As % of 40-hour week
    'yearly_projection': 218.4,    # If you said yes to everyone
    'request_count': 156,          # Number of time requests
}
```

### get_flattery_summary()

Get flattery analysis summary.

```python
summary = analyzer.get_flattery_summary() -> dict
```

**Returns:**

```python
{
    'total_with_flattery': 312,
    'avg_score': 4.2,
    'max_score': 14,
    'top_phrases': [('impressive', 89), ('thought leader', 45), ...],
}
```

### get_weekly_summary()

Get per-week breakdown of outreach.

```python
summary = analyzer.get_weekly_summary(weeks_back: int = 12) -> dict
```

**Returns:**

```python
{
    '2025-W01': {
        'time_requests': 12,
        'financial_advisors': 3,
        'total_messages': 45,
    },
    '2025-W02': {...},
}
```

### get_conversation_threads()

Group parsed messages into reusable conversation-level threads.

```python
threads = analyzer.get_conversation_threads(my_name: str | None = None) -> dict[str, ConversationThread]
```

**Returns:**

```python
{
    'abc123': {
        'conversation_id': 'abc123',
        'conversation_title': 'Reaching out',
        'participants': ['Jane Doe', 'John Smith'],
        'primary_sender': 'John Smith',
        'message_count': 3,
        'incoming_count': 2,
        'outgoing_count': 1,
        'first_message_at': datetime(...),
        'last_message_at': datetime(...),
        'has_response_from_me': True,
        'messages': [...],
    },
}
```

### get_sender_summaries()

Roll up thread activity into sender-level summaries for ranking or triage.

```python
summaries = analyzer.get_sender_summaries(my_name: str | None = None) -> list[SenderSummary]
```

**Returns:**

```python
[
    {
        'sender': 'John Smith',
        'conversation_count': 2,
        'message_count': 4,
        'responded_conversation_count': 0,
        'unanswered_conversation_count': 2,
        'unanswered_message_count': 4,
        'has_received_response': False,
        'first_contact': datetime(...),
        'last_contact': datetime(...),
        'conversation_ids': ['abc123', 'def456'],
    },
]
```

### get_unanswered_threads()

Return unanswered incoming threads ranked by persistence and recency.

```python
threads = analyzer.get_unanswered_threads(
    my_name: str | None = None,
    min_incoming_messages: int = 2,
) -> list[ConversationThread]
```

**Returns:**

```python
[
    {
        'conversation_id': 'abc123',
        'conversation_title': 'Quick intro',
        'primary_sender': 'John Smith',
        'incoming_count': 3,
        'message_count': 3,
        'has_response_from_me': False,
        'last_message_at': datetime(...),
        'messages': [...],
    },
]
```

### get_thread_triage_queue()

Return scored thread triage items with category labels.

```python
items = analyzer.get_thread_triage_queue(
    my_name: str | None = None,
    include_responded: bool = False,
) -> list[ThreadTriageItem]
```

**Returns:**

```python
[
    {
        'conversation_id': 'abc123',
        'primary_sender': 'John Smith',
        'incoming_count': 3,
        'triage_score': 47,
        'labels': ['time_request', 'fake_personalization'],
        'last_message_at': datetime(...),
        'latest_message_preview': 'Checking back in...',
    },
]
```

### run_llm_analysis()

Run LLM-powered analysis on messages (requires llm_analyzer).

```python
analyzer.run_llm_analysis(
    filter_mode: str = 'time_requests',  # 'all', 'time_requests', 'suspicious'
    max_messages: int = 50,
    progress_callback: Callable | None = None,
) -> LinkedInMessageAnalyzer
```

## Properties / Attributes

After running analyses, access results via these attributes:

### Message Collections

| Attribute | Type | Description |
|-----------|------|-------------|
| `messages` | `list[dict]` | All parsed messages |
| `time_requests` | `list[dict]` | Messages requesting time |
| `financial_advisor_messages` | `list[dict]` | FA outreach |
| `franchise_consultant_messages` | `list[dict]` | Franchise pitches |
| `expert_network_messages` | `list[dict]` | Expert network outreach |
| `recruiter_messages` | `list[dict]` | Recruiter messages |
| `ai_generated_messages` | `list[dict]` | AI-detected messages |
| `fake_personalization_messages` | `list[dict]` | Template detection |
| `template_messages` | `list[dict]` | Obvious templates |
| `crypto_hustler_messages` | `list[dict]` | Crypto/web3 spam |
| `mlm_messages` | `list[dict]` | MLM/pyramid schemes |

### Analysis Results

| Attribute | Type | Description |
|-----------|------|-------------|
| `flattery_scores` | `list[dict]` | Messages with flattery scores |
| `repeat_offenders` | `dict[str, dict]` | Senders who message 2+ times |
| `time_patterns` | `dict` | Hour/day distribution |
| `date_range` | `tuple[datetime, datetime]` | Date range of messages |
| `llm_analyses` | `list[dict]` | LLM analysis results |

## Message Structure

Each message in `analyzer.messages` has this structure:

```python
{
    'conversation_id': 'abc123',
    'sender': 'John Smith',
    'date': datetime(2025, 1, 15, 10, 30),
    'content': 'Message text...',
    'subject': 'Message subject',
    'direction': 'INCOMING',  # or 'OUTGOING'
}
```

## Complete Example

```python
from lib import LinkedInMessageAnalyzer, UserProfile

# Setup
profile = UserProfile(
    name="Jane Doe",
    industries=['tech', 'finance'],
)

analyzer = LinkedInMessageAnalyzer('messages.csv', user_profile=profile)

# Load and analyze
analyzer.load_messages().run_all_analyses()

# Access results
print(f"Analyzed {len(analyzer.messages)} messages")
print(f"Date range: {analyzer.date_range[0]} to {analyzer.date_range[1]}")

# Metrics
metrics = analyzer.calculate_audacity_metrics()
print(f"\nAudacity Metrics:")
print(f"  Hours requested per week: {metrics['hours_per_week']:.1f}")
print(f"  Yearly projection: {metrics['yearly_projection']:.0f} hours")

# Categories
print(f"\nMessage Types:")
print(f"  Time requests: {len(analyzer.time_requests)}")
print(f"  Financial advisors: {len(analyzer.financial_advisor_messages)}")
print(f"  AI-generated: {len(analyzer.ai_generated_messages)}")
print(f"  Repeat offenders: {len(analyzer.repeat_offenders)}")

# Top flattery
flattery = analyzer.get_flattery_summary()
print(f"\nFlattery Index:")
print(f"  Messages with flattery: {flattery['total_with_flattery']}")
print(f"  Highest score: {flattery['max_score']}")
```
