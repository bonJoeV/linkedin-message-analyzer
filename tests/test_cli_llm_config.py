"""Regression tests for CLI/config precedence in LLM setup."""

import csv
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

import lib.cli as cli


FIELDNAMES = [
    'CONVERSATION ID',
    'CONVERSATION TITLE',
    'FROM',
    'TO',
    'DATE',
    'SUBJECT',
    'CONTENT',
    'FOLDER',
]


class FakeLLMAnalyzer:
    """Stub LLM analyzer used to capture CLI wiring."""

    last_init: dict | None = None

    def __init__(self, provider: str, api_key: str | None = None, model: str | None = None, **kwargs) -> None:
        type(self).last_init = {
            'provider': provider,
            'api_key': api_key,
            'model': model,
            'provider_kwargs': kwargs,
        }

    @staticmethod
    def list_providers() -> list[str]:
        return ['ollama', 'openai']

    @staticmethod
    def get_provider_info() -> dict[str, dict]:
        return {
            'ollama': {
                'provider_type': 'local / self-hosted',
                'env_var': '',
                'requires_api_key': False,
                'setup_url': 'https://ollama.com/download',
                'default_model': 'llama3.2',
                'recommended_models': ['llama3.2'],
                'description': 'Local models',
                'config_fields': [{'name': 'base_url', 'description': 'Ollama server URL'}],
                'notes': [],
                'install': 'pip install ollama>=0.6.0',
            },
            'openai': {
                'provider_type': 'hosted api',
                'env_var': 'OPENAI_API_KEY',
                'requires_api_key': True,
                'setup_url': 'https://platform.openai.com/api-keys',
                'default_model': 'gpt-4.1-mini',
                'recommended_models': ['gpt-4.1-mini'],
                'description': 'Hosted GPT models',
                'config_fields': [],
                'notes': [],
                'install': 'pip install openai>=1.60.0',
            },
        }

    @property
    def _provider(self):
        return object()


class FakeAnalyzer:
    """Stub core analyzer used to capture CLI orchestration."""

    last_instance = None

    def __init__(self, messages_csv: str, user_profile=None, llm_analyzer=None) -> None:
        self.messages_csv = messages_csv
        self.user_profile = user_profile
        self.llm_analyzer = llm_analyzer
        self.llm_analyses = []
        self.run_llm_calls: list[dict[str, object]] = []
        type(self).last_instance = self

    def load_messages(self) -> None:
        return None

    def run_all_analyses(self, my_name: str | None = None) -> None:
        self.my_name = my_name

    def run_llm_analysis(self, max_messages: int, message_filter: str) -> None:
        self.run_llm_calls.append(
            {
                'max_messages': max_messages,
                'message_filter': message_filter,
            }
        )

    def print_report(self, weeks_back: int = 12) -> None:
        self.weeks_back = weeks_back


