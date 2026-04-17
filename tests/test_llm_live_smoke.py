"""Optional live smoke tests for real LLM providers.

These are opt-in and skipped by default. Enable them with:

    RUN_LLM_SMOKE_TESTS=1

Optionally narrow providers with:

    LLM_SMOKE_PROVIDERS=openai,anthropic,groq

For Ollama, opt in explicitly with:

    OLLAMA_SMOKE_TEST=1

You can also override models per provider with env vars like:

    LLM_SMOKE_MODEL_OPENAI=gpt-4.1-mini
"""

import os
import unittest

from lib.llm import LLMAnalyzer


SMOKE_MESSAGE = (
    'Hi Jane, I came across your background in product leadership and would love '
    'to grab 15 minutes next week to learn about your approach to hiring.'
)


@unittest.skipUnless(
    os.environ.get('RUN_LLM_SMOKE_TESTS') == '1',
    'Set RUN_LLM_SMOKE_TESTS=1 to enable live provider smoke tests.',
)
class LLMLiveSmokeTests(unittest.TestCase):
    """Run one real analysis call against explicitly enabled providers."""

    def test_selected_providers_can_analyze_one_message(self) -> None:
        provider_info = LLMAnalyzer.get_provider_info()
        selected_raw = os.environ.get('LLM_SMOKE_PROVIDERS', '').strip()

        if selected_raw:
            selected = [name.strip().lower() for name in selected_raw.split(',') if name.strip()]
        else:
            selected = [
                name
                for name, info in provider_info.items()
                if (
                    info.get('requires_api_key')
                    and info.get('env_var')
                    and os.environ.get(str(info.get('env_var')))
                ) or (
                    name == 'ollama'
                    and os.environ.get('OLLAMA_SMOKE_TEST') == '1'
                )
            ]

        if not selected:
            self.skipTest('No smoke-test providers were selected or configured.')

        for provider in selected:
            info = provider_info.get(provider)
            if not info:
                self.fail(f'Unknown smoke-test provider: {provider}')

            api_key = None
            env_var = info.get('env_var')
            if info.get('requires_api_key'):
                api_key = os.environ.get(str(env_var))
                if not api_key:
                    self.fail(f'Missing required env var for smoke test: {env_var}')

            provider_kwargs = {}
            if provider == 'ollama' and os.environ.get('OLLAMA_BASE_URL'):
                provider_kwargs['base_url'] = os.environ['OLLAMA_BASE_URL']

            model_override = os.environ.get(f'LLM_SMOKE_MODEL_{provider.upper()}')

            with self.subTest(provider=provider):
                analyzer = LLMAnalyzer(
                    provider=provider,
                    api_key=api_key,
                    model=model_override,
                    **provider_kwargs,
                )
                result = analyzer.analyze_message(
                    SMOKE_MESSAGE,
                    sender_name='Smoke Test Sender',
                    sender_context='Outbound networking request',
                )

                self.assertIsInstance(result, dict)
                self.assertIn('intent', result)
                self.assertIn('recommendation', result)


if __name__ == '__main__':
    unittest.main()