"""
LinkedIn Message Analyzer

Analyzes exported LinkedIn messages to identify:
1. Requests for your time (calls, coffee, meetings, etc.)
2. Financial advisor outreach
3. Franchise consultants, recruiters, expert networks
4. Weekly summaries of all outreach types
"""

from lib.exceptions import (
    LinkedInAnalyzerError,
    FileLoadError,
    InvalidCSVError,
    DateParseError,
    ConfigurationError,
    LLMError,
    RateLimitError,
    QuotaExhaustedError,
    ProviderUnavailableError,
)
from lib.types import (
    Message,
    TimeRequest,
    FlatteryMessage,
    ConversationThread,
    SenderSummary,
    ThreadTriageItem,
)
from lib.constants import (
    LINKEDIN_INMAIL_LIMIT,
    LINKEDIN_CONNECTION_NOTE_LIMIT,
    LINKEDIN_SUBJECT_LIMIT,
)
from lib.config import setup_logging, load_config
from lib.profile import UserProfile, INDUSTRY_PRESETS
from lib.llm import LLMAnalyzer, LLMProvider, ProviderRegistry
from lib.analyzer import LinkedInMessageAnalyzer
from lib.cli import main
from lib.response_generator import ResponseGenerator, generate_response_for_message
from lib.bingo import BingoCard, BingoGenerator, generate_bingo_card
from lib.anonymizer import Anonymizer, anonymize_name, set_anonymizer, get_anonymizer
from lib.trend import TrendAnalyzer
from lib.health import NetworkHealthAnalyzer, HealthScore
from lib.reverse import ReverseAnalyzer, OutreachMetrics
from lib.comparison import ComparisonAnalyzer, ComparisonResult
from lib.llm_advanced import ConversationSummarizer, SmartReplyGenerator, MessageClusterer
from lib.web import create_app, run_dashboard

__all__ = [
    # Main classes
    'LinkedInMessageAnalyzer',
    'UserProfile',
    'LLMAnalyzer',
    'LLMProvider',
    'ProviderRegistry',
    # Analysis modules
    'TrendAnalyzer',
    'NetworkHealthAnalyzer',
    'HealthScore',
    'ReverseAnalyzer',
    'OutreachMetrics',
    'ComparisonAnalyzer',
    'ComparisonResult',
    # Exceptions
    'LinkedInAnalyzerError',
    'FileLoadError',
    'InvalidCSVError',
    'DateParseError',
    'ConfigurationError',
    'LLMError',
    'RateLimitError',
    'QuotaExhaustedError',
    'ProviderUnavailableError',
    # Type definitions
    'Message',
    'TimeRequest',
    'FlatteryMessage',
    'ConversationThread',
    'SenderSummary',
    'ThreadTriageItem',
    # Configuration
    'INDUSTRY_PRESETS',
    # LinkedIn limits
    'LINKEDIN_INMAIL_LIMIT',
    'LINKEDIN_CONNECTION_NOTE_LIMIT',
    'LINKEDIN_SUBJECT_LIMIT',
    # Functions
    'setup_logging',
    'load_config',
    'main',
    # Response generation
    'ResponseGenerator',
    'generate_response_for_message',
    # Bingo
    'BingoCard',
    'BingoGenerator',
    'generate_bingo_card',
    # Anonymization
    'Anonymizer',
    'anonymize_name',
    'set_anonymizer',
    'get_anonymizer',
    # Advanced LLM features
    'ConversationSummarizer',
    'SmartReplyGenerator',
    'MessageClusterer',
    # Web dashboard
    'create_app',
    'run_dashboard',
]
