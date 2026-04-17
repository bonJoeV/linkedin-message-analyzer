"""Regression tests for CSV export thread-aware rows."""

import csv
import io
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from lib import LinkedInMessageAnalyzer, UserProfile
from lib.reporters.csv_export import CSVReporter
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


class CSVExportTests(unittest.TestCase):
    """Validate CSV export for thread-aware reporting."""

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

    def load_analyzer_with_analyses(self) -> LinkedInMessageAnalyzer:
        """Build a loaded analyzer and run the base analyses used by export."""
        analyzer = LinkedInMessageAnalyzer(
            self.create_csv(build_sample_rows()),
            user_profile=UserProfile(name='Jane Doe'),
        )
        analyzer.load_messages()
        analyzer.run_all_analyses(my_name='Jane Doe')
        return analyzer

    def attach_llm_results(self, analyzer: LinkedInMessageAnalyzer) -> None:
        """Attach deterministic thread-level LLM signals to the analyzer."""
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

    def test_csv_export_includes_thread_and_sender_columns(self) -> None:
        """CSV output should flatten thread and sender rollup data into one row per thread."""
        analyzer = self.load_analyzer_with_analyses()

        csv_text = CSVReporter().generate(analyzer)
        rows = list(csv.DictReader(io.StringIO(csv_text)))

        self.assertEqual(len(rows), 4)
        self.assertEqual(rows[0]['conversation_id'], 'conv-dana-1')
        self.assertIn('sender_unanswered_message_count', rows[0])
        self.assertIn('triage_score', rows[0])
        self.assertIn('thread_labels', rows[0])

        alice_followup = next(row for row in rows if row['conversation_id'] == 'conv-alice-2')
        alice_intro = next(row for row in rows if row['conversation_id'] == 'conv-alice-1')
        self.assertEqual(alice_followup['primary_sender'], 'Alice Sender')
        self.assertEqual(alice_followup['is_persistent_unanswered'], 'True')
        self.assertEqual(alice_followup['sender_conversation_count'], '2')
        self.assertEqual(alice_followup['sender_unanswered_message_count'], '4')
        self.assertEqual(alice_intro['thread_labels'], 'time_request')
        self.assertGreaterEqual(int(alice_intro['triage_score']), int(alice_followup['triage_score']))
        self.assertEqual(
            alice_followup['latest_message_preview'],
            'Checking one last time before I close the loop.',
        )

    def test_csv_export_filters_rows_when_requested(self) -> None:
        """CSV export filters should narrow rows to matching thread triage items."""
        analyzer = self.load_analyzer_with_analyses()

        csv_text = CSVReporter(
            labels=['time_request'],
            min_triage_score=30,
            unanswered_only=True,
            recommendation='safe_to_ignore',
        ).generate(analyzer)
        rows = list(csv.DictReader(io.StringIO(csv_text)))

        self.assertEqual(len(rows), 2)
        self.assertEqual(
            {row['conversation_id'] for row in rows},
            {'conv-alice-1', 'conv-alice-2'},
        )
        self.assertTrue(all(row['recommendation'] == 'safe_to_ignore' for row in rows))

    def test_csv_export_includes_llm_columns_and_filters(self) -> None:
        """CSV export should expose thread-level LLM fields and allow filtering on them."""
        analyzer = self.load_analyzer_with_analyses()
        self.attach_llm_results(analyzer)

        csv_text = CSVReporter(
            llm_recommendation='consider',
            llm_intent='networking',
            sort_by='llm_recommendation',
        ).generate(analyzer)
        rows = list(csv.DictReader(io.StringIO(csv_text)))

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['conversation_id'], 'conv-alice-1')
        self.assertEqual(rows[0]['llm_recommendation'], 'consider')
        self.assertEqual(rows[0]['llm_intent'], 'networking')
        self.assertEqual(rows[0]['llm_analysis_count'], '1')


if __name__ == '__main__':
    unittest.main()