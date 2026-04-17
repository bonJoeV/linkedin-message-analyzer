# LinkedIn Message Analyzer

**Finally, data-driven proof that your LinkedIn inbox is a dumpster fire.**

Analyze your exported LinkedIn messages to quantify the audacity of strangers asking for your time, financial advisors who think you can't manage money, and recruiters who clearly didn't read your profile.

## The Problem

Every week, my LinkedIn inbox fills with:
- "Quick 15-minute calls" that are never 15 minutes
- Financial advisors concerned about my retirement (I'm fine, thanks)
- Franchise consultants who think I want to "be my own boss" (I already am)
- "Personalized" messages that definitely came from a template
- AI-generated outreach that somehow feels less human than actual AI

This tool analyzes it all and gives you:
- **The Audacity Metrics™** - How many hours per week strangers request from you
- **Flattery Index** - Quantifying the empty praise before the ask
- **Template Detection** - Catching lazy personalization attempts
- **AI Slop Detection** - Finding those ChatGPT-crafted masterpieces
- **Network Health Score** - Is your inbox a dumpster fire? Now you'll know for sure
- **Trend Analysis** - Track how your inbox chaos changes over time

## Installation

```bash
git clone https://github.com/yourusername/linkedin-message-analyzer.git
cd linkedin-message-analyzer
pip install -r requirements.txt
```

## Getting Your LinkedIn Messages

1. Go to LinkedIn → Settings → Data Privacy → Get a copy of your data
2. Select "Messages"
3. Wait for LinkedIn to email you (usually ~24 hours)
4. Extract `messages.csv` from the download

## Quick Start (For Those Who Fear the Command Line)

**Windows:** Double-click `run.bat`

**macOS/Linux:**
```bash
chmod +x run.sh
./run.sh
```

The startup scripts provide a friendly menu to:
- Run quick analysis
- Launch the C64 web dashboard
- Export HTML reports
- Run LLM-powered analysis

You can also drag-and-drop your `messages.csv` onto `run.bat` (Windows).

## Usage

### Basic Analysis

```bash
# Basic analysis
python linkedin_message_analyzer.py messages.csv

# With your name (to filter out your own messages)
python linkedin_message_analyzer.py messages.csv --my-name "Your Name"

# Generate stats for a snarky LinkedIn post
python linkedin_message_analyzer.py messages.csv --post-stats

# Export results
python linkedin_message_analyzer.py messages.csv --export-json results.json
python linkedin_message_analyzer.py messages.csv --export-csv threads.csv
python linkedin_message_analyzer.py messages.csv --export-html report.html

# Export only high-score unanswered recruiter threads
python linkedin_message_analyzer.py messages.csv --export-csv triage.csv --export-unanswered-only --export-label recruiter --export-min-triage-score 25
```

### Advanced Analysis

```bash
# Trend analysis - see how your inbox changes over time
python linkedin_message_analyzer.py messages.csv --trend

# Network health score - get a grade for your inbox quality
python linkedin_message_analyzer.py messages.csv --health-score

# Reverse mode - analyze YOUR outreach effectiveness
python linkedin_message_analyzer.py messages.csv --reverse --my-name "Your Name"

# Compare two exports - see what changed
python linkedin_message_analyzer.py current.csv --compare previous.csv
```

### LLM-Powered Analysis

For deeper analysis with AI, choose from 6 providers:

```bash
# OpenAI (requires OPENAI_API_KEY, recommended package: openai>=1.60.0)
python linkedin_message_analyzer.py messages.csv --llm openai

# Anthropic Claude (requires ANTHROPIC_API_KEY, recommended package: anthropic>=0.76.0)
python linkedin_message_analyzer.py messages.csv --llm anthropic

# Ollama - FREE local analysis! No API key needed
python linkedin_message_analyzer.py messages.csv --llm ollama
python linkedin_message_analyzer.py messages.csv --llm ollama --ollama-url http://localhost:11434

# Google Gemini (requires GOOGLE_API_KEY, recommended package: google-genai>=1.0.0)
python linkedin_message_analyzer.py messages.csv --llm gemini

# Groq - blazing fast (requires GROQ_API_KEY, recommended package: groq>=1.0.0)
python linkedin_message_analyzer.py messages.csv --llm groq

# Mistral (requires MISTRAL_API_KEY, recommended package: mistralai>=1.5.0)
python linkedin_message_analyzer.py messages.csv --llm mistral

# List all providers and setup instructions
python linkedin_message_analyzer.py --list-llm-providers
```

Current defaults and recommended models:

- OpenAI: default `gpt-4.1-mini`, also good: `gpt-4o-mini`
- Anthropic: default `claude-3-5-haiku-latest`, also good: `claude-3-7-sonnet-latest`
- Gemini: default `gemini-2.5-flash`, also good: `gemini-2.0-flash`
- Groq: default `llama-3.1-8b-instant`, also good: `llama-3.3-70b-versatile`
- Mistral: default `mistral-small-latest`, also good: `mistral-medium-latest`
- Ollama: default `llama3.2`, also good locally: `qwen2.5:7b`

LLM analysis adds:
- Intent classification (sales pitch, recruiting, genuine, etc.)
- Authenticity scoring (1-10)
- Manipulation tactic detection
- Personalized recommendations (ignore/respond/priority)

You can now set LLM defaults in `config.json` and override them with CLI flags. Precedence is: CLI flags > `--config` values > provider defaults.

### Advanced LLM Features

Take your analysis even further with AI-powered features:

```bash
# Summarize conversation threads (who wants what, snark level 1-10)
python linkedin_message_analyzer.py messages.csv --llm openai --summarize

# Generate smart reply suggestions
python linkedin_message_analyzer.py messages.csv --llm openai --smart-replies
python linkedin_message_analyzer.py messages.csv --llm openai --smart-replies --reply-tone deadpan

# Cluster similar messages to find mass outreach campaigns
python linkedin_message_analyzer.py messages.csv --llm openai --cluster

# Find messages that are clearly from templates
python linkedin_message_analyzer.py messages.csv --llm openai --find-templates
```

Available reply tones: `polite`, `firm`, `playful`, `deadpan`, `corporate_speak`

### Web Dashboard (C64 Edition!)

Launch a retro Commodore 64-styled web dashboard:

```bash
# Install the optional dashboard dependency once
pip install flask

# Start the dashboard
python linkedin_message_analyzer.py messages.csv --web

# Custom port
python linkedin_message_analyzer.py messages.csv --web --web-port 3000
```

Then open `http://localhost:6502` in your browser for a nostalgia trip through your inbox metrics.

The dashboard now includes a thread triage queue, sender drill-downs, and filter controls for labels, recommendations, unanswered-only views, and minimum triage scores.
It also lets you export the current filtered view to CSV or JSON and copy a selected thread summary directly from the detail pane.
If LLM analysis is enabled, the dashboard also exposes thread-level LLM recommendation and intent filters plus an LLM-aware sort mode.

Current dashboard filter query params are:

- `label`
- `recommendation`
- `min_score`
- `sender`
- `unanswered_only`
- `llm_recommendation`
- `llm_intent`
- `sort_by` with `triage`, `llm_recommendation`, or `last_message`

### Fun Extras

```bash
# Generate a LinkedIn Bingo card
python linkedin_message_analyzer.py messages.csv --bingo card.html

# Get suggested decline responses
python linkedin_message_analyzer.py messages.csv --suggest-responses --response-tone sarcastic
```

## What It Detects

### Time Vampires
- "Quick call" / "Coffee chat" / "Pick your brain"
- Calendar link drops
- "15 minutes of your time" (multiply by 4 for actual duration)

### Financial Advisors
- Wealth managers who found you on LinkedIn (red flag)
- Anyone mentioning your "financial goals"
- The entire Northwestern Mutual sales force

### Franchise Consultants
- "Be your own boss" pitches
- "Corporate layoff" fear-mongering
- Semi-absentee ownership dreams

### AI-Generated Messages
- "I hope this message finds you well"
- Suspiciously perfect grammar with zero personality
- Generic compliments that apply to literally anyone
- The word "synergy" used unironically

### Fake Personalization
- "Loved your recent post" (which one?)
- "Your profile stood out" (sure it did)
- "People like you" (what people? be specific)

### And More...
- Recruiters with vague "opportunities"
- Expert network consultations
- Crypto/NFT hustlers
- MLM schemes

## Sample Output

```
════════════════════════════════════════════════════════════
LINKEDIN INBOX ANALYSIS: THE AUDACITY REPORT
════════════════════════════════════════════════════════════

MESSAGE BREAKDOWN:
   - Total messages analyzed: 2,847
   - Time requests: 156
   - Financial advisors: 43
   - AI-generated slop: 89
   - Fake personalization: 201

TIME REQUESTED FROM STRANGERS:
   - 47.5 hours total in recent weeks
   - 4.2 hours/week average
   - That's 10.5% of a 40-hour work week
   - If I said yes to everyone: 218 hours/year

NETWORK HEALTH SCORE: 62/100 (Grade: D)
   Spam-Free Score: 45/100
   Engagement Quality: 71/100
   Connection Value: 68/100

RECOMMENDATIONS:
   - Over 50% of messages appear automated. Consider adjusting
     your LinkedIn visibility settings.
```

## Configuration

Copy `config_example.json` to `config.json` and customize:

```json
{
  "user_profile": {
    "name": "Your Name",
      "industries": ["tech"],
      "ignore_senders": ["Your Colleague"]
   },
   "llm": {
      "provider": "ollama",
      "model": "qwen2.5:7b",
      "max_messages": 25,
      "filter": "time_requests",
      "provider_options": {
         "base_url": "http://localhost:11434"
      }
  }
}
```

### LLM Output Surfaces

When LLM analysis runs, the tool now surfaces that metadata consistently across outputs:

- JSON export includes a top-level `llm` block with provider, model, message filter, selected count, recommendation totals, and intent totals.
- JSON thread items include `llm_recommendation`, `llm_intent`, and `llm_analysis_count` when a thread has LLM coverage.
- CSV export includes `llm_recommendation`, `llm_intent`, and `llm_analysis_count` columns.
- The web dashboard shows both run-level LLM settings and per-thread LLM signals.

### Live Smoke Tests

The repo includes an opt-in live smoke test for real providers in [tests/test_llm_live_smoke.py](tests/test_llm_live_smoke.py).

Enable it locally with environment variables:

```bash
set RUN_LLM_SMOKE_TESTS=1
set LLM_SMOKE_PROVIDERS=openai,groq
set OPENAI_API_KEY=...
set GROQ_API_KEY=...
python -m unittest tests.test_llm_live_smoke
```

Optional variables:

- `LLM_SMOKE_MODEL_OPENAI`, `LLM_SMOKE_MODEL_ANTHROPIC`, etc. for provider-specific model overrides
- `OLLAMA_SMOKE_TEST=1` to opt into Ollama smoke tests
- `OLLAMA_BASE_URL=http://localhost:11434` for custom Ollama endpoints

A manual GitHub Actions workflow is also included at [.github/workflows/llm-live-smoke.yml](.github/workflows/llm-live-smoke.yml) for credentialed smoke-test runs.

`--config` now supports:

- `user_profile`: the same shape accepted by `UserProfile.from_dict()`
- `llm.provider`: one of `openai`, `anthropic`, `ollama`, `gemini`, `groq`, `mistral`
- `llm.model`: explicit model override
- `llm.max_messages`: default max messages for LLM analysis
- `llm.filter`: `time_requests`, `suspicious`, or `all`
- `llm.provider_options.base_url`: provider-specific settings such as Ollama's base URL

## Project Structure

```
linkedin-message-analyzer/
├── linkedin_message_analyzer.py   # Main entry point
├── run.bat                        # Windows startup script (menu)
├── run.sh                         # Linux/macOS startup script (menu)
├── lib/
│   ├── analyzer.py                # Core analysis engine
│   ├── llm/                       # LLM provider system
│   │   ├── base.py               # Provider plugin architecture
│   │   ├── analyzer.py           # LLM-powered analysis
│   │   └── providers/            # OpenAI, Anthropic, Ollama, etc.
│   ├── llm_advanced/              # Advanced LLM features
│   │   ├── summarizer.py         # Conversation summarization
│   │   ├── smart_reply.py        # Smart reply generation
│   │   └── clustering.py         # Message clustering
│   ├── patterns/                  # Detection patterns
│   │   ├── outreach.py           # FA, recruiters, etc.
│   │   ├── quality.py            # Flattery, AI detection
│   │   └── time_requests.py      # Time vampire detection
│   ├── reporters/                 # Output formatters
│   ├── web/                       # Web dashboard (C64 style!)
│   │   └── app.py                # Flask app
│   ├── trend.py                   # Trend analysis
│   ├── health.py                  # Network health score
│   ├── reverse.py                 # Outreach effectiveness
│   └── comparison.py              # Period comparison
├── docs/                          # Documentation
│   ├── api/                      # API reference
│   └── architecture.md           # System design
├── samples/                       # Sample CSV files
├── config_example.json
├── CONTRIBUTING.md               # How to contribute
├── CHANGELOG.md                  # Version history
└── requirements.txt
```

## CLI Reference

| Flag | Description |
|------|-------------|
| `--my-name NAME` | Your name (filters your messages) |
| `--industries NAMES` | Industry presets (tech, finance, etc.) |
| `--export-json FILE` | Export to JSON |
| `--export-html FILE` | Export HTML report |
| `--post-stats` | Generate shareable stats |
| `--llm PROVIDER` | Enable LLM analysis (openai, anthropic, ollama, gemini, groq, mistral) |
| `--llm-model MODEL` | Override default model for provider |
| `--llm-max N` | Max messages for LLM analysis (default: 50) |
| `--trend` | Show trend analysis |
| `--trend-period` | weekly or monthly aggregation |
| `--health-score` | Calculate network health |
| `--reverse` | Analyze your outreach |
| `--compare FILE` | Compare with another CSV |
| `--summarize` | LLM-powered conversation summaries |
| `--smart-replies` | Generate smart reply suggestions |
| `--reply-tone TONE` | polite, firm, playful, deadpan, corporate_speak |
| `--cluster` | Cluster similar messages |
| `--find-templates` | Detect mass outreach templates |
| `--web` | Start C64-styled web dashboard |
| `--web-port PORT` | Dashboard port (default: 6502) |
| `--bingo FILE` | Generate bingo card |
| `--suggest-responses` | Show decline templates |
| `--anonymize MODE` | Privacy mode (initials, hash, sequential) |
| `-v, --verbose` | Debug logging |

## Documentation

- [API Reference](docs/api/README.md) - Use programmatically
- [Pattern Guide](docs/api/patterns.md) - Add custom patterns
- [Architecture](docs/architecture.md) - System design
- [Contributing](CONTRIBUTING.md) - How to contribute

## Contributing

Found a new type of LinkedIn annoyance? PRs welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Adding custom patterns
- Creating new reporters
- Development setup

Bonus points for:
- New AI detection patterns
- Industry-specific spam patterns
- Creative snark in the output

## License

MIT - Do whatever you want with it. If it helps you reclaim your inbox, I'm happy.

## Disclaimer

This tool is for entertainment and productivity purposes. No LinkedIn connections were harmed in its making, though several were silently judged.

---

*Built with mass passive aggression after receiving my 47th "quick call" request of the month.*
