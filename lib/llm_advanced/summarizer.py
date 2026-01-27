"""Conversation summarization using LLM."""

import json
import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lib.llm.base import LLMProvider
    from lib.types import Message

logger = logging.getLogger(__name__)


@dataclass
class ConversationSummary:
    """Summary of a conversation thread."""

    sender: str
    message_count: int
    intent: str
    key_points: list[str]
    snark_level: int  # 1-10, how eye-roll-worthy
    worth_responding: bool
    suggested_action: str
    one_liner: str  # Snarky one-line summary


class ConversationSummarizer:
    """Summarizes LinkedIn conversation threads using LLM.

    Groups messages by sender and generates concise summaries
    with intent classification and snark scoring.
    """

    SUMMARIZE_PROMPT = '''Analyze this LinkedIn conversation thread and provide a JSON summary.

Messages from {sender}:
{messages}

Return ONLY valid JSON with this structure:
{{
    "intent": "sales_pitch|recruiting|networking|genuine_connection|spam|information_request|other",
    "key_points": ["point 1", "point 2", "point 3"],
    "snark_level": 7,
    "worth_responding": false,
    "suggested_action": "ignore|polite_decline|respond|block",
    "one_liner": "A snarky one-sentence summary of what they want"
}}

Guidelines:
- snark_level: 1 = genuine, helpful message; 10 = maximum audacity/spam
- worth_responding: true only if there's actual value in responding
- key_points: Max 3 bullet points capturing the essence
- one_liner: Be witty but accurate (e.g., "Wants 30 minutes of your time to sell you something you don't need")

Return ONLY the JSON, no other text.'''

    def __init__(self, provider: 'LLMProvider'):
        """Initialize summarizer with LLM provider.

        Args:
            provider: Initialized LLM provider instance
        """
        self.provider = provider
        self._cache: dict[str, ConversationSummary] = {}

    def summarize_thread(
        self,
        messages: list['Message'],
        sender: str,
    ) -> ConversationSummary:
        """Summarize a conversation thread from a single sender.

        Args:
            messages: List of messages from the sender
            sender: Sender name

        Returns:
            ConversationSummary with intent, key points, and snark score
        """
        # Check cache
        cache_key = f"{sender}:{len(messages)}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        # Format messages for prompt
        formatted = []
        for i, msg in enumerate(messages[:10], 1):  # Limit to 10 messages
            content = msg.get('content', '')[:500]  # Truncate long messages
            date = msg.get('date', 'Unknown date')
            formatted.append(f"[{i}] ({date}): {content}")

        messages_text = "\n\n".join(formatted)

        # Build and send prompt
        prompt = self.SUMMARIZE_PROMPT.format(
            sender=sender,
            messages=messages_text,
        )

        try:
            response = self.provider.complete(prompt, max_tokens=400, temperature=0.3)
            result = self._parse_response(response, sender, len(messages))
            self._cache[cache_key] = result
            return result
        except Exception as e:
            logger.warning(f"Failed to summarize thread from {sender}: {e}")
            return self._fallback_summary(sender, len(messages))

    def summarize_inbox(
        self,
        messages: list['Message'],
        max_senders: int = 20,
    ) -> list[ConversationSummary]:
        """Summarize conversations from multiple senders.

        Args:
            messages: All messages to analyze
            max_senders: Maximum number of senders to summarize

        Returns:
            List of ConversationSummary objects
        """
        # Group messages by sender
        by_sender: dict[str, list['Message']] = {}
        for msg in messages:
            sender = msg.get('from', 'Unknown')
            if sender not in by_sender:
                by_sender[sender] = []
            by_sender[sender].append(msg)

        # Sort by message count (most prolific senders first)
        sorted_senders = sorted(
            by_sender.items(),
            key=lambda x: len(x[1]),
            reverse=True,
        )[:max_senders]

        summaries = []
        for sender, sender_messages in sorted_senders:
            summary = self.summarize_thread(sender_messages, sender)
            summaries.append(summary)

        return summaries

    def _parse_response(
        self,
        response: str,
        sender: str,
        message_count: int,
    ) -> ConversationSummary:
        """Parse LLM response into ConversationSummary."""
        try:
            # Clean response (remove markdown code blocks if present)
            cleaned = response.strip()
            if cleaned.startswith('```'):
                cleaned = cleaned.split('```')[1]
                if cleaned.startswith('json'):
                    cleaned = cleaned[4:]
            cleaned = cleaned.strip()

            data = json.loads(cleaned)

            return ConversationSummary(
                sender=sender,
                message_count=message_count,
                intent=data.get('intent', 'unknown'),
                key_points=data.get('key_points', [])[:3],
                snark_level=min(10, max(1, int(data.get('snark_level', 5)))),
                worth_responding=bool(data.get('worth_responding', False)),
                suggested_action=data.get('suggested_action', 'ignore'),
                one_liner=data.get('one_liner', 'Unable to summarize'),
            )
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"Failed to parse LLM response: {e}")
            return self._fallback_summary(sender, message_count)

    def _fallback_summary(
        self,
        sender: str,
        message_count: int,
    ) -> ConversationSummary:
        """Generate fallback summary when LLM fails."""
        return ConversationSummary(
            sender=sender,
            message_count=message_count,
            intent='unknown',
            key_points=['Unable to analyze - LLM response parsing failed'],
            snark_level=5,
            worth_responding=False,
            suggested_action='review_manually',
            one_liner=f'{message_count} messages from {sender} - review manually',
        )

    def generate_summary_report(
        self,
        summaries: list[ConversationSummary],
    ) -> str:
        """Generate a formatted report from summaries.

        Args:
            summaries: List of conversation summaries

        Returns:
            Formatted string report
        """
        lines = [
            "=" * 60,
            "CONVERSATION SUMMARIES (LLM-Powered)",
            "=" * 60,
        ]

        # Sort by snark level (highest first)
        sorted_summaries = sorted(
            summaries,
            key=lambda s: s.snark_level,
            reverse=True,
        )

        for summary in sorted_summaries:
            snark_bar = "🙄" * (summary.snark_level // 2)
            action_emoji = {
                'ignore': '🚫',
                'polite_decline': '👋',
                'respond': '✅',
                'block': '⛔',
                'review_manually': '👁️',
            }.get(summary.suggested_action, '❓')

            lines.append(f"\n  {summary.sender} ({summary.message_count} messages)")
            lines.append(f"    Intent: {summary.intent}")
            lines.append(f"    Snark Level: {summary.snark_level}/10 {snark_bar}")
            lines.append(f"    Summary: \"{summary.one_liner}\"")
            lines.append(f"    Action: {action_emoji} {summary.suggested_action}")

            if summary.key_points:
                lines.append("    Key Points:")
                for point in summary.key_points:
                    lines.append(f"      • {point}")

        # Add stats
        if summaries:
            avg_snark = sum(s.snark_level for s in summaries) / len(summaries)
            worth_count = sum(1 for s in summaries if s.worth_responding)
            lines.append(f"\n  {'─' * 50}")
            lines.append(f"  Average Snark Level: {avg_snark:.1f}/10")
            lines.append(f"  Worth Responding: {worth_count}/{len(summaries)}")

        return "\n".join(lines)
