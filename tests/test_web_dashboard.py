"""Regression tests for the thread-aware web dashboard."""

import csv
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from lib import LinkedInMessageAnalyzer, UserProfile
from lib.web.app import Flask, create_app
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


@unittest.skipIf(Flask is None, 'Flask is not installed in this environment')
class WebDashboardTests(unittest.TestCase):
    """Validate the new dashboard and filtered dashboard API."""

    def create_csv(self, rows: list[dict[str, str]]) -> Path:
        """Create a temporary CSV file for a test run."""
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        csv_path = Path(temp_dir.name) / 'messages.csv'
        with csv_path.open('w', newline='', encoding='utf-8') as handle:
            writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
            writer.writeheader()
            writer.writerows(rows)
        return csv_path

    def load_app(self):
        """Build a Flask app from the deterministic analyzer fixture."""
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
            'selected_message_count': 2,
        }
        analyzer.llm_analyses = [
            {
                'conversation_id': 'conv-alice-1',
                'intent': 'networking',
                'recommendation': 'consider',
                'authenticity_score': 8,
            },
            {
                'conversation_id': 'conv-dana-1',
                'intent': 'recruiting',
                'recommendation': 'priority',
                'authenticity_score': 6,
            },
        ]
        app = create_app(analyzer)
        app.testing = True
        return app

    def test_dashboard_page_renders_triage_sections(self) -> None:
        """The main dashboard page should render the new triage UI sections."""
        app = self.load_app()

        with app.test_client() as client:
            response = client.get('/')

        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn('THREAD TRIAGE QUEUE', body)
        self.assertIn('SENDER DRILL-DOWN', body)
        self.assertIn('FILTER INBOX', body)
        self.assertIn('EXPORT CSV', body)
        self.assertIn('COPY SUMMARY', body)
        self.assertIn('LLM ANALYSIS', body)
        self.assertIn('qwen2.5:7b', body)
        self.assertIn('LLM RECOMMENDATION', body)
        self.assertIn('LLM INTENT', body)

    def test_dashboard_api_applies_filters(self) -> None:
        """Dashboard API should respect the same triage filters as exports."""
        app = self.load_app()

        with app.test_client() as client:
            response = client.get(
                '/api/dashboard-data?unanswered_only=true&label=time_request&min_score=30&recommendation=safe_to_ignore'
            )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(len(payload['triage_items']), 2)
        self.assertEqual(
            {item['conversation_id'] for item in payload['triage_items']},
            {'conv-alice-1', 'conv-alice-2'},
        )
        self.assertTrue(all(item['recommendation'] == 'safe_to_ignore' for item in payload['triage_items']))
        self.assertEqual(len(payload['thread_details']), 2)
        self.assertTrue(payload['llm']['enabled'])
        self.assertEqual(payload['llm']['provider'], 'ollama')

    def test_dashboard_api_applies_llm_filters(self) -> None:
        """Dashboard API should filter by aggregated LLM thread signals."""
        app = self.load_app()

        with app.test_client() as client:
            response = client.get(
                '/api/dashboard-data?llm_recommendation=consider&llm_intent=networking&sort_by=llm_recommendation'
            )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual([item['conversation_id'] for item in payload['triage_items']], ['conv-alice-1'])
        self.assertEqual(payload['thread_details'][0]['llm']['recommendation'], 'consider')

    def test_dashboard_export_endpoint_returns_filtered_csv(self) -> None:
        """Dashboard export endpoint should emit a filtered CSV file."""
        app = self.load_app()

        with app.test_client() as client:
            response = client.get('/api/export?format=csv&sender=Alice%20Sender&unanswered_only=true')

        self.assertEqual(response.status_code, 200)
        self.assertIn('text/csv', response.headers['Content-Type'])
        self.assertIn('attachment; filename=thread-triage-export.csv', response.headers['Content-Disposition'])
        body = response.get_data(as_text=True)
        self.assertIn('conv-alice-1', body)
        self.assertIn('conv-alice-2', body)
        self.assertNotIn('conv-dana-1', body)