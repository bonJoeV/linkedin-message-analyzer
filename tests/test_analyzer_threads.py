"""Regression tests for analyzer thread and sender aggregation."""

import csv
import tempfile
import unittest
from pathlib import Path

from lib import LinkedInMessageAnalyzer, UserProfile


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


def build_sample_rows() -> list[dict[str, str]]:
    """Build a deterministic mini inbox for thread-oriented tests."""
    return [
        {
            'CONVERSATION ID': 'conv-alice-1',
            'CONVERSATION TITLE': 'Alice intro',
            'FROM': 'Alice Sender',
            'TO': 'Jane Doe',
            'DATE': '2026-04-01 09:00:00',
            'SUBJECT': 'Quick intro',
            'CONTENT': 'Would you have 15 minutes for a quick intro call?',
            'FOLDER': 'INBOX',
        },
        {
            'CONVERSATION ID': 'conv-alice-1',
            'CONVERSATION TITLE': 'Alice intro',
            'FROM': 'Alice Sender',
            'TO': 'Jane Doe',
            'DATE': '2026-04-03 09:30:00',
            'SUBJECT': 'Following up',
            'CONTENT': 'Just bumping this in case it slipped through.',
            'FOLDER': 'INBOX',
        },
        {
            'CONVERSATION ID': 'conv-alice-2',
            'CONVERSATION TITLE': 'Alice new thread',
            'FROM': 'Alice Sender',
            'TO': 'Jane Doe',
            'DATE': '2026-04-05 10:00:00',
            'SUBJECT': 'Another idea',
            'CONTENT': 'Wanted to follow up with one more idea for a quick chat.',
            'FOLDER': 'INBOX',
        },
        {
            'CONVERSATION ID': 'conv-alice-2',
            'CONVERSATION TITLE': 'Alice new thread',
            'FROM': 'Alice Sender',
            'TO': 'Jane Doe',
            'DATE': '2026-04-07 10:15:00',
            'SUBJECT': 'Second bump',
            'CONTENT': 'Checking one last time before I close the loop.',
            'FOLDER': 'INBOX',
        },
        {
            'CONVERSATION ID': 'conv-bob-1',
            'CONVERSATION TITLE': 'Bob outreach',
            'FROM': 'Bob Recruiter',
            'TO': 'Jane Doe',
            'DATE': '2026-04-04 08:00:00',
            'SUBJECT': 'Role',
            'CONTENT': 'Open to a quick conversation about a role?',
            'FOLDER': 'INBOX',
        },
        {
            'CONVERSATION ID': 'conv-bob-1',
            'CONVERSATION TITLE': 'Bob outreach',
            'FROM': 'Jane Doe',
            'TO': 'Bob Recruiter',
            'DATE': '2026-04-04 12:00:00',
            'SUBJECT': 'Re: Role',
            'CONTENT': 'Thanks, but I am not interested right now.',
            'FOLDER': 'SENT',
        },
        {
            'CONVERSATION ID': 'conv-dana-1',
            'CONVERSATION TITLE': 'Dana thread',
            'FROM': 'Dana Founder',
            'TO': 'Jane Doe',
            'DATE': '2026-04-08 14:00:00',
            'SUBJECT': 'Connection',
            'CONTENT': 'Would love to connect on founder challenges.',
            'FOLDER': 'INBOX',
        },
        {
            'CONVERSATION ID': 'conv-dana-1',
            'CONVERSATION TITLE': 'Dana thread',
            'FROM': 'Jane Doe',
            'TO': 'Dana Founder',
            'DATE': '2026-04-08 17:00:00',
            'SUBJECT': 'Re: Connection',
            'CONTENT': 'Happy to connect. Send over a few details.',
            'FOLDER': 'SENT',
        },
        {
            'CONVERSATION ID': 'conv-dana-1',
            'CONVERSATION TITLE': 'Dana thread',
            'FROM': 'Dana Founder',
            'TO': 'Jane Doe',
            'DATE': '2026-04-09 09:00:00',
            'SUBJECT': 'More details',
            'CONTENT': 'Sharing the details you requested.',
            'FOLDER': 'INBOX',
        },
    ]


