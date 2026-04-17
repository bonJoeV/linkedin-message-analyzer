"""Regression tests for config-driven LLM settings."""

import json
import tempfile
import unittest
from pathlib import Path

from lib.config import ConfigurationError, load_config
from lib.patterns import FLATTERY_PATTERNS, get_pattern_registry


class LLMConfigTests(unittest.TestCase):
    """Validate config normalization for weighted patterns, user profile, and llm settings."""

    def write_config(self, payload: dict) -> Path:
        """Write a temporary config file for a test."""
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        config_path = Path(temp_dir.name) / 'config.json'
        config_path.write_text(json.dumps(payload), encoding='utf-8')
        return config_path

    def setUp(self) -> None:
        registry = get_pattern_registry()
        original_flattery = list(registry.get_weighted('flattery'))

        def restore_registry() -> None:
            registry.register_weighted('flattery', original_flattery or FLATTERY_PATTERNS)

        self.addCleanup(restore_registry)

    def test_load_config_accepts_weighted_patterns_and_normalizes_llm_settings(self) -> None:
        """Config loading should accept weighted flattery patterns and normalize llm options."""
        config_path = self.write_config(
            {
                'user_profile': {
                    'name': 'Jane Doe',
                    'industries': ['tech'],
                    'ignore_senders': ['Friendly Coworker'],
                },
                'flattery_patterns': [
                    ['\\bthought leader\\b', 2],
                    '\\bamazing background\\b',
                ],
                'llm': {
                    'provider': 'ollama',
                    'model': 'qwen2.5:7b',
                    'max_messages': 12,
                    'filter': 'all',
                    'ollama_url': 'http://ollama.local:11434',
                },
            }
        )

        config = load_config(str(config_path))

        self.assertEqual(config['user_profile']['name'], 'Jane Doe')
        self.assertEqual(config['llm']['provider'], 'ollama')
        self.assertEqual(config['llm']['model'], 'qwen2.5:7b')
        self.assertEqual(config['llm']['max_messages'], 12)
        self.assertEqual(config['llm']['filter'], 'all')
        self.assertEqual(
            config['llm']['provider_options']['base_url'],
            'http://ollama.local:11434',
        )

    def test_load_config_rejects_unknown_llm_provider(self) -> None:
        """LLM config should fail fast on unknown providers."""
        config_path = self.write_config(
            {
                'llm': {
                    'provider': 'not-a-provider',
                },
            }
        )

        with self.assertRaises(ConfigurationError):
            load_config(str(config_path))


if __name__ == '__main__':
    unittest.main()