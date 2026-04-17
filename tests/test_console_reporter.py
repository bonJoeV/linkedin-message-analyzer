"""Regression tests for console reporter thread-aware sections."""

import csv
import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from lib import LinkedInMessageAnalyzer, UserProfile
from lib.reporters.console import ConsoleReporter
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


class ConsoleReporterTests(unittest.TestCase):
    """Validate console output for thread-aware reporting sections."""

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

    def load_analyzer(self) -> LinkedInMessageAnalyzer:
        """Create and analyze a deterministic fixture inbox."""
        analyzer = LinkedInMessageAnalyzer(
            self.create_csv(build_sample_rows()),
            user_profile=UserProfile(name='Jane Doe'),
        )
        analyzer.load_messages()
        analyzer.run_all_analyses(my_name='Jane Doe')
        return analyzer

    def test_console_report_includes_sender_and_thread_sections(self) -> None:
        """Console report should show sender triage and unanswered thread sections."""
        analyzer = self.load_analyzer()
        reporter = ConsoleReporter(weeks_back=104)
        output = io.StringIO()

        with redirect_stdout(output):
            reporter.print_report(analyzer)

        report_text = output.getvalue()
        self.assertIn('SENDER TRIAGE', report_text)
        self.assertIn('THREAD TRIAGE QUEUE', report_text)
        self.assertIn('UNANSWERED THREADS', report_text)
        self.assertIn('Alice Sender', report_text)
        self.assertIn('Alice new thread', report_text)


if __name__ == '__main__':
    unittest.main()