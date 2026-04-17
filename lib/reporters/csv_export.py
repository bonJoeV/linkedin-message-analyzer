"""CSV export reporter for thread-aware LinkedIn message analysis."""

import csv
import io
import logging
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lib.analyzer import LinkedInMessageAnalyzer

logger = logging.getLogger(__name__)


class CSVReporter:
    """Exports conversation thread rollups to CSV format."""

    def __init__(
        self,
        output_path: str | Path | None = None,
        labels: list[str] | None = None,
        min_triage_score: int | None = None,
        unanswered_only: bool = False,
        recommendation: str | None = None,
        sender: str | None = None,
        llm_recommendation: str | None = None,
        llm_intent: str | None = None,
        sort_by: str = 'triage',
    ) -> None:
        """Initialize the CSV reporter.

        Args:
            output_path: Path to write CSV output. If None, returns string.
        """
        self.output_path = Path(output_path) if output_path else None
        self.labels = labels or []
        self.min_triage_score = min_triage_score
        self.unanswered_only = unanswered_only
        self.recommendation = recommendation
        self.sender = sender
        self.llm_recommendation = llm_recommendation
        self.llm_intent = llm_intent
        self.sort_by = sort_by

    def generate(self, analyzer: 'LinkedInMessageAnalyzer') -> str:
        """Generate CSV output from analysis results.

        Args:
            analyzer: The analyzer with completed analysis

        Returns:
            CSV string of thread-level rollups
        """
        csv_str = self._build_output(analyzer)

        if self.output_path:
            self._write_file(csv_str)

        return csv_str

    def _build_output(self, analyzer: 'LinkedInMessageAnalyzer') -> str:
        """Build the CSV output string."""
        threads = analyzer.get_conversation_threads()
        sender_lookup = {
            summary['sender']: summary
            for summary in analyzer.get_sender_summaries()
            if summary.get('sender')
        }
        filtered_triage = analyzer.get_filtered_thread_triage_queue(
            labels=self.labels,
            min_triage_score=self.min_triage_score,
            unanswered_only=self.unanswered_only,
            recommendation=self.recommendation,
            sender=self.sender,
            llm_recommendation=self.llm_recommendation,
            llm_intent=self.llm_intent,
            sort_by=self.sort_by,
        )
        has_filters = bool(
            self.labels
            or self.unanswered_only
            or self.recommendation
            or self.sender
            or self.min_triage_score is not None
            or self.llm_recommendation
            or self.llm_intent
            or self.sort_by != 'triage'
        )
        filtered_ids = {item['conversation_id'] for item in filtered_triage}
        triage_lookup = {
            item['conversation_id']: item
            for item in (
                filtered_triage
                if has_filters else analyzer.get_thread_triage_queue(include_responded=True)
            )
        }
        unanswered_thread_ids = {
            thread['conversation_id']
            for thread in analyzer.get_unanswered_threads()
        }

        fieldnames = [
            'conversation_id',
            'conversation_title',
            'primary_sender',
            'participants',
            'message_count',
            'incoming_count',
            'outgoing_count',
            'has_response_from_me',
            'is_persistent_unanswered',
            'triage_score',
            'thread_labels',
            'recommendation',
            'recommendation_reason',
            'llm_recommendation',
            'llm_intent',
            'llm_analysis_count',
            'first_message_at',
            'last_message_at',
            'latest_message_preview',
            'sender_conversation_count',
            'sender_message_count',
            'sender_unanswered_conversation_count',
            'sender_unanswered_message_count',
            'sender_has_received_response',
        ]

        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=fieldnames)
        writer.writeheader()

        ordered_threads = list(threads.values())
        if has_filters:
            ordered_threads = [
                threads[conversation_id]
                for conversation_id in [item['conversation_id'] for item in filtered_triage]
                if conversation_id in threads
            ]

        for thread in ordered_threads:
            sender = thread.get('primary_sender', '')
            sender_summary = sender_lookup.get(sender, {})
            triage_item = triage_lookup.get(thread.get('conversation_id', ''), {})
            latest_message_preview = ''
            if thread.get('messages'):
                latest_message_preview = thread['messages'][-1].get('content', '')[:200]

            writer.writerow({
                'conversation_id': thread.get('conversation_id', ''),
                'conversation_title': thread.get('conversation_title', ''),
                'primary_sender': sender,
                'participants': ' | '.join(thread.get('participants', [])),
                'message_count': thread.get('message_count', 0),
                'incoming_count': thread.get('incoming_count', 0),
                'outgoing_count': thread.get('outgoing_count', 0),
                'has_response_from_me': thread.get('has_response_from_me', False),
                'is_persistent_unanswered': thread.get('conversation_id', '') in unanswered_thread_ids,
                'triage_score': triage_item.get('triage_score', 0),
                'thread_labels': ' | '.join(triage_item.get('labels', [])),
                'recommendation': triage_item.get('recommendation', ''),
                'recommendation_reason': triage_item.get('recommendation_reason', ''),
                'llm_recommendation': triage_item.get('llm_recommendation', ''),
                'llm_intent': triage_item.get('llm_intent', ''),
                'llm_analysis_count': triage_item.get('llm_analysis_count', 0),
                'first_message_at': thread['first_message_at'].isoformat() if thread.get('first_message_at') else '',
                'last_message_at': thread['last_message_at'].isoformat() if thread.get('last_message_at') else '',
                'latest_message_preview': latest_message_preview,
                'sender_conversation_count': sender_summary.get('conversation_count', 0),
                'sender_message_count': sender_summary.get('message_count', 0),
                'sender_unanswered_conversation_count': sender_summary.get('unanswered_conversation_count', 0),
                'sender_unanswered_message_count': sender_summary.get('unanswered_message_count', 0),
                'sender_has_received_response': sender_summary.get('has_received_response', False),
            })

        return buffer.getvalue()

    def _write_file(self, csv_str: str) -> None:
        """Write CSV to file."""
        if self.output_path:
            with open(self.output_path, 'w', encoding='utf-8', newline='') as handle:
                handle.write(csv_str)
            logger.info(f"Results exported to {self.output_path}")