class CLILLMConfigTests(unittest.TestCase):
    """Validate CLI precedence when config supplies LLM defaults."""

    def create_csv(self, temp_path: Path) -> Path:
        """Create a minimal input CSV fixture."""
        csv_path = temp_path / 'messages.csv'
        with csv_path.open('w', newline='', encoding='utf-8') as handle:
            writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
            writer.writeheader()
            writer.writerow(
                {
                    'CONVERSATION ID': 'conv-1',
                    'CONVERSATION TITLE': 'Config test',
                    'FROM': 'Alex Sender',
                    'TO': 'Jane Doe',
                    'DATE': '2026-04-01 09:00:00',
                    'SUBJECT': 'Hello',
                    'CONTENT': 'Would you have 15 minutes for a quick intro call?',
                    'FOLDER': 'INBOX',
                }
            )
        return csv_path

    def test_cli_uses_config_defaults_and_allows_flag_overrides(self) -> None:
        """Config should provide LLM defaults, with CLI flags overriding specific values."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            csv_path = self.create_csv(temp_path)
            config_path = temp_path / 'config.json'
            config_path.write_text(
                json.dumps(
                    {
                        'user_profile': {
                            'name': 'Config Name',
                            'industries': ['tech'],
                            'roles': ['Engineering Leader'],
                        },
                        'llm': {
                            'provider': 'ollama',
                            'model': 'qwen2.5:7b',
                            'max_messages': 7,
                            'filter': 'all',
                            'provider_options': {
                                'base_url': 'http://ollama-config:11434',
                            },
                        },
                    }
                ),
                encoding='utf-8',
            )

            FakeLLMAnalyzer.last_init = None
            FakeAnalyzer.last_instance = None

            with patch('lib.cli.LLMAnalyzer', FakeLLMAnalyzer), patch(
                'lib.cli.LinkedInMessageAnalyzer', FakeAnalyzer
            ), patch('lib.cli.setup_logging'):
                with patch(
                    'sys.argv',
                    [
                        'linkedin_message_analyzer.py',
                        str(csv_path),
                        '--config',
                        str(config_path),
                        '--llm-model',
                        'llama3.2',
                        '--my-name',
                        'CLI Name',
                    ],
                ):
                    exit_code = cli.main()

        self.assertEqual(exit_code, 0)
        self.assertIsNotNone(FakeLLMAnalyzer.last_init)
        self.assertEqual(FakeLLMAnalyzer.last_init['provider'], 'ollama')
        self.assertEqual(FakeLLMAnalyzer.last_init['model'], 'llama3.2')
        self.assertEqual(
            FakeLLMAnalyzer.last_init['provider_kwargs']['base_url'],
            'http://ollama-config:11434',
        )

        self.assertIsNotNone(FakeAnalyzer.last_instance)
        self.assertEqual(FakeAnalyzer.last_instance.user_profile.name, 'CLI Name')
        self.assertEqual(FakeAnalyzer.last_instance.user_profile.roles, ['Engineering Leader'])
        self.assertEqual(
            FakeAnalyzer.last_instance.run_llm_calls,
            [{'max_messages': 7, 'message_filter': 'all'}],
        )

    def test_cli_flag_provider_overrides_config_provider(self) -> None:
        """An explicit --llm flag should override the provider from config."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            csv_path = self.create_csv(temp_path)
            config_path = temp_path / 'config.json'
            config_path.write_text(
                json.dumps(
                    {
                        'llm': {
                            'provider': 'ollama',
                            'model': 'qwen2.5:7b',
                            'max_messages': 4,
                        },
                    }
                ),
                encoding='utf-8',
            )

            FakeLLMAnalyzer.last_init = None
            FakeAnalyzer.last_instance = None

            with patch('lib.cli.LLMAnalyzer', FakeLLMAnalyzer), patch(
                'lib.cli.LinkedInMessageAnalyzer', FakeAnalyzer
            ), patch('lib.cli.setup_logging'), patch.dict(
                'os.environ', {'OPENAI_API_KEY': 'fake-openai-key'}, clear=False
            ):
                with patch(
                    'sys.argv',
                    [
                        'linkedin_message_analyzer.py',
                        str(csv_path),
                        '--config',
                        str(config_path),
                        '--llm',
                        'openai',
                    ],
                ):
                    exit_code = cli.main()

        self.assertEqual(exit_code, 0)
        self.assertIsNotNone(FakeLLMAnalyzer.last_init)
        self.assertEqual(FakeLLMAnalyzer.last_init['provider'], 'openai')
        self.assertEqual(FakeLLMAnalyzer.last_init['api_key'], 'fake-openai-key')
        self.assertEqual(FakeLLMAnalyzer.last_init['model'], 'qwen2.5:7b')
        self.assertEqual(
            FakeAnalyzer.last_instance.run_llm_calls,
            [{'max_messages': 4, 'message_filter': 'time_requests'}],
        )

    def test_cli_uses_config_only_provider_without_llm_flag(self) -> None:
        """Config-provided llm settings should activate LLM analysis even without --llm."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            csv_path = self.create_csv(temp_path)
            config_path = temp_path / 'config.json'
            config_path.write_text(
                json.dumps(
                    {
                        'llm': {
                            'provider': 'ollama',
                            'model': 'qwen2.5:7b',
                            'max_messages': 3,
                            'filter': 'suspicious',
                            'ollama_url': 'http://ollama-from-config:11434',
                        },
                    }
                ),
                encoding='utf-8',
            )

            FakeLLMAnalyzer.last_init = None
            FakeAnalyzer.last_instance = None

            with patch('lib.cli.LLMAnalyzer', FakeLLMAnalyzer), patch(
                'lib.cli.LinkedInMessageAnalyzer', FakeAnalyzer
            ), patch('lib.cli.setup_logging'):
                with patch(
                    'sys.argv',
                    [
                        'linkedin_message_analyzer.py',
                        str(csv_path),
                        '--config',
                        str(config_path),
                    ],
                ):
                    exit_code = cli.main()

        self.assertEqual(exit_code, 0)
        self.assertEqual(FakeLLMAnalyzer.last_init['provider'], 'ollama')
        self.assertEqual(FakeLLMAnalyzer.last_init['model'], 'qwen2.5:7b')
        self.assertEqual(
            FakeLLMAnalyzer.last_init['provider_kwargs']['base_url'],
            'http://ollama-from-config:11434',
        )
        self.assertEqual(
            FakeAnalyzer.last_instance.run_llm_calls,
            [{'max_messages': 3, 'message_filter': 'suspicious'}],
        )

    def test_list_llm_providers_shows_provider_types_and_models(self) -> None:
        """Provider listing should include the richer provider metadata table."""
        output = io.StringIO()

        with patch('lib.cli.LLMAnalyzer', FakeLLMAnalyzer), redirect_stdout(output):
            with patch('sys.argv', ['linkedin_message_analyzer.py', '--list-llm-providers']):
                exit_code = cli.main()

        rendered = output.getvalue()
        self.assertEqual(exit_code, 0)
        self.assertIn('AVAILABLE LLM PROVIDERS', rendered)
        self.assertIn('Provider', rendered)
        self.assertIn('Type', rendered)
        self.assertIn('hosted api', rendered)
        self.assertIn('local / self-hosted', rendered)
        self.assertIn('gpt-4.1-mini', rendered)
        self.assertIn('llama3.2', rendered)


if __name__ == '__main__':
    unittest.main()