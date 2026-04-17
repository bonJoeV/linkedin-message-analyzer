"""Regression tests for LLM provider metadata surfaced to users."""

import unittest

from lib.llm import LLMAnalyzer


class LLMProviderMetadataTests(unittest.TestCase):
    """Validate centralized provider metadata used by CLI and docs."""

    def test_provider_info_includes_setup_urls_recommended_models_and_notes(self) -> None:
        """Provider info should expose rich metadata from the provider layer."""
        info = LLMAnalyzer.get_provider_info()

        self.assertIn('openai', info)
        self.assertIn('anthropic', info)
        self.assertIn('ollama', info)

        self.assertEqual(info['openai']['default_model'], 'gpt-4.1-mini')
        self.assertEqual(info['openai']['provider_type'], 'hosted api')
        self.assertEqual(info['openai']['setup_url'], 'https://platform.openai.com/api-keys')
        self.assertIn('gpt-4o-mini', info['openai']['recommended_models'])
        self.assertTrue(info['openai']['requires_api_key'])

        self.assertEqual(info['anthropic']['default_model'], 'claude-3-5-haiku-latest')
        self.assertIn('claude-3-7-sonnet-latest', info['anthropic']['recommended_models'])

        self.assertFalse(info['ollama']['requires_api_key'])
        self.assertEqual(info['ollama']['provider_type'], 'local / self-hosted')
        self.assertTrue(any(field['name'] == 'base_url' for field in info['ollama']['config_fields']))
        self.assertIn('qwen2.5:7b', info['ollama']['recommended_models'])

    def test_install_instructions_match_supported_package_floors(self) -> None:
        """Provider install instructions should reflect the supported package floors."""
        info = LLMAnalyzer.get_provider_info()

        self.assertEqual(info['openai']['install'], 'pip install openai>=1.60.0')
        self.assertEqual(info['anthropic']['install'], 'pip install anthropic>=0.76.0')
        self.assertEqual(info['groq']['install'], 'pip install groq>=1.0.0')
        self.assertEqual(info['mistral']['install'], 'pip install mistralai>=1.5.0')
        self.assertIn('pip install ollama>=0.6.0', info['ollama']['install'])


if __name__ == '__main__':
    unittest.main()