"""Regression tests for HTML report output."""

import csv
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from lib import LinkedInMessageAnalyzer, UserProfile
from lib.reporters.html import generate_html_report
from tests.test_analyzer_threads import build_sample_rows


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


class HTMLReporterTests(unittest.TestCase):
    """Validate HTML report generation with current analyzer fields."""

    def create_csv(self, rows: list[dict[str, str]]) -> Path:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        csv_path = Path(temp_dir.name) / 'messages.csv'
        with csv_path.open('w', newline='', encoding='utf-8') as handle:
            writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
            writer.writeheader()
            writer.writerows(rows)
        return csv_path

    def test_html_report_includes_llm_run_section(self) -> None:
        analyzer = LinkedInMessageAnalyzer(
            self.create_csv(build_sample_rows()),
            user_profile=UserProfile(name='Jane Doe'),
        )
        analyzer.load_messages()
        analyzer.run_all_analyses(my_name='Jane Doe')
        analyzer.llm_analyzer = SimpleNamespace(
            provider_name='ollama',
            model='qwen2.5:7b',
            stats=SimpleNamespace(successful=1, failed=0),
        )
        analyzer.llm_run_config = {
            'message_filter': 'time_requests',
            'max_messages': 5,
            'selected_message_count': 1,
        }
        analyzer.llm_analyses = [
            {
                'intent': 'networking',
                'recommendation': 'consider',
                'authenticity_score': 8,
            }
        ]

        html = generate_html_report(analyzer)

        self.assertIn('LLM Analysis Run', html)
        self.assertIn('qwen2.5:7b', html)
        self.assertIn('local / self-hosted', html)
        self.assertIn('Requested max', html)


if __name__ == '__main__':
    unittest.main()