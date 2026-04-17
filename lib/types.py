"""Type definitions for LinkedIn Message Analyzer."""

from datetime import datetime
from typing import TypedDict


Message = TypedDict(
    'Message',
    {
        'conversation_id': str,
        'conversation_title': str,
        'from': str,
        'sender_url': str,
        'to': str,
        'recipient_urls': str,
        'date': datetime | None,
        'subject': str,
        'content': str,
        'folder': str,
        'attachments': str,
        'is_draft': str,
    },
    total=False,
)


class TimeRequest(Message, total=False):
    """Message identified as a time request."""

    matched_patterns: list[str]
    estimated_minutes: int


class FlatteryMessage(Message, total=False):
    """Message with flattery analysis."""

    flattery_score: int
    matched_phrases: list[str]
    exclamation_count: int


class ConversationThread(TypedDict, total=False):
    """Thread-level aggregation of messages in a conversation."""

    conversation_id: str
    conversation_title: str
    participants: list[str]
    primary_sender: str
    message_count: int
    incoming_count: int
    outgoing_count: int
    first_message_at: datetime | None
    last_message_at: datetime | None
    has_response_from_me: bool
    messages: list[Message]


class SenderSummary(TypedDict, total=False):
    """Sender-level rollup derived from conversation threads."""

    sender: str
    conversation_count: int
    message_count: int
    responded_conversation_count: int
    unanswered_conversation_count: int
    unanswered_message_count: int
    has_received_response: bool
    first_contact: datetime | None
    last_contact: datetime | None
    conversation_ids: list[str]


class ThreadTriageItem(TypedDict, total=False):
    """Thread-level prioritization item for inbox triage surfaces."""

    conversation_id: str
    conversation_title: str
    primary_sender: str
    incoming_count: int
    message_count: int
    has_response_from_me: bool
    triage_score: int
    labels: list[str]
    recommendation: str
    recommendation_reason: str
    llm_recommendation: str
    llm_intent: str
    llm_analysis_count: int
    llm_high_priority_count: int
    llm_max_authenticity_score: int
    last_message_at: datetime | None
    latest_message_preview: str
