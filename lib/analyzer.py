"""Core LinkedIn Message Analyzer class."""

import csv
import logging
import re
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Sequence

from lib.exceptions import (
    FileLoadError,
    InvalidCSVError,
)
from lib.constants import (
    CHARDET_SAMPLE_SIZE,
    CHARDET_CONFIDENCE_THRESHOLD,
    DEFAULT_WEEKS_BACK,
    LLM_DEFAULT_MAX_MESSAGES,
)
from lib.patterns import (
    TIME_REQUEST_KEYWORDS,
    TIME_ESTIMATES,
    FINANCIAL_ADVISOR_PATTERNS,
    FRANCHISE_CONSULTANT_PATTERNS,
    EXPERT_NETWORK_PATTERNS,
    ANGEL_INVESTOR_PATTERNS,
    RECRUITER_PATTERNS,
    FAKE_PERSONALIZATION_PATTERNS,
    FLATTERY_PATTERNS,
    TEMPLATE_INDICATORS,
    USER_ROLES,
    PITCH_ROLE_MISMATCHES,
    AI_GENERATED_PATTERNS,
    AI_WEIGHTED_PATTERNS,
    CRYPTO_HUSTLER_PATTERNS,
    MLM_PATTERNS,
)
from lib.profile import UserProfile
from lib.llm import LLMAnalyzer

# Optional imports - checked at runtime
try:
    from dateutil import parser as dateutil_parser
    _has_dateutil = True
except ImportError:
    _has_dateutil = False
    dateutil_parser = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


