# Changelog

All notable changes to the LinkedIn Message Analyzer will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [1.1.0] - 2026-01-26

### Added
- LLM provider plugin system with support for multiple providers
- Ollama support for local, free LLM analysis
- Google Gemini provider support (using new google-genai SDK)
- Groq provider support (fast inference)
- Mistral provider support
- Trend analysis feature (`--trend`, `--trend-period`)
- Network health score (`--health-score`)
- Reverse mode for outreach effectiveness analysis (`--reverse`)
- Comparison mode for comparing time periods/files (`--compare`)
- Advanced LLM features:
  - Conversation summarization (`--summarize`) with snark level scoring
  - Smart reply generation (`--smart-replies`) with 5 tone options
  - Message clustering (`--cluster`) to find patterns
  - Template detection (`--find-templates`) for mass outreach campaigns
- Web dashboard with Commodore 64 aesthetic (`--web`, `--web-port`) - for those who fear the command line
- Startup scripts for Windows (`run.bat`) and Linux/macOS (`run.sh`) - for those who REALLY fear the command line
- Comprehensive documentation in `docs/`
- CONTRIBUTING.md guide
- This CHANGELOG

### Changed
- Refactored `lib/llm.py` into modular `lib/llm/` package

## [1.0.0] - Initial Release

### Added
- Core message analysis engine
- Time request detection with "Audacity Metrics"
- Financial advisor outreach detection
- Franchise consultant detection
- Recruiter pattern detection
- Expert network pattern detection
- AI-generated message detection (ChatGPT patterns)
- Fake personalization detection
- Flattery scoring system
- Template indicator detection
- Weekly summary generation
- Hall of Shame for repeat offenders
- Console output reporter
- JSON export functionality
- Interactive HTML reports with SVG charts
- Bingo card generator with multiple themes
- Name anonymization for privacy
- Response generator with multiple tones
- LLM-powered analysis (OpenAI, Anthropic)
- User profile system with industry presets
- Configuration file support
- Sample CSV generator for testing

### Pattern Categories
- Time requests: "quick call", "coffee chat", "pick your brain", etc.
- Financial advisors: titles, companies, retirement language
- Franchise consultants: "be your own boss", fear-mongering
- Recruiters: vague opportunities, "perfect fit" language
- Expert networks: GLG, AlphaSights, paid consultations
- AI-generated: ChatGPT tells, buzzwords, generic openers
- Flattery: scored patterns for empty praise
- Templates: `{{first_name}}`, "hope this finds you"

### CLI Options
- `--my-name`: Filter out your own messages
- `--industries`: Set industry context
- `--export-json`: Export to JSON
- `--export-html`: Generate HTML report
- `--bingo`: Generate bingo card
- `--anonymize`: Privacy mode
- `--post-stats`: Shareable statistics
- `--suggest-responses`: Decline templates
- `--llm`: Enable LLM analysis
- `--verbose`: Detailed logging
