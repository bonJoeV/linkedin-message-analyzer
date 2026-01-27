"""Trend analysis for LinkedIn message patterns over time."""

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from lib.analyzer import LinkedInMessageAnalyzer


class TrendAnalyzer:
    """Analyzes inbox trends over time periods.

    Tracks patterns like:
    - Message volume changes
    - Category shifts (more recruiters, fewer FAs, etc.)
    - Anomaly detection (spikes/drops)
    - Velocity metrics (rate of change)
    """

    def __init__(self, analyzer: 'LinkedInMessageAnalyzer') -> None:
        """Initialize with a LinkedInMessageAnalyzer.

        Args:
            analyzer: Analyzer with loaded and analyzed messages
        """
        self.analyzer = analyzer
        self._period_data: dict[str, dict[str, Any]] = {}

    def analyze_by_period(
        self,
        period: str = 'weekly',
        weeks_back: int = 12,
    ) -> dict[str, Any]:
        """Aggregate analysis results by time period.

        Args:
            period: Aggregation period ('weekly' or 'monthly')
            weeks_back: Number of weeks to analyze

        Returns:
            Dict with period data and summaries
        """
        if not self.analyzer.messages:
            return {'error': 'No messages loaded'}

        # Calculate date range
        cutoff = datetime.now() - timedelta(weeks=weeks_back)

        # Group messages by period
        periods: dict[str, dict[str, Any]] = defaultdict(lambda: {
            'messages': [],
            'time_requests': 0,
            'financial_advisors': 0,
            'recruiters': 0,
            'ai_generated': 0,
            'total': 0,
        })

        for msg in self.analyzer.messages:
            msg_date = msg.get('date')
            if not msg_date or msg_date < cutoff:
                continue

            period_key = self._get_period_key(msg_date, period)
            periods[period_key]['messages'].append(msg)
            periods[period_key]['total'] += 1

        # Count categories per period
        self._count_categories(periods)

        # Calculate velocity (rate of change)
        velocity = self._calculate_velocity(periods)

        # Detect anomalies
        anomalies = self._detect_anomalies(periods)

        # Build result
        sorted_periods = sorted(periods.keys())
        period_list = []

        for key in sorted_periods:
            data = periods[key]
            period_list.append({
                'label': key,
                'total_messages': data['total'],
                'time_requests': data['time_requests'],
                'financial_advisors': data['financial_advisors'],
                'recruiters': data['recruiters'],
                'ai_generated': data['ai_generated'],
            })

        # Summary stats
        all_totals = [p['total_messages'] for p in period_list]
        avg_messages = sum(all_totals) / max(len(all_totals), 1)

        return {
            'period_type': period,
            'periods': period_list,
            'summary': {
                'total_periods': len(period_list),
                'avg_messages_per_period': round(avg_messages, 1),
                'peak_period': max(period_list, key=lambda x: x['total_messages'])['label'] if period_list else None,
                'low_period': min(period_list, key=lambda x: x['total_messages'])['label'] if period_list else None,
            },
            'velocity': velocity,
            'anomalies': anomalies,
        }

    def _get_period_key(self, dt: datetime, period: str) -> str:
        """Get period key for a datetime.

        Args:
            dt: Datetime to convert
            period: 'weekly' or 'monthly'

        Returns:
            Period key string (e.g., '2025-W03' or '2025-01')
        """
        if period == 'monthly':
            return dt.strftime('%Y-%m')
        else:  # weekly
            iso_year, iso_week, _ = dt.isocalendar()
            return f"{iso_year}-W{iso_week:02d}"

    def _count_categories(self, periods: dict[str, dict[str, Any]]) -> None:
        """Count message categories in each period.

        Args:
            periods: Dict of period data to update in-place
        """
        # Build lookup sets for O(1) checking
        time_request_ids = {
            msg.get('conversation_id') for msg in self.analyzer.time_requests
        }
        fa_ids = {
            msg.get('conversation_id') for msg in self.analyzer.financial_advisor_messages
        }
        recruiter_ids = {
            msg.get('conversation_id') for msg in self.analyzer.recruiter_messages
        }
        ai_ids = {
            msg.get('conversation_id') for msg in self.analyzer.ai_generated_messages
        }

        for period_key, data in periods.items():
            for msg in data['messages']:
                conv_id = msg.get('conversation_id')
                if conv_id in time_request_ids:
                    data['time_requests'] += 1
                if conv_id in fa_ids:
                    data['financial_advisors'] += 1
                if conv_id in recruiter_ids:
                    data['recruiters'] += 1
                if conv_id in ai_ids:
                    data['ai_generated'] += 1

    def _calculate_velocity(
        self,
        periods: dict[str, dict[str, Any]],
    ) -> dict[str, Any]:
        """Calculate rate of change metrics.

        Args:
            periods: Period data

        Returns:
            Velocity metrics dict
        """
        sorted_keys = sorted(periods.keys())
        if len(sorted_keys) < 2:
            return {'trend': 'insufficient_data'}

        # Compare first half to second half
        mid = len(sorted_keys) // 2
        first_half = sorted_keys[:mid]
        second_half = sorted_keys[mid:]

        first_avg = sum(periods[k]['total'] for k in first_half) / max(len(first_half), 1)
        second_avg = sum(periods[k]['total'] for k in second_half) / max(len(second_half), 1)

        if first_avg == 0:
            change_pct = 100.0 if second_avg > 0 else 0.0
        else:
            change_pct = ((second_avg - first_avg) / first_avg) * 100

        trend = 'increasing' if change_pct > 10 else 'decreasing' if change_pct < -10 else 'stable'

        return {
            'trend': trend,
            'change_percent': round(change_pct, 1),
            'first_half_avg': round(first_avg, 1),
            'second_half_avg': round(second_avg, 1),
        }

    def _detect_anomalies(
        self,
        periods: dict[str, dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Detect unusual spikes or drops.

        Args:
            periods: Period data

        Returns:
            List of anomaly dicts
        """
        if len(periods) < 3:
            return []

        totals = {k: v['total'] for k, v in periods.items()}
        values = list(totals.values())

        if not values:
            return []

        avg = sum(values) / len(values)
        std_dev = (sum((x - avg) ** 2 for x in values) / len(values)) ** 0.5

        if std_dev == 0:
            return []

        anomalies = []
        threshold = 2.0  # 2 standard deviations

        for period_key, total in totals.items():
            z_score = (total - avg) / std_dev
            if abs(z_score) >= threshold:
                anomaly_type = 'spike' if z_score > 0 else 'drop'
                anomalies.append({
                    'period': period_key,
                    'type': anomaly_type,
                    'value': total,
                    'z_score': round(z_score, 2),
                    'description': f"Unusual {anomaly_type}: {total} messages ({abs(z_score):.1f}x std dev)",
                })

        return sorted(anomalies, key=lambda x: abs(x['z_score']), reverse=True)

    def generate_trend_report(
        self,
        period: str = 'weekly',
        weeks_back: int = 12,
    ) -> str:
        """Generate a formatted trend report.

        Args:
            period: 'weekly' or 'monthly'
            weeks_back: Number of weeks to analyze

        Returns:
            Formatted report string
        """
        data = self.analyze_by_period(period=period, weeks_back=weeks_back)

        if 'error' in data:
            return f"Error: {data['error']}"

        lines = [
            "=" * 60,
            "INBOX TREND ANALYSIS",
            "=" * 60,
            "",
            f"Analysis period: Last {weeks_back} weeks ({data['summary']['total_periods']} {period} periods)",
            f"Average messages per {period[:-2] if period.endswith('ly') else period}: {data['summary']['avg_messages_per_period']}",
            "",
        ]

        # Velocity
        velocity = data['velocity']
        if velocity.get('trend') != 'insufficient_data':
            trend_emoji = {
                'increasing': '(trending up)',
                'decreasing': '(trending down)',
                'stable': '(stable)',
            }.get(velocity['trend'], '')

            lines.extend([
                "TREND DIRECTION:",
                f"   Overall: {velocity['trend'].upper()} {trend_emoji}",
                f"   Change: {velocity['change_percent']:+.1f}%",
                f"   First half avg: {velocity['first_half_avg']} messages",
                f"   Second half avg: {velocity['second_half_avg']} messages",
                "",
            ])

        # Peak/low periods
        if data['summary']['peak_period']:
            lines.extend([
                "NOTABLE PERIODS:",
                f"   Busiest: {data['summary']['peak_period']}",
                f"   Quietest: {data['summary']['low_period']}",
                "",
            ])

        # Anomalies
        if data['anomalies']:
            lines.append("ANOMALIES DETECTED:")
            for anomaly in data['anomalies'][:3]:
                lines.append(f"   - {anomaly['description']}")
            lines.append("")

        # Period breakdown (last 6 periods)
        if data['periods']:
            lines.extend([
                "RECENT PERIOD BREAKDOWN:",
                f"   {'Period':<12} {'Total':>7} {'Time Req':>9} {'FA':>5} {'Recruit':>8} {'AI':>5}",
                f"   {'-'*12} {'-'*7} {'-'*9} {'-'*5} {'-'*8} {'-'*5}",
            ])
            for p in data['periods'][-6:]:
                lines.append(
                    f"   {p['label']:<12} {p['total_messages']:>7} "
                    f"{p['time_requests']:>9} {p['financial_advisors']:>5} "
                    f"{p['recruiters']:>8} {p['ai_generated']:>5}"
                )
            lines.append("")

        lines.extend(["=" * 60])

        return "\n".join(lines)
