"""Regression tests for JSON export thread-aware fields."""

import json
import csv
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from lib import LinkedInMessageAnalyzer, UserProfile
from lib.reporters.json_export import JSONReporter
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


class JSONExportTests(unittest.TestCase):
    """Validate that JSON export includes the new thread-aware surfaces."""

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
        """Attach a deterministic LLM run summary to the analyzer."""
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

    def test_json_export_includes_thread_and_sender_rollups(self) -> None:
        """JSON output should include conversation summary, sender summaries, and unanswered threads."""
        analyzer = self.load_analyzer_with_analyses()

        payload = json.loads(JSONReporter().generate(analyzer))

        self.assertEqual(payload['conversation_summary']['total_threads'], 4)
        self.assertEqual(payload['conversation_summary']['responded_threads'], 2)
        self.assertEqual(payload['conversation_summary']['unanswered_threads'], 2)
        self.assertEqual(payload['sender_summaries'][0]['sender'], 'Alice Sender')
        self.assertEqual(payload['sender_summaries'][0]['unanswered_message_count'], 4)
        self.assertIn(
            payload['thread_triage_queue'][0]['conversation_id'],
            {'conv-alice-1', 'conv-alice-2'},
        )
        self.assertIn('time_request', payload['thread_triage_queue'][0]['labels'])
        self.assertIn(payload['thread_triage_queue'][0]['recommendation'], {'needs_reply', 'safe_to_ignore'})
        self.assertEqual(payload['unanswered_threads'][0]['conversation_id'], 'conv-alice-2')
        self.assertEqual(payload['unanswered_threads'][1]['conversation_id'], 'conv-alice-1')
        triage_scores = {
            item['conversation_id']: item['triage_score']
            for item in payload['thread_triage_queue']
        }
        self.assertEqual(payload['unanswered_threads'][1]['triage_score'], triage_scores['conv-alice-1'])
        self.assertEqual(
            payload['unanswered_threads'][0]['latest_message_preview'],
            'Checking one last time before I close the loop.',
        )

    def test_json_export_filters_threads_by_label_score_and_recommendation(self) -> None:
        """JSON export filters should restrict thread-oriented sections to matching items."""
        analyzer = self.load_analyzer_with_analyses()

        payload = json.loads(
            JSONReporter(
                labels=['time_request'],
                min_triage_score=30,
                unanswered_only=True,
                recommendation='safe_to_ignore',
            ).generate(analyzer)
        )

        self.assertEqual(payload['conversation_summary']['total_threads'], 2)
        self.assertEqual(
            {item['conversation_id'] for item in payload['thread_triage_queue']},
            {'conv-alice-1', 'conv-alice-2'},
        )
        self.assertTrue(all(item['recommendation'] == 'safe_to_ignore' for item in payload['thread_triage_queue']))
        self.assertEqual(len(payload['unanswered_threads']), 2)

    def test_json_export_includes_llm_run_metadata_when_available(self) -> None:
        """JSON export should expose structured LLM run info for downstream tooling."""
        analyzer = self.load_analyzer_with_analyses()
        self.attach_llm_results(analyzer)

        payload = json.loads(JSONReporter().generate(analyzer))

        self.assertTrue(payload['llm']['enabled'])
        self.assertEqual(payload['llm']['provider'], 'ollama')
        self.assertEqual(payload['llm']['provider_type'], 'local / self-hosted')
        self.assertEqual(payload['llm']['model'], 'qwen2.5:7b')
        self.assertEqual(payload['llm']['message_filter'], 'time_requests')
        self.assertEqual(payload['llm']['analyses_completed'], 2)
        self.assertEqual(payload['llm']['recommendations']['consider'], 1)
        by_thread = {
            item['conversation_id']: item
            for item in payload['thread_triage_queue']
        }
        self.assertEqual(by_thread['conv-alice-1']['llm_recommendation'], 'consider')
        self.assertEqual(by_thread['conv-dana-1']['llm_intent'], 'recruiting')

    def test_json_export_filters_threads_by_llm_recommendation_and_intent(self) -> None:
        """JSON export should support thread filtering on aggregated LLM signals."""
        analyzer = self.load_analyzer_with_analyses()
        self.attach_llm_results(analyzer)

        payload = json.loads(
            JSONReporter(
                llm_recommendation='consider',
                llm_intent='networking',
                sort_by='llm_recommendation',
            ).generate(analyzer)
        )

        self.assertEqual(
            [item['conversation_id'] for item in payload['thread_triage_queue']],
            ['conv-alice-1'],
        )


if __name__ == '__main__':
    unittest.main()