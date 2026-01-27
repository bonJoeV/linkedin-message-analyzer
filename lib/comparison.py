"""Comparison mode - compare two analyses or time periods."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from lib.analyzer import LinkedInMessageAnalyzer


@dataclass
class ComparisonResult:
    """Results of comparing two analyses.

    Attributes:
        period_a: Metrics from first period/file
        period_b: Metrics from second period/file
        differences: Percentage changes between periods
        improvements: Metrics that improved
        declines: Metrics that got worse
        highlights: Notable changes to call out
    """

    period_a: dict[str, Any]
    period_b: dict[str, Any]
    differences: dict[str, float]
    improvements: list[str] = field(default_factory=list)
    declines: list[str] = field(default_factory=list)
    highlights: list[str] = field(default_factory=list)


class ComparisonAnalyzer:
    """Compare two message analyses to identify changes.

    Can compare:
    - Two different CSV files (e.g., exports from different times)
    - Two date ranges within the same file
    """

    def __init__(
        self,
        analyzer_a: 'LinkedInMessageAnalyzer',
        analyzer_b: 'LinkedInMessageAnalyzer',
        label_a: str = "Period A",
        label_b: str = "Period B",
    ) -> None:
        """Initialize with two analyzers to compare.

        Args:
            analyzer_a: First analyzer (baseline)
            analyzer_b: Second analyzer (comparison)
            label_a: Label for first period
            label_b: Label for second period
        """
        self.analyzer_a = analyzer_a
        self.analyzer_b = analyzer_b
        self.label_a = label_a
        self.label_b = label_b

    @classmethod
    def from_date_ranges(
        cls,
        analyzer: 'LinkedInMessageAnalyzer',
        range_a: tuple[datetime, datetime],
        range_b: tuple[datetime, datetime],
    ) -> 'ComparisonAnalyzer':
        """Create comparison from date ranges within same dataset.

        This creates filtered views of the same analyzer for different
        time periods.

        Args:
            analyzer: Source analyzer with all messages
            range_a: (start, end) for first period
            range_b: (start, end) for second period

        Returns:
            ComparisonAnalyzer configured for the two periods
        """
        # Create wrapper that filters messages by date range
        # For simplicity, we'll use the same analyzer but filter in compare()
        comparison = cls(analyzer, analyzer)
        comparison._date_range_a = range_a
        comparison._date_range_b = range_b
        comparison._use_date_filter = True
        comparison.label_a = f"{range_a[0].strftime('%Y-%m-%d')} to {range_a[1].strftime('%Y-%m-%d')}"
        comparison.label_b = f"{range_b[0].strftime('%Y-%m-%d')} to {range_b[1].strftime('%Y-%m-%d')}"
        return comparison

    def compare(self) -> ComparisonResult:
        """Perform the comparison analysis.

        Returns:
            ComparisonResult with all comparison data
        """
        # Extract metrics from both periods
        if hasattr(self, '_use_date_filter') and self._use_date_filter:
            metrics_a = self._extract_metrics_for_range(
                self.analyzer_a, self._date_range_a
            )
            metrics_b = self._extract_metrics_for_range(
                self.analyzer_b, self._date_range_b
            )
        else:
            metrics_a = self._extract_metrics(self.analyzer_a)
            metrics_b = self._extract_metrics(self.analyzer_b)

        # Calculate differences
        differences = self._calculate_differences(metrics_a, metrics_b)

        # Categorize changes
        improvements = []
        declines = []

        # For most metrics, lower is better (spam, FAs, etc.)
        lower_is_better = {
            'spam_ratio', 'time_requests', 'financial_advisors',
            'ai_generated', 'template_messages', 'repeat_offenders',
            'fake_personalization', 'mlm_messages', 'crypto_messages'
        }

        # For some metrics, higher is better
        higher_is_better = {
            'response_rate', 'genuine_estimate'
        }

        for metric, change in differences.items():
            if abs(change) < 5:  # Ignore small changes
                continue

            if metric in lower_is_better:
                if change < 0:
                    improvements.append(f"{metric}: {change:+.1f}%")
                else:
                    declines.append(f"{metric}: {change:+.1f}%")
            elif metric in higher_is_better:
                if change > 0:
                    improvements.append(f"{metric}: {change:+.1f}%")
                else:
                    declines.append(f"{metric}: {change:+.1f}%")

        # Generate highlights
        highlights = self._generate_highlights(metrics_a, metrics_b, differences)

        return ComparisonResult(
            period_a=metrics_a,
            period_b=metrics_b,
            differences=differences,
            improvements=improvements,
            declines=declines,
            highlights=highlights,
        )

    def _extract_metrics(self, analyzer: 'LinkedInMessageAnalyzer') -> dict[str, Any]:
        """Extract comparable metrics from an analyzer.

        Args:
            analyzer: Analyzer to extract from

        Returns:
            Dict of metric names to values
        """
        total = len(analyzer.messages)

        metrics = {
            'total_messages': total,
            'time_requests': len(analyzer.time_requests),
            'financial_advisors': len(analyzer.financial_advisor_messages),
            'recruiters': len(analyzer.recruiter_messages),
            'ai_generated': len(analyzer.ai_generated_messages),
            'template_messages': len(analyzer.template_messages),
            'fake_personalization': len(analyzer.fake_personalization_messages),
            'repeat_offenders': len(analyzer.repeat_offenders),
            'mlm_messages': len(analyzer.mlm_messages),
            'crypto_messages': len(analyzer.crypto_hustler_messages),
            'franchise_messages': len(analyzer.franchise_consultant_messages),
            'expert_network': len(analyzer.expert_network_messages),
        }

        # Calculate percentages
        if total > 0:
            metrics['spam_ratio'] = (
                (metrics['ai_generated'] + metrics['template_messages']) / total * 100
            )
            metrics['time_request_pct'] = metrics['time_requests'] / total * 100
            metrics['fa_pct'] = metrics['financial_advisors'] / total * 100
        else:
            metrics['spam_ratio'] = 0
            metrics['time_request_pct'] = 0
            metrics['fa_pct'] = 0

        # Flattery stats
        if analyzer.flattery_scores:
            avg_flattery = sum(
                s.get('score', 0) for s in analyzer.flattery_scores
            ) / len(analyzer.flattery_scores)
            metrics['avg_flattery_score'] = round(avg_flattery, 1)
        else:
            metrics['avg_flattery_score'] = 0

        return metrics

    def _extract_metrics_for_range(
        self,
        analyzer: 'LinkedInMessageAnalyzer',
        date_range: tuple[datetime, datetime],
    ) -> dict[str, Any]:
        """Extract metrics for a specific date range.

        Args:
            analyzer: Source analyzer
            date_range: (start, end) tuple

        Returns:
            Metrics dict for messages in range
        """
        start, end = date_range

        # Filter messages by date
        messages_in_range = [
            msg for msg in analyzer.messages
            if msg.get('date') and start <= msg['date'] <= end
        ]

        # Create message ID set for quick lookup
        msg_ids = {msg.get('conversation_id') for msg in messages_in_range}

        # Count categories
        time_requests = sum(
            1 for msg in analyzer.time_requests
            if msg.get('conversation_id') in msg_ids
        )
        fas = sum(
            1 for msg in analyzer.financial_advisor_messages
            if msg.get('conversation_id') in msg_ids
        )
        recruiters = sum(
            1 for msg in analyzer.recruiter_messages
            if msg.get('conversation_id') in msg_ids
        )
        ai_gen = sum(
            1 for msg in analyzer.ai_generated_messages
            if msg.get('conversation_id') in msg_ids
        )
        templates = sum(
            1 for msg in analyzer.template_messages
            if msg.get('conversation_id') in msg_ids
        )
        fake_personal = sum(
            1 for msg in analyzer.fake_personalization_messages
            if msg.get('conversation_id') in msg_ids
        )

        total = len(messages_in_range)

        metrics = {
            'total_messages': total,
            'time_requests': time_requests,
            'financial_advisors': fas,
            'recruiters': recruiters,
            'ai_generated': ai_gen,
            'template_messages': templates,
            'fake_personalization': fake_personal,
            'spam_ratio': (ai_gen + templates) / total * 100 if total > 0 else 0,
            'time_request_pct': time_requests / total * 100 if total > 0 else 0,
            'fa_pct': fas / total * 100 if total > 0 else 0,
        }

        return metrics

    def _calculate_differences(
        self,
        metrics_a: dict[str, Any],
        metrics_b: dict[str, Any],
    ) -> dict[str, float]:
        """Calculate percentage differences between metrics.

        Args:
            metrics_a: Baseline metrics
            metrics_b: Comparison metrics

        Returns:
            Dict of metric name to percentage change
        """
        differences = {}

        for key in metrics_a:
            val_a = metrics_a.get(key, 0)
            val_b = metrics_b.get(key, 0)

            if isinstance(val_a, (int, float)) and isinstance(val_b, (int, float)):
                if val_a == 0:
                    change = 100.0 if val_b > 0 else 0.0
                else:
                    change = ((val_b - val_a) / val_a) * 100

                differences[key] = round(change, 1)

        return differences

    def _generate_highlights(
        self,
        metrics_a: dict[str, Any],
        metrics_b: dict[str, Any],
        differences: dict[str, float],
    ) -> list[str]:
        """Generate notable change highlights.

        Args:
            metrics_a: Baseline metrics
            metrics_b: Comparison metrics
            differences: Calculated differences

        Returns:
            List of highlight strings
        """
        highlights = []

        # Volume change
        vol_change = differences.get('total_messages', 0)
        if abs(vol_change) > 20:
            direction = "increased" if vol_change > 0 else "decreased"
            highlights.append(
                f"Message volume {direction} by {abs(vol_change):.0f}%"
            )

        # Spam change
        spam_change = differences.get('spam_ratio', 0)
        if spam_change < -15:
            highlights.append(
                f"Spam ratio improved by {abs(spam_change):.0f}% - cleaner inbox!"
            )
        elif spam_change > 15:
            highlights.append(
                f"Spam ratio increased by {spam_change:.0f}% - more junk"
            )

        # FA change
        fa_change = differences.get('financial_advisors', 0)
        if fa_change < -30:
            highlights.append("Financial advisor outreach dropped significantly")
        elif fa_change > 50:
            highlights.append("Financial advisor outreach spiked - check profile visibility")

        # AI-generated change
        ai_change = differences.get('ai_generated', 0)
        if ai_change > 50:
            highlights.append("AI-generated messages increased significantly")
        elif ai_change < -30:
            highlights.append("Fewer AI-generated messages detected")

        return highlights

    def generate_comparison_report(self) -> str:
        """Generate a formatted comparison report.

        Returns:
            Formatted report string
        """
        result = self.compare()

        lines = [
            "=" * 60,
            "PERIOD COMPARISON",
            "=" * 60,
            "",
            f"Period A: {self.label_a}",
            f"Period B: {self.label_b}",
            "",
            f"{'Metric':<25} {'Period A':>10} {'Period B':>10} {'Change':>10}",
            f"{'-'*25} {'-'*10} {'-'*10} {'-'*10}",
        ]

        # Key metrics to display
        display_metrics = [
            ('total_messages', 'Total Messages'),
            ('time_requests', 'Time Requests'),
            ('financial_advisors', 'Financial Advisors'),
            ('recruiters', 'Recruiters'),
            ('ai_generated', 'AI-Generated'),
            ('template_messages', 'Template Messages'),
            ('spam_ratio', 'Spam Ratio %'),
        ]

        for key, label in display_metrics:
            val_a = result.period_a.get(key, 0)
            val_b = result.period_b.get(key, 0)
            change = result.differences.get(key, 0)

            # Format values
            if key == 'spam_ratio':
                val_a_str = f"{val_a:.1f}%"
                val_b_str = f"{val_b:.1f}%"
            else:
                val_a_str = str(int(val_a))
                val_b_str = str(int(val_b))

            change_str = f"{change:+.1f}%"

            lines.append(f"{label:<25} {val_a_str:>10} {val_b_str:>10} {change_str:>10}")

        lines.append("")

        # Highlights
        if result.highlights:
            lines.append("HIGHLIGHTS:")
            for h in result.highlights:
                lines.append(f"   - {h}")
            lines.append("")

        # Improvements
        if result.improvements:
            lines.append("IMPROVEMENTS:")
            for imp in result.improvements:
                lines.append(f"   + {imp}")
            lines.append("")

        # Declines
        if result.declines:
            lines.append("DECLINES:")
            for dec in result.declines:
                lines.append(f"   - {dec}")
            lines.append("")

        lines.extend(["=" * 60])

        return "\n".join(lines)
