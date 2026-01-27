"""Type definitions for LinkedIn Message Analyzer."""

from datetime import datetime
from typing import TypedDict


class Message(TypedDict, total=False):
    """Type definition for a parsed LinkedIn message."""
    conversation_id: str
    conversation_title: str
    from_: str  # 'from' is reserved
    sender_url: str
    to: str
    recipient_urls: str
    date: datetime | None
    subject: str
    content: str
    folder: str
    attachments: str
    is_draft: str


class TimeRequest(Message):
    """Message identified as a time request."""
    matched_patterns: list[str]
    estimated_minutes: int


class FlatteryMessage(Message):
    """Message with flattery analysis."""
    flattery_score: int
    matched_phrases: list[str]
    exclamation_count: int
