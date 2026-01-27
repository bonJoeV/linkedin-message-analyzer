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

    def __init__(self, output_path: str | Path | None = None) -> None:
        """Initialize the JSON reporter.

        Args:
            output_path: Path to write JSON output. If None, returns string.
        """
        self.output_path = Path(output_path) if output_path else None

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

        return {
            'generated_at': datetime.now().isoformat(),
            'total_messages': len(analyzer.messages),
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
