"""Regression tests for CLI export flags."""

import csv
import subprocess
import tempfile
import unittest
from pathlib import Path

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


SAMPLE_ROWS = [
    {
        'CONVERSATION ID': 'cli-conv-1',
        'CONVERSATION TITLE': 'CLI export test',
        'FROM': 'Casey Sender',
        'TO': 'Jane Doe',
        'DATE': '2026-04-01 09:00:00',
        'SUBJECT': 'Quick intro',
        'CONTENT': 'Would you have 15 minutes for a quick intro call?',
        'FOLDER': 'INBOX',
    },
    {
        'CONVERSATION ID': 'cli-conv-1',
        'CONVERSATION TITLE': 'CLI export test',
        'FROM': 'Casey Sender',
        'TO': 'Jane Doe',
        'DATE': '2026-04-03 09:30:00',
        'SUBJECT': 'Following up',
        'CONTENT': 'Just bumping this in case it slipped through.',
        'FOLDER': 'INBOX',
    },
]


class CLIExportTests(unittest.TestCase):
    """Validate CLI export options for CSV output."""

    def test_export_csv_flag_writes_thread_rollup_file(self) -> None:
        """CLI should create a CSV export file with thread rollup headers."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            input_path = temp_path / 'messages.csv'
            output_path = temp_path / 'threads.csv'

            with input_path.open('w', newline='', encoding='utf-8') as handle:
                writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
                writer.writeheader()
                writer.writerows(SAMPLE_ROWS)

            result = subprocess.run(
                [
                    'c:/GithubRepo/linkedin-message-analyzer/.venv/Scripts/python.exe',
                    'linkedin_message_analyzer.py',
                    str(input_path),
                    '--my-name',
                    'Jane Doe',
                    '--export-csv',
                    str(output_path),
                ],
                cwd='c:/GithubRepo/linkedin-message-analyzer',
                capture_output=True,
                text=True,
                timeout=60,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertTrue(output_path.exists())

            with output_path.open('r', encoding='utf-8', newline='') as handle:
                rows = list(csv.DictReader(handle))

            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]['conversation_id'], 'cli-conv-1')
            self.assertEqual(rows[0]['is_persistent_unanswered'], 'True')
            self.assertIn('CSV export saved to:', result.stdout)

    def test_export_csv_filters_rows_via_cli_flags(self) -> None:
        """CLI should pass export filter flags through to the CSV reporter."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            input_path = temp_path / 'messages.csv'
            output_path = temp_path / 'filtered-threads.csv'

            with input_path.open('w', newline='', encoding='utf-8') as handle:
                writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
                writer.writeheader()
                writer.writerows(build_sample_rows())

            result = subprocess.run(
                [
                    'c:/GithubRepo/linkedin-message-analyzer/.venv/Scripts/python.exe',
                    'linkedin_message_analyzer.py',
                    str(input_path),
                    '--my-name',
                    'Jane Doe',
                    '--export-csv',
                    str(output_path),
                    '--export-unanswered-only',
                    '--export-label',
                    'time_request',
                    '--export-min-triage-score',
                    '30',
                    '--export-recommendation',
                    'safe_to_ignore',
                ],
                cwd='c:/GithubRepo/linkedin-message-analyzer',
                capture_output=True,
                text=True,
                timeout=60,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            with output_path.open('r', encoding='utf-8', newline='') as handle:
                rows = list(csv.DictReader(handle))

            self.assertEqual(len(rows), 2)
            self.assertEqual(
                {row['conversation_id'] for row in rows},
                {'conv-alice-1', 'conv-alice-2'},
            )


if __name__ == '__main__':
    unittest.main()