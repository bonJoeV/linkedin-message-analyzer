"""Constants for LinkedIn Message Analyzer."""

# LLM Analysis
LLM_MESSAGE_TRUNCATE_LENGTH = 2000  # Max characters to send to LLM
LLM_MAX_TOKENS = 500  # Max tokens for LLM response
LLM_RATE_LIMIT_DELAY = 0.2  # Seconds between API calls (5 req/sec)
LLM_DEFAULT_MAX_MESSAGES = 50  # Default max messages to analyze

# Encoding detection
CHARDET_SAMPLE_SIZE = 10000  # Bytes to sample for encoding detection
CHARDET_CONFIDENCE_THRESHOLD = 0.7  # Minimum confidence for chardet result

# Analysis defaults
DEFAULT_WEEKS_BACK = 12  # Default weeks to analyze for reports

# LinkedIn message character limits
LINKEDIN_INMAIL_LIMIT = 8000           # Direct messages (InMail)
LINKEDIN_CONNECTION_NOTE_LIMIT = 300   # Connection request notes
LINKEDIN_SUBJECT_LIMIT = 200           # InMail subject line
