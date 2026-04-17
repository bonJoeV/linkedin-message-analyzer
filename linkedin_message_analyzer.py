#!/usr/bin/env python3
"""
LinkedIn Message Analyzer

Analyzes exported LinkedIn messages to identify:
1. Requests for your time (calls, coffee, meetings, etc.)
2. Financial advisor outreach
3. Weekly summaries of both

Usage:
    python linkedin_message_analyzer.py messages.csv
    python -m lib messages.csv
"""

# Re-export everything from the package
from lib import (
    # Main classes
    LinkedInMessageAnalyzer,
    UserProfile,
    LLMAnalyzer,
    # Exceptions
    LinkedInAnalyzerError,
    FileLoadError,
    InvalidCSVError,
    DateParseError,
    ConfigurationError,
    # Type definitions
    Message,
    TimeRequest,
    FlatteryMessage,
    ConversationThread,
    SenderSummary,
    ThreadTriageItem,
    # Configuration
    INDUSTRY_PRESETS,
    # LinkedIn limits
    LINKEDIN_INMAIL_LIMIT,
    LINKEDIN_CONNECTION_NOTE_LIMIT,
    LINKEDIN_SUBJECT_LIMIT,
    # Functions
    setup_logging,
    load_config,
    main,
)

# Also export validation helpers for full compatibility
from lib.config import (
    validate_user_profile_data,
    validate_config_data,
)

__all__ = [
    # Main classes
    'LinkedInMessageAnalyzer',
    'UserProfile',
    'LLMAnalyzer',
    # Exceptions
    'LinkedInAnalyzerError',
    'FileLoadError',
    'InvalidCSVError',
    'DateParseError',
    'ConfigurationError',
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
    # Validation helpers
    'validate_user_profile_data',
    'validate_config_data',
]

if __name__ == '__main__':
    import sys
    sys.exit(main())
