"""Console reporter for LinkedIn Message Analyzer."""

import sys
from datetime import datetime
from typing import Any, TYPE_CHECKING

from lib.constants import DEFAULT_WEEKS_BACK
from lib.anonymizer import anonymize_name

if TYPE_CHECKING:
    from lib.analyzer import LinkedInMessageAnalyzer


def safe_str(text: str) -> str:
    """Make text safe for console printing on Windows.

    Replaces characters that can't be encoded in the console's encoding.

    Args:
        text: Input text that may contain Unicode characters

    Returns:
        Text safe to print on any console
    """
    if not text:
        return text
    # Try to encode with console encoding, replacing problematic chars
    try:
        encoding = sys.stdout.encoding or 'utf-8'
        return text.encode(encoding, errors='replace').decode(encoding)
    except (UnicodeError, LookupError):
        # Fallback: keep only ASCII
        return text.encode('ascii', errors='replace').decode('ascii')


class ConsoleReporter:
    """Generates console output reports."""

    def __init__(self, weeks_back: int = DEFAULT_WEEKS_BACK) -> None:
        """Initialize the console reporter.

        Args:
            weeks_back: Number of weeks to include in weekly summaries
        """
        self.weeks_back = weeks_back

    def generate(self, analyzer: 'LinkedInMessageAnalyzer') -> None:
        """Generate and print the full analysis report.

        Args:
            analyzer: The analyzer with completed analysis
        """
        self.print_report(analyzer)

    def _filter_by_date(self, messages: list[dict], cutoff: datetime) -> list[dict]:
        """Filter messages to only include those after the cutoff date."""
        return [m for m in messages if m.get('date') and m['date'] >= cutoff]

    def print_report(self, analyzer: 'LinkedInMessageAnalyzer') -> None:
        """Print a formatted analysis report.

        Args:
            analyzer: The analyzer with completed analysis
        """
        from datetime import timedelta

        summary = analyzer.get_weekly_summary(self.weeks_back)

        # Calculate cutoff for filtering
        cutoff = datetime.now() - timedelta(weeks=self.weeks_back)

        # Filter all message lists by date
        recent_messages = self._filter_by_date(analyzer.messages, cutoff)
        recent_time_requests = self._filter_by_date(analyzer.time_requests, cutoff)
        recent_fa = self._filter_by_date(analyzer.financial_advisor_messages, cutoff)
        recent_franchise = self._filter_by_date(analyzer.franchise_consultant_messages, cutoff)
        recent_expert = self._filter_by_date(analyzer.expert_network_messages, cutoff)
        recent_angel = self._filter_by_date(analyzer.angel_investor_messages, cutoff)
        recent_recruiter = self._filter_by_date(analyzer.recruiter_messages, cutoff)
        recent_role_confusion = self._filter_by_date(analyzer.role_confusion_messages, cutoff)
        recent_fake_personalization = self._filter_by_date(analyzer.fake_personalization_messages, cutoff)

        print("\n" + "=" * 70)
        print(f"LINKEDIN MESSAGE ANALYSIS REPORT (Last {self.weeks_back} weeks)")
        print("=" * 70)

        # Overall stats
        print(f"\nTotal messages analyzed: {len(recent_messages)}")
        print(f"Time request messages found: {len(recent_time_requests)}")
        print(f"Financial advisor messages found: {len(recent_fa)}")
        print(f"Franchise consultant messages found: {len(recent_franchise)}")
        print(f"Expert network messages found: {len(recent_expert)}")
        print(f"Angel investor pitch messages found: {len(recent_angel)}")
        print(f"Recruiter messages found: {len(recent_recruiter)}")
        print(f"Role confusion messages found: {len(recent_role_confusion)}")
        print(f"Fake personalization messages found: {len(recent_fake_personalization)}")

        # Audacity metrics
        metrics = analyzer.calculate_audacity_metrics(self.weeks_back)
        print("\n" + "-" * 70)
        print("THE AUDACITY METRICS")
        print("-" * 70)
        print(f"If you said yes to everyone: {metrics['if_yes_to_all_yearly_hours']} hours/year")
        print(f"That's {metrics['pct_of_40hr_week']}% of a 40-hour work week")
        print(f"Financial advisors: {metrics['fa_pct_of_requests']}% of all time requests")

        # Weekly time requests
        self._print_weekly_time_requests(summary)

        # Weekly FA outreach
        self._print_weekly_fa_outreach(summary)

        # Recent time requests detail
        self._print_recent_time_requests(analyzer)

        # Repeat offenders section
        self._print_repeat_offenders(analyzer)

        # Time patterns section
        self._print_time_patterns(analyzer)

        # Flattery section
        self._print_flattery_section(analyzer)

        # Hall of Shame
        self._print_hall_of_shame(analyzer)

        print("\n" + "=" * 70)

    def _print_weekly_time_requests(self, summary: dict[str, Any]) -> None:
        """Print weekly time requests section."""
        print("\n" + "-" * 70)
        print("WEEKLY TIME REQUESTS (estimated)")
        print("-" * 70)
        print(f"{'Week':<12} {'Requests':<10} {'Est. Hours':<12} {'Top Requesters'}")
        print("-" * 70)

        total_requests = 0
        total_hours = 0

        for week in sorted(summary['time_requests_by_week'].keys(), reverse=True):
            data = summary['time_requests_by_week'][week]
            hours = data['total_minutes'] / 60
            total_requests += data['count']
            total_hours += hours
            top_requesters = ', '.join(anonymize_name(r) for r in data['requesters'][:3])
            if len(data['requesters']) > 3:
                top_requesters += f" (+{len(data['requesters']) - 3} more)"
            print(f"{week:<12} {data['count']:<10} {hours:<12.1f} {safe_str(top_requesters[:40])}")

        print("-" * 70)
        print(f"{'TOTAL':<12} {total_requests:<10} {total_hours:<12.1f}")
        avg_per_week = total_hours / max(len(summary['time_requests_by_week']), 1)
        print(f"\nAverage requested time per week: {avg_per_week:.1f} hours")

    def _print_weekly_fa_outreach(self, summary: dict[str, Any]) -> None:
        """Print weekly financial advisor outreach section."""
        print("\n" + "-" * 70)
        print("WEEKLY FINANCIAL ADVISOR OUTREACH")
        print("-" * 70)
        print(f"{'Week':<12} {'Count':<10} {'Senders'}")
        print("-" * 70)

        total_fa = 0
        for week in sorted(summary['fa_outreach_by_week'].keys(), reverse=True):
            data = summary['fa_outreach_by_week'][week]
            total_fa += data['count']
            senders = ', '.join(set(anonymize_name(s) for s in data['senders'][:3]))
            if len(data['senders']) > 3:
                senders += f" (+{len(data['senders']) - 3} more)"
            print(f"{week:<12} {data['count']:<10} {safe_str(senders[:45])}")

        print("-" * 70)
        print(f"{'TOTAL':<12} {total_fa}")
        avg_fa_per_week = total_fa / max(len(summary['fa_outreach_by_week']), 1)
        print(f"\nAverage FA contacts per week: {avg_fa_per_week:.1f}")

    def _print_recent_time_requests(self, analyzer: 'LinkedInMessageAnalyzer') -> None:
        """Print recent time requests section."""
        print("\n" + "-" * 70)
        print("RECENT TIME REQUESTS (Last 10)")
        print("-" * 70)

        recent_requests = sorted(
            analyzer.time_requests,
            key=lambda x: x['date'] if x['date'] else datetime.min,
            reverse=True
        )[:10]
        for req in recent_requests:
            date_str = req['date'].strftime('%Y-%m-%d') if req['date'] else 'Unknown'
            print(f"\n{date_str} - {safe_str(anonymize_name(req['from']))}")
            print(f"  Est. time: {req['estimated_minutes']} min")
            # Show snippet of the request
            content_snippet = req['content'][:150].replace('\n', ' ') if req['content'] else ''
            if req['content'] and len(req['content']) > 150:
                content_snippet += "..."
            print(f"  Message: {safe_str(content_snippet)}")

    def _print_repeat_offenders(self, analyzer: 'LinkedInMessageAnalyzer') -> None:
        """Print repeat offenders section."""
        print("\n" + "-" * 70)
        print("REPEAT OFFENDERS (2+ messages, no response)")
        print("-" * 70)

        if analyzer.repeat_offenders:
            sorted_offenders = sorted(
                analyzer.repeat_offenders.items(),
                key=lambda x: x[1]['count'],
                reverse=True
            )
            print(f"{'Sender':<30} {'Count':<8} {'First Contact':<12} {'Last Contact'}")
            print("-" * 70)
            for sender, data in sorted_offenders[:10]:
                first = data['first_contact'].strftime('%Y-%m-%d') if data['first_contact'] else 'N/A'
                last = data['last_contact'].strftime('%Y-%m-%d') if data['last_contact'] else 'N/A'
                anon_sender = safe_str(anonymize_name(sender))
                print(f"{anon_sender[:29]:<30} {data['count']:<8} {first:<12} {last}")
        else:
            print("No repeat offenders found.")

    def _print_time_patterns(self, analyzer: 'LinkedInMessageAnalyzer') -> None:
        """Print time patterns section."""
        print("\n" + "-" * 70)
        print("MESSAGE TIME PATTERNS")
        print("-" * 70)

        time_stats = analyzer.get_time_pattern_summary()
        print(f"Peak hour: {time_stats['peak_hour'][0]}:00 ({time_stats['peak_hour'][1]} messages)")
        print(f"Peak day: {time_stats['peak_day'][0]} ({time_stats['peak_day'][1]} messages)")
        print(f"Off-hours messages: {time_stats['off_hours_count']} ({time_stats['off_hours_pct']}%)")
        print(f"Weekend messages: {time_stats['weekend_count']} ({time_stats['weekend_pct']}%)")

        if time_stats['suspicious_hours']:
            print("\nSuspicious hours (likely automation):")
            for hour, count in time_stats['suspicious_hours']:
                print(f"  {hour}:00 - {count} messages")

        # Hour distribution
        print("\nHourly distribution:")
        by_hour = time_stats['by_hour']
        max_count = max(by_hour.values()) if by_hour else 1
        for hour in range(6, 24):  # Show 6am to 11pm
            count = by_hour.get(hour, 0)
            bar = '#' * int(count / max_count * 20) if max_count > 0 else ''
            print(f"  {hour:02d}:00 | {bar:<20} {count}")

    def _print_flattery_section(self, analyzer: 'LinkedInMessageAnalyzer') -> None:
        """Print flattery section."""
        print("\n" + "-" * 70)
        print("FLATTERY INDEX")
        print("-" * 70)

        flattery_stats = analyzer.get_flattery_summary()
        print(f"Messages with flattery: {flattery_stats['messages_with_flattery']}")
        print(f"Average flattery score: {flattery_stats['avg_score']}")
        print(f"Maximum flattery score: {flattery_stats['max_score']}")

        if flattery_stats.get('most_common_phrases'):
            print("\nMost common flattery phrases:")
            for phrase, count in flattery_stats['most_common_phrases'][:5]:
                print(f"  \"{phrase}\" - used {count} times")

        if flattery_stats.get('top_flatterers'):
            print("\nTop flatterers:")
            for msg in flattery_stats['top_flatterers'][:3]:
                print(f"\n  {safe_str(anonymize_name(msg['from']))} (score: {msg['flattery_score']})")
                snippet = msg['content'][:100].replace('\n', ' ')
                print(f"  \"{safe_str(snippet)}...\"")

    def _print_hall_of_shame(self, analyzer: 'LinkedInMessageAnalyzer') -> None:
        """Print the Hall of Shame section."""
        print("\n" + "-" * 70)
        print("HALL OF SHAME")
        print("(The most audacious offenders)")
        print("-" * 70)

        hall_of_shame = analyzer.get_hall_of_shame(top_n=5)

        if not hall_of_shame:
            print("No one worthy of shame... yet.")
            return

        medals = ['#1', '#2', '#3', '#4', '#5']

        for i, offender in enumerate(hall_of_shame):
            medal = medals[i] if i < len(medals) else f'{i+1}.'
            print(f"\n{medal} {safe_str(anonymize_name(offender['sender']))}")
            print(f"   Audacity Score: {offender['audacity_score']} ({offender['persistence_level']})")
            print(f"   Messages Sent: {offender['message_count']}")
            if offender['shame_reasons']:
                reasons = ', '.join(offender['shame_reasons'][:3])
                print(f"   Why: {safe_str(reasons)}")
            if offender['sample_message']:
                snippet = offender['sample_message'][:80].replace('\n', ' ')
                print(f"   Sample: \"{safe_str(snippet)}...\"")

    def generate_post_stats(self, analyzer: 'LinkedInMessageAnalyzer') -> str:
        """Generate witty, quotable statistics for a LinkedIn post.

        Args:
            analyzer: The analyzer with completed analysis

        Returns:
            Formatted string suitable for social media
        """
        from datetime import timedelta

        # Calculate cutoff date for filtering
        cutoff = datetime.now() - timedelta(weeks=self.weeks_back)

        # Filter all message lists by date
        recent_messages = self._filter_by_date(analyzer.messages, cutoff)
        recent_time_requests = self._filter_by_date(analyzer.time_requests, cutoff)
        recent_fa = self._filter_by_date(analyzer.financial_advisor_messages, cutoff)
        recent_franchise = self._filter_by_date(analyzer.franchise_consultant_messages, cutoff)
        recent_expert = self._filter_by_date(analyzer.expert_network_messages, cutoff)
        recent_ai = self._filter_by_date(analyzer.ai_generated_messages, cutoff)
        recent_crypto = self._filter_by_date(analyzer.crypto_hustler_messages, cutoff)
        recent_mlm = self._filter_by_date(analyzer.mlm_messages, cutoff)
        recent_angel = self._filter_by_date(analyzer.angel_investor_messages, cutoff)
        recent_recruiter = self._filter_by_date(analyzer.recruiter_messages, cutoff)

        metrics = analyzer.calculate_audacity_metrics(self.weeks_back)
        time_stats = analyzer.get_time_pattern_summary()
        flattery_stats = analyzer.get_flattery_summary()

        lines = []
        lines.append("=" * 60)
        lines.append("LINKEDIN INBOX ANALYSIS: THE AUDACITY REPORT")
        lines.append(f"(Last {self.weeks_back} weeks)")
        lines.append("=" * 60)
        lines.append("")
        lines.append("I used AI to analyze my LinkedIn messages. Here's what I found:")
        lines.append("")

        # Overall breakdown
        lines.append("MESSAGE BREAKDOWN:")
        lines.append(f"   - Total messages analyzed: {len(recent_messages)}")
        lines.append(f"   - Time requests: {len(recent_time_requests)}")
        lines.append(f"   - Financial advisors: {len(recent_fa)}")
        lines.append(f"   - Franchise consultants: {len(recent_franchise)}")
        lines.append(f"   - Expert networks (GLG, Arbolus, etc.): {len(recent_expert)}")
        lines.append(f"   - AI-generated slop: {len(recent_ai)}")
        lines.append(f"   - Crypto/NFT hustlers: {len(recent_crypto)}")
        lines.append(f"   - MLM/pyramid schemes: {len(recent_mlm)}")
        lines.append(f"   - Angel investor pitches: {len(recent_angel)}")
        lines.append(f"   - Recruiters: {len(recent_recruiter)}")
        lines.append("")

        # Time requests
        lines.append(f"TIME REQUESTED FROM STRANGERS:")
        lines.append(f"   - {metrics['total_hours_requested']} hours total in last {self.weeks_back} weeks")
        lines.append(f"   - {metrics['hours_per_week']} hours/week average")
        lines.append(f"   - That's {metrics['pct_of_40hr_week']}% of a 40-hour work week")
        lines.append(f"   - If I said yes to everyone: {metrics['if_yes_to_all_yearly_hours']} hours/year")
        lines.append("")

        # Financial advisors
        lines.append(f"FINANCIAL ADVISORS:")
        lines.append(f"   - {len(recent_fa)} messages from FAs")
        if len(recent_time_requests) > 0:
            fa_pct = round(len(recent_fa) / len(recent_time_requests) * 100, 1)
            lines.append(f"   - {fa_pct}% of all 'quick call' requests")
        lines.append(f"   - Apparently my retirement is everyone's concern but mine")
        lines.append("")

        # Franchise consultants
        if len(recent_franchise) > 0:
            lines.append(f"FRANCHISE CONSULTANTS:")
            lines.append(f"   - {len(recent_franchise)} messages trying to sell me a franchise")
            lines.append(f"   - I already own one, but thanks for the offer")
            lines.append(f"   - Highlights: 'be your own boss', 'income diversification', 'corporate layoffs'")
            lines.append("")

        # Angel investors
        if len(recent_angel) > 0:
            lines.append(f"ANGEL INVESTOR PITCHES:")
            lines.append(f"   - {len(recent_angel)} startups want my money")
            lines.append(f"   - Common themes: 'angel round', 'advisory board', 'ground floor'")
            lines.append("")

        # Expert networks
        if len(recent_expert) > 0:
            lines.append(f"EXPERT NETWORKS (GLG, Arbolus, Guidepoint, etc.):")
            lines.append(f"   - {len(recent_expert)} paid consultation requests")
            lines.append(f"   - At least these ones pay...")
            lines.append("")

        # AI-generated slop
        if len(recent_ai) > 0:
            lines.append("AI-GENERATED SLOP:")
            lines.append(f"   - {len(recent_ai)} messages that definitely came from ChatGPT")
            lines.append(f"   - Top tells: 'I hope this finds you well', 'I wanted to reach out'")
            # Get highest AI score from recent messages
            top_ai = max(recent_ai, key=lambda x: x.get('ai_score', 0), default=None)
            if top_ai:
                lines.append(f"   - Highest AI score: {top_ai.get('ai_score', 0)} points")
            lines.append(f"   - Using AI to write about how much you love my work... ironic")
            lines.append("")

        # Crypto hustlers
        if len(recent_crypto) > 0:
            lines.append("CRYPTO/NFT HUSTLERS:")
            lines.append(f"   - {len(recent_crypto)} messages about 'the future of finance'")
            lines.append(f"   - No, I don't want to hear about your NFT project")
            lines.append("")

        # MLM
        if len(recent_mlm) > 0:
            lines.append("MLM/PYRAMID SCHEME VIBES:")
            lines.append(f"   - {len(recent_mlm)} 'amazing opportunities' detected")
            lines.append(f"   - 'Passive income' is doing a lot of heavy lifting here")
            lines.append("")

        # Repeat offenders
        lines.append("REPEAT OFFENDERS (messaged 2+ times, no response):")
        lines.append(f"   - {len(analyzer.repeat_offenders)} persistent senders")
        if analyzer.repeat_offenders:
            top_offender = max(analyzer.repeat_offenders.items(), key=lambda x: x[1]['count'])
            lines.append(f"   - Most persistent: {top_offender[1]['count']} messages from one person")
            lines.append(f"   - The follow-up is strong with these ones")
        lines.append("")

        # Time patterns (automation detection)
        lines.append(f"WHEN MESSAGES ARE SENT:")
        lines.append(f"   - Peak hour: {time_stats['peak_hour'][0]}:00 ({time_stats['peak_hour'][1]} messages)")
        lines.append(f"   - Peak day: {time_stats['peak_day'][0]}")
        lines.append(f"   - Off-hours (before 9am/after 5pm): {time_stats['off_hours_pct']}%")
        lines.append(f"   - Weekend messages: {time_stats['weekend_pct']}%")
        if time_stats['suspicious_hours']:
            weird_hours = [f"{h}:00" for h, c in time_stats['suspicious_hours'][:5]]
            lines.append(f"   - Messages at {', '.join(weird_hours)}? Definitely not a bot.")
        lines.append("")

        # Flattery index
        lines.append(f"FLATTERY INDEX:")
        lines.append(f"   - {flattery_stats['messages_with_flattery']} messages contained flattery")
        lines.append(f"   - Average flattery score: {flattery_stats['avg_score']} points")
        lines.append(f"   - Highest flattery score: {flattery_stats['max_score']} points")
        if flattery_stats.get('most_common_phrases'):
            top_phrases = [p[0] for p in flattery_stats['most_common_phrases'][:3]]
            phrases_str = '", "'.join(top_phrases)
            lines.append(f'   - Most used: "{phrases_str}"')
        lines.append("")

        # Automation fails
        lines.append(f"AUTOMATION QUALITY:")
        lines.append(f"   - {metrics['fake_personalization_count']} 'personalized' messages that weren't")
        lines.append(f"   - {metrics['role_confusion_count']} people who confused my roles")
        if metrics['role_confusion_count'] > 0:
            lines.append(f"   - (Yes, Microsoft and a stretch franchise are different things)")
            lines.append(f"   - Bonus: Someone called me a 'Microsoft franchisee'")
        lines.append("")

        # Snarky observations
        lines.append("KEY INSIGHTS:")
        lines.append("   - 'Quick 15-minute call' is never 15 minutes")
        lines.append("   - 'Pick your brain' = free consulting")
        lines.append("   - 'Grab coffee' from someone 2,000 miles away = Zoom call")
        lines.append("   - The more exclamation marks, the less genuine the message!!!")
        lines.append("")

        return "\n".join(lines)
