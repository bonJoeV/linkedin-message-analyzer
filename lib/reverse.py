"""Reverse mode - analyze your own outreach effectiveness."""

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from lib.analyzer import LinkedInMessageAnalyzer


@dataclass
class OutreachMetrics:
    """Metrics for outreach effectiveness.

    Attributes:
        total_sent: Total outbound messages sent
        unique_recipients: Number of unique people messaged
        response_rate: Percentage who responded
        avg_response_time_hours: Average time to get a response
        conversations_started: Conversations you initiated
        conversations_with_response: How many got replies
        best_day: Best day to send messages
        best_hour: Best hour to send messages
        message_length_stats: Stats on your message lengths
    """

    total_sent: int
    unique_recipients: int
    response_rate: float
    avg_response_time_hours: float | None
    conversations_started: int
    conversations_with_response: int
    best_day: str | None
    best_hour: int | None
    message_length_stats: dict[str, Any]


class ReverseAnalyzer:
    """Analyzes user's own outreach messages for effectiveness.

    Helps answer:
    - What's my response rate?
    - What patterns get more responses?
    - When is the best time to send?
    - Are my messages too long/short?
    """

    DAYS_OF_WEEK = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

    def __init__(self, analyzer: 'LinkedInMessageAnalyzer') -> None:
        """Initialize with a LinkedInMessageAnalyzer.

        Args:
            analyzer: Analyzer with loaded and analyzed messages
        """
        self.analyzer = analyzer
        self.outbound_messages: list[dict[str, Any]] = []
        self.conversations_started_by_me: dict[str, dict[str, Any]] = {}
        self.response_times: list[float] = []

    def analyze_outreach(self, my_name: str) -> OutreachMetrics:
        """Analyze outbound message effectiveness.

        Args:
            my_name: Your name as it appears in messages

        Returns:
            OutreachMetrics with all calculated data
        """
        self._identify_outbound_messages(my_name)
        self._identify_conversations_started(my_name)
        self._calculate_response_times()

        # Calculate metrics
        total_sent = len(self.outbound_messages)
        unique_recipients = len(set(
            msg.get('to') or msg.get('recipient', 'unknown')
            for msg in self.outbound_messages
        ))

        conversations_started = len(self.conversations_started_by_me)
        conversations_with_response = sum(
            1 for conv in self.conversations_started_by_me.values()
            if conv.get('got_response', False)
        )

        response_rate = (
            (conversations_with_response / conversations_started * 100)
            if conversations_started > 0 else 0
        )

        avg_response_time = (
            sum(self.response_times) / len(self.response_times)
            if self.response_times else None
        )

        # Best timing analysis
        best_day, best_hour = self._analyze_best_timing()

        # Message length analysis
        length_stats = self._analyze_message_lengths()

        return OutreachMetrics(
            total_sent=total_sent,
            unique_recipients=unique_recipients,
            response_rate=round(response_rate, 1),
            avg_response_time_hours=round(avg_response_time, 1) if avg_response_time else None,
            conversations_started=conversations_started,
            conversations_with_response=conversations_with_response,
            best_day=best_day,
            best_hour=best_hour,
            message_length_stats=length_stats,
        )

    def _identify_outbound_messages(self, my_name: str) -> None:
        """Find all messages sent by the user.

        Args:
            my_name: User's name to match
        """
        my_name_lower = my_name.lower() if my_name else ''

        for msg in self.analyzer.messages:
            sender = msg.get('sender', msg.get('from', '')).lower()
            direction = msg.get('direction', '').upper()

            # Check if this is an outbound message
            is_outbound = (
                direction == 'OUTGOING' or
                (my_name_lower and my_name_lower in sender)
            )

            if is_outbound:
                self.outbound_messages.append(msg)

    def _identify_conversations_started(self, my_name: str) -> None:
        """Identify conversations initiated by the user.

        Args:
            my_name: User's name to match
        """
        my_name_lower = my_name.lower() if my_name else ''

        # Group messages by conversation
        conversations: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for msg in self.analyzer.messages:
            conv_id = msg.get('conversation_id', '')
            if conv_id:
                conversations[conv_id].append(msg)

        # Sort each conversation by date
        for conv_id, messages in conversations.items():
            messages.sort(key=lambda m: m.get('date') or datetime.min)

            if not messages:
                continue

            # Check if I sent the first message
            first_msg = messages[0]
            first_sender = first_msg.get('sender', first_msg.get('from', '')).lower()
            first_direction = first_msg.get('direction', '').upper()

            i_started = (
                first_direction == 'OUTGOING' or
                (my_name_lower and my_name_lower in first_sender)
            )

            if i_started:
                # Check if got a response
                got_response = False
                response_time = None

                for msg in messages[1:]:
                    sender = msg.get('sender', msg.get('from', '')).lower()
                    direction = msg.get('direction', '').upper()

                    is_response = (
                        direction == 'INCOMING' or
                        (my_name_lower and my_name_lower not in sender)
                    )

                    if is_response:
                        got_response = True
                        if first_msg.get('date') and msg.get('date'):
                            delta = msg['date'] - first_msg['date']
                            response_time = delta.total_seconds() / 3600  # Hours
                        break

                self.conversations_started_by_me[conv_id] = {
                    'first_message': first_msg,
                    'got_response': got_response,
                    'response_time_hours': response_time,
                    'total_messages': len(messages),
                }

    def _calculate_response_times(self) -> None:
        """Calculate response times for conversations I started."""
        self.response_times = [
            conv['response_time_hours']
            for conv in self.conversations_started_by_me.values()
            if conv.get('got_response') and conv.get('response_time_hours') is not None
        ]

    def _analyze_best_timing(self) -> tuple[str | None, int | None]:
        """Analyze best day/hour for sending messages.

        Returns:
            Tuple of (best_day, best_hour)
        """
        if not self.conversations_started_by_me:
            return None, None

        # Track response rates by day and hour
        day_stats: dict[int, dict[str, int]] = defaultdict(lambda: {'sent': 0, 'responded': 0})
        hour_stats: dict[int, dict[str, int]] = defaultdict(lambda: {'sent': 0, 'responded': 0})

        for conv in self.conversations_started_by_me.values():
            first_msg = conv['first_message']
            msg_date = first_msg.get('date')

            if not msg_date:
                continue

            day = msg_date.weekday()  # 0=Monday
            hour = msg_date.hour

            day_stats[day]['sent'] += 1
            hour_stats[hour]['sent'] += 1

            if conv.get('got_response'):
                day_stats[day]['responded'] += 1
                hour_stats[hour]['responded'] += 1

        # Find best day (highest response rate with min 3 messages)
        best_day = None
        best_day_rate = 0

        for day, stats in day_stats.items():
            if stats['sent'] >= 3:
                rate = stats['responded'] / stats['sent']
                if rate > best_day_rate:
                    best_day_rate = rate
                    best_day = self.DAYS_OF_WEEK[day]

        # Find best hour (highest response rate with min 2 messages)
        best_hour = None
        best_hour_rate = 0

        for hour, stats in hour_stats.items():
            if stats['sent'] >= 2:
                rate = stats['responded'] / stats['sent']
                if rate > best_hour_rate:
                    best_hour_rate = rate
                    best_hour = hour

        return best_day, best_hour

    def _analyze_message_lengths(self) -> dict[str, Any]:
        """Analyze message lengths and correlation with response rates.

        Returns:
            Dict with length statistics
        """
        if not self.conversations_started_by_me:
            return {}

        lengths_with_response: list[int] = []
        lengths_without_response: list[int] = []

        for conv in self.conversations_started_by_me.values():
            first_msg = conv['first_message']
            content = first_msg.get('content', '')
            length = len(content)

            if conv.get('got_response'):
                lengths_with_response.append(length)
            else:
                lengths_without_response.append(length)

        avg_responded = (
            sum(lengths_with_response) / len(lengths_with_response)
            if lengths_with_response else 0
        )
        avg_no_response = (
            sum(lengths_without_response) / len(lengths_without_response)
            if lengths_without_response else 0
        )

        return {
            'avg_length_responded': round(avg_responded),
            'avg_length_no_response': round(avg_no_response),
            'shorter_is_better': avg_responded < avg_no_response,
            'optimal_length_hint': self._get_length_hint(avg_responded),
        }

    def _get_length_hint(self, avg_length: float) -> str:
        """Get a hint about optimal message length.

        Args:
            avg_length: Average length of responded messages

        Returns:
            Hint string
        """
        if avg_length < 100:
            return "Very short messages (<100 chars) work for you"
        elif avg_length < 300:
            return "Short messages (100-300 chars) work best"
        elif avg_length < 500:
            return "Medium messages (300-500 chars) are your sweet spot"
        else:
            return "Your longer messages (500+ chars) get responses"

    def identify_winning_patterns(self) -> list[dict[str, Any]]:
        """Find patterns in messages that got responses.

        Returns:
            List of pattern insights
        """
        patterns = []

        if not self.conversations_started_by_me:
            return patterns

        # Analyze responded vs non-responded messages
        responded_messages = [
            conv['first_message']
            for conv in self.conversations_started_by_me.values()
            if conv.get('got_response')
        ]

        no_response_messages = [
            conv['first_message']
            for conv in self.conversations_started_by_me.values()
            if not conv.get('got_response')
        ]

        # Check for questions
        questions_in_responded = sum(
            1 for msg in responded_messages
            if '?' in msg.get('content', '')
        )
        questions_in_no_response = sum(
            1 for msg in no_response_messages
            if '?' in msg.get('content', '')
        )

        if responded_messages:
            question_rate_responded = questions_in_responded / len(responded_messages)
            question_rate_no_response = (
                questions_in_no_response / len(no_response_messages)
                if no_response_messages else 0
            )

            if question_rate_responded > question_rate_no_response + 0.1:
                patterns.append({
                    'pattern': 'Questions',
                    'insight': 'Messages with questions get more responses',
                    'responded_rate': f"{question_rate_responded * 100:.0f}%",
                })

        # Check for short messages (under 200 chars)
        short_responded = sum(
            1 for msg in responded_messages
            if len(msg.get('content', '')) < 200
        )
        short_no_response = sum(
            1 for msg in no_response_messages
            if len(msg.get('content', '')) < 200
        )

        if responded_messages and no_response_messages:
            short_rate_responded = short_responded / len(responded_messages)
            short_rate_no_response = short_no_response / len(no_response_messages)

            if short_rate_responded > short_rate_no_response + 0.1:
                patterns.append({
                    'pattern': 'Brevity',
                    'insight': 'Shorter messages (<200 chars) perform better',
                    'responded_rate': f"{short_rate_responded * 100:.0f}%",
                })

        return patterns

    def generate_reverse_report(self, my_name: str) -> str:
        """Generate a formatted outreach effectiveness report.

        Args:
            my_name: User's name

        Returns:
            Formatted report string
        """
        metrics = self.analyze_outreach(my_name)
        patterns = self.identify_winning_patterns()

        lines = [
            "=" * 60,
            "YOUR OUTREACH EFFECTIVENESS",
            "=" * 60,
            "",
            f"Total Messages Sent: {metrics.total_sent}",
            f"Unique Recipients: {metrics.unique_recipients}",
            f"Conversations Started: {metrics.conversations_started}",
            f"Got Responses: {metrics.conversations_with_response}",
            f"Response Rate: {metrics.response_rate}%",
            "",
        ]

        if metrics.avg_response_time_hours is not None:
            if metrics.avg_response_time_hours < 24:
                time_str = f"{metrics.avg_response_time_hours:.1f} hours"
            else:
                days = metrics.avg_response_time_hours / 24
                time_str = f"{days:.1f} days"
            lines.append(f"Average Response Time: {time_str}")
            lines.append("")

        # Timing insights
        if metrics.best_day or metrics.best_hour is not None:
            lines.append("BEST TIMING:")
            if metrics.best_day:
                lines.append(f"   Best day to send: {metrics.best_day}")
            if metrics.best_hour is not None:
                hour_str = f"{metrics.best_hour}:00"
                if metrics.best_hour < 12:
                    hour_str += " AM"
                else:
                    hour_str = f"{metrics.best_hour - 12 if metrics.best_hour > 12 else 12}:00 PM"
                lines.append(f"   Best hour to send: {hour_str}")
            lines.append("")

        # Message length insights
        if metrics.message_length_stats:
            stats = metrics.message_length_stats
            lines.extend([
                "MESSAGE LENGTH INSIGHTS:",
                f"   Avg length (got response): {stats.get('avg_length_responded', 0)} chars",
                f"   Avg length (no response): {stats.get('avg_length_no_response', 0)} chars",
                f"   Hint: {stats.get('optimal_length_hint', 'N/A')}",
                "",
            ])

        # Winning patterns
        if patterns:
            lines.append("WINNING PATTERNS:")
            for p in patterns:
                lines.append(f"   - {p['pattern']}: {p['insight']}")
            lines.append("")

        # Summary advice
        lines.extend([
            "SUMMARY:",
        ])

        if metrics.response_rate > 30:
            lines.append("   Your outreach is performing well (>30% response rate)!")
        elif metrics.response_rate > 15:
            lines.append("   Your outreach is average (15-30% response rate).")
            lines.append("   Consider personalizing more or shortening messages.")
        else:
            lines.append("   Your response rate is low (<15%).")
            lines.append("   Try: shorter messages, specific questions, better timing.")

        lines.extend(["", "=" * 60])

        return "\n".join(lines)
