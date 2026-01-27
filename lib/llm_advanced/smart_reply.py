"""Smart reply generation using LLM."""

import json
import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lib.llm.base import LLMProvider
    from lib.types import Message

logger = logging.getLogger(__name__)

# LinkedIn message character limits
LINKEDIN_INMAIL_LIMIT = 1900
LINKEDIN_CONNECTION_NOTE_LIMIT = 300


@dataclass
class SmartReply:
    """Generated smart reply."""

    tone: str
    subject: str | None  # For InMail replies
    body: str
    character_count: int
    fits_limit: bool
    explanation: str  # Why this response works


class SmartReplyGenerator:
    """Generates context-aware reply suggestions using LLM.

    Goes beyond static templates by understanding the context
    of the conversation and generating appropriate responses.
    """

    TONES = {
        'polite': 'Professional and courteous, firm but not rude',
        'firm': 'Direct and assertive, leaves no room for follow-up',
        'playful': 'Light-hearted with a touch of humor',
        'deadpan': 'Dry humor, subtle sarcasm that could be genuine',
        'corporate_speak': 'Hilariously over-the-top corporate jargon',
    }

    REPLY_PROMPT = '''Generate a LinkedIn reply for this message.

Original message from {sender}:
"{message}"

Message type detected: {message_type}
Desired tone: {tone} ({tone_description})

Requirements:
1. Keep under {char_limit} characters (LinkedIn limit)
2. Match the requested tone perfectly
3. Politely decline or deflect the request
4. Don't be mean, just firm and clear
5. Don't agree to any calls, meetings, or follow-ups

Return ONLY valid JSON:
{{
    "subject": "Reply subject line (or null if not needed)",
    "body": "The reply message body",
    "explanation": "Brief explanation of why this response works"
}}

Return ONLY the JSON, no other text.'''

    def __init__(self, provider: 'LLMProvider'):
        """Initialize generator with LLM provider.

        Args:
            provider: Initialized LLM provider instance
        """
        self.provider = provider

    def generate_reply(
        self,
        message: 'Message',
        tone: str = 'polite',
        message_type: str = 'general',
        is_inmail: bool = False,
    ) -> SmartReply:
        """Generate a smart reply for a message.

        Args:
            message: The message to reply to
            tone: Response tone (polite, firm, playful, deadpan, corporate_speak)
            message_type: Detected message type (sales_pitch, recruiter, etc.)
            is_inmail: Whether this is an InMail (affects character limit)

        Returns:
            SmartReply with generated response
        """
        char_limit = LINKEDIN_INMAIL_LIMIT if is_inmail else LINKEDIN_CONNECTION_NOTE_LIMIT

        sender = message.get('from', 'this person')
        content = message.get('content', '')[:1000]  # Truncate for prompt

        tone_desc = self.TONES.get(tone, self.TONES['polite'])

        prompt = self.REPLY_PROMPT.format(
            sender=sender,
            message=content,
            message_type=message_type,
            tone=tone,
            tone_description=tone_desc,
            char_limit=char_limit,
        )

        try:
            response = self.provider.complete(prompt, max_tokens=300, temperature=0.7)
            return self._parse_response(response, tone, char_limit)
        except Exception as e:
            logger.warning(f"Failed to generate smart reply: {e}")
            return self._fallback_reply(tone, message_type, char_limit)

    def generate_all_tones(
        self,
        message: 'Message',
        message_type: str = 'general',
        is_inmail: bool = False,
    ) -> dict[str, SmartReply]:
        """Generate replies in all available tones.

        Args:
            message: The message to reply to
            message_type: Detected message type
            is_inmail: Whether this is an InMail

        Returns:
            Dict mapping tone names to SmartReply objects
        """
        replies = {}
        for tone in self.TONES:
            replies[tone] = self.generate_reply(
                message,
                tone=tone,
                message_type=message_type,
                is_inmail=is_inmail,
            )
        return replies

    def batch_generate(
        self,
        messages: list['Message'],
        tone: str = 'polite',
        message_types: list[str] | None = None,
    ) -> list[SmartReply]:
        """Generate replies for multiple messages.

        Args:
            messages: Messages to generate replies for
            tone: Response tone for all replies
            message_types: Optional list of message types (parallel to messages)

        Returns:
            List of SmartReply objects
        """
        if message_types is None:
            message_types = ['general'] * len(messages)

        replies = []
        for msg, msg_type in zip(messages, message_types):
            reply = self.generate_reply(msg, tone=tone, message_type=msg_type)
            replies.append(reply)

        return replies

    def _parse_response(
        self,
        response: str,
        tone: str,
        char_limit: int,
    ) -> SmartReply:
        """Parse LLM response into SmartReply."""
        try:
            # Clean response
            cleaned = response.strip()
            if cleaned.startswith('```'):
                cleaned = cleaned.split('```')[1]
                if cleaned.startswith('json'):
                    cleaned = cleaned[4:]
            cleaned = cleaned.strip()

            data = json.loads(cleaned)

            body = data.get('body', '')
            char_count = len(body)

            return SmartReply(
                tone=tone,
                subject=data.get('subject'),
                body=body,
                character_count=char_count,
                fits_limit=char_count <= char_limit,
                explanation=data.get('explanation', ''),
            )
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Failed to parse reply response: {e}")
            return self._fallback_reply(tone, 'general', char_limit)

    def _fallback_reply(
        self,
        tone: str,
        message_type: str,
        char_limit: int,
    ) -> SmartReply:
        """Generate fallback reply when LLM fails."""
        fallbacks = {
            'polite': "Thanks for reaching out! I appreciate you thinking of me, but I'm not able to take on new commitments at this time. Best of luck!",
            'firm': "I'm not interested. Please remove me from your list.",
            'playful': "I'd love to help, but my calendar is currently held hostage by existing commitments. Perhaps in another timeline!",
            'deadpan': "I checked my schedule. It appears I'm busy that day. And the next day. And all the days after that. Interesting.",
            'corporate_speak': "Thank you for the proactive outreach regarding potential synergy opportunities. After careful consideration of bandwidth allocation, I must respectfully decline to leverage this networking vector at this juncture.",
        }

        body = fallbacks.get(tone, fallbacks['polite'])

        return SmartReply(
            tone=tone,
            subject=None,
            body=body,
            character_count=len(body),
            fits_limit=len(body) <= char_limit,
            explanation='Fallback response (LLM generation failed)',
        )

    def generate_reply_report(
        self,
        messages: list['Message'],
        replies: list[SmartReply],
    ) -> str:
        """Generate a formatted report of suggested replies.

        Args:
            messages: Original messages
            replies: Generated replies

        Returns:
            Formatted string report
        """
        lines = [
            "=" * 60,
            "SMART REPLY SUGGESTIONS (LLM-Powered)",
            "=" * 60,
        ]

        for msg, reply in zip(messages, replies):
            sender = msg.get('from', 'Unknown')
            preview = msg.get('content', '')[:100]
            if len(msg.get('content', '')) > 100:
                preview += '...'

            tone_emoji = {
                'polite': '😊',
                'firm': '💪',
                'playful': '😄',
                'deadpan': '😐',
                'corporate_speak': '📊',
            }.get(reply.tone, '💬')

            lines.append(f"\n  From: {sender}")
            lines.append(f"  Preview: \"{preview}\"")
            lines.append(f"\n  {tone_emoji} Suggested Reply ({reply.tone}):")
            lines.append(f"  {'─' * 40}")

            # Wrap body text
            words = reply.body.split()
            current_line = "    "
            for word in words:
                if len(current_line) + len(word) + 1 > 60:
                    lines.append(current_line)
                    current_line = "    " + word
                else:
                    current_line += (" " if current_line.strip() else "") + word
            if current_line.strip():
                lines.append(current_line)

            lines.append(f"  {'─' * 40}")
            lines.append(f"  Characters: {reply.character_count}")
            if not reply.fits_limit:
                lines.append(f"  ⚠️  Exceeds LinkedIn limit - needs trimming")
            if reply.explanation:
                lines.append(f"  Why: {reply.explanation}")

        return "\n".join(lines)
