"""JSON export reporter for LinkedIn Message Analyzer."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from lib.analyzer import LinkedInMessageAnalyzer

logger = logging.getLogger(__name__)


class JSONReporter:
    """Exports analysis results to JSON format."""

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
        """Initialize the JSON reporter.

        Args:
            output_path: Path to write JSON output. If None, returns string.
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
        """Generate JSON output from analysis results.

        Args:
            analyzer: The analyzer with completed analysis

        Returns:
            JSON string of the results
        """
        output = self._build_output(analyzer)
        json_str = json.dumps(output, indent=2, default=str)

        if self.output_path:
            self._write_file(json_str)

        return json_str

    def _build_output(self, analyzer: 'LinkedInMessageAnalyzer') -> dict[str, Any]:
        """Build the output dictionary.

        Args:
            analyzer: The analyzer with completed analysis

        Returns:
            Dictionary ready for JSON serialization
        """
        summary = analyzer.get_weekly_summary()
        metrics = analyzer.calculate_audacity_metrics()
        time_patterns = analyzer.get_time_pattern_summary()
        flattery = analyzer.get_flattery_summary()
        conversation_threads = analyzer.get_conversation_threads()
        labels_by_thread = analyzer.get_thread_labels()
        thread_llm_signals = analyzer.get_thread_llm_signals()
        triage_queue = analyzer.get_filtered_thread_triage_queue(
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
        if has_filters:
            filtered_ids = {item['conversation_id'] for item in triage_queue}
            filtered_threads = {
                conversation_id: thread
                for conversation_id, thread in conversation_threads.items()
                if conversation_id in filtered_ids
            }
            thread_summaries = [
                summary
                for summary in analyzer.get_sender_summaries()
                if any(conversation_id in filtered_ids for conversation_id in summary.get('conversation_ids', []))
            ]
            unanswered_threads = [
                thread
                for thread in analyzer.get_unanswered_threads()
                if thread['conversation_id'] in filtered_ids
            ]
            conversation_threads = filtered_threads
        else:
            thread_summaries = analyzer.get_sender_summaries()
            unanswered_threads = analyzer.get_unanswered_threads()

        return {
            'generated_at': datetime.now().isoformat(),
            'total_messages': len(analyzer.messages),
            'llm': analyzer.get_llm_run_info(),
            'export_filters': {
                'labels': self.labels,
                'min_triage_score': self.min_triage_score,
                'unanswered_only': self.unanswered_only,
                'recommendation': self.recommendation,
                'sender': self.sender,
                'llm_recommendation': self.llm_recommendation,
                'llm_intent': self.llm_intent,
                'sort_by': self.sort_by,
            },
            'conversation_summary': {
                'total_threads': len(conversation_threads),
                'responded_threads': sum(
                    1 for thread in conversation_threads.values() if thread.get('has_response_from_me')
                ),
                'unanswered_threads': len(unanswered_threads),
            },
            'date_range': {
                'start': analyzer.date_range[0].isoformat() if analyzer.date_range else None,
                'end': analyzer.date_range[1].isoformat() if analyzer.date_range else None,
            },
            'summary': {
                'time_requests_by_week': summary['time_requests_by_week'],
                'fa_outreach_by_week': summary['fa_outreach_by_week'],
            },
            'metrics': metrics,
            'time_patterns': {
                'peak_hour': time_patterns['peak_hour'],
                'peak_day': time_patterns['peak_day'],
                'off_hours_pct': time_patterns['off_hours_pct'],
                'weekend_pct': time_patterns['weekend_pct'],
            },
            'flattery': {
                'avg_score': flattery['avg_score'],
                'max_score': flattery['max_score'],
                'count': flattery.get('messages_with_flattery', 0),
            },
            'counts': {
                'time_requests': len(analyzer.time_requests),
                'financial_advisors': len(analyzer.financial_advisor_messages),
                'franchise_consultants': len(analyzer.franchise_consultant_messages),
                'expert_networks': len(analyzer.expert_network_messages),
                'angel_investors': len(analyzer.angel_investor_messages),
                'recruiters': len(analyzer.recruiter_messages),
                'role_confusion': len(analyzer.role_confusion_messages),
                'fake_personalization': len(analyzer.fake_personalization_messages),
                'repeat_offenders': len(analyzer.repeat_offenders),
            },
            'time_requests': [
                {
                    'date': r['date'].isoformat() if r['date'] else None,
                    'from': r['from'],
                    'estimated_minutes': r['estimated_minutes'],
                    'content_preview': r['content'][:200] if r['content'] else '',
                }
                for r in analyzer.time_requests
            ],
            'financial_advisor_messages': [
                {
                    'date': m['date'].isoformat() if m['date'] else None,
                    'from': m['from'],
                    'content_preview': m['content'][:200] if m['content'] else '',
                }
                for m in analyzer.financial_advisor_messages
            ],
            'sender_summaries': [
                {
                    'sender': summary['sender'],
                    'conversation_count': summary['conversation_count'],
                    'message_count': summary['message_count'],
                    'responded_conversation_count': summary['responded_conversation_count'],
                    'unanswered_conversation_count': summary['unanswered_conversation_count'],
                    'unanswered_message_count': summary['unanswered_message_count'],
                    'has_received_response': summary['has_received_response'],
                    'first_contact': summary['first_contact'].isoformat() if summary.get('first_contact') else None,
                    'last_contact': summary['last_contact'].isoformat() if summary.get('last_contact') else None,
                    'conversation_ids': summary['conversation_ids'],
                }
                for summary in thread_summaries[:10]
            ],
            'thread_triage_queue': [
                {
                    'conversation_id': item['conversation_id'],
                    'conversation_title': item['conversation_title'],
                    'primary_sender': item['primary_sender'],
                    'incoming_count': item['incoming_count'],
                    'message_count': item['message_count'],
                    'triage_score': item['triage_score'],
                    'labels': item['labels'],
                    'recommendation': item['recommendation'],
                    'recommendation_reason': item['recommendation_reason'],
                    'llm_recommendation': item.get('llm_recommendation', ''),
                    'llm_intent': item.get('llm_intent', ''),
                    'llm_analysis_count': item.get('llm_analysis_count', 0),
                    'last_message_at': item['last_message_at'].isoformat() if item.get('last_message_at') else None,
                    'latest_message_preview': item['latest_message_preview'],
                }
                for item in triage_queue[:10]
            ],
            'unanswered_threads': [
                {
                    'conversation_id': thread['conversation_id'],
                    'conversation_title': thread['conversation_title'],
                    'primary_sender': thread['primary_sender'],
                    'participants': thread['participants'],
                    'incoming_count': thread['incoming_count'],
                    'message_count': thread['message_count'],
                    'labels': labels_by_thread.get(thread['conversation_id'], []),
                    'recommendation': next(
                        (
                            item['recommendation']
                            for item in triage_queue
                            if item['conversation_id'] == thread['conversation_id']
                        ),
                        'safe_to_ignore',
                    ),
                    'triage_score': next(
                        (
                            item['triage_score']
                            for item in triage_queue
                            if item['conversation_id'] == thread['conversation_id']
                        ),
                        0,
                    ),
                    'llm_recommendation': thread_llm_signals.get(thread['conversation_id'], {}).get('primary_recommendation', ''),
                    'llm_intent': thread_llm_signals.get(thread['conversation_id'], {}).get('primary_intent', ''),
                    'llm_analysis_count': thread_llm_signals.get(thread['conversation_id'], {}).get('analysis_count', 0),
                    'first_message_at': thread['first_message_at'].isoformat() if thread.get('first_message_at') else None,
                    'last_message_at': thread['last_message_at'].isoformat() if thread.get('last_message_at') else None,
                    'latest_message_preview': thread['messages'][-1].get('content', '')[:200] if thread.get('messages') else '',
                }
                for thread in unanswered_threads[:10]
            ],
        }

    def _write_file(self, json_str: str) -> None:
        """Write JSON to file.

        Args:
            json_str: JSON string to write
        """
        if self.output_path:
            with open(self.output_path, 'w', encoding='utf-8') as f:
                f.write(json_str)
            logger.info(f"Results exported to {self.output_path}")
