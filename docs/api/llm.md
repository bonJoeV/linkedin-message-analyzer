# LLM Integration

The LLM layer is optional and uses a provider registry, so the CLI, config loader, and programmatic API all pull from the same provider metadata.

## Supported Providers

| Provider | API Key Env Var | Default Model | Recommended Package |
|----------|------------------|---------------|---------------------|
| OpenAI | `OPENAI_API_KEY` | `gpt-4.1-mini` | `openai>=1.60.0` |
| Anthropic | `ANTHROPIC_API_KEY` | `claude-3-5-haiku-latest` | `anthropic>=0.76.0` |
| Gemini | `GOOGLE_API_KEY` | `gemini-2.5-flash` | `google-genai>=1.0.0` |
| Groq | `GROQ_API_KEY` | `llama-3.1-8b-instant` | `groq>=1.0.0` |
| Mistral | `MISTRAL_API_KEY` | `mistral-small-latest` | `mistralai>=1.5.0` |
| Ollama | none | `llama3.2` | `ollama>=0.6.0` |

## Programmatic Usage

```python
from lib import LLMAnalyzer

llm = LLMAnalyzer(
    provider='anthropic',
    api_key='your-api-key',
    model='claude-3-5-haiku-latest',
)
```

Ollama accepts provider-specific configuration through keyword arguments:

```python
from lib import LLMAnalyzer

llm = LLMAnalyzer(
    provider='ollama',
    model='qwen2.5:7b',
    base_url='http://localhost:11434',
)
```

## Config File Usage

`--config` now supports an `llm` block in addition to custom patterns.

```json
{
  "llm": {
    "provider": "groq",
    "model": "llama-3.3-70b-versatile",
    "max_messages": 20,
    "filter": "suspicious"
  }
}
```

For Ollama, use `provider_options.base_url` or `ollama_url`:

```json
{
  "llm": {
    "provider": "ollama",
    "model": "qwen2.5:7b",
    "provider_options": {
      "base_url": "http://localhost:11434"
    }
  }
}
```

Precedence is:

1. CLI flags
2. `--config` values
3. provider defaults

## Recommended Models

- OpenAI: `gpt-4.1-mini`, `gpt-4o-mini`
- Anthropic: `claude-3-5-haiku-latest`, `claude-3-7-sonnet-latest`
- Gemini: `gemini-2.5-flash`, `gemini-2.0-flash`
- Groq: `llama-3.1-8b-instant`, `llama-3.3-70b-versatile`
- Mistral: `mistral-small-latest`, `mistral-medium-latest`
- Ollama: `llama3.2`, `qwen2.5:7b`

These are advisory model recommendations surfaced from provider metadata. The tool does not hard-fail if you choose a different valid model string.

## CLI Discovery

Use the CLI to inspect provider metadata directly:

```bash
python linkedin_message_analyzer.py --list-llm-providers
```

That output includes setup URLs, package install guidance, recommended models, and any provider-specific config fields.

## Export and Dashboard Surfaces

When LLM analysis is enabled, the structured output surfaces now include LLM metadata in a consistent way.

### JSON Export

`JSONReporter` includes a top-level `llm` block:

```json
{
  "llm": {
    "enabled": true,
    "provider": "ollama",
    "provider_type": "local / self-hosted",
    "model": "qwen2.5:7b",
    "message_filter": "time_requests",
    "selected_message_count": 20,
    "analyses_completed": 18,
    "recommendations": {
      "consider": 9,
      "ignore": 7,
      "priority": 2
    },
    "intents": {
      "networking": 8,
      "recruiting": 6,
      "sales_pitch": 4
    }
  }
}
```

Thread-oriented JSON sections also include:

- `llm_recommendation`
- `llm_intent`
- `llm_analysis_count`

### CSV Export

`CSVReporter` includes thread-level LLM columns:

- `llm_recommendation`
- `llm_intent`
- `llm_analysis_count`

### Web Dashboard

The dashboard filter bar supports the classic thread filters plus:

- `llm_recommendation`
- `llm_intent`
- `sort_by=triage|llm_recommendation|last_message`

These flow through `/api/dashboard-data` and `/api/export`, so exporting the current dashboard view preserves the same LLM filter state.

## Live Smoke Tests

The repo includes an opt-in live smoke test in `tests/test_llm_live_smoke.py`.

Enable it locally with:

```bash
set RUN_LLM_SMOKE_TESTS=1
set LLM_SMOKE_PROVIDERS=openai,anthropic
set OPENAI_API_KEY=...
set ANTHROPIC_API_KEY=...
python -m unittest tests.test_llm_live_smoke
```

Supported environment variables:

- `RUN_LLM_SMOKE_TESTS=1`
- `LLM_SMOKE_PROVIDERS=openai,anthropic,gemini,groq,mistral,ollama`
- `LLM_SMOKE_MODEL_<PROVIDER>` for per-provider model overrides
- `OLLAMA_SMOKE_TEST=1`
- `OLLAMA_BASE_URL=http://localhost:11434`

## GitHub Actions Workflow

The repository also includes a manual workflow at `.github/workflows/llm-live-smoke.yml`.

Use it when you want to run provider smoke tests in GitHub Actions with repo secrets configured for the selected providers. Hosted providers work on standard runners; Ollama remains best suited for local or self-hosted runs.