class LinkedInMessageAnalyzer:
    """Analyzes LinkedIn message exports for patterns and outreach types."""

    def __init__(
        self,
        messages_csv_path: str | Path,
        user_profile: UserProfile | None = None,
        llm_analyzer: LLMAnalyzer | None = None,
    ) -> None:
        """Initialize the analyzer with a path to the LinkedIn messages CSV.

        Args:
            messages_csv_path: Path to the LinkedIn messages.csv export file
            user_profile: Optional UserProfile for personalized analysis
            llm_analyzer: Optional LLMAnalyzer for AI-powered classification
        """
        self.messages_csv_path = Path(messages_csv_path)
        self.user_profile = user_profile
        self.llm_analyzer = llm_analyzer

        # Message collections
        self.messages: list[dict[str, Any]] = []
        self.time_requests: list[dict[str, Any]] = []
        self.financial_advisor_messages: list[dict[str, Any]] = []
        self.role_confusion_messages: list[dict[str, Any]] = []
        self.fake_personalization_messages: list[dict[str, Any]] = []
        self.template_messages: list[dict[str, Any]] = []
        self.repeat_offenders: dict[str, dict[str, Any]] = {}
        self.time_patterns: dict[str, Any] = {
            'by_hour': defaultdict(int),
            'by_day': defaultdict(int)
        }
        self.flattery_scores: list[dict[str, Any]] = []
        self.my_responses: set[str] = set()
        self.franchise_consultant_messages: list[dict[str, Any]] = []
        self.expert_network_messages: list[dict[str, Any]] = []
        self.angel_investor_messages: list[dict[str, Any]] = []
        self.recruiter_messages: list[dict[str, Any]] = []
        self.date_range: tuple[datetime, datetime] | None = None

        # New detection categories
        self.ai_generated_messages: list[dict[str, Any]] = []
        self.crypto_hustler_messages: list[dict[str, Any]] = []
        self.mlm_messages: list[dict[str, Any]] = []

        # LLM analysis results
        self.llm_analyses: list[dict[str, Any]] = []

    def load_messages(self) -> 'LinkedInMessageAnalyzer':
        """Load and parse the LinkedIn messages.csv export.

        Returns:
            self for method chaining

        Raises:
            FileLoadError: If the file cannot be read
            InvalidCSVError: If the CSV structure is invalid
        """
        logger.info(f"Loading messages from {self.messages_csv_path}...")

        if not self.messages_csv_path.exists():
            raise FileLoadError(f"File not found: {self.messages_csv_path}")

        if not self.messages_csv_path.is_file():
            raise FileLoadError(f"Path is not a file: {self.messages_csv_path}")

        # Try multiple encodings
        encoding = self._detect_encoding()
        logger.debug(f"Using encoding: {encoding}")

        try:
            # Detect delimiter (tab or comma)
            with open(self.messages_csv_path, 'r', encoding=encoding) as f:
                first_line = f.readline()
                delimiter = '\t' if '\t' in first_line else ','
                delimiter_name = 'tab' if delimiter == '\t' else 'comma'
                logger.debug(f"Detected delimiter: {delimiter_name}")

            with open(self.messages_csv_path, 'r', encoding=encoding) as f:
                reader = csv.DictReader(f, delimiter=delimiter)

                # Validate required columns
                if reader.fieldnames:
                    self._validate_csv_columns(reader.fieldnames)

                row_count = 0
                skipped_count = 0

                for row in reader:
                    row_count += 1
                    try:
                        message = self._parse_row(row)
                        if message['date']:  # Only include messages with valid dates
                            self.messages.append(message)
                        else:
                            skipped_count += 1
                            logger.debug(f"Row {row_count}: Skipped due to invalid/missing date")
                    except Exception as e:
                        skipped_count += 1
                        logger.warning(f"Row {row_count}: Failed to parse - {e}")
                        continue

                if skipped_count > 0:
                    logger.warning(f"Skipped {skipped_count} rows due to parsing issues")

        except UnicodeDecodeError as e:
            raise FileLoadError(f"Failed to decode file with encoding {encoding}: {e}")
        except csv.Error as e:
            raise InvalidCSVError(f"CSV parsing error: {e}")
        except PermissionError:
            raise FileLoadError(f"Permission denied: {self.messages_csv_path}")

        logger.info(f"Loaded {len(self.messages)} messages")

        # Show and store date range
        if self.messages:
            dates = [m['date'] for m in self.messages if m['date']]
            if dates:
                self.date_range = (min(dates), max(dates))
                logger.info(f"Date range: {self.date_range[0].strftime('%Y-%m-%d')} to {self.date_range[1].strftime('%Y-%m-%d')}")

        return self

    def _detect_encoding(self) -> str:
        """Detect the file encoding, trying multiple options.

        Returns:
            The detected encoding string
        """
        encodings_to_try = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252', 'iso-8859-1']

        # Try chardet if available
        try:
            import chardet
            with open(self.messages_csv_path, 'rb') as f:
                raw_data = f.read(CHARDET_SAMPLE_SIZE)
                result = chardet.detect(raw_data)
                if result['encoding'] and result['confidence'] > CHARDET_CONFIDENCE_THRESHOLD:
                    logger.debug(f"chardet detected: {result['encoding']} (confidence: {result['confidence']:.2f})")
                    return result['encoding']
        except ImportError:
            logger.debug("chardet not available, using fallback encoding detection")

        # Fallback: try each encoding
        for encoding in encodings_to_try:
            try:
                with open(self.messages_csv_path, 'r', encoding=encoding) as f:
                    f.read(1000)  # Try to read first 1KB
                return encoding
            except UnicodeDecodeError:
                continue

        # Default to utf-8 if all else fails
        return 'utf-8'

    def _validate_csv_columns(self, fieldnames: Sequence[str] | None) -> None:
        """Validate that the CSV has the expected columns.

        Args:
            fieldnames: List of column names from the CSV

        Raises:
            InvalidCSVError: If required columns are missing
        """
        # Required columns (checking both uppercase and title case variants)
        required_columns = {
            ('CONVERSATION ID', 'Conversation ID'),
            ('FROM', 'From'),
            ('DATE', 'Date'),
            ('CONTENT', 'Content'),
        }

        fieldnames_set = set(fieldnames) if fieldnames else set()

        missing: list[str] = []
        for variants in required_columns:
            if not any(v in fieldnames_set for v in variants):
                missing.append(variants[0])

        if missing:
            raise InvalidCSVError(
                f"Missing required columns: {', '.join(missing)}. "
                f"Found columns: {', '.join(fieldnames or [])}"
            )

        logger.debug(f"CSV columns validated: {list(fieldnames) if fieldnames else []}")

    def _parse_row(self, row: dict[str, Any]) -> dict[str, Any]:
        """Parse a single CSV row into a message dict.

        Args:
            row: Dictionary from csv.DictReader

        Returns:
            Parsed message dictionary
        """
        return {
            'conversation_id': row.get('CONVERSATION ID', row.get('Conversation ID', '')),
            'conversation_title': row.get('CONVERSATION TITLE', row.get('Conversation Title', '')),
            'from': row.get('FROM', row.get('From', '')),
            'sender_url': row.get('SENDER PROFILE URL', row.get('Sender Profile URL', '')),
            'to': row.get('TO', row.get('To', '')),
            'recipient_urls': row.get('RECIPIENT PROFILE URLS', row.get('Recipient Profile URLs', '')),
            'date': self._parse_date(row.get('DATE', row.get('Date', ''))),
            'subject': row.get('SUBJECT', row.get('Subject', '')),
            'content': row.get('CONTENT', row.get('Content', '')),
            'folder': row.get('FOLDER', row.get('Folder', '')),
            'attachments': row.get('ATTACHMENTS', row.get('Attachments', '')),
            'is_draft': row.get('IS MESSAGE DRAFT', row.get('Is Message Draft', '')),
        }

    def _parse_date(self, date_str: str) -> datetime | None:
        """Parse various date formats from LinkedIn exports."""
        if not date_str:
            return None

        # Clean up the date string
        date_str = date_str.strip()

        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d %H:%M:%S UTC',
            '%m/%d/%Y %H:%M:%S',
            '%m/%d/%Y, %H:%M %p',
            '%m/%d/%Y %H:%M',
            '%Y-%m-%d',
            '%m/%d/%y %H:%M:%S',
            '%m/%d/%y %H:%M',
            '%b %d, %Y %H:%M:%S',
            '%b %d, %Y, %H:%M %p',
            '%d %b %Y %H:%M:%S',
        ]

        # Remove UTC suffix if present for parsing
        clean_date = date_str.replace(' UTC', '').strip()

        for fmt in formats:
            try:
                return datetime.strptime(clean_date, fmt)
            except ValueError:
                continue

        # Try parsing with dateutil if available
        if _has_dateutil and dateutil_parser is not None:
            try:
                return dateutil_parser.parse(date_str)
            except (ValueError, TypeError) as e:
                logger.debug(f"dateutil failed to parse date '{date_str}': {e}")
        else:
            logger.debug("dateutil not available for date parsing")

        logger.warning(f"Could not parse date: '{date_str}'")
        return None

    def _matches_patterns(self, text: str, patterns: list[str]) -> list[str]:
        """Check if text matches any of the given regex patterns.

        Args:
            text: Text to search in
            patterns: List of regex patterns to match against

        Returns:
            List of patterns that matched
        """
        if not text:
            return []
        text_lower = text.lower()
        matches: list[str] = []
        for pattern in patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                matches.append(pattern)
        return matches

    def _estimate_time(self, content: str) -> int:
        """Estimate requested time in minutes based on message content."""
        content_lower = content.lower()

        for keyword, minutes in TIME_ESTIMATES.items():
            if keyword in content_lower:
                return minutes
        return TIME_ESTIMATES['default']

    def _is_from_me(self, message: dict[str, Any], my_name: str | None = None) -> bool:
        """Determine if message is from the user (not incoming)."""
        # Check FOLDER field - SENT or similar indicates outgoing
        folder = message.get('folder', '').upper()
        if folder in ['SENT', 'OUTBOX']:
            return True

        # Use profile name if available, otherwise use passed name
        name_to_check = my_name or (self.user_profile.name if self.user_profile else None)

        if name_to_check:
            from_field = message.get('from', '').lower()
            name_lower = name_to_check.lower()
            # Check if any part of the name matches
            name_parts = name_lower.split()
            for part in name_parts:
                if len(part) > 2 and part in from_field:
                    return True

        return False

    def _should_skip_message(self, message: dict[str, Any], my_name: str | None = None) -> bool:
        """Check if a message should be skipped (from self or ignored sender)."""
        if self._is_from_me(message, my_name):
            return True

        # Check if sender is in ignore list
        if self.user_profile:
            sender = message.get('from', '')
            if self.user_profile.should_ignore_sender(sender):
                return True

        return False

    def _analyze_by_pattern(
        self,
        patterns: list[str],
        target_list: list[dict[str, Any]],
        category_name: str,
        my_name: str | None = None,
        include_sender_info: bool = True,
    ) -> int:
        """Generic pattern-based message analysis.

        Args:
            patterns: List of regex patterns to match
            target_list: List to append matching messages to
            category_name: Name of the category for logging
            my_name: User's name for filtering
            include_sender_info: If True, include sender/title in text to check

        Returns:
            Number of messages matched
        """
        logger.info(f"Analyzing messages for {category_name}...")
        initial_count = len(target_list)

        for msg in self.messages:
            if self._is_from_me(msg, my_name):
                continue

            if include_sender_info:
                text_to_check = (
                    f"{msg['from']} {msg['conversation_title']} "
                    f"{msg['subject']} {msg['content']}"
                )
            else:
                text_to_check = f"{msg['subject']} {msg['content']}"

            matches = self._matches_patterns(text_to_check, patterns)

            if matches:
                target_list.append({
                    **msg,
                    'matched_patterns': matches,
                })

        found_count = len(target_list) - initial_count
        logger.info(f"Found {found_count} {category_name} messages")
        return found_count

    def analyze_time_requests(self, my_name: str | None = None) -> 'LinkedInMessageAnalyzer':
        """Identify messages that contain requests for time."""
        logger.info("Analyzing messages for time requests...")

        for msg in self.messages:
            # Skip messages from ourselves
            if self._is_from_me(msg, my_name):
                continue

            content = f"{msg['subject']} {msg['content']}"
            matches = self._matches_patterns(content, TIME_REQUEST_KEYWORDS)

            if matches:
                self.time_requests.append({
                    **msg,
                    'matched_patterns': matches,
                    'estimated_minutes': self._estimate_time(content),
                })

        logger.info(f"Found {len(self.time_requests)} time request messages")
        return self

    def analyze_financial_advisors(self, my_name: str | None = None) -> 'LinkedInMessageAnalyzer':
        """Identify messages from financial advisors."""
        self._analyze_by_pattern(
            FINANCIAL_ADVISOR_PATTERNS,
            self.financial_advisor_messages,
            "financial advisor",
            my_name=my_name,
        )
        return self

    def analyze_franchise_consultants(self, my_name: str | None = None) -> 'LinkedInMessageAnalyzer':
        """Identify messages from franchise consultants/brokers trying to sell you a franchise."""
        self._analyze_by_pattern(
            FRANCHISE_CONSULTANT_PATTERNS,
            self.franchise_consultant_messages,
            "franchise consultant",
            my_name=my_name,
        )
        return self

    def analyze_expert_networks(self, my_name: str | None = None) -> 'LinkedInMessageAnalyzer':
        """Identify messages from expert networks (GLG, Arbolus, etc.) offering paid consultations."""
        self._analyze_by_pattern(
            EXPERT_NETWORK_PATTERNS,
            self.expert_network_messages,
            "expert network",
            my_name=my_name,
        )
        return self

    def analyze_angel_investors(self, my_name: str | None = None) -> 'LinkedInMessageAnalyzer':
        """Identify messages pitching angel/seed investment opportunities."""
        self._analyze_by_pattern(
            ANGEL_INVESTOR_PATTERNS,
            self.angel_investor_messages,
            "angel investor pitch",
            my_name=my_name,
        )
        return self

    def analyze_recruiters(self, my_name: str | None = None) -> 'LinkedInMessageAnalyzer':
        """Identify messages from recruiters about job opportunities."""
        self._analyze_by_pattern(
            RECRUITER_PATTERNS,
            self.recruiter_messages,
            "recruiter",
            my_name=my_name,
        )
        return self

    def analyze_role_confusion(self, my_name: str | None = None) -> 'LinkedInMessageAnalyzer':
        """Identify messages that confuse your different roles (e.g., Microsoft vs Franchise)."""
        logger.info("Analyzing messages for role confusion...")

        for msg in self.messages:
            if self._is_from_me(msg, my_name):
                continue

            content = f"{msg['from']} {msg['conversation_title']} {msg['subject']} {msg['content']}".lower()

            # Check for mismatched pitches
            confusion_detected: list[str] = []

            for pitch_pattern, expected_role, wrong_indicator in PITCH_ROLE_MISMATCHES:
                if re.search(pitch_pattern, content, re.IGNORECASE):
                    # Check if they're mentioning the wrong role context
                    wrong_role = USER_ROLES.get(wrong_indicator, {})
                    for keyword in wrong_role.get('keywords', []):
                        if re.search(keyword, content, re.IGNORECASE):
                            confusion_detected.append(f"Pitched {expected_role} content but mentioned {wrong_indicator}")

            # Also check for generic role mixing
            roles_mentioned: list[str] = []
            for role_name, role_data in USER_ROLES.items():
                for keyword in role_data['keywords']:
                    if re.search(keyword, content, re.IGNORECASE):
                        roles_mentioned.append(role_name)
                        break

            if len(set(roles_mentioned)) > 1:
                confusion_detected.append(f"Mixed roles: {', '.join(set(roles_mentioned))}")

            if confusion_detected:
                self.role_confusion_messages.append({
                    **msg,
                    'confusion_type': confusion_detected,
                })

        logger.info(f"Found {len(self.role_confusion_messages)} role confusion messages")
        return self

    def analyze_fake_personalization(self, my_name: str | None = None) -> 'LinkedInMessageAnalyzer':
        """Identify messages with fake/lazy personalization attempts."""
        logger.info("Analyzing messages for fake personalization...")

        for msg in self.messages:
            if self._is_from_me(msg, my_name):
                continue

            content = f"{msg['subject']} {msg['content']}"
            fake_matches = self._matches_patterns(content, FAKE_PERSONALIZATION_PATTERNS)
            template_matches = self._matches_patterns(content, TEMPLATE_INDICATORS)

            if fake_matches:
                self.fake_personalization_messages.append({
                    **msg,
                    'fake_patterns': fake_matches,
                })

            if template_matches:
                self.template_messages.append({
                    **msg,
                    'template_patterns': template_matches,
                })

        logger.info(f"Found {len(self.fake_personalization_messages)} fake personalization messages")
        logger.info(f"Found {len(self.template_messages)} obvious template messages")
        return self

    def analyze_repeat_offenders(self, my_name: str | None = None) -> 'LinkedInMessageAnalyzer':
        """Identify people who message multiple times without getting a response."""
        logger.info("Analyzing for repeat offenders...")

        # First, identify conversations where I responded
        for msg in self.messages:
            if self._is_from_me(msg, my_name):
                self.my_responses.add(msg['conversation_id'])

        # Group incoming messages by sender
        sender_messages: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for msg in self.messages:
            if self._is_from_me(msg, my_name):
                continue
            sender = msg['from']
            sender_messages[sender].append(msg)

        # Find repeat offenders (2+ messages, no response from me)
        for sender, messages in sender_messages.items():
            if len(messages) >= 2:
                # Check if I responded to any of their conversations
                conv_ids = set(m['conversation_id'] for m in messages)
                responded = bool(conv_ids & self.my_responses)

                if not responded:
                    # Sort by date
                    messages_sorted = sorted(messages, key=lambda x: x['date'] if x['date'] else datetime.min)
                    self.repeat_offenders[sender] = {
                        'messages': messages_sorted,
                        'count': len(messages),
                        'first_contact': messages_sorted[0]['date'],
                        'last_contact': messages_sorted[-1]['date'],
                        'responded': False,
                    }

        logger.info(f"Found {len(self.repeat_offenders)} repeat offenders (2+ messages, no response)")
        return self

    def analyze_time_patterns(self, my_name: str | None = None) -> 'LinkedInMessageAnalyzer':
        """Analyze when messages are sent - exposes automation patterns."""
        logger.info("Analyzing message time patterns...")

        days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

        for msg in self.messages:
            if self._is_from_me(msg, my_name):
                continue
            if not msg['date']:
                continue

            hour = msg['date'].hour
            day = msg['date'].weekday()

            self.time_patterns['by_hour'][hour] += 1
            self.time_patterns['by_day'][days_of_week[day]] += 1

        # Identify suspicious patterns
        suspicious_hours = []
        for hour, count in self.time_patterns['by_hour'].items():
            if hour < 6 or hour > 22:  # Before 6am or after 10pm
                if count > 0:
                    suspicious_hours.append((hour, count))

        self.time_patterns['suspicious_hours'] = suspicious_hours
        self.time_patterns['weekend_count'] = (
            self.time_patterns['by_day'].get('Saturday', 0) +
            self.time_patterns['by_day'].get('Sunday', 0)
        )

        logger.info("Time pattern analysis complete")
        return self

    def analyze_flattery(self, my_name: str | None = None) -> 'LinkedInMessageAnalyzer':
        """Calculate flattery index - how much empty praise before the ask."""
        logger.info("Analyzing flattery levels...")

        for msg in self.messages:
            if self._is_from_me(msg, my_name):
                continue

            content = f"{msg['subject']} {msg['content']}"
            content_lower = content.lower()

            flattery_score = 0
            matched_phrases: list[str] = []

            for pattern, points in FLATTERY_PATTERNS:
                matches = re.findall(pattern, content_lower, re.IGNORECASE)
                if matches:
                    flattery_score += points * len(matches)
                    matched_phrases.extend(matches if isinstance(matches[0], str) else [m[0] for m in matches])

            # Count exclamation marks as additional signal
            exclamation_count = content.count('!')
            if exclamation_count > 2:
                flattery_score += exclamation_count - 2

            if flattery_score > 0:
                self.flattery_scores.append({
                    **msg,
                    'flattery_score': flattery_score,
                    'matched_phrases': matched_phrases,
                    'exclamation_count': exclamation_count,
                })

        # Sort by flattery score
        self.flattery_scores.sort(key=lambda x: x['flattery_score'], reverse=True)

        avg_flattery = sum(m['flattery_score'] for m in self.flattery_scores) / max(len(self.flattery_scores), 1)
        logger.info(f"Found {len(self.flattery_scores)} messages with flattery (avg score: {avg_flattery:.1f})")
        return self

    def run_all_analyses(self, my_name: str | None = None) -> 'LinkedInMessageAnalyzer':
        """Run all analysis methods in sequence.

        Args:
            my_name: Your name (to filter out your own messages)

        Returns:
            self for method chaining
        """
        logger.info("Running all analyses...")
        self.analyze_time_requests(my_name=my_name)
        self.analyze_financial_advisors(my_name=my_name)
        self.analyze_franchise_consultants(my_name=my_name)
        self.analyze_expert_networks(my_name=my_name)
        self.analyze_angel_investors(my_name=my_name)
        self.analyze_recruiters(my_name=my_name)
        self.analyze_role_confusion(my_name=my_name)
        self.analyze_fake_personalization(my_name=my_name)
        self.analyze_repeat_offenders(my_name=my_name)
        self.analyze_time_patterns(my_name=my_name)
        self.analyze_flattery(my_name=my_name)
        self.analyze_ai_generated(my_name=my_name)
        self.analyze_crypto_hustlers(my_name=my_name)
        self.analyze_mlm(my_name=my_name)
        logger.info("All analyses complete")
        return self

    def analyze_ai_generated(self, my_name: str | None = None) -> 'LinkedInMessageAnalyzer':
        """Identify messages that are obviously AI-generated (ChatGPT slop)."""
        logger.info("Analyzing messages for AI-generated content...")

        for msg in self.messages:
            if self._is_from_me(msg, my_name):
                continue

            content = f"{msg['subject']} {msg['content']}"
            content_lower = content.lower()

            ai_score = 0
            matched_patterns: list[str] = []

            for pattern, points in AI_WEIGHTED_PATTERNS:
                if re.search(pattern, content_lower, re.IGNORECASE):
                    ai_score += points
                    matched_patterns.append(pattern)

            # Also check non-weighted patterns
            basic_matches = self._matches_patterns(content, AI_GENERATED_PATTERNS)
            ai_score += len(basic_matches)
            matched_patterns.extend(basic_matches)

            if ai_score >= 3:  # Threshold for "probably AI"
                self.ai_generated_messages.append({
                    **msg,
                    'ai_score': ai_score,
                    'matched_patterns': matched_patterns,
                })

        # Sort by AI score
        self.ai_generated_messages.sort(key=lambda x: x['ai_score'], reverse=True)
        logger.info(f"Found {len(self.ai_generated_messages)} AI-generated messages")
        return self

    def analyze_crypto_hustlers(self, my_name: str | None = None) -> 'LinkedInMessageAnalyzer':
        """Identify crypto/NFT/Web3 hustler messages."""
        self._analyze_by_pattern(
            CRYPTO_HUSTLER_PATTERNS,
            self.crypto_hustler_messages,
            "crypto hustler",
            my_name=my_name,
        )
        return self

    def analyze_mlm(self, my_name: str | None = None) -> 'LinkedInMessageAnalyzer':
        """Identify MLM/pyramid scheme messages."""
        self._analyze_by_pattern(
            MLM_PATTERNS,
            self.mlm_messages,
            "MLM/pyramid scheme",
            my_name=my_name,
        )
        return self

    def run_llm_analysis(
        self,
        max_messages: int = LLM_DEFAULT_MAX_MESSAGES,
        message_filter: str = 'time_requests',
    ) -> 'LinkedInMessageAnalyzer':
        """Run LLM-powered analysis on messages.

        Args:
            max_messages: Maximum number of messages to analyze (to control API costs)
            message_filter: Which messages to analyze:
                - 'time_requests': Only messages identified as time requests
                - 'all': All incoming messages
                - 'suspicious': Messages with high flattery or fake personalization

        Returns:
            self for method chaining
        """
        if not self.llm_analyzer:
            logger.warning("No LLM analyzer configured, skipping LLM analysis")
            return self

        # Select messages to analyze
        if message_filter == 'time_requests':
            messages_to_analyze = self.time_requests
        elif message_filter == 'suspicious':
            # Combine fake personalization and high flattery messages
            suspicious_ids: set[str] = set()
            messages_to_analyze: list[dict[str, Any]] = []
            for msg in self.fake_personalization_messages:
                conv_id = msg.get('conversation_id', '')
                if conv_id not in suspicious_ids:
                    messages_to_analyze.append(msg)
                    suspicious_ids.add(conv_id)
            for msg in self.flattery_scores[:20]:  # Top 20 flattery messages
                conv_id = msg.get('conversation_id', '')
                if conv_id not in suspicious_ids:
                    messages_to_analyze.append(msg)
                    suspicious_ids.add(conv_id)
        else:  # 'all'
            # Filter to incoming messages only
            my_name = self.user_profile.name if self.user_profile else None
            messages_to_analyze = [
                m for m in self.messages
                if not self._is_from_me(m, my_name)
            ]

        if not messages_to_analyze:
            logger.warning("No messages to analyze with LLM")
            return self

        logger.info(f"Running LLM analysis on {min(len(messages_to_analyze), max_messages)} messages...")

        def progress_callback(current: int, total: int) -> None:
            if current % 10 == 0 or current == total:
                logger.info(f"LLM analysis progress: {current}/{total}")

        self.llm_analyses = self.llm_analyzer.analyze_messages_batch(
            messages_to_analyze,
            max_messages=max_messages,
            progress_callback=progress_callback,
        )

        logger.info(f"LLM analysis complete: {len(self.llm_analyses)} messages analyzed")
        return self

    def get_llm_summary(self) -> str:
        """Get a formatted summary of LLM analysis results."""
        if not self.llm_analyzer:
            return "LLM analysis not configured."
        if not self.llm_analyses:
            return "No LLM analysis results available. Run run_llm_analysis() first."
        return self.llm_analyzer.generate_summary_report(self.llm_analyses)

    def get_high_priority_messages(self) -> list[dict[str, Any]]:
        """Get messages the LLM recommends as priority or to consider."""
        priority: list[dict[str, Any]] = []
        for analysis in self.llm_analyses:
            if analysis.get('recommendation') in ['priority', 'consider']:
                priority.append(analysis)
        return sorted(priority, key=lambda x: x.get('authenticity_score', 0), reverse=True)

    def get_time_pattern_summary(self) -> dict[str, Any]:
        """Generate a summary of time patterns for reporting."""
        by_hour = dict(self.time_patterns['by_hour'])
        by_day = dict(self.time_patterns['by_day'])

        # Find peak hour
        peak_hour = max(by_hour.items(), key=lambda x: x[1]) if by_hour else (0, 0)

        # Find peak day
        peak_day = max(by_day.items(), key=lambda x: x[1]) if by_day else ('Monday', 0)

        # Business hours (9-5) vs off-hours
        business_hours = sum(by_hour.get(h, 0) for h in range(9, 17))
        total_messages = sum(by_hour.values())
        off_hours = total_messages - business_hours

        return {
            'by_hour': by_hour,
            'by_day': by_day,
            'peak_hour': peak_hour,
            'peak_day': peak_day,
            'business_hours_count': business_hours,
            'off_hours_count': off_hours,
            'off_hours_pct': round(off_hours / max(total_messages, 1) * 100, 1),
            'suspicious_hours': self.time_patterns.get('suspicious_hours', []),
            'weekend_count': self.time_patterns.get('weekend_count', 0),
            'weekend_pct': round(self.time_patterns.get('weekend_count', 0) / max(total_messages, 1) * 100, 1),
        }

    def get_flattery_summary(self) -> dict[str, Any]:
        """Generate flattery analysis summary."""
        if not self.flattery_scores:
            return {'avg_score': 0, 'max_score': 0, 'top_flatterers': [], 'messages_with_flattery': 0}

        scores = [m['flattery_score'] for m in self.flattery_scores]

        return {
            'avg_score': round(sum(scores) / len(scores), 1),
            'max_score': max(scores),
            'messages_with_flattery': len(self.flattery_scores),
            'top_flatterers': self.flattery_scores[:5],  # Top 5 most flattering messages
            'most_common_phrases': self._get_common_flattery_phrases(),
        }

    def _get_common_flattery_phrases(self) -> list[tuple[str, int]]:
        """Get the most common flattery phrases used."""
        phrase_counts: dict[str, int] = defaultdict(int)
        for msg in self.flattery_scores:
            for phrase in msg['matched_phrases']:
                # Normalize the phrase
                if isinstance(phrase, tuple):
                    phrase = phrase[0]
                phrase_counts[phrase.lower().strip()] += 1

        # Sort by frequency
        sorted_phrases = sorted(phrase_counts.items(), key=lambda x: x[1], reverse=True)
        return sorted_phrases[:10]

    def _calculate_weeks_of_data(self) -> float:
        """Calculate the number of weeks covered by the message data.

        Returns:
            Number of weeks as a float, minimum 1.0
        """
        if self.date_range:
            start_date, end_date = self.date_range
            days = (end_date - start_date).days
            weeks = max(days / 7, 1.0)
            logger.debug(f"Calculated {weeks:.1f} weeks of data from {start_date} to {end_date}")
            return weeks

        # Fallback: calculate from messages directly
        if self.messages:
            dates = [m['date'] for m in self.messages if m.get('date')]
            if dates:
                days = (max(dates) - min(dates)).days
                weeks = max(days / 7, 1.0)
                logger.debug(f"Calculated {weeks:.1f} weeks from message dates")
                return weeks

        logger.warning(f"Could not calculate weeks of data, defaulting to {DEFAULT_WEEKS_BACK}")
        return float(DEFAULT_WEEKS_BACK)

    def calculate_audacity_metrics(self, weeks_back: int = DEFAULT_WEEKS_BACK) -> dict[str, Any]:
        """Calculate fun metrics about the audacity of requests.

        Args:
            weeks_back: Number of weeks to include in calculations
        """
        # Filter time requests to only include those within the specified window
        cutoff = datetime.now() - timedelta(weeks=weeks_back)
        recent_requests = [
            r for r in self.time_requests
            if r.get('date') and r['date'] >= cutoff
        ]

        total_minutes_requested = sum(r['estimated_minutes'] for r in recent_requests)
        total_hours = total_minutes_requested / 60

        # Use the specified weeks_back for calculations
        hours_per_week_requested = total_hours / weeks_back
        pct_of_work_week = (hours_per_week_requested / 40) * 100

        # Count strangers vs connections (heuristic: first message in conversation)
        # For now, assume all are "cold" outreach
        cold_requests = len(recent_requests)

        # If you said yes to everyone (annualized)
        if_yes_to_all_yearly = total_hours * (52 / weeks_back)

        # Filter other message types for the same window
        recent_fa = [m for m in self.financial_advisor_messages if m.get('date') and m['date'] >= cutoff]
        recent_fake_personalization = [m for m in self.fake_personalization_messages if m.get('date') and m['date'] >= cutoff]
        recent_role_confusion = [m for m in self.role_confusion_messages if m.get('date') and m['date'] >= cutoff]

        return {
            'total_hours_requested': round(total_hours, 1),
            'hours_per_week': round(hours_per_week_requested, 1),
            'pct_of_40hr_week': round(pct_of_work_week, 1),
            'if_yes_to_all_yearly_hours': round(if_yes_to_all_yearly, 0),
            'cold_outreach_count': cold_requests,
            'fa_count': len(recent_fa),
            'fa_pct_of_requests': round(len(recent_fa) / max(len(recent_requests), 1) * 100, 1),
            'fake_personalization_count': len(recent_fake_personalization),
            'role_confusion_count': len(recent_role_confusion),
        }

    def get_weekly_summary(self, weeks_back: int = DEFAULT_WEEKS_BACK) -> dict[str, Any]:
        """Generate weekly summaries of time requests and FA outreach."""

        def get_week_key(dt: datetime) -> str:
            """Get ISO week key for a datetime."""
            return dt.strftime('%Y-W%W')

        # Initialize weekly buckets
        cutoff = datetime.now() - timedelta(weeks=weeks_back)

        weekly_time_requests: dict[str, dict[str, Any]] = defaultdict(lambda: {
            'count': 0,
            'total_minutes': 0,
            'requesters': [],
        })

        weekly_fa_outreach: dict[str, dict[str, Any]] = defaultdict(lambda: {
            'count': 0,
            'senders': [],
        })

        # Aggregate time requests by week
        for req in self.time_requests:
            if req['date'] and req['date'] >= cutoff:
                week_key = get_week_key(req['date'])
                weekly_time_requests[week_key]['count'] += 1
                weekly_time_requests[week_key]['total_minutes'] += req['estimated_minutes']
                weekly_time_requests[week_key]['requesters'].append(req['from'])

        # Aggregate FA messages by week
        for msg in self.financial_advisor_messages:
            if msg['date'] and msg['date'] >= cutoff:
                week_key = get_week_key(msg['date'])
                weekly_fa_outreach[week_key]['count'] += 1
                weekly_fa_outreach[week_key]['senders'].append(msg['from'])

        return {
            'time_requests_by_week': dict(weekly_time_requests),
            'fa_outreach_by_week': dict(weekly_fa_outreach),
        }

    # Convenience methods that delegate to reporters
    def print_report(self, weeks_back: int = DEFAULT_WEEKS_BACK) -> None:
        """Print a formatted analysis report."""
        from lib.reporters import ConsoleReporter
        reporter = ConsoleReporter(weeks_back=weeks_back)
        reporter.print_report(self)

    def generate_post_stats(self, weeks_back: int = DEFAULT_WEEKS_BACK) -> str:
        """Generate witty, quotable statistics for a LinkedIn post."""
        from lib.reporters import ConsoleReporter
        reporter = ConsoleReporter(weeks_back=weeks_back)
        return reporter.generate_post_stats(self)

    def export_to_json(self, output_path: str) -> None:
        """Export analysis results to JSON for further processing."""
        from lib.reporters import JSONReporter
        reporter = JSONReporter(output_path=output_path)
        reporter.generate(self)

    def get_hall_of_shame(self, top_n: int = 10) -> list[dict[str, Any]]:
        """Get the Hall of Shame - worst offenders ranked by audacity.

        Audacity score is calculated based on:
        - Number of messages sent without response
        - Pattern matches (AI-generated, flattery, etc.)
        - Time span of pestering
        - Awkward hours of contact

        Args:
            top_n: Number of offenders to return

        Returns:
            List of offender dicts with audacity scores
        """
        shame_list: list[dict[str, Any]] = []

        for sender, data in self.repeat_offenders.items():
            audacity_score = 0
            shame_reasons: list[str] = []

            # Base score: number of messages
            msg_count = data['count']
            audacity_score += msg_count * 10
            if msg_count >= 5:
                shame_reasons.append(f"Sent {msg_count} messages without taking the hint")
            elif msg_count >= 3:
                shame_reasons.append(f"Persistent: {msg_count} messages")

            # Check if any messages were AI-generated
            sender_ai_msgs = [m for m in self.ai_generated_messages if m.get('from') == sender]
            if sender_ai_msgs:
                audacity_score += len(sender_ai_msgs) * 15
                shame_reasons.append("Used AI-generated templates")

            # Check if any messages had fake personalization
            sender_fake = [m for m in self.fake_personalization_messages if m.get('from') == sender]
            if sender_fake:
                audacity_score += len(sender_fake) * 10
                shame_reasons.append("Fake personalization attempts")

            # Check for high flattery scores
            sender_flattery = [m for m in self.flattery_scores if m.get('from') == sender]
            if sender_flattery:
                max_flattery = max(m.get('flattery_score', 0) for m in sender_flattery)
                if max_flattery > 10:
                    audacity_score += max_flattery
                    shame_reasons.append(f"Excessive flattery (score: {max_flattery})")

            # Check for weird timing
            for msg in data.get('messages', []):
                if msg.get('date'):
                    hour = msg['date'].hour
                    if hour < 6 or hour > 22:
                        audacity_score += 5
                        if "odd hours" not in str(shame_reasons):
                            shame_reasons.append("Messaged at odd hours")

            # Time span bonus - longer pestering = more audacity
            first = data.get('first_contact')
            last = data.get('last_contact')
            if first and last:
                span_days = (last - first).days
                if span_days > 30:
                    audacity_score += span_days // 10
                    shame_reasons.append(f"Pestered over {span_days} days")

            # Determine persistence level
            if audacity_score >= 100:
                persistence_level = "Legendary Pest"
            elif audacity_score >= 70:
                persistence_level = "Relentless"
            elif audacity_score >= 40:
                persistence_level = "Very Persistent"
            elif audacity_score >= 20:
                persistence_level = "Persistent"
            else:
                persistence_level = "Mildly Annoying"

            shame_list.append({
                'sender': sender,
                'audacity_score': audacity_score,
                'message_count': msg_count,
                'persistence_level': persistence_level,
                'shame_reasons': shame_reasons,
                'first_contact': first,
                'last_contact': last,
                'sample_message': data['messages'][0].get('content', '')[:200] if data.get('messages') else '',
            })

        # Sort by audacity score
        shame_list.sort(key=lambda x: x['audacity_score'], reverse=True)

        return shame_list[:top_n]

    def get_message_audacity_scores(self) -> list[dict[str, Any]]:
        """Score individual messages by audacity level.

        Useful for finding the single most egregious messages.

        Returns:
            List of messages with audacity scores, sorted descending
        """
        scored_messages: list[dict[str, Any]] = []

        for msg in self.messages:
            if self._is_from_me(msg):
                continue

            audacity = 0
            reasons: list[str] = []

            content = f"{msg.get('subject', '')} {msg.get('content', '')}"

            # Check for time request
            if any(m['conversation_id'] == msg['conversation_id'] for m in self.time_requests):
                audacity += 10
                reasons.append("Asked for time")

            # Check for AI-generated patterns
            if any(m['conversation_id'] == msg['conversation_id'] for m in self.ai_generated_messages):
                ai_msg = next((m for m in self.ai_generated_messages if m['conversation_id'] == msg['conversation_id']), None)
                if ai_msg:
                    audacity += ai_msg.get('ai_score', 0) * 3
                    reasons.append(f"AI-generated (score: {ai_msg.get('ai_score', 0)})")

            # Check for flattery
            flattery_msg = next((m for m in self.flattery_scores if m['conversation_id'] == msg['conversation_id']), None)
            if flattery_msg:
                audacity += flattery_msg.get('flattery_score', 0)
                if flattery_msg.get('flattery_score', 0) > 5:
                    reasons.append(f"Flattery overload ({flattery_msg.get('flattery_score', 0)} points)")

            # Check for fake personalization
            if any(m['conversation_id'] == msg['conversation_id'] for m in self.fake_personalization_messages):
                audacity += 15
                reasons.append("Fake personalization")

            # Check for template indicators
            if any(m['conversation_id'] == msg['conversation_id'] for m in self.template_messages):
                audacity += 20
                reasons.append("Obvious template")

            # Check message length (very short = lazy, very long = inconsiderate)
            content_len = len(content)
            if content_len < 50:
                audacity += 5
                reasons.append("Lazy short message")
            elif content_len > 1000:
                audacity += 10
                reasons.append("Wall of text")

            # Check for multiple exclamation marks
            exclamation_count = content.count('!')
            if exclamation_count > 5:
                audacity += exclamation_count
                reasons.append(f"Excessive punctuation ({exclamation_count} exclamation marks)")

            # Only include messages with some audacity
            if audacity > 0:
                scored_messages.append({
                    **msg,
                    'audacity_score': audacity,
                    'audacity_reasons': reasons,
                })

        scored_messages.sort(key=lambda x: x['audacity_score'], reverse=True)
        return scored_messages