class AnalyzerThreadTests(unittest.TestCase):
    """Validate the new thread and sender-level analyzer helpers."""

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
        """Build and load an analyzer with a deterministic fixture."""
        analyzer = LinkedInMessageAnalyzer(
            self.create_csv(build_sample_rows()),
            user_profile=UserProfile(name='Jane Doe'),
        )
        analyzer.load_messages()
        return analyzer

    def test_get_conversation_threads_returns_sorted_thread_metadata(self) -> None:
        """Conversation threads should provide counts, participants, and response state."""
        analyzer = self.load_analyzer()

        threads = analyzer.get_conversation_threads()
        dana_thread = threads['conv-dana-1']

        self.assertEqual(list(threads.keys())[0], 'conv-dana-1')
        self.assertEqual(dana_thread['primary_sender'], 'Dana Founder')
        self.assertEqual(dana_thread['message_count'], 3)
        self.assertEqual(dana_thread['incoming_count'], 2)
        self.assertEqual(dana_thread['outgoing_count'], 1)
        self.assertTrue(dana_thread['has_response_from_me'])
        self.assertEqual(dana_thread['participants'], ['Dana Founder', 'Jane Doe'])
        self.assertEqual(
            [message['subject'] for message in dana_thread['messages']],
            ['Connection', 'Re: Connection', 'More details'],
        )

    def test_get_sender_summaries_rolls_up_unanswered_activity(self) -> None:
        """Sender summaries should rank by unanswered incoming message volume."""
        analyzer = self.load_analyzer()

        summaries = analyzer.get_sender_summaries()
        alice_summary = next(summary for summary in summaries if summary['sender'] == 'Alice Sender')
        bob_summary = next(summary for summary in summaries if summary['sender'] == 'Bob Recruiter')

        self.assertEqual(summaries[0]['sender'], 'Alice Sender')
        self.assertEqual(alice_summary['conversation_count'], 2)
        self.assertEqual(alice_summary['message_count'], 4)
        self.assertEqual(alice_summary['unanswered_conversation_count'], 2)
        self.assertEqual(alice_summary['unanswered_message_count'], 4)
        self.assertFalse(alice_summary['has_received_response'])
        self.assertTrue(bob_summary['has_received_response'])
        self.assertEqual(bob_summary['responded_conversation_count'], 1)

    def test_get_unanswered_threads_returns_persistent_unanswered_threads(self) -> None:
        """Unanswered threads should prioritize persistent threads without a reply."""
        analyzer = self.load_analyzer()

        unanswered_threads = analyzer.get_unanswered_threads()

        self.assertEqual(len(unanswered_threads), 2)
        self.assertEqual(unanswered_threads[0]['conversation_id'], 'conv-alice-2')
        self.assertEqual(unanswered_threads[1]['conversation_id'], 'conv-alice-1')
        self.assertTrue(all(not thread['has_response_from_me'] for thread in unanswered_threads))
        self.assertTrue(all(thread['incoming_count'] >= 2 for thread in unanswered_threads))

    def test_analyze_repeat_offenders_uses_thread_level_rollups(self) -> None:
        """Repeat offender detection should align with the sender summary model."""
        analyzer = self.load_analyzer()

        analyzer.analyze_repeat_offenders()

        self.assertIn('Alice Sender', analyzer.repeat_offenders)
        self.assertNotIn('Bob Recruiter', analyzer.repeat_offenders)
        self.assertNotIn('Dana Founder', analyzer.repeat_offenders)
        self.assertEqual(analyzer.repeat_offenders['Alice Sender']['count'], 4)
        self.assertEqual(
            analyzer.repeat_offenders['Alice Sender']['first_contact'].strftime('%Y-%m-%d %H:%M:%S'),
            '2026-04-01 09:00:00',
        )
        self.assertEqual(
            analyzer.repeat_offenders['Alice Sender']['last_contact'].strftime('%Y-%m-%d %H:%M:%S'),
            '2026-04-07 10:15:00',
        )

    def test_get_thread_triage_queue_scores_and_labels_threads(self) -> None:
        """Triage queue should score unanswered threads and attach category labels."""
        analyzer = self.load_analyzer()
        analyzer.run_all_analyses(my_name='Jane Doe')

        triage_queue = analyzer.get_thread_triage_queue()

        top_ids = {triage_queue[0]['conversation_id'], triage_queue[1]['conversation_id']}
        self.assertEqual(top_ids, {'conv-alice-1', 'conv-alice-2'})
        self.assertTrue(all('time_request' in item['labels'] for item in triage_queue[:2]))
        self.assertGreaterEqual(triage_queue[0]['triage_score'], triage_queue[1]['triage_score'])
        self.assertEqual(triage_queue[0]['recommendation'], 'safe_to_ignore')
        self.assertTrue(triage_queue[0]['recommendation_reason'])

    def test_get_filtered_thread_triage_queue_applies_labels_score_and_recommendation(self) -> None:
        """Filtered triage queue should narrow items by export/dashboard filters."""
        analyzer = self.load_analyzer()
        analyzer.run_all_analyses(my_name='Jane Doe')

        filtered = analyzer.get_filtered_thread_triage_queue(
            labels=['time_request'],
            min_triage_score=30,
            unanswered_only=True,
            recommendation='safe_to_ignore',
        )

        self.assertEqual(len(filtered), 2)
        self.assertEqual(
            {item['conversation_id'] for item in filtered},
            {'conv-alice-1', 'conv-alice-2'},
        )

    def test_classifier_marks_active_conversation_as_needing_reply(self) -> None:
        """An existing back-and-forth should stay in the reply bucket."""
        analyzer = self.load_analyzer()
        threads = analyzer.get_conversation_threads()

        recommendation, reason = analyzer.classify_thread_recommendation(threads['conv-dana-1'], [])

        self.assertEqual(recommendation, 'needs_reply')
        self.assertIn('active conversation', reason.lower())

    def test_classifier_marks_direct_question_as_needing_reply(self) -> None:
        """A direct question without spam indicators should be treated as reply-worthy."""
        analyzer = self.load_analyzer()

        recommendation, reason = analyzer.classify_thread_recommendation(
            {
                'incoming_count': 1,
                'messages': [{'content': 'Can you share a few details about timing?'}],
            },
            [],
        )

        self.assertEqual(recommendation, 'needs_reply')
        self.assertIn('direct question', reason.lower())


if __name__ == '__main__':
    unittest.main()