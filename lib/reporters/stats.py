"""Statistics Dashboard for LinkedIn Message Analyzer.

Provides aggregated statistics and insights about message patterns,
trends, and spam behavior over time.
"""

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from lib.analyzer import LinkedInMessageAnalyzer


class StatsDashboard:
    """Generate comprehensive statistics and insights."""

    def __init__(self, analyzer: "LinkedInMessageAnalyzer"):
        """Initialize the dashboard.

        Args:
            analyzer: LinkedInMessageAnalyzer instance with completed analysis
        """
        self.analyzer = analyzer

    def get_overview(self) -> dict[str, Any]:
        """Get high-level overview statistics.

        Returns:
            Dictionary with overview metrics
        """
        a = self.analyzer
        total = len(a.messages)

        # Count unique senders
        unique_senders = len(set(m.get('from', '') for m in a.messages))

        # Response rate (messages where we responded / total conversations)
        conversations = set(m.get('conversation_id', '') for m in a.messages)
        responded_convos = len(a.my_responses)
        response_rate = responded_convos / max(len(conversations), 1) * 100

        return {
            'total_messages': total,
            'unique_senders': unique_senders,
            'conversations': len(conversations),
            'response_rate': round(response_rate, 1),
            'date_range': {
                'start': a.date_range[0].isoformat() if a.date_range else None,
                'end': a.date_range[1].isoformat() if a.date_range else None,
            },
        }

    def get_category_breakdown(self) -> dict[str, dict[str, Any]]:
        """Get breakdown by message category.

        Returns:
            Dictionary with category statistics
        """
        a = self.analyzer
        total = max(len(a.messages), 1)

        categories = {
            'time_requests': {
                'count': len(a.time_requests),
                'percentage': round(len(a.time_requests) / total * 100, 1),
                'description': 'Requests for your time (calls, meetings, coffee)',
            },
            'financial_advisors': {
                'count': len(a.financial_advisor_messages),
                'percentage': round(len(a.financial_advisor_messages) / total * 100, 1),
                'description': 'Financial planners and wealth managers',
            },
            'recruiters': {
                'count': len(a.recruiter_messages),
                'percentage': round(len(a.recruiter_messages) / total * 100, 1),
                'description': 'Job opportunities and recruiting outreach',
            },
            'franchise_consultants': {
                'count': len(a.franchise_consultant_messages),
                'percentage': round(len(a.franchise_consultant_messages) / total * 100, 1),
                'description': 'Franchise and business opportunity pitches',
            },
            'expert_networks': {
                'count': len(a.expert_network_messages),
                'percentage': round(len(a.expert_network_messages) / total * 100, 1),
                'description': 'Paid consultation requests (GLG, Arbolus, etc.)',
            },
            'ai_generated': {
                'count': len(a.ai_generated_messages),
                'percentage': round(len(a.ai_generated_messages) / total * 100, 1),
                'description': 'Obviously AI/ChatGPT generated messages',
            },
            'crypto_hustlers': {
                'count': len(a.crypto_hustler_messages),
                'percentage': round(len(a.crypto_hustler_messages) / total * 100, 1),
                'description': 'Crypto, NFT, and Web3 pitches',
            },
            'mlm': {
                'count': len(a.mlm_messages),
                'percentage': round(len(a.mlm_messages) / total * 100, 1),
                'description': 'MLM and pyramid scheme indicators',
            },
            'angel_investors': {
                'count': len(a.angel_investor_messages),
                'percentage': round(len(a.angel_investor_messages) / total * 100, 1),
                'description': 'Startup investment and advisory pitches',
            },
        }

        return categories

    def get_time_analysis(self) -> dict[str, Any]:
        """Analyze message timing patterns.

        Returns:
            Dictionary with timing analysis
        """
        a = self.analyzer

        # Get hourly distribution
        hourly = dict(a.time_patterns.get('by_hour', {}))

        # Get daily distribution
        daily = dict(a.time_patterns.get('by_day', {}))

        # Calculate business hours vs off-hours
        business_hours = sum(hourly.get(h, 0) for h in range(9, 17))
        total = sum(hourly.values())
        off_hours = total - business_hours

        # Find peak times
        peak_hour = max(hourly.items(), key=lambda x: x[1]) if hourly else (0, 0)
        peak_day = max(daily.items(), key=lambda x: x[1]) if daily else ('Monday', 0)

        # Weekend analysis
        weekend = daily.get('Saturday', 0) + daily.get('Sunday', 0)

        # Suspicious hours (likely bots)
        bot_indicators = []
        for hour in [0, 1, 2, 3, 4, 5, 23]:
            if hourly.get(hour, 0) > 0:
                bot_indicators.append({
                    'hour': f'{hour:02d}:00',
                    'count': hourly[hour],
                    'reason': 'Unusual hour for genuine outreach',
                })

        return {
            'hourly_distribution': hourly,
            'daily_distribution': daily,
            'business_hours_count': business_hours,
            'off_hours_count': off_hours,
            'business_hours_pct': round(business_hours / max(total, 1) * 100, 1),
            'off_hours_pct': round(off_hours / max(total, 1) * 100, 1),
            'peak_hour': {'hour': peak_hour[0], 'count': peak_hour[1]},
            'peak_day': {'day': peak_day[0], 'count': peak_day[1]},
            'weekend_count': weekend,
            'weekend_pct': round(weekend / max(total, 1) * 100, 1),
            'bot_indicators': bot_indicators,
        }

    def get_trend_analysis(self, weeks: int = 12) -> dict[str, Any]:
        """Analyze trends over time.

        Args:
            weeks: Number of weeks to analyze

        Returns:
            Dictionary with trend data
        """
        a = self.analyzer
        cutoff = datetime.now() - timedelta(weeks=weeks)

        # Group messages by week
        weekly_counts: dict[str, int] = defaultdict(int)
        weekly_categories: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

        for msg in a.messages:
            if msg.get('date') and msg['date'] >= cutoff:
                week_key = msg['date'].strftime('%Y-W%W')
                weekly_counts[week_key] += 1

        # Track category trends
        category_sources = [
            ('time_requests', a.time_requests),
            ('financial_advisors', a.financial_advisor_messages),
            ('recruiters', a.recruiter_messages),
            ('ai_generated', a.ai_generated_messages),
        ]

        for cat_name, cat_messages in category_sources:
            for msg in cat_messages:
                if msg.get('date') and msg['date'] >= cutoff:
                    week_key = msg['date'].strftime('%Y-W%W')
                    weekly_categories[week_key][cat_name] += 1

        # Calculate trend direction
        sorted_weeks = sorted(weekly_counts.keys())
        if len(sorted_weeks) >= 2:
            first_half = sum(weekly_counts[w] for w in sorted_weeks[:len(sorted_weeks)//2])
            second_half = sum(weekly_counts[w] for w in sorted_weeks[len(sorted_weeks)//2:])
            if second_half > first_half * 1.1:
                trend = 'increasing'
            elif second_half < first_half * 0.9:
                trend = 'decreasing'
            else:
                trend = 'stable'
        else:
            trend = 'insufficient_data'

        return {
            'weekly_totals': dict(weekly_counts),
            'weekly_by_category': {k: dict(v) for k, v in weekly_categories.items()},
            'overall_trend': trend,
            'weeks_analyzed': len(sorted_weeks),
        }

    def get_sender_analysis(self) -> dict[str, Any]:
        """Analyze sender patterns.

        Returns:
            Dictionary with sender analysis
        """
        a = self.analyzer

        # Count messages per sender
        sender_counts: dict[str, int] = defaultdict(int)
        for msg in a.messages:
            sender = msg.get('from', 'Unknown')
            sender_counts[sender] += 1

        # Top senders
        top_senders = sorted(sender_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        # One-time vs repeat senders
        one_time = sum(1 for count in sender_counts.values() if count == 1)
        repeat = len(sender_counts) - one_time

        # Company domain analysis (extract from sender names/titles heuristically)
        # This is a simplified version - could be enhanced with actual profile data

        return {
            'unique_senders': len(sender_counts),
            'one_time_senders': one_time,
            'repeat_senders': repeat,
            'one_time_pct': round(one_time / max(len(sender_counts), 1) * 100, 1),
            'top_senders': [{'name': name, 'count': count} for name, count in top_senders],
            'repeat_offenders_count': len(a.repeat_offenders),
        }

    def get_quality_analysis(self) -> dict[str, Any]:
        """Analyze message quality indicators.

        Returns:
            Dictionary with quality metrics
        """
        a = self.analyzer

        # Flattery analysis
        flattery = a.get_flattery_summary()

        # Template detection
        template_count = len(a.template_messages)
        fake_personal = len(a.fake_personalization_messages)

        # AI detection
        ai_count = len(a.ai_generated_messages)
        if a.ai_generated_messages:
            avg_ai_score = sum(m.get('ai_score', 0) for m in a.ai_generated_messages) / len(a.ai_generated_messages)
        else:
            avg_ai_score = 0

        # Calculate overall "authenticity score"
        total = max(len(a.messages), 1)
        authenticity = 100 - (
            (template_count / total * 30) +  # Templates hurt authenticity
            (fake_personal / total * 30) +   # Fake personalization hurts
            (ai_count / total * 40)          # AI-generated hurts most
        )
        authenticity = max(0, min(100, authenticity))

        return {
            'flattery': {
                'messages_with_flattery': flattery['messages_with_flattery'],
                'average_score': flattery['avg_score'],
                'max_score': flattery['max_score'],
            },
            'templates': {
                'obvious_templates': template_count,
                'fake_personalization': fake_personal,
            },
            'ai_generated': {
                'count': ai_count,
                'average_score': round(avg_ai_score, 1),
            },
            'authenticity_index': round(authenticity, 1),
            'authenticity_grade': self._grade_authenticity(authenticity),
        }

    def _grade_authenticity(self, score: float) -> str:
        """Convert authenticity score to letter grade."""
        if score >= 90:
            return 'A'
        elif score >= 80:
            return 'B'
        elif score >= 70:
            return 'C'
        elif score >= 60:
            return 'D'
        else:
            return 'F'

    def get_spam_score(self) -> dict[str, Any]:
        """Calculate overall "spam score" for the inbox.

        Returns:
            Dictionary with spam analysis
        """
        a = self.analyzer
        total = max(len(a.messages), 1)

        # Count various spam indicators
        spam_indicators = {
            'time_requests': len(a.time_requests),
            'financial_advisors': len(a.financial_advisor_messages),
            'franchise': len(a.franchise_consultant_messages),
            'ai_generated': len(a.ai_generated_messages),
            'mlm': len(a.mlm_messages),
            'crypto': len(a.crypto_hustler_messages),
            'fake_personalization': len(a.fake_personalization_messages),
            'templates': len(a.template_messages),
        }

        # Calculate weighted spam score
        weights = {
            'time_requests': 1,
            'financial_advisors': 2,
            'franchise': 2,
            'ai_generated': 3,
            'mlm': 5,
            'crypto': 3,
            'fake_personalization': 2,
            'templates': 2,
        }

        weighted_sum = sum(spam_indicators[k] * weights[k] for k in spam_indicators)
        max_possible = total * max(weights.values())
        spam_score = min(100, (weighted_sum / max(max_possible, 1)) * 100)

        # Determine spam level
        if spam_score >= 70:
            level = 'Critical'
            emoji = '🔴'
            message = 'Your inbox is a dumpster fire. Consider LinkedIn detox.'
        elif spam_score >= 50:
            level = 'High'
            emoji = '🟠'
            message = 'Significant spam levels. Time for some aggressive filtering.'
        elif spam_score >= 30:
            level = 'Moderate'
            emoji = '🟡'
            message = 'Normal levels of LinkedIn noise. You\'re not alone.'
        elif spam_score >= 10:
            level = 'Low'
            emoji = '🟢'
            message = 'Your inbox is relatively clean. Lucky you!'
        else:
            level = 'Minimal'
            emoji = '🌟'
            message = 'Are you sure this is a real LinkedIn account?'

        return {
            'spam_score': round(spam_score, 1),
            'level': level,
            'emoji': emoji,
            'message': message,
            'breakdown': spam_indicators,
            'weights': weights,
        }

    def get_full_dashboard(self) -> dict[str, Any]:
        """Get complete dashboard data.

        Returns:
            Dictionary with all dashboard sections
        """
        return {
            'overview': self.get_overview(),
            'categories': self.get_category_breakdown(),
            'timing': self.get_time_analysis(),
            'trends': self.get_trend_analysis(),
            'senders': self.get_sender_analysis(),
            'quality': self.get_quality_analysis(),
            'spam_score': self.get_spam_score(),
            'generated_at': datetime.now().isoformat(),
        }

    def print_dashboard(self) -> None:
        """Print a formatted dashboard to console."""
        dashboard = self.get_full_dashboard()

        print("\n" + "=" * 70)
        print("LINKEDIN MESSAGE STATISTICS DASHBOARD")
        print("=" * 70)

        # Overview
        overview = dashboard['overview']
        print(f"\n📊 OVERVIEW")
        print(f"   Total Messages: {overview['total_messages']}")
        print(f"   Unique Senders: {overview['unique_senders']}")
        print(f"   Conversations: {overview['conversations']}")
        print(f"   Response Rate: {overview['response_rate']}%")

        # Spam Score
        spam = dashboard['spam_score']
        print(f"\n{spam['emoji']} SPAM SCORE: {spam['spam_score']}/100 ({spam['level']})")
        print(f"   {spam['message']}")

        # Quality
        quality = dashboard['quality']
        print(f"\n📝 MESSAGE QUALITY")
        print(f"   Authenticity Index: {quality['authenticity_index']}/100 (Grade: {quality['authenticity_grade']})")
        print(f"   AI-Generated Messages: {quality['ai_generated']['count']}")
        print(f"   Obvious Templates: {quality['templates']['obvious_templates']}")

        # Timing
        timing = dashboard['timing']
        print(f"\n⏰ TIMING PATTERNS")
        print(f"   Peak Hour: {timing['peak_hour']['hour']}:00 ({timing['peak_hour']['count']} messages)")
        print(f"   Peak Day: {timing['peak_day']['day']}")
        print(f"   Business Hours: {timing['business_hours_pct']}%")
        print(f"   Weekend Messages: {timing['weekend_pct']}%")

        # Top Categories
        cats = dashboard['categories']
        print(f"\n📋 TOP CATEGORIES")
        sorted_cats = sorted(cats.items(), key=lambda x: x[1]['count'], reverse=True)
        for cat_name, cat_data in sorted_cats[:5]:
            if cat_data['count'] > 0:
                print(f"   {cat_name.replace('_', ' ').title()}: {cat_data['count']} ({cat_data['percentage']}%)")

        # Trends
        trends = dashboard['trends']
        print(f"\n📈 TREND: {trends['overall_trend'].upper()}")
        print(f"   Analyzed {trends['weeks_analyzed']} weeks of data")

        print("\n" + "=" * 70)


def generate_stats_dashboard(analyzer: "LinkedInMessageAnalyzer") -> dict[str, Any]:
    """Convenience function to generate full dashboard.

    Args:
        analyzer: LinkedInMessageAnalyzer instance

    Returns:
        Complete dashboard data
    """
    dashboard = StatsDashboard(analyzer)
    return dashboard.get_full_dashboard()
