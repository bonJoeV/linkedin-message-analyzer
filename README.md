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
python linkedin_message_analyzer.py messages.csv --export-html report.html
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
# OpenAI (requires OPENAI_API_KEY)
python linkedin_message_analyzer.py messages.csv --llm openai

# Anthropic Claude (requires ANTHROPIC_API_KEY)
python linkedin_message_analyzer.py messages.csv --llm anthropic

# Ollama - FREE local analysis! No API key needed
python linkedin_message_analyzer.py messages.csv --llm ollama

# Google Gemini (requires GOOGLE_API_KEY)
python linkedin_message_analyzer.py messages.csv --llm gemini

# Groq - blazing fast (requires GROQ_API_KEY)
python linkedin_message_analyzer.py messages.csv --llm groq

# Mistral (requires MISTRAL_API_KEY)
python linkedin_message_analyzer.py messages.csv --llm mistral

# List all providers and setup instructions
python linkedin_message_analyzer.py --list-llm-providers
```

LLM analysis adds:
- Intent classification (sales pitch, recruiting, genuine, etc.)
- Authenticity scoring (1-10)
- Manipulation tactic detection
- Personalized recommendations (ignore/respond/priority)

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
# Start the dashboard
python linkedin_message_analyzer.py messages.csv --web

# Custom port
python linkedin_message_analyzer.py messages.csv --web --web-port 3000
```

Then open `http://localhost:6502` in your browser for a nostalgia trip through your inbox metrics.

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
  }
}
```

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
